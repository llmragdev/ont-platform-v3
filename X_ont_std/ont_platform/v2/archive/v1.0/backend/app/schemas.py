from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)


class RagAskRequest(BaseModel):
    question: str = Field(..., min_length=1)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(3, ge=1, le=20)


class WorkflowRequest(BaseModel):
    action: str
    order_id: str
    payload: dict[str, Any] | None = None


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class GraphNodePayload(BaseModel):
    id: str
    type: str
    position: dict[str, float]
    data: dict[str, Any] | None = None


class GraphEdgePayload(BaseModel):
    id: str
    source: str
    target: str
    label: str | None = None


class RelationshipCreateRequest(BaseModel):
    """온톨로지 관계 인스턴스 생성 요청."""

    relationship_type: str = Field(..., description="관계 타입 이름 (예: PLACED_ORDER)")
    source_id: str = Field(..., description="source 객체 ID")
    target_id: str = Field(..., description="target 객체 ID")
    values: dict[str, Any] | None = Field(default=None, description="관계 속성 (선택)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "relationship_type": "PLACED_ORDER",
                    "source_id": "C001",
                    "target_id": "O002",
                }
            ]
        }
    }


# ── 온톨로지 관리 ──────────────────────────────────────────────────────────────

class OntologyExtractRequest(BaseModel):
    doc_id: str


class HybridAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    doc_ids: list[str] | None = None


class EntityTypeCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = ""
    properties: list[str] = []


class RelationTypeCreate(BaseModel):
    name: str = Field(..., min_length=1)
    from_type: str
    to_type: str


class EntityCreate(BaseModel):
    type: str
    name: str = Field(..., min_length=1)
    properties: dict[str, Any] = {}


class EntityUpdate(BaseModel):
    name: str | None = None
    properties: dict[str, Any] | None = None


class OntologyRelationshipCreate(BaseModel):
    from_id: str
    relation: str
    to_id: str


# ── 워크플로우 그래프 ──────────────────────────────────────────────────────────

class WorkflowGraphRequest(BaseModel):
    """워크플로우 그래프 저장 페이로드. /docs에서 이 example 그대로 실행 가능."""

    id: str | None = Field(default=None, description="없으면 자동 생성")
    name: str = Field(default="My First Workflow", description="화면에 표시되는 이름")
    nodes: list[GraphNodePayload]
    edges: list[GraphEdgePayload] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "예제 - LLM 단일 호출",
                    "nodes": [
                        {"id": "n1", "type": "start", "position": {"x": 0, "y": 0}, "data": {"label": "Start"}},
                        {"id": "n2", "type": "llm", "position": {"x": 200, "y": 0}, "data": {"label": "Ask Gemini", "prompt": "안녕, 너는 누구야?"}},
                        {"id": "n3", "type": "end", "position": {"x": 400, "y": 0}, "data": {"label": "End"}}
                    ],
                    "edges": [
                        {"id": "e1", "source": "n1", "target": "n2"},
                        {"id": "e2", "source": "n2", "target": "n3"}
                    ]
                },
                {
                    "name": "예제 - HTTP + Condition + LLM",
                    "nodes": [
                        {"id": "n1", "type": "http", "position": {"x": 0, "y": 0}, "data": {"label": "Fetch Order", "url": "http://localhost:8000/api/objects/orders", "method": "GET"}},
                        {"id": "n2", "type": "condition", "position": {"x": 220, "y": 0}, "data": {"label": "고위험?", "expression": "risk_tier == 'High'"}},
                        {"id": "n3", "type": "llm", "position": {"x": 440, "y": -80}, "data": {"label": "리뷰 코멘트", "prompt": "이 주문 추가 검토 사유를 요약해줘"}},
                        {"id": "n4", "type": "end", "position": {"x": 440, "y": 80}, "data": {"label": "Auto Approve"}}
                    ],
                    "edges": [
                        {"id": "e1", "source": "n1", "target": "n2"},
                        {"id": "e2", "source": "n2", "target": "n3", "label": "true"},
                        {"id": "e3", "source": "n2", "target": "n4", "label": "false"}
                    ]
                }
            ]
        }
    }
