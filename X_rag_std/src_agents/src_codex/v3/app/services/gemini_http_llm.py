import httpx
from collections.abc import AsyncGenerator

from app.core.config import settings
from app.models.schemas import RetrievedChunk


class GeminiHttpLlmClient:
    """LLM client for the central Gemini gateway."""

    def __init__(self) -> None:
        if not settings.llm_gateway_url:
            raise RuntimeError("LLM_GATEWAY_URL is required for gemini_http LLM.")
        base_url = settings.llm_gateway_url.rstrip("/")
        self.generate_url = f"{base_url}/api/v1/generate"
        self.stream_url = f"{base_url}/api/v1/generate/stream"

    def generate_answer(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        tenant_id: str,
    ) -> str:
        if not chunks:
            return "관련 문서 근거를 찾지 못했습니다."
        response = httpx.post(
            self.generate_url,
            json={
                "prompt": self._build_prompt(query, chunks),
                "tenant_id": tenant_id,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()["answer"]

    async def stream_answer(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        tenant_id: str,
    ) -> AsyncGenerator[str, None]:
        if not chunks:
            yield "data: 관련 문서 근거를 찾지 못했습니다.\n\n"
            yield "data: [DONE]\n\n"
            return
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                self.stream_url,
                json={
                    "prompt": self._build_prompt(query, chunks),
                    "tenant_id": tenant_id,
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        yield line + "\n\n"

    @staticmethod
    def _build_prompt(query: str, chunks: list[RetrievedChunk]) -> str:
        context = "\n\n".join(
            f"[출처: {chunk.metadata.source_name}]\n{chunk.content}"
            for chunk in chunks[:5]
        )
        return f"다음 문서를 참고하여 질문에 답변하세요.\n\n{context}\n\n질문: {query}"
