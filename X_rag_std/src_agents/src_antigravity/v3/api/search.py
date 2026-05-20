import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from db.session import get_db, get_new_session
from models.schemas import RagSearchRequest, RagSearchResponse
from services.rag_service import RagSearchService
from core.security import get_tenant_id, get_org_id

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])

@router.post("/search", response_model=RagSearchResponse)
async def search_rag(
    request: RagSearchRequest,
    tenant_id: str = Depends(get_tenant_id),
    org_id: str = Depends(get_org_id),
    db: Session = Depends(get_db)
):
    # 스레드 안전성 확보를 위해 독립 세션 사용
    def run_search():
        new_db = get_new_session()
        try:
            search_service = RagSearchService(new_db)
            return search_service.process_search(
                request, 
                tenant_id=tenant_id, 
                org_id=org_id
            )
        finally:
            new_db.close()

    return await asyncio.to_thread(run_search)

@router.post("/search/stream")
async def search_rag_stream(
    request: RagSearchRequest,
    tenant_id: str = Depends(get_tenant_id),
    org_id: str = Depends(get_org_id),
    db: Session = Depends(get_db)
):
    search_service = RagSearchService(db)
    return StreamingResponse(
        search_service.process_search_stream(request, tenant_id, org_id),
        media_type="text/event-stream"
    )
