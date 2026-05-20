"""DAG 기반 워크플로우 그래프 (Phase 1).

기존 Order 상태 전이용 WorkflowService(workflow.py)와는 별개로,
자유로운 노드 그래프(LLM/HTTP/Condition)를 저장·조회하는 도메인 모델 + 서비스.

Phase 1 범위:
- CRUD (저장·목록·조회·삭제)
- 권한 정책: 역할별 (생성/실행 = AccountManager+, 삭제 = Admin)
- 저장소: Repository 추상화(InMemory/JsonFile/Postgres) 재활용
- 실행은 Phase 2로 분리 (지금은 클라이언트가 시뮬레이션)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .errors import AppError


NodeKind = Literal["llm", "http", "condition", "start", "end"]


class GraphNode(BaseModel):
    id: str
    type: NodeKind
    position: dict[str, float]
    data: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str | None = None


class WorkflowGraph(BaseModel):
    id: str
    name: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    created_at: str
    updated_at: str
    created_by: str

    def touch(self, actor_email: str) -> None:
        self.updated_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _now() -> str:
    # 마이크로초까지 — 같은 초 내 다중 저장 시 정렬 안정성 보장
    return datetime.utcnow().isoformat(timespec="microseconds") + "Z"


def _new_id() -> str:
    return f"wfg-{uuid.uuid4().hex[:12]}"


def _validate_graph_payload(payload: dict[str, Any]) -> None:
    """필수 필드 검증 (id/type/position이 모든 노드에 있어야 함)."""
    nodes = payload.get("nodes", [])
    if not isinstance(nodes, list):
        raise AppError("INVALID_GRAPH", "nodes는 배열이어야 합니다.", 400)
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise AppError("INVALID_GRAPH", f"노드 {index}는 객체여야 합니다.", 400)
        if not node.get("id"):
            raise AppError("INVALID_GRAPH", f"노드 {index}에 id가 없습니다.", 400)
        if not node.get("type"):
            raise AppError("INVALID_GRAPH", f"노드 {node.get('id')}에 type이 없습니다.", 400)
        position = node.get("position")
        if not isinstance(position, dict) or "x" not in position or "y" not in position:
            raise AppError("INVALID_GRAPH", f"노드 {node['id']}의 position이 잘못되었습니다.", 400)


class WorkflowGraphService:
    """워크플로우 그래프 CRUD + 권한 검증."""

    def __init__(self, raw: dict, repository, policy, audit) -> None:
        self.raw = raw
        self.repository = repository
        self.policy = policy
        self.audit = audit
        # raw에 graphs 컬렉션 초기화
        if "workflow_graphs" not in self.raw:
            self.raw["workflow_graphs"] = {}
            self.repository.save(self.raw)

    # --- 권한 ---

    def _check_permission(self, user: dict, action: str) -> None:
        if not self.policy.can_manage_workflow_graph(user, action):
            self.audit.record(
                "WORKFLOW_GRAPH_DENIED", user, "WorkflowGraph", "-", {"action": action}
            )
            raise AppError(
                "FORBIDDEN",
                f"워크플로우 그래프 {action} 권한이 없습니다.",
                403,
            )

    # --- 조회 ---

    def list_graphs(self, user: dict) -> list[dict]:
        self._check_permission(user, "read")
        graphs = list(self.raw["workflow_graphs"].values())
        graphs.sort(key=lambda g: g.get("updated_at", ""), reverse=True)
        return graphs

    def get_graph(self, user: dict, graph_id: str) -> dict:
        self._check_permission(user, "read")
        graph = self.raw["workflow_graphs"].get(graph_id)
        if graph is None:
            raise AppError("OBJECT_NOT_FOUND", "워크플로우 그래프를 찾을 수 없습니다.", 404)
        return graph

    # --- 변경 ---

    def save_graph(self, user: dict, payload: dict[str, Any]) -> dict:
        self._check_permission(user, "write")
        _validate_graph_payload(payload)

        graph_id = payload.get("id") or _new_id()
        existing = self.raw["workflow_graphs"].get(graph_id)
        now = _now()

        graph = {
            "id": graph_id,
            "name": payload.get("name", "Untitled Workflow"),
            "nodes": payload["nodes"],
            "edges": payload.get("edges", []),
            "created_at": existing["created_at"] if existing else now,
            "updated_at": now,
            "created_by": existing["created_by"] if existing else user["email"],
        }
        self.raw["workflow_graphs"][graph_id] = graph
        self.repository.save(self.raw)
        self.audit.record(
            "WORKFLOW_GRAPH_SAVED",
            user,
            "WorkflowGraph",
            graph_id,
            {"name": graph["name"], "node_count": len(graph["nodes"])},
        )
        return graph

    def delete_graph(self, user: dict, graph_id: str) -> None:
        self._check_permission(user, "delete")
        if graph_id not in self.raw["workflow_graphs"]:
            raise AppError("OBJECT_NOT_FOUND", "워크플로우 그래프를 찾을 수 없습니다.", 404)
        del self.raw["workflow_graphs"][graph_id]
        self.repository.save(self.raw)
        self.audit.record(
            "WORKFLOW_GRAPH_DELETED", user, "WorkflowGraph", graph_id, {}
        )

    # --- 실행 이력 조회 (Phase 2) ---

    def list_runs(self, user: dict, graph_id: str | None = None) -> list[dict]:
        self._check_permission(user, "read")
        runs = list(self.raw.get("workflow_runs", {}).values())
        if graph_id is not None:
            runs = [r for r in runs if r.get("graph_id") == graph_id]
        runs.sort(key=lambda r: r.get("started_at", ""), reverse=True)
        return runs

    def get_run(self, user: dict, run_id: str) -> dict:
        self._check_permission(user, "read")
        run = self.raw.get("workflow_runs", {}).get(run_id)
        if run is None:
            raise AppError("OBJECT_NOT_FOUND", "실행 이력을 찾을 수 없습니다.", 404)
        steps = self.raw.get("workflow_run_steps", {}).get(run_id, [])
        return {"run": run, "steps": steps}

    def assert_can_run(self, user: dict) -> None:
        self._check_permission(user, "run")
