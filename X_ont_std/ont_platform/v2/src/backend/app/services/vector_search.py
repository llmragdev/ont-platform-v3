"""VectorSearchService — V-ID shard-based Chroma search (D06, D09)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from storage_config import get_vector_db_path, list_shard_paths
from app.models.tenant_context import TenantContext


class VectorSearchService:
    def __init__(self, embeddings) -> None:
        self._embeddings = embeddings

    # ── 검색 ──────────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        ctx: TenantContext,
        k: int = 3,
        shard_id: str | None = None,
    ) -> list[dict]:
        """V-ID 샤드 기반 검색.

        shard_id 지정 시 해당 샤드만 탐색.
        None이면 프로젝트 내 모든 샤드를 순회해 score 내림차순으로 재정렬.
        """
        shard_paths = self._resolve_shard_paths(ctx, shard_id)
        if not shard_paths:
            return []

        results: list[dict] = []
        for path in shard_paths:
            results.extend(self._search_shard(query, path, k))

        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:k]

    def health(self, ctx: TenantContext) -> dict:
        paths = list_shard_paths(ctx.company_id, ctx.project_id)
        return {
            "available": True,
            "shard_count": len(paths),
            "embedding_model": getattr(self._embeddings, "model", "unknown"),
        }

    # ── 내부 헬퍼 ─────────────────────────────────────────────────────────────

    def _resolve_shard_paths(
        self, ctx: TenantContext, shard_id: str | None
    ) -> list[Path]:
        if shard_id is not None:
            p = get_vector_db_path(ctx.company_id, ctx.project_id, shard_id)
            return [p] if p.exists() else []
        return list_shard_paths(ctx.company_id, ctx.project_id)

    def _search_shard(self, query: str, path: Path, k: int) -> list[dict]:
        try:
            from langchain_chroma import Chroma
        except ImportError:
            from langchain_community.vectorstores import Chroma

        try:
            store = Chroma(
                persist_directory=str(path),
                embedding_function=self._embeddings,
            )
            hits = store.similarity_search_with_score(query, k=k)
        except Exception:
            return []

        results = []
        for doc, score in hits:
            results.append({
                "text": doc.page_content,
                "score": float(score),
                "doc_id": doc.metadata.get("doc_id", ""),
                "filename": doc.metadata.get("filename", ""),
                "page": doc.metadata.get("page", 0),
                "shard_id": path.name,
            })
        return results
