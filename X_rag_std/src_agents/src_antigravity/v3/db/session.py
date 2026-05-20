import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models.db_models import Base

# v3용 데이터베이스 파일 경로
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rag_standard_v3.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    """FastAPI Dependency용 세션 생성기"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_new_session() -> Session:
    """
    asyncio.to_thread 등 백그라운드 스레드에서 사용할 
    독립적인 새로운 세션을 반환합니다.
    사용 후 반드시 session.close()를 호출해야 합니다.
    """
    return SessionLocal()
