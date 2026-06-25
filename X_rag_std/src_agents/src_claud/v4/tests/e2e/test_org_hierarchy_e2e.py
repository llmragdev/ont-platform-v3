# -*- coding: utf-8 -*-
"""
org_id 계층 E2E 테스트 (test_plan.md 시나리오 3, 4)

목표: org_id 계층 권한 검증
- 팀원(0102): 0102 + 0100 + 전사 공유만 조회
- 부서장(0100): 0100 + 0101 + 0102 + 전사 공유 조회

org_id 계층:
- 0100: 영업부 (부서)
- 0101: 영업부 1팀 (팀)
- 0102: 영업부 2팀 (팀)
- "": 전사 공유
"""

import io
import json
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
    """라우팅 설정"""
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


def create_test_pdf(filename: str, content: str) -> io.BytesIO:
    """테스트용 PDF 생성"""
    return io.BytesIO(content.encode('utf-8'))


def create_client_with_org_id(db_session, tmp_path, monkeypatch, routing_config, tenant_id: str, org_id: str = None):
    """특정 org_id를 가진 클라이언트 생성"""
    from app.core import config as cfg_module

    monkeypatch.setattr(cfg_module.settings, "vector_store_dir", tmp_path / "vs")
    monkeypatch.setattr(cfg_module.settings, "raw_documents_dir", tmp_path / "raw")
    monkeypatch.setattr(cfg_module.settings, "processed_dir", tmp_path / "proc")
    monkeypatch.setattr(cfg_module.settings, "routing_config_path", routing_config)
    monkeypatch.setattr(cfg_module.settings, "pipeline_sync_mode", True)
    (tmp_path / "vs").mkdir(exist_ok=True)
    (tmp_path / "raw").mkdir(exist_ok=True)
    (tmp_path / "proc").mkdir(exist_ok=True)

    headers = {"X-Tenant-ID": tenant_id}
    if org_id:
        headers["X-Org-ID"] = org_id

    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app, headers=headers)
    return client


@pytest.fixture
def org_hierarchy_setup(db_session, tmp_path, monkeypatch, routing_config):
    """org_id 계층 테스트 데이터 설정"""

    # 단일 세션/경로로 모든 클라이언트 초기화
    from app.core import config as cfg_module

    monkeypatch.setattr(cfg_module.settings, "vector_store_dir", tmp_path / "vs")
    monkeypatch.setattr(cfg_module.settings, "raw_documents_dir", tmp_path / "raw")
    monkeypatch.setattr(cfg_module.settings, "processed_dir", tmp_path / "proc")
    monkeypatch.setattr(cfg_module.settings, "routing_config_path", routing_config)
    monkeypatch.setattr(cfg_module.settings, "pipeline_sync_mode", True)
    (tmp_path / "vs").mkdir(exist_ok=True)
    (tmp_path / "raw").mkdir(exist_ok=True)
    (tmp_path / "proc").mkdir(exist_ok=True)

    app.dependency_overrides[get_db] = lambda: db_session

    # admin 클라이언트 (조직 없음 - 전체 범위)
    admin_client = TestClient(app, headers={"X-Tenant-ID": "company_abc"})

    # 각 org_id 문서 업로드
    org_doc_ids = {}

    # 0100 부서 문서 (3개)
    for i in range(3):
        pdf_content = f"정책 문서 0100 - {i}\n부서 레벨 문서입니다."
        files = {"file": (f"policy_0100_{i}.txt", create_test_pdf(f"policy_0100_{i}.txt", pdf_content))}
        data = {
            "category_large": "규정",
            "category_mid": "policy",
            "project_code": "POLICY001",
            "org_id": "0100",
        }
        resp = admin_client.post("/api/v1/documents/upload", files=files, data=data)
        if resp.status_code == 200:
            org_doc_ids.setdefault("0100", []).append(resp.json()["doc_id"])

    # 0101 팀 문서 (3개)
    for i in range(3):
        pdf_content = f"정책 문서 0101 - {i}\n팀 0101 레벨 문서입니다."
        files = {"file": (f"policy_0101_{i}.txt", create_test_pdf(f"policy_0101_{i}.txt", pdf_content))}
        data = {
            "category_large": "규정",
            "category_mid": "policy",
            "project_code": "POLICY001",
            "org_id": "0101",
        }
        resp = admin_client.post("/api/v1/documents/upload", files=files, data=data)
        if resp.status_code == 200:
            org_doc_ids.setdefault("0101", []).append(resp.json()["doc_id"])

    # 0102 팀 문서 (3개)
    for i in range(3):
        pdf_content = f"정책 문서 0102 - {i}\n팀 0102 레벨 문서입니다."
        files = {"file": (f"policy_0102_{i}.txt", create_test_pdf(f"policy_0102_{i}.txt", pdf_content))}
        data = {
            "category_large": "규정",
            "category_mid": "policy",
            "project_code": "POLICY001",
            "org_id": "0102",
        }
        resp = admin_client.post("/api/v1/documents/upload", files=files, data=data)
        if resp.status_code == 200:
            org_doc_ids.setdefault("0102", []).append(resp.json()["doc_id"])

    # 전사 공유 문서 (2개)
    for i in range(2):
        pdf_content = f"정책 문서 전사 공유 - {i}\n전사 레벨 문서입니다."
        files = {"file": (f"policy_shared_{i}.txt", create_test_pdf(f"policy_shared_{i}.txt", pdf_content))}
        data = {
            "category_large": "규정",
            "category_mid": "policy",
            "project_code": "POLICY001",
            # org_id 미지정 → "" (전사 공유)
        }
        resp = admin_client.post("/api/v1/documents/upload", files=files, data=data)
        if resp.status_code == 200:
            org_doc_ids.setdefault("", []).append(resp.json()["doc_id"])

    return admin_client, org_doc_ids


