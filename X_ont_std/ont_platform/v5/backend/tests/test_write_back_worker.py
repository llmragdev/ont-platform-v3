"""Write-back Worker 테스트"""
import pytest
import asyncio
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.models import Base, Entity, WriteBackQueue, ActionExecution, ChangeLog
from app.services.write_back_worker import WriteBackWorker, WriteBackWorkerConfig, WriteBackWorkerPool
from app.services.sap_api_mock import SAPApiMock


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
def setup_entities(db: Session):
    """테스트용 엔티티 설정"""
    # Entity 생성
    entity = Entity(
        id="proj_001",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        properties={"status": "UnderReview", "budget": 5000000}
    )
    db.add(entity)
    db.flush()

    # ActionExecution 생성
    action = ActionExecution(
        id="ae_001",
        action_id="approve_project",
        entity_id="proj_001",
        domain_id="ai-voucher-2025",
        status="EXECUTED",
        requested_by="pm@example.com",
        executed_by="pm@example.com",
        requested_at=datetime.utcnow(),
        executed_at=datetime.utcnow()
    )
    db.add(action)
    db.flush()

    # WriteBackQueue 항목 생성
    wb = WriteBackQueue(
        id="wb_001",
        action_execution_id="ae_001",
        target_system="SAP",
        payload={"project_id": "proj_001", "action": "APPROVE"},
        status="PENDING"
    )
    db.add(wb)

    # ChangeLog 생성
    changelog = ChangeLog(
        id="chg_001",
        entity_id="proj_001",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        action_type="APPROVE_PROJECT",
        actor="pm@example.com",
        source="api",
        timestamp=datetime.utcnow(),
        old_status="UnderReview",
        new_status="Approved",
        sync_status="PENDING",
        target_system="SAP"
    )
    db.add(changelog)
    db.commit()

    return entity, action, wb, changelog


class TestWriteBackWorker:
    """Write-back Worker 테스트"""

    def test_worker_initialization(self, db: Session):
        """Test 1: Worker 초기화"""
        sap_mock = SAPApiMock(success_rate=1.0)
        worker = WriteBackWorker(db, sap_mock)

        assert worker.db is db
        assert worker.sap_api is sap_mock
        assert worker.is_running is False
        assert worker.processed_count == 0
        assert worker.success_count == 0
        assert worker.failure_count == 0

    def test_worker_process_successful_item(self, db: Session, setup_entities):
        """Test 2: 성공적인 Write-back 처리"""
        entity, action, wb, changelog = setup_entities

        # 100% 성공 Mock 사용
        sap_mock = SAPApiMock(success_rate=1.0)
        worker = WriteBackWorker(db, sap_mock)

        # Process pending items
        result = worker.process_pending()

        # 결과 검증
        assert result["processed"] == 1
        assert result["succeeded"] == 1
        assert result["failed"] == 0
        assert len(result["errors"]) == 0

        # DB 상태 검증
        db.refresh(wb)
        assert wb.status == "CONFIRMED"
        assert wb.sent_at is not None

    def test_worker_process_timeout_retry(self, db: Session, setup_entities):
        """Test 3: 타임아웃 처리 + 재시도"""
        entity, action, wb, changelog = setup_entities

        # 100% 실패 Mock 사용
        sap_mock = SAPApiMock(success_rate=0.0)
        worker = WriteBackWorker(db, sap_mock)

        # 첫 번째 시도 (실패, 재시도 예정)
        result = worker.process_pending()
        db.refresh(wb)

        assert result["processed"] == 1
        assert result["succeeded"] == 0
        assert wb.status == "PENDING"  # PENDING 유지 (재시도 대기)
        assert wb.retry_count == 1

    def test_worker_max_retries_exceeded(self, db: Session, setup_entities):
        """Test 4: 최대 재시도 초과 → FAILED"""
        entity, action, wb, changelog = setup_entities

        # 100% 실패 Mock 사용
        sap_mock = SAPApiMock(success_rate=0.0)
        config = WriteBackWorkerConfig()
        config.MAX_RETRIES = 2
        worker = WriteBackWorker(db, sap_mock, config)

        # MAX_RETRIES (2) 번 재시도 + 1번 최종 실패
        for i in range(3):
            worker.process_pending()

        db.refresh(wb)
        assert wb.status == "FAILED"
        assert wb.retry_count == 2
        assert wb.error_message is not None

    def test_worker_statistics(self, db: Session, setup_entities):
        """Test 5: Worker 통계"""
        entity, action, wb, changelog = setup_entities

        sap_mock = SAPApiMock(success_rate=1.0)
        worker = WriteBackWorker(db, sap_mock)

        # Process pending items
        worker.process_pending()

        stats = worker.get_statistics()

        assert stats["is_running"] is False
        assert stats["pending_count"] == 0
        assert stats["confirmed_count"] == 1
        assert stats["failed_count"] == 0

    def test_worker_start_stop(self, db: Session):
        """Test 6: Worker 시작/중지"""
        worker = WriteBackWorker(db)

        assert worker.is_running is False

        worker.start()
        assert worker.is_running is True

        worker.stop()
        assert worker.is_running is False

    def test_worker_multiple_items(self, db: Session):
        """Test 7: 여러 Write-back 항목 처리"""
        # 여러 WriteBackQueue 항목 생성
        action_exec = ActionExecution(
            id="ae_test",
            action_id="test",
            entity_id="proj_001",
            domain_id="ai-voucher-2025",
            status="EXECUTED",
            requested_by="user@example.com",
            requested_at=datetime.utcnow()
        )
        db.add(action_exec)
        db.flush()

        for i in range(5):
            wb = WriteBackQueue(
                id=f"wb_{i:03d}",
                action_execution_id="ae_test",
                target_system="SAP",
                payload={"project_id": f"proj_{i:03d}"},
                status="PENDING"
            )
            db.add(wb)

        db.commit()

        sap_mock = SAPApiMock(success_rate=1.0)
        worker = WriteBackWorker(db, sap_mock)

        result = worker.process_pending()

        assert result["processed"] == 5
        assert result["succeeded"] == 5

    def test_worker_mixed_success_failure(self, db: Session):
        """Test 8: 성공과 실패 혼합"""
        # ActionExecution 생성
        action_exec = ActionExecution(
            id="ae_mixed",
            action_id="test",
            entity_id="proj_001",
            domain_id="ai-voucher-2025",
            status="EXECUTED",
            requested_by="user@example.com",
            requested_at=datetime.utcnow()
        )
        db.add(action_exec)
        db.flush()

        # 3개 항목 생성 (절반은 성공할 확률)
        for i in range(10):
            wb = WriteBackQueue(
                id=f"wb_mix_{i:02d}",
                action_execution_id="ae_mixed",
                target_system="SAP",
                payload={"project_id": f"proj_{i:02d}"},
                status="PENDING"
            )
            db.add(wb)

        db.commit()

        # 70% 성공률 Mock
        sap_mock = SAPApiMock(success_rate=0.70)
        worker = WriteBackWorker(db, sap_mock)

        result = worker.process_pending()

        assert result["processed"] == 10
        # 대략 70% 성공 (통계적 검증)
        success_rate = result["succeeded"] / result["processed"]
        assert 0.4 <= success_rate <= 1.0  # 50% 이상 성공

    def test_worker_config_customization(self, db: Session):
        """Test 9: Worker 설정 커스터마이징"""
        config = WriteBackWorkerConfig()
        config.MAX_RETRIES = 5
        config.WORKER_INTERVAL = 30
        config.INITIAL_RETRY_DELAY = 120

        worker = WriteBackWorker(db, config=config)

        assert worker.config.MAX_RETRIES == 5
        assert worker.config.WORKER_INTERVAL == 30
        assert worker.config.INITIAL_RETRY_DELAY == 120


