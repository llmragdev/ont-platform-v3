"""Changelog 서비스 — 액션 실행 이력 저장"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy.orm import Session
from pathlib import Path
import json

from app.db.models import ChangeLog


class ChangeLogService:
    """Changelog 관리 서비스"""

    CHANGELOG_DIR = Path("storage/demo-co/proj-01/changelog")

    @staticmethod
    def create_changelog(
        db: Session,
        entity_id: str,
        entity_type: str,
        domain_id: str,
        action_type: str,
        actor: str,
        old_status: str | None,
        new_status: str | None,
        source: str = "web_ui",
        target_system: str | None = None
    ) -> ChangeLog:
        """
        Changelog 레코드 생성

        Args:
            db: 데이터베이스 세션
            entity_id: 엔티티 ID
            entity_type: 엔티티 타입
            domain_id: 도메인 ID
            action_type: 액션 종류
            actor: 실행자
            old_status: 변경 전 상태
            new_status: 변경 후 상태
            source: 요청 출처
            target_system: 동기화 대상 시스템

        Returns:
            생성된 ChangeLog 객체
        """
        changelog = ChangeLog(
            id=f"chg_{uuid4().hex[:12]}",
            entity_id=entity_id,
            entity_type=entity_type,
            domain_id=domain_id,
            action_type=action_type,
            actor=actor,
            source=source,
            timestamp=datetime.utcnow(),
            old_status=old_status,
            new_status=new_status,
            sync_status="PENDING",
            target_system=target_system,
            retry_count=0
        )
        db.add(changelog)
        db.flush()

        # JSONL 파일에도 저장
        ChangeLogService._save_to_jsonl(changelog)

        return changelog

    @staticmethod
    def _save_to_jsonl(changelog: ChangeLog):
        """JSONL 파일에 저장"""
        ChangeLogService.CHANGELOG_DIR.mkdir(parents=True, exist_ok=True)

        file_path = ChangeLogService.CHANGELOG_DIR / f"{changelog.domain_id}_changes.jsonl"

        record = {
            "id": changelog.id,
            "entity_id": changelog.entity_id,
            "entity_type": changelog.entity_type,
            "domain_id": changelog.domain_id,
            "action_type": changelog.action_type,
            "actor": changelog.actor,
            "source": changelog.source,
            "timestamp": changelog.timestamp.isoformat(),
            "old_status": changelog.old_status,
            "new_status": changelog.new_status,
            "sync_status": changelog.sync_status,
            "target_system": changelog.target_system,
            "retry_count": changelog.retry_count,
            "error_message": changelog.error_message
        }

        with open(file_path, "a") as f:
            f.write(json.dumps(record) + "\n")

    @staticmethod
    def mark_synced(db: Session, changelog_id: str):
        """changelog를 SYNCED로 표시"""
        changelog = db.query(ChangeLog).filter(ChangeLog.id == changelog_id).first()
        if changelog:
            changelog.sync_status = "SYNCED"
            changelog.sync_timestamp = datetime.utcnow()
            db.commit()

    @staticmethod
    def mark_failed(db: Session, changelog_id: str, error_message: str, retry_count: int = 0):
        """changelog를 FAILED로 표시"""
        changelog = db.query(ChangeLog).filter(ChangeLog.id == changelog_id).first()
        if changelog:
            changelog.sync_status = "FAILED"
            changelog.error_message = error_message
            changelog.retry_count = retry_count
            db.commit()

    @staticmethod
    def increment_retry(db: Session, changelog_id: str):
        """재시도 횟수 증가"""
        changelog = db.query(ChangeLog).filter(ChangeLog.id == changelog_id).first()
        if changelog:
            changelog.retry_count += 1
            db.commit()

    @staticmethod
    def get_pending_changes(db: Session, domain_id: str) -> list[ChangeLog]:
        """PENDING 상태의 changelog 조회"""
        return db.query(ChangeLog).filter(
            ChangeLog.domain_id == domain_id,
            ChangeLog.sync_status == "PENDING"
        ).all()

    @staticmethod
    def get_change_history(db: Session, entity_id: str) -> list[ChangeLog]:
        """특정 엔티티의 변경 이력 조회"""
        return db.query(ChangeLog).filter(
            ChangeLog.entity_id == entity_id
        ).order_by(ChangeLog.timestamp.desc()).all()
