"""Phase 4 Week 2: 감시 저장소 (JSONL 기반)"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.models.entity_metadata import (
    AuditLog, AuditLogAction, AuditSummary, EntityVersion, EntityMetadata
)


class AuditRepository:
    """감시 로그 저장소 (JSONL 기반)"""

    def __init__(self):
        # 공통 감시 데이터 경로
        self.base_path = Path.home() / ".ont-platform" / "data" / "audit"
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_audit_path(self, entity_id: str) -> Path:
        """엔티티별 감시 로그 파일 경로"""
        path = self.base_path / f"{entity_id}.jsonl"
        return path

    def _get_version_path(self, entity_id: str) -> Path:
        """엔티티 버전 파일 경로"""
        path = self.base_path / f"{entity_id}_versions.jsonl"
        return path

    def log_action(self, audit_log: AuditLog) -> None:
        """감시 로그 기록 (append-only)"""
        path = self._get_audit_path(audit_log.entity_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(audit_log.model_dump_json() + "\n")

    def save_version(self, version: EntityVersion) -> None:
        """엔티티 버전 저장"""
        path = self._get_version_path(version.entity_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(version.model_dump_json() + "\n")

    def get_audit_logs(
        self, entity_id: str, limit: int = 100, action: Optional[AuditLogAction] = None
    ) -> List[AuditLog]:
        """엔티티의 감시 로그 조회"""
        path = self._get_audit_path(entity_id)
        if not path.exists():
            return []

        logs = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    log = AuditLog(**data)
                    if action is None or log.action == action:
                        logs.append(log)
                        if len(logs) >= limit:
                            break
                except (json.JSONDecodeError, ValueError):
                    continue
        return logs

    def get_versions(self, entity_id: str, limit: int = 50) -> List[EntityVersion]:
        """엔티티의 버전 이력 조회"""
        path = self._get_version_path(entity_id)
        if not path.exists():
            return []

        versions = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    version = EntityVersion(**data)
                    versions.append(version)
                    if len(versions) >= limit:
                        break
                except (json.JSONDecodeError, ValueError):
                    continue
        return versions

    def get_current_version(self, entity_id: str) -> Optional[EntityVersion]:
        """현재 버전 조회"""
        versions = self.get_versions(entity_id, limit=1000)
        if not versions:
            return None
        # 역순으로 순회하여 is_current=True인 첫 번째 찾기
        for version in reversed(versions):
            if version.is_current:
                return version
        return None

    def get_audit_summary(self, entity_id: str) -> Optional[AuditSummary]:
        """감시 요약 생성"""
        logs = self.get_audit_logs(entity_id, limit=1000)
        if not logs:
            return None

        # 통계 계산
        changes_by_action: Dict[str, int] = {}
        changes_by_user: Dict[str, int] = {}

        for log in logs:
            # 액션별 카운트
            action_key = log.action.value
            changes_by_action[action_key] = changes_by_action.get(action_key, 0) + 1

            # 사용자별 카운트
            changes_by_user[log.performed_by] = changes_by_user.get(log.performed_by, 0) + 1

        # 변화 빈도 판정
        change_count = len(logs)
        if change_count > 10:
            frequency = "high"
        elif change_count > 3:
            frequency = "medium"
        else:
            frequency = "low"

        return AuditSummary(
            entity_id=entity_id,
            total_changes=change_count,
            last_change_at=logs[-1].performed_at,
            changes_by_action=changes_by_action,
            changes_by_user=changes_by_user,
            change_frequency=frequency
        )

    def get_logs_by_action(
        self, entity_id: str, action: AuditLogAction, limit: int = 100
    ) -> List[AuditLog]:
        """특정 액션만 조회"""
        return self.get_audit_logs(entity_id, limit=limit, action=action)

    def get_logs_by_user(self, entity_id: str, user_id: str, limit: int = 100) -> List[AuditLog]:
        """특정 사용자의 변경만 조회"""
        logs = self.get_audit_logs(entity_id, limit=limit)
        return [log for log in logs if log.performed_by == user_id]

    def get_logs_in_timerange(
        self, entity_id: str, start_time: datetime, end_time: datetime
    ) -> List[AuditLog]:
        """시간 범위 내 변경 조회"""
        logs = self.get_audit_logs(entity_id, limit=1000)
        return [log for log in logs if start_time <= log.performed_at <= end_time]

    def compare_versions(self, entity_id: str, version1: int, version2: int) -> Dict[str, any]:
        """두 버전 비교"""
        versions = self.get_versions(entity_id, limit=1000)
        v1 = next((v for v in versions if v.version == version1), None)
        v2 = next((v for v in versions if v.version == version2), None)

        if not v1 or not v2:
            return {}

        # 변경된 필드 찾기
        changes = {}
        all_keys = set(v1.data.keys()) | set(v2.data.keys())

        for key in all_keys:
            old_val = v1.data.get(key)
            new_val = v2.data.get(key)
            if old_val != new_val:
                changes[key] = {"old": old_val, "new": new_val}

        return {
            "version1": version1,
            "version2": version2,
            "changed_at": v2.changed_at,
            "changed_by": v2.changed_by,
            "changes": changes
        }

    def restore_version(
        self, entity_id: str, version_number: int, restored_by: str
    ) -> Optional[EntityVersion]:
        """특정 버전으로 복원"""
        versions = self.get_versions(entity_id, limit=1000)
        target_version = next((v for v in versions if v.version == version_number), None)

        if not target_version:
            return None

        # 현재 버전 표시 제거
        current_versions = self.get_versions(entity_id, limit=1000)
        for v in current_versions:
            if v.is_current:
                v.is_current = False

        # 새 버전으로 저장 (복원 버전)
        new_version = EntityVersion(
            entity_id=entity_id,
            version=len(current_versions) + 1,
            data=target_version.data.copy(),
            changed_fields=list(target_version.data.keys()),
            change_reason=f"Restored from version {version_number}",
            changed_by=restored_by,
            changed_at=datetime.utcnow(),
            is_current=True
        )

        self.save_version(new_version)

        # 복원 이벤트 기록
        restore_log = AuditLog(
            audit_id="audit-" + str(datetime.utcnow().timestamp()),
            entity_id=entity_id,
            action=AuditLogAction.RESTORE,
            new_value={"from_version": version_number, "to_version": new_version.version},
            performed_by=restored_by,
            performed_at=datetime.utcnow(),
            reason=f"Restored from version {version_number}"
        )
        self.log_action(restore_log)

        return new_version

    def export_audit_trail(self, entity_id: str, format: str = "json") -> str:
        """감시 추적 내보내기"""
        logs = self.get_audit_logs(entity_id, limit=10000)
        versions = self.get_versions(entity_id, limit=1000)
        summary = self.get_audit_summary(entity_id)

        if format == "json":
            return json.dumps({
                "entity_id": entity_id,
                "summary": summary.model_dump() if summary else None,
                "audit_logs": [log.model_dump() for log in logs],
                "versions": [v.model_dump() for v in versions],
                "exported_at": datetime.utcnow().isoformat()
            }, indent=2, ensure_ascii=False, default=str)

        return ""

    def purge_old_logs(self, entity_id: str, days_to_keep: int = 90) -> int:
        """오래된 로그 삭제"""
        cutoff_time = datetime.utcnow()
        cutoff_seconds = days_to_keep * 86400

        logs = self.get_audit_logs(entity_id, limit=10000)
        recent_logs = [
            log for log in logs
            if (datetime.utcnow() - log.performed_at).total_seconds() < cutoff_seconds
        ]

        # 최근 로그만 유지
        path = self._get_audit_path(entity_id)
        if path.exists():
            with open(path, "w", encoding="utf-8") as f:
                for log in recent_logs:
                    f.write(log.model_dump_json() + "\n")

        return len(logs) - len(recent_logs)
