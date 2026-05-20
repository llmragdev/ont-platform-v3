from abc import ABC, abstractmethod

from app.models.schemas import RetrievedChunk


class VectorDbAdapter(ABC):
    @abstractmethod
    def add_documents(
        self,
        chunks: list[dict],
        metadata: list[dict],
        embeddings: list[list[float]],
    ) -> None:
        """청크와 메타데이터를 벡터 DB에 저장.
        embeddings는 외부 임베딩 서비스로 사전 생성해서 전달 — 어댑터 내부에서 임베딩 생성 금지.
        """
        ...

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict | None = None,
        org_id: str | None = None,
    ) -> list[dict]:
        """유사도 검색.
        filters에 tenant_id 반드시 포함.
        org_id가 있으면 해당 조직 문서 + 전사 공유 문서(org_id="")를 함께 반환.
        """
        ...

    @abstractmethod
    def delete_by_doc_id(self, doc_id: str) -> bool: ...

    @abstractmethod
    def to_retrieved_chunk(self, record: dict) -> RetrievedChunk: ...
