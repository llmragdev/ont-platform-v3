"""Customer MCP client for Scenario v1 / Scenario 1.

Official contract:
ont_platform/v5/scenarios/v1/scenario1/CUSTOMER_MCP_CALL_SPEC.md
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict, Literal, Optional

import httpx
from pydantic import BaseModel, Field


MCP_COMMENT_CREATE_PATH = "/mcp/tools/comment.create"
MCP_QUESTION_LIST_PATH = "/mcp/tools/question.list"


class CustomerMcpConfig(BaseModel):
    """Connection settings for the customer-owned MCP relay server."""

    base_url: str = Field(
        default_factory=lambda: os.getenv("CUSTOMER_MCP_BASE_URL", "http://localhost:8080")
    )
    timeout_seconds: float = Field(
        default_factory=lambda: float(os.getenv("CUSTOMER_MCP_TIMEOUT_SECONDS", "30"))
    )
    retry_count: int = Field(
        default_factory=lambda: int(os.getenv("CUSTOMER_MCP_RETRY_COUNT", "1"))
    )
    bearer_token: Optional[str] = Field(
        default_factory=lambda: os.getenv("CUSTOMER_MCP_BEARER_TOKEN") or None
    )


class CommentCreateArguments(BaseModel):
    """Arguments for the P0 comment.create tool."""

    question_id: str
    thread_id: Optional[str] = None
    post_id: Optional[str] = None
    message: str
    author: str = "ontology-workflow"


class CommentCreateMetadata(BaseModel):
    """Optional trace metadata passed through to customer_mcp."""

    workflow_run_id: Optional[str] = None
    source: str = "ont_platform_v5"
    generated_by: str = "llm_webhook"


class CommentCreateRequest(BaseModel):
    """Official request payload for POST /mcp/tools/comment.create."""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    project_id: str
    mode: Literal["dry_run", "post"] = "dry_run"
    tool: Literal["comment.create"] = "comment.create"
    arguments: CommentCreateArguments
    metadata: CommentCreateMetadata = Field(default_factory=CommentCreateMetadata)


class CustomerMcpError(BaseModel):
    code: str
    message: str
    retryable: bool = False


class CommentCreateResult(BaseModel):
    external_comment_id: Optional[str] = None
    external_thread_id: Optional[str] = None
    message: Optional[str] = None
    url: Optional[str] = None


class CommentCreateResponse(BaseModel):
    """Official response shape returned to v5 callers."""

    request_id: str
    status: Literal["dry_run", "success", "error"]
    tool: str = "comment.create"
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    duration_ms: int = 0
    status_code: Optional[int] = None


class CustomerMcpClient:
    """HTTP client for the customer-owned MCP relay server.

    v5 only calls customer_mcp. It must not call customer_board directly.
    """

    def __init__(self, config: Optional[CustomerMcpConfig] = None):
        self.config = config or CustomerMcpConfig()

    def health(self) -> Dict[str, Any]:
        url = self._url("/health")
        with httpx.Client(timeout=self.config.timeout_seconds) as client:
            response = client.get(url, headers=self._headers())
            response.raise_for_status()
            return response.json()

    async def create_comment(self, request: CommentCreateRequest) -> CommentCreateResponse:
        """Call POST /mcp/tools/comment.create with the official payload."""

        payload = request.model_dump(mode="json")
        url = self._url(MCP_COMMENT_CREATE_PATH)
        start = time.monotonic()
        last_error: Optional[CommentCreateResponse] = None

        for attempt in range(self.config.retry_count + 1):
            try:
                async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                    response = await client.post(url, json=payload, headers=self._headers())

                duration_ms = int((time.monotonic() - start) * 1000)

                if 200 <= response.status_code < 300:
                    return self._parse_success_response(
                        request_id=request.request_id,
                        response=response,
                        duration_ms=duration_ms,
                    )

                last_error = self._http_error_response(
                    request_id=request.request_id,
                    status_code=response.status_code,
                    text=response.text,
                    duration_ms=duration_ms,
                )
            except httpx.TimeoutException as exc:
                last_error = self._exception_response(
                    request_id=request.request_id,
                    code="BOARD_TIMEOUT",
                    message=str(exc) or "customer_mcp timeout",
                    retryable=True,
                    start=start,
                )
            except httpx.RequestError as exc:
                last_error = self._exception_response(
                    request_id=request.request_id,
                    code="BOARD_API_ERROR",
                    message=str(exc),
                    retryable=True,
                    start=start,
                )

            if attempt < self.config.retry_count and last_error and last_error.error:
                if last_error.error.get("retryable"):
                    continue
                break

        return last_error or self._exception_response(
            request_id=request.request_id,
            code="INTERNAL_ERROR",
            message="customer_mcp call failed",
            retryable=True,
            start=start,
        )

    async def list_questions(self, status: str = "open") -> Dict[str, Any]:
        """Call GET /mcp/tools/question.list for batch reconciliation."""

        url = self._url(MCP_QUESTION_LIST_PATH)
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(url, params={"status": status}, headers=self._headers())
            if 200 <= response.status_code < 300:
                return response.json()
            return {
                "status": "error",
                "tool": "question.list",
                "result": None,
                "error": {
                    "code": "BOARD_API_ERROR" if response.status_code >= 500 else "INVALID_REQUEST",
                    "message": f"customer_mcp HTTP {response.status_code}: {response.text[:300]}",
                    "retryable": response.status_code >= 500 or response.status_code in (408, 429),
                },
            }
        except httpx.TimeoutException as exc:
            return {
                "status": "error",
                "tool": "question.list",
                "result": None,
                "error": {"code": "BOARD_TIMEOUT", "message": str(exc), "retryable": True},
            }
        except httpx.RequestError as exc:
            return {
                "status": "error",
                "tool": "question.list",
                "result": None,
                "error": {"code": "BOARD_API_ERROR", "message": str(exc), "retryable": True},
            }

    def _url(self, path: str) -> str:
        return f"{self.config.base_url.rstrip('/')}{path}"

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.bearer_token:
            headers["Authorization"] = f"Bearer {self.config.bearer_token}"
        return headers

    def _parse_success_response(
        self,
        *,
        request_id: str,
        response: httpx.Response,
        duration_ms: int,
    ) -> CommentCreateResponse:
        try:
            data = response.json()
        except ValueError:
            return CommentCreateResponse(
                request_id=request_id,
                status="error",
                result=None,
                error={
                    "code": "INVALID_RESPONSE",
                    "message": "customer_mcp returned non-JSON response",
                    "retryable": True,
                },
                duration_ms=duration_ms,
                status_code=response.status_code,
            )

        return CommentCreateResponse(
            request_id=data.get("request_id", request_id),
            status=data.get("status", "success"),
            tool=data.get("tool", "comment.create"),
            result=data.get("result"),
            error=data.get("error"),
            duration_ms=duration_ms,
            status_code=response.status_code,
        )

    def _http_error_response(
        self,
        *,
        request_id: str,
        status_code: int,
        text: str,
        duration_ms: int,
    ) -> CommentCreateResponse:
        retryable = status_code >= 500 or status_code in (408, 429)
        return CommentCreateResponse(
            request_id=request_id,
            status="error",
            result=None,
            error={
                "code": "BOARD_API_ERROR" if retryable else "INVALID_REQUEST",
                "message": f"customer_mcp HTTP {status_code}: {text[:300]}",
                "retryable": retryable,
            },
            duration_ms=duration_ms,
            status_code=status_code,
        )

    def _exception_response(
        self,
        *,
        request_id: str,
        code: str,
        message: str,
        retryable: bool,
        start: float,
    ) -> CommentCreateResponse:
        return CommentCreateResponse(
            request_id=request_id,
            status="error",
            result=None,
            error={"code": code, "message": message, "retryable": retryable},
            duration_ms=int((time.monotonic() - start) * 1000),
            status_code=None,
        )
