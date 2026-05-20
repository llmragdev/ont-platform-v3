"""OntologyRepository — Handles persistence of entities and relationships."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

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
        """Scan all ontology files in the project to list all entities."""
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
            entities = data.get("entities", [])
            for e in entities:
                # Inject doc_id context if not present
                if "doc_id" not in e:
                    e["doc_id"] = f.stem
                all_entities.append(e)
        return all_entities

    def list_all_relationships(self, ctx: TenantContext) -> List[Dict[str, Any]]:
        """Scan all ontology files in the project to list all relationships."""
        storage_path = self._get_storage_path(ctx)
        if not storage_path.exists():
            return []

        all_rels = []
        for f in storage_path.glob("*.json"):
            if f.name == "domain_schema.json":
                continue
            data = self._load_json(f)
            rels = data.get("relationships", [])
            for r in rels:
                if "doc_id" not in r:
                    r["doc_id"] = f.stem
                all_rels.append(r)
        return all_rels

    def find_entities_by_type(self, entity_type: str, ctx: TenantContext) -> List[Dict[str, Any]]:
        all_entities = self.list_all_entities(ctx)
        return [e for e in all_entities if e.get("type") == entity_type]

    def find_entities_by_property(self, prop_name: str, prop_value: Any, ctx: TenantContext, entity_type: str | None = None, doc_ids: List[str] | None = None) -> List[Dict[str, Any]]:
        from difflib import SequenceMatcher
        all_entities = self.list_all_entities(ctx, doc_ids=doc_ids)
        results = []
        for e in all_entities:
            # 1. Type Filter
            if entity_type and e.get("type") != entity_type:
                continue
            
            # 2. Property Match (Fuzzy for string values)
            props = e.get("properties", {})
            val = props.get(prop_name) or e.get(prop_name)
            
            if val is None: continue
            
            if isinstance(val, str) and isinstance(prop_value, str):
                val_lower = val.lower()
                prop_lower = prop_value.lower()
                score = SequenceMatcher(None, val_lower, prop_lower).ratio()
                is_containment_false_positive = (
                    val_lower != prop_lower
                    and (val_lower in prop_lower or prop_lower in val_lower)
                )
                if val_lower == prop_lower or (not is_containment_false_positive and score >= 0.8):
                    results.append(e)
            elif val == prop_value:
                results.append(e)
        return results
