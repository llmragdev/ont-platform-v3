from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import ensure_runtime_dirs
from app.db.session import get_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_runtime_dirs()
    init_db()
    db = next(get_db())
    try:
        from app.repositories.project_repo import ProjectRepository
        ProjectRepository(db).ensure_default()
    finally:
        db.close()
    yield
