import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.db_models import ProjectRagDocument


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        file_name: str,
        category_mid: str,
        assigned_vector_db: str,
        tenant_id: str,
        org_id: str | None = None,
        category_low: str | None = None,
        project_code: str = "000001",
    ) -> ProjectRagDocument:
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        record = ProjectRagDocument(
            doc_id=doc_id,
            tenant_id=tenant_id,
            org_id=org_id,
            project_code=project_code,
            file_name=file_name,
            source_url=f"storage/raw_documents/{doc_id}_{file_name}",
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
        return (
            self.db.query(ProjectRagDocument)
            .filter(ProjectRagDocument.doc_id == doc_id)
            .first()
        )

    def list_by_tenant(self, tenant_id: str) -> list[ProjectRagDocument]:
        return (
            self.db.query(ProjectRagDocument)
            .filter(ProjectRagDocument.tenant_id == tenant_id)
            .all()
        )

    def set_status(
        self, doc_id: str, status: str, error_msg: str | None = None
    ) -> None:
        record = self.get(doc_id)
        if record:
            record.pipeline_status = status
            if error_msg is not None:
                record.error_message = error_msg
            record.updated_at = datetime.now(timezone.utc)
            self.db.commit()

    def bump_version_for_update(self, doc_id: str) -> int:
        record = self.get(doc_id)
        if not record:
            return 0
        record.version += 1
        record.pipeline_status = "pending"
        record.error_message = None
        record.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return record.version

    def delete(self, doc_id: str) -> bool:
        record = self.get(doc_id)
        if not record:
            return False
        self.db.delete(record)
        self.db.commit()
        return True
