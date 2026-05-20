from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.schemas import RagSearchRequest, RagSearchResponse
from app.services.rag_service import RagSearchService

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


def _company_id(request: Request) -> str:
    return request.headers.get("X-Company-ID", "default")


@router.post("/search", response_model=RagSearchResponse)
def search_rag(
    request_body: RagSearchRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> RagSearchResponse:
    service = RagSearchService(db)
    return service.search(request_body, company_id=_company_id(request))


@router.post("/search/stream")
async def stream_rag(
    request_body: RagSearchRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    service = RagSearchService(db)
    return StreamingResponse(
        service.stream_search(request_body, company_id=_company_id(request)),
        media_type="text/event-stream",
    )
