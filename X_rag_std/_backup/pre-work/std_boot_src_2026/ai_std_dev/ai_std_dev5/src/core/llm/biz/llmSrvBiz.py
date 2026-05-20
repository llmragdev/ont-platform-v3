from core.llm.repository.LlmSrvLRpo import LlmSrvRepository
from core.llm.schemas.llmSrvSch import LlmRequest, LlmResponse

class LlmSrvService:
    def __init__(self):
        self.repo = LlmSrvRepository()

    async def ask_llm(self, req: LlmRequest) -> LlmResponse:
        try:
            if req.engine_type == 1:
                prompt_set = f"Role: {req.persona}\nContext: {req.context}\nTask: {req.prompt}"
                answer = self.repo.call_gemini(prompt_set)
                return LlmResponse(status="success", result=answer, model="Gemini", engine="Standard")
            else:
                answer = self.repo.call_mock(req.prompt)
                return LlmResponse(status="success", result=answer, model="Mock", engine="Test")
        except Exception as e:
            answer = self.repo.call_mock(f"Fallback due to: {str(e)}")
            return LlmResponse(status="warning", result=answer, model="Fallback", engine="Resilience")