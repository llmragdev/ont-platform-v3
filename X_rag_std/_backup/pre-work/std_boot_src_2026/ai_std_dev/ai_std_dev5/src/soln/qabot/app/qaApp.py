from fastapi import APIRouter, Depends
from soln.qabot.biz.qaBiz import QaBizService
from soln.qabot.schemas.qaSch import QaRequest

router = APIRouter()
biz = QaBizService()

@router.post("/admin/ingest")
async def ingest_assets():
    # qaBiz의 메서드 명칭과 일치하도록 수정
    return await biz.ingest_assets()

@router.post("/ask")
async def direct_qa(req: QaRequest):
    return await biz.ask_with_rag(req)