import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 환경 변수에서 DB URL을 읽어옵니다. (기본값: 로컬 SQLite)
# 향후 PostgreSQL로 변경 시 환경 변수만 "postgresql://user:pass@localhost/dbname" 로 바꾸면 소스 코드 수정이 필요 없습니다.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rag_standard.db")

# SQLite인 경우에만 check_same_thread 옵션을 추가하고, 다른 DB(PostgreSQL, MySQL 등)는 일반 엔진을 생성합니다.
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
