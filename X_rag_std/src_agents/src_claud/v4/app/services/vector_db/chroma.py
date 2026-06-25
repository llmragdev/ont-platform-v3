import uuid

from app.models.schemas import ChunkMetadata, RetrievedChunk
from app.services.vector_db.base import VectorDbAdapter


def _build_where_clause(filters: dict, org_id: str | None) -> dict | None:
    """tenant_id 필터 + org 격리 OR 조건을 Chroma where 절로 변환.

    공유 문서(org_id=="")는 모든 팀/부서 검색에 포함.
    """
    conditions: list[dict] = []

    for k, v in filters.items():
        conditions.append({k: {"$eq": v}})

    if org_id:
        is_dept_level = len(org_id) == 4 and org_id[2:] == "00"
        if is_dept_level:
            dept_code = org_id[:2]
            conditions.append(
                {"$or": [{"dept_code": {"$eq": dept_code}}, {"org_id": {"$eq": ""}}]}
            )
        else:
            conditions.append(
                {"$or": [{"org_id": {"$eq": org_id}}, {"org_id": {"$eq": ""}}]}
            )

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


class ChromaAdapter(VectorDbAdapter):
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

    def add_documents(
        self,
        chunks: list[dict],
        metadata: list[dict],
        embeddings: list[list[float]],
    ) -> None:
        ids = [c.get("chunk_id", str(uuid.uuid4())) for c in chunks]
        documents = [c["content"] for c in chunks]
        # tags(배열)와 None 값은 ChromaDB scalar 제약으로 제외
        vector_metadata = [
            {k: v for k, v in m.items() if k != "tags" and v is not None}
            for m in metadata
        ]
        self._collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=vector_metadata,
        )

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict | None = None,
        org_id: str | None = None,
    ) -> list[dict]:
        where = _build_where_clause(filters or {}, org_id)
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
                chunk_type=meta.get("chunk_type", "text"),
                tenant_id=meta.get("tenant_id", ""),
                org_id=meta.get("org_id") or None,
                dept_code=meta.get("dept_code"),
                vector_db_id=meta.get("vector_db_id", self.vector_db_id),
                created_at=meta.get("created_at"),
            ),
        )
