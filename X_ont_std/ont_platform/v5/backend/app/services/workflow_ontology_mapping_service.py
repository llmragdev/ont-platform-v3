"""Workflow-to-ontology mapping template registry."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from app.models.tenant_context import TenantContext
from storage_config import get_ontology_path


MAPPING_DIR = Path(__file__).resolve().parents[1] / "config" / "workflow_ontology_mappings"


class WorkflowOntologyMappingService:
    def __init__(self, mapping_dir: Path | None = None) -> None:
        self.mapping_dir = mapping_dir or MAPPING_DIR

    def list_mappings(self) -> list[dict[str, Any]]:
        mappings = [self._load_file(path) for path in sorted(self.mapping_dir.glob("*.json"))]
        mappings.sort(key=lambda item: item.get("name", ""))
        return mappings

    def get_mapping(self, mapping_id: str) -> dict[str, Any]:
        for mapping in self.list_mappings():
            if mapping.get("mapping_id") == mapping_id:
                return mapping
        raise KeyError(f"Workflow ontology mapping not found: {mapping_id}")

    def install_schema(self, ctx: TenantContext, mapping_id: str) -> dict[str, Any]:
        mapping = self.get_mapping(mapping_id)
        ontology_path = get_ontology_path(ctx.company_id, ctx.project_id)
        ontology_path.mkdir(parents=True, exist_ok=True)
        schema_path = ontology_path / "domain_schema.json"
        schema = self._load_schema(schema_path)

        entity_added = self._merge_by_name(schema.setdefault("entity_types", []), mapping.get("entity_types", []))
        relation_added = self._merge_by_name(schema.setdefault("relation_types", []), mapping.get("relation_types", []))
        schema.setdefault("installed_workflow_mappings", [])
        installed = {
            "mapping_id": mapping["mapping_id"],
            "mapping_version": mapping.get("mapping_version"),
            "workflow_template_id": mapping.get("workflow_template_id"),
            "workflow_executor": mapping.get("workflow_executor"),
        }
        self._upsert_installed_mapping(schema["installed_workflow_mappings"], installed)

        schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "status": "installed",
            "mapping_id": mapping_id,
            "schema_path": str(schema_path),
            "entity_types_added": entity_added,
            "relation_types_added": relation_added,
            "entity_types_total": len(schema.get("entity_types", [])),
            "relation_types_total": len(schema.get("relation_types", [])),
        }

    def _load_file(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _load_schema(self, schema_path: Path) -> dict[str, Any]:
        if not schema_path.exists():
            return {"entity_types": [], "relation_types": []}
        try:
            loaded = json.loads(schema_path.read_text(encoding="utf-8"))
            return loaded if isinstance(loaded, dict) else {"entity_types": [], "relation_types": []}
        except json.JSONDecodeError:
            return {"entity_types": [], "relation_types": []}

    def _merge_by_name(self, target: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> int:
        added = 0
        index = {str(item.get("name")): item for item in target}
        for item in incoming:
            name = str(item.get("name") or "")
            if not name:
                continue
            if name in index:
                index[name].update(copy.deepcopy(item))
            else:
                target.append(copy.deepcopy(item))
                added += 1
        return added

    def _upsert_installed_mapping(self, target: list[dict[str, Any]], incoming: dict[str, Any]) -> None:
        existing = next((item for item in target if item.get("mapping_id") == incoming.get("mapping_id")), None)
        if existing:
            existing.update(incoming)
        else:
            target.append(incoming)
