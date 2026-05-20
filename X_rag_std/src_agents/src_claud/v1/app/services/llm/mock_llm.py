from typing import AsyncGenerator

from app.models.schemas import RetrievedChunk
from app.services.llm.base import LlmClientBase


class MockLlmClient(LlmClientBase):
    """결정론적 더미 LLM — 외부 API 없이 동작 (개발/테스트용).
    Codex SimpleLlmClient와 동일 로직을 LlmClientBase ABC 위에 재구현.
    """

    def generate_answer(self, query: str, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "관련 문서 근거를 찾지 못했습니다."
        lines = [f"질문: {query}", "검색된 근거를 바탕으로 한 답변입니다."]
        for i, chunk in enumerate(chunks[:3], start=1):
            source = chunk.metadata.source_name
            page = f" p.{chunk.metadata.page_no}" if chunk.metadata.page_no else ""
            snippet = chunk.content[:220].strip()
            lines.append(f"{i}. {snippet} (출처: {source}{page})")
        return "\n".join(lines)

    async def stream_answer(
        self, query: str, chunks: list[RetrievedChunk]
    ) -> AsyncGenerator[str, None]:
        answer = self.generate_answer(query, chunks)
        for word in answer.split(" "):
            yield f"data: {word} \n\n"
