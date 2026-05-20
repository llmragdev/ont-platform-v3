"""WG-3 도메인 노드 + 노드 타입별 권한 테스트."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    c = TestClient(app)
    c.post("/api/system/reset")
    return c


def _graph_with(nodes: list[dict]) -> dict:
    edges = []
    for i in range(len(nodes) - 1):
        edges.append({"id": f"e{i}", "source": nodes[i]["id"], "target": nodes[i + 1]["id"]})
    return {"name": "wg3-test", "nodes": nodes, "edges": edges}


def test_approve_order_node_low_risk(client: TestClient):
    payload = _graph_with(
        [
            {"id": "n1", "type": "approve_order", "position": {"x": 0, "y": 0},
             "data": {"label": "Check O001", "order_id": "O001"}},
        ]
    )
    saved = client.post("/api/workflow-graphs", json=payload).json()
    response = client.post(f"/api/workflow-graphs/{saved['id']}/run")
    assert response.status_code == 200
    body = response.text
    assert "event: node_finished" in body
    assert '"status": "success"' in body
    # O001 = Alpha Manufacturing, Low risk, 3200, Seoul → analyst가 ApproveOrder 가능
    assert '"can_approve": true' in body.lower() or '"can_approve": true' in body


def test_approve_order_node_high_risk_blocks(client: TestClient):
    payload = _graph_with(
        [
            {"id": "n1", "type": "approve_order", "position": {"x": 0, "y": 0},
             "data": {"label": "Check O003", "order_id": "O003"}},
        ]
    )
    saved = client.post("/api/workflow-graphs", json=payload).json()
    response = client.post(f"/api/workflow-graphs/{saved['id']}/run")
    # O003 = Gamma Logistics, High risk → analyst의 can_approve = false
    assert response.status_code == 200
    body = response.text
    assert '"can_approve": false' in body or '"can_approve":false' in body


def test_risk_assess_node_masking_for_viewer(client: TestClient):
    payload = _graph_with(
        [
            {"id": "n1", "type": "risk_assess", "position": {"x": 0, "y": 0},
             "data": {"label": "C001", "customer_id": "C001"}},
        ]
    )
    saved = client.post("/api/workflow-graphs", json=payload, params={"user": "admin"}).json()
    # admin이 만든 그래프를 finance 가 실행 → risk_tier 그대로 노출
    response = client.post(f"/api/workflow-graphs/{saved['id']}/run", params={"user": "finance"})
    body = response.text
    assert '"risk_tier": "Low"' in body


def test_node_permission_blocks_viewer_for_http(client: TestClient):
    # http 노드는 Viewer 권한 거부
    payload = _graph_with(
        [
            {"id": "n1", "type": "http", "position": {"x": 0, "y": 0},
             "data": {"label": "fetch", "url": "http://localhost:8000/api/health"}},
        ]
    )
    # admin이 저장
    saved = client.post("/api/workflow-graphs", json=payload, params={"user": "admin"}).json()
    # viewer 가 실행 시도 → 그래프 run 권한 자체에서 FORBIDDEN (403)
    response = client.post(f"/api/workflow-graphs/{saved['id']}/run", params={"user": "viewer"})
    assert response.status_code == 403


def test_unknown_order_in_approve_node_returns_error_event(client: TestClient):
    payload = _graph_with(
        [
            {"id": "n1", "type": "approve_order", "position": {"x": 0, "y": 0},
             "data": {"label": "Unknown", "order_id": "O999"}},
        ]
    )
    saved = client.post("/api/workflow-graphs", json=payload).json()
    response = client.post(f"/api/workflow-graphs/{saved['id']}/run")
    body = response.text
    assert "OBJECT_NOT_FOUND" in body
    # run 자체는 200으로 끝나야 함 — SSE 안에 error 이벤트가 들어감
    assert response.status_code == 200
