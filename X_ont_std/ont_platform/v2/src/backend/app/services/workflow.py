"""WorkflowService + WorkflowGraphService v2.0.

WorkflowService:
  - config/workflow.json 에서 전환 규칙 로드 (도메인 외부화)
  - TenantContext scope 기반 엔티티 상태 관리
  - OntologyService 경유로 엔티티 상태 조회/변경

WorkflowGraphService:
  - DAG 그래프 CRUD (per-tenant JSON 파일)
  - 역할 기반 권한 (read / write / run / delete)

v1.0 참조: claud_v1_legacy/backend/app/workflow.py
           claud_v1_legacy/backend/app/workflow_graph.py
"""
from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.models.tenant_context import TenantContext
from app.services.ontology import OntologyService
from storage_config import get_project_root

# ── 기본 config 경로 ──────────────────────────────────────────────────────────

_DEFAULT_WORKFLOW_CONFIG = Path(__file__).resolve().parents[1] / "config" / "workflow.json"


def _load_workflow_config(path: Path | str | None = None) -> dict:
    config_path = Path(path) if path else _DEFAULT_WORKFLOW_CONFIG
    if not config_path.exists():
        return {"object_type": "Order", "statuses": [], "actions": {}}
    return json.loads(config_path.read_text(encoding="utf-8"))


# ── WorkflowService ───────────────────────────────────────────────────────────

class WorkflowService:
    def __init__(
        self,
        ontology_svc: OntologyService,
        config_path: Path | str | None = None,
    ) -> None:
        self.ontology = ontology_svc
        self._config = _load_workflow_config(config_path)

    # --- 내부 헬퍼 ---

    def _actions_config(self) -> dict[str, dict]:
        return self._config.get("actions", {})

    def available_actions(self, role: str, current_status: str) -> list[str]:
        """현재 상태와 역할에서 실행 가능한 액션 목록."""
        result = []
        for action_name, cfg in self._actions_config().items():
            if current_status in cfg.get("from_statuses", []):
                if role in cfg.get("allowed_roles", []):
                    result.append(action_name)
        return result

    def _all_entities(self, ctx: TenantContext, doc_ids: list[str] | None = None) -> list[dict]:
        """테넌트 scope 내 모든 엔티티 수집 (doc_id 포함)."""
        docs = self.ontology.list_documents(ctx)
        entities: list[dict] = []
        for doc_info in docs:
            doc_id = doc_info["doc_id"]
            if doc_ids and doc_id not in doc_ids:
                continue
            for entity in self.ontology.list_entities(doc_id, ctx):
                entities.append({**entity, "__doc_id": doc_id})
        return entities

    # --- 공개 API ---

    def queue(
        self,
        ctx: TenantContext,
        entity_type: str | None = None,
        doc_ids: list[str] | None = None,
    ) -> list[dict]:
        """역할로 실행 가능한 액션이 존재하는 엔티티 목록."""
        role = ctx.role
        rows: list[dict] = []
        for entity in self._all_entities(ctx, doc_ids):
            if entity_type and entity.get("type") != entity_type:
                continue
            current_status = (entity.get("properties") or {}).get("status") or entity.get("status")
            if not current_status:
                continue
            actions = self.available_actions(role, current_status)
            if actions:
                rows.append({
                    "entity_id": entity["id"],
                    "entity_type": entity.get("type"),
                    "name": entity.get("name"),
                    "status": current_status,
                    "available_actions": actions,
                    "doc_id": entity["__doc_id"],
                })
        return rows

    def execute(
        self,
        ctx: TenantContext,
        doc_id: str,
        entity_id: str,
        action_name: str,
    ) -> dict:
        """액션 실행 — 엔티티 상태 전이."""
        action_cfg = self._actions_config().get(action_name)
        if action_cfg is None:
            raise ValueError(f"알 수 없는 액션: {action_name}")

        if ctx.role not in action_cfg.get("allowed_roles", []):
            raise PermissionError(f"역할 '{ctx.role}'은 '{action_name}' 권한이 없습니다.")

        entities = self.ontology.list_entities(doc_id, ctx)
        entity = next((e for e in entities if e["id"] == entity_id), None)
        if entity is None:
            raise KeyError(f"엔티티를 찾을 수 없습니다: {entity_id}")

        props = entity.get("properties") or {}
        current_status = props.get("status") or entity.get("status")

        if current_status not in action_cfg.get("from_statuses", []):
            raise ValueError(
                f"현재 상태 '{current_status}'에서 '{action_name}'을 실행할 수 없습니다. "
                f"(허용 상태: {action_cfg['from_statuses']})"
            )

        to_status = action_cfg["to_status"]
        # 상태 업데이트
        if "properties" in entity:
            entity["properties"]["status"] = to_status
        else:
            entity["status"] = to_status

        self.ontology.upsert_entity(doc_id, entity, ctx)

        return {
            "entity_id": entity_id,
            "action": action_name,
            "from_status": current_status,
            "to_status": to_status,
        }


