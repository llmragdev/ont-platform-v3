from abc import ABC, abstractmethod


class EmbeddingService(ABC):
    @abstractmethod
    def embed_text(self, text: str, tenant_id: str = "") -> list[float]: ...

    @abstractmethod
    def cosine_similarity(self, a: list[float], b: list[float]) -> float: ...
