"""Phase 3 Week 4: WriteBack API 테스트"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from app.db.models import WriteBackQueue, ActionExecution, Entity


@pytest.fixture()
def setup_writeback_data(db_session):
    """테스트용 WriteBack 데이터 생성"""
    now = datetime.utcnow()

    # Entity 생성 (FK 제약 때문에)
    entity = Entity(
        id="proj_001",
        entity_type="PROJECT",
        domain_id="ai-voucher-2025",
        properties={"name": "Test Project"},
    )
    db_session.add(entity)
    db_session.commit()

    # ActionExecution 생성
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

    # WriteBackQueue 항목들
    writebacks = [
        WriteBackQueue(
            id="wb_001",
            action_execution_id="action_001",
            target_system="SAP",
            payload={"action": "approve", "entity_id": "proj_001"},
            status="CONFIRMED",
            retry_count=0,
            created_at=now,
            sent_at=now + timedelta(seconds=5),
        ),
        WriteBackQueue(
            id="wb_002",
            action_execution_id="action_001",
            target_system="SAP",
            payload={"action": "approve", "entity_id": "proj_002"},
            status="PENDING",
            retry_count=0,
            created_at=now + timedelta(seconds=10),
        ),
        WriteBackQueue(
            id="wb_003",
            action_execution_id="action_001",
            target_system="SAP",
            payload={"action": "approve", "entity_id": "proj_003"},
            status="CONFIRMED",
            retry_count=1,
            created_at=now + timedelta(seconds=20),
            sent_at=now + timedelta(seconds=30),
        ),
        WriteBackQueue(
            id="wb_004",
            action_execution_id="action_001",
            target_system="SAP",
            payload={"action": "approve", "entity_id": "proj_004"},
            status="FAILED",
            retry_count=3,
            created_at=now + timedelta(seconds=40),
            error_message="Connection refused",
        ),
        WriteBackQueue(
            id="wb_005",
            action_execution_id="action_001",
            target_system="SAP",
            payload={"action": "approve", "entity_id": "proj_005"},
            status="PENDING",
            retry_count=1,
            created_at=now + timedelta(seconds=50),
        ),
    ]

    for wb in writebacks:
        db_session.add(wb)
    db_session.commit()
    return writebacks


class TestWritebackAPI:
    """WriteBack 상태 조회 API 테스트"""

    def test_writeback_queue_list(self, client, setup_writeback_data):
        """큐 상태 조회"""
        response = client.get("/api/writeback/queue")
        assert response.status_code == 200
        data = response.json()

        # 상태 별 개수 확인
        assert data["pending"] == 2  # wb_002, wb_005
        assert data["confirmed"] == 2  # wb_001, wb_003
        assert data["failed"] == 1  # wb_004

        # 항목 반환 확인
        assert len(data["items"]) <= 100
        assert "id" in data["items"][0]
        assert "action_execution_id" in data["items"][0]
        assert "target_system" in data["items"][0]
        assert "status" in data["items"][0]

    def test_writeback_filter_by_status(self, client, setup_writeback_data):
        """상태별 필터링"""
        # PENDING 상태만
        response = client.get("/api/writeback/queue?status=PENDING")
        assert response.status_code == 200
        data = response.json()
        assert data["pending"] == 2
        assert all(item["status"] == "PENDING" for item in data["items"])

        # CONFIRMED 상태만
        response = client.get("/api/writeback/queue?status=CONFIRMED")
        assert response.status_code == 200
        data = response.json()
        assert all(item["status"] == "CONFIRMED" for item in data["items"])

        # FAILED 상태만
        response = client.get("/api/writeback/queue?status=FAILED")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert all(item["status"] == "FAILED" for item in data["items"])

    def test_writeback_statistics(self, client, setup_writeback_data):
        """통계 조회"""
        response = client.get("/api/writeback/statistics")
        assert response.status_code == 200
        data = response.json()

        # 통계 필드 확인
        assert "total_processed" in data
        assert "success_rate" in data
        assert "failure_count" in data
        assert "pending_count" in data
        assert "avg_retry_attempts" in data
        assert "last_sync_time" in data

        # 값 검증
        assert data["total_processed"] == 5
        assert data["failure_count"] == 1  # wb_004
        assert data["pending_count"] == 2  # wb_002, wb_005

    def test_writeback_success_rate(self, client, setup_writeback_data):
        """성공률 계산 정확성"""
        response = client.get("/api/writeback/statistics")
        assert response.status_code == 200
        data = response.json()

        # 성공률: confirmed / total = 2 / 5 = 0.4
        expected_rate = 0.4
        assert data["success_rate"] == round(expected_rate, 4)

    def test_writeback_avg_retry(self, client, setup_writeback_data):
        """평균 재시도 횟수"""
        response = client.get("/api/writeback/statistics")
        assert response.status_code == 200
        data = response.json()

        # 평균: (0 + 0 + 1 + 3 + 1) / 5 = 1.0
        expected_avg = 1.0
        assert data["avg_retry_attempts"] == round(expected_avg, 2)

    def test_writeback_last_sync_time(self, client, setup_writeback_data):
        """마지막 동기화 시간"""
        response = client.get("/api/writeback/statistics")
        assert response.status_code == 200
        data = response.json()

        # last_sync_time은 가장 최근의 CONFIRMED 항목의 sent_at
        assert data["last_sync_time"] is not None
        # ISO 형식인지 확인
        assert "T" in data["last_sync_time"]

    def test_writeback_queue_with_limit(self, client, setup_writeback_data):
        """limit 파라미터 테스트"""
        response = client.get("/api/writeback/queue?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2

    def test_writeback_response_fields(self, client, setup_writeback_data):
        """응답 필드 검증"""
        response = client.get("/api/writeback/queue?limit=1")
        assert response.status_code == 200
        data = response.json()
        item = data["items"][0]

        # 필수 필드
        assert "id" in item
        assert "action_execution_id" in item
        assert "target_system" in item
        assert "status" in item
        assert "retry_count" in item
        assert "created_at" in item
        assert "sent_at" in item
        assert "error_message" in item
