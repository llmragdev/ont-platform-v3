"""Dependencies for FastAPI routers — v3.0 with LlmClient injection."""
from __future__ import annotations

import os
from functools import lru_cache
from fastapi import Depends, Header

from app.models.tenant_context import TenantContext
from app.services.document import DocumentService
from app.services.llm_client import LlmClient
from app.services.ontology import OntologyService
from app.services.query_planner import QueryPlannerService
from app.services.vector_search import VectorSearchService
from app.services.embedding_service import CachedEmbeddings
from app.services.cache_service import QueryCacheService


@lru_cache(maxsize=1)
def get_llm_client() -> LlmClient:
    return LlmClient()


@lru_cache(maxsize=1)
def get_embeddings():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY1")
    if not api_key:
        return None
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        base_embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=api_key,
        )
        redis_url = os.getenv("REDIS_URL")
        return CachedEmbeddings(base_embeddings=base_embeddings, redis_url=redis_url)
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_query_cache_service() -> QueryCacheService:
    redis_url = os.getenv("REDIS_URL")
    return QueryCacheService(redis_url=redis_url)


def get_document_service() -> DocumentService:
    return DocumentService(embeddings=get_embeddings())


def get_ontology_service() -> OntologyService:
    return OntologyService()


def get_vector_search_service() -> VectorSearchService:
    return VectorSearchService(embeddings=get_embeddings())


def get_tenant_context(
    x_user_id: str = Header(default="default-user"),
    x_company_id: str = Header(default="default"),
    x_project_id: str = Header(default="proj-default"),
    x_role: str = Header(default="Viewer"),
) -> TenantContext:
    return TenantContext(
        user_id=x_user_id,
        company_id=x_company_id,
        project_id=x_project_id,
        role=x_role,
        permissions={},
    )


def get_query_planner_service(
    ont_svc: OntologyService = Depends(get_ontology_service),
    vec_svc: VectorSearchService = Depends(get_vector_search_service),
    llm: LlmClient = Depends(get_llm_client),
) -> QueryPlannerService:
    return QueryPlannerService(ontology_svc=ont_svc, vector_svc=vec_svc, llm_client=llm)
