from fastapi import FastAPI
from api import documents, search, meta, admin
from db.session import init_db

app = FastAPI(title="Antigravity RAG API v3", version="3.0.0")

# DB 초기화 및 테이블 생성
@app.on_event("startup")
def startup_event():
    init_db()

app.include_router(documents.router)
app.include_router(search.router)
app.include_router(meta.router)
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {"message": "Antigravity RAG API v3 is running", "standard": "v1.3"}
