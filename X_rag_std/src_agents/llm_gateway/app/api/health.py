import asyncio

from fastapi import APIRouter

from app.core.config import settings
from app.models.schemas import HealthItem, HealthResponse
from app.services.gemini_client import embed_text

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    checks: list[HealthItem] = []

    checks.append(HealthItem(
        name="api_key",
        status="ok" if settings.gemini_api_key else "error",
        detail="GEMINI_API_KEY 설정됨" if settings.gemini_api_key else "GEMINI_API_KEY 없음",
    ))

    try:
        await asyncio.to_thread(embed_text, "ping", settings.embed_model)
        checks.append(HealthItem(name="gemini_embed", status="ok", detail=settings.embed_model))
    except Exception as exc:
        checks.append(HealthItem(name="gemini_embed", status="error", detail=str(exc)[:120]))

    overall = "ok" if all(c.status == "ok" for c in checks) else "degraded"
    return HealthResponse(status=overall, checks=checks)
