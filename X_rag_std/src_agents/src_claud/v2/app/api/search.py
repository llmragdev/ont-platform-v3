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
def search(
    request_body: RagSearchRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    service = RagSearchService(db)
    return service.search(request_body, company_id=_company_id(request))


@router.post("/search/stream")
async def stream_search(
    request_body: RagSearchRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """SSE 스트리밍 엔드포인트 — LLM 응답을 청크 단위로 클라이언트에 전송."""
    service = RagSearchService(db)
    return StreamingResponse(
        service.stream_search(request_body, company_id=_company_id(request)),
        media_type="text/event-stream",
    )
