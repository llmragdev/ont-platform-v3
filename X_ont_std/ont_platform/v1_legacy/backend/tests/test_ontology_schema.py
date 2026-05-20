"""Phase 1 — 스키마 외부화 테스트.

목표:
- 기본 스키마 로딩이 기존 동작과 동일한지
- 스키마 메타데이터(id_prefix/icon/sensitive/enum_values)가 잘 노출되는지
- 잘못된 스키마(미정의 type 등)는 INVALID_SCHEMA 오류
- ONTOLOGY_SCHEMA_PATH 환경변수로 스키마 교체 가능
- 새 객체 타입을 JSON에 추가만으로 등록되는지
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.data import fresh_raw_data
from app.errors import AppError
from app.ontology import OntologyService, load_ontology_schema


def test_default_schema_loaded():
    schema = load_ontology_schema()
    names = {t["name"] for t in schema["object_types"]}
    assert names == {"Customer", "Product", "Order"}


def test_service_loads_default_schema_with_metadata():
    svc = OntologyService(fresh_raw_data())
    customer_type = svc.registry.object_types["Customer"]
    assert customer_type.id_prefix == "C"
    assert customer_type.display_name == "고객"
    risk = customer_type.properties["risk_tier"]
    assert risk.sensitive is True
    assert risk.enum_values == ["Low", "Medium", "High"]


def test_relationship_metadata_loaded():
    svc = OntologyService(fresh_raw_data())
    placed = svc.registry.relationship_types["PLACED_ORDER"]
    assert placed.cardinality == "one_to_many"
    assert placed.reverse_display_name == "주문 고객"


def test_invalid_property_type_raises(tmp_path: Path):
    bad = {
        "object_types": [
            {"name": "Foo", "properties": [{"name": "x", "type": "UNKNOWN_TYPE"}]}
        ],
        "relationship_types": [],
    }
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(AppError) as ex:
        OntologyService(fresh_raw_data(), schema_path=p)
    assert ex.value.code == "INVALID_SCHEMA"


def test_relationship_undefined_type_raises(tmp_path: Path):
    bad = {
        "object_types": [{"name": "A", "properties": []}],
        "relationship_types": [
            {"name": "BAD", "source_type": "A", "target_type": "NonExistent"}
        ],
    }
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(AppError) as ex:
        OntologyService(fresh_raw_data(), schema_path=p)
    assert ex.value.code == "INVALID_SCHEMA"


def test_missing_schema_file_raises(tmp_path: Path):
    with pytest.raises(AppError) as ex:
        load_ontology_schema(tmp_path / "missing.json")
    assert ex.value.code == "INVALID_SCHEMA"


def test_custom_schema_via_env_variable(tmp_path: Path, monkeypatch):
    """ONTOLOGY_SCHEMA_PATH 환경변수로 다른 스키마 로딩 가능 (관리자가 코드 수정 없이 변경)."""
    custom = {
        "object_types": [
            {
                "name": "Customer",
                "display_name": "고객",
                "id_prefix": "C",
                "properties": [
                    {"name": "name", "type": "string", "required": True},
                    {"name": "segment", "type": "string", "required": True},
                    {"name": "region", "type": "string", "required": True},
                    {"name": "risk_tier", "type": "string", "required": True},
                ],
            },
            {
                "name": "Product",
                "id_prefix": "P",
                "properties": [
                    {"name": "name", "type": "string", "required": True},
                    {"name": "category", "type": "string", "required": True},
                    {"name": "unit_price", "type": "float", "required": True},
                ],
            },
            {
                "name": "Order",
                "id_prefix": "O",
                "properties": [
                    {"name": "customer_id", "type": "string", "required": True},
                    {"name": "order_date", "type": "string", "required": True},
                    {"name": "status", "type": "string", "required": True},
                    {"name": "amount", "type": "float", "required": True},
                    {"name": "product_ids", "type": "list", "required": True},
                ],
            },
            # 새 객체 타입을 추가! 코드는 그대로
            {
                "name": "Contract",
                "display_name": "계약",
                "id_prefix": "CT",
                "properties": [
                    {"name": "title", "type": "string", "required": True},
                ],
            },
        ],
        "relationship_types": [
            {"name": "PLACED_ORDER", "source_type": "Customer", "target_type": "Order"},
            {"name": "ORDER_CONTAINS_PRODUCT", "source_type": "Order", "target_type": "Product"},
        ],
    }
    p = tmp_path / "custom.json"
    p.write_text(json.dumps(custom), encoding="utf-8")
    monkeypatch.setenv("ONTOLOGY_SCHEMA_PATH", str(p))
    svc = OntologyService(fresh_raw_data())
    assert "Contract" in svc.registry.object_types
    assert svc.registry.object_types["Contract"].id_prefix == "CT"


def test_object_types_returns_list_with_names():
    svc = OntologyService(fresh_raw_data())
    types = svc.object_types()
    names = {t["name"] for t in types}
    assert "Customer" in names and "Order" in names and "Product" in names
