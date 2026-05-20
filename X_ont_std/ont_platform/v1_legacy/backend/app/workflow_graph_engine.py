"""WorkflowGraph 서버 측 실행 엔진 (Phase 2).

설계 원칙:
1. 위상정렬(Kahn's algorithm)로 노드 실행 순서 결정. 사이클이면 거부.
2. AsyncGenerator로 단계별 이벤트를 yield → FastAPI SSE로 그대로 전송.
3. 노드 타입별 실행:
   - start / end : 즉시 성공
   - llm         : LLMGateway 재활용 (RAG가 아닌 단순 프롬프트)
   - http        : httpx로 외부 호출, 응답 처음 500자만 저장
   - condition   : 안전한 미니 파서 (eval 금지) — 변수가 없으면 'true' / 'false' 키워드만 받음
4. 모든 단계 결과를 raw["workflow_runs"], raw["workflow_run_steps"]에 영속.
5. 권한: 시작 전 PolicyEngine으로 'run' 권한 검증.
6. 감사: GRAPH_RUN_STARTED / GRAPH_NODE_* / GRAPH_RUN_FINISHED 기록.
"""

from __future__ import annotations

import asyncio
import json
import re
import uuid
from datetime import datetime
from time import perf_counter
from typing import Any, AsyncIterator

from .errors import AppError


# 기본 노드 타입별 실행 권한 — action_types 스키마가 있으면 동적으로 보강됨
_NODE_TYPE_POLICY_DEFAULT: dict[str, set[str]] = {
    "start": {"Viewer", "Analyst", "AccountManager", "FinanceManager", "Admin"},
    "end": {"Viewer", "Analyst", "AccountManager", "FinanceManager", "Admin"},
    "condition": {"Analyst", "AccountManager", "FinanceManager", "Admin"},
    "http": {"AccountManager", "FinanceManager", "Admin"},
    "llm": {"Analyst", "AccountManager", "FinanceManager", "Admin"},
    # WG-3 도메인 노드 기본값 — 스키마에 action_types가 없을 때 폴백
    "approve_order": {"AccountManager", "FinanceManager", "Admin"},
    "risk_assess": {"Analyst", "AccountManager", "FinanceManager", "Admin"},
}


def _build_node_policy_from_schema(schema: dict | None) -> dict[str, set[str]]:
    """action_types[exposed_as_graph_node=true]를 NODE_TYPE_POLICY에 병합."""
    policy = dict(_NODE_TYPE_POLICY_DEFAULT)
    if schema is None:
        return policy
    for action in schema.get("action_types", []):
        if not action.get("exposed_as_graph_node"):
            continue
        key = action.get("node_type_key") or action["name"].lower()
        roles = action.get("required_role")
        if roles:
            policy[key] = set(roles)
    return policy


# 모듈 레벨 기본값 (테스트·임포트 호환)
NODE_TYPE_POLICY = _NODE_TYPE_POLICY_DEFAULT


_BOOL_TRUE = {"true", "yes", "1"}
_BOOL_FALSE = {"false", "no", "0", ""}

# 안전한 condition 표현식: `lhs op rhs` 한 줄. lhs/rhs는 인용된 문자열·숫자·식별자.
_CONDITION_RE = re.compile(
    r'^\s*(?P<lhs>"[^"]*"|\'[^\']*\'|[\w\.]+)\s*(?P<op>==|!=|>=|<=|>|<)\s*(?P<rhs>"[^"]*"|\'[^\']*\'|[\w\.\-]+)\s*$'
)


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="microseconds") + "Z"


def _new_run_id() -> str:
    return f"run-{uuid.uuid4().hex[:12]}"


