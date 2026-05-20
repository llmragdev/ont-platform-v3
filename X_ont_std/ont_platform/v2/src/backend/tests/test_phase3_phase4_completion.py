"""Phase 3/4 completion checks for document registry and schema-aware planner."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from app.models.query_intent import ActionType, EngineType, QueryAction, QueryPlan, IntentType
from app.models.tenant_context import TenantContext
from app.services.document import DocumentService
from app.services.ontology import OntologyService
from app.services.query_planner import QueryPlannerService
from storage_config import get_ontology_path, get_project_root, get_uploads_path


@pytest.fixture()
def ctx(tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)
    return TenantContext("u-phase", "phase-co", "proj-phase", "Admin", {})


def test_phase3_document_registry_and_audit_log(ctx, monkeypatch):
    svc = DocumentService(embeddings=None)
    monkeypatch.setattr(svc, "_vectorize", lambda *a, **kw: 2)

    entry = svc.upload(b"%PDF fake", "../phase.pdf", ctx, shard_id="5001")

    uploads = get_uploads_path(ctx.company_id, ctx.project_id)
    registry_path = uploads / "documents_registry.json"
    audit_path = get_project_root(ctx.company_id, ctx.project_id) / "audit_log.jsonl"

    assert (uploads / "phase.pdf").exists()
    assert registry_path.exists()
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert registry[entry["doc_id"]]["filename"] == "phase.pdf"
    assert registry[entry["doc_id"]]["shard_id"] == "5001"

    events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert any(e["action"] == "CREATE_DOCUMENT" and e["resource_id"] == entry["doc_id"] for e in events)

    other = TenantContext("u-other", "other-co", "proj-phase", "Admin", {})
    assert svc.list(other) == []


def test_phase4_schema_context_and_plan_validation(ctx):
    ontology_dir = get_ontology_path(ctx.company_id, ctx.project_id)
    ontology_dir.mkdir(parents=True, exist_ok=True)
    (ontology_dir / "domain_schema.json").write_text(
        json.dumps({
            "entity_types": [{"name": "Order", "properties": ["status", "amount"]}],
            "relation_types": [{"name": "PLACED_BY"}],
        }),
        encoding="utf-8",
    )

    planner = QueryPlannerService(ontology_svc=OntologyService())
    plan = planner.classify_intent("Order status: open 목록", ctx)

    assert plan.intent == IntentType.FILTER
    assert "Order" in plan.schema_context["entity_types"]
    assert plan.steps[0].params["entity_type"] == "Order"
    assert plan.steps[0].params["property_key"] == "status"

    invalid = QueryPlan(
        intent=IntentType.FILTER,
        reasoning="invalid property",
        schema_context=plan.schema_context,
        steps=[
            QueryAction(
                engine=EngineType.ONTOLOGY,
                action=ActionType.FILTER,
                params={"entity_type": "Order", "property_key": "unknown"},
            )
        ],
    )
    with pytest.raises(ValueError):
        planner.validate_plan(invalid)
