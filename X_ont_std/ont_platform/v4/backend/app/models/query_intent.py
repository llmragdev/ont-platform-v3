"""QueryIntent — v3.0 with OntologyFilter and QueryPlanV3 extensions."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    DESCRIPTIVE = "descriptive"
    FILTER = "filter"
    COMPARE = "compare"
    CALCULATE = "calculate"
    HYBRID = "hybrid"


class EngineType(str, Enum):
    ONTOLOGY = "ONTOLOGY"
    VECTOR = "VECTOR"
    SYSTEM = "SYSTEM"


class ActionType(str, Enum):
    FILTER = "FILTER"
    SEARCH = "SEARCH"
    COMPARE = "COMPARE"
    CALCULATE = "CALCULATE"


class QueryAction(BaseModel):
    engine: EngineType
    action: ActionType
    params: Dict[str, Any] = Field(default_factory=dict)
    description: str = ""


class QueryPlan(BaseModel):
    intent: IntentType
    reasoning: str
    steps: List[QueryAction] = Field(default_factory=list)
    fallback_to_vector: bool = True
    schema_context: Dict[str, Any] = Field(default_factory=dict)


# ── v3.0 extensions ──────────────────────────────────────────────────────────

class OntologyFilter(BaseModel):
    entity_type: str | None = None
    property: str | None = None
    operator: Literal["eq", "contains", "gt", "lt"] = "eq"
    value: str | None = None


class QueryPlanV3(QueryPlan):
    ontology_filters: List[OntologyFilter] = Field(default_factory=list)
    needs_vector: bool = True
    doc_ids: List[str] | None = None
    estimated_cost: Literal["low", "medium", "high"] = "low"
    validated: bool = False
    llm_classified: bool = False


class QueryResponse(BaseModel):
    answer: str
    intent: IntentType
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    trace: List[str] = Field(default_factory=list)
    ontology_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    quality_metrics: Dict[str, Any] = Field(default_factory=dict)
