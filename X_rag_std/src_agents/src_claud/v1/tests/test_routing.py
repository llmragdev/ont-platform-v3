import json

import pytest

from app.services.embedding.hash_embedding import HashEmbeddingService
from app.services.router import VectorDbRouter


@pytest.fixture
def router(tmp_path, monkeypatch):
    from app.core import config as cfg

    routing = {
        "routing_rules": [
            {
                "vector_db_id": "vdb_tech_01",
                "target_category_mid": ["IT", "tech"],
                "engine_type": "local_json",
            },
            {
                "vector_db_id": "vdb_policy_01",
                "target_category_mid": ["규정", "지침"],
                "engine_type": "local_json",
            },
        ]
    }
    config_path = tmp_path / "routing.json"
    config_path.write_text(json.dumps(routing), encoding="utf-8")
    monkeypatch.setattr(cfg.settings, "routing_config_path", config_path)
    monkeypatch.setattr(cfg.settings, "vector_store_dir", tmp_path)
    return VectorDbRouter(HashEmbeddingService())


def test_vector_db_id_takes_priority_over_category(router):
    resolved = router.resolve_vector_db_id(
        category_mid="IT", vector_db_id="vdb_policy_01"
    )
    assert resolved == "vdb_policy_01"


def test_category_mid_fallback(router):
    resolved = router.resolve_vector_db_id(category_mid="IT")
    assert resolved == "vdb_tech_01"


def test_korean_category_routing(router):
    resolved = router.resolve_vector_db_id(category_mid="규정")
    assert resolved == "vdb_policy_01"


def test_unknown_category_returns_default(router):
    resolved = router.resolve_vector_db_id(category_mid="unknown_xyz")
    assert resolved == "vdb_default_01"


def test_no_args_returns_default(router):
    resolved = router.resolve_vector_db_id()
    assert resolved == "vdb_default_01"
