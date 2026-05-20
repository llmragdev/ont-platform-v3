from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.errors import ProjectNotFoundError, http_error
from app.db.session import get_db
from app.models.schemas import (
    ProjectCreateRequest,
    ProjectRecord,
    ProjectResponse,
    ListProjectsResponse,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


def _company_id(request: Request) -> str:
    return request.headers.get("X-Company-ID", "default")


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(body: ProjectCreateRequest, request: Request, db: Session = Depends(get_db)):
    svc = ProjectService(db)
    proj = svc.create(
        project_name=body.project_name,
        vector_db_id=body.vector_db_id,
        project_code=body.project_code,
        company_id=_company_id(request),
    )
    return ProjectResponse(
        status="success",
        data=ProjectRecord(
            project_code=proj.project_code,
            project_name=proj.project_name,
            vector_db_id=proj.vector_db_id,
        ),
    )


@router.get("", response_model=ListProjectsResponse)
def list_projects(db: Session = Depends(get_db)):
    svc = ProjectService(db)
    projects = svc.list_all()
    return ListProjectsResponse(
        status="success",
        data=[
            ProjectRecord(
                project_code=p.project_code,
                project_name=p.project_name,
                vector_db_id=p.vector_db_id,
            )
            for p in projects
        ],
    )


@router.get("/{project_code}", response_model=ProjectResponse)
def get_project(project_code: str, db: Session = Depends(get_db)):
    svc = ProjectService(db)
    try:
        proj = svc.get(project_code)
    except ProjectNotFoundError as exc:
        raise http_error(404, exc.error_code, exc.message)
    return ProjectResponse(
        status="success",
        data=ProjectRecord(
            project_code=proj.project_code,
            project_name=proj.project_name,
            vector_db_id=proj.vector_db_id,
        ),
    )


@router.delete("/{project_code}")
def delete_project(project_code: str, request: Request, db: Session = Depends(get_db)):
    svc = ProjectService(db)
    try:
        svc.delete(project_code, company_id=_company_id(request))
    except ProjectNotFoundError as exc:
        raise http_error(404, exc.error_code, exc.message)
    return {"status": "success", "data": {"project_code": project_code, "deleted": True}, "error": None}
