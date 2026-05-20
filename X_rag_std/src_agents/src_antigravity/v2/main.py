from fastapi import FastAPI
from db.session import engine
from models.db_models import Base
from api.documents import router as doc_router
from api.search import router as search_router

# 앱 실행 시점에 SQLite 테이블 자동 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RAG Standard API v2 (Production-Ready)", version="2.0.0")

app.include_router(doc_router)
app.include_router(search_router)
