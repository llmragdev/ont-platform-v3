"""OntologyService — Complete version supporting Sprint 07 & 08."""
from __future__ import annotations

import json
import uuid
import logging
from pathlib import Path
from typing import Any, List, Dict, Optional
from difflib import SequenceMatcher

from app.models.tenant_context import TenantContext
from app.repositories.ontology import OntologyRepository
from storage_config import get_ontology_path

BUILTIN_ENTITY_TYPES = [
    {"name": "PERSON",       "description": "인물, 직책, 역할",       "properties": []},
    {"name": "ORGANIZATION", "description": "회사, 기관",              "properties": []},
    {"name": "PRODUCT",      "description": "제품, 서비스",            "properties": []},
    {"name": "METRIC",       "description": "수치, 지표",              "properties": ["value", "unit", "period"]},
    {"name": "CONCEPT",      "description": "개념, 방법론",            "properties": []},
    {"name": "CATEGORY",     "description": "분류, 그룹",             "properties": []},
    {"name": "EVENT",        "description": "사건, 일정",             "properties": ["date"]},
    {"name": "LOCATION",     "description": "지역, 리전",             "properties": []},
]

class OntologyService:
    def __init__(self, repo: OntologyRepository | None = None):
        self.repo = repo or OntologyRepository()

    # ── Entities ──
    def list_entities(self, doc_id: str, ctx: TenantContext, type_filter: str | None = None, offset: int = 0, limit: int = 50) -> List[Dict]:
        data = self.repo.load_document(doc_id, ctx)
        entities = data["entities"]
        if type_filter:
            entities = [e for e in entities if e.get("type") == type_filter]
        return entities[offset : offset + limit]

    def upsert_entity(self, doc_id: str, entity: Dict, ctx: TenantContext) -> Dict:
        data = self.repo.load_document(doc_id, ctx)
        existing = {e["id"]: i for i, e in enumerate(data["entities"])}
        if "id" not in entity or entity["id"] not in existing:
            if "id" not in entity:
                entity["id"] = "E" + uuid.uuid4().hex[:6].upper()
            data["entities"].append(entity)
        else:
            idx = existing[entity["id"]]
            data["entities"][idx].update(entity)
            entity = data["entities"][idx]
        self.repo.save_document(doc_id, data, ctx)
        return entity

    def delete_entity(self, doc_id: str, entity_id: str, ctx: TenantContext) -> bool:
        data = self.repo.load_document(doc_id, ctx)
        before = len(data["entities"])
        data["entities"] = [e for e in data["entities"] if e["id"] != entity_id]
        data["relationships"] = [r for r in data["relationships"] if r.get("from_id") != entity_id and r.get("to_id") != entity_id]
        if len(data["entities"]) == before: return False
        self.repo.save_document(doc_id, data, ctx)
        return True

    # ── Relationships ──
    def list_relationships(self, doc_id: str, ctx: TenantContext) -> List[Dict]:
        return self.repo.load_document(doc_id, ctx)["relationships"]

    def add_relationship(self, doc_id: str, rel: Dict, ctx: TenantContext) -> Dict:
        data = self.repo.load_document(doc_id, ctx)
        if "id" not in rel:
            rel["id"] = "R" + uuid.uuid4().hex[:6].upper()
        data["relationships"].append(rel)
        self.repo.save_document(doc_id, data, ctx)
        return rel

    def delete_relationship(self, doc_id: str, rel_id: str, ctx: TenantContext) -> bool:
        data = self.repo.load_document(doc_id, ctx)
        before = len(data["relationships"])
        data["relationships"] = [r for r in data["relationships"] if r["id"] != rel_id]
        if len(data["relationships"]) == before: return False
        self.repo.save_document(doc_id, data, ctx)
        return True

    # ── Query Planner Support ──
    def _load(self, doc_id: str, ctx: TenantContext) -> Dict:
        """Compatibility helper for older tests and internal callers."""
        return self.repo.load_document(doc_id, ctx)

    def filter_by_property(self, ctx: TenantContext, entity_type: str | None, prop_name: str, prop_value: Any, doc_ids: List[str] | None = None) -> List[Dict]:
        return self.repo.find_entities_by_property(prop_name, prop_value, ctx, entity_type=entity_type, doc_ids=doc_ids)

    def list_all_entities(self, ctx: TenantContext) -> List[Dict]:
        return self.repo.list_all_entities(ctx)

    def find_by_name(self, ctx: TenantContext, name_hint: str, doc_ids: List[str] | None = None) -> List[Dict]:
        all_entities = self.repo.list_all_entities(ctx, doc_ids=doc_ids)
        scored = [(e, SequenceMatcher(None, e.get("name", "").lower(), name_hint.lower()).ratio()) for e in all_entities]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, score in scored if score >= 0.5]

    # ── Metadata & Schema ──
    def get_schema(self, ctx: TenantContext) -> Dict:
        schema_path = get_ontology_path(ctx.company_id, ctx.project_id) / "domain_schema.json"
        domain = {}
        if schema_path.exists():
            try:
                domain = json.loads(schema_path.read_text(encoding="utf-8"))
            except Exception:
                domain = {}
        return {
            "builtin_entity_types": BUILTIN_ENTITY_TYPES,
            "domain_entity_types": domain.get("entity_types", []),
            "domain_relation_types": domain.get("relation_types", []),
        }

    def list_documents(self, ctx: TenantContext) -> List[Dict]:
        ont_dir = get_ontology_path(ctx.company_id, ctx.project_id)
        if not ont_dir.exists(): return []
        results = []
        for f in ont_dir.glob("*.json"):
            if f.name == "domain_schema.json": continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                results.append({
                    "doc_id": data.get("doc_id", f.stem),
                    "entity_count": len(data.get("entities", [])),
                    "relationship_count": len(data.get("relationships", [])),
                })
            except: pass
        return results
    
    def get_graph(self, doc_id: str, ctx: TenantContext) -> Dict:
        data = self.repo.load_document(doc_id, ctx)
        nodes = [{"id": e["id"], "type": "ontologyNode", "data": {"label": e.get("name"), "type": e.get("type")}} for e in data["entities"]]
        edges = [{"id": r["id"], "source": r["from_id"], "target": r["to_id"], "label": r.get("relation")} for r in data["relationships"]]
        return {"nodes": nodes, "edges": edges}
