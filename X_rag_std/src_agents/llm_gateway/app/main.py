from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import embed, generate, health
from app.core.config import settings
from app.core.key_pool import key_pool


@asynccontextmanager
async def lifespan(application: FastAPI):
    print(f"[LLM Gateway] 시작 — 키 풀: {key_pool.pool_size}개, 임베딩 모델: {settings.embed_model}")
    yield
    print("[LLM Gateway] 종료")


app = FastAPI(
    title="LLM Gateway",
    description="Gemini 임베딩 / 생성 API 게이트웨이 — 멀티테넌트, 키 로테이션",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(embed.router)
app.include_router(generate.router)
app.include_router(health.router)
