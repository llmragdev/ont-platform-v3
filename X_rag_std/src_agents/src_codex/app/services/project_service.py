from sqlalchemy.orm import Session

from app.repositories.document_repository import DocumentRepository
from app.repositories.project_repository import ProjectRepository
from app.services.providers import get_embedding_service
from app.services.vector_router import VectorDbRouter


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.project_repository = ProjectRepository(db)
        self.document_repository = DocumentRepository(db)
        self.router = VectorDbRouter(get_embedding_service())

    def create(self, project_name: str, vector_db_id: str, project_code: str | None = None):
        record = self.project_repository.create(project_name, vector_db_id, project_code)
        self.router.get_adapter(vector_db_id=record.vector_db_id)
        return record

    def list_all(self):
        return self.project_repository.list_all()

    def get(self, project_code: str):
        record = self.project_repository.get(project_code)
        if record is None:
            raise KeyError(f"Unknown project: {project_code}")
        return record

    def delete(self, project_code: str) -> bool:
        if self.project_repository.get(project_code) is None:
            raise KeyError(f"Unknown project: {project_code}")
        for document in self.project_repository.list_documents(project_code):
            adapter = self.router.get_adapter(vector_db_id=document.assigned_vector_db)
            adapter.delete_by_doc_id(document.doc_id)
            self.document_repository.delete(document.doc_id)
        return self.project_repository.delete(project_code)
