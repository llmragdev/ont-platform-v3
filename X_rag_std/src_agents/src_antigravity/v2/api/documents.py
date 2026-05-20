import asyncio
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from models.schemas import DocumentUploadResponse, DocumentUploadResponseData
from services.pipeline import DocumentPipelineService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    category_mid: str = Form(...),
    category_low: str = Form(None),
    db: Session = Depends(get_db)
):
    pipeline_service = DocumentPipelineService(db)
    
    # 파이프라인 실제 실행을 스레드 풀에서 실행 (저장 -> 추출 -> 청킹 -> VectorDB 적재)
    doc_record = await asyncio.to_thread(
        pipeline_service.process_upload, 
        file=file, 
        category_mid=category_mid
    )
    
    data = DocumentUploadResponseData(
        doc_id=doc_record.doc_id,
        file_name=doc_record.file_name,
        pipeline_status=doc_record.pipeline_status,
        assigned_vector_db=doc_record.assigned_vector_db
    )
    
    return DocumentUploadResponse(status="success", data=data)
