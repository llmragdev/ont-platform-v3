from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .errors import AppError
from .models import OntologySchema


TYPE_MAP = {
    "string": str,
    "enum": str,
    "date": str,
    "datetime": str,
    "boolean": bool,
    "json": (dict, list),
    "list": list,
    "object_ref": str,
    "object_ref_list": list,
}

FILTER_OPERATORS = {"contains", "eq", "gt", "gte", "lt", "lte"}
CALCULATE_OPERATIONS = {"sum", "avg", "max", "min"}


class SchemaValidator:
    def __init__(self, schema: OntologySchema | None = None, config_dir: Path | None = None) -> None:
        if schema is not None:
            self.schema = schema
        else:
            base_dir = config_dir or Path(__file__).resolve().parents[1] / "config"
            schema_path = base_dir / "ontology.default.json"
            self.schema = OntologySchema.model_validate_json(schema_path.read_text(encoding="utf-8"))

    def validate_object_create(self, payload: dict[str, Any]) -> None:
        type_name = payload.get("type")
        if not isinstance(type_name, str) or not type_name:
            raise AppError("INVALID_OBJECT", "Object type is required.", 400)
        values = payload.get("values") or {}
        if not isinstance(values, dict):
            raise AppError("INVALID_OBJECT", "Object values must be a JSON object.", 400)
        self._validate_object_values(type_name, values, require_all=True)

    def validate_object_update(self, type_name: str, values: dict[str, Any]) -> None:
        if not isinstance(values, dict):
            raise AppError("INVALID_OBJECT", "Object values must be a JSON object.", 400)
        self._validate_object_values(type_name, values, require_all=True)

    def validate_relationship_create(
        self,
        payload: dict[str, Any],
        source_type: str,
        target_type: str,
    ) -> None:
        rel_type = self.relationship_type(payload.get("type"))
        if source_type != rel_type["source_type"] or target_type != rel_type["target_type"]:
            raise AppError("INVALID_RELATIONSHIP", "Relationship source or target type mismatch.", 400)
        properties = payload.get("properties") or {}
        if not isinstance(properties, dict):
            raise AppError("INVALID_RELATIONSHIP", "Relationship properties must be a JSON object.", 400)
        self._validate_properties(rel_type.get("properties", []), properties, "relationship", require_all=True)

    def validate_query_plan(self, plan: dict[str, Any]) -> None:
        plan_type = plan.get("type")
        if plan_type == "object_context":
            if not isinstance(plan.get("object_id"), str):
                raise AppError("INVALID_PLAN", "object_context plan requires object_id.", 400)
            return
        if plan_type == "compare":
            object_ids = plan.get("object_ids")
            if not isinstance(object_ids, list) or len(object_ids) < 2 or not all(isinstance(item, str) for item in object_ids):
                raise AppError("INVALID_PLAN", "compare plan requires at least two object_ids.", 400)
            return
        if plan_type not in {"filter", "calculate"}:
            raise AppError("INVALID_PLAN", f"Unsupported plan type: {plan_type}", 400)

        type_name = plan.get("entity_type")
        type_def = self.object_type(type_name)
        props = {prop["name"]: prop for prop in type_def["properties"]}
        filters = plan.get("filters") or []
        if not isinstance(filters, list):
            raise AppError("INVALID_PLAN", "Plan filters must be a list.", 400)
        for item in filters:
            self._validate_filter(item, props)

        if plan_type == "calculate":
            metric = plan.get("metric")
            metric_def = props.get(metric)
            if metric_def is None:
                raise AppError("INVALID_PLAN", f"Unknown metric for {type_name}: {metric}", 400)
            if metric_def.get("type") != "number":
                raise AppError("INVALID_PLAN", f"Metric must be numeric: {metric}", 400)
            if plan.get("operation") not in CALCULATE_OPERATIONS:
                raise AppError("INVALID_PLAN", f"Unsupported calculate operation: {plan.get('operation')}", 400)

    def object_type(self, type_name: Any) -> dict[str, Any]:
        if not isinstance(type_name, str):
            raise AppError("INVALID_OBJECT", "Object type must be a string.", 400)
        for item in self.schema.object_types:
            if item.name == type_name:
                return item.model_dump()
        raise AppError("INVALID_OBJECT", f"Unknown object type: {type_name}", 400)

    def relationship_type(self, type_name: Any) -> dict[str, Any]:
        if not isinstance(type_name, str):
            raise AppError("INVALID_RELATIONSHIP", "Relationship type must be a string.", 400)
        for item in self.schema.relationship_types:
            if item.name == type_name:
                return item.model_dump()
        raise AppError("INVALID_RELATIONSHIP", f"Unknown relationship type: {type_name}", 400)

    def _validate_object_values(self, type_name: str, values: dict[str, Any], require_all: bool) -> None:
        type_def = self.object_type(type_name)
        self._validate_properties(type_def["properties"], values, f"object {type_name}", require_all)

    def _validate_properties(
        self,
        properties: list[dict[str, Any]],
        values: dict[str, Any],
        label: str,
        require_all: bool,
    ) -> None:
        prop_defs = {prop["name"]: prop for prop in properties}
        unknown = sorted(set(values) - set(prop_defs))
        if unknown:
            raise AppError("INVALID_OBJECT", f"Unknown property for {label}: {unknown[0]}", 400)
        if require_all:
            missing = [prop["name"] for prop in properties if prop.get("required") and prop["name"] not in values]
            if missing:
                raise AppError("INVALID_OBJECT", f"Missing required property for {label}: {missing[0]}", 400)
        for name, value in values.items():
            self._validate_value(name, value, prop_defs[name])

    def _validate_value(self, name: str, value: Any, prop: dict[str, Any]) -> None:
        prop_type = prop["type"]
        if prop_type == "number":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise AppError("INVALID_OBJECT", f"{name} must be a number.", 400)
            return
        expected = TYPE_MAP.get(prop_type)
        if expected and not isinstance(value, expected):
            raise AppError("INVALID_OBJECT", f"{name} must be {prop_type}.", 400)
        if prop_type == "enum" and value not in prop.get("values", []):
            allowed = ", ".join(prop.get("values", []))
            raise AppError("INVALID_OBJECT", f"{name} must be one of: {allowed}", 400)
        if prop_type == "date" and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise AppError("INVALID_OBJECT", f"{name} must be YYYY-MM-DD.", 400)

    def _validate_filter(self, filter_def: Any, props: dict[str, dict[str, Any]]) -> None:
        if not isinstance(filter_def, dict):
            raise AppError("INVALID_PLAN", "Each filter must be a JSON object.", 400)
        prop_name = filter_def.get("property")
        prop = props.get(prop_name)
        if prop is None:
            raise AppError("INVALID_PLAN", f"Unknown filter property: {prop_name}", 400)
        op = filter_def.get("op", "contains")
        if op not in FILTER_OPERATORS:
            raise AppError("INVALID_PLAN", f"Unsupported filter operator: {op}", 400)
        if op in {"gt", "gte", "lt", "lte"} and prop.get("type") != "number":
            raise AppError("INVALID_PLAN", f"Operator {op} requires a numeric property: {prop_name}", 400)
