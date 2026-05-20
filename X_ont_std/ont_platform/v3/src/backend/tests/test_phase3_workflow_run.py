"""Phase 3 DoD tests — WorkflowRun model, HMAC auth, metrics."""
from __future__ import annotations

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.models.workflow_run import StepStatus, WorkflowRun, WorkflowStepRun


class TestWorkflowRunModel:
    def test_default_status(self):
        run = WorkflowRun(run_id="r1", graph_id="g1", triggered_by="alice", started_at="2026-05-14T00:00:00Z")
        assert run.status == StepStatus.PENDING

    def test_step_status_enum_values(self):
        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.RUNNING.value == "running"
        assert StepStatus.SUCCEEDED.value == "succeeded"
        assert StepStatus.FAILED.value == "failed"

    def test_step_run_default_io(self):
        step = WorkflowStepRun(step_id="s1", node_id="n1", node_type="action")
        assert step.input == {}
        assert step.output == {}
        assert step.error is None

    def test_run_serialization(self):
        run = WorkflowRun(
            run_id="r1", graph_id="g1", triggered_by="alice", started_at="2026-05-14T00:00:00Z",
            steps=[WorkflowStepRun(step_id="s1", node_id="n1", node_type="start",
                                    status=StepStatus.SUCCEEDED)],
            user_trace=["단계 1 완료"], tech_trace=["node=n1 type=start"],
        )
        data = run.model_dump(mode="json")
        assert data["run_id"] == "r1"
        assert len(data["steps"]) == 1
        assert data["steps"][0]["status"] == "succeeded"


class TestHmacMiddlewareInactive:
    def test_middleware_inactive_without_secret(self):
        import os
        old = os.environ.pop("HMAC_SECRET", None)
        try:
            from app.middleware.auth import HmacAuthMiddleware
            # Creating with no secret should not raise
            class FakeApp:
                pass
            mw = HmacAuthMiddleware(FakeApp(), secret=None)
            assert mw._active is False
        finally:
            if old:
                os.environ["HMAC_SECRET"] = old

    def test_middleware_active_with_secret(self):
        from app.middleware.auth import HmacAuthMiddleware
        class FakeApp:
            pass
        mw = HmacAuthMiddleware(FakeApp(), secret="test-secret-key")
        assert mw._active is True


class TestQueryResponseV3Fields:
    def test_query_response_has_v3_fields(self):
        from app.models.query_intent import QueryResponse, IntentType
        resp = QueryResponse(answer="test", intent=IntentType.DESCRIPTIVE)
        assert resp.ontology_evidence == []
        assert resp.quality_metrics == {}
