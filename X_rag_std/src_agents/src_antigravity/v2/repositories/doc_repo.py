import uuid
from sqlalchemy.orm import Session
from models.db_models import ProjectRagDoc

class DocRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_doc(self, file_name: str, category_mid: str, project_code: str = "000001") -> ProjectRagDoc:
        new_doc = ProjectRagDoc(
            doc_id=str(uuid.uuid4()),
            project_code=project_code,
            file_name=file_name,
            pipeline_status="pending",
            assigned_vector_db=f"vdb_{category_mid}_01"
        )
        self.db.add(new_doc)
        self.db.commit()
        self.db.refresh(new_doc)
        return new_doc

    def update_status(self, doc_id: str, status: str):
        doc = self.db.query(ProjectRagDoc).filter(ProjectRagDoc.doc_id == doc_id).first()
        if doc:
            doc.pipeline_status = status
            self.db.commit()
            self.db.refresh(doc)
        return doc
