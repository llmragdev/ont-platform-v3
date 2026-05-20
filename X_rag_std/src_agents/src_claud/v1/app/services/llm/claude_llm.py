from app.services.llm.base import LlmClientBase


class ClaudeLlmClient(LlmClientBase):
    """Anthropic Claude API — v2에서 완전 구현 예정."""

    def __init__(self) -> None:
        raise NotImplementedError("ClaudeLlmClient는 v2에서 구현됩니다. LLM_PROVIDER=mock 을 사용하세요.")

    def generate_answer(self, query: str, chunks) -> str:  # pragma: no cover
        raise NotImplementedError

    async def stream_answer(self, query: str, chunks):  # pragma: no cover
        raise NotImplementedError
        yield  # AsyncGenerator 시그니처 유지
