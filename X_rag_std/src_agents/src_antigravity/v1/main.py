from fastapi import FastAPI, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from models import Base, RagSearchRequest, RagSearchResponse, DocumentUploadResponse, DocumentUploadResponseData
from database import engine, get_db
from rag_service import RagService

# SQLite DB 테이블 자동 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RAG Standard API (with SQLite)", version="1.0.0")

@app.post("/api/v1/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    category_mid: str = Form(...),
    category_low: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    상세설계 01: 임베딩 대상 문서 관리 파이프라인 트리거 엔드포인트
    """
    # Dummy implementation of Pipeline Trigger
    data = DocumentUploadResponseData(
        doc_id="doc_12345",
        file_name=file.filename,
        pipeline_status="pending",
        assigned_vector_db=f"vdb_{category_mid}_01"
    )
    return DocumentUploadResponse(status="success", data=data)

@app.post("/api/v1/rag/search", response_model=RagSearchResponse)
async def search_rag(request: RagSearchRequest, db: Session = Depends(get_db)):
    """
    상세설계 03: RAG 검색 및 역매핑 API
    Remote Retriever 패턴 및 디버그 모드 작동 (SQLite 연동 준비)
    """
    return RagService.process_search(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
