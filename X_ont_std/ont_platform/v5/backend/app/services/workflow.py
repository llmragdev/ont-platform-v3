"""WorkflowService + WorkflowGraphService v3.0 — with WorkflowRun history."""
from __future__ import annotations

import json
import sys
import uuid
import copy
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.models.tenant_context import TenantContext
from app.models.workflow_run import StepStatus, WorkflowRun, WorkflowStepRun
from app.services.ontology import OntologyService
from storage_config import get_project_root, get_workflow_runs_path

_DEFAULT_WORKFLOW_CONFIG = Path(__file__).resolve().parents[1] / "config" / "workflow.json"


def _load_workflow_config(path: Path | str | None = None) -> dict:
    config_path = Path(path) if path else _DEFAULT_WORKFLOW_CONFIG
    if not config_path.exists():
        return {"domains": {}}
    return json.loads(config_path.read_text(encoding="utf-8"))


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="microseconds") + "Z"


class WorkflowService:
    def __init__(self, ontology_svc: OntologyService, config_path: Path | str | None = None) -> None:
        self.ontology = ontology_svc
        self._config = _load_workflow_config(config_path)

    def _get_domain_config(self, domain_id: str) -> dict:
        """도메인별 설정 반환"""
        return self._config.get("domains", {}).get(domain_id, {})

    def _actions_config(self, domain_id: str = "ai-voucher-2025") -> dict[str, dict]:
        """도메인의 액션 설정 반환"""
        domain = self._get_domain_config(domain_id)
        return domain.get("actions", {})

    def _check_preconditions(self, entity: dict, preconditions: list) -> tuple[bool, str]:
        """전제 조건 검증"""
        if not preconditions:
            return True, ""

        for cond in preconditions:
            field = cond.get("field", "")
            operator = cond.get("operator", "")
            value = cond.get("value")
            message = cond.get("message", f"조건 '{field}'을 만족하지 않습니다")

            # 필드 값 추출 (e.g., "properties.budget" → entity["properties"]["budget"])
            field_parts = field.split(".")
            field_value = entity
            for part in field_parts:
                if isinstance(field_value, dict):
                    field_value = field_value.get(part)
                else:
                    field_value = None
                    break

            # 조건 검증
            result = self._evaluate_condition(field_value, operator, value)
            if not result:
                return False, message

        return True, ""

    def _evaluate_condition(self, field_value, operator: str, expected_value) -> bool:
        """조건 평가"""
        if operator == "not_null":
            return field_value is not None
        elif operator == "equals":
            return field_value == expected_value
        elif operator == "gte":
            return field_value is not None and field_value >= expected_value
        elif operator == "lte":
            return field_value is not None and field_value <= expected_value
        elif operator == "gt":
            return field_value is not None and field_value > expected_value
        elif operator == "lt":
            return field_value is not None and field_value < expected_value
        elif operator == "exists":
            return field_value is not None
        return False

    def _check_conditional_permission(self, role: str, entity: dict,
                                      conditional_perms: list) -> bool:
        """조건부 권한 검증"""
        if not conditional_perms:
            return False

        for perm in conditional_perms:
            condition = perm.get("condition", {})
            allowed_roles = perm.get("allowed_roles", [])

            # 조건 검증
            if self._evaluate_condition_dict(entity, condition):
                if role in allowed_roles:
                    return True

        return False

    def _evaluate_condition_dict(self, entity: dict, condition: dict) -> bool:
        """복합 조건 평가"""
        field = condition.get("field", "")
        operator = condition.get("operator", "")
        value = condition.get("value")

        # 필드 값 추출
        field_parts = field.split(".")
        field_value = entity
        for part in field_parts:
            if isinstance(field_value, dict):
                field_value = field_value.get(part)
            else:
                field_value = None
                break

        # 기본 조건 평가
        result = self._evaluate_condition(field_value, operator, value)

        # AND 조건 (있으면)
        if "and" in condition and result:
            and_cond = condition["and"]
            result = result and self._evaluate_condition_dict(entity, and_cond)

        return result

    def available_actions(self, role: str, current_status: str, entity: dict | None = None,
                         domain_id: str = "ai-voucher-2025") -> list[str]:
        """사용 가능한 액션 목록 반환 (조건부 권한 포함)"""
        actions = []
        for action_name, cfg in self._actions_config(domain_id).items():
            if current_status not in cfg.get("from_statuses", []):
                continue

            # 기본 권한 확인
            if "allowed_roles" in cfg and role in cfg["allowed_roles"]:
                actions.append(action_name)
            # 조건부 권한 확인
            elif "conditional_permissions" in cfg and entity:
                if self._check_conditional_permission(role, entity, cfg["conditional_permissions"]):
                    actions.append(action_name)

        return actions

    def _all_entities(self, ctx: TenantContext, doc_ids: list[str] | None = None) -> list[dict]:
        docs = self.ontology.list_documents(ctx)
        entities: list[dict] = []
        for doc_info in docs:
            doc_id = doc_info["doc_id"]
            if doc_ids and doc_id not in doc_ids:
                continue
            for entity in self.ontology.list_entities(doc_id, ctx):
                entities.append({**entity, "__doc_id": doc_id})
        return entities

    def queue(self, ctx: TenantContext, entity_type: str | None = None, doc_ids: list[str] | None = None,
              domain_id: str = "ai-voucher-2025") -> list[dict]:
        """대기 중인 엔티티 + 가능한 액션 반환"""
        rows: list[dict] = []
        for entity in self._all_entities(ctx, doc_ids):
            if entity_type and entity.get("type") != entity_type:
                continue
            current_status = (entity.get("properties") or {}).get("status") or entity.get("status")
            if not current_status:
                continue
            actions = self.available_actions(ctx.role, current_status, entity, domain_id)
            if actions:
                rows.append({
                    "entity_id": entity["id"], "entity_type": entity.get("type"),
                    "name": entity.get("name"), "status": current_status,
                    "available_actions": actions, "doc_id": entity["__doc_id"],
                })
        return rows

    def execute(self, ctx: TenantContext, doc_id: str, entity_id: str, action_name: str,
                domain_id: str = "ai-voucher-2025", params: dict | None = None) -> dict:
        """액션 실행 — 권한, 전제 조건, 상태 전이 검증"""
        action_cfg = self._actions_config(domain_id).get(action_name)
        if action_cfg is None:
            raise ValueError(f"알 수 없는 액션: {action_name}")

        entities = self.ontology.list_entities(doc_id, ctx)
        entity = next((e for e in entities if e["id"] == entity_id), None)
        if entity is None:
            raise KeyError(f"엔티티를 찾을 수 없습니다: {entity_id}")

        props = entity.get("properties") or {}
        current_status = props.get("status") or entity.get("status")
        if current_status not in action_cfg.get("from_statuses", []):
            raise ValueError(f"현재 상태 '{current_status}'에서 '{action_name}'을 실행할 수 없습니다.")

        # 1. 전제 조건 검증
        preconditions = action_cfg.get("preconditions", [])
        precond_ok, precond_msg = self._check_preconditions(entity, preconditions)
        if not precond_ok:
            raise ValueError(precond_msg)

        # 2. 권한 검증 (조건부 포함)
        has_permission = False

        # 기본 권한 확인
        if "allowed_roles" in action_cfg:
            has_permission = ctx.role in action_cfg["allowed_roles"]

        # 조건부 권한 확인
        if not has_permission and "conditional_permissions" in action_cfg:
            has_permission = self._check_conditional_permission(ctx.role, entity,
                                                               action_cfg["conditional_permissions"])

        if not has_permission:
            raise PermissionError(f"역할 '{ctx.role}'은 '{action_name}' 권한이 없습니다.")

        # 3. 필수 필드 검증
        required_fields = action_cfg.get("required_fields", [])
        if params:
            for field in required_fields:
                if field not in params:
                    raise ValueError(f"필수 필드 '{field}'가 없습니다.")
        elif required_fields:
            raise ValueError(f"필수 필드가 필요합니다: {', '.join(required_fields)}")

        # 4. 속성 변경 적용
        if "properties" not in entity:
            entity["properties"] = {}

        # 상태 변경 (to_status가 null이면 상태 유지)
        to_status = action_cfg.get("to_status")
        if to_status:
            entity["properties"]["status"] = to_status
        else:
            to_status = current_status

        # 추가 속성 변경
        property_changes = action_cfg.get("property_changes", [])
        for change in property_changes:
            field = change.get("field", "")
            value = change.get("value", "")

            # 템플릿 변수 치환
            if isinstance(value, str):
                if "{{ user_id }}" in value:
                    value = value.replace("{{ user_id }}", ctx.user_id)
                if "{{ timestamp }}" in value:
                    value = value.replace("{{ timestamp }}", _now_iso())
                # 파라미터에서 변수 치환 (e.g., {{ new_deadline }})
                if params:
                    for param_key, param_value in params.items():
                        template_var = f"{{{{ {param_key} }}}}"
                        if template_var in value:
                            value = value.replace(template_var, str(param_value))

            # 필드 설정
            field_parts = field.split(".")
            target = entity
            for part in field_parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            target[field_parts[-1]] = value

        # 5. 엔티티 저장
        self.ontology.upsert_entity(doc_id, entity, ctx)

        return {
            "entity_id": entity_id,
            "action": action_name,
            "from_status": current_status,
            "to_status": to_status,
            "approved_by": ctx.user_id,
            "approved_at": _now_iso()
        }


