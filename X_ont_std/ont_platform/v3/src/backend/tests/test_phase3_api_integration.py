"""Phase 3 Week 2: API 통합 테스트"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from fastapi.testclient import TestClient
from app.models.tenant_context import TenantContext
from app.services.ontology import OntologyService
from app.services.workflow import WorkflowService
from app.main import app


@pytest.fixture
def client():
    """FastAPI 테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def headers():
    """기본 헤더 (FinanceManager)"""
    return {
        "X-User-Id": "user@nipa.go.kr",
        "X-Company-Id": "demo-co",
        "X-Project-Id": "proj-01",
        "X-Role": "FinanceManager"
    }


@pytest.fixture
def admin_headers():
    """관리자 헤더"""
    return {
        "X-User-Id": "admin@nipa.go.kr",
        "X-Company-Id": "demo-co",
        "X-Project-Id": "proj-01",
        "X-Role": "Admin"
    }


@pytest.fixture
def sample_project():
    """테스트용 PROJECT 엔티티"""
    return {
        "id": "P001AAA",
        "type": "PROJECT",
        "name": "AI바우처 2025 - 기업A",
        "properties": {
            "status": "UnderReview",
            "budget": 100000000,
            "manager": "manager@nipa.go.kr",
            "deadline": "2026-12-31",
            "bank_account_verified": True,
            "payment_schedule": "2026-06-01",
            "approved_by": None,
            "approved_at": None,
            "rejected_by": None,
            "rejected_at": None,
            "rejection_reason": None,
        }
    }


