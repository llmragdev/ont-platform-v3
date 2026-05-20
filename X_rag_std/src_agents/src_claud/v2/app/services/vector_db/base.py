from abc import ABC, abstractmethod

from app.models.schemas import RetrievedChunk


class VectorDbAdapter(ABC):
    @abstractmethod
    def add_documents(self, chunks: list[dict], metadata: list[dict]) -> None: ...

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict | None = None,
    ) -> list[dict]: ...

    @abstractmethod
    def delete_by_doc_id(self, doc_id: str) -> bool: ...

    @abstractmethod
    def to_retrieved_chunk(self, record: dict) -> RetrievedChunk: ...
