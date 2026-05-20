from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .errors import AppError
from .provenance_service import ProvenanceService
from .storage_config import resolve_project_paths
from .tenant import TenantContext
from .validators import SchemaValidator


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class BaseRepository:
    def __init__(self, ctx: TenantContext) -> None:
        self.ctx = ctx
        self.paths = resolve_project_paths(ctx.company_id, ctx.project_id)
        self.paths.ontology.mkdir(parents=True, exist_ok=True)
        self.validator = SchemaValidator()
        self.provenance = ProvenanceService(ctx.user_id)

    def _read_list(self, filename: str) -> list[dict[str, Any]]:
        path = self.paths.ontology / filename
        if not path.exists():
            return []
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, list):
            raise AppError("INVALID_DATA", f"{filename} must contain a JSON array.", 500)
        return loaded

    def _write_list(self, filename: str, rows: list[dict[str, Any]]) -> None:
        path = self.paths.ontology / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    def _scope_item(self, item: dict[str, Any]) -> dict[str, Any]:
        copied = dict(item)
        copied["company_id"] = self.ctx.company_id
        copied["project_id"] = self.ctx.project_id
        return copied

    def _is_visible(self, item: dict[str, Any]) -> bool:
        return (
            item.get("company_id") == self.ctx.company_id
            and item.get("project_id") == self.ctx.project_id
            and item.get("status", "active") != "deleted"
        )


class OntologyObjectRepository(BaseRepository):
    filename = "ontology_objects.json"

    def list(self, type_name: str | None = None, include_disabled: bool = False) -> list[dict[str, Any]]:
        rows = [item for item in self._read_list(self.filename) if self._is_visible(item)]
        if not include_disabled:
            rows = [item for item in rows if item.get("status", "active") == "active"]
        if type_name:
            rows = [item for item in rows if item.get("type") == type_name]
        return rows

    def get(self, object_id: str) -> dict[str, Any]:
        item = next((row for row in self._read_list(self.filename) if row.get("id") == object_id), None)
        if item is None or not self._is_visible(item):
            raise AppError("NOT_FOUND", f"Object not found: {object_id}", 404)
        return item

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        rows = self._read_list(self.filename)
        self.validator.validate_object_create(payload)
        scoped = self._scope_item(payload)
        scoped["id"] = self._next_id(rows, scoped["type"])
        scoped["status"] = payload.get("status", "active")
        if payload.get("provenance") is not None:
            scoped["provenance"] = self.provenance.normalize(payload.get("provenance"))
        scoped["created_by"] = self.ctx.user_id
        scoped["created_at"] = _now()
        scoped["updated_at"] = scoped["created_at"]
        rows.append(scoped)
        self._write_list(self.filename, rows)
        return scoped

    def update(self, object_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        rows = self._read_list(self.filename)
        for item in rows:
            if item.get("id") == object_id:
                if not self._is_visible(item):
                    raise AppError("NOT_FOUND", f"Object not found: {object_id}", 404)
                
                changed = False
                if payload.get("values") is not None:
                    merged_values = {**item.get("values", {}), **payload["values"]}
                    self.validator.validate_object_update(item["type"], merged_values)
                    item["values"] = merged_values
                    changed = True
                if payload.get("status") is not None:
                    item["status"] = payload["status"]
                    changed = True
                if payload.get("provenance") is not None:
                    item["provenance"] = self.provenance.normalize(payload["provenance"])
                    changed = True
                    
                if changed:
                    item["updated_at"] = _now()
                    self._write_list(self.filename, rows)
                return item
        raise AppError("NOT_FOUND", f"Object not found: {object_id}", 404)

    def disable(self, object_id: str) -> dict[str, Any]:
        return self.update(object_id, {"status": "disabled"})

    def _next_id(self, rows: list[dict[str, Any]], type_name: str) -> str:
        prefix = "".join(ch for ch in type_name.upper() if ch.isalnum())[:2] or "OB"
        existing = [
            int(row["id"][len(prefix):])
            for row in rows
            if isinstance(row.get("id"), str)
            and row["id"].startswith(prefix)
            and row["id"][len(prefix):].isdigit()
        ]
        return f"{prefix}{(max(existing) + 1) if existing else 1:03d}"


class OntologyRelationshipRepository(BaseRepository):
    filename = "ontology_relationships.json"

    def __init__(self, ctx: TenantContext) -> None:
        super().__init__(ctx)
        self.objects = OntologyObjectRepository(ctx)

    def list(self, include_disabled: bool = False) -> list[dict[str, Any]]:
        rows = [item for item in self._read_list(self.filename) if self._is_visible(item)]
        if not include_disabled:
            rows = [item for item in rows if item.get("status", "active") == "active"]
        return rows

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        source = self.objects.get(payload["source_id"])
        target = self.objects.get(payload["target_id"])
        self.validator.validate_relationship_create(payload, source["type"], target["type"])
        rows = self._read_list(self.filename)
        scoped = self._scope_item(payload)
        scoped["id"] = self._next_id(rows)
        scoped["source_type"] = source["type"]
        scoped["target_type"] = target["type"]
        scoped["origin"] = "user-created"
        scoped["status"] = payload.get("status", "active")
        if payload.get("provenance") is not None:
            scoped["provenance"] = self.provenance.normalize(payload.get("provenance"))
        scoped["created_by"] = self.ctx.user_id
        scoped["created_at"] = _now()
        scoped["updated_at"] = scoped["created_at"]
        rows.append(scoped)
        self._write_list(self.filename, rows)
        return scoped

    def disable(self, relationship_id: str) -> dict[str, Any]:
        rows = self._read_list(self.filename)
        for item in rows:
            if item.get("id") == relationship_id:
                if not self._is_visible(item):
                    raise AppError("NOT_FOUND", f"Relationship not found: {relationship_id}", 404)
                item["status"] = "disabled"
                item["updated_at"] = _now()
                self._write_list(self.filename, rows)
                return item
        raise AppError("NOT_FOUND", f"Relationship not found: {relationship_id}", 404)

    def _next_id(self, rows: list[dict[str, Any]]) -> str:
        existing = [
            int(row["id"][3:])
            for row in rows
            if isinstance(row.get("id"), str)
            and row["id"].startswith("REL")
            and row["id"][3:].isdigit()
        ]
        return f"REL{(max(existing) + 1) if existing else 1:03d}"
