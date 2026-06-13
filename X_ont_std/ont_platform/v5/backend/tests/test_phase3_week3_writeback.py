"""Phase 3 Week 3: WriteBack 통합 테스트"""
import sys
from pathlib import Path
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from datetime import datetime
from app.models.tenant_context import TenantContext
from app.models.changelog import (
    ChangelogEntry, WriteBackItem, SyncStatus, SAPWriteBackPayload
)
from app.repositories.changelog_repository import ChangelogRepository, WriteBackRepository
from app.services.sap_mock import SAPMockAPI, WriteBackSimulator
from app.services.writeback_worker import WriteBackWorker


@pytest.fixture
def tenant_context():
    """테스트용 테넌트 컨텍스트"""
    return TenantContext(
        user_id="user@nipa.go.kr",
        company_id="demo-co",
        project_id="proj-01",
        role="FinanceManager",
        permissions={}
    )


@pytest.fixture
def changelog_repo():
    """Changelog 저장소"""
    repo = ChangelogRepository()
    # 테스트 전에 저장소 정리
    import shutil
    if repo.base_path.exists():
        shutil.rmtree(repo.base_path)
    repo.base_path.mkdir(parents=True, exist_ok=True)
    yield repo
    # 테스트 후 정리
    if repo.base_path.exists():
        shutil.rmtree(repo.base_path)


@pytest.fixture
def writeback_repo():
    """WriteBack 저장소"""
    repo = WriteBackRepository()
    # 테스트 전에 저장소 정리
    import shutil
    if repo.base_path.exists():
        shutil.rmtree(repo.base_path)
    repo.base_path.mkdir(parents=True, exist_ok=True)
    yield repo
    # 테스트 후 정리
    if repo.base_path.exists():
        shutil.rmtree(repo.base_path)


@pytest.fixture
def sap_mock():
    """SAP Mock API"""
    return SAPMockAPI(success_rate=1.0)  # 테스트용: 100% 성공


class TestChangelogRepository:
    """Changelog 저장소 테스트"""

    def test_append_entry(self, changelog_repo, tenant_context):
        """로그 항목 추가"""
        entry = ChangelogEntry(
            changelog_id="cl-" + str(uuid.uuid4())[:8],
            entity_id="P001",
            entity_type="PROJECT",
            action="approve_project",
            old_value={"status": "UnderReview"},
            new_value={"status": "Approved"},
            performed_by="user@nipa.go.kr",
            performed_at=datetime.utcnow(),
            doc_id="ai-voucher-2025",
            domain_id="ai-voucher-2025"
        )

        changelog_repo.append_entry(tenant_context, entry)

        # 조회 검증
        entries = changelog_repo.get_entries(tenant_context, "ai-voucher-2025")
        assert len(entries) > 0
        assert entries[-1].changelog_id == entry.changelog_id

    def test_get_pending_entries(self, changelog_repo, tenant_context):
        """대기 중인 항목 조회"""
        # PENDING 항목 추가
        entry = ChangelogEntry(
            changelog_id="cl-pending-1",
            entity_id="P001",
            entity_type="PROJECT",
            action="approve_project",
            old_value={},
            new_value={"status": "Approved"},
            performed_by="user@nipa.go.kr",
            performed_at=datetime.utcnow(),
            doc_id="ai-voucher-2025",
            domain_id="ai-voucher-2025",
            sync_status=SyncStatus.PENDING
        )

        changelog_repo.append_entry(tenant_context, entry)
        pending = changelog_repo.get_pending_entries(tenant_context, "ai-voucher-2025")

        assert len(pending) > 0
        assert any(e.changelog_id == "cl-pending-1" for e in pending)

    def test_update_entry_status(self, changelog_repo, tenant_context):
        """로그 항목 상태 업데이트"""
        entry = ChangelogEntry(
            changelog_id="cl-update-test",
            entity_id="P001",
            entity_type="PROJECT",
            action="approve_project",
            old_value={},
            new_value={},
            performed_by="user@nipa.go.kr",
            performed_at=datetime.utcnow(),
            doc_id="ai-voucher-2025",
            domain_id="ai-voucher-2025"
        )

        changelog_repo.append_entry(tenant_context, entry)

        # 상태 업데이트
        success = changelog_repo.update_entry_status(
            tenant_context,
            "cl-update-test",
            SyncStatus.SYNCED,
            datetime.utcnow()
        )

        assert success is True


