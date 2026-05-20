from fastapi import APIRouter
# 비동기 비즈니스 및 스키마 임포트
from core.llm.biz.llmSrvAsyncBiz import LlmSrvServiceAsync
from core.llm.schemas.llmSrvSch import LlmRequest, LlmResponse

# 표준 Suffix 및 태그 설정
router = APIRouter(prefix="/core/llm", tags=["Standard-Async-Infrastructure"])
service = LlmSrvServiceAsync()

@router.post("/inference", response_model=LlmResponse)
async def direct_inference(req: LlmRequest):
    """
    [Full-Async] Soln(8002)의 요청을 받아 비동기로 추론 결과를 반환합니다.
    """
    # Biz 계층의 비동기 함수 호출 (await 필수)
    return await service.ask_llm(req)