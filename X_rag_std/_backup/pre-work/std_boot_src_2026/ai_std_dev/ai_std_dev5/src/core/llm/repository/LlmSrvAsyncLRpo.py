import os
# [수정] 스레드 풀 방식이 아닌, 진짜 비동기 어댑터를 임포트합니다.
from core.utility.geminiAyncAdapter import call_gemini_sdk_async

class LlmSrvAsyncRepository:
    def __init__(self):
        # 환경변수에서 모델명을 가져옵니다.
        self._model = os.getenv("LLM_MODEL_NAME", "gemini-2.0-flash-lite")

    async def call_gemini(self, prompt: str) -> str:
        """
        [핵심 수정] 
        기존: ThreadPoolExecutor를 사용한 동기 함수의 비동기 래핑
        변경: 비동기 어댑터(geminiAyncAdapter)를 통한 직접적인 await 호출
        """
        # 스레드 풀 없이 직접 비동기 어댑터를 await 합니다.
        return await call_gemini_sdk_async(prompt, self._model)

    async def call_mock(self, prompt: str) -> str:
        """테스트용 Mock 응답 (비동기 규격 준수)"""
        return f"[MOCK-ASYNC] '{prompt[:10]}...'에 대한 테스트 응답입니다."