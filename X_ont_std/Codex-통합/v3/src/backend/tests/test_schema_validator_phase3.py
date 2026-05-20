from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.errors import AppError
from app.main import app
from app.validators import SchemaValidator


client = TestClient(app)


def test_create_object_rejects_unknown_type() -> None:
    response = client.post(
        "/api/v1/ontology/objects?user_id=alice",
        json={"type": "Invoice", "values": {"name": "INV-1"}},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_OBJECT"


def test_create_object_rejects_missing_required_property() -> None:
    response = client.post(
        "/api/v1/ontology/objects?user_id=alice",
        json={"type": "Customer", "values": {"name": "Missing Fields"}},
    )

    assert response.status_code == 400
    assert "Missing required property" in response.json()["error"]["message"]


def test_create_object_rejects_enum_violation() -> None:
    response = client.post(
        "/api/v1/ontology/objects?user_id=alice",
        json={
            "type": "Customer",
            "values": {"name": "Bad Enum", "segment": "Public", "region": "KR", "risk_tier": "Low"},
        },
    )

    assert response.status_code == 400
    assert "segment must be one of" in response.json()["error"]["message"]


def test_create_object_rejects_unknown_property() -> None:
    response = client.post(
        "/api/v1/ontology/objects?user_id=alice",
        json={
            "type": "Customer",
            "values": {
                "name": "Unknown Prop",
                "segment": "SMB",
                "region": "KR",
                "risk_tier": "Low",
                "private_note": "not in schema",
            },
        },
    )

    assert response.status_code == 400
    assert "Unknown property" in response.json()["error"]["message"]


def test_relationship_rejects_source_target_type_mismatch() -> None:
    response = client.post(
        "/api/v1/ontology/relationships?user_id=alice",
        json={"type": "ORDER_CONTAINS_PRODUCT", "source_id": "CU001", "target_id": "OR001"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_RELATIONSHIP"


def test_plan_validator_rejects_unknown_filter_property() -> None:
    validator = SchemaValidator()

    with pytest.raises(AppError) as exc:
        validator.validate_query_plan(
            {
                "type": "filter",
                "entity_type": "Customer",
                "filters": [{"property": "does_not_exist", "op": "contains", "value": "x"}],
            }
        )

    assert exc.value.code == "INVALID_PLAN"


def test_plan_validator_rejects_non_numeric_metric() -> None:
    validator = SchemaValidator()

    with pytest.raises(AppError) as exc:
        validator.validate_query_plan(
            {
                "type": "calculate",
                "entity_type": "Customer",
                "filters": [],
                "metric": "name",
                "operation": "sum",
            }
        )

    assert exc.value.code == "INVALID_PLAN"
