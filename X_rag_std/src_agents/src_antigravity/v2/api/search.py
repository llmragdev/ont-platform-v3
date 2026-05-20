import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from models.schemas import RagSearchRequest, RagSearchResponse
from services.rag_service import RagSearchService

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])

@router.post("/search", response_model=RagSearchResponse)
async def search_rag(
    request: RagSearchRequest,
    db: Session = Depends(get_db)
):
    search_service = RagSearchService(db)
    # 스레드 풀에서 RAG 프로세스(VectorDB 검색 -> LLM 결과 조립 -> RDBMS 저장) 실행
    return await asyncio.to_thread(search_service.process_search, request)
