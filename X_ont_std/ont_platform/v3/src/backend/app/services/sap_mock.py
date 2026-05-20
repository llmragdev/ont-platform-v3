"""SAP API Mock — 테스트용 SAP 시스템 시뮬레이션"""
from __future__ import annotations

import random
from datetime import datetime
from typing import Optional

from app.models.changelog import SAPWriteBackPayload, WriteBackResult, SyncStatus


class SAPMockAPI:
    """SAP API Mock 서비스"""

    def __init__(self, success_rate: float = 0.95, latency_ms: int = 100):
        """
        Args:
            success_rate: 성공 확률 (0.0 ~ 1.0)
            latency_ms: 시뮬레이션 지연 시간 (ms)
        """
        self.success_rate = success_rate
        self.latency_ms = latency_ms
        self.call_history = []  # 호출 기록 (테스트용)

    def sync_project(self, payload: SAPWriteBackPayload) -> WriteBackResult:
        """프로젝트 데이터 동기화"""
        # 시뮬레이션
        import time
        time.sleep(self.latency_ms / 1000.0)

        # 성공/실패 판정
        is_success = random.random() < self.success_rate

        # 호출 기록 저장
        self.call_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": payload.action,
            "entity_id": payload.entity_id,
            "success": is_success
        })

        if is_success:
            return WriteBackResult(
                write_back_id="wb-" + payload.entity_id,
                status=SyncStatus.SYNCED,
                success=True,
                message=f"Successfully synced {payload.entity_type} {payload.entity_id} to SAP",
                response_data={
                    "sap_document_id": f"SAP-DOC-{payload.entity_id}",
                    "synced_at": datetime.utcnow().isoformat(),
                    "action": payload.action
                }
            )
        else:
            error_msg = "Temporary connection error (simulated)"
            return WriteBackResult(
                write_back_id="wb-" + payload.entity_id,
                status=SyncStatus.FAILED,
                success=False,
                message=error_msg,
                response_data=None
            )

    def sync_payment(self, entity_id: str, amount: float, payment_method: str) -> WriteBackResult:
        """지급 정보 동기화"""
        import time
        time.sleep(self.latency_ms / 1000.0)

        is_success = random.random() < self.success_rate

        if is_success:
            return WriteBackResult(
                write_back_id="wb-pay-" + entity_id,
                status=SyncStatus.SYNCED,
                success=True,
                message=f"Payment {amount} synced to SAP",
                response_data={
                    "sap_payment_id": f"PAY-{entity_id}",
                    "amount": amount,
                    "method": payment_method,
                    "synced_at": datetime.utcnow().isoformat()
                }
            )
        else:
            return WriteBackResult(
                write_back_id="wb-pay-" + entity_id,
                status=SyncStatus.FAILED,
                success=False,
                message="Payment sync failed (simulated)",
                response_data=None
            )

    def get_call_history(self) -> list[dict]:
        """호출 기록 조회"""
        return self.call_history.copy()

    def reset(self) -> None:
        """상태 초기화 (테스트용)"""
        self.call_history = []


class WriteBackSimulator:
    """WriteBack 동작 시뮬레이터 (다양한 시나리오)"""

    @staticmethod
    def simulate_success() -> WriteBackResult:
        """성공 시나리오"""
        return WriteBackResult(
            write_back_id="wb-success",
            status=SyncStatus.SYNCED,
            success=True,
            message="Write-back successful",
            response_data={"sap_id": "SAP-123"}
        )

    @staticmethod
    def simulate_temporary_failure() -> WriteBackResult:
        """임시 실패 (재시도 가능)"""
        return WriteBackResult(
            write_back_id="wb-temp-fail",
            status=SyncStatus.FAILED,
            success=False,
            message="Temporary connection error - will retry",
            response_data=None
        )

    @staticmethod
    def simulate_permanent_failure() -> WriteBackResult:
        """영구 실패 (재시도 불가)"""
        return WriteBackResult(
            write_back_id="wb-perm-fail",
            status=SyncStatus.FAILED,
            success=False,
            message="Invalid data format - cannot retry",
            response_data=None
        )

    @staticmethod
    def simulate_timeout() -> WriteBackResult:
        """타임아웃"""
        return WriteBackResult(
            write_back_id="wb-timeout",
            status=SyncStatus.FAILED,
            success=False,
            message="Request timeout after 30 seconds",
            response_data=None
        )

    @staticmethod
    def simulate_invalid_credentials() -> WriteBackResult:
        """인증 실패"""
        return WriteBackResult(
            write_back_id="wb-auth-fail",
            status=SyncStatus.FAILED,
            success=False,
            message="Authentication failed - invalid credentials",
            response_data=None
        )
