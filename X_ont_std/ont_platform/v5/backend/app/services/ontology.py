"""OntologyService v3.0 — supports Provenance fields."""
from __future__ import annotations

import json
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Dict
from difflib import SequenceMatcher

from app.models.tenant_context import TenantContext
from app.repositories.ontology import OntologyRepository
from storage_config import get_ontology_path

logger = logging.getLogger(__name__)

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

    def list_entities(self, doc_id: str, ctx: TenantContext, type_filter: str | None = None,
                      offset: int = 0, limit: int = 50) -> List[Dict]:
        data = self.repo.load_document(doc_id, ctx)
        entities = data["entities"]
        if type_filter:
            entities = [e for e in entities if e.get("type") == type_filter]
        return entities[offset: offset + limit]

    def upsert_entity(self, doc_id: str, entity: Dict, ctx: TenantContext) -> Dict:
        data = self.repo.load_document(doc_id, ctx)
        existing = {e["id"]: i for i, e in enumerate(data["entities"])}
        now = datetime.now(timezone.utc).isoformat()
        if "id" not in entity or entity["id"] not in existing:
            if "id" not in entity:
                entity["id"] = "E" + uuid.uuid4().hex[:6].upper()
            entity.setdefault("created_at", now)
            entity.setdefault("created_by", ctx.user_id)
            entity.setdefault("version", 1)
            entity.setdefault("status", "active")
            entity["updated_at"] = now
            data["entities"].append(entity)
        else:
            idx = existing[entity["id"]]
            data["entities"][idx].update(entity)
            data["entities"][idx]["updated_at"] = now
            data["entities"][idx]["version"] = data["entities"][idx].get("version", 1) + 1
            entity = data["entities"][idx]
        self.repo.save_document(doc_id, data, ctx)
        return entity

    def delete_entity(self, doc_id: str, entity_id: str, ctx: TenantContext) -> bool:
        data = self.repo.load_document(doc_id, ctx)
        before = len(data["entities"])
        data["entities"] = [e for e in data["entities"] if e["id"] != entity_id]
        data["relationships"] = [r for r in data["relationships"]
                                 if r.get("from_id") != entity_id and r.get("to_id") != entity_id]
        if len(data["entities"]) == before:
            return False
        self.repo.save_document(doc_id, data, ctx)
        return True

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
        if len(data["relationships"]) == before:
            return False
        self.repo.save_document(doc_id, data, ctx)
        return True

    def _load(self, doc_id: str, ctx: TenantContext) -> Dict:
        return self.repo.load_document(doc_id, ctx)

    def filter_by_property(self, ctx: TenantContext, entity_type: str | None,
                            prop_name: str, prop_value: Any, doc_ids: List[str] | None = None) -> List[Dict]:
        return self.repo.find_entities_by_property(prop_name, prop_value, ctx,
                                                    entity_type=entity_type, doc_ids=doc_ids)

    def list_all_entities(self, ctx: TenantContext) -> List[Dict]:
        return self.repo.list_all_entities(ctx)

    def find_by_name(self, ctx: TenantContext, name_hint: str, doc_ids: List[str] | None = None) -> List[Dict]:
        import re as _re
        all_entities = self.repo.list_all_entities(ctx, doc_ids=doc_ids)
        hint_lower = name_hint.lower()

        # Multi-granularity tokens from the query
        query_tokens: set[str] = set()
        for t in _re.findall(r'[가-힣A-Za-z0-9]+', name_hint):
            if len(t) >= 2:
                query_tokens.add(t.lower())
        for t in _re.findall(r'\d{2,}', name_hint):
            query_tokens.add(t)
        for t in _re.findall(r'[가-힣]{2,}', name_hint):
            query_tokens.add(t.lower())

        stopwords = {"어떤", "무엇", "하는가", "역할", "기반", "질의응답", "차이점", "어떻게", "대한", "대해"}
        query_tokens = {t for t in query_tokens if t not in stopwords}

        logger.info("[find_by_name] query=%r all_entities=%d query_tokens=%s", name_hint, len(all_entities), query_tokens)

        results: list[Dict] = []
        for entity in all_entities:
            name_lower = entity.get("name", "").lower()
            name_compact = name_lower.replace(" ", "")

            # 1) any query token is a substring of the entity name
            if any(tok in name_compact for tok in query_tokens):
                results.append(entity)
                logger.info("[find_by_name] match(1) %s", entity.get("name"))
                continue

            # 2) any entity name token appears in the query
            entity_tokens = {
                t.lower()
                for t in _re.findall(r'[가-힣A-Za-z0-9]+', entity.get("name", ""))
                if len(t) >= 2
            }
            if any(t in hint_lower for t in entity_tokens):
                results.append(entity)
                logger.info("[find_by_name] match(2) %s", entity.get("name"))
                continue

            # 3) any query token appears in flattened entity properties
            props_flat = " ".join(str(v) for v in entity.get("properties", {}).values()).lower()
            if any(tok in props_flat for tok in query_tokens if len(tok) >= 2):
                results.append(entity)
                logger.info("[find_by_name] match(3) %s", entity.get("name"))

        logger.info("[find_by_name] matched %d results", len(results))
        results = results[:20]

        # 4) Fetch 1-hop relationships for the matched entities
        if results:
            all_rels = self.repo.list_all_relationships(ctx)
            entity_map = {e.get("entity_id") or e.get("id"): e.get("name") for e in all_entities}
            for entity in results:
                entity_id = entity.get("entity_id") or entity.get("id")
                if not entity_id:
                    continue
                related = []
                for r in all_rels:
                    from_id = r.get("from_entity_id") or r.get("from_id")
                    to_id = r.get("to_entity_id") or r.get("to_id")
                    rel_type = r.get("type") or r.get("relation") or ""
                    
                    if from_id == entity_id:
                        to_name = entity_map.get(to_id, to_id)
                        related.append(f"-[{rel_type}]-> {to_name}")
                    elif to_id == entity_id:
                        from_name = entity_map.get(from_id, from_id)
                        related.append(f"<-[{rel_type}]- {from_name}")
                        
                if related:
                    desc = entity.get("description") or str(entity.get("properties", ""))
                    rel_text = "\n[연관 관계] " + ", ".join(related)
                    entity["description"] = desc + rel_text

        return results

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
        if not ont_dir.exists():
            return []
        results = []
        for f in ont_dir.glob("*.json"):
            if f.name == "domain_schema.json":
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                results.append({
                    "doc_id": data.get("doc_id", f.stem),
                    "entity_count": len(data.get("entities", [])),
                    "relationship_count": len(data.get("relationships", [])),
                })
            except Exception:
                pass
        return results

    def get_graph(self, doc_id: str, ctx: TenantContext) -> Dict:
        data = self.repo.load_document(doc_id, ctx)
        nodes = [{"id": e["id"], "type": "ontologyNode",
                  "data": {"label": e.get("name"), "type": e.get("type"),
                           "provenance": e.get("provenance"), "status": e.get("status", "active")}}
                 for e in data["entities"]]
        edges = [{"id": r["id"], "source": r["from_id"], "target": r["to_id"], "label": r.get("relation")}
                 for r in data["relationships"]]
        return {"nodes": nodes, "edges": edges}
