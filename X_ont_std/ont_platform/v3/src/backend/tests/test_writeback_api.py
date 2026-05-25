"""Tests for the Writeback API endpoints."""
import sys
from pathlib import Path
from datetime import datetime
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from app.db.models import WriteBackQueue, ActionExecution, Entity


def test_writeback_queue_list(client, db_session):
    # Create sample entity
    entity = Entity(
        id="test_proj_wb",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        properties={"status": "UnderReview"}
    )
    db_session.add(entity)
    db_session.commit()

    # Create action execution and writeback queue items
    ae_id = f"ae_{uuid.uuid4().hex[:8]}"
    ae = ActionExecution(
        id=ae_id,
        action_id="approve_project",
        entity_id="test_proj_wb",
        domain_id="ai-voucher-2025",
        status="EXECUTED",
        requested_by="test_user@nipa.go.kr",
        requested_at=datetime.utcnow()
    )
    db_session.add(ae)
    db_session.commit()

    wb = WriteBackQueue(
        id=f"wb_{uuid.uuid4().hex[:8]}",
        action_execution_id=ae_id,
        target_system="SAP",
        payload={"project_id": "test_proj_wb"},
        status="PENDING",
        created_at=datetime.utcnow()
    )
    db_session.add(wb)
    db_session.commit()

    response = client.get("/api/writeback/queue?domain_id=ai-voucher-2025")
    assert response.status_code == 200
    data = response.json()
    assert data["pending"] == 1
    assert data["confirmed"] == 0
    assert data["failed"] == 0
    assert len(data["items"]) == 1
    assert data["items"][0]["action_execution_id"] == ae_id


def test_writeback_filter_by_status(client, db_session):
    entity = Entity(
        id="test_proj_wb",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        properties={"status": "UnderReview"}
    )
    db_session.add(entity)
    db_session.commit()

    ae_id = f"ae_{uuid.uuid4().hex[:8]}"
    ae = ActionExecution(
        id=ae_id,
        action_id="approve_project",
        entity_id="test_proj_wb",
        domain_id="ai-voucher-2025",
        status="EXECUTED",
        requested_by="test_user@nipa.go.kr",
        requested_at=datetime.utcnow()
    )
    db_session.add(ae)
    db_session.commit()

    wb1 = WriteBackQueue(
        id=f"wb_{uuid.uuid4().hex[:8]}",
        action_execution_id=ae_id,
        target_system="SAP",
        payload={},
        status="CONFIRMED",
        created_at=datetime.utcnow()
    )
    wb2 = WriteBackQueue(
        id=f"wb_{uuid.uuid4().hex[:8]}",
        action_execution_id=ae_id,
        target_system="SAP",
        payload={},
        status="FAILED",
        created_at=datetime.utcnow()
    )
    db_session.add_all([wb1, wb2])
    db_session.commit()

    response = client.get("/api/writeback/queue?status=CONFIRMED")
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "CONFIRMED"


def test_writeback_statistics(client, db_session):
    entity = Entity(
        id="test_proj_wb",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        properties={"status": "UnderReview"}
    )
    db_session.add(entity)
    db_session.commit()

    ae_id = f"ae_{uuid.uuid4().hex[:8]}"
    ae = ActionExecution(
        id=ae_id,
        action_id="approve_project",
        entity_id="test_proj_wb",
        domain_id="ai-voucher-2025",
        status="EXECUTED",
        requested_by="test_user@nipa.go.kr",
        requested_at=datetime.utcnow()
    )
    db_session.add(ae)
    db_session.commit()

    wb1 = WriteBackQueue(
        id=f"wb_{uuid.uuid4().hex[:8]}",
        action_execution_id=ae_id,
        target_system="SAP",
        payload={},
        status="CONFIRMED",
        created_at=datetime.utcnow()
    )
    wb2 = WriteBackQueue(
        id=f"wb_{uuid.uuid4().hex[:8]}",
        action_execution_id=ae_id,
        target_system="SAP",
        payload={},
        status="FAILED",
        created_at=datetime.utcnow()
    )
    db_session.add_all([wb1, wb2])
    db_session.commit()

    response = client.get("/api/writeback/statistics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_processed"] == 2
    assert data["success_rate"] == 0.5
    assert data["failure_count"] == 1
    assert data["avg_retry_attempts"] == 0.0
