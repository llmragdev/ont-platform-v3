"""SAP API Mock — 테스트 목적의 Mock API 구현"""
import random
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class MockResponseStatus(str, Enum):
    """Mock API 응답 상태"""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"


class SAPApiMock:
    """SAP API Mock 구현 (90% 성공, 10% 타임아웃/에러)"""

    # 성공률 설정
    SUCCESS_RATE = 0.90  # 90% 성공
    FAILURE_RATE = 0.10  # 10% 실패 (타임아웃)

    # 지원하는 엔드포인트
    SUPPORTED_ENDPOINTS = {
        "SAP",
        "NOTIFICATION",
        "ERP",
    }

    def __init__(self, success_rate: float = 0.90):
        """
        Mock API 초기화

        Args:
            success_rate: 성공률 (기본값 0.90 = 90%)
        """
        self.success_rate = success_rate
        self.call_history = []  # 호출 기록

    def post(self, target_system: str, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock POST 요청

        Args:
            target_system: 대상 시스템 (SAP, NOTIFICATION, ERP)
            endpoint: API 엔드포인트
            payload: 요청 페이로드

        Returns:
            응답 객체 {status, sync_id, message, timestamp, ...}

        Raises:
            TimeoutError: 10% 확률로 발생
            ValueError: 잘못된 시스템/엔드포인트
        """
        # 입력 검증
        if target_system not in self.SUPPORTED_ENDPOINTS:
            raise ValueError(f"Unsupported target system: {target_system}")

        # 호출 기록 저장
        call_record = {
            "target_system": target_system,
            "endpoint": endpoint,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
            "status": None
        }

        # 성공/실패 결정
        if random.random() < self.success_rate:
            response = self._generate_success_response(target_system, endpoint, payload)
            call_record["status"] = MockResponseStatus.SUCCESS
        else:
            call_record["status"] = MockResponseStatus.TIMEOUT
            self.call_history.append(call_record)
            raise TimeoutError(f"SAP API timeout for {target_system}/{endpoint}")

        call_record["response"] = response
        self.call_history.append(call_record)
        return response

    def _generate_success_response(
        self,
        target_system: str,
        endpoint: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """성공 응답 생성"""
        sync_id = f"sync_{random.randint(100000, 999999)}"
        timestamp = datetime.utcnow().isoformat()

        if target_system == "SAP":
            return {
                "status": "ok",
                "sync_id": sync_id,
                "message": f"Successfully synced to SAP",
                "timestamp": timestamp,
                "project_id": payload.get("project_id"),
                "action": payload.get("action"),
                "sap_reference": f"SAP_{sync_id[-6:]}",
            }
        elif target_system == "NOTIFICATION":
            return {
                "status": "ok",
                "notification_id": sync_id,
                "message": f"Notification sent successfully",
                "timestamp": timestamp,
                "recipient": payload.get("recipient", "system@example.com"),
                "type": "info_request",
            }
        elif target_system == "ERP":
            return {
                "status": "ok",
                "erp_id": sync_id,
                "message": f"Successfully synced to ERP",
                "timestamp": timestamp,
                "project_id": payload.get("project_id"),
                "erp_reference": f"ERP_{sync_id[-6:]}",
            }
        else:
            return {
                "status": "ok",
                "id": sync_id,
                "message": f"Request processed",
                "timestamp": timestamp,
            }

    def get_call_history(self) -> list:
        """호출 기록 조회"""
        return self.call_history

    def get_call_count(self, target_system: Optional[str] = None, status: Optional[MockResponseStatus] = None) -> int:
        """
        호출 횟수 조회

        Args:
            target_system: 필터링할 시스템 (None = 전체)
            status: 필터링할 상태 (None = 전체)

        Returns:
            호출 횟수
        """
        count = 0
        for call in self.call_history:
            if target_system and call["target_system"] != target_system:
                continue
            if status and call["status"] != status:
                continue
            count += 1
        return count

    def get_success_rate(self) -> float:
        """실제 성공률 계산"""
        if not self.call_history:
            return 0.0

        success_count = sum(
            1 for call in self.call_history
            if call["status"] == MockResponseStatus.SUCCESS
        )
        return success_count / len(self.call_history)

    def clear_history(self):
        """호출 기록 초기화"""
        self.call_history = []

    def set_success_rate(self, rate: float):
        """성공률 조정 (테스트용)"""
        if not 0.0 <= rate <= 1.0:
            raise ValueError("Success rate must be between 0.0 and 1.0")
        self.success_rate = rate


class NotificationApiMock(SAPApiMock):
    """Notification API Mock (항상 성공)"""

    def __init__(self):
        super().__init__(success_rate=1.0)

    def post(self, target_system: str, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Notification은 항상 성공"""
        if target_system != "NOTIFICATION":
            raise ValueError(f"NotificationApiMock only supports NOTIFICATION, got {target_system}")

        call_record = {
            "target_system": target_system,
            "endpoint": endpoint,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
            "status": MockResponseStatus.SUCCESS
        }

        response = self._generate_success_response(target_system, endpoint, payload)
        call_record["response"] = response
        self.call_history.append(call_record)
        return response


class SAPApiMockFactory:
    """Mock API Factory — 다양한 Mock 객체 생성"""

    @staticmethod
    def create_sap_mock(success_rate: float = 0.90) -> SAPApiMock:
        """SAP Mock 생성 (90% 성공)"""
        return SAPApiMock(success_rate=success_rate)

    @staticmethod
    def create_notification_mock() -> NotificationApiMock:
        """Notification Mock 생성 (100% 성공)"""
        return NotificationApiMock()

    @staticmethod
    def create_flaky_mock(success_rate: float = 0.70) -> SAPApiMock:
        """Flaky Mock 생성 (불안정한 API 시뮬레이션)"""
        return SAPApiMock(success_rate=success_rate)
