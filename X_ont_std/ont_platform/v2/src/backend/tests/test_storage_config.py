"""Unit tests for storage_config.py — D01 coverage."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from storage_config import (
    STORAGE_ROOT,
    get_company_root,
    get_project_root,
    get_uploads_path,
    get_raw_root,
    get_ontology_path,
    get_vector_db_root,
    get_vector_db_path,
    list_shard_paths,
    ensure_project_dirs,
)


# ── 경로 계산 정확성 ──────────────────────────────────────────────────────────

def test_company_root():
    p = get_company_root("acme")
    assert p == STORAGE_ROOT / "acme"


def test_project_root():
    p = get_project_root("acme", "proj-001")
    assert p == STORAGE_ROOT / "acme" / "proj-001"


def test_uploads_path():
    p = get_uploads_path("acme", "proj-001")
    assert p == STORAGE_ROOT / "acme" / "proj-001" / "uploads"


def test_raw_root():
    p = get_raw_root("acme", "proj-001")
    assert p == STORAGE_ROOT / "acme" / "proj-001" / "raw"


def test_ontology_path():
    p = get_ontology_path("acme", "proj-001")
    assert p == STORAGE_ROOT / "acme" / "proj-001" / "ontology"


def test_vector_db_root():
    p = get_vector_db_root("acme", "proj-001")
    assert p == STORAGE_ROOT / "acme" / "proj-001" / "vector_db"


# ── V-ID 샤드 경로 ────────────────────────────────────────────────────────────

def test_vector_db_path_default():
    p = get_vector_db_path("acme", "proj-001")
    assert p.name == "Vdefault"


def test_vector_db_path_numeric():
    p = get_vector_db_path("acme", "proj-001", "5001")
    assert p.name == "V5001"


def test_vector_db_path_already_prefixed():
    """shard_id가 이미 'V'로 시작하면 중복 추가 안 함."""
    p = get_vector_db_path("acme", "proj-001", "V5002")
    assert p.name == "V5002"


def test_vector_db_path_is_under_vector_db_root():
    root = get_vector_db_root("acme", "proj-001")
    shard = get_vector_db_path("acme", "proj-001", "5001")
    assert shard.parent == root


# ── 물리 격리: company 간 경로 분리 (D01 / D05 근거) ─────────────────────────

def test_path_isolation_between_companies():
    path_a = get_vector_db_path("acme", "proj-001", "default")
    path_b = get_vector_db_path("globex", "proj-001", "default")
    assert path_a != path_b


def test_path_isolation_between_projects():
    path_1 = get_vector_db_path("acme", "proj-001", "default")
    path_2 = get_vector_db_path("acme", "proj-002", "default")
    assert path_1 != path_2


def test_all_sub_paths_under_storage_root():
    for fn in (get_uploads_path, get_raw_root, get_ontology_path, get_vector_db_root):
        p = fn("acme", "proj-001")
        assert str(p).startswith(str(STORAGE_ROOT))


# ── list_shard_paths ──────────────────────────────────────────────────────────

def test_list_shard_paths_nonexistent(tmp_path, monkeypatch):
    """존재하지 않는 경로는 빈 리스트."""
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)
    result = list_shard_paths("no-company", "no-project")
    assert result == []


def test_list_shard_paths_returns_v_dirs(tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)

    vdb_root = tmp_path / "acme" / "proj-001" / "vector_db"
    (vdb_root / "Vdefault").mkdir(parents=True)
    (vdb_root / "V5001").mkdir()
    (vdb_root / "not_a_shard").mkdir()  # V 접두사 없음 → 제외

    result = list_shard_paths("acme", "proj-001")
    names = [p.name for p in result]
    assert "Vdefault" in names
    assert "V5001" in names
    assert "not_a_shard" not in names


# ── ensure_project_dirs ───────────────────────────────────────────────────────

def test_ensure_project_dirs_creates_all(tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)

    ensure_project_dirs("acme", "proj-001")

    assert get_uploads_path("acme", "proj-001").exists()
    assert get_raw_root("acme", "proj-001").exists()
    assert get_ontology_path("acme", "proj-001").exists()
    assert get_vector_db_root("acme", "proj-001").exists()


def test_ensure_project_dirs_idempotent(tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)

    ensure_project_dirs("acme", "proj-001")
    ensure_project_dirs("acme", "proj-001")  # 재실행해도 에러 없음
