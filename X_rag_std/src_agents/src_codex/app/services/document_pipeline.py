import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import DocumentParsingError
from app.models.db_models import ProjectRagDocument
from app.repositories.document_repository import DocumentRepository
from app.services.chunking import TextChunker
from app.services.providers import get_embedding_service
from app.services.vector_router import VectorDbRouter


class DocumentPipelineService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedding_service = get_embedding_service()
        self.router = VectorDbRouter(self.embedding_service)
        self.chunker = TextChunker()
        self.repository = DocumentRepository(db)

    async def upload_document(
        self,
        file: UploadFile,
        category_mid: str,
        category_low: str | None = None,
        vector_db_id: str | None = None,
        company_id: str = "default",
    ) -> ProjectRagDocument:
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        assigned_vector_db = self.router.resolve_vector_db_id(category_mid, vector_db_id)
        safe_name = Path(file.filename or "uploaded_document.txt").name
        raw_path = settings.raw_documents_dir / f"{doc_id}_{safe_name}"
        content = await file.read()
        raw_path.write_bytes(content)

        record = self.repository.create(
            doc_id=doc_id,
            file_name=safe_name,
            source_url=str(raw_path),
            assigned_vector_db=assigned_vector_db,
            category_mid=category_mid,
            category_low=category_low,
            company_id=company_id,
        )
        self._run_pipeline(record, raw_path)
        return self.repository.get(doc_id) or record

    async def update_document(
        self,
        doc_id: str,
        file: UploadFile,
        category_mid: str,
        category_low: str | None = None,
        vector_db_id: str | None = None,
        company_id: str = "default",
    ) -> ProjectRagDocument:
        existing = self.repository.get(doc_id)
        if existing is None:
            raise KeyError(f"Unknown document: {doc_id}")
        if existing.company_id != company_id:
            raise KeyError(f"Unknown document for company: {doc_id}")

        assigned_vector_db = self.router.resolve_vector_db_id(category_mid, vector_db_id)
        adapter = self.router.get_adapter(vector_db_id=existing.assigned_vector_db)
        adapter.delete_by_doc_id(doc_id)

        safe_name = Path(file.filename or existing.file_name).name
        raw_path = settings.raw_documents_dir / f"{doc_id}_v{existing.version + 1}_{safe_name}"
        raw_path.write_bytes(await file.read())

        record = self.repository.bump_version_for_update(
            doc_id=doc_id,
            file_name=safe_name,
            source_url=str(raw_path),
            category_mid=category_mid,
            category_low=category_low,
            assigned_vector_db=assigned_vector_db,
        )
        self._run_pipeline(record, raw_path)
        return self.repository.get(doc_id) or record

    def list_documents(self, company_id: str = "default") -> list[ProjectRagDocument]:
        return self.repository.list_all(company_id)

    def delete_document(self, doc_id: str, company_id: str = "default") -> bool:
        existing = self.repository.get(doc_id)
        if existing is None or existing.company_id != company_id:
            raise KeyError(f"Unknown document for company: {doc_id}")
        adapter = self.router.get_adapter(vector_db_id=existing.assigned_vector_db)
        adapter.delete_by_doc_id(doc_id)
        return self.repository.delete(doc_id)

    def _run_pipeline(self, record: ProjectRagDocument, raw_path: Path) -> None:
        self.repository.set_status(record.doc_id, "processing")
        try:
            text = self._extract_text(raw_path)
            chunks = self.chunker.split_text(text)
            if not chunks:
                raise DocumentParsingError("No text could be extracted from the uploaded file.")

            processed_path = settings.processed_dir / f"{record.doc_id}.txt"
            processed_path.write_text("\n\n".join(chunks), encoding="utf-8")

            chunk_payloads = []
            metadata_payloads = []
            for index, chunk in enumerate(chunks):
                chunk_id = f"{record.doc_id}#chunk{index}"
                chunk_payloads.append({"chunk_id": chunk_id, "content": chunk})
                metadata_payloads.append(
                    {
                        "doc_id": record.doc_id,
                        "company_id": record.company_id,
                        "source_name": record.file_name,
                        "source_url": record.source_url,
                        "page_no": index + 1,
                        "category_mid": record.category_mid,
                        "category_low": record.category_low,
                        "vector_db_id": record.assigned_vector_db,
                        "chunk_type": "text",
                        "tags": [],
                    }
                )

            adapter = self.router.get_adapter(
                category_mid=record.category_mid,
                vector_db_id=record.assigned_vector_db,
            )
            adapter.add_documents(chunk_payloads, metadata_payloads)
            self.repository.set_status(record.doc_id, "completed")
        except Exception as exc:
            self.repository.set_status(record.doc_id, "error", str(exc))

    @staticmethod
    def _extract_text(path: Path) -> str:
        if path.suffix.lower() == ".pdf":
            try:
                from pypdf import PdfReader

                reader = PdfReader(str(path))
                page_texts = [page.extract_text() or "" for page in reader.pages]
                return "\n\n".join(page_texts)
            except Exception as exc:
                raise DocumentParsingError(f"PDF parsing failed: {path.name}") from exc

        data = path.read_bytes()
        for encoding in ("utf-8", "cp949", "latin-1"):
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise DocumentParsingError(f"Unable to decode document: {path.name}")
