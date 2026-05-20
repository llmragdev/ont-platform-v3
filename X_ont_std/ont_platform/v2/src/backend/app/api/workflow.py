"""Workflow API 라우터 v2.0.

app_context.py 없이 WorkflowService + WorkflowGraphService로 동작.
"""
from __future__ import annotations

import asyncio
import json as _json
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse

from app.models.tenant_context import TenantContext
from app.services.ontology import OntologyService
from app.services.workflow import WorkflowGraphService, WorkflowService

router = APIRouter(prefix="/api/workflow", tags=["workflow"])
graph_router = APIRouter(prefix="/api/workflow-graphs", tags=["workflow-graphs"])


# ── 의존성 ────────────────────────────────────────────────────────────────────

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


# ── Workflow 엔드포인트 ────────────────────────────────────────────────────────

@router.get("/queue")
def workflow_queue(
    entity_type: str | None = None,
    ctx: TenantContext = Depends(_ctx),
    svc: WorkflowService = Depends(_get_workflow_svc),
):
    """역할로 실행 가능한 액션이 있는 엔티티 목록."""
    rows = svc.queue(ctx, entity_type=entity_type)
    return {"count": len(rows), "items": rows}


@router.post("/execute")
def workflow_execute(
    body: dict,
    ctx: TenantContext = Depends(_ctx),
    svc: WorkflowService = Depends(_get_workflow_svc),
):
    """액션 실행 — 엔티티 상태 전이."""
    doc_id = body.get("doc_id", "")
    entity_id = body.get("entity_id", "")
    action_name = body.get("action", "")
    if not (doc_id and entity_id and action_name):
        raise HTTPException(status_code=400, detail="doc_id, entity_id, action 필드가 필요합니다.")
    try:
        return svc.execute(ctx, doc_id, entity_id, action_name)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ── WorkflowGraph 엔드포인트 ──────────────────────────────────────────────────

@graph_router.get("")
def list_graphs(
    ctx: TenantContext = Depends(_ctx),
    svc: WorkflowGraphService = Depends(_get_graph_svc),
):
    try:
        return svc.list_graphs(ctx)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@graph_router.get("/{graph_id}")
def get_graph(
    graph_id: str,
    ctx: TenantContext = Depends(_ctx),
    svc: WorkflowGraphService = Depends(_get_graph_svc),
):
    try:
        return svc.get_graph(ctx, graph_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@graph_router.post("")
def save_graph(
    body: dict,
    ctx: TenantContext = Depends(_ctx),
    svc: WorkflowGraphService = Depends(_get_graph_svc),
):
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
    """SSE 스트리밍으로 워크플로우 그래프를 시뮬레이션 실행합니다."""
    try:
        graph = svc.get_graph(ctx, graph_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    nodes = graph.get("nodes", [])

    async def event_stream():
        import time
        started_at = None
        completed = 0
        for node in nodes:
            node_id = node.get("id", "?")
            node_type = node.get("type", "start")
            label = (node.get("data") or {}).get("label") or node_type
            ts = __import__("datetime").datetime.utcnow().isoformat() + "Z"
            yield f"event: node_started\ndata: {_json.dumps({'node_id': node_id, 'label': label, 'type': node_type, 'started_at': ts})}\n\n"
            await asyncio.sleep(0.3)
            finished_ts = __import__("datetime").datetime.utcnow().isoformat() + "Z"
            output = f"[{node_type}] executed"
            yield f"event: node_finished\ndata: {_json.dumps({'node_id': node_id, 'label': label, 'type': node_type, 'status': 'success', 'output': output, 'started_at': ts, 'finished_at': finished_ts, 'duration_ms': 300})}\n\n"
            completed += 1
        yield f"event: run_finished\ndata: {_json.dumps({'status': 'completed', 'completed_count': completed})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@graph_router.delete("/{graph_id}")
def delete_graph(
    graph_id: str,
    ctx: TenantContext = Depends(_ctx),
    svc: WorkflowGraphService = Depends(_get_graph_svc),
):
    try:
        svc.delete_graph(ctx, graph_id)
        return {"deleted": graph_id}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
