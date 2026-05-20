import random
import string

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db_models import Project, ProjectRagDocument


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        project_name: str,
        vector_db_id: str,
        project_code: str | None = None,
        tenant_id: str = "default",
    ) -> Project:
        code = project_code or self._generate_code()
        while project_code is None and self.get(code) is not None:
            code = self._generate_code()
        record = Project(
            project_code=code,
            tenant_id=tenant_id,
            project_name=project_name,
            vector_db_id=vector_db_id,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def ensure_default(self) -> None:
        if self.get("000001") is not None:
            return
        self.db.add(
            Project(
                project_code="000001",
                tenant_id="default",
                project_name="기본 프로젝트",
                vector_db_id="vdb_default_01",
            )
        )
        self.db.commit()

    def get(self, project_code: str) -> Project | None:
        return self.db.get(Project, project_code)

    def list_all(self) -> list[Project]:
        return list(self.db.scalars(select(Project).order_by(Project.project_code.asc())))

    def list_documents(self, project_code: str) -> list[ProjectRagDocument]:
        stmt = select(ProjectRagDocument).where(ProjectRagDocument.project_code == project_code)
        return list(self.db.scalars(stmt))

    def delete(self, project_code: str) -> bool:
        record = self.get(project_code)
        if record is None:
            return False
        self.db.delete(record)
        self.db.commit()
        return True

    @staticmethod
    def _generate_code() -> str:
        return "".join(random.choices(string.digits, k=6))
