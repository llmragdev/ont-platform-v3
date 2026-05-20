from fastapi import APIRouter
from core.llm.biz.llmSrvBiz import LlmSrvService
from core.llm.schemas.llmSrvSch import LlmRequest, LlmResponse

router = APIRouter(prefix="/core/llm", tags=["Standard-Infrastructure"])
service = LlmSrvService()

@router.post("/inference", response_model=LlmResponse)
async def direct_inference(req: LlmRequest):
    return await service.ask_llm(req)