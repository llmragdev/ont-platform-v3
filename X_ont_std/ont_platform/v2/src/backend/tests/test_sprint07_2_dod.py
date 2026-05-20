"""Sprint 08 DoD 자동 테스트.

DoD:
  S08-D01  descriptive / filter 분류 가능
  S08-D02  filter 질문에서 entity_type / property_key / property_value 추출 or fallback
  S08-D03  OntologyService.filter_by_property — tenant scope JSON만 검색
  S08-D04  /api/hybrid/ask — filter 결과 구조화 응답
  S08-D05  타 company/project ontology 미검색
  S08-D06  Sprint 07 테스트 38개 계속 통과 (import 검증)
  S08-D07  (이 파일 통과 자체가 기록 기준)

실행:
    conda run -n claud_be python -m pytest tests/test_sprint08_dod.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from app.models.tenant_context import TenantContext
from app.services.ontology import OntologyService
from app.services.query_planner import QueryPlannerService


# ── 공통 픽스처 ───────────────────────────────────────────────────────────────

@pytest.fixture()
def ctx_acme(tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)
    return TenantContext("u-1", "acme", "proj-001", "Admin", {"can_edit_ontology": True})


@pytest.fixture()
def ctx_globex(tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)
    return TenantContext("u-2", "globex", "proj-002", "Admin", {})


@pytest.fixture()
def ont_svc():
    return OntologyService()


@pytest.fixture()
def planner(ont_svc):
    return QueryPlannerService(ontology_svc=ont_svc)


# ── S08-D01: descriptive / filter 분류 ───────────────────────────────────────

def test_d01_filter_keyword_classification(planner):
    """'목록', '모두' 같은 키워드 → filter 분류."""
    result = planner.classify("PRODUCT 유형의 항목 목록을 모두 보여줘")
    assert result["type"] == "filter"


def test_d01_descriptive_fallback(planner):
    """필터 키워드 없음 → descriptive 폴백."""
    result = planner.classify("온톨로지란 무엇인가요?")
    assert result["type"] == "descriptive"


def test_d01_classify_returns_required_keys(planner):
    """분류 결과에 필수 키 포함."""
    result = planner.classify("어떤 제품이 있나요?")
    for key in ("type", "entities", "operation", "property_key", "property_value", "entity_type"):
        assert key in result


# ── S08-D02: filter 파라미터 추출 or fallback ─────────────────────────────────

def test_d02_filter_with_override_full(planner, ctx_acme, ont_svc):
    """override로 property_key/value를 명시하면 filter_by_property 호출."""
    ont_svc.upsert_entity("doc-1", {
        "type": "PRODUCT", "name": "Widget Pro",
        "properties": {"category": "hardware"}
    }, ctx_acme)

    result = planner.execute(
        "하드웨어 제품 목록",
        ctx_acme,
        override={
            "type": "filter",
            "entity_type": "PRODUCT",
            "property_key": "category",
            "property_value": "hardware",
            "entities": [], "operation": "list",
        },
    )
    assert result["query_type"] == "filter"
    assert result["count"] >= 1
    assert any(e["name"] == "Widget Pro" for e in result["results"])


def test_d02_filter_fallback_to_name_search(planner, ctx_acme, ont_svc):
    """property_key/value 없으면 name_search fallback."""
    ont_svc.upsert_entity("doc-2", {"type": "PERSON", "name": "Alice"}, ctx_acme)

    result = planner.execute(
        "Alice 목록",
        ctx_acme,
        override={
            "type": "filter",
            "entity_type": None,
            "property_key": None,
            "property_value": None,
            "entities": [], "operation": "list",
        },
    )
    assert result["query_type"] == "filter"
    assert result.get("fallback") == "name_search"


# ── S08-D03: filter_by_property tenant scope 격리 ─────────────────────────────

def test_d03_filter_by_property_in_scope(ctx_acme, ont_svc):
    """자사 scope 내 엔티티만 반환."""
    ont_svc.upsert_entity("doc-x", {
        "type": "PRODUCT", "name": "Gadget",
        "properties": {"status": "active"}
    }, ctx_acme)

    result = ont_svc.filter_by_property(ctx_acme, "PRODUCT", "status", "active")
    assert len(result) >= 1
    assert all(e["type"] == "PRODUCT" for e in result)


def test_d03_filter_by_property_empty_other_type(ctx_acme, ont_svc):
    """entity_type 불일치 → 빈 결과."""
    ont_svc.upsert_entity("doc-x", {
        "type": "CONCEPT", "name": "RAG",
        "properties": {"domain": "AI"}
    }, ctx_acme)

    result = ont_svc.filter_by_property(ctx_acme, "PRODUCT", "domain", "AI")
    assert result == []


def test_d03_filter_fuzzy_match(ctx_acme, ont_svc):
    """속성값 fuzzy match (오타 허용)."""
    ont_svc.upsert_entity("doc-x", {
        "type": "ORGANIZATION", "name": "Acme Corp",
        "properties": {"industry": "manufacturing"}
    }, ctx_acme)

    result = ont_svc.filter_by_property(ctx_acme, "ORGANIZATION", "industry", "manufakturing")
    assert len(result) >= 1  # fuzzy 0.6 이상


def test_d03_filter_no_cross_project(ctx_acme, ctx_globex, ont_svc):
    """다른 project scope는 검색 안 됨."""
    ont_svc.upsert_entity("doc-x", {
        "type": "PRODUCT", "name": "SecretWidget",
        "properties": {"status": "active"}
    }, ctx_acme)

    result = ont_svc.filter_by_property(ctx_globex, "PRODUCT", "status", "active")
    assert result == []


# ── S08-D04: /api/hybrid/ask API 응답 구조 ────────────────────────────────────

def test_d04_hybrid_ask_filter_response(tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)

    from fastapi.testclient import TestClient
    from app.main import app, get_query_planner_service

    ont = OntologyService()
    ctx_seed = TenantContext("u", "acme", "proj-001", "Admin", {})
    ont.upsert_entity("doc-seed", {
        "type": "PRODUCT", "name": "Widget",
        "properties": {"color": "red"}
    }, ctx_seed)

    mock_planner = QueryPlannerService(ontology_svc=ont)
    app.dependency_overrides[get_query_planner_service] = lambda: mock_planner

    client = TestClient(app)
    resp = client.post(
        "/api/hybrid/ask",
        json={
            "question": "빨간 제품 목록",
            "override": {
                "type": "filter",
                "entity_type": "PRODUCT",
                "property_key": "color",
                "property_value": "red",
                "entities": [], "operation": "list",
            },
        },
        headers={"x-company-id": "acme", "x-project-id": "proj-001"},
    )
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["query_type"] == "filter"
    assert "results" in body
    assert "count" in body
    assert body["count"] >= 1


def test_d04_hybrid_ask_missing_question(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    resp = client.post("/api/hybrid/ask", json={})
    assert resp.status_code == 400


def test_d04_hybrid_ask_descriptive_structure(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app, get_query_planner_service

    mock_planner = QueryPlannerService(ontology_svc=OntologyService())
    app.dependency_overrides[get_query_planner_service] = lambda: mock_planner

    client = TestClient(app)
    resp = client.post(
        "/api/hybrid/ask",
        json={
            "question": "온톨로지란 무엇인가요?",
            "override": {"type": "descriptive", "entities": [], "operation": "explain",
                         "property_key": None, "property_value": None, "entity_type": None},
        },
    )
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["query_type"] == "descriptive"


# ── S08-D05: 타 company/project ontology 미검색 ──────────────────────────────

def test_d05_no_cross_company_via_planner(ctx_acme, ctx_globex, planner, ont_svc):
    """planner.execute가 ctx scope 밖 데이터에 접근 안 함."""
    ont_svc.upsert_entity("doc-secret", {
        "type": "PRODUCT", "name": "TopSecret",
        "properties": {"level": "classified"}
    }, ctx_acme)

    result = planner.execute(
        "classified 제품 목록",
        ctx_globex,
        override={
            "type": "filter",
            "entity_type": "PRODUCT",
            "property_key": "level",
            "property_value": "classified",
            "entities": [], "operation": "list",
        },
    )
    assert result["count"] == 0


# ── S08-D06: Sprint 07-1 테스트 39개 import 검증 ─────────────────────────────

def test_d06_sprint07_1_tests_importable():
    """Sprint 07-1 테스트 모듈이 여전히 import 가능함을 확인."""
    from tests import test_sprint07_1_dod  # noqa: F401
    from tests import test_storage_config  # noqa: F401
