from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .errors import AppError
from .models import ObjectInstance, ObjectType, RelationshipDefinition, RelationshipInstance


# Phase 1 — 스키마 type 문자열 → Python type 매핑
SCHEMA_TYPE_MAP: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "enum": str,
    "date": str,
    "datetime": str,
    "number": (int, float),
    "int": int,
    "float": float,
    "boolean": bool,
    "bool": bool,
    "list": list,
    "dict": dict,
    "object_ref": str,
}


def _resolve_property_type(type_label: str) -> type | tuple[type, ...]:
    target = SCHEMA_TYPE_MAP.get(type_label)
    if target is None:
        raise AppError("INVALID_SCHEMA", f"Unknown property type: {type_label}", 500)
    return target


def _default_schema_path() -> Path:
    return Path(__file__).resolve().parent / "config" / "ontology.default.json"


def load_ontology_schema(path: Path | str | None = None) -> dict:
    """ontology.default.json 로드 + 최소 검증."""
    schema_path = Path(path) if path else Path(
        os.environ.get("ONTOLOGY_SCHEMA_PATH", _default_schema_path())
    )
    if not schema_path.exists():
        raise AppError("INVALID_SCHEMA", f"Schema file not found: {schema_path}", 500)
    raw = json.loads(schema_path.read_text(encoding="utf-8"))
    if "object_types" not in raw or "relationship_types" not in raw:
        raise AppError("INVALID_SCHEMA", "Schema must define object_types and relationship_types.", 500)
    return raw


class OntologyRegistry:
    def __init__(self) -> None:
        self.object_types: dict[str, ObjectType] = {}
        self.objects: dict[str, ObjectInstance] = {}
        self.relationship_types: dict[str, RelationshipDefinition] = {}
        self.relationships: list[RelationshipInstance] = []

    def register_object_type(self, object_type: ObjectType) -> None:
        self.object_types[object_type.name] = object_type

    def create_object(self, object_id: str, object_type_name: str, values: dict[str, Any]) -> ObjectInstance:
        object_type = self.object_types[object_type_name]
        instance = ObjectInstance(object_id, object_type, values)
        instance.validate()
        self.objects[object_id] = instance
        return instance

    def register_relationship_type(self, relationship_type: RelationshipDefinition) -> None:
        self.relationship_types[relationship_type.name] = relationship_type

    def link(
        self,
        relationship_name: str,
        source_id: str,
        target_id: str,
        values: dict[str, Any] | None = None,
    ) -> RelationshipInstance:
        relationship_type = self.relationship_types[relationship_name]
        source = self.objects[source_id]
        target = self.objects[target_id]
        if source.object_type.name != relationship_type.source_type.name:
            raise TypeError("Invalid source object type")
        if target.object_type.name != relationship_type.target_type.name:
            raise TypeError("Invalid target object type")
        relationship = RelationshipInstance(relationship_type, source_id, target_id, values or {})
        self.relationships.append(relationship)
        return relationship

    def find_related(self, source_id: str, relationship_name: str) -> list[ObjectInstance]:
        return [
            self.objects[relationship.target_id]
            for relationship in self.relationships
            if relationship.source_id == source_id and relationship.relationship_type.name == relationship_name
        ]

    def find_sources(self, target_id: str, relationship_name: str) -> list[ObjectInstance]:
        return [
            self.objects[relationship.source_id]
            for relationship in self.relationships
            if relationship.target_id == target_id and relationship.relationship_type.name == relationship_name
        ]

    def find_relationships(
        self,
        source_id: str | None = None,
        target_id: str | None = None,
        relationship_name: str | None = None,
    ) -> list[dict]:
        """방향·타입 모두 옵션인 범용 관계 탐색."""
        result = []
        for rel in self.relationships:
            if source_id is not None and rel.source_id != source_id:
                continue
            if target_id is not None and rel.target_id != target_id:
                continue
            if relationship_name is not None and rel.relationship_type.name != relationship_name:
                continue
            result.append({
                "relationship_type": rel.relationship_type.name,
                "display_name": rel.relationship_type.display_name,
                "reverse_display_name": rel.relationship_type.reverse_display_name,
                "source_id": rel.source_id,
                "target_id": rel.target_id,
                "values": rel.values,
            })
        return result


