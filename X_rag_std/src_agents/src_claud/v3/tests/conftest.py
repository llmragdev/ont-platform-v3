import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import app
from app.models.db_models import Base


@pytest.fixture
def test_db_engine():
    """함수 스코프 — 테스트마다 독립된 인메모리 DB 보장."""
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
    monkeypatch.setattr(cfg_module.settings, "pipeline_sync_mode", True)
    (tmp_path / "vs").mkdir()
    (tmp_path / "raw").mkdir()
    (tmp_path / "proc").mkdir()

    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app, headers={"X-Tenant-ID": "test_tenant"}) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def client_no_tenant(db_session, tmp_path, monkeypatch, routing_config):
    """X-Tenant-ID 헤더 없는 클라이언트 — 400 응답 검증용."""
    from app.core import config as cfg_module

    monkeypatch.setattr(cfg_module.settings, "vector_store_dir", tmp_path / "vs")
    monkeypatch.setattr(cfg_module.settings, "raw_documents_dir", tmp_path / "raw")
    monkeypatch.setattr(cfg_module.settings, "processed_dir", tmp_path / "proc")
    monkeypatch.setattr(cfg_module.settings, "routing_config_path", routing_config)
    monkeypatch.setattr(cfg_module.settings, "pipeline_sync_mode", True)
    (tmp_path / "vs").mkdir()
    (tmp_path / "raw").mkdir()
    (tmp_path / "proc").mkdir()

    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
