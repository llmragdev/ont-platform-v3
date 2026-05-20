from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from models.schemas import ProjectCreate, ProjectResponse, CategoryCreate, CategoryResponse
from repositories.meta_repo import ProjectRepository, CategoryRepository
from core.security import get_tenant_id
from typing import List

router = APIRouter(prefix="/api/v1/meta", tags=["metadata"])

@router.post("/projects", response_model=ProjectResponse)
def create_project(
    req: ProjectCreate,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    repo = ProjectRepository(db)
    # 중복 체크
    if repo.get_project(tenant_id, req.project_code):
        raise HTTPException(status_code=400, detail="Project already exists")
    
    return repo.create_project(
        tenant_id=tenant_id,
        project_code=req.project_code,
        project_name=req.project_name,
        vector_db_id=req.vector_db_id
    )

@router.get("/projects", response_model=List[ProjectResponse])
def list_projects(
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    repo = ProjectRepository(db)
    return repo.list_projects(tenant_id)

@router.post("/categories", response_model=CategoryResponse)
def create_category(
    req: CategoryCreate,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    repo = CategoryRepository(db)
    return repo.create_category(
        tenant_id=tenant_id,
        category_mid=req.category_mid,
        category_low=req.category_low,
        vector_db_id=req.vector_db_id
    )

@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    repo = CategoryRepository(db)
    return repo.list_categories(tenant_id)
