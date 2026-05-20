from typing import Dict, Any, Optional
from app.models.identity import UserIdentity
from app.repositories.audit import AuditRepository

class AuditService:
    """시스템 내 발생하는 주요 액션을 기록하는 서비스"""

    def __init__(self, identity: UserIdentity):
        self.identity = identity
        self.repo = AuditRepository(identity.company_id, identity.current_project_id)

    def log_action(self, action: str, resource_id: str, details: Dict[str, Any]):
        """액션 기록 실행"""
        event = {
            "user_id": self.identity.user_id,
            "username": self.identity.username,
            "action": action,
            "resource_id": resource_id,
            "details": details
        }
        self.repo.append_log(event)

# 사용 예시:
# audit_service.log_action("CREATE_ENTITY", entity_id, {"type": "EQUIPMENT"})
