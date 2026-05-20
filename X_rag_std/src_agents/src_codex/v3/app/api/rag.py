from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import RequestContext, get_request_context
from app.db.session import get_db
from app.models.schemas import RagSearchRequest, RagSearchResponse
from app.services.rag_service import RagSearchService

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


@router.post("/search", response_model=RagSearchResponse)
def search_rag(
    request_body: RagSearchRequest,
    context: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> RagSearchResponse:
    service = RagSearchService(db)
    return service.search(request_body, context=context)


@router.post("/search/stream")
async def stream_rag(
    request_body: RagSearchRequest,
    context: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    service = RagSearchService(db)
    return StreamingResponse(
        service.stream_search(request_body, context=context),
        media_type="text/event-stream",
    )
