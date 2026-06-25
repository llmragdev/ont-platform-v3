from fastapi import APIRouter, Depends, File, Form, Header, UploadFile
from sqlalchemy.orm import Session

from app.core.errors import DocumentNotFoundError, http_error
from app.db.session import get_db
from app.models.schemas import DocumentRecord, DocumentUploadResponse, ListDocumentsResponse
from app.repositories.document_repo import DocumentRepository
from app.services.document_service import DocumentPipelineService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    category_mid: str = Form(...),
    category_large: str = Form(None),
    vector_db_id: str = Form(None),
    category_low: str = Form(None),
    project_code: str = Form("000001"),
    org_id: str = Form(None),
    x_tenant_id: str = Header(..., description="Tenant ID (required)"),
    x_org_id: str | None = Header(None, description="Organization ID (optional)"),
    db: Session = Depends(get_db),
):
    service = DocumentPipelineService(db)
    return await service.upload(
        file=file,
        category_large=category_large,
        category_mid=category_mid,
        vector_db_id=vector_db_id,
        category_low=category_low,
        tenant_id=x_tenant_id,
        org_id=x_org_id or org_id,
        project_code=project_code,
    )


@router.put("/{doc_id}", response_model=DocumentUploadResponse)
async def update_document(
    doc_id: str,
    file: UploadFile = File(...),
    x_tenant_id: str = Header(..., description="Tenant ID (required)"),
    x_org_id: str | None = Header(None, description="Organization ID (optional)"),
    db: Session = Depends(get_db),
):
    service = DocumentPipelineService(db)
    try:
        return await service.update(
            doc_id=doc_id,
            file=file,
            tenant_id=x_tenant_id,
            org_id=x_org_id,
        )
    except DocumentNotFoundError as exc:
        raise http_error(404, exc.error_code, exc.message)


@router.get("", response_model=ListDocumentsResponse)
def list_documents(
    x_tenant_id: str = Header(..., description="Tenant ID (required)"),
    db: Session = Depends(get_db),
):
    repo = DocumentRepository(db)
    records = repo.list_by_tenant(x_tenant_id)
    documents = [
        DocumentRecord(
            doc_id=r.doc_id,
            tenant_id=r.tenant_id,
            org_id=r.org_id,
            file_name=r.file_name,
            pipeline_status=r.pipeline_status,
            assigned_vector_db=r.assigned_vector_db,
            category_mid=r.category_mid,
            category_low=r.category_low,
            version=r.version,
            error_message=r.error_message,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in records
    ]
    return ListDocumentsResponse(
        status="success",
        data=documents,
        documents=documents,
        error=None,
    )


@router.delete("/{doc_id}")
def delete_document(
    doc_id: str,
    x_tenant_id: str = Header(..., description="Tenant ID (required)"),
    db: Session = Depends(get_db),
):
    service = DocumentPipelineService(db)
    try:
        service.delete(doc_id, tenant_id=x_tenant_id)
    except DocumentNotFoundError as exc:
        raise http_error(404, exc.error_code, exc.message)
    return {"status": "success", "data": {"doc_id": doc_id, "deleted": True}, "error": None}