# ── WorkflowGraphService ──────────────────────────────────────────────────────

_GRAPH_WRITE_ROLES = {"Admin", "FinanceManager", "AccountManager"}
_GRAPH_RUN_ROLES = {"Admin", "FinanceManager", "AccountManager"}
_GRAPH_DELETE_ROLES = {"Admin", "FinanceManager", "AccountManager"}
_GRAPH_READ_ROLES = {"Admin", "FinanceManager", "AccountManager", "Analyst", "Viewer"}


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
        allowed = {"read": _GRAPH_READ_ROLES, "write": _GRAPH_WRITE_ROLES,
                   "run": _GRAPH_RUN_ROLES, "delete": _GRAPH_DELETE_ROLES}.get(action, set())
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
            "id": graph_id, "name": payload.get("name", "Untitled Workflow"),
            "nodes": nodes, "edges": payload.get("edges", []),
            "created_at": existing["created_at"] if existing else now,
            "updated_at": now,
            "created_by": existing["created_by"] if existing else ctx.user_id,
        }
        for key in (
            "scenario_id", "scenario_version", "template_id", "template_version",
            "graph_kind", "execution_mode", "runtime", "tenant_scope", "source",
        ):
            if key in payload:
                graph[key] = payload[key]
            elif existing and key in existing:
                graph[key] = existing[key]
        graph.setdefault("tenant_scope", {"company_id": ctx.company_id, "project_id": ctx.project_id})
        data["graphs"][graph_id] = graph
        self._save(ctx, data)
        return graph

    def clone_graph(self, ctx: TenantContext, graph_id: str, name: str | None = None) -> dict:
        self._check_role(ctx, "write")
        source = self.get_graph(ctx, graph_id)
        now = _now_iso()
        cloned = copy.deepcopy(source)
        cloned["id"] = _new_graph_id()
        cloned["name"] = name or f"{source.get('name', 'Workflow')} Copy"
        cloned["created_at"] = now
        cloned["updated_at"] = now
        cloned["created_by"] = ctx.user_id
        cloned["graph_kind"] = "template_copy" if source.get("graph_kind") == "system_template" else source.get("graph_kind", "custom")
        cloned["tenant_scope"] = {"company_id": ctx.company_id, "project_id": ctx.project_id}
        cloned["source"] = {
            "type": "project_graph",
            "source_graph_id": source.get("id"),
            "cloned_from": source.get("id"),
            "template_id": source.get("template_id"),
        }
        data = self._load(ctx)
        data["graphs"][cloned["id"]] = cloned
        self._save(ctx, data)
        return cloned

    def delete_graph(self, ctx: TenantContext, graph_id: str) -> None:
        self._check_role(ctx, "delete")
        data = self._load(ctx)
        if graph_id not in data["graphs"]:
            raise KeyError(f"그래프를 찾을 수 없습니다: {graph_id}")
        del data["graphs"][graph_id]
        self._save(ctx, data)

    # ── v3.0 Run history ─────────────────────────────────────────────────────

    def save_run(self, ctx: TenantContext, run: WorkflowRun) -> WorkflowRun:
        runs_dir = get_workflow_runs_path(ctx.company_id, ctx.project_id)
        runs_dir.mkdir(parents=True, exist_ok=True)
        path = runs_dir / f"{run.run_id}.json"
        path.write_text(run.model_dump_json(indent=2), encoding="utf-8")
        return run

    def list_runs(self, ctx: TenantContext, graph_id: str) -> list[dict]:
        self._check_role(ctx, "read")
        runs_dir = get_workflow_runs_path(ctx.company_id, ctx.project_id)
        if not runs_dir.exists():
            return []
        runs = []
        for f in sorted(runs_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("graph_id") == graph_id:
                    runs.append(data)
            except Exception:
                pass
        return runs

    def get_run(self, ctx: TenantContext, graph_id: str, run_id: str) -> dict:
        self._check_role(ctx, "read")
        runs_dir = get_workflow_runs_path(ctx.company_id, ctx.project_id)
        path = runs_dir / f"{run_id}.json"
        if not path.exists():
            raise KeyError(f"Run not found: {run_id}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("graph_id") != graph_id:
            raise KeyError(f"Run {run_id} does not belong to graph {graph_id}")
        return data
