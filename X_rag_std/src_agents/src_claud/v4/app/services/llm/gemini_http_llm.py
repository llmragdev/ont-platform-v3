from typing import AsyncIterator

import httpx

from app.core.config import settings
from app.models.schemas import RetrievedChunk
from app.services.llm.base import LlmClientBase


class GeminiHttpLlmClient(LlmClientBase):
    """LLM Gateway를 통한 Gemini LLM 호출 — RAG ↔ LLM 서버 분리 구조."""

    def __init__(self) -> None:
        if not settings.llm_gateway_url:
            raise RuntimeError("LLM_GATEWAY_URL 이 설정되지 않았습니다.")
        base = settings.llm_gateway_url.rstrip("/")
        self._generate_url = f"{base}/api/v1/generate"
        self._stream_url = f"{base}/api/v1/generate/stream"

    def _build_context_chunks(self, chunks: list[RetrievedChunk]) -> list[dict]:
        return [
            {
                "content": c.content,
                "source_name": c.metadata.source_name,
                "page_no": c.metadata.page_no,
            }
            for c in chunks[:5]
        ]

    def generate_answer(
        self, query: str, chunks: list[RetrievedChunk], tenant_id: str = ""
    ) -> str:
        if not chunks:
            return "관련 문서 근거를 찾지 못했습니다."
        resp = httpx.post(
            self._generate_url,
            json={
                "query": query,
                "context_chunks": self._build_context_chunks(chunks),
                "tenant_id": tenant_id,
                "stream": False,
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json()["answer"]

    async def stream_answer(
        self, query: str, chunks: list[RetrievedChunk], tenant_id: str = ""
    ) -> AsyncIterator[str]:
        if not chunks:
            yield "data: 관련 문서 근거를 찾지 못했습니다.\n\n"
            return
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                self._stream_url,
                json={
                    "query": query,
                    "context_chunks": self._build_context_chunks(chunks),
                    "tenant_id": tenant_id,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data:") and not line.endswith("[DONE]"):
                        yield line + "\n\n"
