from typing import AsyncIterator

from app.core.config import settings
from app.models.schemas import RetrievedChunk
from app.services.llm.base import LlmClientBase


class ClaudeLlmClient(LlmClientBase):
    """Anthropic Claude API 연동 — 스트리밍 및 일반 응답 모두 지원.
    LLM_PROVIDER=claude 로 활성화.
    """

    MODEL = "claude-sonnet-4-6"

    def __init__(self) -> None:
        import anthropic
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def _build_context(self, chunks: list[RetrievedChunk]) -> str:
        return "\n\n".join(
            f"[출처: {c.metadata.source_name}]\n{c.content}" for c in chunks[:5]
        )

    def generate_answer(self, query: str, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "관련 문서 근거를 찾지 못했습니다."
        context = self._build_context(chunks)
        message = self._client.messages.create(
            model=self.MODEL,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"다음 문서를 참고하여 질문에 답변하세요.\n\n{context}\n\n질문: {query}",
                }
            ],
        )
        return message.content[0].text

    async def stream_answer(
        self, query: str, chunks: list[RetrievedChunk]
    ) -> AsyncIterator[str]:
        if not chunks:
            yield "data: 관련 문서 근거를 찾지 못했습니다.\n\n"
            return
        context = self._build_context(chunks)
        with self._client.messages.stream(
            model=self.MODEL,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"다음 문서를 참고하여 질문에 답변하세요.\n\n{context}\n\n질문: {query}",
                }
            ],
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {text}\n\n"
