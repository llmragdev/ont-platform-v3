from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.db_models import Project, Category

class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, tenant_id: str, project_code: str, project_name: str, vector_db_id: str = None):
        project = Project(
            tenant_id=tenant_id,
            project_code=project_code,
            project_name=project_name,
            vector_db_id=vector_db_id
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_project(self, tenant_id: str, project_code: str):
        return self.db.query(Project).filter(
            and_(Project.tenant_id == tenant_id, Project.project_code == project_code)
        ).first()

    def list_projects(self, tenant_id: str):
        return self.db.query(Project).filter(Project.tenant_id == tenant_id).all()

class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_category(self, tenant_id: str, category_mid: str, category_low: str = None, vector_db_id: str = None):
        category = Category(
            tenant_id=tenant_id,
            category_mid=category_mid,
            category_low=category_low,
            vector_db_id=vector_db_id
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def list_categories(self, tenant_id: str):
        return self.db.query(Category).filter(Category.tenant_id == tenant_id).all()
