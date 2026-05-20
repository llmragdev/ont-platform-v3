from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.db_models import ProjectRagDoc, Project
import uuid

class DocRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_doc(self, tenant_id: str, project_code: str, file_name: str, org_id: str = None, source_url: str = None):
        # 1. 프로젝트 존재 여부 확인 및 vector_db_id 가져오기
        project = self.db.query(Project).filter(
            and_(Project.tenant_id == tenant_id, Project.project_code == project_code)
        ).first()
        
        if not project:
            # 실무에서는 에러를 던져야 하지만, 여기서는 자동 생성하거나 기본값 사용
            assigned_vdb = "vdb_default_01"
        else:
            assigned_vdb = project.vector_db_id or "vdb_default_01"

        # dept_code 파생 (앞 2자리)
        dept_code = org_id[:2] if org_id and len(org_id) >= 2 else None

        doc_record = ProjectRagDoc(
            doc_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            project_code=project_code,
            org_id=org_id,
            dept_code=dept_code,
            file_name=file_name,
            source_url=source_url,
            assigned_vector_db=assigned_vdb,
            pipeline_status="pending"
        )
        self.db.add(doc_record)
        self.db.commit()
        self.db.refresh(doc_record)
        return doc_record

    def update_status(self, doc_id: str, status: str, error_message: str = None):
        doc = self.db.query(ProjectRagDoc).filter(ProjectRagDoc.doc_id == doc_id).first()
        if doc:
            doc.pipeline_status = status
            if error_message:
                doc.error_message = error_message
            self.db.commit()
            self.db.refresh(doc)
        return doc

    def get_doc(self, doc_id: str):
        return self.db.query(ProjectRagDoc).filter(ProjectRagDoc.doc_id == doc_id).first()

    def delete_doc(self, doc_id: str, tenant_id: str):
        doc = self.db.query(ProjectRagDoc).filter(
            and_(ProjectRagDoc.doc_id == doc_id, ProjectRagDoc.tenant_id == tenant_id)
        ).first()
        if doc:
            vdb_id = doc.assigned_vector_db
            self.db.delete(doc)
            self.db.commit()
            return vdb_id
        return None
