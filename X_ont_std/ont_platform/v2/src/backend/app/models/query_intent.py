"""QueryIntent — Definitions for query types and execution plans."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    DESCRIPTIVE = "descriptive"   # Vector search (RAG)
    FILTER = "filter"             # Structured property filter
    COMPARE = "compare"           # Comparison between entities
    CALCULATE = "calculate"       # Aggregation/Calculation
    HYBRID = "hybrid"             # Combination of above


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


class QueryResponse(BaseModel):
    answer: str
    intent: IntentType
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    trace: List[str] = Field(default_factory=list)
