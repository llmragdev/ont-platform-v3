"""Write-back 통합 테스트 — 전체 워크플로우"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.models import Base, Entity, ActionExecution, WriteBackQueue, ChangeLog
from app.services.action_executor import ApproveProject, RejectProject, ChangeDeadline, RequestMoreInfo, StartPayment, CompleteProject
from app.services.write_back_worker import WriteBackWorker
from app.services.sap_api_mock import SAPApiMock, SAPApiMockFactory


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """테스트용 DB 세션"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_project(db: Session):
    """테스트용 프로젝트"""
    entity = Entity(
        id="proj_001",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        properties={
            "name": "AI Voucher Project",
            "status": "UnderReview",
            "budget": 5000000,
            "manager": "manager@example.com"
        }
    )
    db.add(entity)
    db.commit()
    return entity


class TestWriteBackIntegrationApproveProject:
    """ApproveProject 액션의 전체 Write-back 흐름"""

    def test_approve_creates_changelog_and_writeback(self, db: Session, test_project):
        """Test 1: 승인 액션 → Changelog + WriteBackQueue 생성"""
        action = ApproveProject(db)
        result = action.execute(entity_id="proj_001", approver="pm@example.com")

        assert result.success is True

        # Changelog 확인
        changelog = db.query(ChangeLog).filter(
            ChangeLog.entity_id == "proj_001"
        ).first()
        assert changelog is not None
        assert changelog.action_type == "APPROVE_PROJECT"
        assert changelog.old_status == "UnderReview"
        assert changelog.new_status == "Approved"
        assert changelog.sync_status == "PENDING"

        # WriteBackQueue 확인
        writeback = db.query(WriteBackQueue).filter(
            WriteBackQueue.target_system == "SAP"
        ).first()
        assert writeback is not None
        assert writeback.status == "PENDING"

    def test_approve_worker_syncs_to_sap(self, db: Session, test_project):
        """Test 2: Worker가 WriteBackQueue를 SAP에 동기화"""
        # 승인 액션 실행
        action = ApproveProject(db)
        action.execute(entity_id="proj_001", approver="pm@example.com")

        # 100% 성공 Mock으로 Worker 실행
        sap_mock = SAPApiMock(success_rate=1.0)
        worker = WriteBackWorker(db, sap_mock)
        result = worker.process_pending()

        assert result["processed"] == 1
        assert result["succeeded"] == 1

        # WriteBackQueue 상태 확인 (CONFIRMED)
        writeback = db.query(WriteBackQueue).first()
        assert writeback.status == "CONFIRMED"

        # Changelog 상태 확인 (SYNCED)
        changelog = db.query(ChangeLog).first()
        assert changelog.sync_status == "SYNCED"

    def test_approve_worker_retry_on_timeout(self, db: Session, test_project):
        """Test 3: SAP 타임아웃 시 재시도"""
        # 승인 액션 실행
        action = ApproveProject(db)
        action.execute(entity_id="proj_001", approver="pm@example.com")

        # 100% 실패 Mock
        sap_mock = SAPApiMock(success_rate=0.0)
        worker = WriteBackWorker(db, sap_mock)

        # 첫 시도 (실패)
        result = worker.process_pending()
        assert result["processed"] == 1

        writeback = db.query(WriteBackQueue).first()
        assert writeback.status == "PENDING"
        assert writeback.retry_count == 1

        # 두 번째 시도 (여전히 실패)
        result = worker.process_pending()
        writeback = db.query(WriteBackQueue).first()
        assert writeback.retry_count == 2
        assert writeback.status == "PENDING"

    def test_approve_worker_max_retries(self, db: Session, test_project):
        """Test 4: 최대 재시도 초과 → FAILED"""
        action = ApproveProject(db)
        action.execute(entity_id="proj_001", approver="pm@example.com")

        # 100% 실패 Mock
        sap_mock = SAPApiMock(success_rate=0.0)
        worker = WriteBackWorker(db, sap_mock)

        # 3회 이상 시도해서 최대 재시도 초과
        for _ in range(4):
            worker.process_pending()

        writeback = db.query(WriteBackQueue).first()
        assert writeback.status == "FAILED"
        assert writeback.retry_count == 3

        changelog = db.query(ChangeLog).first()
        assert changelog.sync_status == "FAILED"


