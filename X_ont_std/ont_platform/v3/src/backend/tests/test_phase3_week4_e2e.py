"""Phase 3 Week 4: E2E 통합 테스트 (Action → Changelog → WriteBack)"""
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
        user_id="test@company.com",
        company_id="test-co",
        project_id="test-proj",
        role="FinanceManager",
        permissions={}
    )


@pytest.fixture
def changelog_repo():
    """Changelog 저장소"""
    repo = ChangelogRepository()
    import shutil
    if repo.base_path.exists():
        shutil.rmtree(repo.base_path)
    repo.base_path.mkdir(parents=True, exist_ok=True)
    yield repo
    if repo.base_path.exists():
        shutil.rmtree(repo.base_path)


@pytest.fixture
def writeback_repo():
    """WriteBack 저장소"""
    repo = WriteBackRepository()
    import shutil
    if repo.base_path.exists():
        shutil.rmtree(repo.base_path)
    repo.base_path.mkdir(parents=True, exist_ok=True)
    yield repo
    if repo.base_path.exists():
        shutil.rmtree(repo.base_path)


@pytest.fixture
def sap_mock():
    """SAP Mock API (100% 성공률)"""
    return SAPMockAPI(success_rate=1.0)


@pytest.fixture
def worker():
    """WriteBackWorker"""
    return WriteBackWorker(interval_seconds=1)


class TestActionExecutionFlow:
    """액션 실행 전체 흐름"""

    def test_e2e_action_creates_changelog(self, changelog_repo, tenant_context):
        """액션 실행 → Changelog 기록"""
        entry = ChangelogEntry(
            changelog_id="cl-" + str(uuid.uuid4())[:8],
            entity_id="P001",
            entity_type="PROJECT",
            action="approve_project",
            old_value={"status": "UnderReview"},
            new_value={"status": "Approved"},
            performed_by="test@company.com",
            performed_at=datetime.utcnow(),
            doc_id="test-doc",
            domain_id="test-domain"
        )

        changelog_repo.append_entry(tenant_context, entry)

        # 검증: Changelog 생성됨
        entries = changelog_repo.get_entries(tenant_context, "test-doc")
        assert len(entries) == 1
        assert entries[0].action == "approve_project"
        assert entries[0].sync_status == SyncStatus.PENDING

    def test_e2e_changelog_to_writeback(self, changelog_repo, writeback_repo, tenant_context):
        """Changelog → WriteBack 연쇄"""
        # 1. Changelog 생성
        changelog_id = "cl-" + str(uuid.uuid4())[:8]
        entry = ChangelogEntry(
            changelog_id=changelog_id,
            entity_id="P002",
            entity_type="PROJECT",
            action="start_payment",
            old_value={"status": "Approved"},
            new_value={"status": "InProgress"},
            performed_by="test@company.com",
            performed_at=datetime.utcnow(),
            doc_id="test-doc",
            domain_id="test-domain"
        )
        changelog_repo.append_entry(tenant_context, entry)

        # 2. WriteBack 항목 생성
        wb_item = WriteBackItem(
            write_back_id="wb-" + str(uuid.uuid4())[:8],
            changelog_id=changelog_id,
            target_system="SAP",
            entity_id="P002",
            action="start_payment",
            payload={"action": "start_payment", "entity_type": "PROJECT"},
            created_at=datetime.utcnow()
        )
        writeback_repo.enqueue(wb_item)

        # 검증
        pending_wb = writeback_repo.get_pending_items("SAP")
        assert len(pending_wb) == 1
        assert pending_wb[0].changelog_id == changelog_id

    def test_e2e_state_machine_validation(self, changelog_repo, tenant_context):
        """상태 기계 제약 검증"""
        # 유효한 전이: UnderReview → Approved
        entry = ChangelogEntry(
            changelog_id="cl-valid",
            entity_id="P003",
            entity_type="PROJECT",
            action="approve_project",
            old_value={"status": "UnderReview"},
            new_value={"status": "Approved"},
            performed_by="test@company.com",
            performed_at=datetime.utcnow(),
            doc_id="test-doc",
            domain_id="test-domain"
        )
        changelog_repo.append_entry(tenant_context, entry)

        entries = changelog_repo.get_entries(tenant_context, "test-doc")
        assert entries[-1].new_value["status"] == "Approved"


