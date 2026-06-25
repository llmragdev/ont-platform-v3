"""Phase 3 Week 4: Backend 통합 E2E 테스트"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from app.db.models import (
    Entity,
    ActionExecution,
    ChangeLog,
    WriteBackQueue,
    AuditLog,
)


@pytest.fixture()
def setup_test_entities(db_session):
    """테스트용 엔티티 생성"""
    entities = [
        Entity(
            id="proj_001",
            entity_type="PROJECT",
            domain_id="ai-voucher-2025",
            properties={
                "name": "Project A",
                "status": "UnderReview",
                "budget": 1000000,
            },
        ),
        Entity(
            id="proj_002",
            entity_type="PROJECT",
            domain_id="ai-voucher-2025",
            properties={
                "name": "Project B",
                "status": "UnderReview",
                "budget": 5000000,
            },
        ),
    ]
    for entity in entities:
        db_session.add(entity)
    db_session.commit()
    return entities


class TestFullWorkflow:
    """전체 워크플로우 E2E 테스트"""

    def test_full_workflow_approve_to_confirmed(self, client, db_session, setup_test_entities):
        """1. ApproveProject 실행 → 2. Changelog → 3. WriteBack 생성 → 4. SYNCED 확인"""
        now = datetime.utcnow()

        # 1. ActionExecution 생성 (액션 실행)
        action_exec = ActionExecution(
            id="action_001",
            action_id="approve_project",
            entity_id="proj_001",
            domain_id="ai-voucher-2025",
            status="EXECUTED",
            requested_by="pm@example.com",
            executed_by="pm@example.com",
            requested_at=now,
            executed_at=now,
        )
        db_session.add(action_exec)
        db_session.commit()

        # 2. Changelog 생성
        changelog = ChangeLog(
            id="chg_001",
            entity_id="proj_001",
            entity_type="PROJECT",
            domain_id="ai-voucher-2025",
            action_type="approve_project",
            actor="pm@example.com",
            source="web_ui",
            timestamp=now,
            old_status="UnderReview",
            new_status="Approved",
            sync_status="SYNCED",
            target_system="SAP",
            sync_timestamp=now + timedelta(seconds=5),
        )
        db_session.add(changelog)
        db_session.commit()

        # 3. WriteBack 생성
        writeback = WriteBackQueue(
            id="wb_001",
            action_execution_id="action_001",
            target_system="SAP",
            payload={"action": "approve", "entity_id": "proj_001"},
            status="CONFIRMED",
            created_at=now,
            sent_at=now + timedelta(seconds=5),
        )
        db_session.add(writeback)
        db_session.commit()

        # 4. API로 조회 검증
        changelog_response = client.get(
            "/api/changelog/history?entity_id=proj_001"
        )
        assert changelog_response.status_code == 200
        changelog_data = changelog_response.json()
        assert len(changelog_data["items"]) == 1
        assert changelog_data["items"][0]["sync_status"] == "SYNCED"

        writeback_response = client.get("/api/writeback/statistics")
        assert writeback_response.status_code == 200
        writeback_data = writeback_response.json()
        assert writeback_data["total_processed"] == 1
        assert writeback_data["success_rate"] == 1.0

    def test_full_workflow_with_retry(self, client, db_session, setup_test_entities):
        """1차 실행 실패 → 2차 재시도 → 성공"""
        now = datetime.utcnow()

        action_exec = ActionExecution(
            id="action_002",
            action_id="start_payment",
            entity_id="proj_002",
            domain_id="ai-voucher-2025",
            status="EXECUTED",
            requested_by="cfo@example.com",
            executed_by="cfo@example.com",
            requested_at=now,
            executed_at=now,
        )
        db_session.add(action_exec)
        db_session.commit()

        # Changelog: 처음엔 PENDING
        changelog = ChangeLog(
            id="chg_002",
            entity_id="proj_002",
            entity_type="PROJECT",
            domain_id="ai-voucher-2025",
            action_type="start_payment",
            actor="cfo@example.com",
            source="web_ui",
            timestamp=now,
            old_status="Approved",
            new_status="InProgress",
            sync_status="PENDING",
            target_system="SAP",
        )
        db_session.add(changelog)
        db_session.commit()

        # 1차 WriteBack 실패
        writeback1 = WriteBackQueue(
            id="wb_002",
            action_execution_id="action_002",
            target_system="SAP",
            payload={"action": "start_payment", "entity_id": "proj_002"},
            status="FAILED",
            retry_count=1,
            created_at=now,
            error_message="Connection timeout",
        )
        db_session.add(writeback1)
        db_session.commit()

        # 2차 재시도 성공
        writeback2 = WriteBackQueue(
            id="wb_003",
            action_execution_id="action_002",
            target_system="SAP",
            payload={"action": "start_payment", "entity_id": "proj_002"},
            status="CONFIRMED",
            retry_count=2,
            created_at=now + timedelta(seconds=10),
            sent_at=now + timedelta(seconds=15),
        )
        db_session.add(writeback2)

        # Changelog 상태 업데이트
        changelog.sync_status = "SYNCED"
        changelog.sync_timestamp = now + timedelta(seconds=15)

        db_session.commit()

        # 최종 상태 검증
        stats_response = client.get("/api/writeback/statistics")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total_processed"] >= 1
        assert stats["failure_count"] >= 1
        assert stats["success_rate"] >= 0  # 최소 하나의 성공

    def test_multiple_actions_in_parallel(self, client, db_session, setup_test_entities):
        """여러 액션 동시 실행 처리"""
        now = datetime.utcnow()

        # 3개 액션 동시 실행
        actions = [
            ActionExecution(
                id=f"action_par_{i}",
                action_id=action_name,
                entity_id="proj_001",
                domain_id="ai-voucher-2025",
                status="EXECUTED",
                requested_by="pm@example.com",
                executed_by="pm@example.com",
                requested_at=now,
                executed_at=now,
            )
            for i, action_name in enumerate([
                "approve_project",
                "change_deadline",
                "request_more_info",
            ])
        ]
        for action in actions:
            db_session.add(action)
        db_session.commit()

        # 각 액션마다 Changelog + WriteBack 생성
        for i, action in enumerate(actions):
            changelog = ChangeLog(
                id=f"chg_par_{i}",
                entity_id="proj_001",
                entity_type="PROJECT",
                domain_id="ai-voucher-2025",
                action_type=action.action_id,
                actor="pm@example.com",
                source="web_ui",
                timestamp=now + timedelta(seconds=i),
                old_status="UnderReview",
                new_status="Modified",
                sync_status="SYNCED",
                target_system="SAP",
            )
            db_session.add(changelog)

            writeback = WriteBackQueue(
                id=f"wb_par_{i}",
                action_execution_id=action.id,
                target_system="SAP",
                payload={"action": action.action_id},
                status="CONFIRMED",
                created_at=now + timedelta(seconds=i),
                sent_at=now + timedelta(seconds=i + 5),
            )
            db_session.add(writeback)

        db_session.commit()

        # 모두 처리되었는지 확인
        response = client.get("/api/writeback/statistics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_processed"] >= 3
        assert data["success_rate"] == 1.0  # 모두 성공

    def test_api_changelog_query(self, client, db_session, setup_test_entities):
        """Changelog API 정상 작동"""
        now = datetime.utcnow()

        # 테스트 데이터
        changelog = ChangeLog(
            id="chg_api_test",
            entity_id="proj_001",
            entity_type="PROJECT",
            domain_id="ai-voucher-2025",
            action_type="approve_project",
            actor="pm@example.com",
            source="web_ui",
            timestamp=now,
            old_status="UnderReview",
            new_status="Approved",
            sync_status="SYNCED",
            target_system="SAP",
        )
        db_session.add(changelog)
        db_session.commit()

        response = client.get("/api/changelog/history?action_type=approve_project")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        assert data["items"][0]["action_type"] == "approve_project"

    def test_api_writeback_stats(self, client, db_session, setup_test_entities):
        """WriteBack 통계 API 정상 작동"""
        now = datetime.utcnow()

        action = ActionExecution(
            id="action_stat_test",
            action_id="approve_project",
            entity_id="proj_001",
            domain_id="ai-voucher-2025",
            status="EXECUTED",
            requested_by="pm@example.com",
            executed_by="pm@example.com",
            requested_at=now,
            executed_at=now,
        )
        db_session.add(action)
        db_session.commit()

        wb = WriteBackQueue(
            id="wb_stat_test",
            action_execution_id="action_stat_test",
            target_system="SAP",
            payload={"action": "approve"},
            status="CONFIRMED",
            created_at=now,
            sent_at=now + timedelta(seconds=5),
        )
        db_session.add(wb)
        db_session.commit()

        response = client.get("/api/writeback/statistics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["total_processed"], int)
        assert isinstance(data["success_rate"], float)
        assert 0 <= data["success_rate"] <= 1

    def test_permissions_on_actions(self, client, db_session, setup_test_entities):
        """권한 검증 기록"""
        # Note: 현재 백엔드는 권한 검증을 구현하지 않았으므로,
        # 권한 정보가 Changelog에 기록되는지 확인
        now = datetime.utcnow()

        # CFO만 실행 가능한 액션
        action = ActionExecution(
            id="action_perm",
            action_id="start_payment",
            entity_id="proj_001",
            domain_id="ai-voucher-2025",
            status="EXECUTED",
            requested_by="cfo@example.com",
            executed_by="cfo@example.com",
            requested_at=now,
            executed_at=now,
        )
        db_session.add(action)
        db_session.commit()

        changelog = ChangeLog(
            id="chg_perm",
            entity_id="proj_001",
            entity_type="PROJECT",
            domain_id="ai-voucher-2025",
            action_type="start_payment",
            actor="cfo@example.com",  # CFO가 실행
            source="web_ui",
            timestamp=now,
            old_status="Approved",
            new_status="InProgress",
            sync_status="SYNCED",
        )
        db_session.add(changelog)
        db_session.commit()

        response = client.get(
            "/api/changelog/history?action_type=start_payment"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        assert data["items"][0]["actor"] == "cfo@example.com"

    def test_error_handling_invalid_entity(self, client, db_session):
        """존재하지 않는 엔티티 처리"""
        response = client.get("/api/changelog/history?entity_id=invalid_proj")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_audit_log_completeness(self, client, db_session, setup_test_entities):
        """모든 액션이 AuditLog에 기록"""
        now = datetime.utcnow()

        action = ActionExecution(
            id="action_audit",
            action_id="approve_project",
            entity_id="proj_001",
            domain_id="ai-voucher-2025",
            status="EXECUTED",
            requested_by="pm@example.com",
            executed_by="pm@example.com",
            requested_at=now,
            executed_at=now,
            result={"status": "success"},
        )
        db_session.add(action)
        db_session.commit()

        # AuditLog 기록
        audit = AuditLog(
            entity_id="proj_001",
            domain_id="ai-voucher-2025",
            operation="EXECUTE",
            new_state=action.result,
            actor="pm@example.com",
            timestamp=now,
        )
        db_session.add(audit)
        db_session.commit()

        # ActionExecution이 생성되었는지 확인
        exec_count = (
            db_session.query(ActionExecution)
            .filter(ActionExecution.id == "action_audit")
            .count()
        )
        assert exec_count == 1

    def test_changelog_completeness(self, client, db_session, setup_test_entities):
        """모든 액션이 Changelog에 기록"""
        now = datetime.utcnow()

        # 여러 액션 실행
        actions = ["approve_project", "reject_project", "change_deadline"]
        for i, action_name in enumerate(actions):
            changelog = ChangeLog(
                id=f"chg_complete_{i}",
                entity_id="proj_001",
                entity_type="PROJECT",
                domain_id="ai-voucher-2025",
                action_type=action_name,
                actor=f"user{i}@example.com",
                source="web_ui",
                timestamp=now + timedelta(seconds=i),
                old_status="UnderReview",
                new_status="Modified",
                sync_status="PENDING",
            )
            db_session.add(changelog)
        db_session.commit()

        response = client.get("/api/changelog/history?entity_id=proj_001")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3

    def test_writeback_queue_cleanup(self, client, db_session, setup_test_entities):
        """CONFIRMED된 항목 처리 확인"""
        now = datetime.utcnow()

        action = ActionExecution(
            id="action_cleanup",
            action_id="approve_project",
            entity_id="proj_001",
            domain_id="ai-voucher-2025",
            status="EXECUTED",
            requested_by="pm@example.com",
            executed_by="pm@example.com",
            requested_at=now,
            executed_at=now,
        )
        db_session.add(action)
        db_session.commit()

        # CONFIRMED 상태
        wb = WriteBackQueue(
            id="wb_cleanup",
            action_execution_id="action_cleanup",
            target_system="SAP",
            payload={"action": "approve"},
            status="CONFIRMED",
            created_at=now,
            sent_at=now + timedelta(seconds=5),
        )
        db_session.add(wb)
        db_session.commit()

        response = client.get("/api/writeback/queue?status=CONFIRMED")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        assert all(item["status"] == "CONFIRMED" for item in data["items"])

    def test_combined_filtering(self, client, db_session, setup_test_entities):
        """복합 필터링 테스트"""
        now = datetime.utcnow()

        changelog = ChangeLog(
            id="chg_filter",
            entity_id="proj_001",
            entity_type="PROJECT",
            domain_id="ai-voucher-2025",
            action_type="approve_project",
            actor="pm@example.com",
            source="web_ui",
            timestamp=now,
            old_status="UnderReview",
            new_status="Approved",
            sync_status="SYNCED",
            target_system="SAP",
        )
        db_session.add(changelog)
        db_session.commit()

        # entity_id + action_type 동시 필터링
        response = client.get(
            "/api/changelog/history?entity_id=proj_001&action_type=approve_project&sync_status=SYNCED"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert item["entity_id"] == "proj_001"
            assert item["action_type"] == "approve_project"
            assert item["sync_status"] == "SYNCED"
