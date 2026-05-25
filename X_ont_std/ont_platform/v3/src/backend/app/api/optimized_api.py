from __future__ import annotations

import time
from typing import Dict

from fastapi import APIRouter, Depends
from app.dependencies import get_query_cache_service, get_tenant_context
from app.models.tenant_context import TenantContext
from app.services.cache_service import QueryCacheService
from app.services.graph_index import GraphIndex
from app.services.sparql_service import SPARQLService

router = APIRouter(prefix="/api/rdf", tags=["rdf"])


def _make_cache_key(uri: str, depth: int, limit: int) -> str:
    return f"rdf:neighborhood:{uri}:{depth}:{limit}"


@router.get("/neighborhood-optimized/{uri:path}")
async def get_neighborhood_optimized(
    uri: str,
    limit: int = 100,
    depth: int = 1,
    ctx: TenantContext = Depends(get_tenant_context),
    cache: QueryCacheService = Depends(get_query_cache_service),
) -> Dict[str, object]:
    """최적화된 RDF 이웃 탐색 API"""
    tenant_domain = f"{ctx.company_id}:{ctx.project_id}"
    cache_key = _make_cache_key(uri, depth, limit)
    cached = cache.get_query(cache_key, tenant_domain)
    if cached is not None:
        response = dict(cached)
        response["cached"] = True
        return response

    start_time = time.time()
    sparql_service = SPARQLService(domain_id=ctx.project_id or "default")
    triples = [t.to_tuple() for t in sparql_service.engine.store.get_all_triples()]
    graph_index = GraphIndex(triples=triples)

    neighborhood = graph_index.lookup_neighborhood(uri, depth=depth, limit=limit)
    response = {
        "centerNode": neighborhood["centerNode"],
        "nodes": neighborhood["nodes"],
        "edges": neighborhood["edges"],
        "hasMore": neighborhood["has_more"],
        "processingTimeMs": int((time.time() - start_time) * 1000),
        "cached": False,
    }
    cache.set_query(cache_key, tenant_domain, response, ttl_seconds=300)
    return response
