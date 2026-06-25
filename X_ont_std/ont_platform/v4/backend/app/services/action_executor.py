"""Phase 3: 액션 실행 엔진 — 6개 핵심 액션"""
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import Entity, ActionExecution, WriteBackQueue, AuditLog, ChangeLog
from app.services.changelog_service import ChangeLogService


class ActionResult:
    """액션 실행 결과"""
    def __init__(self, success: bool, message: str, data: Dict[str, Any] = None, error: str = None):
        self.success = success
        self.message = message
        self.data = data or {}
        self.error = error


class ActionBase(ABC):
    """액션 기본 클래스"""

    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def execute(self, entity_id: str, **kwargs) -> ActionResult:
        """액션 실행 (구현해야 함)"""
        pass

    def _create_action_execution(
        self,
        action_id: str,
        entity_id: str,
        requested_by: str,
        result: Dict = None
    ) -> ActionExecution:
        """ActionExecution 레코드 생성"""
        action_exec = ActionExecution(
            id=f"ae_{uuid4().hex[:8]}",
            action_id=action_id,
            entity_id=entity_id,
            domain_id="ai-voucher-2025",
            status="EXECUTED",
            requested_by=requested_by,
            executed_by=requested_by,
            result=result or {},
            requested_at=datetime.utcnow(),
            executed_at=datetime.utcnow()
        )
        self.db.add(action_exec)
        self.db.flush()
        return action_exec

    def _record_audit_log(
        self,
        entity_id: str,
        action_id: str,
        old_state: Dict,
        new_state: Dict,
        actor: str
    ):
        """Audit log 기록"""
        audit = AuditLog(
            entity_id=entity_id,
            domain_id="ai-voucher-2025",
            operation="EXECUTE",
            old_state=old_state,
            new_state=new_state,
            actor=actor,
            timestamp=datetime.utcnow()
        )
        self.db.add(audit)

    def _queue_writeback(
        self,
        action_execution_id: str,
        target_system: str,
        payload: Dict[str, Any]
    ) -> WriteBackQueue:
        """Write-back 큐에 추가"""
        writeback = WriteBackQueue(
            id=f"wb_{uuid4().hex[:8]}",
            action_execution_id=action_execution_id,
            target_system=target_system,
            payload=payload,
            status="PENDING"
        )
        self.db.add(writeback)
        return writeback


