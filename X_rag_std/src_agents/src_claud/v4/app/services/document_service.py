import asyncio
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import DocumentNotFoundError
from app.models.schemas import DocumentUploadData, DocumentUploadResponse
from app.repositories.audit_repo import AuditRepository
from app.repositories.document_repo import DocumentRepository
from app.services.pipeline.extractor import FileExtractor
from app.services.providers import get_chunker, get_embedding_service
from app.services.router import VectorDbRouter


def _run_pipeline_isolated(
    doc_id: str,
    safe_name: str,
    raw_path: Path,
    category_large: str | None,
    category_mid: str,
    category_low: str | None,
    assigned_vdb: str,
    tenant_id: str,
    org_id: str | None,
) -> None:
    """파이프라인 워커 — 독립 Session 생성 (asyncio.to_thread 에서 실행).
    요청 스레드의 Session을 절대 공유하지 않음.
    """
    from app.db.session import SessionLocal

    embedding_service = get_embedding_service()
    router = VectorDbRouter(embedding_service)
    extractor = FileExtractor()
    chunker = get_chunker()

    with SessionLocal() as db:
        doc_repo = DocumentRepository(db)
        try:
            doc_repo.set_status(doc_id, "processing")
        except Exception:
            pass
        try:
            text = extractor.extract(raw_path)
            chunks = chunker.split_text(text)

            processed_path = settings.processed_dir / f"{doc_id}.txt"
            processed_path.write_text("\n\n".join(chunks), encoding="utf-8")

            now_iso = datetime.now(timezone.utc).isoformat()
            org_id_stored = org_id or ""   # 전사 공유 문서는 "" 저장 (ChromaDB scalar 호환)
            dept_code = org_id[:2] if org_id else None

            chunk_payloads = [
                {"chunk_id": f"{doc_id}#chunk{i}", "content": c}
                for i, c in enumerate(chunks)
            ]
            meta_payloads = [
                {
                    "source_name": safe_name,
                    "source_url": str(raw_path),
                    "doc_id": doc_id,
                    "category_large": category_large,
                    "category_mid": category_mid,
                    "category_low": category_low,
                    "chunk_type": "text",
                    "tenant_id": tenant_id,
                    "org_id": org_id_stored,
                    **({"dept_code": dept_code} if dept_code else {}),
                    "vector_db_id": assigned_vdb,
                    "created_at": now_iso,
                    # tags는 vector metadata에서 제외 — RDBMS 저장 시에만 사용
                }
                for _ in chunks
            ]

            # embeddings= 명시 전달 — 어댑터 내부 임베딩 생성 금지 (표준 2.2)
            embeddings = [
                embedding_service.embed_text(c["content"], tenant_id=tenant_id)
                for c in chunk_payloads
            ]

            adapter = router.get_adapter(vector_db_id=assigned_vdb)
            adapter.add_documents(chunk_payloads, meta_payloads, embeddings)
            try:
                doc_repo.set_status(doc_id, "completed")
            except Exception:
                pass
        except Exception as exc:
            try:
                doc_repo.set_status(doc_id, "error", str(exc))
            except Exception:
                pass


class DocumentPipelineService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._doc_repo = DocumentRepository(db)
        self._audit_repo = AuditRepository(db)
        self._embedding_service = get_embedding_service()
        self._router = VectorDbRouter(self._embedding_service)

    async def upload(
        self,
        file: UploadFile,
        category_mid: str,
        category_large: str | None = None,
        vector_db_id: str | None = None,
        category_low: str | None = None,
        tenant_id: str = "",
        org_id: str | None = None,
        project_code: str = "000001",
    ) -> DocumentUploadResponse:
        content = await file.read()
        safe_name = Path(file.filename or "upload").name

        assigned_vdb = self._router.resolve_vector_db_id(
            category_mid=category_mid, vector_db_id=vector_db_id
        )
        record = self._doc_repo.create(
            file_name=safe_name,
            category_mid=category_mid,
            assigned_vector_db=assigned_vdb,
            tenant_id=tenant_id,
            org_id=org_id,
            category_low=category_low,
            project_code=project_code,
        )

        raw_path = settings.raw_documents_dir / f"{record.doc_id}_{safe_name}"
        raw_path.write_bytes(content)

        pipeline_coro = asyncio.to_thread(
            _run_pipeline_isolated,
            record.doc_id, safe_name, raw_path,
            category_large, category_mid, category_low, assigned_vdb,
            tenant_id, org_id,
        )
        if settings.pipeline_sync_mode:
            await pipeline_coro
        else:
            asyncio.create_task(pipeline_coro)

        self._audit_repo.log("upload", tenant_id=tenant_id, resource=record.doc_id)

        return DocumentUploadResponse(
            status="success",
            data=DocumentUploadData(
                doc_id=record.doc_id,
                pipeline_status="pending",
                file_name=safe_name,
                assigned_vector_db=assigned_vdb,
                version=record.version,
            ),
            doc_id=record.doc_id,
        )

    def delete(self, doc_id: str, tenant_id: str = "") -> bool:
        record = self._doc_repo.get(doc_id)
        if not record:
            raise DocumentNotFoundError(f"doc_id={doc_id} not found")
        self._router.get_adapter(vector_db_id=record.assigned_vector_db).delete_by_doc_id(doc_id)
        self._audit_repo.log("delete", tenant_id=tenant_id, resource=doc_id)
        return self._doc_repo.delete(doc_id)

    async def update(
        self,
        doc_id: str,
        file: UploadFile,
        tenant_id: str = "",
        org_id: str | None = None,
    ) -> DocumentUploadResponse:
        record = self._doc_repo.get(doc_id)
        if not record:
            raise DocumentNotFoundError(f"doc_id={doc_id} not found")

        adapter = self._router.get_adapter(vector_db_id=record.assigned_vector_db)
        adapter.delete_by_doc_id(doc_id)

        version = self._doc_repo.bump_version_for_update(doc_id)
        content = await file.read()
        safe_name = Path(file.filename or "upload").name

        raw_path = settings.raw_documents_dir / f"{doc_id}_v{version}_{safe_name}"
        raw_path.write_bytes(content)

        update_coro = asyncio.to_thread(
            _run_pipeline_isolated,
            doc_id, safe_name, raw_path,
            None, record.category_mid, record.category_low, record.assigned_vector_db,
            tenant_id, org_id,
        )
        if settings.pipeline_sync_mode:
            await update_coro
        else:
            asyncio.create_task(update_coro)

        self._audit_repo.log("update", tenant_id=tenant_id, resource=doc_id)

        return DocumentUploadResponse(
            status="success",
            data=DocumentUploadData(
                doc_id=doc_id,
                pipeline_status="pending",
                file_name=safe_name,
                assigned_vector_db=record.assigned_vector_db,
                version=version,
            ),
            doc_id=doc_id,
        )