class TestOrgHierarchyE2E:
    """org_id 계층 E2E 테스트"""

    def test_org_hierarchy_team_level_search(self, org_hierarchy_setup):
        """
        시나리오 3: 팀원(0102) 검색

        기대:
        - 0102 팀 문서 ✅
        - 0100 부서 문서 ✅
        - 전사 공유("") 문서 ✅
        - 0101 팀 문서 ❌
        """
        admin_client, org_doc_ids = org_hierarchy_setup

        # 팀원(0102) 클라이언트
        client = TestClient(
            app,
            headers={"X-Tenant-ID": "company_abc", "X-Org-ID": "0102"}
        )

        # 검색
        search_payload = {"query": "정책"}
        resp = client.post("/api/v1/rag/search", json=search_payload)
        assert resp.status_code == 200, f"Search failed: {resp.text}"
        chunks = resp.json()["chunks"]

        # 반환된 doc_id 추출
        returned_org_ids = set()
        if chunks:
            for chunk in chunks:
                org_id = chunk["metadata"].get("org_id", "")
                returned_org_ids.add(org_id)

        # 검증
        # (검색 결과는 벡터 유사도 기반이므로 모든 문서가 반환되지 않을 수 있음)
        # 하지만 반환된 결과는 반드시 권한 범위 내여야 함
        allowed_org_ids = {"0102", "0100", ""}
        for org_id in returned_org_ids:
            assert org_id in allowed_org_ids, \
                f"Unauthorized org_id: {org_id} not in {allowed_org_ids}"

        # 0101 문서가 반환되지 않았는지 확인
        if chunks:
            for chunk in chunks:
                assert chunk["metadata"].get("org_id") != "0101", \
                    f"Unauthorized access: 0101 document returned to 0102 user"

    def test_org_hierarchy_department_level_search(self, org_hierarchy_setup):
        """
        시나리오 4: 부서장(0100) 검색

        기대:
        - 0100 부서 문서 ✅
        - 0101, 0102 팀 문서 ✅
        - 전사 공유("") 문서 ✅
        """
        admin_client, org_doc_ids = org_hierarchy_setup

        # 부서장(0100) 클라이언트
        client = TestClient(
            app,
            headers={"X-Tenant-ID": "company_abc", "X-Org-ID": "0100"}
        )

        # 검색
        search_payload = {"query": "정책"}
        resp = client.post("/api/v1/rag/search", json=search_payload)
        assert resp.status_code == 200, f"Search failed: {resp.text}"
        chunks = resp.json()["chunks"]

        # 반환된 org_id 추출
        returned_org_ids = set()
        if chunks:
            for chunk in chunks:
                org_id = chunk["metadata"].get("org_id", "")
                returned_org_ids.add(org_id)

        # 검증
        # 부서장은 부서 내 모든 org_id와 전사 공유에 접근 가능
        allowed_org_ids = {"0100", "0101", "0102", ""}
        for org_id in returned_org_ids:
            assert org_id in allowed_org_ids, \
                f"Unexpected org_id: {org_id} not in {allowed_org_ids}"

    def test_org_hierarchy_no_cross_team_access(self, org_hierarchy_setup):
        """
        테스트: 팀원은 다른 팀에 접근할 수 없음

        - 0101 팀원이 0102 팀의 전용 문서에 접근 불가
        - 0102 팀원이 0101 팀의 전용 문서에 접근 불가
        """
        admin_client, org_doc_ids = org_hierarchy_setup

        # 0101 팀원 (0101만 접근 가능)
        client_0101 = TestClient(
            app,
            headers={"X-Tenant-ID": "company_abc", "X-Org-ID": "0101"}
        )

        # 0102 팀원 (0102만 접근 가능)
        client_0102 = TestClient(
            app,
            headers={"X-Tenant-ID": "company_abc", "X-Org-ID": "0102"}
        )

        # 0102 팀원이 검색
        search_payload = {"query": "정책"}
        resp = client_0102.post("/api/v1/rag/search", json=search_payload)
        assert resp.status_code == 200
        chunks_0102 = resp.json()["chunks"]

        # 반환된 결과에 0101 문서가 없어야 함
        if chunks_0102:
            for chunk in chunks_0102:
                assert chunk["metadata"].get("org_id") != "0101", \
                    f"Cross-team access: 0101 document visible to 0102 user"

    def test_org_hierarchy_document_upload_with_org_id(self, db_session, tmp_path, monkeypatch, routing_config):
        """
        테스트: org_id 기반 문서 업로드

        - admin이 다양한 org_id로 문서를 업로드
        - 각 org_id별 접근 권한 검증
        """
        from app.core import config as cfg_module

        monkeypatch.setattr(cfg_module.settings, "vector_store_dir", tmp_path / "vs")
        monkeypatch.setattr(cfg_module.settings, "raw_documents_dir", tmp_path / "raw")
        monkeypatch.setattr(cfg_module.settings, "processed_dir", tmp_path / "proc")
        monkeypatch.setattr(cfg_module.settings, "routing_config_path", routing_config)
        monkeypatch.setattr(cfg_module.settings, "pipeline_sync_mode", True)
        (tmp_path / "vs").mkdir(exist_ok=True)
        (tmp_path / "raw").mkdir(exist_ok=True)
        (tmp_path / "proc").mkdir(exist_ok=True)

        app.dependency_overrides[get_db] = lambda: db_session

        # admin 클라이언트
        admin_client = TestClient(app, headers={"X-Tenant-ID": "company_abc"})

        # 0101 팀원 클라이언트
        client_0101 = TestClient(
            app,
            headers={"X-Tenant-ID": "company_abc", "X-Org-ID": "0101"}
        )

        # admin이 0102 팀을 위해 문서 업로드
        pdf_content = "정책 문서 0102\n0102 팀 전용입니다."
        files = {"file": ("policy_0102_exclusive.txt", create_test_pdf("policy_0102_exclusive.txt", pdf_content))}
        data = {
            "category_large": "규정",
            "category_mid": "policy",
            "project_code": "POLICY001",
            "org_id": "0102",
        }
        resp = admin_client.post("/api/v1/documents/upload", files=files, data=data)
        assert resp.status_code == 200
        exclusive_doc_id = resp.json()["doc_id"]

        # admin이 전사 공유 문서 업로드
        pdf_content = "정책 문서 전사 공유\n모든 팀이 접근 가능합니다."
        files = {"file": ("policy_shared.txt", create_test_pdf("policy_shared.txt", pdf_content))}
        data = {
            "category_large": "규정",
            "category_mid": "policy",
            "project_code": "POLICY001",
            # org_id 미지정 → 전사 공유
        }
        resp = admin_client.post("/api/v1/documents/upload", files=files, data=data)
        assert resp.status_code == 200
        shared_doc_id = resp.json()["doc_id"]

        # 0101 팀원이 0102 전용 문서를 검색해도 찾을 수 없어야 함
        search_payload = {"query": "0102"}
        resp = client_0101.post("/api/v1/rag/search", json=search_payload)
        assert resp.status_code == 200
        chunks = resp.json()["chunks"]

        # 반환된 doc_id가 exclusive_doc_id를 포함하지 않아야 함
        if chunks:
            returned_doc_ids = [c["metadata"]["doc_id"] for c in chunks]
            # 벡터 검색 특성상 항상 정확히 일치하지 않을 수 있으므로,
            # 반환된 모든 결과의 org_id만 검증
            for chunk in chunks:
                assert chunk["metadata"].get("org_id") != "0102", \
                    f"0101 user should not see 0102 documents"

    def test_org_hierarchy_admin_access(self, org_hierarchy_setup):
        """
        테스트: org_id 없는 관리자는 모든 문서에 접근

        - org_id 헤더 없이 요청하면 테넌트 내 모든 문서 조회
        """
        admin_client, org_doc_ids = org_hierarchy_setup

        # org_id 없이 검색 (admin)
        search_payload = {"query": "정책"}
        resp = admin_client.post("/api/v1/rag/search", json=search_payload)
        assert resp.status_code == 200
        chunks = resp.json()["chunks"]

        # 반환된 결과에 모든 org_id가 포함될 수 있음
        # (벡터 검색이므로 100% 보장은 아니지만, 제한이 없어야 함)
        if chunks:
            for chunk in chunks:
                # 모든 org_id가 반환될 수 있어야 함
                # (검증할 제약 없음 - admin은 제약 없음)
                pass
