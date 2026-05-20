"""WorkflowGraph CRUD + 권한 정책 테스트 (Phase 1)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    c = TestClient(app)
    c.post("/api/system/reset")
    return c


def _sample_payload(name: str = "test-flow") -> dict:
    return {
        "name": name,
        "nodes": [
            {"id": "n1", "type": "start", "position": {"x": 0, "y": 0}, "data": {"label": "Start"}},
            {"id": "n2", "type": "llm", "position": {"x": 200, "y": 0}, "data": {"label": "Ask", "prompt": "hi"}},
            {"id": "n3", "type": "end", "position": {"x": 400, "y": 0}, "data": {"label": "End"}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
        ],
    }


def test_save_and_get_graph_as_analyst(client: TestClient) -> None:
    response = client.post("/api/workflow-graphs", json=_sample_payload())
    assert response.status_code == 200, response.text
    saved = response.json()
    assert saved["id"].startswith("wfg-")
    assert saved["name"] == "test-flow"
    assert len(saved["nodes"]) == 3

    fetched = client.get(f"/api/workflow-graphs/{saved['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == saved["id"]


def test_save_then_update_keeps_id_and_created_at(client: TestClient) -> None:
    first = client.post("/api/workflow-graphs", json=_sample_payload("v1")).json()
    payload = _sample_payload("v2")
    payload["id"] = first["id"]
    second = client.post("/api/workflow-graphs", json=payload).json()
    assert second["id"] == first["id"]
    assert second["name"] == "v2"
    assert second["created_at"] == first["created_at"]
    assert second["updated_at"] >= first["updated_at"]


def test_list_graphs_recent_first(client: TestClient) -> None:
    a = client.post("/api/workflow-graphs", json=_sample_payload("a")).json()
    b = client.post("/api/workflow-graphs", json=_sample_payload("b")).json()
    listed = client.get("/api/workflow-graphs").json()["graphs"]
    ids = [g["id"] for g in listed]
    # b 가 더 최근에 갱신됐어야 함
    assert ids.index(b["id"]) <= ids.index(a["id"])


def test_viewer_can_read_but_not_write(client: TestClient) -> None:
    # 먼저 analyst로 저장
    saved = client.post("/api/workflow-graphs", json=_sample_payload()).json()
    # viewer로 조회는 가능
    response = client.get(f"/api/workflow-graphs/{saved['id']}", params={"user": "viewer"})
    assert response.status_code == 200
    # viewer로 저장은 거부
    response = client.post(
        "/api/workflow-graphs", params={"user": "viewer"}, json=_sample_payload("denied")
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_analyst_cannot_delete_admin_only(client: TestClient) -> None:
    saved = client.post("/api/workflow-graphs", json=_sample_payload()).json()
    # analyst 삭제 시도 → 403
    response = client.delete(f"/api/workflow-graphs/{saved['id']}", params={"user": "analyst"})
    assert response.status_code == 403
    # admin 삭제 → 200
    response = client.delete(f"/api/workflow-graphs/{saved['id']}", params={"user": "admin"})
    assert response.status_code == 200
    # 다음 조회는 404
    response = client.get(f"/api/workflow-graphs/{saved['id']}")
    assert response.status_code == 404


def test_invalid_payload_missing_position(client: TestClient) -> None:
    bad = {
        "name": "bad",
        "nodes": [{"id": "n1", "type": "start"}],  # position 없음
        "edges": [],
    }
    response = client.post("/api/workflow-graphs", json=bad)
    # Pydantic 검증으로 422
    assert response.status_code == 422


def test_get_unknown_returns_404(client: TestClient) -> None:
    response = client.get("/api/workflow-graphs/wfg-does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "OBJECT_NOT_FOUND"
