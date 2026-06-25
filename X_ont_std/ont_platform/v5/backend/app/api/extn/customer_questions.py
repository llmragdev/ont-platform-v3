"""Customer question event and batch polling APIs for Scenario 1."""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.extn.customer_replies import (
    DraftReplyResponse,
    GenerateAndPostResponse,
    PostViaMcpResponse,
    _generate_draft,
    _post_to_customer_mcp,
    DraftReplyRequest,
    PostViaMcpRequest,
)
from app.dependencies import (
    get_llm_client,
    get_ontology_service,
    get_query_planner_service,
    get_tenant_context,
    get_vector_search_service,
)
from app.extn.customer_mcp_client import CustomerMcpClient
from app.models.tenant_context import TenantContext
from app.services.customer_question_state import CustomerQuestionStateStore
from app.services.query_planner import QueryPlannerService


router = APIRouter(prefix="/api/extn/customer-questions", tags=["extn-customer-questions"])
logger = logging.getLogger(__name__)
_batch_task: Optional[asyncio.Task] = None


class CustomerQuestionEventRequest(BaseModel):
    event_id: str
    event_type: Literal["question.created"] = "question.created"
    question_id: str
    thread_id: Optional[str] = None
    post_id: Optional[str] = None
    title: Optional[str] = None
    content: str
    author: Optional[str] = None
    created_at: Optional[str] = None
    mode: Literal["dry_run", "post"] = "dry_run"
    force_reprocess: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CustomerQuestionEventResponse(BaseModel):
    event_id: str
    request_id: str
    status: Literal["accepted", "skipped", "error"]
    workflow_status: Literal["started", "skipped", "failed"]
    duplicate: bool
    draft: Optional[DraftReplyResponse] = None
    mcp: Optional[PostViaMcpResponse] = None
    reason: Optional[str] = None


class BatchPollingRequest(BaseModel):
    status: str = "open"
    mode: Literal["dry_run", "post"] = "dry_run"
    limit: int = Field(default=25, ge=1, le=100)
    force_reprocess: bool = False


class BatchPollingResponse(BaseModel):
    status: Literal["success", "error"]
    checked: int
    started: int
    skipped: int
    errors: int
    items: List[CustomerQuestionEventResponse] = Field(default_factory=list)
    error: Optional[Dict[str, Any]] = None


@router.post("/events", response_model=CustomerQuestionEventResponse)
async def receive_customer_question_event(
    request: CustomerQuestionEventRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    query_svc: QueryPlannerService = Depends(get_query_planner_service),
):
    """Receive a webhook/API trigger from the customer side and start reply workflow."""

    return await _handle_question_event(request, ctx, query_svc)


@router.post("/batch/run-once", response_model=BatchPollingResponse)
async def run_customer_question_batch_once(
    request: BatchPollingRequest = BatchPollingRequest(),
    ctx: TenantContext = Depends(get_tenant_context),
    query_svc: QueryPlannerService = Depends(get_query_planner_service),
):
    """Poll customer_mcp for open questions and reconcile missed webhooks."""

    return await _run_batch_once(request, ctx, query_svc)


@router.on_event("startup")
async def start_customer_question_batch_scheduler() -> None:
    """Optional 5-minute scheduler. Enable with CUSTOMER_QUESTION_BATCH_ENABLED=true."""

    global _batch_task
    enabled = os.getenv("CUSTOMER_QUESTION_BATCH_ENABLED", "false").lower() in {"1", "true", "yes"}
    if not enabled or _batch_task:
        return
    interval_seconds = int(os.getenv("CUSTOMER_QUESTION_BATCH_INTERVAL_SECONDS", "300"))
    mode = os.getenv("CUSTOMER_QUESTION_BATCH_MODE", "dry_run")
    if mode not in {"dry_run", "post"}:
        mode = "dry_run"
    _batch_task = asyncio.create_task(_batch_scheduler_loop(interval_seconds, mode))


async def _batch_scheduler_loop(interval_seconds: int, mode: str) -> None:
    ctx = TenantContext(
        user_id="system-batch",
        company_id=os.getenv("CUSTOMER_QUESTION_BATCH_COMPANY_ID", "default"),
        project_id=os.getenv("CUSTOMER_QUESTION_BATCH_PROJECT_ID", "proj-default"),
        role="System",
        permissions={},
    )
    query_svc = QueryPlannerService(
        ontology_svc=get_ontology_service(),
        vector_svc=get_vector_search_service(),
        llm_client=get_llm_client(),
    )
    while True:
        try:
            await _run_batch_once(BatchPollingRequest(mode=mode), ctx, query_svc)
        except Exception:
            logger.exception("customer question batch polling failed")
        await asyncio.sleep(interval_seconds)


