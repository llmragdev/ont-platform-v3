import asyncio

from fastapi import APIRouter

from app.core.config import settings
from app.models.schemas import EmbedRequest, EmbedResponse
from app.services.embed_cache import embed_cache
from app.services.gemini_client import embed_text

router = APIRouter(prefix="/api/v1", tags=["embed"])


@router.post("/embed", response_model=EmbedResponse)
async def create_embedding(req: EmbedRequest) -> EmbedResponse:
    model = req.model or settings.embed_model
    tenant_id = req.effective_tenant_id

    cached = embed_cache.get(req.text, model, tenant_id)
    if cached is not None:
        return EmbedResponse(
            embedding=cached,
            model=model,
            dimension=len(cached),
            cached=True,
        )

    # CPU/IO 블로킹 호출을 스레드풀로 오프로드
    vector = await asyncio.to_thread(embed_text, req.text, model)

    embed_cache.set(req.text, model, vector, tenant_id)
    return EmbedResponse(
        embedding=vector,
        model=model,
        dimension=len(vector),
        cached=False,
    )
