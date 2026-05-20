from __future__ import annotations

from copy import deepcopy

from .errors import AppError


class PolicyEngine:
    def __init__(self, audit) -> None:
        self.audit = audit

    def can_read_object(self, user: dict, obj: dict) -> bool:
        if user["role"] in ["Admin", "FinanceManager"]:
            return True
        if obj["type"] == "Customer":
            return obj.get("region") in user["regions"] or obj.get("owner") == user["email"]
        if obj["type"] == "Order":
            return self._region_for_order(obj) in user["regions"]
        if obj["type"] == "Product":
            return True
        return False

    def assert_can_read_object(self, user: dict, obj: dict) -> None:
        if not self.can_read_object(user, obj):
            self.audit.record("ACCESS_DENIED", user, obj.get("type", "Object"), obj.get("id", "-"), {"reason": "object"})
            raise AppError("FORBIDDEN", "이 정보에 접근할 권한이 없습니다.", 403)

    def mask_object(self, user: dict, obj: dict) -> dict:
        masked = deepcopy(obj)
        if obj["type"] == "Customer":
            if user["role"] == "Viewer":
                masked["risk_tier"] = "Restricted"
                masked["contract_terms"] = "Restricted"
            elif user["role"] == "Analyst":
                masked["contract_terms"] = "Custom discount rate: ***"
            elif user["role"] == "AccountManager":
                masked["contract_terms"] = "Custom discount rate: ***"
        return masked

    def can_read_document(self, user: dict, document: dict) -> bool:
        return user["role"] in document["visibility"]

    def available_actions(self, user: dict, order: dict, customer: dict) -> list[str]:
        self.assert_can_read_object(user, order)
        if order["status"] not in ["Submitted", "Review", "Approved", "Fulfilled"]:
            return []
        actions: list[str] = []
        if order["status"] in ["Submitted", "Review"]:
            if self.can_execute_action(user, "ApproveOrder", order, customer):
                actions.append("ApproveOrder")
            if self.can_execute_action(user, "RejectOrder", order, customer):
                actions.append("RejectOrder")
            if self.can_execute_action(user, "HoldOrder", order, customer):
                actions.append("HoldOrder")
        if order["status"] == "Approved" and user["role"] in ["Admin", "FinanceManager"]:
            actions.append("FulfillOrder")
        if order["status"] == "Fulfilled" and user["role"] in ["Admin", "FinanceManager"]:
            actions.append("CloseOrder")
        return actions

    def can_execute_action(self, user: dict, action: str, order: dict, customer: dict) -> bool:
        if user["role"] in ["Admin"]:
            return True
        if action == "ApproveOrder":
            if customer["risk_tier"] == "High":
                return False
            if order["amount"] < 5000:
                return user["role"] in ["AccountManager", "FinanceManager"]
            return user["role"] == "FinanceManager"
        if action in ["RejectOrder", "HoldOrder"]:
            return user["role"] in ["AccountManager", "FinanceManager"]
        return False

    @staticmethod
    def _region_for_order(order: dict) -> str | None:
        order_region = {
            "O001": "Seoul",
            "O002": "Busan",
            "O003": "Incheon",
        }
        return order_region.get(order["id"])