async def _handle_question_event(
    request: CustomerQuestionEventRequest,
    ctx: TenantContext,
    query_svc: QueryPlannerService,
) -> CustomerQuestionEventResponse:
    store = CustomerQuestionStateStore(ctx)
    request_id = request.metadata.get("request_id") or str(uuid.uuid4())
    event_dict = request.model_dump(mode="json")

    if store.seen_event(request.event_id) and not request.force_reprocess:
        store.append_event(event_dict, status="skipped", duplicate=True)
        return CustomerQuestionEventResponse(
            event_id=request.event_id,
            request_id=request_id,
            status="skipped",
            workflow_status="skipped",
            duplicate=True,
            reason="event_already_seen",
        )

    processed = store.successful_question(request.question_id)
    if processed and not request.force_reprocess:
        store.mark_event(
            request.event_id,
            {
                "status": "skipped",
                "question_id": request.question_id,
                "request_id": request_id,
                "reason": "question_already_processed",
            },
        )
        store.append_event(event_dict, status="skipped", duplicate=False)
        return CustomerQuestionEventResponse(
            event_id=request.event_id,
            request_id=request_id,
            status="skipped",
            workflow_status="skipped",
            duplicate=False,
            reason="question_already_processed",
        )

    question_text = _event_question_text(request)
    try:
        draft = _generate_draft(
            DraftReplyRequest(
                request_id=request_id,
                question_id=request.question_id,
                question_text=question_text,
                context={**request.metadata, "event_id": request.event_id},
            ),
            ctx,
            query_svc,
        )
        mcp = await _post_to_customer_mcp(
            PostViaMcpRequest(
                request_id=request_id,
                question_id=request.question_id,
                reply_message=draft.reply_message,
                mode=request.mode,
                thread_id=request.thread_id,
                post_id=request.post_id or request.question_id,
                workflow_run_id=request.metadata.get("workflow_run_id"),
                metadata={
                    **request.metadata,
                    "event_id": request.event_id,
                    "force_reprocess": request.force_reprocess,
                },
            ),
            ctx,
        )
    except HTTPException:
        raise
    except Exception as exc:
        store.mark_event(
            request.event_id,
            {
                "status": "error",
                "question_id": request.question_id,
                "request_id": request_id,
                "error": str(exc),
            },
        )
        store.append_event(event_dict, status="error", duplicate=False)
        raise HTTPException(status_code=500, detail=f"customer question workflow failed: {exc}") from exc

    workflow_status = "started" if mcp.status in {"dry_run", "success"} else "failed"
    status = "accepted" if workflow_status == "started" else "error"
    store.mark_event(
        request.event_id,
        {
            "status": status,
            "workflow_status": workflow_status,
            "question_id": request.question_id,
            "request_id": request_id,
            "mcp_status": mcp.status,
        },
    )
    if request.mode == "post" and mcp.status == "success":
        result = mcp.result or {}
        store.mark_question(
            request.question_id,
            {
                "status": "success",
                "request_id": request_id,
                "event_id": request.event_id,
                "external_comment_id": result.get("external_comment_id"),
                "external_thread_id": result.get("external_thread_id"),
                "url": result.get("url"),
                "source": request.metadata.get("source", "event_trigger"),
            },
        )
    store.append_event(event_dict, status=status, duplicate=False)
    return CustomerQuestionEventResponse(
        event_id=request.event_id,
        request_id=request_id,
        status=status,
        workflow_status=workflow_status,
        duplicate=False,
        draft=draft,
        mcp=mcp,
    )


async def _run_batch_once(
    request: BatchPollingRequest,
    ctx: TenantContext,
    query_svc: QueryPlannerService,
) -> BatchPollingResponse:
    client = CustomerMcpClient()
    listed = await client.list_questions(status=request.status)
    if listed.get("status") != "success":
        return BatchPollingResponse(
            status="error",
            checked=0,
            started=0,
            skipped=0,
            errors=1,
            error=listed.get("error") or {"code": "UNKNOWN", "message": "question.list failed", "retryable": True},
        )

    questions = (listed.get("result") or {}).get("questions") or []
    items: List[CustomerQuestionEventResponse] = []
    for question in questions[: request.limit]:
        event = CustomerQuestionEventRequest(
            event_id=f"batch-{question.get('question_id')}-{uuid.uuid4()}",
            question_id=str(question.get("question_id")),
            thread_id=question.get("thread_id"),
            post_id=question.get("post_id") or question.get("question_id"),
            title=question.get("title"),
            content=str(question.get("content") or ""),
            author=question.get("author"),
            created_at=question.get("created_at"),
            mode=request.mode,
            force_reprocess=request.force_reprocess,
            metadata={"source": "batch_polling"},
        )
        items.append(await _handle_question_event(event, ctx, query_svc))

    started = sum(1 for item in items if item.workflow_status == "started")
    skipped = sum(1 for item in items if item.workflow_status == "skipped")
    errors = sum(1 for item in items if item.workflow_status == "failed")
    CustomerQuestionStateStore(ctx).mark_batch(
        {
            "status": request.status,
            "mode": request.mode,
            "checked": len(questions[: request.limit]),
            "started": started,
            "skipped": skipped,
            "errors": errors,
        }
    )
    return BatchPollingResponse(
        status="success",
        checked=len(questions[: request.limit]),
        started=started,
        skipped=skipped,
        errors=errors,
        items=items,
    )


def _event_question_text(request: CustomerQuestionEventRequest) -> str:
    if request.title:
        return f"{request.title}\n\n{request.content}"
    return request.content
