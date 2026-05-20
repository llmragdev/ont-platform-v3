from time import perf_counter
from typing import AsyncGenerator

from sqlalchemy.orm import Session

from app.models.schemas import (
    DebugInfo,
    RagSearchData,
    RagSearchFilter,
    RagSearchRequest,
    RagSearchResponse,
    RetrievedChunk,
)
from app.repositories.audit_repo import AuditRepository
from app.repositories.dialog_repo import DialogRepository
from app.services.providers import get_embedding_service, get_llm_client
from app.services.router import VectorDbRouter


class RagSearchService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._embedding_service = get_embedding_service()
        self._router = VectorDbRouter(self._embedding_service)
        self._llm = get_llm_client()
        self._dialog_repo = DialogRepository(db)
        self._audit_repo = AuditRepository(db)

    def search(
        self, request: RagSearchRequest, company_id: str = "default"
    ) -> RagSearchResponse:
        started = perf_counter()
        filters = request.filters or RagSearchFilter()

        adapter = self._router.get_adapter(
            category_mid=filters.category_mid,
            vector_db_id=filters.vector_db_id,
        )
        query_vector = self._embedding_service.embed_text(request.query)
        raw = adapter.search(
            query_vector=query_vector,
            top_k=max(request.top_k * 2, 10),
            filters=self._adapter_filters(filters),
        )
        candidates = [adapter.to_retrieved_chunk(r) for r in raw]
        used = self._select_chunks(candidates, request.top_k)
        answer = self._llm.generate_answer(request.query, used)

        self._dialog_repo.save(request.query, answer, used, company_id)
        self._audit_repo.log("search", company_id=company_id, resource=request.query[:100])

        debug_info = None
        if request.debug_mode:
            elapsed = int((perf_counter() - started) * 1000)
            debug_info = DebugInfo(execution_time_ms=elapsed, candidate_chunks=candidates)

        return RagSearchResponse(
            status="success",
            data=RagSearchData(
                query=request.query,
                answer=answer,
                used_chunks=used,
                debug_info=debug_info,
            ),
            error=None,
        )

    async def stream_search(
        self, request: RagSearchRequest, company_id: str = "default"
    ) -> AsyncGenerator[str, None]:
        filters = request.filters or RagSearchFilter()
        adapter = self._router.get_adapter(
            category_mid=filters.category_mid,
            vector_db_id=filters.vector_db_id,
        )
        query_vector = self._embedding_service.embed_text(request.query)
        raw = adapter.search(
            query_vector=query_vector,
            top_k=max(request.top_k * 2, 10),
            filters=self._adapter_filters(filters),
        )
        candidates = [adapter.to_retrieved_chunk(r) for r in raw]
        used = self._select_chunks(candidates, request.top_k)

        self._audit_repo.log("stream_search", company_id=company_id, resource=request.query[:100])

        async for chunk_text in self._llm.stream_answer(request.query, used):
            yield chunk_text

    @staticmethod
    def _adapter_filters(filters: RagSearchFilter) -> dict:
        values = filters.model_dump(exclude_none=True)
        values.pop("vector_db_id", None)
        return values

    @staticmethod
    def _select_chunks(candidates: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
        threshold = 0.05
        selected = [c for c in candidates if c.similarity_score >= threshold]
        if not selected and candidates:
            selected = candidates[:1]
        return selected[:top_k]
