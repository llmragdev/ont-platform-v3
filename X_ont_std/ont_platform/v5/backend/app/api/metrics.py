"""Quality Metrics API v3.0 — fallback rate, no-answer rate."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_tenant_context
from app.models.tenant_context import TenantContext
from app.services.audit import list_audit_events

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/query")
def query_metrics(
    limit: int = 200,
    ctx: TenantContext = Depends(get_tenant_context),
):
    events = list_audit_events(ctx, limit=limit)
    ask_events = [e for e in events if e.get("action") == "COMPLETE_HYBRID_ASK"]

    total = len(ask_events)
    if total == 0:
        return {"total_queries": 0, "llm_used_rate": 0.0, "fallback_rate": 0.0,
                "by_intent": {}, "vector_hits_avg": 0.0, "ontology_hits_avg": 0.0}

    llm_used = sum(1 for e in ask_events if e.get("details", {}).get("llm_used"))
    intent_counts: dict[str, int] = {}
    vector_total = 0
    ontology_total = 0

    for e in ask_events:
        d = e.get("details", {})
        intent = d.get("intent", "unknown")
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
        vector_total += d.get("vector_count", 0)
        ontology_total += d.get("ontology_count", 0)

    return {
        "total_queries": total,
        "llm_used_rate": round(llm_used / total, 3),
        "fallback_rate": round((total - llm_used) / total, 3),
        "by_intent": intent_counts,
        "vector_hits_avg": round(vector_total / total, 2),
        "ontology_hits_avg": round(ontology_total / total, 2),
    }
