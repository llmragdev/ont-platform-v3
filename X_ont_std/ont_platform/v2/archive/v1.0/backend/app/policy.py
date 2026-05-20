from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path

from .errors import AppError


def _default_policy_path() -> Path:
    return Path(__file__).resolve().parent / "config" / "policy.default.json"


def load_masking_policy(path: Path | str | None = None) -> dict:
    policy_path = Path(path) if path else Path(
        os.environ.get("POLICY_MASKING_PATH", _default_policy_path())
    )
    if not policy_path.exists():
        return {"masking_rules": []}
    return json.loads(policy_path.read_text(encoding="utf-8"))


ORDER_REGION_MAP = {
    "O001": "Seoul",
    "O002": "Busan",
    "O003": "Incheon",
}


class PolicyEngine:
    def __init__(self, audit, schema: dict | None = None) -> None:
        self.audit = audit
        self._ontology_schema = schema or {}
        self._masking_policy = load_masking_policy()
        # object_type → set of sensitive field names
        self._sensitive_fields: dict[str, set[str]] = {}
        for type_def in self._ontology_schema.get("object_types", []):
            sensitive = {p["name"] for p in type_def.get("properties", []) if p.get("sensitive")}
            if sensitive:
                self._sensitive_fields[type_def["name"]] = sensitive

    def can_read_object(self, user: dict, obj: dict) -> bool:
        if user["role"] in ["Admin", "FinanceManager"]:
            return True
        if obj["type"] == "Customer":
            return obj.get("region") in user["regions"] or obj.get("owner") == user["email"]
        if obj["type"] == "Order":
            return ORDER_REGION_MAP.get(obj["id"]) in user["regions"]
        if obj["type"] == "Product":
            return True
        return False

    def assert_can_read_object(self, user: dict, obj: dict) -> None:
        if not self.can_read_object(user, obj):
            self.audit.record(
                "ACCESS_DENIED", user, obj.get("type", "Object"), obj.get("id", "-"), {"reason": "object"}
            )
            raise AppError("FORBIDDEN", "이 정보에 접근할 권한이 없습니다.", 403)

    def mask_object(self, user: dict, obj: dict) -> dict:
        """스키마의 sensitive:true 필드에 policy.default.json 규칙을 적용해 마스킹."""
        masked = deepcopy(obj)
        role = user.get("role", "")
        obj_type = obj.get("type", "")
        sensitive_fields = self._sensitive_fields.get(obj_type, set())
        if not sensitive_fields:
            return masked
        for rule in self._masking_policy.get("masking_rules", []):
            if rule.get("role") != role:
                continue
            rule_type = rule.get("object_type", "*")
            if rule_type != "*" and rule_type != obj_type:
                continue
            mask_value = rule.get("mask_value", "***")
            if rule.get("mask_all_sensitive"):
                for field in sensitive_fields:
                    if field in masked:
                        masked[field] = mask_value
            else:
                for field in rule.get("fields", []):
                    if field in sensitive_fields and field in masked:
                        masked[field] = mask_value
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

    def can_manage_workflow_graph(self, user: dict, action: str) -> bool:
        """워크플로우 그래프 CRUD 권한 (Phase 1).

        - read   : 모든 인증 사용자
        - write  : AccountManager / FinanceManager / Admin
        - run    : AccountManager / FinanceManager / Admin
        - delete : Admin
        """
        role = user.get("role")
        if action == "read":
            return role in {"Viewer", "Analyst", "AccountManager", "FinanceManager", "Admin"}
        if action == "write" or action == "run":
            return role in {"AccountManager", "FinanceManager", "Admin"}
        if action == "delete":
            return role == "Admin"
        return False

    def can_manage_ontology(self, user: dict, action: str) -> bool:
        """온톨로지 관계 인스턴스 CRUD 권한.

        - write  : AccountManager / FinanceManager / Admin
        - delete : Admin
        """
        role = user.get("role")
        if action == "write":
            return role in {"AccountManager", "FinanceManager", "Admin"}
        if action == "delete":
            return role == "Admin"
        return False

    def assert_can_manage_ontology(self, user: dict, action: str) -> None:
        if not self.can_manage_ontology(user, action):
            self.audit.record(
                "ACCESS_DENIED", user, "OntologyRelationship", "-",
                {"reason": f"ontology:{action}"},
            )
            raise AppError("FORBIDDEN", f"온톨로지 관계 {action} 권한이 없습니다.", 403)

    def can_execute_action(self, user: dict, action: str, order: dict, customer: dict) -> bool:
        if user["role"] == "Admin":
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
