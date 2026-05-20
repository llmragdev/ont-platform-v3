from __future__ import annotations

import json
from typing import Any

from .provenance_service import utc_now
from .storage_config import resolve_project_paths
from .tenant import TenantContext


class WriteBackService:
    def __init__(self, ctx: TenantContext) -> None:
        self.ctx = ctx
        self.paths = resolve_project_paths(ctx.company_id, ctx.project_id)
        self.writeback_dir = self.paths.ontology / "writeback"
        self.adapter_dir = self.paths.ontology / "external_writeback"

    def request(
        self,
        *,
        operation: str,
        object_id: str,
        payload: dict[str, Any],
        source: str = "ontology_action",
        target_system: str = "simulated_erp",
        metadata: dict[str, Any] | None = None,
        execute: bool = True,
    ) -> dict[str, Any]:
        rows = self._read_log()
        record = {
            "id": f"WB{len(rows) + 1:04d}",
            "company_id": self.ctx.company_id,
            "project_id": self.ctx.project_id,
            "source": source,
            "target_system": target_system,
            "operation": operation,
            "object_id": object_id,
            "payload": payload,
            "metadata": metadata or {},
            "status": "pending",
            "requested_by": self.ctx.user_id,
            "requested_at": utc_now(),
        }
        if execute:
            record = self._simulate_external_adapter(record)
        rows.append(record)
        self._write_log(rows)
        return record

    def list_requests(self) -> list[dict[str, Any]]:
        return self._read_log()

    def _simulate_external_adapter(self, record: dict[str, Any]) -> dict[str, Any]:
        self.adapter_dir.mkdir(parents=True, exist_ok=True)
        adapter_record = {
            "erp_sync_id": f"ERP-{record['object_id']}",
            "writeback_id": record["id"],
            "last_action": record["operation"],
            "timestamp": utc_now(),
            "data": record["payload"],
        }
        sync_file = self.adapter_dir / f"{record['object_id']}_sync.json"
        sync_file.write_text(json.dumps(adapter_record, ensure_ascii=False, indent=2), encoding="utf-8")
        return record | {"status": "succeeded", "completed_at": adapter_record["timestamp"]}

    def _read_log(self) -> list[dict[str, Any]]:
        path = self.writeback_dir / "writeback_requests.json"
        if not path.exists():
            return []
        loaded = json.loads(path.read_text(encoding="utf-8"))
        return loaded if isinstance(loaded, list) else []

    def _write_log(self, rows: list[dict[str, Any]]) -> None:
        path = self.writeback_dir / "writeback_requests.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
