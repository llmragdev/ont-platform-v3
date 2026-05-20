from app.models.schemas import RetrievedChunk
from collections.abc import AsyncGenerator


class SimpleLlmClient:
    """LLM boundary used by the RAG service.

    This standalone implementation is deterministic. In production the class can
    be replaced with an OpenAI, Claude, or internal LLM HTTP client without
    changing the retriever/router/adapter layers.
    """

    def generate_answer(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        tenant_id: str = "",
    ) -> str:
        if not chunks:
            return "관련 문서 근거를 찾지 못했습니다."

        lines = [f"질문: {query}", "검색된 근거를 바탕으로 한 답변입니다."]
        for index, chunk in enumerate(chunks[:3], start=1):
            source = chunk.metadata.source_name
            page = f" p.{chunk.metadata.page_no}" if chunk.metadata.page_no else ""
            snippet = chunk.content[:220].strip()
            lines.append(f"{index}. {snippet} (출처: {source}{page})")
        return "\n".join(lines)

    async def stream_answer(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        tenant_id: str = "",
    ) -> AsyncGenerator[str, None]:
        answer = self.generate_answer(query, chunks, tenant_id=tenant_id)
        for line in answer.splitlines():
            yield f"data: {line}\n\n"
        yield "data: [DONE]\n\n"
