from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import DocumentNotFoundError
from app.models.schemas import DocumentUploadData, DocumentUploadResponse
from app.repositories.audit_repo import AuditRepository
from app.repositories.document_repo import DocumentRepository
from app.services.embedding.base import EmbeddingService
from app.services.pipeline.chunker import ChunkerBase, FixedSizeChunker, SemanticChunker
from app.services.pipeline.extractor import FileExtractor
from app.services.router import VectorDbRouter


def _get_embedding_service() -> EmbeddingService:
    if settings.embedding_provider == "claude":
        from app.services.embedding.claude_embedding import ClaudeEmbeddingService
        return ClaudeEmbeddingService()
    from app.services.embedding.hash_embedding import HashEmbeddingService
    return HashEmbeddingService()


def _get_chunker() -> ChunkerBase:
    if settings.chunker_type == "fixed":
        return FixedSizeChunker()
    return SemanticChunker()


class DocumentPipelineService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._doc_repo = DocumentRepository(db)
        self._audit_repo = AuditRepository(db)
        self._embedding_service = _get_embedding_service()
        self._router = VectorDbRouter(self._embedding_service)
        self._extractor = FileExtractor()
        self._chunker = _get_chunker()

    async def upload(
        self,
        file: UploadFile,
        category_mid: str,
        vector_db_id: str | None = None,
        category_low: str | None = None,
        company_id: str = "default",
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
            company_id=company_id,
            category_low=category_low,
        )

        raw_path = settings.raw_documents_dir / f"{record.doc_id}_{safe_name}"
        raw_path.write_bytes(content)

        self._run_pipeline(
            record.doc_id, safe_name, raw_path,
            category_mid, category_low, assigned_vdb,
        )
        self._audit_repo.log("upload", company_id=company_id, resource=record.doc_id)

        refreshed = self._doc_repo.get(record.doc_id)
        return DocumentUploadResponse(
            status="success",
            data=DocumentUploadData(
                doc_id=refreshed.doc_id,
                pipeline_status=refreshed.pipeline_status,
                file_name=refreshed.file_name,
                assigned_vector_db=refreshed.assigned_vector_db,
                version=refreshed.version,
            ),
        )

    def _run_pipeline(
        self,
        doc_id: str,
        safe_name: str,
        raw_path: Path,
        category_mid: str,
        category_low: str | None,
        assigned_vdb: str,
    ) -> None:
        self._doc_repo.set_status(doc_id, "processing")
        try:
            text = self._extractor.extract(raw_path)
            chunks = self._chunker.split_text(text)

            processed_path = settings.processed_dir / f"{doc_id}.txt"
            processed_path.write_text("\n\n".join(chunks), encoding="utf-8")

            chunk_payloads = [
                {"chunk_id": f"{doc_id}#chunk{i}", "content": c}
                for i, c in enumerate(chunks)
            ]
            meta_payloads = [
                {
                    "source_name": safe_name,
                    "source_url": str(raw_path),
                    "doc_id": doc_id,
                    "category_mid": category_mid,
                    "category_low": category_low,
                    "chunk_type": "text",
                    "tags": [],
                }
                for _ in chunks
            ]

            adapter = self._router.get_adapter(vector_db_id=assigned_vdb)
            adapter.add_documents(chunk_payloads, meta_payloads)
            self._doc_repo.set_status(doc_id, "completed")
        except Exception as exc:
            self._doc_repo.set_status(doc_id, "error", str(exc))

    def delete(self, doc_id: str, company_id: str = "default") -> bool:
        record = self._doc_repo.get(doc_id)
        if not record:
            raise DocumentNotFoundError(f"doc_id={doc_id} not found")
        self._router.get_adapter(vector_db_id=record.assigned_vector_db).delete_by_doc_id(doc_id)
        self._audit_repo.log("delete", company_id=company_id, resource=doc_id)
        return self._doc_repo.delete(doc_id)

    async def update(
        self,
        doc_id: str,
        file: UploadFile,
        company_id: str = "default",
    ) -> DocumentUploadResponse:
        record = self._doc_repo.get(doc_id)
        if not record:
            raise DocumentNotFoundError(f"doc_id={doc_id} not found")

        # 기존 벡터 삭제 후 버전 증가
        adapter = self._router.get_adapter(vector_db_id=record.assigned_vector_db)
        adapter.delete_by_doc_id(doc_id)

        version = self._doc_repo.bump_version_for_update(doc_id)
        content = await file.read()
        safe_name = Path(file.filename or "upload").name

        raw_path = settings.raw_documents_dir / f"{doc_id}_v{version}_{safe_name}"
        raw_path.write_bytes(content)

        self._run_pipeline(
            doc_id, safe_name, raw_path,
            record.category_mid, record.category_low, record.assigned_vector_db,
        )
        self._audit_repo.log("update", company_id=company_id, resource=doc_id)

        refreshed = self._doc_repo.get(doc_id)
        return DocumentUploadResponse(
            status="success",
            data=DocumentUploadData(
                doc_id=refreshed.doc_id,
                pipeline_status=refreshed.pipeline_status,
                file_name=refreshed.file_name,
                assigned_vector_db=refreshed.assigned_vector_db,
                version=refreshed.version,
            ),
        )