def _eval_condition_token(token: str, ctx: dict) -> Any:
    """식별자 또는 인용 문자열/숫자를 안전하게 평가."""
    if (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
        return token[1:-1]
    try:
        if "." in token:
            return float(token)
        return int(token)
    except ValueError:
        pass
    # ctx에서 값 찾기 (예: prev.output, vars.x 등)
    if token in ctx:
        return ctx[token]
    # 알 수 없는 식별자는 None 으로 취급
    return None


def _evaluate_condition(expression: str | None, ctx: dict) -> bool:
    if not expression or not expression.strip():
        return True
    lowered = expression.strip().lower()
    if lowered in _BOOL_TRUE:
        return True
    if lowered in _BOOL_FALSE:
        return False
    match = _CONDITION_RE.match(expression)
    if not match:
        # 알 수 없는 형태면 안전 기본값 False
        return False
    lhs = _eval_condition_token(match.group("lhs"), ctx)
    rhs = _eval_condition_token(match.group("rhs"), ctx)
    op = match.group("op")
    try:
        if op == "==":
            return lhs == rhs
        if op == "!=":
            return lhs != rhs
        if op == ">":
            return float(lhs) > float(rhs)
        if op == "<":
            return float(lhs) < float(rhs)
        if op == ">=":
            return float(lhs) >= float(rhs)
        if op == "<=":
            return float(lhs) <= float(rhs)
    except (TypeError, ValueError):
        return False
    return False


def _topological_order(nodes: list[dict], edges: list[dict]) -> list[str] | None:
    in_degree: dict[str, int] = {node["id"]: 0 for node in nodes}
    adj: dict[str, list[str]] = {node["id"]: [] for node in nodes}
    for edge in edges:
        if edge["target"] in in_degree:
            in_degree[edge["target"]] = in_degree.get(edge["target"], 0) + 1
        if edge["source"] in adj:
            adj[edge["source"]].append(edge["target"])
    queue = [node_id for node_id, deg in in_degree.items() if deg == 0]
    order: list[str] = []
    while queue:
        current = queue.pop(0)
        order.append(current)
        for neighbor in adj.get(current, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    return order if len(order) == len(nodes) else None


class WorkflowGraphEngine:
    """노드 실행 핸들러 + AsyncGenerator 기반 이벤트 스트림."""

    def __init__(self, llm, audit, ontology=None, policy=None) -> None:
        self.llm = llm
        self.audit = audit
        self.ontology = ontology
        self.policy = policy
        schema = ontology.schema if ontology is not None else None
        self._node_type_policy = _build_node_policy_from_schema(schema)

    def _check_node_permission(self, user: dict, node_type: str) -> None:
        allowed = self._node_type_policy.get(node_type)
        if allowed is None:
            return
        if user.get("role") not in allowed:
            raise AppError(
                "FORBIDDEN",
                f"역할 '{user.get('role')}'은 노드 타입 '{node_type}' 실행 권한이 없습니다.",
                403,
            )

    async def run(
        self,
        user: dict,
        graph: dict,
        raw: dict,
        on_persist,
    ) -> AsyncIterator[dict]:
        """워크플로우 한 번 실행. 이벤트를 yield 하면서 raw에 영속화한다.

        on_persist: 변경된 raw를 저장하는 콜백 (Repository.save).
        """
        run_id = _new_run_id()
        graph_id = graph["id"]
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        order = _topological_order(nodes, edges)
        if order is None:
            yield {"event": "run_failed", "data": {"run_id": run_id, "error": "cycle_detected"}}
            return

        node_index = {node["id"]: node for node in order_to_nodes(order, nodes)}

        # run 레코드 초기화
        run_record = {
            "run_id": run_id,
            "graph_id": graph_id,
            "status": "running",
            "started_at": _now(),
            "finished_at": None,
            "triggered_by": user["email"],
            "step_count": len(nodes),
            "completed_count": 0,
        }
        raw.setdefault("workflow_runs", {})[run_id] = run_record
        raw.setdefault("workflow_run_steps", {})[run_id] = []
        on_persist(raw)

        self.audit.record(
            "GRAPH_RUN_STARTED",
            user,
            "WorkflowGraph",
            graph_id,
            {"run_id": run_id, "node_count": len(nodes)},
        )

        yield {"event": "run_started", "data": {"run_id": run_id, "graph_id": graph_id, "order": order}}

        outputs: dict[str, Any] = {}
        ctx: dict[str, Any] = {}
        run_failed = False
        completed = 0

        for step_index, node_id in enumerate(order):
            node = node_index[node_id]
            node_data = node.get("data") or {}
            label = node_data.get("label") or node_id
            kind = node["type"]
            step_started = _now()
            t0 = perf_counter()
            yield {
                "event": "node_started",
                "data": {
                    "run_id": run_id,
                    "node_id": node_id,
                    "step_index": step_index,
                    "type": kind,
                    "label": label,
                    "started_at": step_started,
                },
            }
            try:
                self._check_node_permission(user, kind)
                output = await self._execute_node(kind, node_data, ctx, user)
                status = "success"
                error = None
            except AppError as exc:
                output = None
                status = "error"
                error = f"{exc.code}: {exc.message}"
            except Exception as exc:  # noqa: BLE001
                output = None
                status = "error"
                error = f"{exc.__class__.__name__}: {exc}"
            duration_ms = round((perf_counter() - t0) * 1000)
            outputs[node_id] = output
            ctx[node_id] = output
            ctx["last_output"] = output

            step_record = {
                "run_id": run_id,
                "node_id": node_id,
                "step_index": step_index,
                "type": kind,
                "label": label,
                "status": status,
                "started_at": step_started,
                "finished_at": _now(),
                "duration_ms": duration_ms,
                "output": (output[:1000] if isinstance(output, str) else output) if not isinstance(output, (list, dict)) or len(json.dumps(output, default=str)) < 4000 else json.dumps(output, default=str)[:1000],
                "error": error,
            }
            raw["workflow_run_steps"][run_id].append(step_record)
            self.audit.record(
                f"GRAPH_NODE_{status.upper()}",
                user,
                "WorkflowGraph",
                graph_id,
                {"run_id": run_id, "node_id": node_id, "duration_ms": duration_ms, "error": error},
            )

            yield {
                "event": "node_finished",
                "data": step_record,
            }
            completed += 1
            run_record["completed_count"] = completed
            if status == "error":
                run_failed = True
                break
            # 짧은 양보로 SSE flush 유도
            await asyncio.sleep(0)

        run_record["status"] = "failed" if run_failed else "completed"
        run_record["finished_at"] = _now()
        on_persist(raw)

        self.audit.record(
            "GRAPH_RUN_FINISHED",
            user,
            "WorkflowGraph",
            graph_id,
            {"run_id": run_id, "status": run_record["status"], "completed": completed},
        )

        yield {
            "event": "run_finished",
            "data": {
                "run_id": run_id,
                "status": run_record["status"],
                "completed_count": completed,
            },
        }

    async def _execute_node(self, kind: str, data: dict, ctx: dict, user: dict) -> Any:
        if kind in ("start", "end"):
            return f"{kind} ok"
        if kind == "llm":
            prompt = (data.get("prompt") or "").strip()
            if not prompt:
                raise AppError("INVALID_NODE", "LLM 노드에 prompt가 비어 있습니다.", 400)
            # LLMGateway가 RAG용 generate를 가지고 있으므로 직접 SDK 호출
            return await asyncio.to_thread(self._call_llm, prompt)
        if kind == "http":
            url = (data.get("url") or "").strip()
            method = (data.get("method") or "GET").upper()
            if not url:
                raise AppError("INVALID_NODE", "HTTP 노드에 url이 비어 있습니다.", 400)
            return await self._call_http(method, url)
        if kind == "condition":
            expression = data.get("expression")
            result = _evaluate_condition(expression, ctx)
            return {"expression": expression, "result": result}
        # WG-3 도메인 노드 — Ontology + PolicyEngine과 결합
        if kind == "approve_order":
            return self._execute_approve_order(data, user)
        if kind == "risk_assess":
            return self._execute_risk_assess(data, user)
        return f"unknown_kind:{kind}"

    def _execute_approve_order(self, data: dict, user: dict) -> dict:
        """도메인 노드 — 특정 주문에 대한 정책 미리보기 (실제 상태 전이 없음).

        활용: 그래프 안에서 "이 주문 승인 가능한가?"를 정책 엔진으로 검증.
        """
        if self.ontology is None or self.policy is None:
            raise AppError("MODEL_ERROR", "OntologyService/PolicyEngine이 주입되지 않았습니다.", 500)
        order_id = (data.get("order_id") or "").strip()
        if not order_id:
            raise AppError("INVALID_NODE", "approve_order 노드에 order_id가 비어 있습니다.", 400)
        context = self.ontology.get_order_context(order_id)
        self.policy.assert_can_read_object(user, context["order"])
        actions = self.policy.available_actions(user, context["order"], context["customer"])
        return {
            "order_id": order_id,
            "customer_id": context["customer"]["id"],
            "risk_tier": context["customer"]["risk_tier"],
            "amount": context["order"]["amount"],
            "available_actions": actions,
            "can_approve": "ApproveOrder" in actions,
        }

    def _execute_risk_assess(self, data: dict, user: dict) -> dict:
        """도메인 노드 — 고객 리스크 등급 평가 + 권고사항."""
        if self.ontology is None or self.policy is None:
            raise AppError("MODEL_ERROR", "OntologyService/PolicyEngine이 주입되지 않았습니다.", 500)
        customer_id = (data.get("customer_id") or "").strip()
        if not customer_id:
            raise AppError("INVALID_NODE", "risk_assess 노드에 customer_id가 비어 있습니다.", 400)
        instance = self.ontology.registry.objects.get(customer_id)
        if instance is None or instance.object_type.name != "Customer":
            raise AppError("OBJECT_NOT_FOUND", f"고객을 찾을 수 없습니다: {customer_id}", 404)
        customer_dict = self.ontology.to_dict(instance)
        self.policy.assert_can_read_object(user, customer_dict)
        masked = self.policy.mask_object(user, customer_dict)
        risk = masked.get("risk_tier", "Unknown")
        recommendation = {
            "Low": "정상 승인 프로세스 가능",
            "Medium": "추가 검토 후 승인 권장",
            "High": "재무 팀장 결재 + 계약 검증 필수",
            "Restricted": "권한 부족으로 등급 확인 불가",
        }.get(risk, "기준 미정")
        return {"customer_id": customer_id, "risk_tier": risk, "recommendation": recommendation}

    def _call_llm(self, prompt: str) -> str:
        """LLMGateway의 클라이언트 재활용. 키 없거나 실패 시 룰베이스 폴백."""
        client = getattr(self.llm, "_client", None) or self.llm._genai and self.llm._genai.Client(
            api_key=self.llm.keys[0][1]
        ) if self.llm.keys else None
        if not self.llm.keys or self.llm._genai is None:
            return f"[rule-based] echo: {prompt[:200]}"
        for label, key in self.llm.keys:
            try:
                client = self.llm._genai.Client(api_key=key)
                response = client.models.generate_content(model=self.llm.model, contents=prompt)
                text = getattr(response, "text", None)
                if text:
                    self.llm.stats[label]["success"] += 1
                    self.llm.last_used_label = label
                    return text
            except Exception as exc:  # noqa: BLE001
                if "RESOURCE_EXHAUSTED" in str(exc) or "429" in str(exc):
                    self.llm.stats[label]["quota_fail"] += 1
                    continue
                self.llm.stats[label]["other_fail"] += 1
                continue
        return f"[rule-based fallback] echo: {prompt[:200]}"

    async def _call_http(self, method: str, url: str) -> dict:
        try:
            import httpx
        except ImportError as exc:
            raise AppError("MODEL_ERROR", "httpx가 설치되지 않았습니다.", 500) from exc
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.request(method, url)
        text = response.text[:500]
        try:
            payload = response.json() if response.headers.get("content-type", "").startswith("application/json") else text
        except Exception:  # noqa: BLE001
            payload = text
        return {"status": response.status_code, "preview": payload if not isinstance(payload, str) else payload}


def order_to_nodes(order: list[str], nodes: list[dict]) -> list[dict]:
    """위상정렬 순서대로 노드 dict를 반환."""
    by_id = {n["id"]: n for n in nodes}
    return [by_id[node_id] for node_id in order if node_id in by_id]
