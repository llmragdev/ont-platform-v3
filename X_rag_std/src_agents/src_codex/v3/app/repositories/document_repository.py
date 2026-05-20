from app.models.db_models import utc_now

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db_models import ProjectRagDocument


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        doc_id: str,
        file_name: str,
        source_url: str,
        assigned_vector_db: str,
        category_mid: str,
        category_low: str | None,
        tenant_id: str,
        org_id: str | None = None,
        project_code: str = "000001",
    ) -> ProjectRagDocument:
        record = ProjectRagDocument(
            doc_id=doc_id,
            project_code=project_code,
            tenant_id=tenant_id,
            org_id=org_id,
            file_name=file_name,
            source_url=source_url,
            pipeline_status="pending",
            assigned_vector_db=assigned_vector_db,
            category_mid=category_mid,
            category_low=category_low,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get(self, doc_id: str) -> ProjectRagDocument | None:
        return self.db.get(ProjectRagDocument, doc_id)

    def list_all(self, tenant_id: str | None = None) -> list[ProjectRagDocument]:
        stmt = select(ProjectRagDocument).order_by(ProjectRagDocument.created_at.desc())
        if tenant_id is not None:
            stmt = stmt.where(ProjectRagDocument.tenant_id == tenant_id)
        return list(self.db.scalars(stmt))

    def set_status(
        self,
        doc_id: str,
        pipeline_status: str,
        error_message: str | None = None,
    ) -> ProjectRagDocument:
        record = self.db.get(ProjectRagDocument, doc_id)
        if record is None:
            raise KeyError(f"Unknown document: {doc_id}")
        record.pipeline_status = pipeline_status
        record.error_message = error_message
        record.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(record)
        return record

    def bump_version_for_update(
        self,
        doc_id: str,
        file_name: str,
        source_url: str,
        category_mid: str,
        category_low: str | None,
        assigned_vector_db: str,
        org_id: str | None = None,
    ) -> ProjectRagDocument:
        record = self.db.get(ProjectRagDocument, doc_id)
        if record is None:
            raise KeyError(f"Unknown document: {doc_id}")
        record.file_name = file_name
        record.source_url = source_url
        record.category_mid = category_mid
        record.category_low = category_low
        record.assigned_vector_db = assigned_vector_db
        record.org_id = org_id
        record.pipeline_status = "pending"
        record.error_message = None
        record.version += 1
        record.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(record)
        return record

    def delete(self, doc_id: str) -> bool:
        record = self.db.get(ProjectRagDocument, doc_id)
        if record is None:
            return False
        self.db.delete(record)
        self.db.commit()
        return True
