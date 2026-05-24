"""권한 검증 시스템"""
from typing import Tuple, Dict, Any


class PermissionChecker:
    """액션 실행 권한 확인"""

    # 액션별 권한 규칙
    PERMISSION_RULES = {
        "approve_project": {
            "allowed_roles": ["PM", "CFO", "CEO"],
        },
        "reject_project": {
            "allowed_roles": ["PM", "CFO", "CEO"],
        },
        "change_deadline": {
            "allowed_roles": ["PM", "CEO"],
        },
        "request_more_info": {
            "allowed_roles": ["PM", "CFO", "CEO"],
        },
        "start_payment": {
            "allowed_roles": ["ACCOUNTANT", "CFO", "CEO"],
            # 금액 기반 추가 규칙은 action_executor에서 처리
        },
        "complete_project": {
            "allowed_roles": ["PM", "CEO"],
        },
    }

    def check_action(
        self,
        user_role: str,
        action_id: str,
        context: Dict[str, Any] = None
    ) -> Tuple[bool, str]:
        """
        액션 실행 권한 확인

        Args:
            user_role: 사용자 역할 (e.g., "CEO", "CFO", "PM")
            action_id: 액션 ID (e.g., "approve_project")
            context: 추가 컨텍스트 (e.g., {"amount": 1500000})

        Returns:
            (허용 여부, 사유 메시지)
        """

        # 1. 액션 존재 여부 확인
        if action_id not in self.PERMISSION_RULES:
            return False, f"Unknown action: {action_id}"

        rules = self.PERMISSION_RULES[action_id]

        # 2. 기본 역할 확인
        allowed_roles = rules.get("allowed_roles", [])
        if user_role not in allowed_roles:
            return False, f"User role '{user_role}' not allowed. Required: {', '.join(allowed_roles)}"

        # 3. 금액 기반 권한 (start_payment의 경우)
        if action_id == "start_payment" and context:
            amount = context.get("amount", 0)

            if amount >= 10000000 and user_role != "CEO":
                return False, "CEO approval required for amounts >= 10,000,000"
            elif amount >= 1000000 and user_role not in ["CFO", "CEO"]:
                return False, "CFO approval required for amounts >= 1,000,000"

        return True, "OK"

    def get_allowed_actions(self, user_role: str) -> Dict[str, str]:
        """사용자 역할에 따른 허용 액션 목록"""
        allowed_actions = {}

        for action_id, rules in self.PERMISSION_RULES.items():
            allowed_roles = rules.get("allowed_roles", [])
            if user_role in allowed_roles:
                allowed_actions[action_id] = self._get_action_display_name(action_id)

        return allowed_actions

    @staticmethod
    def _get_action_display_name(action_id: str) -> str:
        """액션 ID에서 표시 이름 생성"""
        action_names = {
            "approve_project": "프로젝트 승인",
            "reject_project": "프로젝트 거절",
            "change_deadline": "기한 변경",
            "request_more_info": "추가 정보 요청",
            "start_payment": "결제 시작",
            "complete_project": "프로젝트 완료",
        }
        return action_names.get(action_id, action_id)
