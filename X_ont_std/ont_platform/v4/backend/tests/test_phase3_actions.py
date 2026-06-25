"""Phase 3: 비즈니스 액션 단위 테스트"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from app.models.tenant_context import TenantContext
from app.models.action import ActionDefinition, Condition, ConditionOperator
from app.services.ontology import OntologyService
from app.services.workflow import WorkflowService
from storage_config import get_project_root


@pytest.fixture
def tenant_context():
    """테스트용 테넌트 컨텍스트"""
    return TenantContext(
        user_id="user@nipa.go.kr",
        company_id="demo-co",
        project_id="proj-01",
        role="FinanceManager",
        permissions={}
    )


@pytest.fixture
def ontology_service(tenant_context, sample_project):
    """온톨로지 서비스 (mocked)"""
    service = MagicMock(spec=OntologyService)
    service.list_entities = MagicMock(return_value=[sample_project])
    return service


@pytest.fixture
def workflow_service(ontology_service):
    """워크플로우 서비스"""
    return WorkflowService(ontology_service)


@pytest.fixture
def sample_project():
    """테스트용 PROJECT 엔티티"""
    return {
        "id": "P001AAA",
        "type": "PROJECT",
        "name": "AI바우처 2025 - 기업A",
        "properties": {
            "status": "UnderReview",
            "budget": 100000000,  # 1억원
            "manager": "manager@nipa.go.kr",
            "deadline": "2026-12-31",
            "bank_account_verified": True,
            "payment_schedule": "2026-06-01",
            "approved_by": None,
            "approved_at": None,
            "rejected_by": None,
            "rejected_at": None,
            "rejection_reason": None,
        }
    }


class TestApproveProjectAction:
    """ApproveProject 액션 테스트"""

    def test_approve_by_finance_manager_medium_budget(
        self, workflow_service, tenant_context, sample_project
    ):
        """FinanceManager이 1억원 과제 승인 → 성공"""
        # 예산 1억원: FinanceManager 권한 충분
        result = workflow_service.execute(
            ctx=tenant_context,
            doc_id="ai-voucher-2025",
            entity_id=sample_project["id"],
            action_name="approve_project",
            domain_id="ai-voucher-2025",
            params={}
        )

        assert result["action"] == "approve_project"
        assert result["from_status"] == "UnderReview"
        assert result["to_status"] == "Approved"
        assert result["approved_by"] == tenant_context.user_id

    def test_approve_by_admin_large_budget(
        self, workflow_service, sample_project
    ):
        """Admin이 3억원 과제 승인 → 성공"""
        ctx = TenantContext(
            user_id="admin@nipa.go.kr",
            company_id="demo-co",
            project_id="proj-01",
            role="Admin",
            permissions={}
        )
        sample_project["properties"]["budget"] = 300000000

        result = workflow_service.execute(
            ctx=ctx,
            doc_id="ai-voucher-2025",
            entity_id=sample_project["id"],
            action_name="approve_project",
            domain_id="ai-voucher-2025"
        )

        assert result["to_status"] == "Approved"

    def test_approve_by_teamlead_small_budget(
        self, workflow_service, sample_project
    ):
        """TeamLead이 3천만원 과제 승인 → 성공"""
        ctx = TenantContext(
            user_id="lead@nipa.go.kr",
            company_id="demo-co",
            project_id="proj-01",
            role="TeamLead",
            permissions={}
        )
        sample_project["properties"]["budget"] = 30000000

        result = workflow_service.execute(
            ctx=ctx,
            doc_id="ai-voucher-2025",
            entity_id=sample_project["id"],
            action_name="approve_project",
            domain_id="ai-voucher-2025"
        )

        assert result["to_status"] == "Approved"

    def test_approve_by_teamlead_large_budget_fails(
        self, workflow_service, sample_project
    ):
        """TeamLead이 6천만원 과제 승인 시도 → 실패 (권한 부족)"""
        ctx = TenantContext(
            user_id="lead@nipa.go.kr",
            company_id="demo-co",
            project_id="proj-01",
            role="TeamLead",
            permissions={}
        )
        sample_project["properties"]["budget"] = 60000000

        with pytest.raises(PermissionError, match="권한이 없습니다"):
            workflow_service.execute(
                ctx=ctx,
                doc_id="ai-voucher-2025",
                entity_id=sample_project["id"],
                action_name="approve_project",
                domain_id="ai-voucher-2025"
            )

    def test_approve_precondition_failed_no_manager(
        self, workflow_service, tenant_context, sample_project
    ):
        """담당자 미배정 상태에서 승인 시도 → 실패"""
        sample_project["properties"]["manager"] = None

        with pytest.raises(ValueError, match="담당자"):
            workflow_service.execute(
                ctx=tenant_context,
                doc_id="ai-voucher-2025",
                entity_id=sample_project["id"],
                action_name="approve_project",
                domain_id="ai-voucher-2025"
            )

    def test_approve_precondition_failed_low_budget(
        self, workflow_service, tenant_context, sample_project
    ):
        """예산 500만원 과제 승인 시도 → 실패 (최소 예산 미만)"""
        sample_project["properties"]["budget"] = 5000000

        with pytest.raises(ValueError, match="최소 예산"):
            workflow_service.execute(
                ctx=tenant_context,
                doc_id="ai-voucher-2025",
                entity_id=sample_project["id"],
                action_name="approve_project",
                domain_id="ai-voucher-2025"
            )

    def test_approve_wrong_status(
        self, workflow_service, tenant_context, sample_project
    ):
        """Submitted 상태에서 승인 시도 → 실패 (상태 불일치)"""
        sample_project["properties"]["status"] = "Submitted"

        with pytest.raises(ValueError, match="현재 상태"):
            workflow_service.execute(
                ctx=tenant_context,
                doc_id="ai-voucher-2025",
                entity_id=sample_project["id"],
                action_name="approve_project",
                domain_id="ai-voucher-2025"
            )


class TestRejectProjectAction:
    """RejectProject 액션 테스트"""

    def test_reject_with_reason(
        self, workflow_service, tenant_context, sample_project
    ):
        """반려 사유와 함께 반려 → 성공"""
        result = workflow_service.execute(
            ctx=tenant_context,
            doc_id="ai-voucher-2025",
            entity_id=sample_project["id"],
            action_name="reject_project",
            domain_id="ai-voucher-2025",
            params={"rejection_reason": "요건 미충족"}
        )

        assert result["to_status"] == "Rejected"

    def test_reject_without_reason(
        self, workflow_service, tenant_context, sample_project
    ):
        """반려 사유 없이 반려 시도 → 실패"""
        with pytest.raises(ValueError, match="rejection_reason"):
            workflow_service.execute(
                ctx=tenant_context,
                doc_id="ai-voucher-2025",
                entity_id=sample_project["id"],
                action_name="reject_project",
                domain_id="ai-voucher-2025",
                params={}
            )

    def test_reject_from_submitted(
        self, workflow_service, tenant_context, sample_project
    ):
        """Submitted 상태에서 반려 → 성공"""
        sample_project["properties"]["status"] = "Submitted"

        result = workflow_service.execute(
            ctx=tenant_context,
            doc_id="ai-voucher-2025",
            entity_id=sample_project["id"],
            action_name="reject_project",
            domain_id="ai-voucher-2025",
            params={"rejection_reason": "조기 검토"}
        )

        assert result["to_status"] == "Rejected"


class TestChangeDeadlineAction:
    """ChangeDeadline 액션 테스트"""

    def test_change_deadline_success(
        self, workflow_service, tenant_context, sample_project
    ):
        """일정 변경 → 성공"""
        sample_project["properties"]["status"] = "Approved"

        result = workflow_service.execute(
            ctx=tenant_context,
            doc_id="ai-voucher-2025",
            entity_id=sample_project["id"],
            action_name="change_deadline",
            domain_id="ai-voucher-2025",
            params={"new_deadline": "2026-12-31"}
        )

        assert result["action"] == "change_deadline"
        assert sample_project["properties"]["deadline"] == "2026-12-31"

    def test_change_deadline_no_state_change(
        self, workflow_service, tenant_context, sample_project
    ):
        """일정 변경은 상태 유지 (UnderReview → UnderReview)"""
        sample_project["properties"]["status"] = "UnderReview"

        result = workflow_service.execute(
            ctx=tenant_context,
            doc_id="ai-voucher-2025",
            entity_id=sample_project["id"],
            action_name="request_more_info",
            domain_id="ai-voucher-2025",
            params={"info_needed": "더 상세한 설명"}
        )

        # 상태 유지 확인
        assert result["from_status"] == "UnderReview"
        assert result["to_status"] == "UnderReview"


class TestConditionEvaluation:
    """조건 평가 테스트"""

    def test_condition_not_null(self, workflow_service):
        """not_null 연산자"""
        entity = {"properties": {"manager": "manager@nipa.go.kr"}}
        result = workflow_service._evaluate_condition(
            entity["properties"]["manager"],
            "not_null",
            None
        )
        assert result is True

        result = workflow_service._evaluate_condition(None, "not_null", None)
        assert result is False

    def test_condition_equals(self, workflow_service):
        """equals 연산자"""
        entity = {"properties": {"status": "UnderReview"}}
        result = workflow_service._evaluate_condition(
            entity["properties"]["status"],
            "equals",
            "UnderReview"
        )
        assert result is True

        result = workflow_service._evaluate_condition(
            entity["properties"]["status"],
            "equals",
            "Approved"
        )
        assert result is False

    def test_condition_gte(self, workflow_service):
        """gte (>=) 연산자"""
        result = workflow_service._evaluate_condition(100000000, "gte", 10000000)
        assert result is True

        result = workflow_service._evaluate_condition(5000000, "gte", 10000000)
        assert result is False

    def test_condition_lte(self, workflow_service):
        """lte (<=) 연산자"""
        result = workflow_service._evaluate_condition(50000000, "lte", 50000000)
        assert result is True

        result = workflow_service._evaluate_condition(60000000, "lte", 50000000)
        assert result is False

    def test_condition_gt(self, workflow_service):
        """gt (>) 연산자"""
        result = workflow_service._evaluate_condition(200000001, "gt", 200000000)
        assert result is True

        result = workflow_service._evaluate_condition(200000000, "gt", 200000000)
        assert result is False


class TestConditionalPermission:
    """조건부 권한 테스트"""

    def test_conditional_permission_small_budget_teamlead(
        self, workflow_service, sample_project
    ):
        """예산 5천만원 이하: TeamLead 권한 있음"""
        sample_project["properties"]["budget"] = 50000000
        ctx = TenantContext(
            user_id="lead@nipa.go.kr",
            company_id="demo-co",
            project_id="proj-01",
            role="TeamLead",
            permissions={}
        )

        can_approve = workflow_service.available_actions(
            role=ctx.role,
            current_status="UnderReview",
            entity=sample_project,
            domain_id="ai-voucher-2025"
        )

        assert "approve_project" in can_approve

    def test_conditional_permission_large_budget_teamlead(
        self, workflow_service, sample_project
    ):
        """예산 6천만원: TeamLead 권한 없음"""
        sample_project["properties"]["budget"] = 60000000
        ctx = TenantContext(
            user_id="lead@nipa.go.kr",
            company_id="demo-co",
            project_id="proj-01",
            role="TeamLead",
            permissions={}
        )

        can_approve = workflow_service.available_actions(
            role=ctx.role,
            current_status="UnderReview",
            entity=sample_project,
            domain_id="ai-voucher-2025"
        )

        assert "approve_project" not in can_approve


class TestActionModel:
    """ActionDefinition 모델 테스트"""

    def test_action_definition_from_dict(self):
        """workflow.json 딕셔너리에서 ActionDefinition 생성"""
        action_dict = {
            "id": "approve_project",
            "display_name": "과제 승인",
            "entity_type": "PROJECT",
            "from_statuses": ["UnderReview"],
            "to_status": "Approved",
            "preconditions": [
                {
                    "field": "properties.budget",
                    "operator": "gte",
                    "value": 10000000
                }
            ],
            "allowed_roles": ["Admin", "FinanceManager"]
        }

        action = ActionDefinition(**action_dict)

        assert action.id == "approve_project"
        assert action.display_name == "과제 승인"
        assert len(action.preconditions) == 1
        assert action.preconditions[0].field == "properties.budget"

    def test_action_definition_has_preconditions(self):
        """전제 조건 확인"""
        action_dict = {
            "id": "approve_project",
            "display_name": "과제 승인",
            "entity_type": "PROJECT",
            "from_statuses": ["UnderReview"],
            "to_status": "Approved",
            "preconditions": [{"field": "properties.manager", "operator": "not_null"}],
            "allowed_roles": ["Admin"]
        }

        action = ActionDefinition(**action_dict)
        assert action.has_preconditions() is True

    def test_action_definition_requires_approval(self):
        """승인 필요 여부 확인"""
        action_dict = {
            "id": "approve_project",
            "display_name": "과제 승인",
            "entity_type": "PROJECT",
            "from_statuses": ["UnderReview"],
            "to_status": "Approved",
            "allowed_roles": ["Admin"]
        }

        action = ActionDefinition(**action_dict)
        assert action.requires_approval() is True


class TestStartPaymentAction:
    """StartPayment 액션 테스트"""

    def test_start_payment_success(
        self, workflow_service, tenant_context, sample_project
    ):
        """지급 시작 → 성공"""
        sample_project["properties"]["status"] = "Approved"
        sample_project["properties"]["payment_schedule"] = "2026-06-01"
        sample_project["properties"]["bank_account_verified"] = True

        result = workflow_service.execute(
            ctx=tenant_context,
            doc_id="ai-voucher-2025",
            entity_id=sample_project["id"],
            action_name="start_payment",
            domain_id="ai-voucher-2025"
        )

        assert result["action"] == "start_payment"
        assert result["from_status"] == "Approved"
        assert result["to_status"] == "InProgress"

    def test_start_payment_no_schedule(
        self, workflow_service, tenant_context, sample_project
    ):
        """지급 일정 미설정 상태에서 지급 시작 시도 → 실패"""
        sample_project["properties"]["status"] = "Approved"
        sample_project["properties"]["payment_schedule"] = None

        with pytest.raises(ValueError, match="지급 일정"):
            workflow_service.execute(
                ctx=tenant_context,
                doc_id="ai-voucher-2025",
                entity_id=sample_project["id"],
                action_name="start_payment",
                domain_id="ai-voucher-2025"
            )

    def test_start_payment_unverified_account(
        self, workflow_service, tenant_context, sample_project
    ):
        """계좌 미검증 상태에서 지급 시작 시도 → 실패"""
        sample_project["properties"]["status"] = "Approved"
        sample_project["properties"]["payment_schedule"] = "2026-06-01"
        sample_project["properties"]["bank_account_verified"] = False

        with pytest.raises(ValueError, match="계좌"):
            workflow_service.execute(
                ctx=tenant_context,
                doc_id="ai-voucher-2025",
                entity_id=sample_project["id"],
                action_name="start_payment",
                domain_id="ai-voucher-2025"
            )

    def test_start_payment_wrong_status(
        self, workflow_service, tenant_context, sample_project
    ):
        """UnderReview 상태에서 지급 시작 시도 → 실패"""
        sample_project["properties"]["status"] = "UnderReview"

        with pytest.raises(ValueError, match="현재 상태"):
            workflow_service.execute(
                ctx=tenant_context,
                doc_id="ai-voucher-2025",
                entity_id=sample_project["id"],
                action_name="start_payment",
                domain_id="ai-voucher-2025"
            )


class TestCompleteProjectAction:
    """CompleteProject 액션 테스트"""

    def test_complete_project_success(
        self, workflow_service, tenant_context, sample_project
    ):
        """과제 완료 → 성공"""
        sample_project["properties"]["status"] = "InProgress"
        sample_project["properties"]["payment_completed"] = True
        sample_project["properties"]["final_report_submitted"] = True

        result = workflow_service.execute(
            ctx=tenant_context,
            doc_id="ai-voucher-2025",
            entity_id=sample_project["id"],
            action_name="complete_project",
            domain_id="ai-voucher-2025"
        )

        assert result["action"] == "complete_project"
        assert result["from_status"] == "InProgress"
        assert result["to_status"] == "Completed"

    def test_complete_project_payment_not_completed(
        self, workflow_service, tenant_context, sample_project
    ):
        """지급 미완료 상태에서 완료 시도 → 실패"""
        sample_project["properties"]["status"] = "InProgress"
        sample_project["properties"]["payment_completed"] = False
        sample_project["properties"]["final_report_submitted"] = True

        with pytest.raises(ValueError, match="지급"):
            workflow_service.execute(
                ctx=tenant_context,
                doc_id="ai-voucher-2025",
                entity_id=sample_project["id"],
                action_name="complete_project",
                domain_id="ai-voucher-2025"
            )

    def test_complete_project_no_final_report(
        self, workflow_service, tenant_context, sample_project
    ):
        """최종 보고서 미제출 상태에서 완료 시도 → 실패"""
        sample_project["properties"]["status"] = "InProgress"
        sample_project["properties"]["payment_completed"] = True
        sample_project["properties"]["final_report_submitted"] = False

        with pytest.raises(ValueError, match="보고서"):
            workflow_service.execute(
                ctx=tenant_context,
                doc_id="ai-voucher-2025",
                entity_id=sample_project["id"],
                action_name="complete_project",
                domain_id="ai-voucher-2025"
            )

    def test_complete_project_wrong_status(
        self, workflow_service, tenant_context, sample_project
    ):
        """Approved 상태에서 완료 시도 → 실패"""
        sample_project["properties"]["status"] = "Approved"

        with pytest.raises(ValueError, match="현재 상태"):
            workflow_service.execute(
                ctx=tenant_context,
                doc_id="ai-voucher-2025",
                entity_id=sample_project["id"],
                action_name="complete_project",
                domain_id="ai-voucher-2025"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
