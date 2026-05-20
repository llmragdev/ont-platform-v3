import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core import config as config_module
from app.db.session import get_db
from app.main import app
from app.models.db_models import Base


@pytest.fixture
def test_db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db_engine):
    test_session = sessionmaker(bind=test_db_engine, autocommit=False, autoflush=False)
    session = test_session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(db_session, tmp_path, monkeypatch):
    routing_config = tmp_path / "vector_routing.json"
    routing_config.write_text(
        json.dumps(
            {
                "routing_rules": [
                    {
                        "vector_db_id": "vdb_policy_01",
                        "target_category_mid": ["policy", "규정"],
                        "engine_type": "local_json",
                        "connection": {"collection_name": "policy"},
                    },
                    {
                        "vector_db_id": "vdb_tech_01",
                        "target_category_mid": ["IT", "tech"],
                        "engine_type": "local_json",
                        "connection": {"collection_name": "tech"},
                    },
                    {
                        "vector_db_id": "vdb_default_01",
                        "target_category_mid": ["default"],
                        "engine_type": "local_json",
                        "connection": {"collection_name": "default"},
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(config_module.settings, "storage_root", tmp_path / "storage")
    monkeypatch.setattr(config_module.settings, "raw_documents_dir", tmp_path / "raw")
    monkeypatch.setattr(config_module.settings, "processed_dir", tmp_path / "processed")
    monkeypatch.setattr(config_module.settings, "vector_store_dir", tmp_path / "vector_store")
    monkeypatch.setattr(config_module.settings, "routing_config_path", routing_config)
    monkeypatch.setattr(config_module.settings, "embedding_provider", "hash")
    monkeypatch.setattr(config_module.settings, "llm_provider", "mock")
    (tmp_path / "raw").mkdir()
    (tmp_path / "processed").mkdir()
    (tmp_path / "vector_store").mkdir()

    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

