from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .errors import AppError
from .models import ObjectInstance, ObjectType, RelationshipDefinition, RelationshipInstance


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
        relationship_name: str | None = None,
        source_id: str | None = None,
        target_id: str | None = None,
    ) -> list[RelationshipInstance]:
        return [
            relationship
            for relationship in self.relationships
            if (relationship_name is None or relationship.relationship_type.name == relationship_name)
            and (source_id is None or relationship.source_id == source_id)
            and (target_id is None or relationship.target_id == target_id)
        ]


class OntologyService:
    def __init__(self, raw: dict, on_change: Callable[[dict], None] | None = None) -> None:
        self.raw = raw
        self.on_change = on_change
        self.registry = OntologyRegistry()
        self._build_registry()

    def _build_registry(self) -> None:
        customer_type = ObjectType("Customer")
        customer_type.add_property("name", str, required=True)
        customer_type.add_property("segment", str, required=True)
        customer_type.add_property("region", str, required=True)
        customer_type.add_property("risk_tier", str, required=True)
        customer_type.add_property("contract_terms", str)
        customer_type.add_property("owner", str)

        product_type = ObjectType("Product")
        product_type.add_property("name", str, required=True)
        product_type.add_property("category", str, required=True)
        product_type.add_property("unit_price", float, required=True)

        order_type = ObjectType("Order")
        order_type.add_property("customer_id", str, required=True)
        order_type.add_property("order_date", str, required=True)
        order_type.add_property("status", str, required=True)
        order_type.add_property("amount", float, required=True)
        order_type.add_property("product_ids", list, required=True)

        for object_type in [customer_type, product_type, order_type]:
            self.registry.register_object_type(object_type)

        self.registry.register_relationship_type(RelationshipDefinition("PLACED_ORDER", customer_type, order_type))
        self.registry.register_relationship_type(RelationshipDefinition("ORDER_CONTAINS_PRODUCT", order_type, product_type))

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

    def get_order_context(self, order_id: str, customer_id: str | None = None) -> dict:
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

    def update_order_status(self, order_id: str, status: str) -> None:
        order = self.get_object(order_id)
        order.values["status"] = status
        self.raw["orders"][order_id]["status"] = status
        if self.on_change is not None:
            self.on_change(self.raw)

    @staticmethod
    def to_dict(instance: ObjectInstance) -> dict:
        return {"id": instance.object_id, "type": instance.object_type.name, **instance.values}
