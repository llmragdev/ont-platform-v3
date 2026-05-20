import time
from typing import List
from models import RagSearchRequest, RagSearchResponse, RagSearchData, RetrievedChunk, ChunkMetadata, DebugInfo
from vector_db_adapter import VectorDbRouter

class RagService:
    @staticmethod
    def process_search(request: RagSearchRequest) -> RagSearchResponse:
        start_time = time.time()
        
        # 1. Routing & Adapter Initialization
        category = request.filters.category_mid if request.filters else "IT"
        adapter = VectorDbRouter.get_adapter_by_category(category)
        
        # 2. Retrieval (Mocking Embedding generation)
        query_vector = [0.1, 0.2, 0.3] # Dummy embedded vector
        raw_results = adapter.search(query_vector=query_vector, top_k=request.top_k)
        
        # Parse into Pydantic models
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
            
        # 3. LLM Generation (Mocked)
        # Here we pretend the LLM picked the first chunk to generate the answer
        used_chunks = [candidate_chunks[0]] if candidate_chunks else []
        answer = f"'{request.query}'에 대한 답변입니다. (Remote Retriever를 통해 분리된 LLM이 생성)"
        
        # 4. Response Assembly
        exec_time = int((time.time() - start_time) * 1000)
        
        debug_info = None
        if request.debug_mode:
            debug_info = DebugInfo(
                execution_time_ms=exec_time,
                candidate_chunks=candidate_chunks
            )
            
        data = RagSearchData(
            query=request.query,
            answer=answer,
            used_chunks=used_chunks,
            debug_info=debug_info
        )
        
        return RagSearchResponse(status="success", data=data)
