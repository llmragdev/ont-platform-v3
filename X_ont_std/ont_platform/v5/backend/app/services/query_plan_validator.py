"""QueryPlanValidator — schema-based plan validation (v3.0)."""
from __future__ import annotations

from pydantic import BaseModel

from app.models.query_intent import QueryPlanV3
from app.models.tenant_context import TenantContext
from app.services.ontology import OntologyService


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str] = []


class QueryPlanValidator:
    def __init__(self, ontology_svc: OntologyService) -> None:
        self._ontology = ontology_svc

    def validate(self, plan: QueryPlanV3, ctx: TenantContext) -> ValidationResult:
        errors: list[str] = []
        schema = self._ontology.get_schema(ctx)

        valid_types = {t["name"] for group in ("builtin_entity_types", "domain_entity_types")
                       for t in schema.get(group, []) if t.get("name")}
        props_by_type: dict[str, set[str]] = {}
        for group in ("builtin_entity_types", "domain_entity_types"):
            for t in schema.get(group, []):
                name = t.get("name")
                if name:
                    props_by_type[name] = set(t.get("properties") or [])

        for f in plan.ontology_filters:
            if f.entity_type and valid_types and f.entity_type not in valid_types:
                errors.append(f"Unknown entity_type: {f.entity_type}")
            if f.property and f.entity_type:
                allowed = props_by_type.get(f.entity_type, set())
                if allowed and f.property not in allowed:
                    errors.append(f"Unknown property '{f.property}' for {f.entity_type}")

        if plan.doc_ids:
            accessible = {d["doc_id"] for d in self._ontology.list_documents(ctx)}
            for doc_id in plan.doc_ids:
                if doc_id not in accessible:
                    errors.append(f"Inaccessible doc_id: {doc_id}")

        return ValidationResult(valid=len(errors) == 0, errors=errors)
