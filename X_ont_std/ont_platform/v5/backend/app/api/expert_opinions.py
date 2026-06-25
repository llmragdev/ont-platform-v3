"""
Expert Opinions API Router

Endpoints:
- GET /api/expert-opinions - List all opinions
- POST /api/expert-opinions - Create opinion
- DELETE /api/expert-opinions/{opinion_id} - Delete opinion
"""

from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel

from app.core.context import TenantContext
from app.services.expert_opinion_service import ExpertOpinionService

router = APIRouter(prefix="/api", tags=["expert-opinions"])
service = ExpertOpinionService()


class ExpertOpinionPayload(BaseModel):
    """Request payload for creating expert opinion."""
    expert_name: str
    role: str
    topic: str
    opinion: str
    keywords: list[str] = []
    confidence_adjustment: float = 0.0


class ExpertOpinionResponse(BaseModel):
    """Response for expert opinion."""
    id: str
    project_id: str
    expert_name: str
    role: str
    topic: str
    opinion: str
    keywords: list[str]
    confidence_adjustment: float
    created_at: str
    updated_at: str


def _get_tenant_context(
    x_user_id: str = Header(...),
    x_company_id: str = Header(...),
    x_project_id: str = Header(...),
    x_role: str = Header(default="user"),
) -> TenantContext:
    """Extract tenant context from headers."""
    return TenantContext(
        user_id=x_user_id,
        company_id=x_company_id,
        project_id=x_project_id,
        role=x_role,
    )


@router.get("/expert-opinions")
async def list_opinions(ctx: TenantContext = Depends(_get_tenant_context)) -> list[dict]:
    """List all expert opinions for the project."""
    try:
        opinions = service.list_opinions(ctx)
        return opinions
    except Exception:
        return []


@router.post("/expert-opinions")
async def create_opinion(
    payload: ExpertOpinionPayload,
    x_user_id: str = Header(...),
    x_company_id: str = Header(...),
    x_project_id: str = Header(...),
    x_role: str = Header(default="user"),
) -> dict:
    """Create a new expert opinion."""
    ctx = TenantContext(
        user_id=x_user_id,
        company_id=x_company_id,
        project_id=x_project_id,
        role=x_role,
    )
    opinion = service.create_opinion(ctx, payload.model_dump())
    return opinion


@router.delete("/expert-opinions/{opinion_id}")
async def delete_opinion(
    opinion_id: str,
    x_user_id: str = Header(...),
    x_company_id: str = Header(...),
    x_project_id: str = Header(...),
    x_role: str = Header(default="user"),
) -> dict:
    """Delete an expert opinion."""
    ctx = TenantContext(
        user_id=x_user_id,
        company_id=x_company_id,
        project_id=x_project_id,
        role=x_role,
    )
    result = service.delete_opinion(ctx, opinion_id)
    return {"deleted": opinion_id, "success": result}
