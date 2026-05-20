from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models.db_models import Base
from app.repositories.project_repository import ProjectRepository


def _connect_args(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(settings.database_url, connect_args=_connect_args(settings.database_url))
session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()
    with session_local() as db:
        ProjectRepository(db).ensure_default()


def get_db() -> Generator[Session, None, None]:
    db = session_local()
    try:
        yield db
    finally:
        db.close()


def _ensure_sqlite_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    inspector = inspect(engine)
    with engine.begin() as connection:
        if "wc_project_rag_doc" in inspector.get_table_names():
            columns = {column["name"] for column in inspector.get_columns("wc_project_rag_doc")}
            if "company_id" not in columns:
                connection.execute(
                    text("ALTER TABLE wc_project_rag_doc ADD COLUMN company_id VARCHAR(64) DEFAULT 'default' NOT NULL")
                )
        if "wc_dialog_history" in inspector.get_table_names():
            columns = {column["name"] for column in inspector.get_columns("wc_dialog_history")}
            if "company_id" not in columns:
                connection.execute(
                    text("ALTER TABLE wc_dialog_history ADD COLUMN company_id VARCHAR(64) DEFAULT 'default' NOT NULL")
                )
