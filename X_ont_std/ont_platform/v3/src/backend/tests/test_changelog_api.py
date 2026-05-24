"""Phase 3 Week 4: Changelog API 테스트"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from app.db.models import ChangeLog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def setup_changelog_data(db_session):
    """테스트용 Changelog 데이터 생성"""
    now = datetime.utcnow()

    changelogs = [
        ChangeLog(
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
        ),
        ChangeLog(
            id="chg_002",
            entity_id="proj_002",
            entity_type="PROJECT",
            domain_id="ai-voucher-2025",
            action_type="reject_project",
            actor="reviewer@example.com",
            source="web_ui",
            timestamp=now + timedelta(minutes=1),
            old_status="UnderReview",
            new_status="Rejected",
            sync_status="PENDING",
            target_system="SAP",
        ),
        ChangeLog(
            id="chg_003",
            entity_id="proj_001",
            entity_type="PROJECT",
            domain_id="ai-voucher-2025",
            action_type="change_deadline",
            actor="pm@example.com",
            source="web_ui",
            timestamp=now + timedelta(minutes=2),
            old_status="Approved",
            new_status="Approved",
            sync_status="FAILED",
            target_system="SAP",
            error_message="Connection timeout",
        ),
        ChangeLog(
            id="chg_004",
            entity_id="proj_003",
            entity_type="PROJECT",
            domain_id="order-2025",
            action_type="start_payment",
            actor="cfo@example.com",
            source="web_ui",
            timestamp=now + timedelta(minutes=3),
            old_status="Approved",
            new_status="InProgress",
            sync_status="SYNCED",
            target_system="SAP",
        ),
    ]

    for changelog in changelogs:
        db_session.add(changelog)
    db_session.commit()
    return changelogs


class TestChangelogAPI:
    """Changelog 조회 API 테스트"""

    def test_changelog_list_all(self, client, setup_changelog_data):
        """모든 changelog 조회"""
        response = client.get("/api/changelog/history")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert len(data["items"]) == 4
        assert data["page"] == 1
        assert data["page_size"] == 50

    def test_changelog_filter_by_entity(self, client, setup_changelog_data):
        """entity_id로 필터링"""
        response = client.get("/api/changelog/history?entity_id=proj_001")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert all(item["entity_id"] == "proj_001" for item in data["items"])

    def test_changelog_filter_by_action_type(self, client, setup_changelog_data):
        """action_type으로 필터링"""
        response = client.get("/api/changelog/history?action_type=approve_project")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["action_type"] == "approve_project"

    def test_changelog_filter_by_sync_status(self, client, setup_changelog_data):
        """sync_status로 필터링"""
        response = client.get("/api/changelog/history?sync_status=SYNCED")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(item["sync_status"] == "SYNCED" for item in data["items"])

    def test_changelog_filter_by_domain(self, client, setup_changelog_data):
        """domain_id로 필터링"""
        response = client.get("/api/changelog/history?domain_id=order-2025")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["domain_id"] == "order-2025"

    def test_changelog_date_range(self, client, setup_changelog_data):
        """날짜 범위로 필터링"""
        now = datetime.utcnow()
        date_from = (now - timedelta(minutes=5)).isoformat()
        date_to = (now + timedelta(minutes=1, seconds=30)).isoformat()

        response = client.get(
            f"/api/changelog/history?date_from={date_from}&date_to={date_to}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_changelog_pagination(self, client, setup_changelog_data):
        """페이징 정상 작동"""
        # 페이지 1: 2개
        response1 = client.get("/api/changelog/history?page=1&page_size=2")
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["items"]) == 2
        assert data1["page"] == 1
        assert data1["total"] == 4

        # 페이지 2: 2개
        response2 = client.get("/api/changelog/history?page=2&page_size=2")
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["items"]) == 2
        assert data2["page"] == 2

        # 페이지 3: 0개
        response3 = client.get("/api/changelog/history?page=3&page_size=2")
        assert response3.status_code == 200
        data3 = response3.json()
        assert len(data3["items"]) == 0

    def test_changelog_timestamp_desc_order(self, client, setup_changelog_data):
        """timestamp 역순 정렬"""
        response = client.get("/api/changelog/history")
        assert response.status_code == 200
        data = response.json()
        items = data["items"]

        # 타임스탐프가 내림차순인지 확인
        timestamps = [
            datetime.fromisoformat(item["timestamp"]) for item in items
        ]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_changelog_response_fields(self, client, setup_changelog_data):
        """응답 필드 검증"""
        response = client.get("/api/changelog/history?page=1&page_size=1")
        assert response.status_code == 200
        data = response.json()
        item = data["items"][0]

        # 필수 필드 확인
        assert "id" in item
        assert "entity_id" in item
        assert "entity_type" in item
        assert "domain_id" in item
        assert "action_type" in item
        assert "actor" in item
        assert "old_status" in item
        assert "new_status" in item
        assert "timestamp" in item
        assert "sync_status" in item
        assert "target_system" in item
        assert "sync_timestamp" in item
        assert "error_message" in item
