from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.schemas import RagSearchRequest, RagSearchResponse
from app.services.rag_service import RagSearchService

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


@router.post("/search", response_model=RagSearchResponse)
def search(
    request_body: RagSearchRequest,
    x_tenant_id: str = Header(..., description="Tenant ID (required)"),
    x_org_id: str | None = Header(None, description="Organization ID (optional)"),
    db: Session = Depends(get_db),
):
    service = RagSearchService(db)
    return service.search(
        request_body,
        tenant_id=x_tenant_id,
        org_id=x_org_id,
    )


@router.post("/search/stream")
async def stream_search(
    request_body: RagSearchRequest,
    x_tenant_id: str = Header(..., description="Tenant ID (required)"),
    x_org_id: str | None = Header(None, description="Organization ID (optional)"),
    db: Session = Depends(get_db),
):
    """SSE 스트리밍 엔드포인트 — LLM 응답을 청크 단위로 클라이언트에 전송."""
    service = RagSearchService(db)
    return StreamingResponse(
        service.stream_search(
            request_body,
            tenant_id=x_tenant_id,
            org_id=x_org_id,
        ),
        media_type="text/event-stream",
    )
