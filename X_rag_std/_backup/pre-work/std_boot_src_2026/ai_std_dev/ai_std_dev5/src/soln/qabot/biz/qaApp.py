ai_std_dev5/src/soln/qabot/app/qaApp.pyfrom fastapi import APIRouter
from soln.qabot.schemas.qaSch import QaRequest, QaResponse, IngestResponse
from soln.qabot.biz.qaBiz import QaBizService

router = APIRouter(prefix="/soln/qabot", tags=["Standard-Solution"])
biz = QaBizService()

@router.post("/admin/ingest", response_model=IngestResponse)
async def ingest_assets():
    """관리자: 지식 자산 적재 API"""
    return await biz.ingest_assets()

@router.post("/ask", response_model=QaResponse)
async def direct_qa(req: QaRequest):
    """사용자: RAG 기반 질문 답변 API"""
    return await biz.ask_with_rag(req)