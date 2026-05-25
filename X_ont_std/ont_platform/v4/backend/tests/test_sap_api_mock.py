"""SAP API Mock 테스트"""
import pytest
from app.services.sap_api_mock import (
    SAPApiMock,
    NotificationApiMock,
    SAPApiMockFactory,
    MockResponseStatus,
)


class TestSAPApiMock:
    """SAP API Mock 테스트"""

    @pytest.fixture
    def sap_mock(self):
        """테스트용 SAP Mock 객체"""
        return SAPApiMock(success_rate=1.0)  # 테스트용 100% 성공

    def test_successful_sap_post(self, sap_mock):
        """Test 1: SAP API 성공 응답"""
        payload = {
            "project_id": "proj_001",
            "action": "APPROVE",
            "approver": "pm@example.com",
        }

        response = sap_mock.post("SAP", "/sap/project/approve", payload)

        assert response["status"] == "ok"
        assert response["sync_id"] is not None
        assert response["project_id"] == "proj_001"
        assert response["action"] == "APPROVE"
        assert "sap_reference" in response
        assert "timestamp" in response

    def test_sap_post_with_different_actions(self, sap_mock):
        """Test 2: 다양한 액션 처리"""
        actions = [
            ("APPROVE", "approve"),
            ("REJECT", "reject"),
            ("CHANGE_DEADLINE", "change_deadline"),
            ("COMPLETE", "complete"),
        ]

        for action, endpoint in actions:
            payload = {"project_id": f"proj_{action}", "action": action}
            response = sap_mock.post("SAP", endpoint, payload)

            assert response["status"] == "ok"
            assert response["action"] == action
            assert response["project_id"] == f"proj_{action}"

    def test_notification_api_success(self):
        """Test 3: Notification API는 항상 성공"""
        mock = NotificationApiMock()
        payload = {
            "project_id": "proj_001",
            "info_needed": "Additional budget details",
        }

        response = mock.post("NOTIFICATION", "/notify/info_request", payload)

        assert response["status"] == "ok"
        assert response["notification_id"] is not None
        assert response["type"] == "info_request"

    def test_timeout_simulation(self):
        """Test 4: 타임아웃 시뮬레이션 (10% 실패율)"""
        mock = SAPApiMock(success_rate=0.0)  # 100% 실패
        payload = {"project_id": "proj_001", "action": "APPROVE"}

        with pytest.raises(TimeoutError) as exc_info:
            mock.post("SAP", "/sap/project/approve", payload)

        assert "timeout" in str(exc_info.value).lower()

    def test_call_history_tracking(self, sap_mock):
        """Test 5: 호출 기록 추적"""
        payload1 = {"project_id": "proj_001", "action": "APPROVE"}
        payload2 = {"project_id": "proj_002", "action": "REJECT"}

        sap_mock.post("SAP", "/sap/project/approve", payload1)
        sap_mock.post("SAP", "/sap/project/reject", payload2)

        history = sap_mock.get_call_history()

        assert len(history) == 2
        assert history[0]["payload"]["project_id"] == "proj_001"
        assert history[1]["payload"]["project_id"] == "proj_002"
        assert history[0]["status"] == MockResponseStatus.SUCCESS
        assert history[1]["status"] == MockResponseStatus.SUCCESS

    def test_call_count_by_system(self, sap_mock):
        """Test 6: 시스템별 호출 횟수"""
        sap_mock.post("SAP", "/sap/endpoint", {"project_id": "p1"})
        sap_mock.post("SAP", "/sap/endpoint", {"project_id": "p2"})

        count = sap_mock.get_call_count(target_system="SAP")
        assert count == 2

    def test_call_count_by_status(self):
        """Test 7: 상태별 호출 횟수"""
        mock = SAPApiMock(success_rate=0.5)

        # 충분한 호출로 통계적 검증
        for _ in range(100):
            try:
                mock.post("SAP", "/sap/endpoint", {"project_id": "p"})
            except TimeoutError:
                pass

        success_count = mock.get_call_count(status=MockResponseStatus.SUCCESS)
        timeout_count = mock.get_call_count(status=MockResponseStatus.TIMEOUT)

        assert success_count + timeout_count == 100
        assert 30 <= success_count <= 70  # 50% 성공률이므로 대략 50개

    def test_success_rate_calculation(self):
        """Test 8: 성공률 계산"""
        mock = SAPApiMock(success_rate=1.0)

        for _ in range(10):
            mock.post("SAP", "/sap/endpoint", {"project_id": "p"})

        assert mock.get_success_rate() == 1.0

    def test_invalid_target_system(self, sap_mock):
        """Test 9: 지원하지 않는 시스템 에러"""
        with pytest.raises(ValueError) as exc_info:
            sap_mock.post("INVALID_SYSTEM", "/endpoint", {})

        assert "unsupported" in str(exc_info.value).lower()

    def test_success_rate_adjustment(self, sap_mock):
        """Test 10: 성공률 조정"""
        sap_mock.set_success_rate(0.5)
        assert sap_mock.success_rate == 0.5

        with pytest.raises(ValueError):
            sap_mock.set_success_rate(1.5)  # 범위 초과

    def test_clear_history(self, sap_mock):
        """Test 11: 호출 기록 초기화"""
        sap_mock.post("SAP", "/sap/endpoint", {"project_id": "p"})
        assert len(sap_mock.get_call_history()) == 1

        sap_mock.clear_history()
        assert len(sap_mock.get_call_history()) == 0

    def test_different_target_systems(self):
        """Test 12: 다양한 대상 시스템"""
        mock = SAPApiMock(success_rate=1.0)

        sap_response = mock.post("SAP", "/endpoint", {"project_id": "p"})
        assert "sap_reference" in sap_response

        mock.clear_history()
        erp_response = mock.post("ERP", "/endpoint", {"project_id": "p"})
        assert "erp_reference" in erp_response

    def test_mock_factory_sap(self):
        """Test 13: Factory - SAP Mock 생성"""
        mock = SAPApiMockFactory.create_sap_mock(success_rate=0.95)
        assert mock.success_rate == 0.95

    def test_mock_factory_notification(self):
        """Test 14: Factory - Notification Mock 생성"""
        mock = SAPApiMockFactory.create_notification_mock()
        response = mock.post("NOTIFICATION", "/notify", {"type": "test"})
        assert response["status"] == "ok"

    def test_mock_factory_flaky(self):
        """Test 15: Factory - Flaky Mock 생성 (70% 성공)"""
        mock = SAPApiMockFactory.create_flaky_mock()
        assert mock.success_rate == 0.70


class TestSAPApiMockStressScenarios:
    """SAP API Mock 스트레스 테스트"""

    def test_high_volume_calls(self):
        """Test 16: 대량 호출 처리"""
        mock = SAPApiMock(success_rate=0.90)

        for i in range(1000):
            try:
                mock.post("SAP", "/endpoint", {"project_id": f"p{i}"})
            except TimeoutError:
                pass

        # 호출 기록이 모두 저장되었는지 확인
        assert len(mock.get_call_history()) == 1000

        # 성공률이 대략 90% 근처인지 확인 (±5%)
        actual_rate = mock.get_success_rate()
        assert 0.85 <= actual_rate <= 0.95

    def test_concurrent_style_calls(self):
        """Test 17: 연속 호출 (순차 실행)"""
        mock = SAPApiMock(success_rate=1.0)

        results = []
        for i in range(50):
            payload = {"project_id": f"proj_{i:03d}"}
            response = mock.post("SAP", "/endpoint", payload)
            results.append(response)

        assert len(results) == 50
        assert all(r["status"] == "ok" for r in results)
        assert len(mock.get_call_history()) == 50