class OntologyService:
    def __init__(
        self,
        raw: dict,
        on_change: Callable[[dict], None] | None = None,
        schema_path: Path | str | None = None,
    ) -> None:
        self.raw = raw
        self.on_change = on_change
        self.registry = OntologyRegistry()
        # Phase 1 — 스키마 외부화: ontology.default.json 로드
        self.schema = load_ontology_schema(schema_path)
        self._build_registry()

    def _build_registry(self) -> None:
        # Phase 1 — 객체/관계 타입을 JSON 스키마에서 로딩
        type_by_name: dict[str, ObjectType] = {}
        for type_def in self.schema["object_types"]:
            obj_type = ObjectType(
                name=type_def["name"],
                display_name=type_def.get("display_name"),
                id_prefix=type_def.get("id_prefix"),
                icon=type_def.get("icon"),
            )
            for prop in type_def.get("properties", []):
                resolved = _resolve_property_type(prop["type"])
                obj_type.add_property(
                    prop["name"],
                    resolved,  # type: ignore[arg-type]
                    required=prop.get("required", False),
                    sensitive=prop.get("sensitive", False),
                    searchable=prop.get("searchable", False),
                    enum_values=prop.get("enum_values"),
                )
            self.registry.register_object_type(obj_type)
            type_by_name[obj_type.name] = obj_type

        for rel_def in self.schema["relationship_types"]:
            source = type_by_name.get(rel_def["source_type"])
            target = type_by_name.get(rel_def["target_type"])
            if source is None or target is None:
                raise AppError(
                    "INVALID_SCHEMA",
                    f"Relationship {rel_def['name']} references undefined object type",
                    500,
                )
            self.registry.register_relationship_type(
                RelationshipDefinition(
                    name=rel_def["name"],
                    source_type=source,
                    target_type=target,
                    display_name=rel_def.get("display_name"),
                    reverse_display_name=rel_def.get("reverse_display_name"),
                    cardinality=rel_def.get("cardinality", "many_to_many"),
                )
            )

        for customer_id, values in self.raw["customers"].items():
            self.registry.create_object(customer_id, "Customer", values)

        for product_id, values in self.raw["products"].items():
            self.registry.create_object(product_id, "Product", values)

        order_items_by_order: dict[str, list[dict]] = {}
        for item in self.raw["order_items"].values():
            order_items_by_order.setdefault(item["order_id"], []).append(item)

        for order_id, values in self.raw["orders"].items():
            items = order_items_by_order.get(order_id, [])
            amount = sum(self.raw["products"][item["product_id"]]["unit_price"] * item["quantity"] for item in items)
            product_ids = [item["product_id"] for item in items]
            order_values = {**values, "amount": float(amount), "product_ids": product_ids}
            self.registry.create_object(order_id, "Order", order_values)
            self.registry.link("PLACED_ORDER", values["customer_id"], order_id)
            for item in items:
                self.registry.link("ORDER_CONTAINS_PRODUCT", order_id, item["product_id"], {"quantity": item["quantity"]})

        # Phase 3 — 사용자가 추가한 커스텀 관계 인스턴스 복원
        for saved in self.raw.get("ontology_relationships", []):
            rel_type_name = saved.get("relationship_type")
            if rel_type_name not in self.registry.relationship_types:
                continue
            src = saved.get("source_id")
            tgt = saved.get("target_id")
            if src not in self.registry.objects or tgt not in self.registry.objects:
                continue
            inst = self.registry.link(rel_type_name, src, tgt, saved.get("values", {}))
            inst.rel_id = saved["rel_id"]

    def object_types(self) -> list[dict]:
        return [
            {
                "name": object_type.name,
                "properties": [
                    {"name": prop.name, "type": prop.type_name, "required": prop.required}
                    for prop in object_type.properties.values()
                ],
            }
            for object_type in self.registry.object_types.values()
        ]

    def customers(self) -> list[dict]:
        return [self.to_dict(obj) for obj in self.registry.objects.values() if obj.object_type.name == "Customer"]

    def orders(self) -> list[dict]:
        return [self.to_dict(obj) for obj in self.registry.objects.values() if obj.object_type.name == "Order"]

    def get_object(self, object_id: str) -> ObjectInstance:
        obj = self.registry.objects.get(object_id)
        if obj is None:
            raise AppError("OBJECT_NOT_FOUND", "요청한 객체를 찾을 수 없습니다.", 404)
        return obj

    def object_context(self, object_id: str) -> dict:
        """어떤 객체 타입이든 동작하는 범용 컨텍스트 조회.

        반환:
          object      - 대상 객체 dict
          outgoing    - 이 객체가 source인 관계 목록 (relationship_type, target_id, target 객체 포함)
          incoming    - 이 객체가 target인 관계 목록 (relationship_type, source_id, source 객체 포함)
        """
        obj = self.get_object(object_id)
        outgoing_rels = self.registry.find_relationships(source_id=object_id)
        incoming_rels = self.registry.find_relationships(target_id=object_id)

        outgoing = []
        for rel in outgoing_rels:
            target = self.registry.objects.get(rel["target_id"])
            entry = dict(rel)
            if target:
                entry["target"] = self.to_dict(target)
            outgoing.append(entry)

        incoming = []
        for rel in incoming_rels:
            source = self.registry.objects.get(rel["source_id"])
            entry = dict(rel)
            if source:
                entry["source"] = self.to_dict(source)
            incoming.append(entry)

        return {
            "object": self.to_dict(obj),
            "object_type": obj.object_type.name,
            "outgoing": outgoing,
            "incoming": incoming,
        }

    def get_order_context(self, order_id: str, customer_id: str | None = None) -> dict:
        """하위호환 유지 — 내부적으로 object_context 활용."""
        order = self.get_object(order_id)
        if order.object_type.name != "Order":
            raise AppError("OBJECT_NOT_FOUND", "요청한 객체를 찾을 수 없습니다.", 404)

        customers = self.registry.find_sources(order_id, "PLACED_ORDER")
        if not customers:
            raise AppError("RELATION_MISSING", "주문과 연결된 고객 관계를 찾을 수 없습니다.", 409)
        customer = customers[0]
        if customer_id and customer_id != customer.object_id:
            raise AppError("RELATION_MISMATCH", "고객과 주문의 연결 관계가 일치하지 않습니다.", 409)

        products = self.registry.find_related(order_id, "ORDER_CONTAINS_PRODUCT")
        return {
            "order": self.to_dict(order),
            "customer": self.to_dict(customer),
            "products": [self.to_dict(product) for product in products],
        }

    def get_full_graph(self) -> dict:
        """전체 객체+관계를 React Flow 형식으로 반환 (Phase 3 — /api/ontology/graph용)."""
        type_order = list(self.registry.object_types.keys())
        col_width = 250
        row_height = 100
        type_col: dict[str, int] = {t: i for i, t in enumerate(type_order)}
        type_row: dict[str, int] = {t: 0 for t in type_order}

        nodes = []
        for obj in self.registry.objects.values():
            t = obj.object_type.name
            col = type_col.get(t, 0)
            row = type_row.get(t, 0)
            nodes.append({
                "id": obj.object_id,
                "type": "ontology",
                "position": {"x": col * col_width, "y": row * row_height},
                "data": {
                    "label": obj.values.get("name", obj.object_id),
                    "object_type": t,
                    "icon": obj.object_type.icon,
                    **{k: v for k, v in obj.values.items()},
                },
            })
            type_row[t] = row + 1

        edges = []
        for rel in self.registry.relationships:
            edges.append({
                "id": rel.rel_id,
                "source": rel.source_id,
                "target": rel.target_id,
                "label": rel.relationship_type.display_name or rel.relationship_type.name,
                "data": {
                    "relationship_type": rel.relationship_type.name,
                    "values": rel.values,
                },
            })

        return {"nodes": nodes, "edges": edges}

    def add_relationship_instance(
        self,
        rel_type_name: str,
        source_id: str,
        target_id: str,
        values: dict | None = None,
    ) -> dict:
        """관계 인스턴스 추가 — 스키마 검증 후 영속화."""
        if rel_type_name not in self.registry.relationship_types:
            raise AppError("INVALID_SCHEMA", f"정의되지 않은 관계 타입: {rel_type_name}", 400)
        rel_def = self.registry.relationship_types[rel_type_name]
        if source_id not in self.registry.objects:
            raise AppError("OBJECT_NOT_FOUND", f"source 객체 없음: {source_id}", 404)
        if target_id not in self.registry.objects:
            raise AppError("OBJECT_NOT_FOUND", f"target 객체 없음: {target_id}", 404)
        src_type = self.registry.objects[source_id].object_type.name
        tgt_type = self.registry.objects[target_id].object_type.name
        if src_type != rel_def.source_type.name:
            raise AppError(
                "TYPE_MISMATCH",
                f"{rel_type_name}의 source는 {rel_def.source_type.name}이어야 합니다 (받은 값: {src_type}).",
                400,
            )
        if tgt_type != rel_def.target_type.name:
            raise AppError(
                "TYPE_MISMATCH",
                f"{rel_type_name}의 target은 {rel_def.target_type.name}이어야 합니다 (받은 값: {tgt_type}).",
                400,
            )
        inst = self.registry.link(rel_type_name, source_id, target_id, values or {})
        saved = {
            "rel_id": inst.rel_id,
            "relationship_type": rel_type_name,
            "source_id": source_id,
            "target_id": target_id,
            "values": values or {},
        }
        self.raw.setdefault("ontology_relationships", []).append(saved)
        if self.on_change is not None:
            self.on_change(self.raw)
        return saved

    def delete_relationship_instance(self, rel_id: str) -> None:
        """관계 인스턴스 삭제 (내장 관계 포함 모두 삭제 가능)."""
        before = len(self.registry.relationships)
        self.registry.relationships = [
            r for r in self.registry.relationships if r.rel_id != rel_id
        ]
        if len(self.registry.relationships) == before:
            raise AppError("OBJECT_NOT_FOUND", f"관계 인스턴스 없음: {rel_id}", 404)
        self.raw["ontology_relationships"] = [
            r for r in self.raw.get("ontology_relationships", []) if r.get("rel_id") != rel_id
        ]
        if self.on_change is not None:
            self.on_change(self.raw)

    def update_order_status(self, order_id: str, status: str) -> None:
        order = self.get_object(order_id)
        order.values["status"] = status
        self.raw["orders"][order_id]["status"] = status
        if self.on_change is not None:
            self.on_change(self.raw)

    @staticmethod
    def to_dict(instance: ObjectInstance) -> dict:
        return {"id": instance.object_id, "type": instance.object_type.name, **instance.values}