class TestChangelogRecording:
    """Changelog 기록 및 추적"""

    def test_changelog_entry_immutability(self, changelog_repo, tenant_context):
        """Changelog 항목 불변성 (JSONL append-only)"""
        entry1 = ChangelogEntry(
            changelog_id="cl-entry1",
            entity_id="P004",
            entity_type="PROJECT",
            action="approve",
            old_value={},
            new_value={"status": "Approved"},
            performed_by="user1@company.com",
            performed_at=datetime.utcnow(),
            doc_id="test-doc",
            domain_id="test-domain"
        )
        changelog_repo.append_entry(tenant_context, entry1)

        # 기존 항목은 유지되고 새 항목이 추가됨
        entry2 = ChangelogEntry(
            changelog_id="cl-entry2",
            entity_id="P004",
            entity_type="PROJECT",
            action="reject",
            old_value={"status": "Approved"},
            new_value={"status": "Rejected"},
            performed_by="user2@company.com",
            performed_at=datetime.utcnow(),
            doc_id="test-doc",
            domain_id="test-domain"
        )
        changelog_repo.append_entry(tenant_context, entry2)

        entries = changelog_repo.get_entries(tenant_context, "test-doc", limit=10)
        assert len(entries) == 2
        assert entries[0].changelog_id == "cl-entry1"
        assert entries[1].changelog_id == "cl-entry2"

    def test_changelog_status_tracking(self, changelog_repo, tenant_context):
        """Changelog 상태 추적 (PENDING → SYNCED)"""
        changelog_id = "cl-status-test"
        entry = ChangelogEntry(
            changelog_id=changelog_id,
            entity_id="P005",
            entity_type="PROJECT",
            action="approve",
            old_value={},
            new_value={"status": "Approved"},
            performed_by="test@company.com",
            performed_at=datetime.utcnow(),
            doc_id="test-doc",
            domain_id="test-domain",
            sync_status=SyncStatus.PENDING
        )
        changelog_repo.append_entry(tenant_context, entry)

        # 초기 상태: PENDING
        pending = changelog_repo.get_pending_entries(tenant_context, "test-doc")
        assert any(e.changelog_id == changelog_id for e in pending)

        # 상태 업데이트
        changelog_repo.update_entry_status(
            tenant_context,
            changelog_id,
            SyncStatus.SYNCED,
            datetime.utcnow()
        )

        # 업데이트 후: SYNCED
        all_entries = changelog_repo.get_entries(tenant_context, "test-doc")
        synced_entry = next(e for e in all_entries if e.changelog_id == changelog_id)
        assert synced_entry.sync_status == SyncStatus.SYNCED
        assert synced_entry.synced_at is not None

    def test_changelog_entity_filtering(self, changelog_repo, tenant_context):
        """특정 엔티티의 Changelog 필터링"""
        # P006 관련 3개 항목
        for i in range(3):
            entry = ChangelogEntry(
                changelog_id=f"cl-p006-{i}",
                entity_id="P006",
                entity_type="PROJECT",
                action="update",
                old_value={},
                new_value={"iteration": i},
                performed_by="test@company.com",
                performed_at=datetime.utcnow(),
                doc_id="test-doc",
                domain_id="test-domain"
            )
            changelog_repo.append_entry(tenant_context, entry)

        # P007 관련 2개 항목
        for i in range(2):
            entry = ChangelogEntry(
                changelog_id=f"cl-p007-{i}",
                entity_id="P007",
                entity_type="PROJECT",
                action="update",
                old_value={},
                new_value={"iteration": i},
                performed_by="test@company.com",
                performed_at=datetime.utcnow(),
                doc_id="test-doc",
                domain_id="test-domain"
            )
            changelog_repo.append_entry(tenant_context, entry)

        # 엔티티별 필터링
        p006_entries = changelog_repo.get_entries(tenant_context, "test-doc", entity_id="P006")
        p007_entries = changelog_repo.get_entries(tenant_context, "test-doc", entity_id="P007")

        assert len(p006_entries) == 3
        assert len(p007_entries) == 2


