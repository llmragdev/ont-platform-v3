import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import app
from app.models.db_models import Base


@pytest.fixture(scope="session")
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
    TestSession = sessionmaker(
        bind=test_db_engine, autocommit=False, autoflush=False
    )
    session = TestSession()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def routing_config(tmp_path):
    cfg = [
        {"category_mid": "ontology", "vector_db_id": "vdb_ontology_01"},
        {"category_mid": "policy", "vector_db_id": "vdb_policy_01"},
    ]
    cfg_file = tmp_path / "routing_config.json"
    cfg_file.write_text(json.dumps(cfg), encoding="utf-8")
    return cfg_file


@pytest.fixture
def client(db_session, tmp_path, monkeypatch, routing_config):
    from app.core import config as cfg_module

    monkeypatch.setattr(cfg_module.settings, "vector_store_dir", tmp_path / "vs")
    monkeypatch.setattr(cfg_module.settings, "raw_documents_dir", tmp_path / "raw")
    monkeypatch.setattr(cfg_module.settings, "processed_dir", tmp_path / "proc")
    monkeypatch.setattr(cfg_module.settings, "routing_config_path", routing_config)
    (tmp_path / "vs").mkdir()
    (tmp_path / "raw").mkdir()
    (tmp_path / "proc").mkdir()

    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
