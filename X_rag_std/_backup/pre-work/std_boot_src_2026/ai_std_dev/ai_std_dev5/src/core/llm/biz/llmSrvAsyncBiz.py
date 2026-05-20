# llmSrvBizAsync.py
import asyncio
from core.llm.repository.LlmSrvAsyncLRpo import LlmSrvAsyncRepository
from core.llm.schemas.llmSrvSch import LlmRequest, LlmResponse

class LlmSrvServiceAsync:
    def __init__(self):
        self.repo = LlmSrvAsyncRepository()

    async def ask_llm(self, req: LlmRequest) -> LlmResponse:
        try:
            if req.engine_type == 1:
                prompt_set = f"Role: {req.persona}\nContext: {req.context}\nTask: {req.prompt}"
                # repository의 비동기 메서드 호출
                answer = await self.repo.call_gemini(prompt_set)
                return LlmResponse(status="success", result=answer, model="Gemini", engine="Standard")
            else:
                answer = await self.repo.call_mock(req.prompt)
                return LlmResponse(status="success", result=answer, model="Mock", engine="Test")
        except Exception as e:
            # 예외 발생 시 fallback (비동기 mock)
            answer = await self.repo.call_mock(f"Fallback due to: {str(e)}")
            return LlmResponse(status="warning", result=answer, model="Fallback", engine="Resilience")