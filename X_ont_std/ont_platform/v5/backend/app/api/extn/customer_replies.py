"""Customer reply API for LLM webhook draft + customer MCP relay.

This API follows:
ont_platform/v5/scenarios/v1/scenario1/CUSTOMER_MCP_CALL_SPEC.md
"""
from __future__ import annotations

import json
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_query_planner_service, get_tenant_context
from app.extn.customer_mcp_client import (
    CommentCreateArguments,
    CommentCreateMetadata,
    CommentCreateRequest,
    CustomerMcpClient,
)
from app.models.query_intent import SearchMode
from app.models.tenant_context import TenantContext
from app.services.customer_question_state import CustomerQuestionStateStore
from app.services.query_planner import QueryPlannerService


router = APIRouter(prefix="/api/extn/customer-replies", tags=["extn-customer-replies"])


class DraftReplyRequest(BaseModel):
    question_id: str
    question_text: str
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    context: Dict[str, Any] = Field(default_factory=dict)


class DraftReplyResponse(BaseModel):
    request_id: str
    reply_id: str
    question_id: str
    reply_message: str
    confidence: float
    source: str = "llm_webhook"
    intent: Optional[str] = None
    created_at: str


class PostViaMcpRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str
    reply_message: str
    mode: Literal["dry_run", "post"] = "dry_run"
    thread_id: Optional[str] = None
    post_id: Optional[str] = None
    author: str = "ontology-workflow"
    workflow_run_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PostViaMcpResponse(BaseModel):
    request_id: str
    status: Literal["dry_run", "success", "error"]
    tool: str = "comment.create"
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    audit_id: str
    duration_ms: int
    status_code: Optional[int] = None


class GenerateAndPostRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str
    question_text: str
    mode: Literal["dry_run", "post"] = "dry_run"
    thread_id: Optional[str] = None
    post_id: Optional[str] = None
    author: str = "ontology-workflow"
    workflow_run_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class GenerateAndPostResponse(BaseModel):
    draft: DraftReplyResponse
    mcp: PostViaMcpResponse


@router.post("/draft", response_model=DraftReplyResponse)
async def create_draft_reply(
    request: DraftReplyRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    query_svc: QueryPlannerService = Depends(get_query_planner_service),
):
    """Generate a reply message with the existing v5 LLM/hybrid path."""

    return _generate_draft(request, ctx, query_svc)


