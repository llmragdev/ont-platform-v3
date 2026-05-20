from time import perf_counter
from collections.abc import AsyncGenerator

from sqlalchemy.orm import Session

from app.models.schemas import (
    DebugInfo,
    RagSearchData,
    RagSearchFilter,
    RagSearchRequest,
    RagSearchResponse,
    RetrievedChunk,
)
from app.repositories.dialog_repository import DialogRepository
from app.services.providers import get_embedding_service, get_llm_client
from app.services.vector_adapters import LocalJsonVectorDbAdapter
from app.services.vector_router import VectorDbRouter


class RagSearchService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedding_service = get_embedding_service()
        self.router = VectorDbRouter(self.embedding_service)
        self.llm_client = get_llm_client()
        self.dialog_repository = DialogRepository(db)

    def search(
        self,
        request: RagSearchRequest,
        company_id: str = "default",
    ) -> RagSearchResponse:
        started = perf_counter()
        filters = request.filters or RagSearchFilter()
        adapter = self.router.get_adapter(
            category_mid=filters.category_mid,
            vector_db_id=filters.vector_db_id,
        )
        query_vector = self._embed_query(request.query, company_id)
        raw_candidates = adapter.search(
            query_vector=query_vector,
            top_k=max(request.top_k, 1),
            filters=self._adapter_filters(filters, company_id),
        )
        candidate_chunks = self._to_retrieved_chunks(adapter, raw_candidates)
        used_chunks = self._select_used_chunks(candidate_chunks, request.top_k)
        answer = self.llm_client.generate_answer(request.query, used_chunks, company_id=company_id)
        self.dialog_repository.save(request.query, answer, used_chunks, company_id=company_id)

        debug_info = None
        if request.debug_mode:
            elapsed_ms = int((perf_counter() - started) * 1000)
            debug_info = DebugInfo(
                execution_time_ms=elapsed_ms,
                candidate_chunks=candidate_chunks,
            )

        return RagSearchResponse(
            status="success",
            data=RagSearchData(
                query=request.query,
                answer=answer,
                used_chunks=used_chunks,
                debug_info=debug_info,
            ),
            error=None,
        )

    async def stream_search(
        self,
        request: RagSearchRequest,
        company_id: str = "default",
    ) -> AsyncGenerator[str, None]:
        filters = request.filters or RagSearchFilter()
        adapter = self.router.get_adapter(
            category_mid=filters.category_mid,
            vector_db_id=filters.vector_db_id,
        )
        query_vector = self._embed_query(request.query, company_id)
        raw_candidates = adapter.search(
            query_vector=query_vector,
            top_k=max(request.top_k, 1),
            filters=self._adapter_filters(filters, company_id),
        )
        candidate_chunks = self._to_retrieved_chunks(adapter, raw_candidates)
        used_chunks = self._select_used_chunks(candidate_chunks, request.top_k)
        async for chunk in self.llm_client.stream_answer(
            request.query,
            used_chunks,
            company_id=company_id,
        ):
            yield chunk

    @staticmethod
    def _adapter_filters(filters: RagSearchFilter, company_id: str) -> dict:
        values = filters.model_dump(exclude_none=True)
        values.pop("vector_db_id", None)
        values["company_id"] = company_id
        return values

    def _embed_query(self, query: str, company_id: str) -> list[float]:
        try:
            return self.embedding_service.embed_text(query, company_id=company_id)
        except TypeError:
            return self.embedding_service.embed_text(query)

    @staticmethod
    def _to_retrieved_chunks(
        adapter,
        raw_candidates: list[dict],
    ) -> list[RetrievedChunk]:
        if isinstance(adapter, LocalJsonVectorDbAdapter):
            return [adapter.to_retrieved_chunk(record) for record in raw_candidates]
        raise TypeError(f"Unsupported adapter conversion: {type(adapter).__name__}")

    @staticmethod
    def _select_used_chunks(candidates: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
        threshold = 0.05
        selected = [chunk for chunk in candidates if chunk.similarity_score >= threshold]
        if not selected and candidates:
            selected = candidates[:1]
        return selected[:top_k]