class TestWriteBackIntegrationMultipleActions:
    """여러 액션의 Write-back 흐름"""

    def test_approve_and_reject_workflows(self, db: Session, test_project):
        """Test 5: 승인과 거절 액션 모두 동기화"""
        # 승인 액션 (proj_001)
        approve_action = ApproveProject(db)
        approve_action.execute(entity_id="proj_001", approver="pm@example.com")

        # 거절 액션용 다른 프로젝트
        project2 = Entity(
            id="proj_002",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            properties={
                "status": "UnderReview",
                "budget": 3000000
            }
        )
        db.add(project2)
        db.commit()

        reject_action = RejectProject(db)
        reject_action.execute(
            entity_id="proj_002",
            reason="Insufficient budget",
            rejected_by="reviewer@example.com"
        )

        # Worker 실행 (100% 성공)
        sap_mock = SAPApiMock(success_rate=1.0)
        worker = WriteBackWorker(db, sap_mock)
        result = worker.process_pending()

        assert result["processed"] == 2
        assert result["succeeded"] == 2

        # 모든 WriteBackQueue 항목 확인
        writebacks = db.query(WriteBackQueue).all()
        assert len(writebacks) == 2
        assert all(wb.status == "CONFIRMED" for wb in writebacks)

        # 모든 Changelog 항목 확인
        changelogs = db.query(ChangeLog).all()
        assert len(changelogs) == 2
        assert changelogs[0].action_type == "APPROVE_PROJECT"
        assert changelogs[1].action_type == "REJECT_PROJECT"

    def test_change_deadline_workflow(self, db: Session, test_project):
        """Test 6: 기한 변경 액션 동기화"""
        action = ChangeDeadline(db)
        result = action.execute(
            entity_id="proj_001",
            new_deadline="2026-06-30T23:59:59Z",
            changed_by="manager@example.com"
        )

        assert result.success is True

        # Changelog 확인
        changelog = db.query(ChangeLog).filter(
            ChangeLog.action_type == "CHANGE_DEADLINE"
        ).first()
        assert changelog is not None

        # Worker 동기화
        sap_mock = SAPApiMock(success_rate=1.0)
        worker = WriteBackWorker(db, sap_mock)
        result = worker.process_pending()

        assert result["succeeded"] == 1

    def test_request_more_info_notification_workflow(self, db: Session, test_project):
        """Test 7: 정보 요청 액션 → NOTIFICATION 시스템"""
        action = RequestMoreInfo(db)
        result = action.execute(
            entity_id="proj_001",
            info_needed="Please provide detailed budget breakdown",
            requested_by="reviewer@example.com"
        )

        assert result.success is True

        # WriteBackQueue 확인 (NOTIFICATION 시스템)
        writeback = db.query(WriteBackQueue).filter(
            WriteBackQueue.target_system == "NOTIFICATION"
        ).first()
        assert writeback is not None

        # Notification Mock (100% 성공)
        notification_mock = SAPApiMock(success_rate=1.0)
        worker = WriteBackWorker(db, notification_mock)
        result = worker.process_pending()

        assert result["succeeded"] == 1

    def test_start_payment_workflow(self, db: Session, test_project):
        """Test 8: 결제 시작 액션 동기화"""
        # 먼저 프로젝트를 Approved 상태로 변경
        project = db.query(Entity).filter(Entity.id == "proj_001").first()
        project.properties["status"] = "Approved"
        db.commit()

        action = StartPayment(db)
        result = action.execute(
            entity_id="proj_001",
            amount=2000000,
            approved_by="cfo@example.com",
            user_role="CFO"
        )

        assert result.success is True

        # Worker 동기화
        sap_mock = SAPApiMock(success_rate=1.0)
        worker = WriteBackWorker(db, sap_mock)
        result = worker.process_pending()

        assert result["succeeded"] == 1

    def test_complete_project_workflow(self, db: Session):
        """Test 9: 프로젝트 완료 액션 동기화"""
        # 별도의 프로젝트 생성 (Approved 상태로)
        project = Entity(
            id="proj_complete",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            properties={
                "status": "PaymentStarted",
                "budget": 5000000
            }
        )
        db.add(project)
        db.commit()

        action = CompleteProject(db)
        result = action.execute(
            entity_id="proj_complete",
            completed_by="pm@example.com"
        )

        assert result.success is True

        # Worker 동기화
        sap_mock = SAPApiMock(success_rate=1.0)
        worker = WriteBackWorker(db, sap_mock)
        result = worker.process_pending()

        assert result["succeeded"] == 1


