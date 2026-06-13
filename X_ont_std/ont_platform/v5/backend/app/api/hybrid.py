"""Hybrid Ask API v3.0 — with ontology_evidence and quality_metrics."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Any, Dict

from app.models.query_intent import SearchMode
from app.models.tenant_context import TenantContext
from app.services.query_planner import QueryPlannerService
from app.services.cache_service import QueryCacheService
from app.dependencies import get_tenant_context, get_query_planner_service, get_query_cache_service

router = APIRouter(prefix="/api/hybrid", tags=["hybrid"])
router_v5 = APIRouter(prefix="/api/v5/hybrid", tags=["hybrid-v5"])


class AskRequest(BaseModel):
    query: Optional[str] = None
    question: Optional[str] = None
    doc_ids: Optional[list[str]] = None
    override: Optional[Dict[str, Any]] = None


class AskRequestV5(BaseModel):
    query: Optional[str] = None
    question: Optional[str] = None
    search_mode: SearchMode = SearchMode.AUTO
    doc_ids: Optional[list[str]] = None
    override: Optional[Dict[str, Any]] = None


@router.post("/ask")
def ask_hybrid(
    request: AskRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    svc: QueryPlannerService = Depends(get_query_planner_service),
    cache_svc: QueryCacheService = Depends(get_query_cache_service),
):
    query = request.query or request.question
    if not query:
        raise HTTPException(status_code=400, detail="query or question field is required.")

    if request.override:
        return svc.execute(query, ctx, doc_ids=request.doc_ids, override=request.override)

    doc_scope = ",".join(sorted(request.doc_ids or []))
    cache_query = f"{query}::doc_ids={doc_scope}" if doc_scope else query

    # 1. Cache Lookup
    cached_res = cache_svc.get_query(cache_query, ctx.company_id)
    if cached_res:
        cached_res["cached"] = True
        return cached_res

    # 2. Exec and Cache write
    response = svc.ask(query, ctx, doc_ids=request.doc_ids)
    res_dict = response.model_dump(mode="json") if hasattr(response, "model_dump") else response.dict()
    res_dict["query_type"] = res_dict["intent"]
    ontology_sources = [s for s in res_dict.get("sources", []) if s.get("source_type") == "ontology"]
    res_dict["results"] = [{"id": s["id"], "name": s.get("name"), "type": s.get("type")}
                           for s in ontology_sources]
    res_dict["count"] = len(res_dict["results"])
    
    # Store with 5-minute TTL
    cache_svc.set_query(cache_query, ctx.company_id, res_dict, ttl_seconds=300)
    res_dict["cached"] = False
    return res_dict


@router_v5.post("/ask")
def ask_hybrid_v5(
    request: AskRequestV5,
    ctx: TenantContext = Depends(get_tenant_context),
    svc: QueryPlannerService = Depends(get_query_planner_service),
):
    query = request.query or request.question
    if not query:
        raise HTTPException(status_code=400, detail="query or question field is required.")

    if request.override:
        return svc.execute(query, ctx, doc_ids=request.doc_ids, override=request.override)

    response = svc.ask_v5(
        query,
        ctx,
        search_mode=request.search_mode,
        doc_ids=request.doc_ids,
    )
    res_dict = response.model_dump(mode="json") if hasattr(response, "model_dump") else response.dict()
    res_dict["query_type"] = res_dict["intent"]
    res_dict["cached"] = False
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
