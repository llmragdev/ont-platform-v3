"""Phase 3 Week 2: API 통합 테스트 (15개)"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.models import Base, Entity
from app.db.database import get_db


# 테스트용 인메모리 SQLite DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

# DB 테이블 생성 (module load 시)
Base.metadata.create_all(bind=engine)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Global session for tests
_session = None

def get_test_session():
    global _session
    if _session is None:
        _session = TestingSessionLocal()
    return _session

def override_get_db():
    """모든 요청에서 테스트 DB 사용"""
    db = get_test_session()
    try:
        yield db
    finally:
        pass  # Don't close immediately

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_db():
    """각 테스트 후 데이터베이스 정리"""
    yield
    # Clean up after test
    db = get_test_session()
    db.rollback()
    # Delete all entities to start fresh
    db.query(Entity).delete()
    db.commit()


class TestPermissionCheckAPI:
    """권한 확인 API 테스트 (4개)"""

    def test_permission_check_pm_approve_project(self):
        """Test 1: GET /api/actions/approve_project/permission-check — PM 권한"""
        response = client.get(
            "/api/actions/approve_project/permission-check",
            params={"user_role": "PM"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is True
        assert data["action_id"] == "approve_project"
        assert data["user_role"] == "PM"

    def test_permission_check_user_cannot_approve(self):
        """Test 2: GET /api/actions/approve_project/permission-check — USER 권한 거부"""
        response = client.get(
            "/api/actions/approve_project/permission-check",
            params={"user_role": "USER"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is False
        assert "not allowed" in data["reason"].lower()

    def test_permission_check_cfo_1m_amount(self):
        """Test 3: GET /api/actions/start_payment/permission-check — 금액 기반 권한 (CFO 100만원)"""
        response = client.get(
            "/api/actions/start_payment/permission-check",
            params={"user_role": "CFO", "amount": 1000000}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is True

    def test_permission_check_cfo_cannot_10m(self):
        """Test 4: GET /api/actions/start_payment/permission-check — CEO만 1000만원 이상"""
        response = client.get(
            "/api/actions/start_payment/permission-check",
            params={"user_role": "CFO", "amount": 10000000}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is False


class TestAvailableActionsAPI:
    """사용 가능 액션 조회 API 테스트 (2개)"""

    def test_available_actions_pm_role(self):
        """Test 5: GET /api/actions/available — PM 역할 액션 목록"""
        response = client.get(
            "/api/actions/available",
            params={"user_role": "PM"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_role"] == "PM"
        assert "available_actions" in data
        assert len(data["available_actions"]) > 0

    def test_available_actions_ceo_role(self):
        """Test 6: GET /api/actions/available — CEO 역할 액션 목록"""
        response = client.get(
            "/api/actions/available",
            params={"user_role": "CEO"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_role"] == "CEO"
        assert "available_actions" in data
        assert len(data["available_actions"]) >= 5


class TestActionExecutionSuccess:
    """액션 실행 성공 케이스 (4개)"""

    def setup_method(self):
        """각 테스트 전에 엔티티 생성"""
        db = get_test_session()
        entity = Entity(
            id="proj_test",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            properties={
                "name": "Test Project",
                "status": "UnderReview",
                "budget": 5000000,
                "deadline": "2026-12-31"
            }
        )
        db.add(entity)
        db.commit()

    def test_execute_approve_project_success(self):
        """Test 7: POST /api/actions/approve_project/execute — 성공"""
        response = client.post(
            "/api/actions/approve_project/execute",
            params={"user_role": "PM"},
            json={
                "entity_id": "proj_test",
                "approver": "pm@example.com"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["new_status"] == "Approved"

    def test_execute_reject_project_success(self):
        """Test 8: POST /api/actions/reject_project/execute — 성공"""
        response = client.post(
            "/api/actions/reject_project/execute",
            params={"user_role": "PM"},
            json={
                "entity_id": "proj_test",
                "reason": "Budget issues",
                "rejected_by": "pm@example.com"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["new_status"] == "Rejected"

    def test_execute_change_deadline_success(self):
        """Test 9: POST /api/actions/change_deadline/execute — 성공"""
        response = client.post(
            "/api/actions/change_deadline/execute",
            params={"user_role": "PM"},
            json={
                "entity_id": "proj_test",
                "new_deadline": "2026-06-30T23:59:59Z",
                "changed_by": "pm@example.com"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["new_deadline"] == "2026-06-30T23:59:59Z"

    def test_execute_start_payment_cfo_success(self):
        """Test 10: POST /api/actions/start_payment/execute — CFO 권한 OK"""
        db = get_test_session()
        # Update status to Approved first
        entity = db.query(Entity).filter(Entity.id == "proj_test").first()
        entity.properties["status"] = "Approved"
        db.commit()

        response = client.post(
            "/api/actions/start_payment/execute",
            params={"user_role": "CFO"},
            json={
                "entity_id": "proj_test",
                "amount": 1500000,
                "approved_by": "cfo@example.com"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["amount"] == 1500000


class TestActionExecutionFailure:
    """액션 실행 실패 케이스 (3개)"""

    def setup_method(self):
        """각 테스트 전에 엔티티 생성"""
        db = get_test_session()
        entity = Entity(
            id="proj_test",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            properties={
                "name": "Test Project",
                "status": "UnderReview",
                "budget": 5000000,
                "deadline": "2026-12-31"
            }
        )
        db.add(entity)
        db.commit()

    def test_execute_start_payment_amount_exceeded(self):
        """Test 11: POST /api/actions/start_payment/execute — 금액 초과 거부"""
        response = client.post(
            "/api/actions/start_payment/execute",
            params={"user_role": "ACCOUNTANT"},
            json={
                "entity_id": "proj_test",
                "amount": 5000000,
                "approved_by": "accountant@example.com"
            }
        )
        assert response.status_code == 403

    def test_execute_complete_project_wrong_status(self):
        """Test 12: POST /api/actions/complete_project/execute — 잘못된 상태 전이 실패"""
        response = client.post(
            "/api/actions/complete_project/execute",
            params={"user_role": "PM"},
            json={
                "entity_id": "proj_test",
                "completed_by": "pm@example.com"
            }
        )
        assert response.status_code == 400

    def test_execute_action_insufficient_permission(self):
        """Test 13: Error: 권한 부족"""
        response = client.post(
            "/api/actions/approve_project/execute",
            params={"user_role": "ACCOUNTANT"},
            json={
                "entity_id": "proj_test",
                "approver": "accountant@example.com"
            }
        )
        assert response.status_code == 403


class TestErrorHandling:
    """에러 처리 테스트 (2개)"""

    def test_error_nonexistent_entity(self):
        """Test 14: Error: 존재하지 않는 엔티티"""
        response = client.post(
            "/api/actions/approve_project/execute",
            params={"user_role": "PM"},
            json={
                "entity_id": "nonexistent_proj",
                "approver": "pm@example.com"
            }
        )
        assert response.status_code == 400

    def test_error_missing_required_field(self):
        """Test 15: Error: 필수 필드 누락"""
        response = client.post(
            "/api/actions/approve_project/execute",
            params={"user_role": "PM"},
            json={
                "approver": "pm@example.com"
            }
        )
        assert response.status_code == 400
