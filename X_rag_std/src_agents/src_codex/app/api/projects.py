from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.errors import http_error
from app.db.session import get_db
from app.models.schemas import (
    ListProjectsResponse,
    ProjectCreateRequest,
    ProjectRecord,
    ProjectResponse,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(body: ProjectCreateRequest, db: Session = Depends(get_db)) -> ProjectResponse:
    service = ProjectService(db)
    record = service.create(body.project_name, body.vector_db_id, body.project_code)
    return ProjectResponse(status="success", data=_to_response(record), error=None)


@router.get("", response_model=ListProjectsResponse)
def list_projects(db: Session = Depends(get_db)) -> ListProjectsResponse:
    service = ProjectService(db)
    return ListProjectsResponse(
        status="success",
        data=[_to_response(record) for record in service.list_all()],
        error=None,
    )


@router.get("/{project_code}", response_model=ProjectResponse)
def get_project(project_code: str, db: Session = Depends(get_db)) -> ProjectResponse:
    service = ProjectService(db)
    try:
        record = service.get(project_code)
    except KeyError as exc:
        raise http_error(404, "project_not_found", str(exc)) from exc
    return ProjectResponse(status="success", data=_to_response(record), error=None)


@router.delete("/{project_code}")
def delete_project(project_code: str, db: Session = Depends(get_db)) -> dict:
    service = ProjectService(db)
    try:
        deleted = service.delete(project_code)
    except KeyError as exc:
        raise http_error(404, "project_not_found", str(exc)) from exc
    return {
        "status": "success",
        "data": {"project_code": project_code, "deleted": deleted},
        "error": None,
    }


def _to_response(record) -> ProjectRecord:
    return ProjectRecord(
        project_code=record.project_code,
        project_name=record.project_name,
        vector_db_id=record.vector_db_id,
    )
