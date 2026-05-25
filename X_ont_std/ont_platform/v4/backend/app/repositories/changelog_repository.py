"""Changelog 저장소 (JSONL 형식)"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.models.changelog import ChangelogEntry, WriteBackItem, SyncStatus
from app.models.tenant_context import TenantContext
from storage_config import get_project_root


class ChangelogRepository:
    """변경 로그 저장소 (JSONL)"""

    def __init__(self):
        # 공통 데이터 경로 (모든 테넌트 공유)
        self.base_path = Path.home() / ".ont-platform" / "data" / "changelogs"
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_changelog_path(self, ctx: TenantContext, doc_id: str) -> Path:
        """변경 로그 파일 경로"""
        # 테넌트별 디렉토리
        path = self.base_path / ctx.company_id / ctx.project_id / f"{doc_id}.jsonl"
        if path.parent != self.base_path:
            path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def append_entry(self, ctx: TenantContext, entry: ChangelogEntry) -> None:
        """변경 로그 항목 추가 (append)"""
        path = self._get_changelog_path(ctx, entry.doc_id)
        with open(path, "a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")

    def get_entries(
        self, ctx: TenantContext, doc_id: str, entity_id: str | None = None, limit: int = 100
    ) -> list[ChangelogEntry]:
        """변경 로그 조회"""
        path = self._get_changelog_path(ctx, doc_id)
        if not path.exists():
            return []

        entries = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    entry = ChangelogEntry(**data)
                    if entity_id is None or entry.entity_id == entity_id:
                        entries.append(entry)
                        if len(entries) >= limit:
                            break
                except json.JSONDecodeError:
                    continue
        return entries

    def get_pending_entries(self, ctx: TenantContext, doc_id: str) -> list[ChangelogEntry]:
        """전송 대기 중인 항목 조회"""
        path = self._get_changelog_path(ctx, doc_id)
        if not path.exists():
            return []

        entries = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    entry = ChangelogEntry(**data)
                    if entry.sync_status == SyncStatus.PENDING:
                        entries.append(entry)
                except json.JSONDecodeError:
                    continue
        return entries

    def update_entry_status(
        self, ctx: TenantContext, changelog_id: str, status: SyncStatus, synced_at: datetime | None = None
    ) -> bool:
        """로그 항목 상태 업데이트 (전체 파일 재작성)"""
        all_doc_ids = set()
        for path in self.base_path.glob(f"{ctx.company_id}/{ctx.project_id}/*.jsonl"):
            all_doc_ids.add(path.stem)

        for doc_id in all_doc_ids:
            path = self._get_changelog_path(ctx, doc_id)
            entries = []
            updated = False

            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        entry = ChangelogEntry(**data)
                        if entry.changelog_id == changelog_id:
                            entry.sync_status = status
                            entry.synced_at = synced_at
                            updated = True
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue

            if updated:
                with open(path, "w", encoding="utf-8") as f:
                    for entry in entries:
                        f.write(entry.model_dump_json() + "\n")
                return True

        return False


class WriteBackRepository:
    """WriteBack 큐 저장소 (JSON 라인 형식)"""

    def __init__(self):
        # 공통 데이터 경로 (모든 테넌트 공유)
        self.base_path = Path.home() / ".ont-platform" / "data" / "writebacks"
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_queue_path(self, target_system: str) -> Path:
        """WriteBack 큐 파일 경로"""
        path = self.base_path / f"{target_system}.jsonl"
        return path

    def enqueue(self, item: WriteBackItem) -> None:
        """큐에 항목 추가"""
        path = self._get_queue_path(item.target_system)
        with open(path, "a", encoding="utf-8") as f:
            f.write(item.model_dump_json() + "\n")

    def get_pending_items(self, target_system: str) -> list[WriteBackItem]:
        """전송 대기 중인 항목 조회"""
        path = self._get_queue_path(target_system)
        if not path.exists():
            return []

        items = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    item = WriteBackItem(**data)
                    if item.status == SyncStatus.PENDING:
                        items.append(item)
                except json.JSONDecodeError:
                    continue
        return items

    def update_item_status(self, write_back_id: str, status: SyncStatus, error_msg: str | None = None) -> bool:
        """큐 항목 상태 업데이트"""
        for path in self.base_path.glob("*.jsonl"):
            items = []
            updated = False

            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        item = WriteBackItem(**data)
                        if item.write_back_id == write_back_id:
                            item.status = status
                            item.last_attempt_at = datetime.utcnow()
                            if error_msg:
                                item.errors.append({
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "message": error_msg
                                })
                            updated = True
                        items.append(item)
                    except json.JSONDecodeError:
                        continue

            if updated:
                with open(path, "w", encoding="utf-8") as f:
                    for item in items:
                        f.write(item.model_dump_json() + "\n")
                return True

        return False

    def get_all_items(self, target_system: str) -> list[WriteBackItem]:
        """모든 항목 조회 (상태 무관)"""
        path = self._get_queue_path(target_system)
        if not path.exists():
            return []

        items = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    item = WriteBackItem(**data)
                    items.append(item)
                except json.JSONDecodeError:
                    continue
        return items
