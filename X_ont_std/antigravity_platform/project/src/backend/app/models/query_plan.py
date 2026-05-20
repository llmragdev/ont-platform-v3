from enum import Enum
from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field

class EngineType(str, Enum):
    ONTOLOGY = "ONTOLOGY"
    VECTOR = "VECTOR"
    SYSTEM = "SYSTEM"

class ActionType(str, Enum):
    FILTER = "FILTER"
    JOIN = "JOIN"
    AGGREGATE = "AGGREGATE"
    SEARCH = "SEARCH"
    CALCULATE = "CALCULATE"

class QueryAction(BaseModel):
    """실행 계획의 개별 액션 단위"""
    engine: EngineType
    action: ActionType
    params: Dict[str, Any] = Field(description="액션 수행에 필요한 세부 파라미터")
    description: str = Field(description="이 액션이 필요한 이유")

class QueryPlan(BaseModel):
    """최종 실행 계획 모델"""
    question: str
    intent: str
    steps: List[QueryAction]
    needs_hybrid_merge: bool = False
    fallback_reason: Optional[str] = None

class HybridResponse(BaseModel):
    """최종 답변 응답 모델"""
    question: str
    query_plan: QueryPlan
    answer: str
    structured_data: Optional[Dict[str, Any]] = None
    evidence: List[Dict[str, Any]] = []
    trace: List[str] = []
