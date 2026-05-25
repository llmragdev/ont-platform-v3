import hashlib
import math
import re

from app.services.embedding.base import EmbeddingService


class HashEmbeddingService(EmbeddingService):
    """SHA256 토큰 해싱 기반 결정론적 임베딩 — 외부 API 없이 동작 (개발/테스트용)."""

    def __init__(self, dimension: int = 64) -> None:
        self.dimension = dimension

    def embed_text(self, text: str, tenant_id: str = "") -> list[float]:
        vector = [0.0] * self.dimension
        tokens = self._tokenize(text)
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        return self._normalize(vector)

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        return sum(x * y for x, y in zip(a, b, strict=False))

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[\w가-힣]+", text.lower())

    @staticmethod
    def _normalize(vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            return vector
        return [v / norm for v in vector]
