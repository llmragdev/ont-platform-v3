"""DocumentService — upload / vectorize / delete."""
from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from storage_config import (
    ensure_project_dirs,
    get_ontology_path,
    get_uploads_path,
    get_vector_db_path,
    list_shard_paths,
)
from app.models.tenant_context import TenantContext
from app.services.audit import append_audit_event

_REGISTRY_FILE = "documents_registry.json"
_LEGACY_REGISTRY_FILE = "docs_registry.json"


class DocumentService:
    def __init__(self, embeddings, chunk_size: int = 1000, chunk_overlap: int = 150) -> None:
        self._embeddings = embeddings
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def upload(self, file_bytes: bytes, filename: str, ctx: TenantContext, shard_id: str = "default") -> dict:
        ensure_project_dirs(ctx.company_id, ctx.project_id)
        doc_id = f"doc-{uuid.uuid4().hex[:8]}"
        safe_filename = os.path.basename(filename)
        dest = get_uploads_path(ctx.company_id, ctx.project_id) / safe_filename
        dest.write_bytes(file_bytes)
        try:
            chunk_count = self._vectorize(dest, doc_id, safe_filename, ctx, shard_id)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("vectorize 실패 (파일 저장은 완료): %s", exc)
            chunk_count = 0
        entry = {
            "doc_id": doc_id,
            "filename": safe_filename,
            "company_id": ctx.company_id,
            "project_id": ctx.project_id,
            "shard_id": shard_id,
            "chunk_count": chunk_count,
            "physical_path": str(dest),
            "size_bytes": len(file_bytes),
            "uploaded_by": ctx.user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._update_registry(ctx, doc_id, entry)
        append_audit_event(ctx, "CREATE_DOCUMENT", "document", doc_id,
                           {"filename": safe_filename, "shard_id": shard_id, "chunk_count": chunk_count})
        return entry

    def _vectorize(self, file_path: Path, doc_id: str, filename: str, ctx: TenantContext, shard_id: str) -> int:
        from langchain_community.document_loaders import PyPDFLoader
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore[no-redef]
        try:
            from langchain_chroma import Chroma
        except ImportError:
            from langchain_community.vectorstores import Chroma

        loader = PyPDFLoader(str(file_path))
        try:
            pages = loader.load()
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("PDF 파싱 실패 (%s): %s", file_path.name, exc)
            pages = []

        if self._embeddings is None or not pages:
            return len(pages)

        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore[no-redef]

        splitter = RecursiveCharacterTextSplitter(chunk_size=self._chunk_size, chunk_overlap=self._chunk_overlap)
        chunks = splitter.split_documents(pages)
        for chunk in chunks:
            chunk.metadata.update({"doc_id": doc_id, "filename": filename,
                                   "company_id": ctx.company_id, "project_id": ctx.project_id})
        persist_dir = str(get_vector_db_path(ctx.company_id, ctx.project_id, shard_id))
        store = Chroma(persist_directory=persist_dir, embedding_function=self._embeddings)
        store.add_documents(chunks)
        return len(chunks)

    def list(self, ctx: TenantContext) -> list[dict]:
        return list(self._load_registry(ctx).values())

    def delete(self, doc_id: str, ctx: TenantContext) -> bool:
        registry = self._load_registry(ctx)
        entry = registry.get(doc_id)
        if not entry:
            return False
        self._delete_from_chroma(doc_id, entry, ctx)
        self._delete_file(entry, ctx)
        del registry[doc_id]
        self._save_registry(ctx, registry)
        append_audit_event(ctx, "DELETE_DOCUMENT", "document", doc_id, {"filename": entry.get("filename")})
        return True

    def _delete_from_chroma(self, doc_id: str, entry: dict, ctx: TenantContext) -> None:
        try:
            from langchain_chroma import Chroma
        except ImportError:
            from langchain_community.vectorstores import Chroma
        shard_id = entry.get("shard_id", "default")
        persist_dir = str(get_vector_db_path(ctx.company_id, ctx.project_id, shard_id))
        try:
            store = Chroma(persist_directory=persist_dir, embedding_function=self._embeddings)
            ids = store.get(where={"doc_id": doc_id}).get("ids", [])
            if ids:
                store.delete(ids=ids)
        except Exception:
            pass

    def _delete_file(self, entry: dict, ctx: TenantContext) -> None:
        dest = get_uploads_path(ctx.company_id, ctx.project_id) / entry["filename"]
        if dest.exists():
            dest.unlink()

    def _registry_path(self, ctx: TenantContext) -> Path:
        return get_uploads_path(ctx.company_id, ctx.project_id) / _REGISTRY_FILE

    def _load_registry(self, ctx: TenantContext) -> dict:
        p = self._registry_path(ctx)
        if not p.exists():
            legacy = get_uploads_path(ctx.company_id, ctx.project_id) / _LEGACY_REGISTRY_FILE
            if not legacy.exists():
                return {}
            return json.loads(legacy.read_text(encoding="utf-8"))
        return json.loads(p.read_text(encoding="utf-8"))

    def _save_registry(self, ctx: TenantContext, registry: dict) -> None:
        p = self._registry_path(ctx)
        p.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")

    def _update_registry(self, ctx: TenantContext, doc_id: str, entry: dict) -> None:
        registry = self._load_registry(ctx)
        registry[doc_id] = entry
        self._save_registry(ctx, registry)
