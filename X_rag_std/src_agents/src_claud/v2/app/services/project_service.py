from sqlalchemy.orm import Session

from app.core.errors import ProjectNotFoundError
from app.models.db_models import Project
from app.repositories.audit_repo import AuditRepository
from app.repositories.document_repo import DocumentRepository
from app.repositories.project_repo import ProjectRepository
from app.services.providers import get_embedding_service
from app.services.router import VectorDbRouter


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._repo = ProjectRepository(db)
        self._doc_repo = DocumentRepository(db)
        self._audit_repo = AuditRepository(db)
        self._router = VectorDbRouter(get_embedding_service())

    def create(
        self,
        project_name: str,
        vector_db_id: str,
        project_code: str | None = None,
        company_id: str = "default",
    ) -> Project:
        from app.core.config import settings
        proj = self._repo.create(
            project_name=project_name,
            vector_db_id=vector_db_id,
            project_code=project_code,
        )
        # chroma 모드: 프로젝트 생성 즉시 컬렉션 자동 생성
        if settings.vector_db_engine == "chroma":
            self._router.get_adapter(vector_db_id=proj.vector_db_id)
        self._audit_repo.log("create_project", company_id=company_id, resource=proj.project_code)
        return proj

    def list_all(self) -> list[Project]:
        return self._repo.list_all()

    def get(self, project_code: str) -> Project:
        proj = self._repo.get(project_code)
        if not proj:
            raise ProjectNotFoundError(f"project_code={project_code} not found")
        return proj

    def delete(self, project_code: str, company_id: str = "default") -> None:
        proj = self._repo.get(project_code)
        if not proj:
            raise ProjectNotFoundError(f"project_code={project_code} not found")

        docs = self._repo.list_docs(project_code)
        for doc in docs:
            try:
                self._router.get_adapter(vector_db_id=doc.assigned_vector_db).delete_by_doc_id(doc.doc_id)
            except Exception:
                pass
            self._doc_repo.delete(doc.doc_id)

        self._repo.delete(project_code)
        self._audit_repo.log("delete_project", company_id=company_id, resource=project_code)
