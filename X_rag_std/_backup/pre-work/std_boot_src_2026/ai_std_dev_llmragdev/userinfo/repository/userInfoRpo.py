from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, create_engine, or_
from sqlalchemy.orm import declarative_base, sessionmaker

from userinfo.schemas.userInfoSch import UserInfoRead, UserInfoSearch, UserInfoSettings


Base = declarative_base()


class User(Base):
    __tablename__ = "temp_users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)


class UserInfoRepository:
    def __init__(self):
        settings = UserInfoSettings()
        self.engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)
        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

    def list_users(self, search: UserInfoSearch) -> list[UserInfoRead]:
        db = self.session_factory()
        try:
            query = db.query(User).order_by(User.id.asc())
            keyword = (search.keyword or "").strip()

            if keyword:
                like_keyword = f"%{keyword}%"
                query = query.filter(
                    or_(
                        User.name.ilike(like_keyword),
                        User.email.ilike(like_keyword),
                    )
                )

            rows = query.limit(search.limit).all()
            return [UserInfoRead.model_validate(row) for row in rows]
        finally:
            db.close()

    def count_users(self, keyword: str | None = None) -> int:
        db = self.session_factory()
        try:
            query = db.query(User)
            keyword = (keyword or "").strip()

            if keyword:
                like_keyword = f"%{keyword}%"
                query = query.filter(
                    or_(
                        User.name.ilike(like_keyword),
                        User.email.ilike(like_keyword),
                    )
                )

            return query.count()
        finally:
            db.close()
