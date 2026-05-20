import asyncio

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.models.schemas import GenerateRequest, GenerateResponse
from app.services.gemini_client import generate_text, stream_text

router = APIRouter(prefix="/api/v1", tags=["generate"])


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest) -> GenerateResponse:
    model = req.model or settings.llm_model
    answer = await asyncio.to_thread(generate_text, req.prompt, model, req.max_tokens)
    return GenerateResponse(answer=answer, model=model)


@router.post("/generate/stream")
async def generate_stream(req: GenerateRequest) -> StreamingResponse:
    model = req.model or settings.llm_model

    async def event_generator():
        async for chunk in stream_text(req.prompt, model, req.max_tokens):
            yield chunk
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
