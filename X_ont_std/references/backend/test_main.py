import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_state():
    # Reset system state before each test to ensure isolation
    client.post("/api/system/reset")

def test_get_customers():
    response = client.get("/api/objects/customers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "name" in data[0]

def test_get_orders():
    response = client.get("/api/objects/orders")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "amount" in data[0]

def test_get_order_context_success():
    order_id = "O001"
    response = client.get(f"/api/objects/orders/{order_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["order"]["id"] == order_id
    assert "customer" in data
    assert "products" in data

def test_get_order_context_not_found():
    response = client.get("/api/objects/orders/O999")
    assert response.status_code == 404

def test_ask_question_approval_rag():
    # O001 is 3200 (under 5000) and C001 is Low risk
    response = client.post("/api/ask", json={
        "question": "O001 주문 승인해도 될까?",
        "selectedOrderId": "O001"
    })
    assert response.status_code == 200
    data = response.json()
    assert "승인이 권장됩니다" in data["answer"]
    assert "D001" in data["answer"]  # Check if policy was referenced
    assert len(data["evidence"]) > 0
    assert "O001" in data["detected_objects"]

def test_ask_question_relation_mismatch():
    # Query with C001 and O002 (O002 belongs to C002)
    response = client.post("/api/ask", json={
        "question": "C001 고객의 O002 주문 확인해줘",
        "selectedOrderId": "O002"
    })
    assert response.status_code == 200
    data = response.json()
    assert "관계를 온톨로지에서 확인할 수 없습니다" in data["answer"]

def test_workflow_execution_valid():
    order_id = "O001"
    # Execute Approve
    response = client.post("/api/workflow/execute", json={
        "orderId": order_id,
        "action": "ApproveOrder"
    })
    assert response.status_code == 200
    assert response.json()["newStatus"] == "Approved"

def test_workflow_invalid_transition():
    order_id = "O003" # Already Approved
    response = client.post("/api/workflow/execute", json={
        "orderId": order_id,
        "action": "ApproveOrder"
    })
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]

def test_audit_logs():
    # Trigger some events
    client.get("/api/objects/customers")
    client.post("/api/ask", json={"question": "test query"})
    
    response = client.get("/api/audit/events")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert data[-1]["event_type"] == "AI_QUERY"
