from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import ensure_runtime_dirs
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_runtime_dirs()
    init_db()
    yield
