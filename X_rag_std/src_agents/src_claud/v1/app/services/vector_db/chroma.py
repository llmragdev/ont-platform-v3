import uuid

from app.models.schemas import ChunkMetadata, RetrievedChunk
from app.services.vector_db.base import VectorDbAdapter


class ChromaAdapter(VectorDbAdapter):
    """ChromaDB HTTP 클라이언트 어댑터 (운영 환경용).
    v1이 목표했던 ChromaDB 연동을 VectorDbAdapter ABC 위에서 완성.
    engine_type=chroma 인 라우팅 규칙에서 자동 선택.
    """

    def __init__(
        self,
        vector_db_id: str,
        host: str = "localhost",
        port: int = 8000,
        collection_name: str = "default",
    ) -> None:
        import chromadb
        self.vector_db_id = vector_db_id
        self._client = chromadb.HttpClient(host=host, port=port)
        self._collection = self._client.get_or_create_collection(collection_name)

    def add_documents(self, chunks: list[dict], metadata: list[dict]) -> None:
        ids = [c.get("chunk_id", str(uuid.uuid4())) for c in chunks]
        documents = [c["content"] for c in chunks]
        self._collection.add(ids=ids, documents=documents, metadatas=metadata)

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict | None = None,
    ) -> list[dict]:
        where = {k: {"$eq": v} for k, v in (filters or {}).items()} or None
        results = self._collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where,
        )
        output = []
        for cid, doc, meta, dist in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            score = max(0.0, 1.0 - dist)
            output.append(
                {"chunk_id": cid, "content": doc, "metadata": meta, "similarity_score": score}
            )
        return output

    def delete_by_doc_id(self, doc_id: str) -> bool:
        results = self._collection.get(where={"doc_id": {"$eq": doc_id}})
        if not results["ids"]:
            return False
        self._collection.delete(ids=results["ids"])
        return True

    def to_retrieved_chunk(self, record: dict) -> RetrievedChunk:
        meta = record.get("metadata", {})
        return RetrievedChunk(
            chunk_id=record["chunk_id"],
            content=record["content"],
            similarity_score=record.get("similarity_score", 0.0),
            metadata=ChunkMetadata(
                source_name=meta.get("source_name", "unknown"),
                source_url=meta.get("source_url", ""),
                page_no=meta.get("page_no"),
                doc_id=meta.get("doc_id", ""),
                category_mid=meta.get("category_mid", ""),
                category_low=meta.get("category_low"),
            ),
        )
