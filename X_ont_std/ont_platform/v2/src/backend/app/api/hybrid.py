"""Hybrid Ask API 라우터 — supports query and legacy question."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict

from app.models.tenant_context import TenantContext
from app.services.query_planner import QueryPlannerService
from app.dependencies import get_tenant_context, get_query_planner_service

router = APIRouter(prefix="/api/hybrid", tags=["hybrid"])

class AskRequest(BaseModel):
    query: Optional[str] = None
    question: Optional[str] = None
    doc_ids: Optional[list[str]] = None
    override: Optional[Dict[str, Any]] = None

@router.post("/ask")
def ask_hybrid(
    request: AskRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    svc: QueryPlannerService = Depends(get_query_planner_service)
):
    query = request.query or request.question
    if not query:
        raise HTTPException(status_code=400, detail="query or question field is required.")

    # If override is present, use the legacy execute path to satisfy old tests
    if request.override:
        return svc.execute(query, ctx, doc_ids=request.doc_ids, override=request.override)

    # New Sprint 08 path
    response = svc.ask(query, ctx)
    
    # Return as dict to include both 'intent' and 'query_type' for compatibility
    res_dict = response.model_dump(mode="json") if hasattr(response, "model_dump") else response.dict()
    res_dict["query_type"] = res_dict["intent"]
    # Add flat results/count for frontend compatibility
    ontology_sources = [s for s in res_dict.get("sources", []) if s.get("source_type") == "ontology"]
    res_dict["results"] = [{"id": s["id"], "name": s.get("name"), "type": s.get("type")} for s in ontology_sources]
    res_dict["count"] = len(res_dict["results"])
    return res_dict


@router.post("/plan")
def plan_hybrid(
    request: AskRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    svc: QueryPlannerService = Depends(get_query_planner_service),
):
    query = request.query or request.question
    if not query:
        raise HTTPException(status_code=400, detail="query or question field is required.")
    try:
        plan = svc.classify_intent(query, ctx)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return plan.model_dump(mode="json") if hasattr(plan, "model_dump") else plan.dict()
