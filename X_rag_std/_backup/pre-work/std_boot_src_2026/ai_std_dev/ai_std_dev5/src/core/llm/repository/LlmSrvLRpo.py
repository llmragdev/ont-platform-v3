import os
from core.utility.geminiAdapter import call_gemini_sdk

class LlmSrvRepository:
    def __init__(self):
        self._model = os.getenv("LLM_MODEL_NAME", "gemini-2.0-flash-lite")

    def call_gemini(self, prompt: str):
        return call_gemini_sdk(prompt, self._model)

    def call_mock(self, prompt: str):
        return f"[MOCK] '{prompt[:10]}...'에 대한 테스트 응답입니다."