from app.services.embedding.base import EmbeddingService


class ClaudeEmbeddingService(EmbeddingService):
    """Voyage AI 임베딩 — v2에서 완전 구현 예정."""

    def __init__(self) -> None:
        raise NotImplementedError("ClaudeEmbeddingService는 v2에서 구현됩니다. EMBEDDING_PROVIDER=hash 를 사용하세요.")

    def embed_text(self, text: str) -> list[float]:  # pragma: no cover
        raise NotImplementedError

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:  # pragma: no cover
        raise NotImplementedError
