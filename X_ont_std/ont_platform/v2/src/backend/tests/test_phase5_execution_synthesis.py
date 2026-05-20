"""Phase 5 checks for query execution and hybrid synthesis."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from app.models.tenant_context import TenantContext
from app.services.ontology import OntologyService
from app.services.query_planner import QueryPlannerService
from storage_config import get_project_root


class FakeVectorSearch:
    def search(self, query, ctx, k=3, shard_id=None):
        return [{
            "text": "Antigravity Inc is an active Seoul organization.",
            "score": 0.91,
            "doc_id": "doc-vector",
            "filename": "company.pdf",
            "page": 2,
            "shard_id": shard_id or "Vdefault",
        }]


@pytest.fixture()
def ctx(tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)
    return TenantContext("u-phase5", "phase5-co", "proj-phase5", "Admin", {})


def test_phase5_hybrid_pipeline_returns_data_evidence_trace_and_audit(ctx):
    ontology = OntologyService()
    ontology.upsert_entity("doc-ontology", {
        "type": "ORGANIZATION",
        "name": "Antigravity Inc",
        "properties": {"status": "active", "location": "Seoul"},
    }, ctx)

    planner = QueryPlannerService(ontology_svc=ontology, vector_svc=FakeVectorSearch())
    response = planner.ask("하이브리드 ORGANIZATION status: active 찾아줘", ctx)

    assert response.intent == "hybrid"
    assert response.structured_data["ontology"]["count"] == 1
    assert response.structured_data["vector"]["count"] == 1
    assert any(src["source_type"] == "ontology" for src in response.sources)
    assert any(src["source_type"] == "vector" for src in response.sources)
    assert any(e["citation"].startswith("ontology:") for e in response.evidence)
    assert any(e["citation"].startswith("document:doc-vector") for e in response.evidence)
    assert any("planner:" in item for item in response.trace)
    assert any("ontology.filter" in item for item in response.trace)
    assert any("vector.search" in item for item in response.trace)

    audit_path = get_project_root(ctx.company_id, ctx.project_id) / "audit_log.jsonl"
    events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert any(event["action"] == "COMPLETE_HYBRID_ASK" for event in events)


def test_phase5_filter_pipeline_uses_ontology_engine_count(ctx):
    ontology = OntologyService()
    ontology.upsert_entity("doc-filter", {
        "type": "PRODUCT",
        "name": "Widget Pro",
        "properties": {"status": "active"},
    }, ctx)
    ontology.upsert_entity("doc-filter", {
        "type": "PRODUCT",
        "name": "Widget Old",
        "properties": {"status": "inactive"},
    }, ctx)

    planner = QueryPlannerService(ontology_svc=ontology, vector_svc=FakeVectorSearch())
    response = planner.ask("PRODUCT status: active 목록", ctx)

    assert response.intent == "filter"
    assert response.structured_data["ontology"]["count"] == 1
    assert response.structured_data["ontology"]["items"][0]["name"] == "Widget Pro"
    assert "Found 1 ontology item" in response.answer
