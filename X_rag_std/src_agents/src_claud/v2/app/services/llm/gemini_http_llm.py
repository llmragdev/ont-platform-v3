from typing import AsyncIterator

import httpx

from app.core.config import settings
from app.models.schemas import RetrievedChunk
from app.services.llm.base import LlmClientBase


class GeminiHttpLlmClient(LlmClientBase):
    """LLM Gateway를 통한 Gemini LLM 호출 — RAG ↔ LLM 서버 분리 구조.
    LLM_PROVIDER=gemini_http + LLM_GATEWAY_URL 설정 시 활성화.
    """

    def __init__(self) -> None:
        if not settings.llm_gateway_url:
            raise RuntimeError("LLM_GATEWAY_URL 이 설정되지 않았습니다.")
        base = settings.llm_gateway_url.rstrip("/")
        self._generate_url = f"{base}/api/v1/generate"
        self._stream_url = f"{base}/api/v1/generate/stream"

    def _build_prompt(self, query: str, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return query
        context = "\n\n".join(
            f"[출처: {c.metadata.source_name}]\n{c.content}" for c in chunks[:5]
        )
        return f"다음 문서를 참고하여 질문에 답변하세요.\n\n{context}\n\n질문: {query}"

    def generate_answer(self, query: str, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "관련 문서 근거를 찾지 못했습니다."
        resp = httpx.post(
            self._generate_url,
            json={"prompt": self._build_prompt(query, chunks)},
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json()["answer"]

    async def stream_answer(
        self, query: str, chunks: list[RetrievedChunk]
    ) -> AsyncIterator[str]:
        if not chunks:
            yield "data: 관련 문서 근거를 찾지 못했습니다.\n\n"
            return
        prompt = self._build_prompt(query, chunks)
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                self._stream_url,
                json={"prompt": prompt, "stream": True},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data:") and not line.endswith("[DONE]"):
                        yield line + "\n\n"
