"""Phase 3 Week 3: WriteBack Worker — 백그라운드 동기화"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from threading import Thread, Event

from app.models.changelog import WriteBackItem, SyncStatus
from app.repositories.changelog_repository import WriteBackRepository
from app.services.sap_mock import SAPMockAPI

logger = logging.getLogger(__name__)


class WriteBackWorker:
    """WriteBack 워커 — 1분 주기로 SAP와 동기화"""

    def __init__(self, interval_seconds: int = 60, max_retries: int = 3, retry_delay_hours: int = 1):
        """
        Args:
            interval_seconds: 실행 주기 (초)
            max_retries: 최대 재시도 횟수
            retry_delay_hours: 재시도 대기 시간 (시간)
        """
        self.interval_seconds = interval_seconds
        self.max_retries = max_retries
        self.retry_delay_hours = retry_delay_hours
        self.repository = WriteBackRepository()
        self.sap_api = SAPMockAPI(success_rate=0.95)  # 95% 성공률로 시뮬레이션
        self.running = False
        self.thread = None
        self.stop_event = Event()
        self.stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "retried": 0,
            "last_run": None,
            "next_run": None
        }

    def start(self) -> None:
        """워커 시작"""
        if self.running:
            logger.warning("Worker already running")
            return

        self.running = True
        self.stop_event.clear()
        self.thread = Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"WriteBack Worker started (interval: {self.interval_seconds}s)")

    def stop(self) -> None:
        """워커 중지"""
        if not self.running:
            logger.warning("Worker not running")
            return

        self.running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("WriteBack Worker stopped")

    def _run_loop(self) -> None:
        """메인 루프"""
        while self.running:
            try:
                self.stats["next_run"] = datetime.utcnow() + timedelta(seconds=self.interval_seconds)
                self._process_pending_items()
                self.stats["last_run"] = datetime.utcnow()
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)

            # 주기적 대기
            if self.stop_event.wait(timeout=self.interval_seconds):
                break

    def _process_pending_items(self) -> None:
        """대기 중인 항목 처리"""
        # SAP 시스템용 큐 처리
        pending_items = self.repository.get_pending_items("SAP")

        for item in pending_items:
            self._process_item(item)

    def _process_item(self, item: WriteBackItem) -> None:
        """단일 항목 처리"""
        self.stats["processed"] += 1

        # 재시도 대기 시간 확인
        if item.next_retry_at and datetime.utcnow() < item.next_retry_at:
            logger.debug(f"Skipping {item.write_back_id} - retry scheduled for later")
            return

        # 최대 재시도 횟수 초과 확인
        if item.attempt_count >= self.max_retries:
            logger.warning(f"Max retries exceeded for {item.write_back_id}")
            self.repository.update_item_status(item.write_back_id, SyncStatus.FAILED, "Max retries exceeded")
            self.stats["failed"] += 1
            return

        # SAP API 호출
        try:
            from app.models.changelog import SAPWriteBackPayload
            payload = SAPWriteBackPayload(**item.payload)
            result = self.sap_api.sync_project(payload)

            if result.success:
                logger.info(f"Successfully synced {item.write_back_id}")
                self.repository.update_item_status(item.write_back_id, SyncStatus.SYNCED)
                self.stats["succeeded"] += 1
            else:
                # 실패 - 재시도 스케줄
                item.attempt_count += 1
                next_retry = datetime.utcnow() + timedelta(hours=self.retry_delay_hours)

                if item.attempt_count >= self.max_retries:
                    logger.error(f"Final failure for {item.write_back_id}: {result.message}")
                    self.repository.update_item_status(item.write_back_id, SyncStatus.FAILED, result.message)
                    self.stats["failed"] += 1
                else:
                    logger.warning(
                        f"Sync failed for {item.write_back_id}, will retry at {next_retry}. "
                        f"Attempt {item.attempt_count}/{self.max_retries}"
                    )
                    self.stats["retried"] += 1
                    # 다음 재시도 시간을 저장하려면 저장소 업데이트 필요

        except Exception as e:
            logger.error(f"Error processing {item.write_back_id}: {e}")
            item.attempt_count += 1

            if item.attempt_count >= self.max_retries:
                self.repository.update_item_status(item.write_back_id, SyncStatus.FAILED, str(e))
                self.stats["failed"] += 1
            else:
                self.stats["retried"] += 1

    def get_stats(self) -> dict:
        """워커 통계 조회"""
        return self.stats.copy()

    def get_sap_call_history(self) -> list[dict]:
        """SAP API 호출 기록 조회"""
        return self.sap_api.get_call_history()


class WriteBackWorkerManager:
    """WriteBack 워커 관리자 (싱글톤)"""

    _instance = None
    _worker = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._worker is None:
            self._worker = WriteBackWorker()

    @classmethod
    def get_worker(cls) -> WriteBackWorker:
        """워커 인스턴스 조회"""
        manager = cls()
        return manager._worker

    @classmethod
    def start_worker(cls) -> None:
        """워커 시작"""
        worker = cls.get_worker()
        worker.start()

    @classmethod
    def stop_worker(cls) -> None:
        """워커 중지"""
        worker = cls.get_worker()
        worker.stop()


# 모듈 수준에서 워커 인스턴스 생성 (선택적)
_global_worker = None

def initialize_worker(auto_start: bool = False) -> WriteBackWorker:
    """글로벌 워커 초기화"""
    global _global_worker
    _global_worker = WriteBackWorker()
    if auto_start:
        _global_worker.start()
    return _global_worker

def get_global_worker() -> WriteBackWorker | None:
    """글로벌 워커 조회"""
    return _global_worker
