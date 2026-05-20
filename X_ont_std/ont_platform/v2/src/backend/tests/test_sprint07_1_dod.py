"""Sprint 07 DoD 자동 테스트 (D01~D15).

실행:
    cd E:\\ontology_edu\\ont_platform\\src\\backend
    pytest tests/test_sprint07_dod.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from storage_config import (
    get_ontology_path,
    get_uploads_path,
    get_vector_db_path,
    get_vector_db_root,
    list_shard_paths,
)
from app.models.tenant_context import TenantContext
from app.services.ontology import OntologyService
from app.services.document import DocumentService
from app.services.vector_search import VectorSearchService


# ── 공통 픽스처 ───────────────────────────────────────────────────────────────

@pytest.fixture()
def ctx_acme(tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)
    return TenantContext(
        user_id="u-001",
        company_id="acme",
        project_id="proj-001",
        role="Admin",
        permissions={"can_edit_ontology": True, "can_upload_doc": True},
    )


@pytest.fixture()
def ctx_globex(tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)
    return TenantContext(
        user_id="u-002",
        company_id="globex",
        project_id="proj-002",
        role="Admin",
        permissions={},
    )


@pytest.fixture()
def ont_svc():
    return OntologyService()


@pytest.fixture()
def doc_svc():
    return DocumentService(embeddings=None)


@pytest.fixture()
def vsearch_svc():
    return VectorSearchService(embeddings=None)


# ── D01: storage_config.py 경로 함수만으로 경로 결정 ──────────────────────────

def test_d01_path_factory(tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)

    uploads = get_uploads_path("acme", "proj-001")
    vector = get_vector_db_path("acme", "proj-001", "default")
    ontology = get_ontology_path("acme", "proj-001")

    assert str(uploads).startswith(str(tmp_path))
    assert str(vector).startswith(str(tmp_path))
    assert str(ontology).startswith(str(tmp_path))


# ── D02: uploads/ 저장 경로 ───────────────────────────────────────────────────

def test_d02_upload_path(ctx_acme, tmp_path):
    expected = tmp_path / "acme" / "proj-001" / "uploads"
    assert get_uploads_path("acme", "proj-001") == expected


# ── D03: vector_db/V{shard_id}/ Chroma 경로 ──────────────────────────────────

def test_d03_vector_db_shard_path(ctx_acme, tmp_path):
    p = get_vector_db_path("acme", "proj-001", "default")
    assert p == tmp_path / "acme" / "proj-001" / "vector_db" / "Vdefault"

    p2 = get_vector_db_path("acme", "proj-001", "5001")
    assert p2 == tmp_path / "acme" / "proj-001" / "vector_db" / "V5001"


# ── D04: ontology/ 저장 ───────────────────────────────────────────────────────

def test_d04_ontology_path_and_save(ctx_acme, ont_svc):
    entity = {"type": "PRODUCT", "name": "Widget"}
    result = ont_svc.upsert_entity("doc-aaa", entity, ctx_acme)

    saved = ont_svc._load("doc-aaa", ctx_acme)
    assert any(e["id"] == result["id"] for e in saved["entities"])

    ont_file = get_ontology_path("acme", "proj-001") / "doc-aaa.json"
    assert ont_file.exists()


# ── D05: company 간 물리 격리 ─────────────────────────────────────────────────

def test_d05_physical_isolation(ctx_acme, ctx_globex, ont_svc):
    ont_svc.upsert_entity("doc-secret", {"type": "PERSON", "name": "Alice"}, ctx_acme)

    # globex 컨텍스트로 acme 문서 조회 → 빈 결과
    result = ont_svc.list_entities("doc-secret", ctx_globex)
    assert result == []


# ── D06: V-ID 지정 검색 + 전체 샤드 순회 ─────────────────────────────────────

def test_d06_shard_search_specific(ctx_acme, vsearch_svc, tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)

    # 샤드 디렉토리 없으면 빈 결과
    results = vsearch_svc.search("test", ctx_acme, shard_id="5001")
    assert results == []


def test_d06_shard_search_all(ctx_acme, vsearch_svc, tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)

    # 샤드 없으면 빈 결과
    results = vsearch_svc.search("test", ctx_acme)
    assert results == []


def test_d06_list_shard_paths(ctx_acme, tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)

    vdb_root = get_vector_db_root("acme", "proj-001")
    (vdb_root / "Vdefault").mkdir(parents=True)
    (vdb_root / "V5001").mkdir()

    paths = list_shard_paths("acme", "proj-001")
    names = [p.name for p in paths]
    assert "Vdefault" in names
    assert "V5001" in names


# ── D07: OntologyService CRUD ─────────────────────────────────────────────────

def test_d07_entity_crud(ctx_acme, ont_svc):
    e = ont_svc.upsert_entity("doc-x", {"type": "CONCEPT", "name": "RAG"}, ctx_acme)
    assert e["id"].startswith("E")

    entities = ont_svc.list_entities("doc-x", ctx_acme)
    assert len(entities) == 1

    ok = ont_svc.delete_entity("doc-x", e["id"], ctx_acme)
    assert ok
    assert ont_svc.list_entities("doc-x", ctx_acme) == []


def test_d07_relationship_crud(ctx_acme, ont_svc):
    e1 = ont_svc.upsert_entity("doc-x", {"type": "PERSON", "name": "Bob"}, ctx_acme)
    e2 = ont_svc.upsert_entity("doc-x", {"type": "ORGANIZATION", "name": "Acme"}, ctx_acme)

    rel = ont_svc.add_relationship("doc-x", {
        "from_id": e1["id"], "relation": "WORKS_AT", "to_id": e2["id"]
    }, ctx_acme)
    assert rel["id"].startswith("R")

    rels = ont_svc.list_relationships("doc-x", ctx_acme)
    assert len(rels) == 1

    ok = ont_svc.delete_relationship("doc-x", rel["id"], ctx_acme)
    assert ok


# ── D08: DocumentService upload/vectorize (임베딩 없이 경로만 검증) ─────────

def test_d08_upload_creates_registry(ctx_acme, doc_svc, tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)

    # 임베딩 없이 _vectorize를 mock
    monkeypatch.setattr(doc_svc, "_vectorize", lambda *a, **kw: 3)

    result = doc_svc.upload(b"%PDF fake", "test.pdf", ctx_acme)

    assert result["doc_id"].startswith("doc-")
    assert result["chunk_count"] == 3
    assert result["company_id"] == "acme"
    assert result["project_id"] == "proj-001"

    uploads_dir = get_uploads_path("acme", "proj-001")
    assert (uploads_dir / "test.pdf").exists()

    docs = doc_svc.list(ctx_acme)
    assert len(docs) == 1
    assert docs[0]["doc_id"] == result["doc_id"]


def test_d08_delete_removes_registry(ctx_acme, doc_svc, tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)
    monkeypatch.setattr(doc_svc, "_vectorize", lambda *a, **kw: 2)
    monkeypatch.setattr(doc_svc, "_delete_from_chroma", lambda *a, **kw: None)

    result = doc_svc.upload(b"%PDF fake", "del.pdf", ctx_acme)
    ok = doc_svc.delete(result["doc_id"], ctx_acme)

    assert ok
    assert doc_svc.list(ctx_acme) == []


# ── D09: VectorSearchService (임베딩 없이 경로 로직만) ───────────────────────

def test_d09_search_empty_when_no_shards(ctx_acme, vsearch_svc, tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)

    result = vsearch_svc.search("query", ctx_acme)
    assert result == []


def test_d09_health(ctx_acme, vsearch_svc, tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)

    h = vsearch_svc.health(ctx_acme)
    assert "shard_count" in h
    assert h["shard_count"] == 0


# ── D10: TenantContext 주입 ───────────────────────────────────────────────────

def test_d10_tenant_context_fields():
    ctx = TenantContext(
        user_id="u-1",
        company_id="acme",
        project_id="proj-001",
        role="Admin",
        permissions={"can_edit_ontology": True},
    )
    assert ctx.can("can_edit_ontology") is True
    assert ctx.can("nonexistent") is False


def test_d10_assert_can_raises():
    ctx = TenantContext("u", "co", "pr", "Viewer", {})
    with pytest.raises(PermissionError):
        ctx.assert_can("can_upload_doc")


# ── D11: app_context 없이 서비스 단독 실행 ────────────────────────────────────

def test_d11_services_independent_of_app_context():
    """app_context를 import하지 않고 세 서비스 모두 인스턴스화 가능."""
    import sys
    assert "app.app_context" not in sys.modules
    assert "app_context" not in sys.modules

    OntologyService()
    DocumentService(embeddings=None)
    VectorSearchService(embeddings=None)


# ── D12: POST /api/documents/upload (FastAPI TestClient) ─────────────────────

def test_d12_upload_api(tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)

    from fastapi.testclient import TestClient
    from app.main import app, get_document_service

    mock_svc = DocumentService(embeddings=None)
    monkeypatch.setattr(mock_svc, "_vectorize", lambda *a, **kw: 5)

    app.dependency_overrides[get_document_service] = lambda: mock_svc
    client = TestClient(app)

    resp = client.post(
        "/api/documents/upload",
        files={"file": ("sample.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        headers={"x-company-id": "acme", "x-project-id": "proj-001"},
    )
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["doc_id"].startswith("doc-")
    assert body["company_id"] == "acme"


# ── D13: GET /api/documents company/project 필터 ─────────────────────────────

def test_d13_list_documents_api(tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)

    from fastapi.testclient import TestClient
    from app.main import app, get_document_service

    mock_svc = DocumentService(embeddings=None)
    monkeypatch.setattr(mock_svc, "_vectorize", lambda *a, **kw: 1)

    app.dependency_overrides[get_document_service] = lambda: mock_svc
    client = TestClient(app)

    ctx_acme = TenantContext("u", "acme", "proj-001", "Admin", {})
    mock_svc.upload(b"%PDF fake", "a.pdf", ctx_acme)

    resp = client.get(
        "/api/documents",
        headers={"x-company-id": "acme", "x-project-id": "proj-001"},
    )
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) == 1
    assert docs[0]["company_id"] == "acme"


# ── D14: POST /api/ontology/{doc_id}/entities ─────────────────────────────────

def test_d14_create_entity_api(tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)

    from fastapi.testclient import TestClient
    from app.main import app, get_ontology_service

    mock_svc = OntologyService()
    app.dependency_overrides[get_ontology_service] = lambda: mock_svc
    client = TestClient(app)

    resp = client.post(
        "/api/ontology/doc-001/entities",
        json={"type": "PRODUCT", "name": "Widget"},
        headers={"x-company-id": "acme", "x-project-id": "proj-001"},
    )
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"].startswith("E")
    assert body["name"] == "Widget"


# ── D15: /api/workflow/* 엔드포인트 smoke test ───────────────────────────────
#
# Sprint 07-3 완료 후 실제 엔드포인트로 교체됨 (2026-05-13).

def test_d15_app_starts_correctly():
    """v2.0 FastAPI 앱이 정상 기동되는지 확인."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["version"] == "2.0.0"


def test_d15_workflow_queue_endpoint_exists():
    """GET /api/workflow/queue 엔드포인트가 200을 반환한다."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    resp = client.get(
        "/api/workflow/queue",
        headers={"x-company-id": "acme", "x-project-id": "proj-001", "x-role": "Admin"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "count" in body
