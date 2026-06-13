"""Workflow API v3.0 — with WorkflowRun history."""
from __future__ import annotations

import asyncio
import json as _json
import uuid
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse

from pydantic import BaseModel, Field
from fastapi import Query
from app.models.tenant_context import TenantContext
from app.models.workflow_run import StepStatus, WorkflowRun, WorkflowStepRun
from app.models.action import ActionRequest, ActionResponse
from app.services.ontology import OntologyService
from app.services.workflow import WorkflowGraphService, WorkflowService
from storage_config import get_workflow_runs_path

router = APIRouter(prefix="/api/workflow", tags=["workflow"])
graph_router = APIRouter(prefix="/api/workflow-graphs", tags=["workflow-graphs"])

FACTORY_STEP_LABELS = {
    "request-input": "현장 요청 입력",
    "category-classify": "고장/품질 분류",
    "asset-map": "공장-라인-설비 매핑",
    "recurrence-check": "반복 여부 확인",
    "fault-register": "고장 상황 등록",
    "maintenance-task": "정비팀 확인 건 생성",
    "quality-link": "품질 문제 연결",
    "draft-response": "현장 안내 답변 생성",
    "notify-teams": "정비/품질팀 알림",
    "ontology-write": "온톨로지 저장",
}


def _get_ontology_svc() -> OntologyService:
    return OntologyService()


def _get_workflow_svc(ont: OntologyService = Depends(_get_ontology_svc)) -> WorkflowService:
    return WorkflowService(ontology_svc=ont)


def _get_graph_svc() -> WorkflowGraphService:
    return WorkflowGraphService()


def _ctx(
    x_user_id: str = Header(default="default-user"),
    x_company_id: str = Header(default="default"),
    x_project_id: str = Header(default="proj-default"),
    x_role: str = Header(default="Viewer"),
) -> TenantContext:
    return TenantContext(x_user_id, x_company_id, x_project_id, x_role, {})


# ── Workflow ──────────────────────────────────────────────────────────────────

@router.get("/queue", summary="액션 큐 조회", tags=["workflow"])
def workflow_queue(
    entity_type: str | None = Query(None, description="엔티티 타입 필터 (e.g., PROJECT)"),
    domain_id: str = Query("ai-voucher-2025", description="도메인 ID (e.g., ai-voucher-2025, order)"),
    ctx: TenantContext = Depends(_ctx),
    svc: WorkflowService = Depends(_get_workflow_svc),
):
    """
    현재 사용자가 실행 가능한 액션 목록 조회

    **파라미터**:
    - `entity_type`: 엔티티 타입별 필터링 (선택사항)
    - `domain_id`: 워크플로우 도메인 지정 (기본값: ai-voucher-2025)

    **응답**:
    - `count`: 반환된 액션 수
    - `items`: 실행 가능한 액션 목록
    """
    rows = svc.queue(ctx, entity_type=entity_type, domain_id=domain_id)
    return {"count": len(rows), "items": rows}


class WorkflowGraphCloneRequest(BaseModel):
    name: str | None = None


class WorkflowGraphRunRequest(BaseModel):
    execution_mode: str | None = None
    mode: str | None = None
    status: str = "open"
    limit: int = 10
    force_reprocess: bool = False


class WorkflowExecuteRequest(BaseModel):
    """액션 실행 요청"""
    doc_id: str = Field(..., description="문서 ID (e.g., ai-voucher-2025)")
    entity_id: str = Field(..., description="엔티티 ID (e.g., P001AAA)")
    action: str = Field(..., description="액션 이름 (e.g., approve_project)")
    domain_id: str = Field("ai-voucher-2025", description="도메인 ID")
    params: dict = Field({}, description="액션 파라미터 (e.g., {\"new_deadline\": \"2027-12-31\"})")