class TestWriteBackWorkerPool:
    """Write-back Worker Pool 테스트"""

    def test_pool_initialization(self, db: Session):
        """Test 10: Worker Pool 초기화"""
        pool = WriteBackWorkerPool(db, num_workers=3)

        assert len(pool.workers) == 3
        assert pool.num_workers == 3

    def test_pool_stop_all(self, db: Session):
        """Test 11: Pool 모든 Worker 중지"""
        pool = WriteBackWorkerPool(db, num_workers=3)

        for worker in pool.workers:
            worker.start()

        pool.stop_all()

        for worker in pool.workers:
            assert worker.is_running is False

    def test_pool_statistics(self, db: Session):
        """Test 12: Pool 통계"""
        pool = WriteBackWorkerPool(db, num_workers=2)

        stats = pool.get_all_statistics()

        assert len(stats) == 2
        assert all(s["is_running"] is False for s in stats)


class TestWriteBackWorkerAsyncBehavior:
    """Write-back Worker 비동기 동작 테스트"""

    def test_worker_error_handling(self, db: Session):
        """Test 13: 예상치 못한 에러 처리"""
        # 일반적인 Exception 발생하는 Mock
        class FailingMock(SAPApiMock):
            def post(self, target_system, endpoint, payload):
                raise RuntimeError("Unexpected database error")

        action_exec = ActionExecution(
            id="ae_error",
            action_id="test",
            entity_id="proj_001",
            domain_id="ai-voucher-2025",
            status="EXECUTED",
            requested_by="user@example.com",
            requested_at=datetime.utcnow()
        )
        db.add(action_exec)
        db.flush()

        wb = WriteBackQueue(
            id="wb_error",
            action_execution_id="ae_error",
            target_system="SAP",
            payload={"project_id": "proj_001"},
            status="PENDING"
        )
        db.add(wb)
        db.commit()

        failing_mock = FailingMock()
        worker = WriteBackWorker(db, failing_mock)

        result = worker.process_pending()

        # 첫 번째 시도에서 error로 인해 FAILED 상태
        db.refresh(wb)
        assert wb.status == "FAILED"
        assert "error" in wb.error_message.lower()
