import hashlib
import math
import re


class HashEmbeddingService:
    """Deterministic local embedding for runnable demos and adapter tests.

    It keeps the retrieval boundary explicit while avoiding dependency on a
    hosted embedding API in this standalone agent workspace.
    """

    def __init__(self, dimension: int = 64) -> None:
        self.dimension = dimension

    def embed_text(self, text: str) -> list[float]:
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

    @staticmethod
    def cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right:
            return 0.0
        return sum(a * b for a, b in zip(left, right, strict=False))

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[\w가-힣]+", text.lower())

    @staticmethod
    def _normalize(vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
