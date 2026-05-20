"""OntologyRepository — JSON persistence for v3 entities."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from app.models.tenant_context import TenantContext
from app.repositories.base import BaseRepository
from storage_config import get_ontology_path


class OntologyRepository(BaseRepository):
    def __init__(self):
        super().__init__(collection_name="ontology")

    def _get_storage_path(self, ctx: TenantContext) -> Path:
        return get_ontology_path(ctx.company_id, ctx.project_id)

    def load_document(self, doc_id: str, ctx: TenantContext) -> Dict[str, Any]:
        path = self._get_file_path(ctx, doc_id)
        return self._load_json(path, default={"doc_id": doc_id, "entities": [], "relationships": []})

    def save_document(self, doc_id: str, data: Dict[str, Any], ctx: TenantContext) -> None:
        path = self._get_file_path(ctx, doc_id)
        self._save_json(path, data)

    def list_all_entities(self, ctx: TenantContext, doc_ids: List[str] | None = None) -> List[Dict[str, Any]]:
        storage_path = self._get_storage_path(ctx)
        if not storage_path.exists():
            return []
        all_entities = []
        for f in storage_path.glob("*.json"):
            if f.name == "domain_schema.json":
                continue
            if doc_ids and f.stem not in doc_ids:
                continue
            data = self._load_json(f)
            for e in data.get("entities", []):
                if "doc_id" not in e:
                    e["doc_id"] = f.stem
                all_entities.append(e)
        return all_entities

    def list_all_relationships(self, ctx: TenantContext) -> List[Dict[str, Any]]:
        storage_path = self._get_storage_path(ctx)
        if not storage_path.exists():
            return []
        all_rels = []
        for f in storage_path.glob("*.json"):
            if f.name == "domain_schema.json":
                continue
            data = self._load_json(f)
            for r in data.get("relationships", []):
                if "doc_id" not in r:
                    r["doc_id"] = f.stem
                all_rels.append(r)
        return all_rels

    def find_entities_by_type(self, entity_type: str, ctx: TenantContext) -> List[Dict[str, Any]]:
        return [e for e in self.list_all_entities(ctx) if e.get("type") == entity_type]

    def find_entities_by_property(self, prop_name: str, prop_value: Any, ctx: TenantContext,
                                   entity_type: str | None = None, doc_ids: List[str] | None = None) -> List[Dict[str, Any]]:
        from difflib import SequenceMatcher
        results = []
        for e in self.list_all_entities(ctx, doc_ids=doc_ids):
            if entity_type and e.get("type") != entity_type:
                continue
            props = e.get("properties", {})
            val = props.get(prop_name) or e.get(prop_name)
            if val is None:
                continue
            if isinstance(val, str) and isinstance(prop_value, str):
                val_l, prop_l = val.lower(), prop_value.lower()
                score = SequenceMatcher(None, val_l, prop_l).ratio()
                is_fp = val_l != prop_l and (val_l in prop_l or prop_l in val_l)
                if val_l == prop_l or (not is_fp and score >= 0.8):
                    results.append(e)
            elif val == prop_value:
                results.append(e)
        return results
