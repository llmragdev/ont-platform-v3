"""Changelog 모델 및 서비스 테스트"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.models import Base, Entity, ChangeLog
from app.services.changelog_service import ChangeLogService


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
def test_entity(db: Session):
    """테스트용 엔티티"""
    entity = Entity(
        id="proj_001",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        properties={
            "name": "Test Project",
            "status": "UnderReview",
            "budget": 5000000
        }
    )
    db.add(entity)
    db.commit()
    return entity


class TestChangeLogModel:
    """ChangeLog 모델 테스트"""

    def test_changelog_creation(self, db: Session, test_entity):
        """Test 1: Changelog 레코드 생성"""
        changelog = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="APPROVE_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Approved",
            source="api",
            target_system="SAP"
        )
        db.commit()

        assert changelog.id is not None
        assert changelog.entity_id == "proj_001"
        assert changelog.action_type == "APPROVE_PROJECT"
        assert changelog.actor == "pm@example.com"
        assert changelog.sync_status == "PENDING"

    def test_changelog_old_new_status(self, db: Session, test_entity):
        """Test 2: 상태 변화 기록"""
        changelog = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="REJECT_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Rejected"
        )
        db.commit()

        assert changelog.old_status == "UnderReview"
        assert changelog.new_status == "Rejected"

    def test_changelog_mark_synced(self, db: Session, test_entity):
        """Test 3: Changelog을 SYNCED로 표시"""
        changelog = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="APPROVE_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Approved"
        )
        db.commit()

        ChangeLogService.mark_synced(db, changelog.id)

        updated = db.query(ChangeLog).filter(ChangeLog.id == changelog.id).first()
        assert updated.sync_status == "SYNCED"
        assert updated.sync_timestamp is not None

    def test_changelog_mark_failed(self, db: Session, test_entity):
        """Test 4: Changelog을 FAILED로 표시"""
        changelog = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="APPROVE_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Approved"
        )
        db.commit()

        ChangeLogService.mark_failed(db, changelog.id, "SAP API timeout", retry_count=1)

        updated = db.query(ChangeLog).filter(ChangeLog.id == changelog.id).first()
        assert updated.sync_status == "FAILED"
        assert updated.error_message == "SAP API timeout"
        assert updated.retry_count == 1

    def test_changelog_increment_retry(self, db: Session, test_entity):
        """Test 5: 재시도 횟수 증가"""
        changelog = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="APPROVE_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Approved"
        )
        db.commit()

        ChangeLogService.increment_retry(db, changelog.id)
        updated1 = db.query(ChangeLog).filter(ChangeLog.id == changelog.id).first()
        assert updated1.retry_count == 1

        ChangeLogService.increment_retry(db, changelog.id)
        updated2 = db.query(ChangeLog).filter(ChangeLog.id == changelog.id).first()
        assert updated2.retry_count == 2

    def test_get_pending_changes(self, db: Session, test_entity):
        """Test 6: PENDING 상태의 changelog 조회"""
        cl1 = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="APPROVE_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Approved"
        )
        cl2 = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_002",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="REJECT_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Rejected"
        )
        db.commit()

        ChangeLogService.mark_synced(db, cl1.id)

        pending = ChangeLogService.get_pending_changes(db, "ai-voucher-2025")
        assert len(pending) == 1
        assert pending[0].id == cl2.id

    def test_get_change_history(self, db: Session, test_entity):
        """Test 7: 특정 엔티티의 변경 이력 조회"""
        import time

        cl1 = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="APPROVE_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Approved"
        )
        db.commit()

        time.sleep(0.01)  # 약간의 시간 간격

        cl2 = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="START_PAYMENT",
            actor="cfo@example.com",
            old_status="Approved",
            new_status="PaymentStarted"
        )
        db.commit()

        history = ChangeLogService.get_change_history(db, "proj_001")
        assert len(history) == 2
        # 최신순이므로 cl2가 먼저
        assert history[0].id == cl2.id
        assert history[1].id == cl1.id

    def test_changelog_timestamp_auto_set(self, db: Session, test_entity):
        """Test 8: timestamp 자동 설정"""
        before = datetime.utcnow()

        changelog = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="APPROVE_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Approved"
        )
        db.commit()

        after = datetime.utcnow()

        assert before <= changelog.timestamp <= after

    def test_changelog_jsonl_file_created(self, db: Session, test_entity):
        """Test 9: JSONL 파일에 저장됨"""
        import os

        changelog = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="APPROVE_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Approved"
        )
        db.commit()

        file_path = "storage/demo-co/proj-01/changelog/ai-voucher-2025_changes.jsonl"
        assert os.path.exists(file_path)

        with open(file_path, "r") as f:
            content = f.read()
            assert changelog.id in content
            assert "APPROVE_PROJECT" in content
