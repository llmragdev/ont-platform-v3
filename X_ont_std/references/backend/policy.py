from typing import List

class PolicyService:
    # 역할별 기본 권한 정의
    ROLES = {
        "Admin": {"view": "all", "actions": ["ApproveOrder", "RejectOrder", "HoldOrder", "FulfillOrder", "CloseOrder"]},
        "FinanceManager": {"view": "all", "actions": ["ApproveOrder", "RejectOrder", "HoldOrder", "FulfillOrder", "CloseOrder"]},
        "AccountManager": {"view": "assigned", "actions": ["ApproveOrder", "RejectOrder", "HoldOrder"]},
        "Viewer": {"view": "all", "actions": []},
        "Analyst": {"view": "all", "actions": []}
    }

    @staticmethod
    def can_read_object(user: dict, obj: dict) -> bool:
        role = user.get("role", "Viewer")
        role_cfg = PolicyService.ROLES.get(role, PolicyService.ROLES["Viewer"])
        
        if role_cfg["view"] == "all":
            return True
            
        # assigned 권한의 경우: 사용자의 지역(region)과 객체의 지역이 일치해야 함
        if role_cfg["view"] == "assigned":
            return obj.get("region") in user.get("regions", [])
            
        return False

    @staticmethod
    def mask_object(user: dict, obj: dict) -> dict:
        import copy
        masked = copy.deepcopy(obj)
        role = user.get("role", "Viewer")

        if obj.get("type") == "Customer":
            if role in ["Viewer", "Analyst"]:
                # 민감 정보 마스킹
                if "riskTier" in masked:
                    masked["riskTier"] = "***"
                if "contract_terms" in masked:
                    masked["contract_terms"] = "Restricted"
            elif role == "AccountManager":
                 if "contract_terms" in masked:
                    masked["contract_terms"] = "Custom discount rate: ***"
        
        return masked

    @staticmethod
    def can_execute_action(user: dict, action: str, order: dict, customer: dict = None) -> bool:
        role = user.get("role", "Viewer")
        role_cfg = PolicyService.ROLES.get(role, PolicyService.ROLES["Viewer"])

        # 1. 역할 기반 액션 권한 확인
        if action not in role_cfg["actions"]:
            return False

        # 2. 비즈니스 규칙 확인 (Requirement 08 기반)
        if action == "ApproveOrder":
            # 고위험 고객은 승인 불가 (추가 검토 필요)
            if customer and customer.get("riskTier") == "High":
                return False
            
            # 금액에 따른 승인 권한 차등
            amount = order.get("amount", 0)
            if amount >= 5000:
                return role in ["FinanceManager", "Admin"]
            return role in ["AccountManager", "FinanceManager", "Admin"]

        return True
