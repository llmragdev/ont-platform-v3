from fastapi import FastAPI

from app.api import documents, health, search
from app.core.events import lifespan

app = FastAPI(
    title="Claude RAG API",
    description="Enterprise Ontology RAG — Claude Code 설계안 (v1·Codex 계승)",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(documents.router)
app.include_router(search.router)
app.include_router(health.router)
