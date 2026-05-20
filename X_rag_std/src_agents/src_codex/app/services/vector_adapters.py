from abc import ABC, abstractmethod
from pathlib import Path
import json

from app.core.errors import VectorDbConnectionError
from app.models.schemas import ChunkMetadata, RetrievedChunk
from app.services.embeddings import HashEmbeddingService


class BaseVectorDbAdapter(ABC):
    @abstractmethod
    def add_documents(self, chunks: list[dict], metadata: list[dict]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict | None = None,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def delete_by_doc_id(self, doc_id: str) -> bool:
        raise NotImplementedError


class LocalJsonVectorDbAdapter(BaseVectorDbAdapter):
    def __init__(self, vector_db_id: str, store_path: Path, embedding_service: HashEmbeddingService) -> None:
        self.vector_db_id = vector_db_id
        self.store_path = store_path
        self.embedding_service = embedding_service
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

    def add_documents(self, chunks: list[dict], metadata: list[dict]) -> bool:
        records = self._load_records()
        for chunk, meta in zip(chunks, metadata, strict=True):
            content = chunk["content"]
            records.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "content": content,
                    "metadata": meta,
                    "embedding": self._embed_document(content, meta),
                }
            )
        self._save_records(records)
        return True

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict | None = None,
    ) -> list[dict]:
        records = self._load_records()
        scored = []
        for record in records:
            if not self._matches_filters(record.get("metadata", {}), filters or {}):
                continue
            score = self.embedding_service.cosine_similarity(query_vector, record.get("embedding", []))
            scored.append({**record, "similarity_score": round(score, 6)})
        scored.sort(key=lambda item: item["similarity_score"], reverse=True)
        return scored[:top_k]

    def delete_by_doc_id(self, doc_id: str) -> bool:
        records = self._load_records()
        kept = [record for record in records if record.get("metadata", {}).get("doc_id") != doc_id]
        self._save_records(kept)
        return len(kept) != len(records)

    def to_retrieved_chunk(self, record: dict) -> RetrievedChunk:
        metadata = ChunkMetadata(**record["metadata"])
        return RetrievedChunk(
            chunk_id=record["chunk_id"],
            content=record["content"],
            metadata=metadata,
            similarity_score=float(record["similarity_score"]),
        )

    def _load_records(self) -> list[dict]:
        if not self.store_path.exists():
            return []
        try:
            return json.loads(self.store_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise VectorDbConnectionError(f"Invalid vector store file: {self.store_path}") from exc

    def _save_records(self, records: list[dict]) -> None:
        self.store_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _matches_filters(metadata: dict, filters: dict) -> bool:
        for key, expected in filters.items():
            if expected is None:
                continue
            if metadata.get(key) != expected:
                return False
        return True

    def _embed_document(self, content: str, metadata: dict) -> list[float]:
        try:
            return self.embedding_service.embed_text(
                content,
                company_id=metadata.get("company_id", "default"),
            )
        except TypeError:
            return self.embedding_service.embed_text(content)


class ChromaVectorDbAdapter(BaseVectorDbAdapter):
    def __init__(
        self,
        vector_db_id: str,
        host: str,
        port: int,
        collection_name: str,
        embedding_service: HashEmbeddingService,
    ) -> None:
        import chromadb

        self.vector_db_id = vector_db_id
        self.embedding_service = embedding_service
        self.client = chromadb.HttpClient(host=host, port=port)
        self.collection = self.client.get_or_create_collection(collection_name)

    def add_documents(self, chunks: list[dict], metadata: list[dict]) -> bool:
        ids = [chunk["chunk_id"] for chunk in chunks]
        documents = [chunk["content"] for chunk in chunks]
        embeddings = [
            self._embed_document(chunk["content"], meta)
            for chunk, meta in zip(chunks, metadata, strict=True)
        ]
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadata,
            embeddings=embeddings,
        )
        return True

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict | None = None,
    ) -> list[dict]:
        where = {key: {"$eq": value} for key, value in (filters or {}).items() if value is not None}
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where or None,
        )
        records = []
        for chunk_id, document, metadata, distance in zip(
            results.get("ids", [[]])[0],
            results.get("documents", [[]])[0],
            results.get("metadatas", [[]])[0],
            results.get("distances", [[]])[0],
            strict=False,
        ):
            records.append(
                {
                    "chunk_id": chunk_id,
                    "content": document,
                    "metadata": metadata,
                    "similarity_score": max(0.0, 1.0 - float(distance)),
                }
            )
        return records

    def delete_by_doc_id(self, doc_id: str) -> bool:
        results = self.collection.get(where={"doc_id": {"$eq": doc_id}})
        ids = results.get("ids", [])
        if not ids:
            return False
        self.collection.delete(ids=ids)
        return True

    def to_retrieved_chunk(self, record: dict) -> RetrievedChunk:
        metadata = ChunkMetadata(**record["metadata"])
        return RetrievedChunk(
            chunk_id=record["chunk_id"],
            content=record["content"],
            metadata=metadata,
            similarity_score=float(record["similarity_score"]),
        )

    def _embed_document(self, content: str, metadata: dict) -> list[float]:
        try:
            return self.embedding_service.embed_text(
                content,
                company_id=metadata.get("company_id", "default"),
            )
        except TypeError:
            return self.embedding_service.embed_text(content)
