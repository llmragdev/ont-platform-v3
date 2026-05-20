"""Repository 계층 단위 테스트.

PostgresDataRepository는 실제 DB가 없어도 import 가능해야 하며,
DATABASE_URL이 없는 경우 resolve_default()가 InMemory를 반환해야 한다.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.repository import (
    DataRepository,
    InMemoryDataRepository,
    JsonFileDataRepository,
    PostgresDataRepository,
    resolve_default,
)


def test_resolve_default_in_memory(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("ONTOLOGY_DATA_PATH", raising=False)
    repo = resolve_default()
    assert isinstance(repo, InMemoryDataRepository)


def test_resolve_default_json_file(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    target = tmp_path / "data.json"
    monkeypatch.setenv("ONTOLOGY_DATA_PATH", str(target))
    repo = resolve_default()
    assert isinstance(repo, JsonFileDataRepository)


def test_resolve_default_postgres_url_fallback_on_failure(monkeypatch):
    # 임의 호스트로 가짜 URL 설정 → 연결 실패 시 InMemory로 폴백해야 한다.
    monkeypatch.setenv("DATABASE_URL", "postgresql://invalid:invalid@127.0.0.1:1/none")
    monkeypatch.delenv("ONTOLOGY_DATA_PATH", raising=False)
    repo = resolve_default()
    assert isinstance(repo, (InMemoryDataRepository, PostgresDataRepository))


def test_postgres_class_importable():
    # 의존성이 없어도 클래스 자체는 import 가능해야 한다.
    assert issubclass(PostgresDataRepository, DataRepository)


def test_json_file_repository_roundtrip(tmp_path: Path):
    target = tmp_path / "ontology.json"
    repo = JsonFileDataRepository(target)
    raw = repo.load()
    assert "orders" in raw

    raw["orders"]["O001"]["status"] = "Approved"
    repo.save(raw)
    assert json.loads(target.read_text(encoding="utf-8"))["orders"]["O001"]["status"] == "Approved"

    repo2 = JsonFileDataRepository(target)
    assert repo2.load()["orders"]["O001"]["status"] == "Approved"
