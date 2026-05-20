from __future__ import annotations
from typing import Any, Dict, List, Optional
from .engine import ObjectInstance, OntologyEngine

class PolicyEngine:
    def __init__(self, engine: OntologyEngine):
        self.engine = engine
        # 역할별 권한 정의 (실제로는 DB나 설정 파일에서 로드)
        self.role_policies = {
            "admin": {"can_view_sensitive": True, "allowed_actions": ["*"]},
            "approver": {"can_view_sensitive": True, "allowed_actions": ["ApproveOrder", "RejectOrder"]},
            "analyst": {"can_view_sensitive": False, "allowed_actions": ["ApproveOrder"]},
            "viewer": {"can_view_sensitive": False, "allowed_actions": []}
        }

    def get_user_policy(self, role: str) -> Dict[str, Any]:
        return self.role_policies.get(role, self.role_policies["viewer"])

    def filter_object(self, obj: ObjectInstance, role: str) -> Dict[str, Any]:
        """사용자 역할에 따라 객체의 속성을 마스킹함 (Ontology-level Security)"""
        policy = self.get_user_policy(role)
        schema = next((ot for ot in self.engine.schema.object_types if ot.id == obj.type), None)
        
        filtered_values = {}
        for key, value in obj.values.items():
            prop_schema = next((p for p in schema.properties if p.name == key), None) if schema else None
            
            if prop_schema and prop_schema.sensitive and not policy["can_view_sensitive"]:
                filtered_values[key] = "●●●●● (Restricted)"
            else:
                filtered_values[key] = value
                
        return {
            "id": obj.id,
            "type": obj.type,
            "values": filtered_values,
            "display_info": {
                "display_name": schema.display_name if schema else obj.type,
                "icon": schema.icon if schema else "Box"
            }
        }

    def can_execute(self, action_name: str, role: str) -> bool:
        policy = self.get_user_policy(role)
        allowed = policy["allowed_actions"]
        return "*" in allowed or action_name in allowed
