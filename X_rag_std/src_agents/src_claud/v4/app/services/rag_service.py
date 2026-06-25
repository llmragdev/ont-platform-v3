from time import perf_counter
from typing import AsyncGenerator

from sqlalchemy.orm import Session

from app.core.cache import VectorDBCache
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
        # 벡터DB 검색 결과 캐시 (1시간 TTL)
        self._search_cache = VectorDBCache(ttl_seconds=3600)

    def search(
        self,
        request: RagSearchRequest,
        tenant_id: str,
        org_id: str | None = None,
    ) -> RagSearchResponse:
        started = perf_counter()
        filters = request.filters or RagSearchFilter()
        top_k = request.limit or request.top_k

        # 캐시 키 생성
        cache_key = self._search_cache._get_cache_key(
            query=request.query,
            filters={
                "category_mid": filters.category_mid,
                "vector_db_id": filters.vector_db_id,
                "tenant_id": tenant_id,
            }
        )

        # 캐시 확인
        cached_result = self._search_cache.get(cache_key)
        from_cache = False

        if cached_result:
            # 캐시 히트: 벡터DB 검색 스킵
            candidates = cached_result.get("candidates", [])
            from_cache = True
        else:
            # 캐시 미스: 벡터DB 검색 수행
            query_vector = self._embedding_service.embed_text(request.query, tenant_id=tenant_id)
            if filters.category_mid or filters.vector_db_id:
                adapter = self._router.get_adapter(
                    category_mid=filters.category_mid,
                    vector_db_id=filters.vector_db_id,
                )
                raw = adapter.search(
                    query_vector=query_vector,
                    top_k=max(top_k * 2, 10),
                    filters=self._build_tenant_filters(filters, tenant_id),
                    org_id=org_id,
                )
                candidates = [adapter.to_retrieved_chunk(r) for r in raw]
            else:
                inferred_category = self._infer_category_mid(request.query)
                if inferred_category:
                    adapter = self._router.get_adapter(category_mid=inferred_category)
                    raw = adapter.search(
                        query_vector=query_vector,
                        top_k=max(top_k * 2, 10),
                        filters=self._build_tenant_filters(filters, tenant_id),
                        org_id=org_id,
                    )
                    candidates = [adapter.to_retrieved_chunk(r) for r in raw]
                else:
                    candidates = []
                    vector_db_ids = [rule.vector_db_id for rule in self._router.rules] or ["vdb_default_01"]
                    for vector_db_id in dict.fromkeys(vector_db_ids):
                        adapter = self._router.get_adapter(vector_db_id=vector_db_id)
                        raw = adapter.search(
                            query_vector=query_vector,
                            top_k=max(top_k * 2, 10),
                            filters=self._build_tenant_filters(filters, tenant_id),
                            org_id=org_id,
                        )
                        candidates.extend(adapter.to_retrieved_chunk(r) for r in raw)
                    candidates.sort(key=lambda c: c.similarity_score, reverse=True)

            # 캐시 저장
            self._search_cache.set(cache_key, {"candidates": candidates})

        used = self._select_chunks(candidates, top_k)
        answer = self._llm.generate_answer(request.query, used, tenant_id=tenant_id)

        self._dialog_repo.save(request.query, answer, used, tenant_id, org_id)
        self._audit_repo.log("search", tenant_id=tenant_id, resource=request.query[:100])

        debug_info = None
        if request.debug_mode:
            elapsed = int((perf_counter() - started) * 1000)
            cache_stats = self._search_cache.stats()
            debug_info = DebugInfo(
                execution_time_ms=elapsed,
                candidate_chunks=candidates,
                metadata={
                    "from_cache": from_cache,
                    "cache_hit_rate": cache_stats.get("hit_rate"),
                }
            )

        return RagSearchResponse(
            status="success",
            data=RagSearchData(
                query=request.query,
                answer=answer,
                used_chunks=used,
                debug_info=debug_info,
            ),
            chunks=used,
            total_chunks=len(used),
            error=None,
        )

    async def stream_search(
        self,
        request: RagSearchRequest,
        tenant_id: str,
        org_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        filters = request.filters or RagSearchFilter()
        adapter = self._router.get_adapter(
            category_mid=filters.category_mid,
            vector_db_id=filters.vector_db_id,
        )
        query_vector = self._embedding_service.embed_text(request.query, tenant_id=tenant_id)
        raw = adapter.search(
            query_vector=query_vector,
            top_k=max(request.top_k * 2, 10),
            filters=self._build_tenant_filters(filters, tenant_id),
            org_id=org_id,
        )
        candidates = [adapter.to_retrieved_chunk(r) for r in raw]
        used = self._select_chunks(candidates, request.top_k)

        self._audit_repo.log("stream_search", tenant_id=tenant_id, resource=request.query[:100])

        async for chunk_text in self._llm.stream_answer(request.query, used, tenant_id=tenant_id):
            yield chunk_text

    @staticmethod
    def _build_tenant_filters(filters: RagSearchFilter, tenant_id: str) -> dict:
        """tenant_id를 항상 강제 주입. vector_db_id는 라우팅에만 쓰므로 제외."""
        values = filters.model_dump(exclude_none=True)
        values.pop("vector_db_id", None)
        values["tenant_id"] = tenant_id
        return values

    @staticmethod
    def _select_chunks(candidates: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
        threshold = 0.05
        selected = [c for c in candidates if c.similarity_score >= threshold]
        if not selected and candidates:
            selected = candidates[:1]
        return selected[:top_k]

    @staticmethod
    def _infer_category_mid(query: str) -> str | None:
        lowered = query.lower()
        technical_terms = {
            "온톨로지", "knowledge graph", "semantic web", "rdf", "semantic relationship",
            "ai", "nlp", "자연언어처리", "머신러닝", "벡터", "임베딩", "텍스트 분석",
            "데이터", "모델", "학습", "성능",
        }
        hr_terms = {
            "신입사원", "채용", "지원자", "합격", "면접", "급여", "월급", "보너스",
            "복리후생", "퇴직금", "직급", "부서", "승진", "업무", "평가", "성과",
            "교육", "복무", "수당", "세금", "권리",
        }
        policy_terms = {
            "취업규칙", "휴가", "근무시간", "보안", "규정", "정책", "조직", "문서",
            "규칙", "지침", "근태",
        }
        if any(term in lowered for term in technical_terms):
            return "ontology"
        if any(term in lowered for term in hr_terms):
            return "급여" if any(term in lowered for term in {"급여", "월급", "보너스", "수당", "세금"}) else "채용"
        if any(term in lowered for term in policy_terms):
            return "policy"
        return None