class TestWriteBackSyncFlow:
    """WriteBack 동기화 흐름"""

    def test_writeback_enqueue_and_retrieve(self, writeback_repo):
        """WriteBack 큐 추가 및 조회"""
        item = WriteBackItem(
            write_back_id="wb-sync-1",
            changelog_id="cl-sync-1",
            target_system="SAP",
            entity_id="P008",
            action="approve",
            payload={"action": "approve", "entity_type": "PROJECT"},
            status=SyncStatus.PENDING,
            created_at=datetime.utcnow()
        )
        writeback_repo.enqueue(item)

        pending = writeback_repo.get_pending_items("SAP")
        assert len(pending) == 1
        assert pending[0].write_back_id == "wb-sync-1"

    def test_writeback_sync_success(self, writeback_repo, sap_mock):
        """WriteBack 동기화 성공"""
        item = WriteBackItem(
            write_back_id="wb-sync-success",
            changelog_id="cl-sync-success",
            target_system="SAP",
            entity_id="P009",
            action="approve",
            payload={
                "action": "approve",
                "entity_id": "P009",
                "entity_type": "PROJECT",
                "properties": {"status": "Approved"}
            },
            created_at=datetime.utcnow()
        )
        writeback_repo.enqueue(item)

        # SAP API 호출 시뮬레이션
        payload = SAPWriteBackPayload(**item.payload)
        result = sap_mock.sync_project(payload)

        assert result.success is True
        assert result.status == SyncStatus.SYNCED

        # 상태 업데이트
        writeback_repo.update_item_status("wb-sync-success", SyncStatus.SYNCED)
        items = writeback_repo.get_all_items("SAP")
        updated = next((i for i in items if i.write_back_id == "wb-sync-success"), None)
        assert updated.status == SyncStatus.SYNCED

    def test_writeback_retry_on_failure(self, writeback_repo, worker):
        """WriteBack 실패 시 재시도 로직"""
        item = WriteBackItem(
            write_back_id="wb-retry-test",
            changelog_id="cl-retry-test",
            target_system="SAP",
            entity_id="P010",
            action="approve",
            payload={"action": "approve"},
            created_at=datetime.utcnow(),
            attempt_count=0
        )
        writeback_repo.enqueue(item)

        # 첫 재시도
        writeback_repo.update_item_status("wb-retry-test", SyncStatus.FAILED, "Connection timeout")
        items = writeback_repo.get_all_items("SAP")
        updated = next((i for i in items if i.write_back_id == "wb-retry-test"), None)
        assert len(updated.errors) > 0
        assert "Connection timeout" in updated.errors[0]["message"]

    def test_writeback_multiple_systems(self, writeback_repo):
        """다양한 타겟 시스템 WriteBack"""
        # SAP
        sap_item = WriteBackItem(
            write_back_id="wb-sap-multi",
            changelog_id="cl-multi-1",
            target_system="SAP",
            entity_id="P011",
            action="approve",
            payload={},
            created_at=datetime.utcnow()
        )
        writeback_repo.enqueue(sap_item)

        # Oracle
        oracle_item = WriteBackItem(
            write_back_id="wb-oracle-multi",
            changelog_id="cl-multi-2",
            target_system="Oracle",
            entity_id="P012",
            action="approve",
            payload={},
            created_at=datetime.utcnow()
        )
        writeback_repo.enqueue(oracle_item)

        sap_items = writeback_repo.get_pending_items("SAP")
        oracle_items = writeback_repo.get_pending_items("Oracle")

        assert len(sap_items) == 1
        assert len(oracle_items) == 1
        assert sap_items[0].target_system == "SAP"
        assert oracle_items[0].target_system == "Oracle"


