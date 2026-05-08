from typing import List

class PolicyService:
    ROLES = {
        "Admin": ["view_all", "execute_all", "audit_view"],
        "FinanceManager": ["view_all", "execute_approve", "execute_reject"],
        "AccountManager": ["view_assigned", "execute_hold"],
        "Viewer": ["view_all"]
    }

    @staticmethod
    def check_permission(role: str, action: str) -> bool:
        permissions = PolicyService.ROLES.get(role, [])
        if "execute_all" in permissions:
            return True
        return action in permissions

    @staticmethod
    def get_masking_required(role: str, field: str) -> bool:
        # Example: Viewer cannot see riskTier
        if role == "Viewer" and field == "riskTier":
            return True
        return False