@router.post("/execute", response_model=ActionResponse, summary="액션 실행", tags=["workflow"])
def workflow_execute(
    body: WorkflowExecuteRequest,
    ctx: TenantContext = Depends(_ctx),
    svc: WorkflowService = Depends(_get_workflow_svc),
):
    """
    엔티티에 대해 액션 실행

    **가능한 액션**:
    - `approve_project`: 과제 승인 (상태: UnderReview → Approved)
    - `reject_project`: 과제 반려 (반려_사유 필수)
    - `change_deadline`: 일정 변경 (new_deadline 파라미터 필수)
    - `request_more_info`: 정보 요청 (info_needed 파라미터 필수)
    - `start_payment`: 지급 시작 (상태: Approved → InProgress)
    - `complete_project`: 과제 완료 (상태: InProgress → Completed)

    **권한 요구사항**:
    - `approve_project`: 조건부 권한 (예산 규모에 따라 TeamLead/FinanceManager/Admin)
    - `reject_project`: Admin, FinanceManager, AccountManager
    - `change_deadline`: Admin, FinanceManager, Manager
    - `request_more_info`: Admin, FinanceManager, AccountManager
    - `start_payment`: Admin, FinanceManager, PaymentManager
    - `complete_project`: Admin, FinanceManager

    **응답**:
    - `entity_id`: 처리된 엔티티 ID
    - `action`: 실행된 액션 이름
    - `from_status`: 이전 상태
    - `to_status`: 변경된 상태 (null이면 상태 유지)
    """
    doc_id = body.doc_id
    entity_id = body.entity_id
    action_name = body.action
    domain_id = body.domain_id
    params = body.params

    if not (doc_id and entity_id and action_name):
        raise HTTPException(status_code=400, detail="doc_id, entity_id, action 필드가 필요합니다.")

    try:
        return svc.execute(ctx, doc_id, entity_id, action_name, domain_id=domain_id, params=params)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ── WorkflowGraph ─────────────────────────────────────────────────────────────

@graph_router.get("")
def list_graphs(ctx: TenantContext = Depends(_ctx), svc: WorkflowGraphService = Depends(_get_graph_svc)):
    try:
        return svc.list_graphs(ctx)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@graph_router.get("/{graph_id}")
