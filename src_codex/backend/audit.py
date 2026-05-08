from __future__ import annotations

from datetime import datetime


class AuditService:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def record(self, event_type: str, actor: dict, object_type: str, object_id: str, detail: dict | None = None) -> dict:
        event = {
            "id": f"E{len(self.events) + 1:04d}",
            "event_type": event_type,
            "actor": actor.get("email", "system"),
            "object_type": object_type,
            "object_id": object_id,
            "detail": detail or {},
            "occurred_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }
        self.events.insert(0, event)
        return event

    def list_events(self) -> list[dict]:
        return self.events

