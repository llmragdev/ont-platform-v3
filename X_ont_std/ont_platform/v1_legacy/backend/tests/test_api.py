from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["llm_provider"] in {"gemini", "rule-based"}


def test_me_default_user(client: TestClient) -> None:
    response = client.get("/api/me")
    assert response.status_code == 200
    assert response.json()["role"] == "AccountManager"


def test_me_finance_user(client: TestClient) -> None:
    response = client.get("/api/me", params={"user": "finance"})
    assert response.status_code == 200
    assert response.json()["role"] == "FinanceManager"


def test_customers_masked_for_viewer(client: TestClient) -> None:
    response = client.get("/api/objects/customers", params={"user": "viewer"})
    assert response.status_code == 200
    customers = response.json()["customers"]
    if customers:
        for customer in customers:
            assert customer["risk_tier"] == "Restricted"


def test_order_context_seoul_for_analyst(client: TestClient) -> None:
    response = client.get("/api/objects/orders/O001/context")
    assert response.status_code == 200
    payload = response.json()
    assert payload["order"]["id"] == "O001"
    assert payload["customer"]["id"] == "C001"


def test_order_context_forbidden_for_viewer_busan(client: TestClient) -> None:
    response = client.get("/api/objects/orders/O002/context", params={"user": "viewer"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_relation_mismatch(client: TestClient) -> None:
    response = client.get(
        "/api/objects/orders/O002/context",
        params={"customer_id": "C001"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "RELATION_MISMATCH"


def test_ask_returns_evidence_and_trace(client: TestClient) -> None:
    response = client.post("/api/ask", json={"question": "O001 주문 승인해도 될까?"})
    assert response.status_code == 200
    body = response.json()
    assert body["detected_objects"] == ["O001"]
    assert body["evidence"]
    assert any("Policy" in step["name"] for step in body["steps"])
    assert body["llm_provider"] in {"gemini", "rule-based"}


def test_workflow_approve_low_risk_under_5000(client: TestClient) -> None:
    response = client.post(
        "/api/workflow/execute",
        json={"action": "ApproveOrder", "order_id": "O001"},
    )
    assert response.status_code == 200
    assert response.json()["result"]["to_status"] == "Approved"


def test_workflow_high_risk_rejected_by_policy(client: TestClient) -> None:
    response = client.post(
        "/api/workflow/execute",
        params={"user": "analyst"},
        json={"action": "ApproveOrder", "order_id": "O003"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


def test_audit_events_recorded(client: TestClient) -> None:
    client.get("/api/objects/orders")
    response = client.get("/api/audit/events")
    assert response.status_code == 200
    events = response.json()["events"]
    assert any(event["event_type"] == "ACCESS_DENIED" or event["event_type"] == "OBJECT_CONTEXT_READ" or event["event_type"] for event in events)
