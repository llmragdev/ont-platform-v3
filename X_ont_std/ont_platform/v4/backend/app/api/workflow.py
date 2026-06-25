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


@graph_router.post("/{graph_id}/run")
async def run_graph(
    graph_id: str,
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
