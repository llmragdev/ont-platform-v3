"""OntologyRepository — JSON persistence for v3 entities."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from app.models.tenant_context import TenantContext
from app.repositories.base import BaseRepository
from app.db.ontology_index import OntologyIndex
from storage_config import get_ontology_path


class OntologyRepository(BaseRepository):
    def __init__(self):
        super().__init__(collection_name="ontology")
        self._index_cache: Dict[str, OntologyIndex] = {}

    def _get_storage_path(self, ctx: TenantContext) -> Path:
        return get_ontology_path(ctx.company_id, ctx.project_id)

    def _get_index(self, ctx: TenantContext) -> OntologyIndex:
        """Get or create index for tenant"""
        key = f"{ctx.company_id}_{ctx.project_id}"
        if key not in self._index_cache:
            self._index_cache[key] = OntologyIndex(ctx.company_id, ctx.project_id)
        return self._index_cache[key]

    def load_document(self, doc_id: str, ctx: TenantContext) -> Dict[str, Any]:
        path = self._get_file_path(ctx, doc_id)
        return self._load_json(path, default={"doc_id": doc_id, "entities": [], "relationships": []})

    def save_document(self, doc_id: str, data: Dict[str, Any], ctx: TenantContext) -> None:
        path = self._get_file_path(ctx, doc_id)
        self._save_json(path, data)

        # Index entities and relationships
        index = self._get_index(ctx)
        index.delete_doc_index(doc_id)
        index.index_entities_batch(data.get("entities", []), doc_id)
        index.index_relationships_batch(data.get("relationships", []), doc_id)

    def list_all_entities(self, ctx: TenantContext, doc_ids: List[str] | None = None) -> List[Dict[str, Any]]:
        """Query entities from index (fast), fallback to JSON if needed"""
        index = self._get_index(ctx)

        # Query from index
        indexed = index.query_entities(doc_ids=doc_ids)
        if indexed:
            # Reconstruct entities with full data from index
            all_entities = []
            for row in indexed:
                entity = {
                    "entity_id": row.get("entity_id"),
                    "doc_id": row.get("doc_id"),
                    "type": row.get("entity_type"),
                    "name": row.get("name"),
                }
                if row.get("properties"):
                    import json
                    try:
                        props = json.loads(row.get("properties"))
                        entity["properties"] = props
                        if "description" in props:
                            entity["description"] = props["description"]
                    except Exception:
                        pass
                all_entities.append(entity)
            return all_entities

        # Fallback: Load from JSON and index
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
            if not isinstance(data, dict):
                continue
            for e in data.get("entities", []):
                if "doc_id" not in e:
                    e["doc_id"] = f.stem
                all_entities.append(e)

            # Index for next time
            index.index_entities_batch(data.get("entities", []), f.stem)

        return all_entities

    def list_all_relationships(self, ctx: TenantContext) -> List[Dict[str, Any]]:
        """Query relationships from index (fast), fallback to JSON if needed"""
        index = self._get_index(ctx)

        # Query from index
        indexed = index.query_relationships()
        if indexed:
            all_rels = []
            for row in indexed:
                relation = {
                    "relation_id": row.get("relation_id"),
                    "doc_id": row.get("doc_id"),
                    "from_entity_id": row.get("from_entity_id"),
                    "to_entity_id": row.get("to_entity_id"),
                    "type": row.get("relation_type"),
                }
                if row.get("properties"):
                    relation["properties"] = row.get("properties")
                all_rels.append(relation)
            return all_rels

        # Fallback: Load from JSON and index
        storage_path = self._get_storage_path(ctx)
        if not storage_path.exists():
            return []
        all_rels = []
        for f in storage_path.glob("*.json"):
            if f.name == "domain_schema.json":
                continue
            data = self._load_json(f)
            if not isinstance(data, dict):
                continue
            for r in data.get("relationships", []):
                if "doc_id" not in r:
                    r["doc_id"] = f.stem
                all_rels.append(r)

            # Index for next time
            index.index_relationships_batch(data.get("relationships", []), f.stem)

        return all_rels

    def find_entities_by_type(self, entity_type: str, ctx: TenantContext) -> List[Dict[str, Any]]:
        """Find entities by type using index (fast)"""
        index = self._get_index(ctx)
        indexed = index.query_entities(entity_type=entity_type)

        if indexed:
            all_entities = []
            for row in indexed:
                entity = {
                    "entity_id": row.get("entity_id"),
                    "doc_id": row.get("doc_id"),
                    "type": row.get("entity_type"),
                    "name": row.get("name"),
                }
                if row.get("properties"):
                    import json
                    try:
                        props = json.loads(row.get("properties"))
                        entity["properties"] = props
                        if "description" in props:
                            entity["description"] = props["description"]
                    except Exception:
                        pass
                all_entities.append(entity)
            return all_entities

        # Fallback: Linear search and index
        results = [e for e in self.list_all_entities(ctx) if e.get("type") == entity_type]
        return results

    def find_entities_by_property(self, prop_name: str, prop_value: Any, ctx: TenantContext,
                                   entity_type: str | None = None, doc_ids: List[str] | None = None) -> List[Dict[str, Any]]:
        """Find entities by property using index (faster for large datasets)"""
        from difflib import SequenceMatcher

        index = self._get_index(ctx)
        indexed = index.query_entities_by_property(
            prop_name, prop_value, entity_type=entity_type, doc_ids=doc_ids
        )

        if indexed:
            results = []
            for row in indexed:
                entity = {
                    "entity_id": row.get("entity_id"),
                    "doc_id": row.get("doc_id"),
                    "type": row.get("entity_type"),
                    "name": row.get("name"),
                }
                if row.get("properties"):
                    import json
                    try:
                        props = json.loads(row.get("properties"))
                        entity["properties"] = props
                        if "description" in props:
                            entity["description"] = props["description"]
                    except Exception:
                        pass
                results.append(entity)
            return results

        # Fallback: Linear search
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
