"""권한 검증 시스템 Unit 테스트"""
import pytest
from app.services.permission_checker import PermissionChecker


@pytest.fixture
def checker():
    """PermissionChecker 인스턴스"""
    return PermissionChecker()


class TestApproveProjectPermission:
    """ApproveProject 권한 테스트"""

    def test_pm_can_approve(self, checker):
        """PM은 승인 가능"""
        allowed, reason = checker.check_action("PM", "approve_project")
        assert allowed
        assert reason == "OK"

    def test_cfo_can_approve(self, checker):
        """CFO는 승인 가능"""
        allowed, reason = checker.check_action("CFO", "approve_project")
        assert allowed

    def test_ceo_can_approve(self, checker):
        """CEO는 승인 가능"""
        allowed, reason = checker.check_action("CEO", "approve_project")
        assert allowed

    def test_user_cannot_approve(self, checker):
        """일반 사용자는 승인 불가"""
        allowed, reason = checker.check_action("USER", "approve_project")
        assert not allowed
        assert "not allowed" in reason.lower()


class TestRejectProjectPermission:
    """RejectProject 권한 테스트"""

    def test_pm_can_reject(self, checker):
        """PM은 거절 가능"""
        allowed, reason = checker.check_action("PM", "reject_project")
        assert allowed

    def test_accountant_cannot_reject(self, checker):
        """회계담당자는 거절 불가"""
        allowed, reason = checker.check_action("ACCOUNTANT", "reject_project")
        assert not allowed


class TestChangeDeadlinePermission:
    """ChangeDeadline 권한 테스트"""

    def test_pm_can_change_deadline(self, checker):
        """PM은 기한 변경 가능"""
        allowed, reason = checker.check_action("PM", "change_deadline")
        assert allowed

    def test_ceo_can_change_deadline(self, checker):
        """CEO는 기한 변경 가능"""
        allowed, reason = checker.check_action("CEO", "change_deadline")
        assert allowed

    def test_cfo_cannot_change_deadline(self, checker):
        """CFO는 기한 변경 불가"""
        allowed, reason = checker.check_action("CFO", "change_deadline")
        assert not allowed


class TestStartPaymentPermission:
    """StartPayment 권한 테스트"""

    def test_accountant_can_start_small_payment(self, checker):
        """회계담당자는 100만원 이하 결제 시작 가능"""
        allowed, reason = checker.check_action(
            "ACCOUNTANT",
            "start_payment",
            {"amount": 500000}
        )
        assert allowed

    def test_accountant_cannot_start_1m_payment(self, checker):
        """회계담당자는 100만원 이상 결제 불가"""
        allowed, reason = checker.check_action(
            "ACCOUNTANT",
            "start_payment",
            {"amount": 1000000}
        )
        assert not allowed
        assert "CFO" in reason

    def test_cfo_can_start_1m_payment(self, checker):
        """CFO는 100만원 이상 결제 시작 가능"""
        allowed, reason = checker.check_action(
            "CFO",
            "start_payment",
            {"amount": 5000000}
        )
        assert allowed

    def test_cfo_cannot_start_10m_payment(self, checker):
        """CFO는 1000만원 이상 결제 불가"""
        allowed, reason = checker.check_action(
            "CFO",
            "start_payment",
            {"amount": 10000000}
        )
        assert not allowed
        assert "CEO" in reason

    def test_ceo_can_start_unlimited_payment(self, checker):
        """CEO는 무제한 결제 시작 가능"""
        allowed, reason = checker.check_action(
            "CEO",
            "start_payment",
            {"amount": 100000000}
        )
        assert allowed

    def test_start_payment_no_context(self, checker):
        """컨텍스트 없이 권한 확인"""
        allowed, reason = checker.check_action("ACCOUNTANT", "start_payment")
        assert allowed

    def test_start_payment_zero_amount(self, checker):
        """0원은 모두 가능"""
        allowed, reason = checker.check_action(
            "USER",
            "start_payment",
            {"amount": 0}
        )
        # USER는 어차피 권한 없음
        assert not allowed


class TestUnknownAction:
    """존재하지 않는 액션 테스트"""

    def test_unknown_action(self, checker):
        """존재하지 않는 액션"""
        allowed, reason = checker.check_action("PM", "unknown_action")
        assert not allowed
        assert "Unknown action" in reason


class TestGetAllowedActions:
    """사용자 역할별 허용 액션 테스트"""

    def test_pm_allowed_actions(self, checker):
        """PM의 허용 액션"""
        actions = checker.get_allowed_actions("PM")

        assert "approve_project" in actions
        assert "reject_project" in actions
        assert "change_deadline" in actions
        assert "request_more_info" in actions
        assert "complete_project" in actions
        assert "start_payment" not in actions

    def test_cfo_allowed_actions(self, checker):
        """CFO의 허용 액션"""
        actions = checker.get_allowed_actions("CFO")

        assert "approve_project" in actions
        assert "reject_project" in actions
        assert "start_payment" in actions
        assert "change_deadline" not in actions

    def test_ceo_allowed_actions(self, checker):
        """CEO의 허용 액션"""
        actions = checker.get_allowed_actions("CEO")

        # CEO는 모든 액션 가능
        assert len(actions) == 6

    def test_user_allowed_actions(self, checker):
        """일반 사용자의 허용 액션"""
        actions = checker.get_allowed_actions("USER")

        # USER는 아무 액션도 불가
        assert len(actions) == 0

    def test_accountant_allowed_actions(self, checker):
        """회계담당자의 허용 액션"""
        actions = checker.get_allowed_actions("ACCOUNTANT")

        assert "start_payment" in actions
        assert len(actions) == 1


class TestMultipleAmountThresholds:
    """여러 금액 구간 테스트"""

    def test_500k_payment_permission(self, checker):
        """50만원"""
        allowed, _ = checker.check_action(
            "ACCOUNTANT",
            "start_payment",
            {"amount": 500000}
        )
        assert allowed

    def test_999k_payment_permission(self, checker):
        """99만9천원"""
        allowed, _ = checker.check_action(
            "ACCOUNTANT",
            "start_payment",
            {"amount": 999000}
        )
        assert allowed

    def test_1m_boundary_payment_permission(self, checker):
        """정확히 100만원"""
        allowed, _ = checker.check_action(
            "ACCOUNTANT",
            "start_payment",
            {"amount": 1000000}
        )
        assert not allowed

    def test_9999k_cfo_permission(self, checker):
        """999만9천원 (CFO)"""
        allowed, _ = checker.check_action(
            "CFO",
            "start_payment",
            {"amount": 9999000}
        )
        assert allowed

    def test_10m_boundary_cfo_permission(self, checker):
        """정확히 1000만원 (CFO)"""
        allowed, _ = checker.check_action(
            "CFO",
            "start_payment",
            {"amount": 10000000}
        )
        assert not allowed

    def test_10m_boundary_ceo_permission(self, checker):
        """정확히 1000만원 (CEO)"""
        allowed, _ = checker.check_action(
            "CEO",
            "start_payment",
            {"amount": 10000000}
        )
        assert allowed
