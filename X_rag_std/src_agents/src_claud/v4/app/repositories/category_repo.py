from sqlalchemy.orm import Session

from app.models.db_models import Category


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, category_mid: str, vector_db_id: str, category_low: str | None = None) -> Category:
        cat = Category(category_mid=category_mid, category_low=category_low, vector_db_id=vector_db_id)
        self.db.add(cat)
        self.db.commit()
        self.db.refresh(cat)
        return cat

    def get(self, category_id: int) -> Category | None:
        return self.db.query(Category).filter(Category.category_id == category_id).first()

    def list_all(self) -> list[Category]:
        return self.db.query(Category).all()

    def find_by_mid(self, category_mid: str) -> list[Category]:
        return self.db.query(Category).filter(Category.category_mid == category_mid).all()

    def delete(self, category_id: int) -> bool:
        cat = self.get(category_id)
        if not cat:
            return False
        self.db.delete(cat)
        self.db.commit()
        return True