# ── WorkflowGraphService ──────────────────────────────────────────────────────

_GRAPH_WRITE_ROLES = {"Admin", "FinanceManager", "AccountManager"}
_GRAPH_RUN_ROLES = {"Admin", "FinanceManager", "AccountManager"}
_GRAPH_DELETE_ROLES = {"Admin"}
_GRAPH_READ_ROLES = {"Admin", "FinanceManager", "AccountManager", "Analyst", "Viewer"}


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="microseconds") + "Z"


def _new_graph_id() -> str:
    return f"wfg-{uuid.uuid4().hex[:12]}"


def _validate_graph_nodes(nodes: list) -> None:
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise ValueError(f"노드 {i}는 객체여야 합니다.")
        if not node.get("id"):
            raise ValueError(f"노드 {i}에 id가 없습니다.")
        if not node.get("type"):
            raise ValueError(f"노드 {node.get('id')}에 type이 없습니다.")
        pos = node.get("position")
        if not isinstance(pos, dict) or "x" not in pos or "y" not in pos:
            raise ValueError(f"노드 {node['id']}의 position이 잘못되었습니다.")


class WorkflowGraphService:
    def __init__(self) -> None:
        pass

    def _graph_file(self, ctx: TenantContext) -> Path:
        return get_project_root(ctx.company_id, ctx.project_id) / "workflow_graphs.json"

    def _load(self, ctx: TenantContext) -> dict:
        path = self._graph_file(ctx)
        if not path.exists():
            return {"graphs": {}}
        return json.loads(path.read_text(encoding="utf-8"))

    def _save(self, ctx: TenantContext, data: dict) -> None:
        path = self._graph_file(ctx)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _check_role(self, ctx: TenantContext, action: str) -> None:
        allowed = {
            "read": _GRAPH_READ_ROLES,
            "write": _GRAPH_WRITE_ROLES,
            "run": _GRAPH_RUN_ROLES,
            "delete": _GRAPH_DELETE_ROLES,
        }.get(action, set())
        if ctx.role not in allowed:
            raise PermissionError(f"역할 '{ctx.role}'은 그래프 {action} 권한이 없습니다.")

    def list_graphs(self, ctx: TenantContext) -> list[dict]:
        self._check_role(ctx, "read")
        data = self._load(ctx)
        graphs = list(data["graphs"].values())
        graphs.sort(key=lambda g: g.get("updated_at", ""), reverse=True)
        return graphs

    def get_graph(self, ctx: TenantContext, graph_id: str) -> dict:
        self._check_role(ctx, "read")
        data = self._load(ctx)
        graph = data["graphs"].get(graph_id)
        if graph is None:
            raise KeyError(f"그래프를 찾을 수 없습니다: {graph_id}")
        return graph

    def save_graph(self, ctx: TenantContext, payload: dict[str, Any]) -> dict:
        self._check_role(ctx, "write")
        nodes = payload.get("nodes", [])
        if not isinstance(nodes, list):
            raise ValueError("nodes는 배열이어야 합니다.")
        _validate_graph_nodes(nodes)

        data = self._load(ctx)
        graph_id = payload.get("id") or _new_graph_id()
        existing = data["graphs"].get(graph_id)
        now = _now_iso()

        graph: dict[str, Any] = {
            "id": graph_id,
            "name": payload.get("name", "Untitled Workflow"),
            "nodes": nodes,
            "edges": payload.get("edges", []),
            "created_at": existing["created_at"] if existing else now,
            "updated_at": now,
            "created_by": existing["created_by"] if existing else ctx.user_id,
        }
        data["graphs"][graph_id] = graph
        self._save(ctx, data)
        return graph

    def delete_graph(self, ctx: TenantContext, graph_id: str) -> None:
        self._check_role(ctx, "delete")
        data = self._load(ctx)
        if graph_id not in data["graphs"]:
            raise KeyError(f"그래프를 찾을 수 없습니다: {graph_id}")
        del data["graphs"][graph_id]
        self._save(ctx, data)
