from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["overview"]["object_type_count"] == 3


def test_schema_loaded_from_json() -> None:
    response = client.get("/api/ontology/schema")
    assert response.status_code == 200
    names = {item["name"] for item in response.json()["object_types"]}
    assert {"Customer", "Order", "Product"} <= names


def test_relationship_types_loaded_from_json() -> None:
    response = client.get("/api/ontology/relationship-types")
    names = {item["name"] for item in response.json()["relationship_types"]}
    assert "PLACED_ORDER" in names
    assert "ORDER_CONTAINS_PRODUCT" in names


def test_object_context_has_incoming_and_outgoing() -> None:
    response = client.get("/api/ontology/objects/O001/context")
    assert response.status_code == 200
    payload = response.json()
    assert payload["object"]["id"] == "O001"
    assert payload["incoming"][0]["source"]["id"] == "C001"
    assert payload["outgoing"][0]["target"]["type"] == "Product"


def test_add_relationship_validates_source_target() -> None:
    response = client.post(
        "/api/ontology/relationships",
        json={"type": "PLACED_ORDER", "source_id": "C001", "target_id": "O003", "properties": {}},
    )
    assert response.status_code == 200
    assert response.json()["type"] == "PLACED_ORDER"


def test_add_relationship_rejects_type_mismatch() -> None:
    response = client.post(
        "/api/ontology/relationships",
        json={"type": "PLACED_ORDER", "source_id": "O001", "target_id": "C001", "properties": {}},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_RELATIONSHIP"


def test_ask_uses_generic_object_context() -> None:
    response = client.post("/api/ask", json={"question": "O001 관계와 근거를 알려줘"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["detected_object_id"] == "O001"
    assert "load_object_context" in payload["trace"]


def test_hybrid_ask_filters_ontology_and_returns_rag_evidence() -> None:
    response = client.post("/api/hybrid/ask", json={"question": "5000 이상 주문 목록과 승인 근거를 알려줘"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["query_type"] == "filter"
    assert "O002" in payload["ontology_nodes"]
    assert payload["structured_data"]["headers"][:2] == ["id", "type"]
    assert payload["vector_evidence"]


def test_hybrid_ask_compares_multiple_objects() -> None:
    response = client.post("/api/hybrid/ask", json={"question": "C001 C002 고객 비교"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["query_type"] == "compare"
    assert payload["ontology_nodes"] == ["C001", "C002"]


def test_hybrid_ask_calculates_order_amount_sum() -> None:
    response = client.post("/api/hybrid/ask", json={"question": "주문 금액 합계 계산"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["query_type"] == "calculate"
    assert payload["structured_data"]["rows"][0][3] == "15840.0"
