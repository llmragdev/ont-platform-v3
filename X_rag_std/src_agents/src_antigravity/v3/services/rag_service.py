from typing import Any
from sqlalchemy.orm import Session
from models.schemas import RagSearchRequest, RagSearchResponse, RagSearchData, RetrievedChunk, ChunkMetadata, DebugInfo
from services.vector_db import VectorDbRouter
from services.gateway_client import LlmGatewayClient
from models.db_models import DialogHistory
import time

class RagSearchService:
    def __init__(self, db: Session):
        self.db = db
        self.gateway = LlmGatewayClient()

    def process_search(self, request: RagSearchRequest, tenant_id: str, org_id: str = None) -> RagSearchResponse:
        start_time = time.time()
        
        # 1. 쿼리 임베딩 생성
        query_vector = self.gateway.embed_text(request.query, tenant_id=tenant_id)
        
        # 2. Vector DB 검색 (테넌트 및 조직 필터 적용)
        adapter = VectorDbRouter.get_adapter(
            vector_db_id=request.filters.vector_db_id if request.filters else None
        )
        
        search_results = adapter.search(
            query_vector=query_vector,
            tenant_id=tenant_id,
            org_id=org_id,
            top_k=request.top_k
        )
        
        # 3. 결과 조립 (RetrievedChunk 모델 변환)
        retrieved_chunks = []
        context_text = ""
        for i, res in enumerate(search_results):
            meta = res["metadata"]
            chunk = RetrievedChunk(
                chunk_id=f"{meta.get('doc_id', 'unknown')}#chunk{i}",
                content=res["content"],
                metadata=ChunkMetadata(**meta),
                similarity_score=res["score"]
            )
            retrieved_chunks.append(chunk)
            # 상위 3개 정도만 컨텍스트로 사용
            if i < 3:
                context_text += f"{res['content']}\n"
        
        # 4. LLM 답변 생성
        prompt = f"Context:\n{context_text}\n\nQuestion: {request.query}\nAnswer:"
        answer = self.gateway.generate_answer(prompt, tenant_id=tenant_id)
        
        # 5. 대화 이력 저장 (테넌트 포함)
        history = DialogHistory(
            tenant_id=tenant_id,
            query=request.query,
            answer=answer,
            used_chunks_meta=str([c.model_dump() for c in retrieved_chunks])
        )
        self.db.add(history)
        self.db.commit()
        
        execution_time = int((time.time() - start_time) * 1000)
        
        # 6. 응답 생성
        data = RagSearchData(
            query=request.query,
            answer=answer,
            used_chunks=retrieved_chunks,
            debug_info=DebugInfo(
                execution_time_ms=execution_time,
                candidate_chunks=retrieved_chunks if request.debug_mode else []
            )
        )
        
        return RagSearchResponse(status="success", data=data)

    async def process_search_stream(self, request: RagSearchRequest, tenant_id: str, org_id: str = None):
        """
        RAG 검색 결과를 스트리밍 방식으로 반환합니다.
        """
        # 1. 쿼리 임베딩 및 검색 (컨텍스트 구성은 비스트리밍과 동일)
        query_vector = self.gateway.embed_text(request.query, tenant_id=tenant_id)
        adapter = VectorDbRouter.get_adapter(
            vector_db_id=request.filters.vector_db_id if request.filters else None
        )
        search_results = adapter.search(
            query_vector=query_vector,
            tenant_id=tenant_id,
            org_id=org_id,
            top_k=request.top_k
        )
        
        context_text = ""
        for i, res in enumerate(search_results[:3]):
            context_text += f"{res['content']}\n"
            
        prompt = f"Context:\n{context_text}\n\nQuestion: {request.query}\nAnswer:"
        
        # 2. 스트리밍 답변 생성 및 반환
        async for chunk in self.gateway.stream_answer(prompt, tenant_id=tenant_id):
            yield chunk
