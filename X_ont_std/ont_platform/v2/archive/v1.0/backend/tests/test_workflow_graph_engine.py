"""WorkflowGraph 실행 엔진 (Phase 2) 테스트."""

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.workflow_graph_engine import _evaluate_condition, _topological_order


@pytest.fixture()
def client() -> TestClient:
    c = TestClient(app)
    c.post("/api/system/reset")
    return c


def _sample_payload() -> dict:
    return {
        "name": "engine-test",
        "nodes": [
            {"id": "n1", "type": "start", "position": {"x": 0, "y": 0}, "data": {"label": "Start"}},
            {"id": "n2", "type": "condition", "position": {"x": 200, "y": 0}, "data": {"label": "Branch", "expression": "true"}},
            {"id": "n3", "type": "end", "position": {"x": 400, "y": 0}, "data": {"label": "End"}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
        ],
    }


# --- 순수 함수 단위 테스트 ---

def test_topological_simple():
    nodes = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    edges = [{"source": "a", "target": "b"}, {"source": "b", "target": "c"}]
    order = _topological_order(nodes, edges)
    assert order == ["a", "b", "c"]


def test_topological_cycle_returns_none():
    nodes = [{"id": "a"}, {"id": "b"}]
    edges = [{"source": "a", "target": "b"}, {"source": "b", "target": "a"}]
    assert _topological_order(nodes, edges) is None


def test_condition_simple_true_false():
    assert _evaluate_condition("true", {}) is True
    assert _evaluate_condition("false", {}) is False
    assert _evaluate_condition("", {}) is True  # 비어 있으면 통과 기본


def test_condition_string_equality():
    ctx = {"risk_tier": "High"}
    assert _evaluate_condition('risk_tier == "High"', ctx) is True
    assert _evaluate_condition('risk_tier == "Low"', ctx) is False


def test_condition_numeric_comparison():
    ctx = {"amount": 8200}
    assert _evaluate_condition("amount > 5000", ctx) is True
    assert _evaluate_condition("amount < 5000", ctx) is False


def test_condition_unknown_format_defaults_false():
    assert _evaluate_condition("os.system('rm -rf /')", {}) is False  # 미니 파서가 거부


# --- API 통합 테스트 ---

def test_run_stream_completes(client: TestClient):
    saved = client.post("/api/workflow-graphs", json=_sample_payload()).json()
    response = client.post(f"/api/workflow-graphs/{saved['id']}/run")
    assert response.status_code == 200
    body = response.text
    # SSE 형식 — event/data 라인 포함
    assert "event: run_started" in body
    assert "event: node_started" in body
    assert "event: node_finished" in body
    assert "event: run_finished" in body
    # 모든 노드 완료
    finished_lines = [l for l in body.splitlines() if l.startswith("event: node_finished")]
    assert len(finished_lines) == 3


def test_run_then_history_lookup(client: TestClient):
    saved = client.post("/api/workflow-graphs", json=_sample_payload()).json()
    client.post(f"/api/workflow-graphs/{saved['id']}/run")
    # 그래프의 실행 이력
    history = client.get(f"/api/workflow-graphs/{saved['id']}/runs").json()
    assert len(history["runs"]) == 1
    run_id = history["runs"][0]["run_id"]
    # 상세 조회
    detail = client.get(f"/api/workflow-runs/{run_id}").json()
    assert detail["run"]["status"] == "completed"
    assert len(detail["steps"]) == 3
    assert detail["steps"][0]["type"] == "start"
    assert detail["steps"][-1]["type"] == "end"


def test_run_with_cycle_returns_failed_event(client: TestClient):
    cycle_payload = {
        "name": "cycle",
        "nodes": [
            {"id": "n1", "type": "start", "position": {"x": 0, "y": 0}},
            {"id": "n2", "type": "end", "position": {"x": 200, "y": 0}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n1"},
        ],
    }
    saved = client.post("/api/workflow-graphs", json=cycle_payload).json()
    response = client.post(f"/api/workflow-graphs/{saved['id']}/run")
    assert response.status_code == 200
    assert "event: run_failed" in response.text


def test_viewer_cannot_run_workflow(client: TestClient):
    saved = client.post("/api/workflow-graphs", json=_sample_payload()).json()
    response = client.post(
        f"/api/workflow-graphs/{saved['id']}/run", params={"user": "viewer"}
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_run_records_audit_events(client: TestClient):
    saved = client.post("/api/workflow-graphs", json=_sample_payload()).json()
    client.post(f"/api/workflow-graphs/{saved['id']}/run")
    events = client.get("/api/audit/events").json()["events"]
    types = [e["event_type"] for e in events]
    assert "GRAPH_RUN_STARTED" in types
    assert "GRAPH_RUN_FINISHED" in types
    assert "GRAPH_NODE_SUCCESS" in types
