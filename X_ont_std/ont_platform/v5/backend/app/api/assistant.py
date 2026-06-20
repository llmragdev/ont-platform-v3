from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_tenant_context
from app.models.assistant import AssistantChatRequest, AssistantChatResponse
from app.models.tenant_context import TenantContext
from app.services.assistant_service import AssistantService


router = APIRouter(prefix="/api/assistant", tags=["assistant"])


def get_assistant_service() -> AssistantService:
    return AssistantService()


@router.post("/chat", response_model=AssistantChatResponse)
def chat(
    request: AssistantChatRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    service: AssistantService = Depends(get_assistant_service),
) -> AssistantChatResponse:
    request.context.company_id = request.context.company_id or ctx.company_id
    request.context.project_id = request.context.project_id or ctx.project_id
    request.context.user_id = request.context.user_id or ctx.user_id
    request.context.role = request.context.role or ctx.role
    return service.chat(request)