class ApproveProject(ActionBase):
    """프로젝트 승인"""

    def execute(self, entity_id: str, approver: str, **kwargs) -> ActionResult:
        entity = self.db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            return ActionResult(False, f"Entity {entity_id} not found", error="NOT_FOUND")

        old_status = entity.properties.get("status", "UnderReview")
        if old_status != "UnderReview":
            return ActionResult(False, f"Cannot approve project in {old_status} status", error="INVALID_STATUS")

        old_state = entity.properties.copy()
        entity.properties["status"] = "Approved"
        entity.properties["approved_by"] = approver
        entity.properties["approved_at"] = datetime.utcnow().isoformat()
        entity.version += 1

        action_exec = self._create_action_execution(
            action_id="approve_project",
            entity_id=entity_id,
            requested_by=approver,
            result={"new_status": "Approved"}
        )

        self._record_audit_log(
            entity_id=entity_id,
            action_id="approve_project",
            old_state=old_state,
            new_state=entity.properties,
            actor=approver
        )

        self._queue_writeback(
            action_execution_id=action_exec.id,
            target_system="SAP",
            payload={
                "project_id": entity_id,
                "action": "APPROVE",
                "approver": approver,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # ✅ Changelog 생성
        ChangeLogService.create_changelog(
            db=self.db,
            entity_id=entity_id,
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="APPROVE_PROJECT",
            actor=approver,
            old_status=old_status,
            new_status="Approved",
            source="api",
            target_system="SAP"
        )

        self.db.commit()
        return ActionResult(True, "Project approved successfully", data={"entity_id": entity_id, "new_status": "Approved"})


class RejectProject(ActionBase):
    """프로젝트 거절"""

    def execute(self, entity_id: str, reason: str, rejected_by: str, **kwargs) -> ActionResult:
        entity = self.db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            return ActionResult(False, f"Entity {entity_id} not found", error="NOT_FOUND")

        old_state = entity.properties.copy()
        old_status = entity.properties.get("status", "Unknown")
        entity.properties["status"] = "Rejected"
        entity.properties["rejection_reason"] = reason
        entity.properties["rejected_by"] = rejected_by
        entity.properties["rejected_at"] = datetime.utcnow().isoformat()
        entity.version += 1

        action_exec = self._create_action_execution(
            action_id="reject_project",
            entity_id=entity_id,
            requested_by=rejected_by,
            result={"new_status": "Rejected"}
        )

        self._record_audit_log(
            entity_id=entity_id,
            action_id="reject_project",
            old_state=old_state,
            new_state=entity.properties,
            actor=rejected_by
        )

        self._queue_writeback(
            action_execution_id=action_exec.id,
            target_system="SAP",
            payload={
                "project_id": entity_id,
                "action": "REJECT",
                "reason": reason,
                "rejected_by": rejected_by,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # ✅ Changelog 생성
        ChangeLogService.create_changelog(
            db=self.db,
            entity_id=entity_id,
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="REJECT_PROJECT",
            actor=rejected_by,
            old_status=old_status,
            new_status="Rejected",
            source="api",
            target_system="SAP"
        )

        self.db.commit()
        return ActionResult(True, "Project rejected successfully", data={"entity_id": entity_id, "new_status": "Rejected"})


class ChangeDeadline(ActionBase):
    """기한 변경"""

    def execute(self, entity_id: str, new_deadline: str, changed_by: str, **kwargs) -> ActionResult:
        entity = self.db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            return ActionResult(False, f"Entity {entity_id} not found", error="NOT_FOUND")

        try:
            datetime.fromisoformat(new_deadline.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return ActionResult(False, "Invalid deadline format", error="INVALID_DEADLINE")

        old_state = entity.properties.copy()
        old_status = entity.properties.get("status", "Unknown")
        old_deadline = entity.properties.get("deadline")
        entity.properties["deadline"] = new_deadline
        entity.properties["deadline_changed_by"] = changed_by
        entity.properties["deadline_changed_at"] = datetime.utcnow().isoformat()
        entity.version += 1

        action_exec = self._create_action_execution(
            action_id="change_deadline",
            entity_id=entity_id,
            requested_by=changed_by,
            result={"new_deadline": new_deadline}
        )

        self._record_audit_log(
            entity_id=entity_id,
            action_id="change_deadline",
            old_state=old_state,
            new_state=entity.properties,
            actor=changed_by
        )

        self._queue_writeback(
            action_execution_id=action_exec.id,
            target_system="SAP",
            payload={
                "project_id": entity_id,
                "action": "CHANGE_DEADLINE",
                "old_deadline": old_deadline,
                "new_deadline": new_deadline,
                "changed_by": changed_by,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # ✅ Changelog 생성
        ChangeLogService.create_changelog(
            db=self.db,
            entity_id=entity_id,
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="CHANGE_DEADLINE",
            actor=changed_by,
            old_status=old_status,
            new_status=old_status,  # 상태는 변하지 않음
            source="api",
            target_system="SAP"
        )

        self.db.commit()
        return ActionResult(True, "Deadline changed successfully", data={"entity_id": entity_id, "old_deadline": old_deadline, "new_deadline": new_deadline})


class RequestMoreInfo(ActionBase):
    """추가 정보 요청"""

    def execute(self, entity_id: str, info_needed: str, requested_by: str, **kwargs) -> ActionResult:
        entity = self.db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            return ActionResult(False, f"Entity {entity_id} not found", error="NOT_FOUND")

        old_state = entity.properties.copy()
        old_status = entity.properties.get("status", "Unknown")
        entity.properties["status"] = "MoreInfoNeeded"
        entity.properties["info_needed"] = info_needed
        entity.properties["info_requested_by"] = requested_by
        entity.properties["info_requested_at"] = datetime.utcnow().isoformat()
        entity.version += 1

        action_exec = self._create_action_execution(
            action_id="request_more_info",
            entity_id=entity_id,
            requested_by=requested_by,
            result={"new_status": "MoreInfoNeeded"}
        )

        self._record_audit_log(
            entity_id=entity_id,
            action_id="request_more_info",
            old_state=old_state,
            new_state=entity.properties,
            actor=requested_by
        )

        self._queue_writeback(
            action_execution_id=action_exec.id,
            target_system="NOTIFICATION",
            payload={
                "project_id": entity_id,
                "action": "REQUEST_INFO",
                "info_needed": info_needed,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # ✅ Changelog 생성
        ChangeLogService.create_changelog(
            db=self.db,
            entity_id=entity_id,
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="REQUEST_MORE_INFO",
            actor=requested_by,
            old_status=old_status,
            new_status="MoreInfoNeeded",
            source="api",
            target_system="NOTIFICATION"
        )

        self.db.commit()
        return ActionResult(True, "More info requested successfully", data={"entity_id": entity_id, "new_status": "MoreInfoNeeded"})


class StartPayment(ActionBase):
    """결제 시작 (금액 기반 권한)"""

    def execute(self, entity_id: str, amount: float, approved_by: str, **kwargs) -> ActionResult:
        entity = self.db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            return ActionResult(False, f"Entity {entity_id} not found", error="NOT_FOUND")

        user_role = kwargs.get("user_role", "USER")
        if amount >= 10000000 and user_role != "CEO":
            return ActionResult(False, "CEO approval required for amounts >= 10,000,000", error="INSUFFICIENT_PERMISSION")
        elif amount >= 1000000 and user_role not in ["CFO", "CEO"]:
            return ActionResult(False, "CFO approval required for amounts >= 1,000,000", error="INSUFFICIENT_PERMISSION")

        old_state = entity.properties.copy()
        old_status = entity.properties.get("status", "Unknown")
        entity.properties["status"] = "PaymentStarted"
        entity.properties["payment_amount"] = amount
        entity.properties["approved_by"] = approved_by
        entity.properties["approval_date"] = datetime.utcnow().isoformat()
        entity.version += 1

        action_exec = self._create_action_execution(
            action_id="start_payment",
            entity_id=entity_id,
            requested_by=approved_by,
            result={"amount": amount}
        )

        self._record_audit_log(
            entity_id=entity_id,
            action_id="start_payment",
            old_state=old_state,
            new_state=entity.properties,
            actor=approved_by
        )

        self._queue_writeback(
            action_execution_id=action_exec.id,
            target_system="SAP",
            payload={
                "project_id": entity_id,
                "action": "START_PAYMENT",
                "amount": amount,
                "approved_by": approved_by,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # ✅ Changelog 생성
        ChangeLogService.create_changelog(
            db=self.db,
            entity_id=entity_id,
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="START_PAYMENT",
            actor=approved_by,
            old_status=old_status,
            new_status="PaymentStarted",
            source="api",
            target_system="SAP"
        )

        self.db.commit()
        return ActionResult(True, f"Payment started for amount {amount}", data={"entity_id": entity_id, "amount": amount})


class CompleteProject(ActionBase):
    """프로젝트 완료"""

    def execute(self, entity_id: str, completed_by: str, **kwargs) -> ActionResult:
        entity = self.db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            return ActionResult(False, f"Entity {entity_id} not found", error="NOT_FOUND")

        old_state = entity.properties.copy()
        old_status = entity.properties.get("status", "Unknown")
        current_status = entity.properties.get("status", "Unknown")
        if current_status not in ["Approved", "PaymentStarted"]:
            return ActionResult(False, f"Cannot complete project in {current_status} status", error="INVALID_STATUS")

        entity.properties["status"] = "Completed"
        entity.properties["completed_by"] = completed_by
        entity.properties["completion_date"] = datetime.utcnow().isoformat()
        entity.version += 1

        action_exec = self._create_action_execution(
            action_id="complete_project",
            entity_id=entity_id,
            requested_by=completed_by,
            result={"new_status": "Completed"}
        )

        self._record_audit_log(
            entity_id=entity_id,
            action_id="complete_project",
            old_state=old_state,
            new_state=entity.properties,
            actor=completed_by
        )

        self._queue_writeback(
            action_execution_id=action_exec.id,
            target_system="SAP",
            payload={
                "project_id": entity_id,
                "action": "COMPLETE",
                "completed_by": completed_by,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # ✅ Changelog 생성
        ChangeLogService.create_changelog(
            db=self.db,
            entity_id=entity_id,
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="COMPLETE_PROJECT",
            actor=completed_by,
            old_status=old_status,
            new_status="Completed",
            source="api",
            target_system="SAP"
        )

        self.db.commit()
        return ActionResult(True, "Project completed successfully", data={"entity_id": entity_id, "new_status": "Completed"})


class ActionExecutor:
    """액션 실행 매니저"""

    ACTIONS = {
        "approve_project": ApproveProject,
        "reject_project": RejectProject,
        "change_deadline": ChangeDeadline,
        "request_more_info": RequestMoreInfo,
        "start_payment": StartPayment,
        "complete_project": CompleteProject,
    }

    def __init__(self, db: Session):
        self.db = db

    def execute(self, action_id: str, entity_id: str, **kwargs) -> ActionResult:
        """액션 실행"""
        if action_id not in self.ACTIONS:
            return ActionResult(False, f"Unknown action: {action_id}", error="UNKNOWN_ACTION")

        action_class = self.ACTIONS[action_id]
        action = action_class(self.db)

        try:
            return action.execute(entity_id, **kwargs)
        except Exception as e:
            return ActionResult(False, str(e), error="EXECUTION_ERROR")

    def get_available_actions(self) -> Dict[str, str]:
        """사용 가능한 액션 목록"""
        return {
            "approve_project": "프로젝트 승인",
            "reject_project": "프로젝트 거절",
            "change_deadline": "기한 변경",
            "request_more_info": "추가 정보 요청",
            "start_payment": "결제 시작",
            "complete_project": "프로젝트 완료",
        }
