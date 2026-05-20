from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class ProvenanceService:
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id

    def normalize(self, provenance: dict[str, Any] | None, *, source_kind: str = "manual") -> dict[str, Any]:
        payload = dict(provenance or {})
        payload.setdefault("source_kind", source_kind)
        payload.setdefault("confidence", 1.0)
        payload.setdefault("created_by", self.user_id)
        payload.setdefault("created_at", utc_now())
        return payload

    def for_action(self, action_name: str, params: dict[str, Any]) -> dict[str, Any]:
        return self.normalize(
            {
                "source_kind": "action",
                "doc_id": params.get("doc_id"),
                "page_no": params.get("page_no"),
                "chunk_id": params.get("chunk_id"),
            },
            source_kind="action",
        ) | {"action_name": action_name}