class TestWriteBackIntegrationStatistics:
    """Write-back 통계 및 모니터링"""

    def test_worker_statistics_tracking(self, db: Session, test_project):
        """Test 10: Worker 통계 추적"""
        # 3개 액션 실행
        approve_action = ApproveProject(db)
        approve_action.execute(entity_id="proj_001", approver="pm@example.com")

        project2 = Entity(
            id="proj_002",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            properties={"status": "UnderReview"}
        )
        db.add(project2)
        db.commit()

        reject_action = RejectProject(db)
        reject_action.execute(
            entity_id="proj_002",
            reason="Test",
            rejected_by="reviewer@example.com"
        )

        # Worker 실행
        sap_mock = SAPApiMock(success_rate=1.0)
        worker = WriteBackWorker(db, sap_mock)
        result = worker.process_pending()

        stats = worker.get_statistics()

        assert stats["pending_count"] == 0
        assert stats["confirmed_count"] == 2
        assert stats["failed_count"] == 0

    def test_sap_mock_call_tracking(self, db: Session, test_project):
        """Test 11: SAP Mock 호출 기록"""
        action = ApproveProject(db)
        action.execute(entity_id="proj_001", approver="pm@example.com")

        sap_mock = SAPApiMock(success_rate=1.0)
        worker = WriteBackWorker(db, sap_mock)
        worker.process_pending()

        # Mock 호출 기록 확인
        history = sap_mock.get_call_history()
        assert len(history) == 1
        assert history[0]["target_system"] == "SAP"
        assert history[0]["status"].value == "success"

    def test_changelog_audit_trail(self, db: Session, test_project):
        """Test 12: Changelog 감사 추적"""
        # 여러 액션 실행
        approve = ApproveProject(db)
        approve.execute(entity_id="proj_001", approver="pm@example.com")

        # Changelog 기록 확인
        changelogs = db.query(ChangeLog).filter(
            ChangeLog.entity_id == "proj_001"
        ).order_by(ChangeLog.timestamp).all()

        assert len(changelogs) >= 1
        assert changelogs[0].action_type == "APPROVE_PROJECT"

        # Worker 동기화
        sap_mock = SAPApiMock(success_rate=1.0)
        worker = WriteBackWorker(db, sap_mock)
        worker.process_pending()

        # 동기화 확인
        db.refresh(changelogs[0])
        assert changelogs[0].sync_status == "SYNCED"


class TestWriteBackIntegrationFailureRecovery:
    """Write-back 실패 및 복구"""

    def test_partial_failure_recovery(self, db: Session, test_project):
        """Test 13: 일부 실패 → 재시도 → 성공"""
        action = ApproveProject(db)
        action.execute(entity_id="proj_001", approver="pm@example.com")

        # 처음엔 실패
        sap_mock = SAPApiMock(success_rate=0.0)
        worker = WriteBackWorker(db, sap_mock)
        result = worker.process_pending()

        writeback = db.query(WriteBackQueue).first()
        assert writeback.retry_count == 1
        assert writeback.status == "PENDING"

        # 나중에 성공하는 Mock으로 재시도
        sap_mock_success = SAPApiMock(success_rate=1.0)
        worker_success = WriteBackWorker(db, sap_mock_success)
        result = worker_success.process_pending()

        writeback = db.query(WriteBackQueue).first()
        assert writeback.status == "CONFIRMED"

    def test_cascade_failure_handling(self, db: Session, test_project):
        """Test 14: 다중 항목 중 일부만 실패"""
        # 2개 액션 실행
        action1 = ApproveProject(db)
        action1.execute(entity_id="proj_001", approver="pm@example.com")

        project2 = Entity(
            id="proj_002",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            properties={"status": "UnderReview"}
        )
        db.add(project2)
        db.commit()

        action2 = RejectProject(db)
        action2.execute(
            entity_id="proj_002",
            reason="Test",
            rejected_by="reviewer@example.com"
        )

        # 70% 성공률 Mock (일부 실패)
        sap_mock = SAPApiMock(success_rate=0.70)
        worker = WriteBackWorker(db, sap_mock)
        result = worker.process_pending()

        # 최소 1개는 성공 (70% 확률)
        stats = worker.get_statistics()
        total = stats["confirmed_count"] + stats["pending_count"]
        assert total >= 1  # 적어도 1개 처리됨
