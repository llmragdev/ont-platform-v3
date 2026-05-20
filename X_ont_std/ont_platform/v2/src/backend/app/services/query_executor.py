"""Deterministic execution engines for QueryPlan steps."""
from __future__ import annotations

from typing import Any

from app.models.query_intent import ActionType, EngineType, QueryAction
from app.models.tenant_context import TenantContext
from app.services.ontology import OntologyService


class OntologyQueryEngine:
    """Execute ONTOLOGY plan steps without using an LLM."""

    def __init__(self, ontology_svc: OntologyService) -> None:
        self.ontology_svc = ontology_svc

    def execute(
        self,
        step: QueryAction,
        ctx: TenantContext,
        question: str,
        doc_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        if step.engine != EngineType.ONTOLOGY:
            raise ValueError(f"Unsupported engine for OntologyQueryEngine: {step.engine}")
        if step.action == ActionType.FILTER:
            return self._filter(step, ctx, question, doc_ids)
        if step.action == ActionType.CALCULATE:
            filtered = self._filter(step, ctx, question, doc_ids)
            return {
                **filtered,
                "action": ActionType.CALCULATE.value,
                "result": filtered["count"],
                "trace": filtered["trace"] + ["ontology.calculate: returned count"],
            }
        return {
            "engine": EngineType.ONTOLOGY.value,
            "action": step.action.value,
            "items": [],
            "count": 0,
            "trace": [f"ontology.{step.action.value.lower()}: unsupported action"],
        }

    def _filter(
        self,
        step: QueryAction,
        ctx: TenantContext,
        question: str,
        doc_ids: list[str] | None,
    ) -> dict[str, Any]:
        params = step.params or {}
        entity_type = params.get("entity_type")
        property_key = params.get("property_key")
        property_value = params.get("property_value")

        if property_key and property_value:
            items = self.ontology_svc.filter_by_property(
                ctx, entity_type, property_key, property_value, doc_ids
            )
            trace = [
                "ontology.filter: property filter",
                f"ontology.filter: entity_type={entity_type or '*'} {property_key}={property_value}",
            ]
        else:
            items = self.ontology_svc.find_by_name(ctx, question, doc_ids)
            trace = ["ontology.filter: fallback name search"]

        return {
            "engine": EngineType.ONTOLOGY.value,
            "action": ActionType.FILTER.value,
            "items": items,
            "count": len(items),
            "params": {
                "entity_type": entity_type,
                "property_key": property_key,
                "property_value": property_value,
            },
            "trace": trace + [f"ontology.filter: matched {len(items)} item(s)"],
        }
