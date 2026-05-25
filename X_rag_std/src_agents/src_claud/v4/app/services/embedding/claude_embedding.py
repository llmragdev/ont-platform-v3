import math

from app.core.config import settings
from app.services.embedding.base import EmbeddingService


class ClaudeEmbeddingService(EmbeddingService):
    """Voyage AI 임베딩 API 연동 — voyageai 패키지 사용 (운영 환경).
    EMBEDDING_PROVIDER=claude 로 활성화.
    """

    MODEL = "voyage-3"

    def __init__(self, dimension: int = 1024) -> None:
        import voyageai
        self._client = voyageai.Client(api_key=settings.anthropic_api_key)
        self.dimension = dimension

    def embed_text(self, text: str, tenant_id: str = "") -> list[float]:
        result = self._client.embed([text], model=self.MODEL)
        vector = result.embeddings[0]
        return self._normalize(vector[: self.dimension])

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        return sum(x * y for x, y in zip(a, b, strict=False))

    @staticmethod
    def _normalize(vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            return vector
        return [v / norm for v in vector]
