import asyncio
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from db.session import get_db, get_new_session
from models.schemas import DocumentUploadResponse, DocumentUploadResponseData
from services.pipeline import DocumentPipelineService
from core.security import get_tenant_id, get_org_id

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    project_code: str = Form("000001"), # 기본값 유지하되 Form으로 수신 가능
    org_id: str = Depends(get_org_id), # 헤더에서 수신
    tenant_id: str = Depends(get_tenant_id), # 헤더 필수 검증
    db: Session = Depends(get_db)
):
    # 스레드 풀에서 실행할 때 독립된 새 세션 사용 (Thread-safety 확보)
    def run_pipeline():
        new_db = get_new_session()
        try:
            pipeline_service = DocumentPipelineService(new_db)
            return pipeline_service.process_upload(
                tenant_id=tenant_id,
                project_code=project_code,
                file=file,
                org_id=org_id
            )
        finally:
            new_db.close()

    doc_record = await asyncio.to_thread(run_pipeline)
    
    data = DocumentUploadResponseData(
        doc_id=doc_record.doc_id,
        file_name=doc_record.file_name,
        pipeline_status=doc_record.pipeline_status,
        assigned_vector_db=doc_record.assigned_vector_db
    )
    
    return DocumentUploadResponse(status="success", data=data)

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    repo = DocRepository(db)
    vdb_id = repo.delete_doc(doc_id, tenant_id)
    if vdb_id:
        adapter = VectorDbRouter.get_adapter(vdb_id)
        adapter.delete_by_doc_id(doc_id, tenant_id)
        return {"status": "success", "message": f"Document {doc_id} deleted"}
    raise HTTPException(status_code=404, detail="Document not found")

@router.put("/{doc_id}", response_model=DocumentUploadResponse)
async def update_document(
    doc_id: str,
    file: UploadFile = File(...),
    project_code: str = Form("000001"),
    org_id: str = Depends(get_org_id),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    repo = DocRepository(db)
    # 1. 기존 문서 삭제 (Vector DB 포함)
    vdb_id = repo.delete_doc(doc_id, tenant_id)
    if vdb_id:
        adapter = VectorDbRouter.get_adapter(vdb_id)
        adapter.delete_by_doc_id(doc_id, tenant_id)
    
    # 2. 새 문서로 재업로드 (pipeline 실행)
    def run_pipeline():
        new_db = get_new_session()
        try:
            pipeline_service = DocumentPipelineService(new_db)
            return pipeline_service.process_upload(
                tenant_id=tenant_id,
                project_code=project_code,
                file=file,
                org_id=org_id
            )
        finally:
            new_db.close()

    doc_record = await asyncio.to_thread(run_pipeline)
    
    data = DocumentUploadResponseData(
        doc_id=doc_record.doc_id,
        file_name=doc_record.file_name,
        pipeline_status=doc_record.pipeline_status,
        assigned_vector_db=doc_record.assigned_vector_db
    )
    
    return DocumentUploadResponse(status="success", data=data)
