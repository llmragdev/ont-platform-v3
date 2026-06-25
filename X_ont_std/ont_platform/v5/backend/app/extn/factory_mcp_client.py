"""Factory MCP client for Scenario 2 repeated fault demo."""
from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict, Literal, Optional

import httpx
from pydantic import BaseModel, Field


class FactoryMcpConfig(BaseModel):
    base_url: str = Field(default_factory=lambda: os.getenv("FACTORY_MCP_BASE_URL", "http://localhost:8081"))
    timeout_seconds: float = Field(default_factory=lambda: float(os.getenv("FACTORY_MCP_TIMEOUT_SECONDS", "30")))


class FactoryToolRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    project_id: str
    mode: Literal["dry_run", "post"] = "dry_run"
    tool: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FactoryToolResponse(BaseModel):
    request_id: str
    status: Literal["dry_run", "success", "error"]
    tool: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    duration_ms: int = 0
    status_code: Optional[int] = None


class FactoryMcpClient:
    def __init__(self, config: FactoryMcpConfig | None = None) -> None:
        self.config = config or FactoryMcpConfig()

    async def list_events(self, *, request_id: str, company_id: str, project_id: str, status: str = "open", limit: int = 20) -> FactoryToolResponse:
        return await self.call_tool(
            FactoryToolRequest(
                request_id=request_id,
                company_id=company_id,
                project_id=project_id,
                tool="factory_event.list",
                arguments={"status": status, "limit": limit},
            )
        )

    async def create_response(
        self,
        *,
        request_id: str,
        company_id: str,
        project_id: str,
        mode: Literal["dry_run", "post"],
        event_id: str,
        message: str,
        workflow_run_id: str | None = None,
    ) -> FactoryToolResponse:
        return await self.call_tool(
            FactoryToolRequest(
                request_id=request_id,
                company_id=company_id,
                project_id=project_id,
                mode=mode,
                tool="factory_response.create",
                arguments={"event_id": event_id, "message": message, "author": "ontology-workflow"},
                metadata={"workflow_run_id": workflow_run_id, "source": "ont_platform_v5"},
            )
        )

    async def create_maintenance_task(
        self,
        *,
        request_id: str,
        company_id: str,
        project_id: str,
        mode: Literal["dry_run", "post"],
        event: Dict[str, Any],
        priority: str,
        message: str,
        workflow_run_id: str | None = None,
    ) -> FactoryToolResponse:
        return await self.call_tool(
            FactoryToolRequest(
                request_id=request_id,
                company_id=company_id,
                project_id=project_id,
                mode=mode,
                tool="maintenance_task.create",
                arguments={
                    "factory_event_id": event.get("factory_event_id") or event.get("id"),
                    "equipment_name": event.get("equipment_name"),
                    "fault_message": event.get("fault_message"),
                    "assigned_team": "정비팀",
                    "priority": priority,
                    "message": message,
                },
                metadata={"workflow_run_id": workflow_run_id, "source": "ont_platform_v5"},
            )
        )

    async def call_tool(self, request: FactoryToolRequest) -> FactoryToolResponse:
        start = time.monotonic()
        url = f"{self.config.base_url.rstrip('/')}/mcp/tools/{request.tool}"
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post(url, json=request.model_dump(mode="json"))
            duration_ms = int((time.monotonic() - start) * 1000)
            try:
                data = response.json()
            except ValueError:
                data = {"request_id": request.request_id, "status": "error", "tool": request.tool, "error": {"code": "INVALID_RESPONSE", "message": response.text[:300], "retryable": True}}
            if 200 <= response.status_code < 300:
                return FactoryToolResponse(
                    request_id=data.get("request_id", request.request_id),
                    status=data.get("status", "success"),
                    tool=data.get("tool", request.tool),
                    result=data.get("result"),
                    error=data.get("error"),
                    duration_ms=duration_ms,
                    status_code=response.status_code,
                )
            return FactoryToolResponse(
                request_id=request.request_id,
                status="error",
                tool=request.tool,
                result=None,
                error=data.get("error") or {"code": "FACTORY_MCP_ERROR", "message": response.text[:300], "retryable": response.status_code >= 500},
                duration_ms=duration_ms,
                status_code=response.status_code,
            )
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            return FactoryToolResponse(
                request_id=request.request_id,
                status="error",
                tool=request.tool,
                result=None,
                error={"code": "FACTORY_MCP_ERROR", "message": str(exc), "retryable": True},
                duration_ms=int((time.monotonic() - start) * 1000),
                status_code=None,
            )