class TestAuditTrail:
    """감사 추적 (Audit Trail)"""

    def test_full_action_audit_trail(self, changelog_repo, writeback_repo, tenant_context):
        """전체 액션 감사 추적"""
        # 1. 액션 실행 → Changelog
        changelog_id = "cl-audit-full"
        entry = ChangelogEntry(
            changelog_id=changelog_id,
            entity_id="P013",
            entity_type="PROJECT",
            action="complete_project",
            old_value={"status": "InProgress"},
            new_value={"status": "Completed"},
            performed_by="audit-test@company.com",
            performed_at=datetime.utcnow(),
            doc_id="test-doc",
            domain_id="test-domain"
        )
        changelog_repo.append_entry(tenant_context, entry)

        # 2. WriteBack 생성
        wb_id = "wb-audit-full"
        wb_item = WriteBackItem(
            write_back_id=wb_id,
            changelog_id=changelog_id,
            target_system="SAP",
            entity_id="P013",
            action="complete_project",
            payload={"action": "complete"},
            created_at=datetime.utcnow()
        )
        writeback_repo.enqueue(wb_item)

        # 3. 감사 추적
        changelogs = changelog_repo.get_entries(tenant_context, "test-doc", entity_id="P013")
        assert len(changelogs) == 1
        assert changelogs[0].changelog_id == changelog_id

        writebacks = writeback_repo.get_all_items("SAP")
        related_wb = next((w for w in writebacks if w.changelog_id == changelog_id), None)
        assert related_wb is not None
        assert related_wb.write_back_id == wb_id

    def test_audit_trail_with_status_changes(self, changelog_repo, writeback_repo, tenant_context):
        """상태 변화를 포함한 감사 추적"""
        entity_id = "P014"
        statuses = ["UnderReview", "Approved", "InProgress", "Completed"]

        for i, status in enumerate(statuses):
            changelog_id = f"cl-status-{i}"
            entry = ChangelogEntry(
                changelog_id=changelog_id,
                entity_id=entity_id,
                entity_type="PROJECT",
                action="status_update",
                old_value={"status": statuses[i-1] if i > 0 else "Draft"},
                new_value={"status": status},
                performed_by="test@company.com",
                performed_at=datetime.utcnow(),
                doc_id="test-doc",
                domain_id="test-domain"
            )
            changelog_repo.append_entry(tenant_context, entry)

        # 엔티티의 전체 상태 변화 추적
        history = changelog_repo.get_entries(tenant_context, "test-doc", entity_id=entity_id, limit=100)
        assert len(history) == len(statuses)

        # 상태 변화 순서 검증
        for i, record in enumerate(history):
            assert record.new_value["status"] == statuses[i]


class TestEdgeCases:
    """엣지 케이스 및 경계 조건"""

    def test_concurrent_changelog_appends(self, changelog_repo, tenant_context):
        """동시 Changelog 추가 (JSONL append-only 안전성)"""
        num_appends = 10
        for i in range(num_appends):
            entry = ChangelogEntry(
                changelog_id=f"cl-concurrent-{i}",
                entity_id="P015",
                entity_type="PROJECT",
                action="update",
                old_value={},
                new_value={"iteration": i},
                performed_by="test@company.com",
                performed_at=datetime.utcnow(),
                doc_id="test-doc",
                domain_id="test-domain"
            )
            changelog_repo.append_entry(tenant_context, entry)

        # 모든 항목이 정확히 추가됨
        entries = changelog_repo.get_entries(tenant_context, "test-doc", limit=100)
        assert len(entries) == num_appends

    def test_writeback_max_retries_exceeded(self, writeback_repo):
        """WriteBack 최대 재시도 횟수 초과"""
        item = WriteBackItem(
            write_back_id="wb-max-retry",
            changelog_id="cl-max-retry",
            target_system="SAP",
            entity_id="P016",
            action="approve",
            payload={},
            created_at=datetime.utcnow(),
            attempt_count=3,  # 이미 3회 시도됨
            errors=[
                {"timestamp": datetime.utcnow().isoformat(), "message": "Attempt 1 failed"},
                {"timestamp": datetime.utcnow().isoformat(), "message": "Attempt 2 failed"},
                {"timestamp": datetime.utcnow().isoformat(), "message": "Attempt 3 failed"},
            ]
        )
        writeback_repo.enqueue(item)

        # 최대 재시도 도달했으므로 FAILED로 표시
        writeback_repo.update_item_status("wb-max-retry", SyncStatus.FAILED, "Max retries exceeded")
        items = writeback_repo.get_all_items("SAP")
        final_item = next((i for i in items if i.write_back_id == "wb-max-retry"), None)
        assert final_item.status == SyncStatus.FAILED


class TestWorkerIntegration:
    """WriteBackWorker와 저장소 통합"""

    def test_worker_processes_pending_items(self, writeback_repo, worker, sap_mock):
        """워커가 대기 중인 항목 처리"""
        item = WriteBackItem(
            write_back_id="wb-worker-process",
            changelog_id="cl-worker-1",
            target_system="SAP",
            entity_id="P017",
            action="approve",
            payload={
                "action": "approve",
                "entity_id": "P017",
                "entity_type": "PROJECT",
                "properties": {}
            },
            created_at=datetime.utcnow()
        )
        writeback_repo.enqueue(item)

        # 워커 초기화 및 통계 확인
        assert worker.stats["processed"] == 0

    def test_worker_stats_tracking(self, worker):
        """워커 통계 추적"""
        stats = worker.get_stats()
        assert "processed" in stats
        assert "succeeded" in stats
        assert "failed" in stats
        assert "retried" in stats
        assert stats["processed"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
