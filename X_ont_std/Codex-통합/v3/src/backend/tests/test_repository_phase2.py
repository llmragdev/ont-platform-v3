from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@pytest.fixture()
def isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    storage_root = tmp_path / "storage"
    monkeypatch.setenv("STORAGE_ROOT", str(storage_root))

    _write_json(
        storage_root / "acme" / "proj-001" / "ontology" / "ontology_objects.json",
        [
            {
                "id": "CU001",
                "type": "Customer",
                "values": {"name": "ACME Korea"},
                "company_id": "acme",
                "project_id": "proj-001",
                "status": "active",
            },
            {
                "id": "OR001",
                "type": "Order",
                "values": {"amount": 1200},
                "company_id": "acme",
                "project_id": "proj-001",
                "status": "active",
            },
        ],
    )
    _write_json(storage_root / "acme" / "proj-001" / "ontology" / "ontology_relationships.json", [])
    _write_json(
        storage_root / "globex" / "proj-002" / "ontology" / "ontology_objects.json",
        [
            {
                "id": "GL001",
                "type": "Customer",
                "values": {"name": "Globex Korea"},
                "company_id": "globex",
                "project_id": "proj-002",
                "status": "active",
            }
        ],
    )
    _write_json(storage_root / "globex" / "proj-002" / "ontology" / "ontology_relationships.json", [])
    return storage_root


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_object_list_is_tenant_project_scoped(isolated_storage: Path) -> None:
    acme = client.get("/api/v1/ontology/objects?user_id=alice")
    globex = client.get("/api/v1/ontology/objects?user_id=carol")

    assert acme.status_code == 200
    assert {item["id"] for item in acme.json()["objects"]} == {"CU001", "OR001"}
    assert globex.status_code == 200
    assert {item["id"] for item in globex.json()["objects"]} == {"GL001"}


def test_viewer_cannot_create_object(isolated_storage: Path) -> None:
    response = client.post(
        "/api/v1/ontology/objects?user_id=bob",
        json={
            "type": "Customer",
            "values": {"name": "Blocked", "segment": "SMB", "region": "KR", "risk_tier": "Low"},
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_create_object_ignores_client_supplied_tenant_scope(isolated_storage: Path) -> None:
    response = client.post(
        "/api/v1/ontology/objects?user_id=alice",
        json={
            "type": "Customer",
            "values": {"name": "New ACME", "segment": "SMB", "region": "KR", "risk_tier": "Low"},
            "company_id": "globex",
            "project_id": "proj-002",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "CU002"
    assert payload["company_id"] == "acme"
    assert payload["project_id"] == "proj-001"
    assert payload["created_by"] == "alice"


def test_cross_tenant_object_lookup_returns_not_found(isolated_storage: Path) -> None:
    response = client.get("/api/v1/ontology/objects/GL001?user_id=alice")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_relationship_crud_is_tenant_scoped(isolated_storage: Path) -> None:
    created = client.post(
        "/api/v1/ontology/relationships?user_id=alice",
        json={"type": "PLACED_ORDER", "source_id": "CU001", "target_id": "OR001"},
    )
    assert created.status_code == 200
    assert created.json()["id"] == "REL001"
    assert created.json()["company_id"] == "acme"

    blocked = client.delete("/api/v1/ontology/relationships/REL001?user_id=bob")
    assert blocked.status_code == 403

    disabled = client.delete("/api/v1/ontology/relationships/REL001?user_id=alice")
    assert disabled.status_code == 200
    assert disabled.json()["status"] == "disabled"

    visible = client.get("/api/v1/ontology/relationships?user_id=alice")
    assert visible.json()["relationships"] == []

    all_rows = client.get("/api/v1/ontology/relationships?user_id=alice&include_disabled=true")
    assert all_rows.status_code == 200
    assert all_rows.json()["relationships"][0]["status"] == "disabled"


def test_disable_object_removes_it_from_default_list(isolated_storage: Path) -> None:
    disabled = client.delete("/api/v1/ontology/objects/CU001?user_id=alice")
    assert disabled.status_code == 200
    assert disabled.json()["status"] == "disabled"

    visible = client.get("/api/v1/ontology/objects?user_id=alice")
    assert {item["id"] for item in visible.json()["objects"]} == {"OR001"}

    all_rows = client.get("/api/v1/ontology/objects?user_id=alice&include_disabled=true")
    assert {item["id"] for item in all_rows.json()["objects"]} == {"CU001", "OR001"}
