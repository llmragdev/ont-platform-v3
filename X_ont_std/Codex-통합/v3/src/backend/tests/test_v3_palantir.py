import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_action_writeback_provenance_and_materialize(tmp_path: Path, monkeypatch):
    storage_root = tmp_path / "storage"
    monkeypatch.setenv("STORAGE_ROOT", str(storage_root))

    payload = {
        "type": "Order",
        "values": {
            "order_date": "2026-05-16",
            "amount": 5000,
            "status": "Submitted",
        },
        "provenance": {
            "source_kind": "llm_extracted",
            "confidence": 0.95,
            "doc_id": "doc-palantir-001",
        },
    }
    response = client.post("/api/v1/ontology/objects?user_id=alice&project_id=proj-001", json=payload)
    assert response.status_code == 200
    data = response.json()
    object_id = data["id"]
    assert data["provenance"]["doc_id"] == "doc-palantir-001"

    response = client.post(
        "/api/v1/ontology/actions/execute?user_id=alice&project_id=proj-001",
        json={
        "action_name": "APPROVE_ORDER",
        "target_id": object_id,
        "params": {"doc_id": "action-log-001"},
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert result["object"]["values"]["status"] == "Approved"

    storage_path = storage_root / "acme" / "proj-001" / "ontology" / "external_writeback"
    sync_file = storage_path / f"{object_id}_sync.json"
    assert sync_file.exists()
    sync_data = json.loads(sync_file.read_text(encoding="utf-8"))
    assert sync_data["data"]["status"] == "Approved"
    assert sync_data["last_action"] == "UPDATE"

    materialized = client.post(
        "/api/v1/ontology/materialize?user_id=alice&project_id=proj-001",
        json={"dataset_name": "생산_공정지연_v1", "object_type": "Order"},
    )
    assert materialized.status_code == 200
    assert materialized.json()["row_count"] == 1
