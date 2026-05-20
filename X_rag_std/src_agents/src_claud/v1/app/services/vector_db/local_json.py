import json
import uuid
from pathlib import Path

from app.models.schemas import ChunkMetadata, RetrievedChunk
from app.services.embedding.base import EmbeddingService
from app.services.vector_db.base import VectorDbAdapter


class LocalJsonVectorDbAdapter(VectorDbAdapter):
    """JSON 파일 기반 로컬 벡터 스토어 (개발/테스트용).
    Codex LocalJsonVectorDbAdapter에서 EmbeddingService 의존성 주입 + 타입 안전 zip 추가.
    """

    def __init__(
        self,
        vector_db_id: str,
        store_path: Path,
        embedding_service: EmbeddingService,
    ) -> None:
        self.vector_db_id = vector_db_id
        self.store_path = store_path
        self.embedding_service = embedding_service

    def add_documents(self, chunks: list[dict], metadata: list[dict]) -> None:
        records = self._load()
        for chunk, meta in zip(chunks, metadata, strict=True):
            records.append(
                {
                    "chunk_id": chunk.get("chunk_id", str(uuid.uuid4())),
                    "content": chunk["content"],
                    "metadata": meta,
                    "embedding": self.embedding_service.embed_text(chunk["content"]),
                }
            )
        self._save(records)

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict | None = None,
    ) -> list[dict]:
        records = self._load()
        scored: list[dict] = []
        for rec in records:
            if not self._matches_filters(rec.get("metadata", {}), filters or {}):
                continue
            score = self.embedding_service.cosine_similarity(
                query_vector, rec.get("embedding", [])
            )
            scored.append({**rec, "similarity_score": round(score, 6)})
        scored.sort(key=lambda r: r["similarity_score"], reverse=True)
        return scored[:top_k]

    def delete_by_doc_id(self, doc_id: str) -> bool:
        records = self._load()
        kept = [r for r in records if r.get("metadata", {}).get("doc_id") != doc_id]
        if len(kept) == len(records):
            return False
        self._save(kept)
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
                tags=meta.get("tags", []),
            ),
        )

    def _load(self) -> list[dict]:
        if not self.store_path.exists():
            return []
        try:
            return json.loads(self.store_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self, records: list[dict]) -> None:
        self.store_path.write_text(
            json.dumps(records, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    @staticmethod
    def _matches_filters(metadata: dict, filters: dict) -> bool:
        for key, value in filters.items():
            if metadata.get(key) != value:
                return False
        return True
