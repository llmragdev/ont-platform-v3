"""Write-back Worker — 비동기 백그라운드 작업"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.db.models import WriteBackQueue, ChangeLog
from app.services.sap_api_mock import SAPApiMock, SAPApiMockFactory


class WriteBackWorkerConfig:
    """Write-back Worker 설정"""
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 60  # 1분
    RETRY_BACKOFF_MULTIPLIER = 2  # 지수 백오프
    WORKER_INTERVAL = 60  # 1분 주기


class WriteBackWorker:
    """
    Write-back Worker — 백그라운드에서 주기적으로 실행

    역할:
    1. WriteBackQueue의 PENDING 항목 조회
    2. SAP API 호출
    3. 성공: SYNCED 상태로 변경
    4. 실패: FAILED 상태로 변경 (재시도 가능한 경우는 다시 PENDING)
    """

    def __init__(
        self,
        db: Session,
        sap_api: Optional[SAPApiMock] = None,
        config: Optional[WriteBackWorkerConfig] = None
    ):
        """
        Worker 초기화

        Args:
            db: 데이터베이스 세션
            sap_api: SAP API Mock (기본값: 90% 성공률)
            config: Worker 설정
        """
        self.db = db
        self.sap_api = sap_api or SAPApiMockFactory.create_sap_mock()
        self.config = config or WriteBackWorkerConfig()
        self.is_running = False
        self.processed_count = 0
        self.success_count = 0
        self.failure_count = 0

    def start(self) -> None:
        """Worker 시작 (동기 버전)"""
        self.is_running = True

    def stop(self) -> None:
        """Worker 중지"""
        self.is_running = False

    async def run_async(self) -> None:
        """
        Async 실행 — 주기적으로 pending 항목 처리

        사용:
            worker = WriteBackWorker(db)
            await worker.run_async()
        """
        self.is_running = True

        try:
            while self.is_running:
                self.process_pending()
                await asyncio.sleep(self.config.WORKER_INTERVAL)
        finally:
            self.is_running = False

    def process_pending(self) -> dict:
        """
        Pending 항목 처리

        Changes:
        - FOR UPDATE SKIP LOCKED 적용 (다중 워커 경합 방지)
        - LIMIT 10 추가 (배치 크기 제한)
        - 개별 항목마다 db.commit() 수행 (트랜잭션 유실 방지)

        Returns:
            {processed: int, succeeded: int, failed: int, errors: list}
        """
        # Pending 항목 조회 (FOR UPDATE SKIP LOCKED 적용 + 다음 재시도 시간 필터)
        pending_items = self.db.query(WriteBackQueue).filter(
            WriteBackQueue.status == "PENDING",
            (WriteBackQueue.next_retry_at.is_(None)) |
            (WriteBackQueue.next_retry_at <= datetime.utcnow())
        ).with_for_update(skip_locked=True).limit(10).all()

        errors = []
        self.processed_count += len(pending_items)

        for item in pending_items:
            try:
                self._process_single_item(item)
                self.db.commit()
            except Exception as e:
                self.db.commit()
                errors.append({
                    "item_id": item.id,
                    "error": str(e)
                })

        result = {
            "processed": len(pending_items),
            "succeeded": self.success_count,
            "failed": self.failure_count,
            "errors": errors
        }

        return result

    def _process_single_item(self, item: WriteBackQueue) -> None:
        """
        단일 Write-back 항목 처리

        처리 로직:
        1. SAP API 호출
        2. 성공 → SYNCED 상태로 변경
        3. 실패 (TimeoutError):
           - retry_count < MAX_RETRIES → PENDING 상태 유지 + retry_count 증가
           - retry_count >= MAX_RETRIES → FAILED 상태로 변경

        Args:
            item: WriteBackQueue 항목
        """
        try:
            # SAP API 호출
            response = self.sap_api.post(
                target_system=item.target_system,
                endpoint="/api/sync",
                payload=item.payload
            )

            # 성공
            item.status = "CONFIRMED"
            item.sent_at = datetime.utcnow()
            self.success_count += 1

            # Changelog 업데이트 (target_system 기반으로 해당 changelog 찾아서 update)
            self._update_changelog_synced(item)

        except TimeoutError as e:
            # 재시도 가능 여부 판단
            if item.retry_count < self.config.MAX_RETRIES:
                # PENDING 상태 유지, retry_count 증가
                item.retry_count += 1
                item.last_error_at = datetime.utcnow()
                item.error_message = str(e)

                # Task 4: 지수 백오프 계산 및 DB에 저장
                next_retry_delay = (
                    self.config.INITIAL_RETRY_DELAY *
                    (self.config.RETRY_BACKOFF_MULTIPLIER ** item.retry_count)
                )
                item.next_retry_at = (
                    datetime.utcnow() + timedelta(seconds=next_retry_delay)
                )
            else:
                # Task 3: 재시도 횟수 초과 → DLQ 상태로 격리
                item.status = "DLQ"
                item.dlq_reason = f"Max retries ({self.config.MAX_RETRIES}) exceeded: {str(e)}"
                item.dlq_at = datetime.utcnow()
                item.last_error_at = datetime.utcnow()
                item.error_message = str(e)
                self.failure_count += 1

                # Changelog 업데이트 (FAILED)
                self._update_changelog_failed(item, item.error_message)

        except Exception as e:
            # 예상치 못한 에러 (재시도 불가)
            item.status = "DLQ"
            item.dlq_reason = f"Unexpected error: {str(e)}"
            item.dlq_at = datetime.utcnow()
            item.last_error_at = datetime.utcnow()
            item.error_message = str(e)
            self.failure_count += 1

            # Changelog 업데이트 (FAILED)
            self._update_changelog_failed(item, item.error_message)

    def _update_changelog_synced(self, item: WriteBackQueue) -> None:
        """
        Changelog을 SYNCED로 업데이트

        Args:
            item: WriteBackQueue 항목
        """
        # WriteBackQueue의 payload에서 project_id를 추출하여 해당 changelog 찾기
        project_id = item.payload.get("project_id")

        if project_id:
            changelog = self.db.query(ChangeLog).filter(
                ChangeLog.entity_id == project_id,
                ChangeLog.sync_status == "PENDING",
                ChangeLog.target_system == item.target_system
            ).first()

            if changelog:
                changelog.sync_status = "SYNCED"
                changelog.sync_timestamp = datetime.utcnow()

    def _update_changelog_failed(self, item: WriteBackQueue, error_message: str) -> None:
        """
        Changelog을 FAILED로 업데이트

        Args:
            item: WriteBackQueue 항목
            error_message: 에러 메시지
        """
        # WriteBackQueue의 payload에서 project_id를 추출하여 해당 changelog 찾기
        project_id = item.payload.get("project_id")

        if project_id:
            changelog = self.db.query(ChangeLog).filter(
                ChangeLog.entity_id == project_id,
                ChangeLog.sync_status == "PENDING",
                ChangeLog.target_system == item.target_system
            ).first()

            if changelog:
                changelog.sync_status = "FAILED"
                changelog.error_message = error_message
                changelog.retry_count = item.retry_count

    def get_statistics(self) -> dict:
        """Worker 통계"""
        return {
            "is_running": self.is_running,
            "processed": self.processed_count,
            "succeeded": self.success_count,
            "failed": self.failure_count,
            "pending_count": self.db.query(WriteBackQueue).filter(
                WriteBackQueue.status == "PENDING"
            ).count(),
            "confirmed_count": self.db.query(WriteBackQueue).filter(
                WriteBackQueue.status == "CONFIRMED"
            ).count(),
            "failed_count": self.db.query(WriteBackQueue).filter(
                WriteBackQueue.status == "FAILED"
            ).count(),
        }


class WriteBackWorkerPool:
    """다중 Worker 풀 관리"""

    def __init__(self, db: Session, num_workers: int = 1):
        """
        Worker Pool 초기화

        Args:
            db: 데이터베이스 세션
            num_workers: 워커 개수
        """
        self.db = db
        self.num_workers = num_workers
        self.workers = [
            WriteBackWorker(db) for _ in range(num_workers)
        ]

    async def run_async(self) -> None:
        """모든 Worker 실행"""
        tasks = [worker.run_async() for worker in self.workers]
        await asyncio.gather(*tasks)

    def stop_all(self) -> None:
        """모든 Worker 중지"""
        for worker in self.workers:
            worker.stop()

    def get_all_statistics(self) -> list:
        """모든 Worker 통계"""
        return [worker.get_statistics() for worker in self.workers]