def get_graph(graph_id: str, ctx: TenantContext = Depends(_ctx), svc: WorkflowGraphService = Depends(_get_graph_svc)):
    try:
        return svc.get_graph(ctx, graph_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@graph_router.post("")
def save_graph(body: dict, ctx: TenantContext = Depends(_ctx), svc: WorkflowGraphService = Depends(_get_graph_svc)):
    try:
        return svc.save_graph(ctx, body)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@graph_router.post("/{graph_id}/clone")
def clone_graph(
    graph_id: str,
    body: WorkflowGraphCloneRequest = WorkflowGraphCloneRequest(),
    ctx: TenantContext = Depends(_ctx),
    svc: WorkflowGraphService = Depends(_get_graph_svc),
):
    try:
        return svc.clone_graph(ctx, graph_id, name=body.name)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@graph_router.post("/{graph_id}/run")
async def run_graph(
    graph_id: str,
    body: WorkflowGraphRunRequest | None = None,
    ctx: TenantContext = Depends(_ctx),
    svc: WorkflowGraphService = Depends(_get_graph_svc),
):
    """SSE 스트리밍으로 그래프를 실행하고 WorkflowRun 이력을 저장합니다."""
    try:
        graph = svc.get_graph(ctx, graph_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    runtime = graph.get("runtime") or {}
    if runtime.get("executor") == "scenario1.customer_question_auto_reply":
        options = body or WorkflowGraphRunRequest()
        return StreamingResponse(
            _run_scenario1_customer_reply_stream(graph, graph_id, ctx, svc, options),
            media_type="text/event-stream",
        )
    if runtime.get("executor") == "factory.repeated_fault_response":
        options = body or WorkflowGraphRunRequest()
        return StreamingResponse(
            _run_factory_repeated_fault_stream(graph, graph_id, ctx, svc, options),
            media_type="text/event-stream",
        )

    nodes = graph.get("nodes", [])
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    import datetime as dt

    async def event_stream():
        import datetime as _dt
        started_at = _dt.datetime.utcnow().isoformat() + "Z"
        step_runs: list[WorkflowStepRun] = []
        user_trace: list[str] = []
        tech_trace: list[str] = [f"run_id={run_id}", f"graph_id={graph_id}"]
        completed = 0

        for node in nodes:
            node_id = node.get("id", "?")
            node_type = node.get("type", "start")
            label = (node.get("data") or {}).get("label") or node_type
            ts = _dt.datetime.utcnow().isoformat() + "Z"
            step_id = f"step-{uuid.uuid4().hex[:8]}"

            step_run = WorkflowStepRun(step_id=step_id, node_id=node_id, node_type=node_type,
                                       status=StepStatus.RUNNING, started_at=ts)
            yield f"event: node_started\ndata: {_json.dumps({'node_id': node_id, 'label': label, 'type': node_type, 'started_at': ts})}\n\n"
            await asyncio.sleep(0.3)

            finished_ts = _dt.datetime.utcnow().isoformat() + "Z"
            output = f"[{node_type}] executed"
            step_run.status = StepStatus.SUCCEEDED
            step_run.finished_at = finished_ts
            step_run.output = {"result": output}
            step_runs.append(step_run)
            user_trace.append(f"{label} 완료")
            tech_trace.append(f"node={node_id} type={node_type} duration_ms=300")
            completed += 1

            yield f"event: node_finished\ndata: {_json.dumps({'node_id': node_id, 'label': label, 'type': node_type, 'status': 'success', 'output': output, 'started_at': ts, 'finished_at': finished_ts, 'duration_ms': 300})}\n\n"

        finished_at = _dt.datetime.utcnow().isoformat() + "Z"
        run = WorkflowRun(
            run_id=run_id, graph_id=graph_id, status=StepStatus.SUCCEEDED,
            triggered_by=ctx.user_id, started_at=started_at, finished_at=finished_at,
            steps=step_runs, user_trace=user_trace, tech_trace=tech_trace,
        )
        svc.save_run(ctx, run)
        yield f"event: run_finished\ndata: {_json.dumps({'status': 'completed', 'completed_count': completed, 'run_id': run_id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


async def _run_scenario1_customer_reply_stream(
    graph: dict,
    graph_id: str,
    ctx: TenantContext,
    svc: WorkflowGraphService,
    options: WorkflowGraphRunRequest,
):
    import datetime as _dt
    from app.api.extn.customer_questions import BatchPollingRequest, _run_batch_once
    from app.dependencies import get_llm_client, get_ontology_service, get_vector_search_service
    from app.services.query_planner import QueryPlannerService
    from app.services.workflow_ontology_writer import WorkflowOntologyWriter

    nodes = graph.get("nodes", [])
    node_by_id = {node.get("id"): node for node in nodes}
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    started_at = _dt.datetime.utcnow().isoformat() + "Z"
    step_runs: list[WorkflowStepRun] = []
    user_trace: list[str] = []
    tech_trace: list[str] = [
        f"run_id={run_id}",
        f"graph_id={graph_id}",
        "executor=scenario1.customer_question_auto_reply",
    ]

    async def emit_node(node_id: str, output: dict, status: StepStatus = StepStatus.SUCCEEDED):
        node = node_by_id.get(node_id) or {"id": node_id, "type": node_id, "data": {"label": node_id}}
        node_type = node.get("type", node_id)
        label = (node.get("data") or {}).get("label") or node_type
        ts = _dt.datetime.utcnow().isoformat() + "Z"
        step_id = f"step-{uuid.uuid4().hex[:8]}"
        yield f"event: node_started\ndata: {_json.dumps({'node_id': node_id, 'label': label, 'type': node_type, 'started_at': ts}, ensure_ascii=False)}\n\n"
        finished_ts = _dt.datetime.utcnow().isoformat() + "Z"
        step_runs.append(
            WorkflowStepRun(
                step_id=step_id,
                node_id=node_id,
                node_type=node_type,
                status=status,
                started_at=ts,
                finished_at=finished_ts,
                output=output,
            )
        )
        user_trace.append(f"{label} completed")
        tech_trace.append(f"node={node_id} type={node_type} status={status.value}")
        yield f"event: node_finished\ndata: {_json.dumps({'node_id': node_id, 'label': label, 'type': node_type, 'status': 'success' if status == StepStatus.SUCCEEDED else 'error', 'output': output, 'started_at': ts, 'finished_at': finished_ts, 'duration_ms': 0}, ensure_ascii=False)}\n\n"

    try:
        runtime = graph.get("runtime") or {}
        mode = options.mode or runtime.get("default_mode") or "dry_run"
        if mode not in {"dry_run", "post"}:
            mode = "dry_run"
        limit = options.limit or int(runtime.get("batch_limit") or 10)
        status = options.status or runtime.get("batch_status") or "open"

        async for frame in emit_node("request-input", {"execution_mode": options.execution_mode or "batch", "mode": mode, "status": status, "limit": limit}):
            yield frame

        query_svc = QueryPlannerService(
            ontology_svc=get_ontology_service(),
            vector_svc=get_vector_search_service(),
            llm_client=get_llm_client(),
        )
        batch_result = await _run_batch_once(
            BatchPollingRequest(
                status=status,
                mode=mode,
                limit=limit,
                force_reprocess=options.force_reprocess,
            ),
            ctx,
            query_svc,
        )
        result_dict = batch_result.model_dump(mode="json")
        ontology_writeback = {"status": "skipped"}

        async for frame in emit_node("draft-response", {"started": result_dict.get("started"), "skipped": result_dict.get("skipped")}):
            yield frame
        async for frame in emit_node("post-comment", result_dict):
            yield frame
        finished_for_ontology = _dt.datetime.utcnow().isoformat() + "Z"
        try:
            ontology_writeback = {
                "status": "success",
                **WorkflowOntologyWriter().write_scenario1_batch_result(
                    ctx=ctx,
                    graph=graph,
                    run_id=run_id,
                    run_started_at=started_at,
                    run_finished_at=finished_for_ontology,
                    mode=mode,
                    batch_result=result_dict,
                ),
            }
        except Exception as exc:
            ontology_writeback = {"status": "failed", "error": str(exc)}
            tech_trace.append(f"ontology_writeback_error={exc}")

        async for frame in emit_node("audit-write", {"audit": "customer_mcp_calls.jsonl", "events": "customer_question_state.json", "ontology_writeback": ontology_writeback}):
            yield frame

        finished_at = _dt.datetime.utcnow().isoformat() + "Z"
        run_status = StepStatus.SUCCEEDED if result_dict.get("status") == "success" and result_dict.get("errors", 0) == 0 else StepStatus.FAILED
        run = WorkflowRun(
            run_id=run_id,
            graph_id=graph_id,
            status=run_status,
            triggered_by=ctx.user_id,
            started_at=started_at,
            finished_at=finished_at,
            steps=step_runs,
            user_trace=user_trace,
            tech_trace=tech_trace,
        )
        svc.save_run(ctx, run)
        yield f"event: run_finished\ndata: {_json.dumps({'status': 'completed' if run_status == StepStatus.SUCCEEDED else 'failed', 'completed_count': len(step_runs), 'run_id': run_id, 'summary': result_dict, 'ontology_writeback': ontology_writeback}, ensure_ascii=False)}\n\n"
    except Exception as exc:
        finished_at = _dt.datetime.utcnow().isoformat() + "Z"
        run = WorkflowRun(
            run_id=run_id,
            graph_id=graph_id,
            status=StepStatus.FAILED,
            triggered_by=ctx.user_id,
            started_at=started_at,
            finished_at=finished_at,
            steps=step_runs,
            user_trace=user_trace,
            tech_trace=tech_trace + [f"error={exc}"],
        )
        svc.save_run(ctx, run)
        yield f"event: run_failed\ndata: {_json.dumps({'run_id': run_id, 'error': str(exc)}, ensure_ascii=False)}\n\n"


async def _run_factory_repeated_fault_stream(
    graph: dict,
    graph_id: str,
    ctx: TenantContext,
    svc: WorkflowGraphService,
    options: WorkflowGraphRunRequest,
):
    import datetime as _dt
    from app.api.extn.factory_events import FactoryBatchRequest, _run_factory_batch_once

    nodes = graph.get("nodes", [])
    runtime = graph.get("runtime") or {}
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    started_at = _dt.datetime.utcnow().isoformat() + "Z"
    step_runs: list[WorkflowStepRun] = []
    user_trace: list[str] = []
    tech_trace: list[str] = [f"run_id={run_id}", f"graph_id={graph_id}", "executor=factory.repeated_fault_response"]

    async def emit_node(node_id: str, output: dict[str, Any], status: StepStatus = StepStatus.SUCCEEDED):
        node = next((item for item in nodes if item.get("id") == node_id), {"id": node_id, "type": node_id, "data": {"label": node_id}})
        node_type = node.get("type", node_id)
        label = FACTORY_STEP_LABELS.get(node_id) or (node.get("data") or {}).get("label") or node_type
        ts = _dt.datetime.utcnow().isoformat() + "Z"
        step_id = f"step-{uuid.uuid4().hex[:8]}"
        yield f"event: node_started\ndata: {_json.dumps({'node_id': node_id, 'label': label, 'type': node_type, 'started_at': ts}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.05)
        finished_ts = _dt.datetime.utcnow().isoformat() + "Z"
        step_runs.append(WorkflowStepRun(step_id=step_id, node_id=node_id, node_type=node_type, status=status, started_at=ts, finished_at=finished_ts, output=output))
        user_trace.append(f"{label} completed")
        tech_trace.append(f"node={node_id} type={node_type} status={status}")
        yield f"event: node_finished\ndata: {_json.dumps({'node_id': node_id, 'label': label, 'type': node_type, 'status': 'success' if status == StepStatus.SUCCEEDED else 'error', 'output': output, 'started_at': ts, 'finished_at': finished_ts, 'duration_ms': 50}, ensure_ascii=False)}\n\n"

    try:
        mode = options.mode or runtime.get("default_mode") or "dry_run"
        limit = options.limit or runtime.get("batch_limit") or 20
        async for frame in emit_node("request-input", {"execution_mode": "batch", "mode": mode, "limit": limit}):
            yield frame
        async for frame in emit_node("category-classify", {"categories": ["equipment_fault", "quality_issue"]}):
            yield frame
        async for frame in emit_node("asset-map", {"factory": runtime.get("sample_factory"), "line": runtime.get("sample_line"), "equipment": runtime.get("sample_equipment")}):
            yield frame
        result = await _run_factory_batch_once(
            FactoryBatchRequest(status=options.status or "open", mode=mode, limit=limit, force_reprocess=options.force_reprocess),
            ctx,
        )
        result_dict = result.model_dump(mode="json")
        async for frame in emit_node("recurrence-check", {"checked": result.checked, "started": result.started, "skipped": result.skipped, "errors": result.errors}):
            yield frame
        async for frame in emit_node("fault-register", {"status": result.status, "items": len(result.items)}):
            yield frame
        maintenance_count = sum(1 for item in result.items if item.maintenance_mcp is not None)
        async for frame in emit_node("maintenance-task", {"created_or_dry_run": maintenance_count}):
            yield frame
        quality_count = sum(1 for item in result.items if "quality" in (item.reason or "") or (item.ontology_writeback or {}).get("repeated"))
        async for frame in emit_node("quality-link", {"linked": quality_count}):
            yield frame
        async for frame in emit_node("draft-response", {"responses": sum(1 for item in result.items if item.response_mcp is not None)}):
            yield frame
        async for frame in emit_node("notify-teams", {"factory_mcp": "s2_factory_mcp", "port": 8081}):
            yield frame
        async for frame in emit_node("ontology-write", {"doc_id": "factory-repeated-faults", "items": [item.ontology_writeback for item in result.items]}):
            yield frame

        finished_at = _dt.datetime.utcnow().isoformat() + "Z"
        run_status = StepStatus.SUCCEEDED if result.errors == 0 else StepStatus.FAILED
        run = WorkflowRun(run_id=run_id, graph_id=graph_id, status=run_status, triggered_by=ctx.user_id, started_at=started_at, finished_at=finished_at, steps=step_runs, user_trace=user_trace, tech_trace=tech_trace)
        svc.save_run(ctx, run)
        yield f"event: run_finished\ndata: {_json.dumps({'status': 'completed' if run_status == StepStatus.SUCCEEDED else 'failed', 'completed_count': len(step_runs), 'run_id': run_id, 'summary': result_dict}, ensure_ascii=False)}\n\n"
    except Exception as exc:
        finished_at = _dt.datetime.utcnow().isoformat() + "Z"
        run = WorkflowRun(run_id=run_id, graph_id=graph_id, status=StepStatus.FAILED, triggered_by=ctx.user_id, started_at=started_at, finished_at=finished_at, steps=step_runs, user_trace=user_trace + ["factory workflow failed"], tech_trace=tech_trace + [f"error={exc}"])
        svc.save_run(ctx, run)
        yield f"event: run_failed\ndata: {_json.dumps({'run_id': run_id, 'error': str(exc)}, ensure_ascii=False)}\n\n"


@graph_router.get("/{graph_id}/runs")
def list_runs(graph_id: str, ctx: TenantContext = Depends(_ctx),
              svc: WorkflowGraphService = Depends(_get_graph_svc)):
    try:
        return {"graph_id": graph_id, "runs": svc.list_runs(ctx, graph_id)}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@graph_router.get("/{graph_id}/runs/{run_id}")
def get_run(graph_id: str, run_id: str, ctx: TenantContext = Depends(_ctx),
            svc: WorkflowGraphService = Depends(_get_graph_svc)):
    try:
        return svc.get_run(ctx, graph_id, run_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@graph_router.delete("/{graph_id}")
def delete_graph(graph_id: str, ctx: TenantContext = Depends(_ctx),
                 svc: WorkflowGraphService = Depends(_get_graph_svc)):
    try:
        svc.delete_graph(ctx, graph_id)
        return {"deleted": graph_id}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
