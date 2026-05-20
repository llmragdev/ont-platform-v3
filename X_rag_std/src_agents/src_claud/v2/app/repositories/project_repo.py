import random
import string

from sqlalchemy.orm import Session

from app.models.db_models import Project, ProjectRagDocument


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _gen_code() -> str:
        return "".join(random.choices(string.digits, k=6))

    def create(self, project_name: str, vector_db_id: str, project_code: str | None = None) -> Project:
        code = project_code or self._gen_code()
        while not project_code and self.get(code):
            code = self._gen_code()
        proj = Project(project_code=code, project_name=project_name, vector_db_id=vector_db_id)
        self.db.add(proj)
        self.db.commit()
        self.db.refresh(proj)
        return proj

    def get(self, project_code: str) -> Project | None:
        return self.db.query(Project).filter(Project.project_code == project_code).first()

    def list_all(self) -> list[Project]:
        return self.db.query(Project).all()

    def delete(self, project_code: str) -> bool:
        proj = self.get(project_code)
        if not proj:
            return False
        self.db.delete(proj)
        self.db.commit()
        return True

    def list_docs(self, project_code: str) -> list[ProjectRagDocument]:
        return (
            self.db.query(ProjectRagDocument)
            .filter(ProjectRagDocument.project_code == project_code)
            .all()
        )

    def ensure_default(self) -> None:
        if not self.get("000001"):
            proj = Project(
                project_code="000001",
                project_name="기본 프로젝트",
                vector_db_id="vdb_default_01",
            )
            self.db.add(proj)
            self.db.commit()
