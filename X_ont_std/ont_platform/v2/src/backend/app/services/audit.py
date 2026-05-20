"""Append-only audit logging scoped by TenantContext."""
from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.models.tenant_context import TenantContext
from storage_config import ensure_project_dirs, get_project_root

AUDIT_LOG_FILE = "audit_log.jsonl"


def list_audit_events(ctx: TenantContext, limit: int = 200) -> list[dict[str, Any]]:
    """Read the latest audit events for the current tenant (newest first)."""
    log_path = get_project_root(ctx.company_id, ctx.project_id) / AUDIT_LOG_FILE
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding="utf-8").splitlines()
    events = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return list(reversed(events))[:limit]


def append_audit_event(
    ctx: TenantContext,
    action: str,
    resource_type: str,
    resource_id: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write one audit event to the current project's JSONL log."""
    ensure_project_dirs(ctx.company_id, ctx.project_id)
    event = {
        "event_id": f"audit-{uuid.uuid4().hex[:12]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "company_id": ctx.company_id,
        "project_id": ctx.project_id,
        "user_id": ctx.user_id,
        "role": ctx.role,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details or {},
    }
    log_path = get_project_root(ctx.company_id, ctx.project_id) / AUDIT_LOG_FILE
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event
