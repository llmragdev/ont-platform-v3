"""File-backed idempotency state for Scenario 1 customer question events."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from app.models.tenant_context import TenantContext


def utc_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


class CustomerQuestionStateStore:
    """Persists event and question processing state under tenant storage."""

    def __init__(self, ctx: TenantContext, storage_root: str = "storage"):
        self.ctx = ctx
        self.events_dir = Path(storage_root) / ctx.company_id / ctx.project_id / "events"
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self.events_log_path = self.events_dir / "customer_question_events.jsonl"
        self.state_path = self.events_dir / "customer_question_state.json"

    def load_state(self) -> Dict[str, Any]:
        if not self.state_path.exists():
            return {"events": {}, "processed_questions": {}, "last_batch": None}
        try:
            with self.state_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            data = {}
        data.setdefault("events", {})
        data.setdefault("processed_questions", {})
        data.setdefault("last_batch", None)
        return data

    def save_state(self, state: Dict[str, Any]) -> None:
        temp_path = self.state_path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        temp_path.replace(self.state_path)

    def append_event(self, event: Dict[str, Any], status: str, duplicate: bool) -> None:
        record = {
            "timestamp": utc_now(),
            "company_id": self.ctx.company_id,
            "project_id": self.ctx.project_id,
            "user_id": self.ctx.user_id,
            "event": event,
            "status": status,
            "duplicate": duplicate,
        }
        with self.events_log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def seen_event(self, event_id: str) -> bool:
        return event_id in self.load_state().get("events", {})

    def mark_event(self, event_id: str, record: Dict[str, Any]) -> None:
        state = self.load_state()
        state["events"][event_id] = {"updated_at": utc_now(), **record}
        self.save_state(state)

    def successful_question(self, question_id: str) -> Optional[Dict[str, Any]]:
        record = self.load_state().get("processed_questions", {}).get(question_id)
        if record and record.get("status") == "success":
            return record
        return None

    def mark_question(self, question_id: str, record: Dict[str, Any]) -> None:
        state = self.load_state()
        state["processed_questions"][question_id] = {"updated_at": utc_now(), **record}
        self.save_state(state)

    def mark_batch(self, record: Dict[str, Any]) -> None:
        state = self.load_state()
        state["last_batch"] = {"updated_at": utc_now(), **record}
        self.save_state(state)