@router.post("/post-via-mcp", response_model=PostViaMcpResponse)
async def post_reply_via_mcp(
    request: PostViaMcpRequest,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Send the official comment.create payload to customer_mcp."""

    return await _post_to_customer_mcp(request, ctx)


@router.post("/generate-and-post", response_model=GenerateAndPostResponse)
async def generate_and_post(
    request: GenerateAndPostRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    query_svc: QueryPlannerService = Depends(get_query_planner_service),
):
    """Generate a draft and then call customer_mcp with comment.create."""

    draft = _generate_draft(
        DraftReplyRequest(
            request_id=request.request_id,
            question_id=request.question_id,
            question_text=request.question_text,
            context=request.context,
        ),
        ctx,
        query_svc,
    )
    mcp = await _post_to_customer_mcp(
        PostViaMcpRequest(
            request_id=request.request_id,
            question_id=request.question_id,
            reply_message=draft.reply_message,
            mode=request.mode,
            thread_id=request.thread_id,
            post_id=request.post_id,
            author=request.author,
            workflow_run_id=request.workflow_run_id,
            metadata=request.context,
        ),
        ctx,
    )
    return GenerateAndPostResponse(draft=draft, mcp=mcp)


def _generate_draft(
    request: DraftReplyRequest,
    ctx: TenantContext,
    query_svc: QueryPlannerService,
) -> DraftReplyResponse:
    reply_id = str(uuid.uuid4())

    try:
        response = query_svc.ask_v5(
            request.question_text,
            ctx,
            search_mode=SearchMode.AUTO,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LLM webhook draft failed: {exc}") from exc

    res_dict = response.model_dump(mode="json") if hasattr(response, "model_dump") else response.dict()
    raw_reply_message = (
        res_dict.get("answer")
        or res_dict.get("message")
        or "The system could not generate a grounded reply."
    )
    reply_message = _customer_safe_reply(str(raw_reply_message), request.question_text)

    return DraftReplyResponse(
        request_id=request.request_id,
        reply_id=reply_id,
        question_id=request.question_id,
        reply_message=reply_message,
        confidence=float(res_dict.get("confidence") or res_dict.get("score") or 0.5),
        intent=res_dict.get("intent") or res_dict.get("query_type"),
        created_at=datetime.utcnow().isoformat() + "Z",
    )


def _customer_safe_reply(reply_message: str, question_text: str) -> str:
    """Keep internal ontology/RAG fallback text from leaking to customer comments."""

    message = reply_message.strip()
    if message and not _looks_internal_or_ungrounded(message):
        return message
    return _fallback_customer_reply(question_text)


def _looks_internal_or_ungrounded(message: str) -> bool:
    internal_patterns = [
        r"Found \d+ ontology item",
        r"Citations:\s*ontology:",
        r"document result\(s\)",
        r"provided documents?",
        r"직접적인 근거를 찾지 못했습니다",
        r"could not generate a grounded reply",
    ]
    return any(re.search(pattern, message, flags=re.IGNORECASE) for pattern in internal_patterns)


def _fallback_customer_reply(question_text: str) -> str:
    normalized = question_text.lower()
    if any(keyword in normalized for keyword in ["비밀번호", "password", "로그인", "login", "계정", "account"]):
        return (
            "안녕하세요. 문의 주신 계정/비밀번호 관련 요청을 확인했습니다. "
            "보안을 위해 본인 확인 후 초기화 절차를 진행해야 하며, 담당자가 확인하는 대로 처리 방법과 예상 소요 시간을 안내드리겠습니다."
        )
    if any(keyword in normalized for keyword in ["환불", "결제", "payment", "refund", "청구"]):
        return (
            "안녕하세요. 결제 관련 문의를 확인했습니다. "
            "주문 또는 결제 정보를 확인한 뒤 환불/정정 가능 여부와 다음 절차를 안내드리겠습니다."
        )
    if any(keyword in normalized for keyword in ["배송", "delivery", "주문", "order", "출고"]):
        return (
            "안녕하세요. 주문/배송 관련 문의를 확인했습니다. "
            "현재 처리 상태를 확인한 뒤 예상 일정과 필요한 조치를 안내드리겠습니다."
        )
    return (
        "안녕하세요. 문의 내용을 확인했습니다. "
        "담당자가 내용을 검토한 뒤 처리 방향과 필요한 추가 정보를 안내드리겠습니다."
    )


async def _post_to_customer_mcp(
    request: PostViaMcpRequest,
    ctx: TenantContext,
) -> PostViaMcpResponse:
    start = time.monotonic()
    audit_id = str(uuid.uuid4())
    state_store = CustomerQuestionStateStore(ctx)

    force_reprocess = bool(request.metadata.get("force_reprocess"))
    processed = state_store.successful_question(request.question_id)
    if request.mode == "post" and processed and not force_reprocess:
        return PostViaMcpResponse(
            request_id=request.request_id,
            status="success",
            result={
                "external_comment_id": processed.get("external_comment_id"),
                "external_thread_id": request.thread_id or request.question_id,
                "skipped": True,
                "reason": "question_already_processed",
            },
            error=None,
            audit_id=audit_id,
            duration_ms=int((time.monotonic() - start) * 1000),
            status_code=None,
        )

    mcp_request = CommentCreateRequest(
        request_id=request.request_id,
        company_id=ctx.company_id,
        project_id=ctx.project_id,
        mode=request.mode,
        arguments=CommentCreateArguments(
            question_id=request.question_id,
            thread_id=request.thread_id,
            post_id=request.post_id,
            message=request.reply_message,
            author=request.author,
        ),
        metadata=CommentCreateMetadata(
            workflow_run_id=request.workflow_run_id,
            source=str(request.metadata.get("source", "ont_platform_v5")),
            generated_by=str(request.metadata.get("generated_by", "llm_webhook")),
        ),
    )

    client = CustomerMcpClient()
    response = await client.create_comment(mcp_request)
    duration_ms = response.duration_ms or int((time.monotonic() - start) * 1000)

    api_response = PostViaMcpResponse(
        request_id=response.request_id,
        status=response.status,
        tool=response.tool,
        result=response.result,
        error=response.error,
        audit_id=audit_id,
        duration_ms=duration_ms,
        status_code=response.status_code,
    )
    _write_audit(ctx, mcp_request, api_response)
    if request.mode == "post" and api_response.status == "success":
        result = api_response.result or {}
        state_store.mark_question(
            request.question_id,
            {
                "status": "success",
                "request_id": request.request_id,
                "workflow_run_id": request.workflow_run_id,
                "external_comment_id": result.get("external_comment_id"),
                "external_thread_id": result.get("external_thread_id"),
                "url": result.get("url"),
                "source": request.metadata.get("source", "ont_platform_v5"),
            },
        )
    return api_response


def _write_audit(
    ctx: TenantContext,
    request: CommentCreateRequest,
    response: PostViaMcpResponse,
) -> None:
    audit_dir = Path("storage") / ctx.company_id / ctx.project_id / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_path = audit_dir / "customer_mcp_calls.jsonl"
    record = {
        "audit_id": response.audit_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "company_id": ctx.company_id,
        "project_id": ctx.project_id,
        "user_id": ctx.user_id,
        "request": request.model_dump(mode="json"),
        "response": response.model_dump(mode="json"),
    }
    with audit_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
