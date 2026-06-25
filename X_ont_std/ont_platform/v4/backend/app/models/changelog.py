"""Phase 3 Week 3: Changelog 및 Write-back 모델"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class SyncStatus(str, Enum):
    """동기화 상태"""
    PENDING = "pending"      # 아직 전송되지 않음
    SYNCING = "syncing"      # 전송 중
    SYNCED = "synced"        # 성공적으로 전송됨
    FAILED = "failed"        # 전송 실패
    SKIPPED = "skipped"      # 건너뜀 (필요 없음)


class ChangelogEntry(BaseModel):
    """변경 로그 항목 (JSONL 형식)"""
    changelog_id: str                    # 변경 로그 고유 ID
    entity_id: str                       # 대상 엔티티
    entity_type: str                     # 엔티티 타입
    action: str                          # 액션 이름 (approve_project 등)
    old_value: dict | None               # 이전 값
    new_value: dict                      # 변경된 값
    performed_by: str                    # 수행자
    performed_at: datetime               # 수행 시간
    doc_id: str                          # 문서 ID
    domain_id: str                       # 도메인 ID
    sync_status: SyncStatus = SyncStatus.PENDING
    sync_attempts: int = 0               # 동기화 시도 횟수
    sync_errors: list[str] = []          # 동기화 오류 기록
    synced_at: datetime | None = None    # 동기화 완료 시간


class WriteBackItem(BaseModel):
    """WriteBack 큐 항목"""
    write_back_id: str                   # 큐 항목 ID
    changelog_id: str                    # 관련 변경 로그 ID
    target_system: str                   # 대상 시스템 (e.g., "SAP")
    entity_id: str                       # 대상 엔티티
    action: str                          # 액션
    payload: dict                        # 전송할 데이터
    status: SyncStatus = SyncStatus.PENDING
    created_at: datetime                 # 생성 시간
    last_attempt_at: datetime | None = None  # 마지막 시도 시간
    next_retry_at: datetime | None = None    # 다음 재시도 시간
    attempt_count: int = 0               # 시도 횟수 (최대 3회)
    errors: list[dict] = []              # 오류 기록 [{timestamp, message, code}]


class WriteBackResult(BaseModel):
    """WriteBack 결과"""
    write_back_id: str
    status: SyncStatus
    success: bool
    message: str
    response_data: dict | None = None
    timestamp: datetime = datetime.utcnow()


class SAPWriteBackPayload(BaseModel):
    """SAP 시스템용 WriteBack 페이로드"""
    action: str                          # "approve", "reject", "complete"
    entity_id: str
    entity_type: str                     # "PROJECT"
    properties: dict                     # 변경된 속성들
    metadata: dict = {}                  # 메타데이터 (user, timestamp 등)


class NotificationPayload(BaseModel):
    """알림 페이로드"""
    recipients: list[str]                # 수신자 목록 (applicant, manager 등)
    title: str
    message: str
    action: str                          # 액션 이름
    entity_id: str
    metadata: dict = {}
