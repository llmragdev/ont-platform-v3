from time import perf_counter

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.schemas import (
    BatchSearchRequest,
    BatchSearchResponse,
    BatchSearchResult,
    QueryExpansionRequest,
    QueryExpansionResponse,
    ExpandedQuery,
    RagSearchRequest,
    RagSearchResponse,
    RerankRequest,
    RerankResponse,
)
from app.services.rag_service import RagSearchService

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


@router.post("/search", response_model=RagSearchResponse)
def search(
    request_body: RagSearchRequest,
    x_tenant_id: str | None = Header(None, description="Tenant ID (required)"),
    x_org_id: str | None = Header(None, description="Organization ID (optional)"),
    db: Session = Depends(get_db),
):
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID is required")
    service = RagSearchService(db)
    return service.search(
        request_body,
        tenant_id=x_tenant_id,
        org_id=x_org_id,
    )


@router.post("/search/stream")
async def stream_search(
    request_body: RagSearchRequest,
    x_tenant_id: str | None = Header(None, description="Tenant ID (required)"),
    x_org_id: str | None = Header(None, description="Organization ID (optional)"),
    db: Session = Depends(get_db),
):
    """SSE 스트리밍 엔드포인트 — LLM 응답을 청크 단위로 클라이언트에 전송."""
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID is required")
    service = RagSearchService(db)
    return StreamingResponse(
        service.stream_search(
            request_body,
            tenant_id=x_tenant_id,
            org_id=x_org_id,
        ),
        media_type="text/event-stream",
    )


@router.post("/expand-query", response_model=QueryExpansionResponse)
def expand_query(
    request_body: QueryExpansionRequest,
    x_tenant_id: str | None = Header(None, description="Tenant ID (required)"),
):
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID is required")

    synonyms = {
        "정책": ["규정", "규칙", "지침"],
        "온톨로지": ["knowledge graph", "semantic web", "RDF"],
        "채용": ["신입사원", "지원자", "면접"],
        "급여": ["월급", "보너스", "수당"],
    }
    expanded = [ExpandedQuery(query=request_body.query, weight=1.0)]
    for term, values in synonyms.items():
        if term in request_body.query:
            expanded.extend(
                ExpandedQuery(query=value, weight=max(0.5, 0.9 - idx * 0.1))
                for idx, value in enumerate(values, start=1)
            )
            break
    if len(expanded) == 1:
        expanded.append(ExpandedQuery(query=f"{request_body.query} 관련 문서", weight=0.7))

    return QueryExpansionResponse(
        original_query=request_body.query,
        expanded_queries=expanded,
    )


@router.post("/rerank", response_model=RerankResponse)
def rerank(
    request_body: RerankRequest,
    x_tenant_id: str | None = Header(None, description="Tenant ID (required)"),
):
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID is required")

    query_terms = {term.lower() for term in request_body.query.split() if term.strip()}

    def score(chunk):
        content = chunk.content.lower()
        keyword_hits = sum(1 for term in query_terms if term in content)
        return chunk.similarity_score + keyword_hits

    chunks = sorted(request_body.chunks, key=score, reverse=True)
    return RerankResponse(chunks=chunks)


@router.post("/batch-search", response_model=BatchSearchResponse)
def batch_search(
    request_body: BatchSearchRequest,
    x_tenant_id: str | None = Header(None, description="Tenant ID (required)"),
    x_org_id: str | None = Header(None, description="Organization ID (optional)"),
    db: Session = Depends(get_db),
):
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID is required")

    started = perf_counter()
    service = RagSearchService(db)
    results = []
    for query in request_body.queries:
        response = service.search(query, tenant_id=x_tenant_id, org_id=x_org_id)
        chunks = response.chunks or []
        results.append(
            BatchSearchResult(
                query=query.query,
                chunks=chunks,
                total_chunks=len(chunks),
            )
        )

    return BatchSearchResponse(
        results=results,
        processing_time_ms=int((perf_counter() - started) * 1000),
    )
