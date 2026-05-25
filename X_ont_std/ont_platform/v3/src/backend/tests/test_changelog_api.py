"""Tests for the Changelog API endpoint."""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from app.db.models import ChangeLog, Entity


def test_changelog_list_all(client, db_session):
    # Create a sample entity
    entity = Entity(
        id="test_proj_chg",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        properties={"status": "UnderReview"}
    )
    db_session.add(entity)
    db_session.commit()

    # Insert test changelogs
    changelog1 = ChangeLog(
        id=f"chg_{uuid.uuid4().hex[:12]}",
        entity_id="test_proj_chg",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        action_type="APPROVE_PROJECT",
        actor="test_user@nipa.go.kr",
        source="api",
        timestamp=datetime.utcnow() - timedelta(minutes=5),
        sync_status="SYNCED"
    )
    changelog2 = ChangeLog(
        id=f"chg_{uuid.uuid4().hex[:12]}",
        entity_id="test_proj_chg",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        action_type="REJECT_PROJECT",
        actor="test_user@nipa.go.kr",
        source="api",
        timestamp=datetime.utcnow(),
        sync_status="FAILED",
        error_message="SAP Timeout"
    )
    db_session.add_all([changelog1, changelog2])
    db_session.commit()

    response = client.get("/api/changelog/history?entity_id=test_proj_chg")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] == 2
    
    items = data["items"]
    assert items[0]["action_type"] == "REJECT_PROJECT"
    assert items[1]["action_type"] == "APPROVE_PROJECT"


def test_changelog_filter_by_entity(client, db_session):
    entity = Entity(
        id="test_proj_chg",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        properties={"status": "UnderReview"}
    )
    db_session.add(entity)
    db_session.commit()

    changelog = ChangeLog(
        id=f"chg_{uuid.uuid4().hex[:12]}",
        entity_id="test_proj_chg",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        action_type="APPROVE_PROJECT",
        actor="test_user@nipa.go.kr",
        source="api",
        timestamp=datetime.utcnow(),
        sync_status="SYNCED"
    )
    db_session.add(changelog)
    db_session.commit()

    response = client.get("/api/changelog/history?entity_id=test_proj_chg")
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["entity_id"] == "test_proj_chg"


def test_changelog_filter_by_status(client, db_session):
    entity = Entity(
        id="test_proj_chg",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        properties={"status": "UnderReview"}
    )
    db_session.add(entity)
    db_session.commit()

    changelog = ChangeLog(
        id=f"chg_{uuid.uuid4().hex[:12]}",
        entity_id="test_proj_chg",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        action_type="APPROVE_PROJECT",
        actor="test_user@nipa.go.kr",
        source="api",
        timestamp=datetime.utcnow(),
        sync_status="FAILED"
    )
    db_session.add(changelog)
    db_session.commit()

    response = client.get("/api/changelog/history?entity_id=test_proj_chg&sync_status=FAILED")
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["sync_status"] == "FAILED"


def test_changelog_date_range(client, db_session):
    entity = Entity(
        id="test_proj_chg",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        properties={"status": "UnderReview"}
    )
    db_session.add(entity)
    db_session.commit()

    now = datetime.utcnow()
    changelog = ChangeLog(
        id=f"chg_{uuid.uuid4().hex[:12]}",
        entity_id="test_proj_chg",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        action_type="APPROVE_PROJECT",
        actor="test_user@nipa.go.kr",
        source="api",
        timestamp=now,
        sync_status="SYNCED"
    )
    db_session.add(changelog)
    db_session.commit()

    date_from = (now - timedelta(hours=1)).isoformat() + "Z"
    date_to = (now + timedelta(hours=1)).isoformat() + "Z"

    response = client.get(f"/api/changelog/history?entity_id=test_proj_chg&date_from={date_from}&date_to={date_to}")
    data = response.json()
    assert len(data["items"]) == 1


def test_changelog_pagination(client, db_session):
    entity = Entity(
        id="test_proj_chg",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        properties={"status": "UnderReview"}
    )
    db_session.add(entity)
    db_session.commit()

    for i in range(5):
        changelog = ChangeLog(
            id=f"chg_{uuid.uuid4().hex[:12]}",
            entity_id="test_proj_chg",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type=f"ACTION_{i}",
            actor="test_user@nipa.go.kr",
            source="api",
            timestamp=datetime.utcnow() - timedelta(minutes=i),
            sync_status="SYNCED"
        )
        db_session.add(changelog)
    db_session.commit()

    response = client.get("/api/changelog/history?entity_id=test_proj_chg&page=1&page_size=2")
    data = response.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
