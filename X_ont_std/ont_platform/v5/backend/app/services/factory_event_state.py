"""File-backed idempotency state for factory event processing."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from app.models.tenant_context import TenantContext
from app.services.customer_question_state import utc_now


class FactoryEventStateStore:
    def __init__(self, ctx: TenantContext, storage_root: str = "storage") -> None:
        self.ctx = ctx
        self.events_dir = Path(storage_root) / ctx.company_id / ctx.project_id / "events"
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self.events_log_path = self.events_dir / "factory_events.jsonl"
        self.state_path = self.events_dir / "factory_event_state.json"

    def load_state(self) -> Dict[str, Any]:
        if not self.state_path.exists():
            return {"events": {}, "processed_factory_events": {}, "last_batch": None}
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        data.setdefault("events", {})
        data.setdefault("processed_factory_events", {})
        data.setdefault("last_batch", None)
        return data

    def save_state(self, state: Dict[str, Any]) -> None:
        temp_path = self.state_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(self.state_path)

    def append_event(self, event: Dict[str, Any], status: str, duplicate: bool) -> None:
        with self.events_log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"timestamp": utc_now(), "company_id": self.ctx.company_id, "project_id": self.ctx.project_id, "user_id": self.ctx.user_id, "event": event, "status": status, "duplicate": duplicate}, ensure_ascii=False) + "\n")

    def seen_event(self, event_id: str) -> bool:
        return event_id in self.load_state().get("events", {})

    def mark_event(self, event_id: str, record: Dict[str, Any]) -> None:
        state = self.load_state()
        state["events"][event_id] = {"updated_at": utc_now(), **record}
        self.save_state(state)

    def successful_factory_event(self, factory_event_id: str) -> Optional[Dict[str, Any]]:
        record = self.load_state().get("processed_factory_events", {}).get(factory_event_id)
        if record and record.get("status") == "success":
            return record
        return None

    def mark_factory_event(self, factory_event_id: str, record: Dict[str, Any]) -> None:
        state = self.load_state()
        state["processed_factory_events"][factory_event_id] = {"updated_at": utc_now(), **record}
        self.save_state(state)

    def mark_batch(self, record: Dict[str, Any]) -> None:
        state = self.load_state()
        state["last_batch"] = {"updated_at": utc_now(), **record}
        self.save_state(state)
