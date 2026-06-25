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
from app.repositories.category_repo import CategoryRepository

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.post("", response_model=CategoryResponse, status_code=201)
def create_category(body: CategoryCreateRequest, db: Session = Depends(get_db)):
    repo = CategoryRepository(db)
    cat = repo.create(
        category_mid=body.category_mid,
        vector_db_id=body.vector_db_id,
        category_low=body.category_low,
    )
    return CategoryResponse(
        status="success",
        data=CategoryRecord(
            category_id=cat.category_id,
            category_mid=cat.category_mid,
            category_low=cat.category_low,
            vector_db_id=cat.vector_db_id,
        ),
    )


@router.get("", response_model=ListCategoriesResponse)
def list_categories(db: Session = Depends(get_db)):
    repo = CategoryRepository(db)
    cats = repo.list_all()
    return ListCategoriesResponse(
        status="success",
        data=[
            CategoryRecord(
                category_id=c.category_id,
                category_mid=c.category_mid,
                category_low=c.category_low,
                vector_db_id=c.vector_db_id,
            )
            for c in cats
        ],
    )


@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    repo = CategoryRepository(db)
    deleted = repo.delete(category_id)
    if not deleted:
        raise http_error(404, "category_not_found", f"category_id={category_id} not found")
    return {"status": "success", "data": {"category_id": category_id, "deleted": True}, "error": None}