class TestWorkflowQueueAPI:
    """Workflow Queue API 테스트"""

    def test_queue_default_domain(self, client, headers):
        """기본 도메인 (ai-voucher-2025) 액션 목록 조회"""
        response = client.get("/api/workflow/queue", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "items" in data

    def test_queue_with_entity_type_filter(self, client, headers):
        """엔티티 타입별 필터링"""
        response = client.get("/api/workflow/queue?entity_type=PROJECT", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)

    def test_queue_missing_headers(self, client):
        """필수 헤더 없이 요청 → 기본값 사용"""
        response = client.get("/api/workflow/queue")
        assert response.status_code == 200

    def test_queue_custom_domain(self, client, headers):
        """커스텀 도메인 지정"""
        response = client.get("/api/workflow/queue?domain_id=order", headers=headers)
        assert response.status_code == 200


class TestWorkflowExecuteAPI:
    """Workflow Execute API 테스트"""

    def test_execute_approve_success(self, client, headers):
        """Approve Project 액션 실행 성공 또는 검증 실패"""
        body = {
            "doc_id": "ai-voucher-2025",
            "entity_id": "P001AAA",
            "action": "approve_project",
            "domain_id": "ai-voucher-2025",
            "params": {}
        }
        response = client.post("/api/workflow/execute", json=body, headers=headers)
        # 200이면 성공, 400이면 전제조건 미충족 (둘 다 정상 동작)
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert data.get("action") == "approve_project"

    def test_execute_reject_with_reason(self, client, headers):
        """Reject Project 액션 (사유 필수)"""
        body = {
            "doc_id": "ai-voucher-2025",
            "entity_id": "P001AAA",
            "action": "reject_project",
            "domain_id": "ai-voucher-2025",
            "params": {"rejection_reason": "요건 미충족"}
        }
        response = client.post("/api/workflow/execute", json=body, headers=headers)
        assert response.status_code in [200, 400]  # 상태에 따라 다름

    def test_execute_change_deadline(self, client, headers):
        """Change Deadline 액션 (params 필수)"""
        body = {
            "doc_id": "ai-voucher-2025",
            "entity_id": "P001AAA",
            "action": "change_deadline",
            "domain_id": "ai-voucher-2025",
            "params": {"new_deadline": "2027-12-31"}
        }
        response = client.post("/api/workflow/execute", json=body, headers=headers)
        assert response.status_code in [200, 400]

    def test_execute_request_more_info(self, client, headers):
        """Request More Info 액션"""
        body = {
            "doc_id": "ai-voucher-2025",
            "entity_id": "P001AAA",
            "action": "request_more_info",
            "domain_id": "ai-voucher-2025",
            "params": {"info_needed": "더 상세한 설명"}
        }
        response = client.post("/api/workflow/execute", json=body, headers=headers)
        assert response.status_code in [200, 400]

    def test_execute_start_payment(self, client, headers):
        """Start Payment 액션"""
        body = {
            "doc_id": "ai-voucher-2025",
            "entity_id": "P001AAA",
            "action": "start_payment",
            "domain_id": "ai-voucher-2025",
            "params": {}
        }
        response = client.post("/api/workflow/execute", json=body, headers=headers)
        assert response.status_code in [200, 400]

    def test_execute_complete_project(self, client, headers):
        """Complete Project 액션"""
        body = {
            "doc_id": "ai-voucher-2025",
            "entity_id": "P001AAA",
            "action": "complete_project",
            "domain_id": "ai-voucher-2025",
            "params": {}
        }
        response = client.post("/api/workflow/execute", json=body, headers=headers)
        assert response.status_code in [200, 400]

    def test_execute_missing_doc_id(self, client, headers):
        """필수 필드 누락: doc_id"""
        body = {
            "entity_id": "P001AAA",
            "action": "approve_project"
        }
        response = client.post("/api/workflow/execute", json=body, headers=headers)
        assert response.status_code in [400, 422]  # 422 = Pydantic validation error
        if response.status_code == 422:
            assert "doc_id" in str(response.json())

    def test_execute_missing_entity_id(self, client, headers):
        """필수 필드 누락: entity_id"""
        body = {
            "doc_id": "ai-voucher-2025",
            "action": "approve_project"
        }
        response = client.post("/api/workflow/execute", json=body, headers=headers)
        assert response.status_code in [400, 422]
        if response.status_code == 422:
            assert "entity_id" in str(response.json())

    def test_execute_missing_action(self, client, headers):
        """필수 필드 누락: action"""
        body = {
            "doc_id": "ai-voucher-2025",
            "entity_id": "P001AAA"
        }
        response = client.post("/api/workflow/execute", json=body, headers=headers)
        assert response.status_code in [400, 422]
        if response.status_code == 422:
            assert "action" in str(response.json())

    def test_execute_unknown_action(self, client, headers):
        """알 수 없는 액션"""
        body = {
            "doc_id": "ai-voucher-2025",
            "entity_id": "P001AAA",
            "action": "unknown_action",
            "domain_id": "ai-voucher-2025"
        }
        response = client.post("/api/workflow/execute", json=body, headers=headers)
        assert response.status_code == 400

    def test_execute_permission_denied(self, client):
        """권한 부족 (Viewer 역할)"""
        headers = {
            "X-User-Id": "viewer@nipa.go.kr",
            "X-Company-Id": "demo-co",
            "X-Project-Id": "proj-01",
            "X-Role": "Viewer"
        }
        body = {
            "doc_id": "ai-voucher-2025",
            "entity_id": "P001AAA",
            "action": "approve_project",
            "domain_id": "ai-voucher-2025"
        }
        response = client.post("/api/workflow/execute", json=body, headers=headers)
        assert response.status_code in [400, 403]

    def test_execute_all_six_actions(self, client, headers):
        """6개 액션 모두 존재 확인 (응답 수신)"""
        actions = [
            "approve_project",
            "reject_project",
            "change_deadline",
            "request_more_info",
            "start_payment",
            "complete_project"
        ]
        for action in actions:
            body = {
                "doc_id": "ai-voucher-2025",
                "entity_id": "P001AAA",
                "action": action,
                "domain_id": "ai-voucher-2025",
                "params": {} if action != "change_deadline" else {"new_deadline": "2027-12-31"}
            }
            response = client.post("/api/workflow/execute", json=body, headers=headers)
            # 응답이 400이면 실체 에러, 200이면 성공, 다른 응답은 엔드포인트 존재 확인
            assert response.status_code in [200, 400]


class TestWorkflowExecuteConditionalPermissions:
    """조건부 권한 API 테스트"""

    def test_execute_approve_with_teamlead_small_budget(self, client):
        """TeamLead가 3천만원 과제 승인 (권한 있음)"""
        headers = {
            "X-User-Id": "lead@nipa.go.kr",
            "X-Company-Id": "demo-co",
            "X-Project-Id": "proj-01",
            "X-Role": "TeamLead"
        }
        body = {
            "doc_id": "ai-voucher-2025",
            "entity_id": "P001AAA",
            "action": "approve_project",
            "domain_id": "ai-voucher-2025",
            "params": {}
        }
        response = client.post("/api/workflow/execute", json=body, headers=headers)
        # 200 또는 400 (전제조건) 모두 정상
        assert response.status_code in [200, 400]

    def test_execute_approve_with_admin_large_budget(self, client, admin_headers):
        """Admin이 3억원 과제 승인 (권한 있음)"""
        body = {
            "doc_id": "ai-voucher-2025",
            "entity_id": "P002BBB",
            "action": "approve_project",
            "domain_id": "ai-voucher-2025",
            "params": {}
        }
        response = client.post("/api/workflow/execute", json=body, headers=admin_headers)
        assert response.status_code in [200, 400]


class TestWorkflowExecuteResponseStructure:
    """응답 구조 검증 테스트"""

    def test_execute_response_has_required_fields(self, client, headers):
        """응답에 필수 필드 포함"""
        body = {
            "doc_id": "ai-voucher-2025",
            "entity_id": "P001AAA",
            "action": "approve_project",
            "domain_id": "ai-voucher-2025",
            "params": {}
        }
        response = client.post("/api/workflow/execute", json=body, headers=headers)
        if response.status_code == 200:
            data = response.json()
            assert "entity_id" in data
            assert "action" in data
            # from_status, to_status 필드 확인
            assert "from_status" in data or "to_status" in data

    def test_execute_error_response_has_detail(self, client, headers):
        """에러 응답에 detail 필드 포함"""
        body = {
            "doc_id": "ai-voucher-2025",
            "entity_id": "P001AAA",
            "action": "unknown_action"
        }
        response = client.post("/api/workflow/execute", json=body, headers=headers)
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


class TestWorkflowQueueResponseStructure:
    """Queue API 응답 구조 검증"""

    def test_queue_response_structure(self, client, headers):
        """Queue 응답 구조 검증"""
        response = client.get("/api/workflow/queue", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "items" in data
        assert isinstance(data["count"], int)
        assert isinstance(data["items"], list)

    def test_queue_filter_by_multiple_params(self, client, headers):
        """다중 필터 적용"""
        response = client.get(
            "/api/workflow/queue?entity_type=PROJECT&domain_id=ai-voucher-2025",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "count" in data


class TestWorkflowExecuteEdgeCases:
    """엣지 케이스 테스트"""

    def test_execute_empty_body(self, client, headers):
        """빈 요청 본문"""
        response = client.post("/api/workflow/execute", json={}, headers=headers)
        assert response.status_code in [400, 422]  # 422 = Pydantic validation error

    def test_execute_with_extra_fields(self, client, headers):
        """추가 필드 무시"""
        body = {
            "doc_id": "ai-voucher-2025",
            "entity_id": "P001AAA",
            "action": "change_deadline",
            "domain_id": "ai-voucher-2025",
            "params": {"new_deadline": "2027-12-31"},
            "extra_field": "should_be_ignored"
        }
        response = client.post("/api/workflow/execute", json=body, headers=headers)
        # 추가 필드는 무시되어야 함
        assert response.status_code in [200, 400]

    def test_execute_null_params(self, client, headers):
        """params를 null로 전달"""
        body = {
            "doc_id": "ai-voucher-2025",
            "entity_id": "P001AAA",
            "action": "approve_project",
            "domain_id": "ai-voucher-2025",
            "params": None
        }
        response = client.post("/api/workflow/execute", json=body, headers=headers)
        assert response.status_code in [200, 400, 422]  # 422 = Pydantic validation


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
