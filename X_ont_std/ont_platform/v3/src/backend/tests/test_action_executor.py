"""액션 실행 엔진 Unit 테스트"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.database import get_db, engine
from app.db.base import Base
from app.db.models import Entity, ActionExecution, WriteBackQueue, AuditLog
from app.services.action_executor import (
    ActionExecutor, ApproveProject, RejectProject, ChangeDeadline,
    RequestMoreInfo, StartPayment, CompleteProject
)


@pytest.fixture
def setup_db():
    """테스트 DB 초기화"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_db):
    """DB 세션"""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_entity(db_session):
    """샘플 엔티티 생성"""
    entity = Entity(
        id="proj_001",
        entity_type="PROJECT",
        domain_id="ai-voucher-2025",
        properties={
            "name": "Test Project",
            "status": "UnderReview",
            "budget": 5000000
        }
    )
    db_session.add(entity)
    db_session.commit()
    return entity


class TestApproveProject:
    """ApproveProject 액션 테스트"""

    def test_approve_success(self, db_session, sample_entity):
        """프로젝트 승인 성공"""
        action = ApproveProject(db_session)
        result = action.execute(
            entity_id="proj_001",
            approver="john@example.com"
        )

        assert result.success
        assert result.message == "Project approved successfully"
        assert result.data["new_status"] == "Approved"

    def test_approve_nonexistent_entity(self, db_session):
        """존재하지 않는 엔티티 승인"""
        action = ApproveProject(db_session)
        result = action.execute(
            entity_id="nonexistent",
            approver="john@example.com"
        )

        assert not result.success
        assert result.error == "NOT_FOUND"

    def test_approve_invalid_status(self, db_session, sample_entity):
        """이미 승인된 엔티티 다시 승인"""
        # 먼저 승인
        action = ApproveProject(db_session)
        action.execute(entity_id="proj_001", approver="john@example.com")

        # 다시 승인 시도
        result = action.execute(
            entity_id="proj_001",
            approver="jane@example.com"
        )

        assert not result.success
        assert result.error == "INVALID_STATUS"

    def test_approve_creates_audit_log(self, db_session, sample_entity):
        """승인 시 Audit log 생성"""
        action = ApproveProject(db_session)
        action.execute(entity_id="proj_001", approver="john@example.com")

        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_id == "proj_001"
        ).all()

        assert len(audit_logs) > 0
        assert audit_logs[0].operation == "EXECUTE"
        assert audit_logs[0].actor == "john@example.com"

    def test_approve_queues_writeback(self, db_session, sample_entity):
        """승인 시 Write-back 큐 추가"""
        action = ApproveProject(db_session)
        action.execute(entity_id="proj_001", approver="john@example.com")

        writebacks = db_session.query(WriteBackQueue).all()

        assert len(writebacks) > 0
        assert writebacks[0].target_system == "SAP"
        assert writebacks[0].status == "PENDING"


class TestRejectProject:
    """RejectProject 액션 테스트"""

    def test_reject_success(self, db_session, sample_entity):
        """프로젝트 거절 성공"""
        action = RejectProject(db_session)
        result = action.execute(
            entity_id="proj_001",
            reason="Budget too high",
            rejected_by="manager@example.com"
        )

        assert result.success
        assert result.data["new_status"] == "Rejected"

    def test_reject_stores_reason(self, db_session, sample_entity):
        """거절 사유 저장"""
        action = RejectProject(db_session)
        action.execute(
            entity_id="proj_001",
            reason="Invalid budget",
            rejected_by="manager@example.com"
        )

        entity = db_session.query(Entity).filter(Entity.id == "proj_001").first()
        assert entity.properties["rejection_reason"] == "Invalid budget"


class TestChangeDeadline:
    """ChangeDeadline 액션 테스트"""

    def test_change_deadline_success(self, db_session, sample_entity):
        """기한 변경 성공"""
        action = ChangeDeadline(db_session)
        new_deadline = "2026-12-31T23:59:59Z"
        result = action.execute(
            entity_id="proj_001",
            new_deadline=new_deadline,
            changed_by="admin@example.com"
        )

        assert result.success
        assert result.data["new_deadline"] == new_deadline

    def test_change_deadline_invalid_format(self, db_session, sample_entity):
        """잘못된 기한 형식"""
        action = ChangeDeadline(db_session)
        result = action.execute(
            entity_id="proj_001",
            new_deadline="invalid-date",
            changed_by="admin@example.com"
        )

        assert not result.success
        assert result.error == "INVALID_DEADLINE"


class TestRequestMoreInfo:
    """RequestMoreInfo 액션 테스트"""

    def test_request_info_success(self, db_session, sample_entity):
        """추가 정보 요청 성공"""
        action = RequestMoreInfo(db_session)
        result = action.execute(
            entity_id="proj_001",
            info_needed="Provide detailed budget breakdown",
            requested_by="reviewer@example.com"
        )

        assert result.success
        assert result.data["new_status"] == "MoreInfoNeeded"

    def test_request_info_updates_status(self, db_session, sample_entity):
        """상태가 MoreInfoNeeded로 변경"""
        action = RequestMoreInfo(db_session)
        action.execute(
            entity_id="proj_001",
            info_needed="Budget details",
            requested_by="reviewer@example.com"
        )

        entity = db_session.query(Entity).filter(Entity.id == "proj_001").first()
        assert entity.properties["status"] == "MoreInfoNeeded"


