# -*- coding: utf-8 -*-
"""
멀티테넌트 & org_id 계층 검색 테스트

README.md의 테스트 데이터 정의를 기반으로 한 통합 테스트:
- tenant_id: "company_abc" (고정)
- org_id: 0100(부서), 0101/0102(팀), ""(전사 공유)
- project_code: HR001, HR002, POLICY001, TECH001
"""

import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import app
from app.models.db_models import Base


@pytest.fixture
def test_db_engine():
    """독립된 인메모리 DB"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db_engine):
    TestSession = sessionmaker(
        bind=test_db_engine, autocommit=False, autoflush=False
    )
    session = TestSession()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def routing_config(tmp_path):
    import json
    cfg = {
        "routing_rules": [
            {
                "vector_db_id": "vdb_hr_recruit_01",
                "target_category_mid": ["채용", "recruitment"],
                "engine_type": "local_json",
            },
            {
                "vector_db_id": "vdb_hr_payroll_01",
                "target_category_mid": ["급여", "payroll"],
                "engine_type": "local_json",
            },
            {
                "vector_db_id": "vdb_policy_01",
                "target_category_mid": ["취업규칙", "policy"],
                "engine_type": "local_json",
            },
            {
                "vector_db_id": "vdb_ontology_01",
                "target_category_mid": ["ontology"],
                "engine_type": "local_json",
            },
        ]
    }
    cfg_file = tmp_path / "routing_config.json"
    cfg_file.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    return cfg_file


@pytest.fixture
def client_company_abc(db_session, tmp_path, monkeypatch, routing_config):
    """company_abc 테넌트 클라이언트"""
    from app.core import config as cfg_module

    monkeypatch.setattr(cfg_module.settings, "vector_store_dir", tmp_path / "vs")
    monkeypatch.setattr(cfg_module.settings, "raw_documents_dir", tmp_path / "raw")
    monkeypatch.setattr(cfg_module.settings, "processed_dir", tmp_path / "proc")
    monkeypatch.setattr(cfg_module.settings, "routing_config_path", routing_config)
    monkeypatch.setattr(cfg_module.settings, "pipeline_sync_mode", True)
    (tmp_path / "vs").mkdir()
    (tmp_path / "raw").mkdir()
    (tmp_path / "proc").mkdir()

    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app, headers={"X-Tenant-ID": "company_abc"}) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def client_other_tenant(db_session, tmp_path, monkeypatch, routing_config):
    """company_xyz 테넌트 클라이언트 (멀티테넌트 격리 테스트용)"""
    from app.core import config as cfg_module

    monkeypatch.setattr(cfg_module.settings, "vector_store_dir", tmp_path / "vs2")
    monkeypatch.setattr(cfg_module.settings, "raw_documents_dir", tmp_path / "raw2")
    monkeypatch.setattr(cfg_module.settings, "processed_dir", tmp_path / "proc2")
    monkeypatch.setattr(cfg_module.settings, "routing_config_path", routing_config)
    monkeypatch.setattr(cfg_module.settings, "pipeline_sync_mode", True)
    (tmp_path / "vs2").mkdir()
    (tmp_path / "raw2").mkdir()
    (tmp_path / "proc2").mkdir()

    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app, headers={"X-Tenant-ID": "company_xyz"}) as c:
        yield c
    app.dependency_overrides.clear()


# ── 멀티테넌트 격리 ─────────────────────────────────────────

def test_multitenant_isolation(client_company_abc, client_other_tenant):
    """
    Scenario: Upload document to company_abc, company_xyz cannot retrieve it
    """
    # company_abc uploads recruitment document to HR001 project
    content_abc = b"2026 Recruitment Announcement - company_abc exclusive" * 5
    response_abc = client_company_abc.post(
        "/api/v1/documents/upload",
        files={"file": ("recruitment_abc.txt", io.BytesIO(content_abc), "text/plain")},
        data={
            "category_large": "인사",
            "category_mid": "채용",
            "project_code": "HR001",
        },
    )
    assert response_abc.status_code == 200
    doc_id_abc = response_abc.json()["data"]["doc_id"]

    # company_abc's document list: 1 document
    list_abc = client_company_abc.get("/api/v1/documents")
    assert list_abc.status_code == 200
    assert len(list_abc.json()["data"]) >= 1

    # company_xyz's document list: 0 documents (isolated)
    list_xyz = client_other_tenant.get("/api/v1/documents")
    assert list_xyz.status_code == 200
    assert len(list_xyz.json()["data"]) == 0

    # company_xyz search: no results (isolation enforced)
    search_xyz = client_other_tenant.post(
        "/api/v1/rag/search",
        json={"query": "recruitment announcement", "top_k": 5},
    )
    assert search_xyz.status_code == 200
    assert len(search_xyz.json()["data"]["used_chunks"]) == 0


# ── org_id 계층 검색 ─────────────────────────────────────────

def test_upload_with_org_id_team_level(client_company_abc):
    """
    Scenario: Upload document at team level (0101) -> saved with org_id="0101"
    """
    content = b"Sales Team 1 Recruitment Notice" * 5
    response = client_company_abc.post(
        "/api/v1/documents/upload",
        files={"file": ("team_recruit.txt", io.BytesIO(content), "text/plain")},
        data={
            "category_large": "인사",
            "category_mid": "채용",
            "project_code": "HR001",
        },
        headers={"X-Org-ID": "0101"},  # 영업부 1팀
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["doc_id"].startswith("doc_")


def test_upload_without_org_id_corporate_shared(client_company_abc):
    """
    Scenario: Upload without org_id -> Corporate shared document (org_id="")
    """
    content = b"Corporate Shared Policy Document" * 5
    response = client_company_abc.post(
        "/api/v1/documents/upload",
        files={"file": ("corporate_policy.txt", io.BytesIO(content), "text/plain")},
        data={
            "category_large": "규정",
            "category_mid": "취업규칙",
            "project_code": "POLICY001",
        },
        # X-Org-ID 헤더 없음 = 전사 공유
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_org_hierarchy_search_team_level():
    """
    Scenario: Team member (0102) searches
    - Can see: 0102 team docs + 0100 dept + "" corporate shared
    - Cannot see: 0101 team docs

    (Vector DB filtering verification needed with multiple org_id docs)
    """
    # TODO: Vector DB filter test needed — currently structure validation only
    pass


def test_org_hierarchy_search_department_level():
    """
    Scenario: Department manager (0100) searches
    - Can see: 0100 dept + "" corporate shared
    - Cannot see: subordinate team info (0101, 0102)

    (Should be implemented via query-time filtering)
    """
    # TODO: Vector DB filter test needed
    pass


# ── 프로젝트별 라우팅 ───────────────────────────────────────

def test_project_hr001_routes_to_vdb_hr_recruit_01(client_company_abc):
    """
    Scenario: HR001 project + recruitment category
    -> routes to vdb_hr_recruit_01
    """
    content = b"HR001 Project Recruitment Notice" * 5
    response = client_company_abc.post(
        "/api/v1/documents/upload",
        files={"file": ("hr001_recruit.txt", io.BytesIO(content), "text/plain")},
        data={
            "category_large": "인사",
            "category_mid": "채용",
            "project_code": "HR001",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["assigned_vector_db"] == "vdb_hr_recruit_01"


def test_project_hr002_routes_to_vdb_hr_payroll_01(client_company_abc):
    """
    Scenario: HR002 project + salary category
    -> routes to vdb_hr_payroll_01
    """
    content = b"HR002 Project Salary Policy" * 5
    response = client_company_abc.post(
        "/api/v1/documents/upload",
        files={"file": ("hr002_payroll.txt", io.BytesIO(content), "text/plain")},
        data={
            "category_large": "인사",
            "category_mid": "급여",
            "project_code": "HR002",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["assigned_vector_db"] == "vdb_hr_payroll_01"


def test_project_policy001_routes_to_vdb_policy_01(client_company_abc):
    """
    Scenario: POLICY001 project + employment rules category
    -> routes to vdb_policy_01
    """
    content = b"POLICY001 Employment Rules and Benefits" * 5
    response = client_company_abc.post(
        "/api/v1/documents/upload",
        files={"file": ("policy001.txt", io.BytesIO(content), "text/plain")},
        data={
            "category_large": "규정",
            "category_mid": "취업규칙",
            "project_code": "POLICY001",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["assigned_vector_db"] == "vdb_policy_01"


def test_project_tech001_routes_to_vdb_ontology_01(client_company_abc):
    """
    Scenario: TECH001 project + ontology category
    -> routes to vdb_ontology_01
    """
    content = b"TECH001 Ontology Standard and Guide" * 5
    response = client_company_abc.post(
        "/api/v1/documents/upload",
        files={"file": ("tech001_ontology.txt", io.BytesIO(content), "text/plain")},
        data={
            "category_large": "기술",
            "category_mid": "ontology",
            "project_code": "TECH001",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["assigned_vector_db"] == "vdb_ontology_01"


# ── 엔드-투-엔드 시나리오 ──────────────────────────────────────

def test_e2e_scenario_1_team_upload_and_search(client_company_abc):
    """
    Scenario 1: Team-level upload and search
    1. Team 0101 uploads recruitment notice (HR001)
    2. Same team searches -> finds document
    """
    # Upload
    content = b"2026 New Graduate Recruitment - Development Team" * 10
    upload = client_company_abc.post(
        "/api/v1/documents/upload",
        files={"file": ("recruit.txt", io.BytesIO(content), "text/plain")},
        data={
            "category_large": "인사",
            "category_mid": "채용",
            "project_code": "HR001",
        },
        headers={"X-Org-ID": "0101"},
    )
    assert upload.status_code == 200

    # Search
    search = client_company_abc.post(
        "/api/v1/rag/search",
        json={"query": "New Graduate Recruitment", "top_k": 5},
        headers={"X-Org-ID": "0101"},
    )
    assert search.status_code == 200
    data = search.json()
    assert data["status"] == "success"
    assert "answer" in data["data"]


def test_e2e_scenario_3_corporate_shared_document(client_company_abc):
    """
    Scenario 3: Corporate shared document
    1. Upload corporate shared policy (no org_id)
    2. All organizations can search (team, dept, corporate)
    """
    # Upload (corporate shared)
    content = b"Company-wide Benefits Policy" * 10
    upload = client_company_abc.post(
        "/api/v1/documents/upload",
        files={"file": ("corporate_benefit.txt", io.BytesIO(content), "text/plain")},
        data={
            "category_large": "규정",
            "category_mid": "취업규칙",
            "project_code": "POLICY001",
        },
        # No X-Org-ID = corporate shared
    )
    assert upload.status_code == 200

    # Team member (0102) search
    search_team = client_company_abc.post(
        "/api/v1/rag/search",
        json={"query": "Benefits Policy", "top_k": 5},
        headers={"X-Org-ID": "0102"},
    )
    assert search_team.status_code == 200
    assert search_team.json()["status"] == "success"

    # Department manager (0100) search
    search_dept = client_company_abc.post(
        "/api/v1/rag/search",
        json={"query": "Benefits Policy", "top_k": 5},
        headers={"X-Org-ID": "0100"},
    )
    assert search_dept.status_code == 200
    assert search_dept.json()["status"] == "success"
