from sqlalchemy.orm import Session
from extn.models.userMdl import User

class UserSyncAntiRepository:
    def read_orm_with_tech_dep(self, db: Session, name: str = None):
        # 나쁜 예: 리포지토리가 외부 기술 상세(SQLAlchemy)를 직접 호출함
        print(f"[Rpo] 나쁜 사례 로그: 직접 SQLAlchemy 필터 쿼리(name={name})를 실행합니다.")
        query = db.query(User)
        if name:
            query = query.filter(User.name == name)
        return query.all()