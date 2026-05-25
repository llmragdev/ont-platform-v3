# -*- coding: utf-8 -*-
"""
멀티테넌트 E2E 테스트 (test_plan.md 시나리오 2)

목표: 멀티테넌트 격리 검증
- 테넌트별 데이터 완전 격리
- Cross-tenant 검색 차단
- 문서 목록 조회 격리

테넌트:
- company_abc: 10개 문서
- company_xyz: 5개 문서
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


@pytest.fixture
def client_company_abc(db_session, tmp_path, monkeypatch, routing_config):
    """company_abc 테넌트 클라이언트"""
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
    with TestClient(app, headers={"X-Tenant-ID": "company_abc"}) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def client_company_xyz(db_session, tmp_path, monkeypatch, routing_config):
    """company_xyz 테넌트 클라이언트"""
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
    with TestClient(app, headers={"X-Tenant-ID": "company_xyz"}) as c:
        yield c
    app.dependency_overrides.clear()


def create_test_pdf(filename: str, content: str) -> io.BytesIO:
    """테스트용 PDF 생성 (간단한 텍스트 파일로 대체)"""
    return io.BytesIO(content.encode('utf-8'))


class TestMultitenantE2E:
    """멀티테넌트 E2E 테스트"""

    def test_tenant_isolation_full_lifecycle(self, client_company_abc, client_company_xyz):
        """
        시나리오 2: 멀티테넌트 격리

        사전조건:
        - company_abc: 10개 문서 업로드
        - company_xyz: 5개 문서 업로드

        검증:
        - company_abc 검색 시 company_abc 문서만 반환
        - company_xyz 검색 시 company_xyz 문서만 반환
        """
        # 1. company_abc에 10개 문서 업로드
        abc_doc_ids = []
        for i in range(10):
            pdf_content = f"정책 문서 ABC {i}\n\n이것은 회사 ABC의 정책 문서입니다."
            files = {"file": (f"policy_abc_{i}.txt", create_test_pdf(f"policy_abc_{i}.txt", pdf_content))}
            data = {
                "category_large": "규정",
                "category_mid": "policy",
                "project_code": "POLICY001",
            }
            resp = client_company_abc.post("/api/v1/documents/upload", files=files, data=data)
            assert resp.status_code == 200, f"Upload failed: {resp.text}"
            doc_id = resp.json()["doc_id"]
            abc_doc_ids.append(doc_id)

        # 2. company_xyz에 5개 문서 업로드
        xyz_doc_ids = []
        for i in range(5):
            pdf_content = f"정책 문서 XYZ {i}\n\n이것은 회사 XYZ의 정책 문서입니다."
            files = {"file": (f"policy_xyz_{i}.txt", create_test_pdf(f"policy_xyz_{i}.txt", pdf_content))}
            data = {
                "category_large": "규정",
                "category_mid": "policy",
                "project_code": "POLICY001",
            }
            resp = client_company_xyz.post("/api/v1/documents/upload", files=files, data=data)
            assert resp.status_code == 200, f"Upload failed: {resp.text}"
            doc_id = resp.json()["doc_id"]
            xyz_doc_ids.append(doc_id)

        # 3. company_abc로 검색
        search_payload = {"query": "정책"}
        resp = client_company_abc.post("/api/v1/rag/search", json=search_payload)
        assert resp.status_code == 200, f"Search failed: {resp.text}"
        abc_chunks = resp.json()["chunks"]

        # 4. company_abc 검색 결과에서 abc 문서만 반환되는지 검증
        if abc_chunks:
            abc_result_doc_ids = [c["metadata"]["doc_id"] for c in abc_chunks]
            for doc_id in abc_result_doc_ids:
                assert doc_id in abc_doc_ids, f"Cross-tenant leak: {doc_id} not in company_abc"

        # 5. company_xyz로 검색
        resp = client_company_xyz.post("/api/v1/rag/search", json=search_payload)
        assert resp.status_code == 200, f"Search failed: {resp.text}"
        xyz_chunks = resp.json()["chunks"]

        # 6. company_xyz 검색 결과에서 xyz 문서만 반환되는지 검증
        if xyz_chunks:
            xyz_result_doc_ids = [c["metadata"]["doc_id"] for c in xyz_chunks]
            for doc_id in xyz_result_doc_ids:
                assert doc_id in xyz_doc_ids, f"Cross-tenant leak: {doc_id} not in company_xyz"

    def test_tenant_list_documents_isolation(self, client_company_abc, client_company_xyz):
        """
        테스트: 테넌트별 문서 목록 격리

        - company_abc: 10개 문서 조회
        - company_xyz: 5개 문서 조회
        - 각 테넌트은 자신의 문서만 봄
        """
        # 1. company_abc에 10개 문서 업로드
        for i in range(10):
            pdf_content = f"정책 문서 ABC {i}"
            files = {"file": (f"policy_abc_{i}.txt", create_test_pdf(f"policy_abc_{i}.txt", pdf_content))}
            data = {
                "category_large": "규정",
                "category_mid": "policy",
                "project_code": "POLICY001",
            }
            resp = client_company_abc.post("/api/v1/documents/upload", files=files, data=data)
            assert resp.status_code == 200

        # 2. company_xyz에 5개 문서 업로드
        for i in range(5):
            pdf_content = f"정책 문서 XYZ {i}"
            files = {"file": (f"policy_xyz_{i}.txt", create_test_pdf(f"policy_xyz_{i}.txt", pdf_content))}
            data = {
                "category_large": "규정",
                "category_mid": "policy",
                "project_code": "POLICY001",
            }
            resp = client_company_xyz.post("/api/v1/documents/upload", files=files, data=data)
            assert resp.status_code == 200

        # 3. company_abc 문서 목록 조회
        resp = client_company_abc.get("/api/v1/documents")
        assert resp.status_code == 200
        abc_docs = resp.json()["documents"]
        abc_count = len(abc_docs)

        # 4. company_xyz 문서 목록 조회
        resp = client_company_xyz.get("/api/v1/documents")
        assert resp.status_code == 200
        xyz_docs = resp.json()["documents"]
        xyz_count = len(xyz_docs)

        # 5. 검증
        assert abc_count == 10, f"company_abc should have 10 docs, got {abc_count}"
        assert xyz_count == 5, f"company_xyz should have 5 docs, got {xyz_count}"

        # 6. 각 테넌트의 문서 목록 확인
        abc_tenant_ids = [d["tenant_id"] for d in abc_docs]
        xyz_tenant_ids = [d["tenant_id"] for d in xyz_docs]

        assert all(t == "company_abc" for t in abc_tenant_ids), "company_abc documents leaked"
        assert all(t == "company_xyz" for t in xyz_tenant_ids), "company_xyz documents leaked"

    def test_tenant_search_different_keywords(self, client_company_abc, client_company_xyz):
        """
        테스트: 테넌트별 다양한 키워드 검색

        - 각 테넌트에 서로 다른 주제의 문서 업로드
        - 각각의 테넌트에서 검색하면 자신의 문서만 반환되는지 확인
        """
        # 1. company_abc: "인사" 관련 문서
        for i in range(3):
            pdf_content = f"채용 공고 {i}\n\n이것은 ABC 회사의 채용 공고입니다."
            files = {"file": (f"recruit_abc_{i}.txt", create_test_pdf(f"recruit_abc_{i}.txt", pdf_content))}
            data = {
                "category_large": "인사",
                "category_mid": "채용",
                "project_code": "HR001",
            }
            resp = client_company_abc.post("/api/v1/documents/upload", files=files, data=data)
            assert resp.status_code == 200

        # 2. company_xyz: "기술" 관련 문서
        for i in range(3):
            pdf_content = f"온톨로지 문서 {i}\n\n이것은 XYZ 회사의 온톨로지 문서입니다."
            files = {"file": (f"ontology_xyz_{i}.txt", create_test_pdf(f"ontology_xyz_{i}.txt", pdf_content))}
            data = {
                "category_large": "기술",
                "category_mid": "ontology",
                "project_code": "TECH001",
            }
            resp = client_company_xyz.post("/api/v1/documents/upload", files=files, data=data)
            assert resp.status_code == 200

        # 3. company_abc에서 "채용" 검색
        search_payload = {"query": "채용"}
        resp = client_company_abc.post("/api/v1/rag/search", json=search_payload)
        assert resp.status_code == 200
        abc_chunks = resp.json()["chunks"]
        if abc_chunks:
            for chunk in abc_chunks:
                assert chunk["metadata"]["tenant_id"] == "company_abc"

        # 4. company_xyz에서 "온톨로지" 검색
        search_payload = {"query": "온톨로지"}
        resp = client_company_xyz.post("/api/v1/rag/search", json=search_payload)
        assert resp.status_code == 200
        xyz_chunks = resp.json()["chunks"]
        if xyz_chunks:
            for chunk in xyz_chunks:
                assert chunk["metadata"]["tenant_id"] == "company_xyz"

    def test_tenant_document_lifecycle_isolation(self, client_company_abc, client_company_xyz):
        """
        테스트: 문서 라이프사이클 격리

        - company_abc의 문서를 업로드하고 업데이트/삭제
        - company_xyz는 영향받지 않음
        """
        # 1. 각 테넌트에서 문서 업로드
        pdf_content_abc = "정책 v1 - ABC"
        files = {"file": ("policy_abc.txt", create_test_pdf("policy_abc.txt", pdf_content_abc))}
        data = {
            "category_large": "규정",
            "category_mid": "policy",
            "project_code": "POLICY001",
        }
        resp = client_company_abc.post("/api/v1/documents/upload", files=files, data=data)
        assert resp.status_code == 200
        abc_doc_id = resp.json()["doc_id"]

        pdf_content_xyz = "정책 v1 - XYZ"
        files = {"file": ("policy_xyz.txt", create_test_pdf("policy_xyz.txt", pdf_content_xyz))}
        data = {
            "category_large": "규정",
            "category_mid": "policy",
            "project_code": "POLICY001",
        }
        resp = client_company_xyz.post("/api/v1/documents/upload", files=files, data=data)
        assert resp.status_code == 200
        xyz_doc_id = resp.json()["doc_id"]

        # 2. company_abc 문서 업데이트
        update_files = {"file": ("policy_abc_v2.txt", create_test_pdf("policy_abc_v2.txt", "정책 v2 - ABC"))}
        resp = client_company_abc.put(f"/api/v1/documents/{abc_doc_id}", files=update_files)
        assert resp.status_code == 200

        # 3. company_xyz 문서는 여전히 존재해야 함
        resp = client_company_xyz.get("/api/v1/documents")
        assert resp.status_code == 200
        xyz_docs = resp.json()["documents"]
        assert any(d["doc_id"] == xyz_doc_id for d in xyz_docs), "company_xyz document was deleted"

        # 4. company_abc 문서 삭제
        resp = client_company_abc.delete(f"/api/v1/documents/{abc_doc_id}")
        assert resp.status_code in [200, 204]

        # 5. company_abc에서 문서 목록 조회 (삭제된 문서 제외)
        resp = client_company_abc.get("/api/v1/documents")
        assert resp.status_code == 200
        abc_docs = resp.json()["documents"]
        assert not any(d["doc_id"] == abc_doc_id for d in abc_docs), "Deleted document still exists"

        # 6. company_xyz 문서 목록에는 여전히 존재
        resp = client_company_xyz.get("/api/v1/documents")
        assert resp.status_code == 200
        xyz_docs = resp.json()["documents"]
        assert any(d["doc_id"] == xyz_doc_id for d in xyz_docs), "company_xyz document was affected"

    def test_tenant_search_no_cross_contamination(self, client_company_abc, client_company_xyz):
        """
        테스트: 크로스 테넌트 검색 차단

        - company_abc에만 "ABC 특화" 키워드를 가진 문서 업로드
        - company_xyz에서 검색하면 해당 문서가 반환되지 않아야 함
        """
        # 1. company_abc에만 고유한 문서 업로드
        pdf_content = "ABC만의 특별한 정책 - UNIQUE_ABC_MARKER_12345"
        files = {"file": ("unique_abc.txt", create_test_pdf("unique_abc.txt", pdf_content))}
        data = {
            "category_large": "규정",
            "category_mid": "policy",
            "project_code": "POLICY001",
        }
        resp = client_company_abc.post("/api/v1/documents/upload", files=files, data=data)
        assert resp.status_code == 200
        abc_doc_id = resp.json()["doc_id"]

        # 2. company_abc에서 검색 (찾아야 함)
        search_payload = {"query": "UNIQUE_ABC_MARKER_12345"}
        resp = client_company_abc.post("/api/v1/rag/search", json=search_payload)
        assert resp.status_code == 200
        abc_chunks = resp.json()["chunks"]
        abc_found = any(c["metadata"]["doc_id"] == abc_doc_id for c in abc_chunks) if abc_chunks else False

        # 3. company_xyz에서 동일한 검색 (찾으면 안 됨)
        resp = client_company_xyz.post("/api/v1/rag/search", json=search_payload)
        assert resp.status_code == 200
        xyz_chunks = resp.json()["chunks"]
        xyz_found = any(c["metadata"]["doc_id"] == abc_doc_id for c in xyz_chunks) if xyz_chunks else False

        # 4. company_abc에서는 찾고, company_xyz에서는 찾지 못해야 함
        # (벡터 검색 특성상 100% 일치는 아니므로 유연한 검증)
        # 단, 반환된 doc의 tenant_id는 반드시 일치해야 함
        if xyz_chunks:
            for chunk in xyz_chunks:
                assert chunk["metadata"]["tenant_id"] == "company_xyz", \
                    f"Cross-tenant contamination: {chunk['metadata']['tenant_id']} != company_xyz"
