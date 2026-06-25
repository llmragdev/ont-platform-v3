"""Factory event webhook and batch APIs for repeated fault demo."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_tenant_context
from app.extn.factory_mcp_client import FactoryMcpClient, FactoryToolResponse
from app.models.tenant_context import TenantContext
from app.services.factory_event_state import FactoryEventStateStore
from app.services.factory_ontology_writer import FactoryOntologyWriter


router = APIRouter(prefix="/api/extn/factory-events", tags=["extn-factory-events"])


class FactoryEventRequest(BaseModel):
    event_id: str
    event_type: Literal["factory_event.created"] = "factory_event.created"
    factory_event_id: str
    category: str
    factory_name: str
    line_name: str
    process_step: str
    equipment_name: str
    fault_message: Optional[str] = None
    severity: str = "medium"
    occurred_at: str
    title: str
    content: str
    reporter: str
    mode: Literal["dry_run", "post"] = "dry_run"
    force_reprocess: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FactoryEventResponse(BaseModel):
    event_id: str
    request_id: str
    status: Literal["accepted", "skipped", "error"]
    workflow_status: Literal["started", "skipped", "failed"]
    duplicate: bool
    repeated: bool = False
    response_mcp: Optional[FactoryToolResponse] = None
    maintenance_mcp: Optional[FactoryToolResponse] = None
    ontology_writeback: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None


class FactoryBatchRequest(BaseModel):
    status: str = "open"
    mode: Literal["dry_run", "post"] = "dry_run"
    limit: int = Field(default=20, ge=1, le=100)
    force_reprocess: bool = False


class FactoryBatchResponse(BaseModel):
    status: Literal["success", "error"]
    checked: int
    started: int
    skipped: int
    errors: int
    items: List[FactoryEventResponse] = Field(default_factory=list)
    error: Optional[Dict[str, Any]] = None


@router.post("/events", response_model=FactoryEventResponse)
async def receive_factory_event(
    request: FactoryEventRequest,
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await _handle_factory_event(request, ctx)


@router.post("/batch/run-once", response_model=FactoryBatchResponse)
async def run_factory_batch_once(
    request: FactoryBatchRequest = FactoryBatchRequest(),
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await _run_factory_batch_once(request, ctx)


async def _run_factory_batch_once(request: FactoryBatchRequest, ctx: TenantContext) -> FactoryBatchResponse:
    client = FactoryMcpClient()
    request_id = str(uuid.uuid4())
    listed = await client.list_events(request_id=request_id, company_id=ctx.company_id, project_id=ctx.project_id, status=request.status, limit=request.limit)
    if listed.status == "error":
        return FactoryBatchResponse(status="error", checked=0, started=0, skipped=0, errors=1, error=listed.error)

    raw_items = ((listed.result or {}).get("items") or [])[: request.limit]
    items: list[FactoryEventResponse] = []
    started = skipped = errors = 0
    for raw in raw_items:
        try:
            event = _event_from_board_item(raw, mode=request.mode, force_reprocess=request.force_reprocess)
            result = await _handle_factory_event(event, ctx)
            items.append(result)
            if result.status == "accepted":
                started += 1
            elif result.status == "skipped":
                skipped += 1
            else:
                errors += 1
        except Exception as exc:
            errors += 1
            items.append(
                FactoryEventResponse(
                    event_id=f"batch-error-{uuid.uuid4()}",
                    request_id=str(uuid.uuid4()),
                    status="error",
                    workflow_status="failed",
                    duplicate=False,
                    reason=str(exc),
                )
            )
    FactoryEventStateStore(ctx).mark_batch({"status": "success", "checked": len(raw_items), "started": started, "skipped": skipped, "errors": errors})
    return FactoryBatchResponse(status="success", checked=len(raw_items), started=started, skipped=skipped, errors=errors, items=items)


async def _handle_factory_event(request: FactoryEventRequest, ctx: TenantContext, workflow_run_id: str | None = None) -> FactoryEventResponse:
    store = FactoryEventStateStore(ctx)
    request_id = request.metadata.get("request_id") or str(uuid.uuid4())
    event_dict = request.model_dump(mode="json")

    if store.seen_event(request.event_id) and not request.force_reprocess:
        store.append_event(event_dict, status="skipped", duplicate=True)
        return FactoryEventResponse(event_id=request.event_id, request_id=request_id, status="skipped", workflow_status="skipped", duplicate=True, reason="event_already_seen")

    processed = store.successful_factory_event(request.factory_event_id)
    if processed and not request.force_reprocess:
        store.mark_event(request.event_id, {"status": "skipped", "factory_event_id": request.factory_event_id, "request_id": request_id, "reason": "factory_event_already_processed"})
        store.append_event(event_dict, status="skipped", duplicate=False)
        return FactoryEventResponse(event_id=request.event_id, request_id=request_id, status="skipped", workflow_status="skipped", duplicate=False, reason="factory_event_already_processed")

    client = FactoryMcpClient()
    related_events = await client.list_events(request_id=str(uuid.uuid4()), company_id=ctx.company_id, project_id=ctx.project_id, status="open", limit=100)
    all_events = (related_events.result or {}).get("items") or []
    repeated = _is_repeated(request.model_dump(mode="json"), all_events)
    response_message = _response_message(request, repeated)

    response_mcp = await client.create_response(
        request_id=request_id,
        company_id=ctx.company_id,
        project_id=ctx.project_id,
        mode=request.mode,
        event_id=request.factory_event_id,
        message=response_message,
        workflow_run_id=workflow_run_id,
    )
    maintenance_mcp: FactoryToolResponse | None = None
    if repeated or request.category == "quality_issue":
        maintenance_mcp = await client.create_maintenance_task(
            request_id=str(uuid.uuid4()),
            company_id=ctx.company_id,
            project_id=ctx.project_id,
            mode=request.mode,
            event=request.model_dump(mode="json"),
            priority="high" if repeated else "medium",
            message=_maintenance_message(request, repeated),
            workflow_run_id=workflow_run_id,
        )

    ok = response_mcp.status in {"dry_run", "success"} and (maintenance_mcp is None or maintenance_mcp.status in {"dry_run", "success"})
    ontology = FactoryOntologyWriter().write_event_result(
        ctx=ctx,
        event=request.model_dump(mode="json"),
        request_id=request_id,
        mode=request.mode,
        repeated=repeated,
        response_result=response_mcp.result,
        maintenance_result=maintenance_mcp.result if maintenance_mcp else None,
        workflow_run_id=workflow_run_id,
    )
    status = "accepted" if ok else "error"
    workflow_status = "started" if ok else "failed"
    store.mark_event(request.event_id, {"status": status, "workflow_status": workflow_status, "factory_event_id": request.factory_event_id, "request_id": request_id, "mcp_status": response_mcp.status})
    if ok and request.mode == "post":
        store.mark_factory_event(request.factory_event_id, {"status": "success", "request_id": request_id, "event_id": request.event_id, "response": response_mcp.result, "maintenance": maintenance_mcp.result if maintenance_mcp else None})
    store.append_event(event_dict, status=status, duplicate=False)
    return FactoryEventResponse(event_id=request.event_id, request_id=request_id, status=status, workflow_status=workflow_status, duplicate=False, repeated=repeated, response_mcp=response_mcp, maintenance_mcp=maintenance_mcp, ontology_writeback=ontology)


def _event_from_board_item(raw: Dict[str, Any], *, mode: str, force_reprocess: bool) -> FactoryEventRequest:
    event_id = f"batch-{raw.get('id')}-{uuid.uuid4()}"
    return FactoryEventRequest(
        event_id=event_id,
        factory_event_id=raw["id"],
        category=raw.get("category") or "equipment_fault",
        factory_name=raw.get("factory_name") or "",
        line_name=raw.get("line_name") or "",
        process_step=raw.get("process_step") or "",
        equipment_name=raw.get("equipment_name") or "",
        fault_message=raw.get("fault_message"),
        severity=raw.get("severity") or "medium",
        occurred_at=raw.get("occurred_at") or raw.get("created_at") or "",
        title=raw.get("title") or raw.get("id"),
        content=raw.get("content") or "",
        reporter=raw.get("reporter") or "factory-user",
        mode=mode,
        force_reprocess=force_reprocess,
        metadata={"source": "factory_batch"},
    )


def _is_repeated(event: Dict[str, Any], all_events: List[Dict[str, Any]]) -> bool:
    if event.get("category") == "quality_issue":
        return True
    equipment = event.get("equipment_name")
    fault = event.get("fault_message")
    if not equipment or not fault:
        return False
    matches = [
        item for item in all_events
        if item.get("equipment_name") == equipment and item.get("fault_message") == fault
    ]
    ids = {item.get("id") for item in matches}
    ids.add(event.get("factory_event_id"))
    return len([i for i in ids if i]) >= 2


def _response_message(request: FactoryEventRequest, repeated: bool) -> str:
    if request.category == "quality_issue":
        return "장비 고장 이후 품질 문제가 함께 접수되었습니다. 앞선 설비 이상과 연결해 정비팀과 품질팀이 함께 확인하도록 올리겠습니다."
    if repeated:
        return "같은 장비에서 같은 문제가 반복 접수되었습니다. 단순 문의가 아니라 반복 고장으로 보고 정비팀 확인 건으로 올리겠습니다."
    return f"{request.equipment_name} 고장 문의를 접수했습니다. 같은 장비에서 같은 문제가 반복되는지 확인하겠습니다."


def _maintenance_message(request: FactoryEventRequest, repeated: bool) -> str:
    if request.category == "quality_issue":
        return f"{request.line_name}에서 품질 이상이 감지되었습니다. 최근 설비 고장과 연관 가능성을 함께 확인해 주세요."
    if repeated:
        return f"{request.equipment_name}에서 '{request.fault_message}' 문제가 반복되었습니다. 정비팀 확인이 필요합니다."
    return f"{request.equipment_name} 점검 요청입니다."
