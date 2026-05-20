from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.errors import http_error
from app.db.session import get_db
from app.models.schemas import (
    CategoryCreateRequest,
    CategoryRecord,
    CategoryResponse,
    ListCategoriesResponse,
)
from app.repositories.category_repository import CategoryRepository

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.post("", response_model=CategoryResponse, status_code=201)
def create_category(body: CategoryCreateRequest, db: Session = Depends(get_db)) -> CategoryResponse:
    repository = CategoryRepository(db)
    record = repository.create(body.category_mid, body.vector_db_id, body.category_low)
    return CategoryResponse(status="success", data=_to_response(record), error=None)


@router.get("", response_model=ListCategoriesResponse)
def list_categories(db: Session = Depends(get_db)) -> ListCategoriesResponse:
    repository = CategoryRepository(db)
    return ListCategoriesResponse(
        status="success",
        data=[_to_response(record) for record in repository.list_all()],
        error=None,
    )


@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)) -> dict:
    repository = CategoryRepository(db)
    deleted = repository.delete(category_id)
    if not deleted:
        raise http_error(404, "category_not_found", f"Unknown category: {category_id}")
    return {
        "status": "success",
        "data": {"category_id": category_id, "deleted": True},
        "error": None,
    }


def _to_response(record) -> CategoryRecord:
    return CategoryRecord(
        category_id=record.category_id,
        category_mid=record.category_mid,
        category_low=record.category_low,
        vector_db_id=record.vector_db_id,
    )
