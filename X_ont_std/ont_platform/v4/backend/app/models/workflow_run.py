"""v3.0 WorkflowRun models — execution history with step-level tracking."""
from __future__ import annotations

from enum import Enum
from pydantic import BaseModel


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"


class WorkflowStepRun(BaseModel):
    step_id: str
    node_id: str
    node_type: str
    status: StepStatus = StepStatus.PENDING
    started_at: str | None = None
    finished_at: str | None = None
    input: dict = {}
    output: dict = {}
    error: str | None = None


class WorkflowRun(BaseModel):
    run_id: str
    graph_id: str
    status: StepStatus = StepStatus.PENDING
    triggered_by: str
    started_at: str
    finished_at: str | None = None
    steps: list[WorkflowStepRun] = []
    user_trace: list[str] = []
    tech_trace: list[str] = []