class TestStartPayment:
    """StartPayment 액션 테스트 (금액 기반 권한)"""

    def test_start_payment_user_fails(self, db_session, sample_entity):
        """일반 사용자는 결제 시작 실패"""
        action = StartPayment(db_session)
        result = action.execute(
            entity_id="proj_001",
            amount=5000000,
            approved_by="user@example.com",
            user_role="USER"
        )

        # USER는 권한이 없어야 함
        assert not result.success

    def test_start_payment_accountant_1m_success(self, db_session, sample_entity):
        """회계담당자는 100만원 이상 결제 시작 가능"""
        action = StartPayment(db_session)
        result = action.execute(
            entity_id="proj_001",
            amount=5000000,
            approved_by="accountant@example.com",
            user_role="ACCOUNTANT"
        )

        assert result.success

    def test_start_payment_cfo_10m_success(self, db_session, sample_entity):
        """CFO는 1000만원 이상 결제 시작 가능"""
        action = StartPayment(db_session)
        result = action.execute(
            entity_id="proj_001",
            amount=15000000,
            approved_by="cfo@example.com",
            user_role="CFO"
        )

        assert result.success

    def test_start_payment_ceo_unlimited(self, db_session, sample_entity):
        """CEO는 무제한 결제 시작 가능"""
        action = StartPayment(db_session)
        result = action.execute(
            entity_id="proj_001",
            amount=100000000,
            approved_by="ceo@example.com",
            user_role="CEO"
        )

        assert result.success

    def test_start_payment_accountant_cannot_approve_10m(self, db_session, sample_entity):
        """회계담당자는 1000만원 이상 승인 불가"""
        action = StartPayment(db_session)
        result = action.execute(
            entity_id="proj_001",
            amount=15000000,
            approved_by="accountant@example.com",
            user_role="ACCOUNTANT"
        )

        assert not result.success

    def test_start_payment_cfo_cannot_approve_10m(self, db_session, sample_entity):
        """CFO는 1000만원 이상 승인 불가"""
        action = StartPayment(db_session)
        result = action.execute(
            entity_id="proj_001",
            amount=15000000,
            approved_by="cfo@example.com",
            user_role="CFO"
        )

        assert not result.success


class TestCompleteProject:
    """CompleteProject 액션 테스트"""

    def test_complete_success(self, db_session, sample_entity):
        """프로젝트 완료 성공"""
        # 먼저 승인 상태로 변경
        entity = db_session.query(Entity).filter(Entity.id == "proj_001").first()
        entity.properties["status"] = "Approved"
        db_session.commit()

        action = CompleteProject(db_session)
        result = action.execute(
            entity_id="proj_001",
            completed_by="manager@example.com"
        )

        assert result.success
        assert result.data["new_status"] == "Completed"

    def test_complete_from_payment_status(self, db_session, sample_entity):
        """PaymentStarted 상태에서도 완료 가능"""
        entity = db_session.query(Entity).filter(Entity.id == "proj_001").first()
        entity.properties["status"] = "PaymentStarted"
        db_session.commit()

        action = CompleteProject(db_session)
        result = action.execute(
            entity_id="proj_001",
            completed_by="manager@example.com"
        )

        assert result.success

    def test_complete_from_invalid_status(self, db_session, sample_entity):
        """UnderReview 상태에서는 완료 불가"""
        action = CompleteProject(db_session)
        result = action.execute(
            entity_id="proj_001",
            completed_by="manager@example.com"
        )

        assert not result.success
        assert result.error == "INVALID_STATUS"


class TestActionExecutor:
    """ActionExecutor 매니저 테스트"""

    def test_execute_unknown_action(self, db_session, sample_entity):
        """존재하지 않는 액션 실행"""
        executor = ActionExecutor(db_session)
        result = executor.execute(
            action_id="unknown_action",
            entity_id="proj_001"
        )

        assert not result.success
        assert result.error == "UNKNOWN_ACTION"

    def test_get_available_actions(self, db_session):
        """사용 가능한 액션 목록"""
        executor = ActionExecutor(db_session)
        actions = executor.get_available_actions()

        assert len(actions) == 6
        assert "approve_project" in actions
        assert "reject_project" in actions
        assert "change_deadline" in actions
        assert "request_more_info" in actions
        assert "start_payment" in actions
        assert "complete_project" in actions

    def test_execute_all_actions(self, db_session, sample_entity):
        """모든 액션 실행 가능"""
        executor = ActionExecutor(db_session)

        # 1. Approve
        result = executor.execute(
            "approve_project",
            "proj_001",
            approver="john@example.com"
        )
        assert result.success

        # 2. Request More Info (새 엔티티 필요)
        entity2 = Entity(
            id="proj_002",
            entity_type="PROJECT",
            domain_id="ai-voucher-2025",
            properties={"status": "UnderReview"}
        )
        db_session.add(entity2)
        db_session.commit()

        result = executor.execute(
            "request_more_info",
            "proj_002",
            info_needed="Budget",
            requested_by="reviewer@example.com"
        )
        assert result.success

        # 3. Change Deadline
        result = executor.execute(
            "change_deadline",
            "proj_001",
            new_deadline="2026-12-31T23:59:59Z",
            changed_by="admin@example.com"
        )
        assert result.success

        # 4. Start Payment
        result = executor.execute(
            "start_payment",
            "proj_001",
            amount=5000000,
            approved_by="cfo@example.com",
            user_role="CFO"
        )
        assert result.success

        # 5. Complete
        result = executor.execute(
            "complete_project",
            "proj_001",
            completed_by="manager@example.com"
        )
        assert result.success
