from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db_models import Category


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        category_mid: str,
        vector_db_id: str,
        category_low: str | None = None,
    ) -> Category:
        record = Category(
            category_mid=category_mid,
            category_low=category_low,
            vector_db_id=vector_db_id,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_all(self) -> list[Category]:
        stmt = select(Category).order_by(Category.category_mid.asc(), Category.category_id.asc())
        return list(self.db.scalars(stmt))

    def delete(self, category_id: int) -> bool:
        record = self.db.get(Category, category_id)
        if record is None:
            return False
        self.db.delete(record)
        self.db.commit()
        return True
