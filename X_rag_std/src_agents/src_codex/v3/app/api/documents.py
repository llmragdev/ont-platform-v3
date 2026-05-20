from datetime import datetime
from datetime import UTC

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api.dependencies import RequestContext, get_request_context
from app.core.errors import http_error
from app.db.session import get_db
from app.models.db_models import ProjectRagDocument
from app.models.schemas import (
    DocumentRecordResponse,
    DocumentUploadData,
    DocumentUploadResponse,
    ListDocumentsResponse,
)
from app.services.document_pipeline import DocumentPipelineService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    category_mid: str = Form(...),
    category_low: str | None = Form(default=None),
    vector_db_id: str | None = Form(default=None),
    context: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    service = DocumentPipelineService(db)
    record = await service.upload_document(
        file,
        category_mid,
        category_low,
        vector_db_id,
        tenant_id=context.tenant_id,
        org_id=context.org_id,
    )
    return DocumentUploadResponse(
        status="success",
        data=DocumentUploadData(
            doc_id=record.doc_id,
            file_name=record.file_name,
            pipeline_status=record.pipeline_status,
            assigned_vector_db=record.assigned_vector_db,
        ),
        error=None,
    )


@router.put("/{doc_id}", response_model=DocumentUploadResponse)
async def update_document(
    doc_id: str,
    file: UploadFile = File(...),
    category_mid: str = Form(...),
    category_low: str | None = Form(default=None),
    vector_db_id: str | None = Form(default=None),
    context: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    service = DocumentPipelineService(db)
    try:
        record = await service.update_document(
            doc_id,
            file,
            category_mid,
            category_low,
            vector_db_id,
            tenant_id=context.tenant_id,
            org_id=context.org_id,
        )
    except KeyError as exc:
        raise http_error(404, "document_not_found", str(exc)) from exc

    return DocumentUploadResponse(
        status="success",
        data=DocumentUploadData(
            doc_id=record.doc_id,
            file_name=record.file_name,
            pipeline_status=record.pipeline_status,
            assigned_vector_db=record.assigned_vector_db,
        ),
        error=None,
    )


@router.get("", response_model=ListDocumentsResponse)
def list_documents(
    context: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> ListDocumentsResponse:
    service = DocumentPipelineService(db)
    return ListDocumentsResponse(
        status="success",
        data=[_to_response(record) for record in service.list_documents(context.tenant_id)],
        error=None,
    )


@router.delete("/{doc_id}")
def delete_document(
    doc_id: str,
    context: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> dict:
    service = DocumentPipelineService(db)
    try:
        deleted = service.delete_document(doc_id, tenant_id=context.tenant_id)
    except KeyError as exc:
        raise http_error(404, "document_not_found", str(exc)) from exc
    return {
        "status": "success",
        "data": {"doc_id": doc_id, "deleted": deleted},
        "error": None,
    }


def _to_response(record: ProjectRagDocument) -> DocumentRecordResponse:
    def iso(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.isoformat()

    return DocumentRecordResponse(
        doc_id=record.doc_id,
        project_code=record.project_code,
        tenant_id=record.tenant_id,
        org_id=record.org_id,
        file_name=record.file_name,
        source_url=record.source_url,
        pipeline_status=record.pipeline_status,
        assigned_vector_db=record.assigned_vector_db,
        category_mid=record.category_mid,
        category_low=record.category_low,
        error_message=record.error_message,
        version=record.version,
        created_at=iso(record.created_at),
        updated_at=iso(record.updated_at),
    )
