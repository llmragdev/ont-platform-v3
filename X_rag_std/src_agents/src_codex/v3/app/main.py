from fastapi import FastAPI

from app.api.categories import router as categories_router
from app.api.documents import router as documents_router
from app.api.projects import router as projects_router
from app.api.rag import router as rag_router
from app.core.config import ensure_runtime_dirs, settings
from app.db.session import init_db


def create_app() -> FastAPI:
    ensure_runtime_dirs()
    init_db()

    app = FastAPI(
        title="Enterprise RAG Standard Backend - Codex",
        version="1.0.0",
        description="Remote Retriever based RAG backend following X_rag_std specs.",
    )
    app.include_router(projects_router)
    app.include_router(categories_router)
    app.include_router(documents_router)
    app.include_router(rag_router)

    @app.get("/api/v1/health")
    def health() -> dict:
        return {
            "status": "success",
            "data": {
                "service": "src_codex_rag_backend",
                "storage_root": str(settings.storage_root),
            },
            "error": None,
        }

    return app


app = create_app()
