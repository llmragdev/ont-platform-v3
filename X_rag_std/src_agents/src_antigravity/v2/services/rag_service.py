import time
from typing import List
from sqlalchemy.orm import Session
from models.schemas import RagSearchRequest, RagSearchResponse, RagSearchData, RetrievedChunk, ChunkMetadata, DebugInfo
from services.vector_db import VectorDbRouter
from repositories.chat_repo import ChatRepository
from services.gateway_client import LlmGatewayClient

class RagSearchService:
    def __init__(self, db: Session):
        self.db = db
        self.chat_repo = ChatRepository(db)

    def process_search(self, request: RagSearchRequest) -> RagSearchResponse:
        start_time = time.time()
        
        # 1. Routing (vector_db_id 1순위, category_mid 2순위)
        cat_mid = request.filters.category_mid if request.filters else None
        vdb_id = request.filters.vector_db_id if request.filters else None
        
        adapter = VectorDbRouter.get_adapter(category_mid=cat_mid, vector_db_id=vdb_id)
        
        # 2. Retrieval (Local JSON DB 검색)
        gateway = LlmGatewayClient()
        query_vector = gateway.embed_text(request.query)
        search_filters = {"category_mid": cat_mid} if cat_mid else None
        
        raw_results = adapter.search(
            query_vector=query_vector, 
            top_k=request.top_k,
            filters=search_filters
        )
        
        candidate_chunks: List[RetrievedChunk] = []
        for res in raw_results:
            meta = ChunkMetadata(**res["metadata"])
            chunk = RetrievedChunk(
                chunk_id=res["chunk_id"],
                content=res["content"],
                similarity_score=res["similarity_score"],
                metadata=meta
            )
            candidate_chunks.append(chunk)
            
        # 3. Remote Retriever 응답 구성
        used_chunks = candidate_chunks[:3] if candidate_chunks else []
        
        if not used_chunks:
            answer = "관련 문서 근거를 찾지 못했습니다."
        else:
            context = "\n\n".join([f"[출처: {c.metadata.source_name}]\n{c.content}" for c in used_chunks])
            prompt = f"다음 문서를 참고하여 질문에 답변하세요.\n\n{context}\n\n질문: {request.query}"
            answer = gateway.generate_answer(prompt)
        
        # 4. RDBMS에 질의 이력 및 사용된 청크 저장
        self.chat_repo.save_dialog(query=request.query, answer=answer, used_chunks=used_chunks)
        
        exec_time = int((time.time() - start_time) * 1000)
        debug_info = DebugInfo(execution_time_ms=exec_time, candidate_chunks=candidate_chunks) if request.debug_mode else None
            
        data = RagSearchData(
            query=request.query,
            answer=answer,
            used_chunks=used_chunks,
            debug_info=debug_info
        )
        
        return RagSearchResponse(status="success", data=data)