class TestWriteBackRepository:
    """WriteBack 저장소 테스트"""

    def test_enqueue_item(self, writeback_repo):
        """큐 항목 추가"""
        item = WriteBackItem(
            write_back_id="wb-" + str(uuid.uuid4())[:8],
            changelog_id="cl-001",
            target_system="SAP",
            entity_id="P001",
            action="approve_project",
            payload={
                "action": "approve",
                "entity_type": "PROJECT",
                "properties": {"status": "Approved"}
            },
            created_at=datetime.utcnow()
        )

        writeback_repo.enqueue(item)

        # 조회 검증
        items = writeback_repo.get_all_items("SAP")
        assert len(items) > 0
        assert any(i.write_back_id == item.write_back_id for i in items)

    def test_get_pending_items(self, writeback_repo):
        """대기 중인 항목 조회"""
        item = WriteBackItem(
            write_back_id="wb-pending-1",
            changelog_id="cl-002",
            target_system="SAP",
            entity_id="P002",
            action="start_payment",
            payload={"action": "start_payment"},
            status=SyncStatus.PENDING,
            created_at=datetime.utcnow()
        )

        writeback_repo.enqueue(item)
        pending = writeback_repo.get_pending_items("SAP")

        assert len(pending) > 0
        assert any(i.write_back_id == "wb-pending-1" for i in pending)

    def test_update_item_status(self, writeback_repo):
        """큐 항목 상태 업데이트"""
        item = WriteBackItem(
            write_back_id="wb-update-1",
            changelog_id="cl-003",
            target_system="SAP",
            entity_id="P003",
            action="complete_project",
            payload={},
            created_at=datetime.utcnow()
        )

        writeback_repo.enqueue(item)

        success = writeback_repo.update_item_status("wb-update-1", SyncStatus.SYNCED)
        assert success is True

        # 상태 확인
        items = writeback_repo.get_all_items("SAP")
        updated_item = next((i for i in items if i.write_back_id == "wb-update-1"), None)
        assert updated_item.status == SyncStatus.SYNCED


class TestSAPMockAPI:
    """SAP Mock API 테스트"""

    def test_sync_project_success(self, sap_mock):
        """프로젝트 동기화 성공"""
        payload = SAPWriteBackPayload(
            action="approve",
            entity_id="P001",
            entity_type="PROJECT",
            properties={"status": "Approved"}
        )

        result = sap_mock.sync_project(payload)

        assert result.success is True
        assert result.status == SyncStatus.SYNCED
        assert result.response_data is not None

    def test_sap_call_history(self, sap_mock):
        """호출 기록 확인"""
        payload1 = SAPWriteBackPayload(
            action="approve",
            entity_id="P001",
            entity_type="PROJECT",
            properties={}
        )
        payload2 = SAPWriteBackPayload(
            action="complete",
            entity_id="P002",
            entity_type="PROJECT",
            properties={}
        )

        sap_mock.sync_project(payload1)
        sap_mock.sync_project(payload2)

        history = sap_mock.get_call_history()
        assert len(history) >= 2


class TestWriteBackSimulator:
    """WriteBack 시뮬레이터 테스트"""

    def test_simulate_success(self):
        """성공 시뮬레이션"""
        result = WriteBackSimulator.simulate_success()
        assert result.success is True
        assert result.status == SyncStatus.SYNCED

    def test_simulate_temporary_failure(self):
        """임시 실패 시뮬레이션"""
        result = WriteBackSimulator.simulate_temporary_failure()
        assert result.success is False
        assert result.status == SyncStatus.FAILED

    def test_simulate_permanent_failure(self):
        """영구 실패 시뮬레이션"""
        result = WriteBackSimulator.simulate_permanent_failure()
        assert result.success is False


class TestWriteBackWorker:
    """WriteBack 워커 테스트"""

    def test_worker_initialization(self):
        """워커 초기화"""
        worker = WriteBackWorker(interval_seconds=1)
        assert worker.interval_seconds == 1
        assert worker.running is False

    def test_worker_start_stop(self):
        """워커 시작 및 중지"""
        worker = WriteBackWorker(interval_seconds=1)

        worker.start()
        assert worker.running is True

        time.sleep(0.5)  # 워커 실행 확인

        worker.stop()
        assert worker.running is False

    def test_worker_stats(self):
        """워커 통계 조회"""
        worker = WriteBackWorker(interval_seconds=1)

        stats = worker.get_stats()
        assert "processed" in stats
        assert "succeeded" in stats
        assert "failed" in stats
        assert stats["processed"] == 0


class TestWriteBackIntegration:
    """WriteBack 통합 테스트"""

    def test_full_writeback_flow(self, changelog_repo, writeback_repo, tenant_context):
        """전체 WriteBack 흐름"""
        # 1. Changelog 항목 생성
        changelog_entry = ChangelogEntry(
            changelog_id="cl-flow-1",
            entity_id="P001",
            entity_type="PROJECT",
            action="approve_project",
            old_value={},
            new_value={"status": "Approved"},
            performed_by="user@nipa.go.kr",
            performed_at=datetime.utcnow(),
            doc_id="ai-voucher-2025",
            domain_id="ai-voucher-2025"
        )

        changelog_repo.append_entry(tenant_context, changelog_entry)

        # 2. WriteBack 큐 항목 생성
        writeback_item = WriteBackItem(
            write_back_id="wb-flow-1",
            changelog_id="cl-flow-1",
            target_system="SAP",
            entity_id="P001",
            action="approve_project",
            payload={
                "action": "approve",
                "entity_type": "PROJECT",
                "properties": {"status": "Approved"}
            },
            created_at=datetime.utcnow()
        )

        writeback_repo.enqueue(writeback_item)

        # 3. 상태 확인
        pending_items = writeback_repo.get_pending_items("SAP")
        assert len(pending_items) > 0
        assert pending_items[0].write_back_id == "wb-flow-1"

        # 4. 상태 업데이트
        writeback_repo.update_item_status("wb-flow-1", SyncStatus.SYNCED)

        # 5. 최종 확인
        items = writeback_repo.get_all_items("SAP")
        final_item = next((i for i in items if i.write_back_id == "wb-flow-1"), None)
        assert final_item.status == SyncStatus.SYNCED


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
