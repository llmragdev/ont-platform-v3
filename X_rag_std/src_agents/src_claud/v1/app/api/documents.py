from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.errors import DocumentNotFoundError, http_error
from app.db.session import get_db
from app.models.schemas import DocumentRecord, DocumentUploadResponse, ListDocumentsResponse
from app.repositories.document_repo import DocumentRepository
from app.services.document_service import DocumentPipelineService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def _company_id(request: Request) -> str:
    return request.headers.get("X-Company-ID", "default")


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    category_mid: str = Form(...),
    vector_db_id: str = Form(None),
    category_low: str = Form(None),
    db: Session = Depends(get_db),
):
    service = DocumentPipelineService(db)
    return await service.upload(
        file=file,
        category_mid=category_mid,
        vector_db_id=vector_db_id,
        category_low=category_low,
        company_id=_company_id(request),
    )


@router.put("/{doc_id}", response_model=DocumentUploadResponse)
async def update_document(
    doc_id: str,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    service = DocumentPipelineService(db)
    try:
        return await service.update(
            doc_id=doc_id, file=file, company_id=_company_id(request)
        )
    except DocumentNotFoundError as exc:
        raise http_error(404, exc.error_code, exc.message)


@router.get("", response_model=ListDocumentsResponse)
def list_documents(request: Request, db: Session = Depends(get_db)):
    repo = DocumentRepository(db)
    records = repo.list_by_company(_company_id(request))
    return ListDocumentsResponse(
        status="success",
        data=[
            DocumentRecord(
                doc_id=r.doc_id,
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
        ],
        error=None,
    )


@router.delete("/{doc_id}")
def delete_document(doc_id: str, request: Request, db: Session = Depends(get_db)):
    service = DocumentPipelineService(db)
    try:
        service.delete(doc_id, company_id=_company_id(request))
    except DocumentNotFoundError as exc:
        raise http_error(404, exc.error_code, exc.message)
    return {"status": "success", "data": {"doc_id": doc_id, "deleted": True}, "error": None}
