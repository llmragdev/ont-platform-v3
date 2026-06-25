"""JsonOntologyRepository — BaseRepositoryInterface implementation over JSON files.

This wraps OntologyRepository to satisfy the ABC interface.
Swap this for SqliteOntologyRepository in v4.0 without changing business logic.
"""
from __future__ import annotations

from app.models.ontology import OntologyEntityV3
from app.models.tenant_context import TenantContext
from app.repositories.base_interface import BaseRepositoryInterface
from app.repositories.ontology import OntologyRepository


class JsonOntologyRepository(BaseRepositoryInterface[OntologyEntityV3]):
    def __init__(self) -> None:
        self._repo = OntologyRepository()

    def get(self, id: str, ctx: TenantContext) -> OntologyEntityV3 | None:
        all_entities = self._repo.list_all_entities(ctx)
        for raw in all_entities:
            if raw.get("id") == id:
                return OntologyEntityV3.from_dict(raw)
        return None

    def list(self, ctx: TenantContext, doc_id: str | None = None, **filters) -> list[OntologyEntityV3]:
        if doc_id:
            data = self._repo.load_document(doc_id, ctx)
            raw_list = data.get("entities", [])
        else:
            raw_list = self._repo.list_all_entities(ctx)

        entities = [OntologyEntityV3.from_dict(e) for e in raw_list]

        entity_type = filters.get("entity_type")
        if entity_type:
            entities = [e for e in entities if e.type == entity_type]
        status = filters.get("status")
        if status:
            entities = [e for e in entities if e.status == status]
        return entities

    def save(self, item: OntologyEntityV3, ctx: TenantContext) -> OntologyEntityV3:
        doc_id = (item.provenance.source_doc_id if item.provenance else None) or "default"
        data = self._repo.load_document(doc_id, ctx)
        raw = item.model_dump(mode="json")
        existing = {e["id"]: i for i, e in enumerate(data["entities"])}
        if item.id in existing:
            data["entities"][existing[item.id]] = raw
        else:
            data["entities"].append(raw)
        self._repo.save_document(doc_id, data, ctx)
        return item

    def delete(self, id: str, ctx: TenantContext) -> bool:
        all_docs = self._repo.list_all_entities(ctx)
        doc_ids = {e.get("doc_id") for e in all_docs if e.get("id") == id and e.get("doc_id")}
        deleted = False
        for doc_id in doc_ids:
            data = self._repo.load_document(doc_id, ctx)
            before = len(data["entities"])
            data["entities"] = [e for e in data["entities"] if e["id"] != id]
            if len(data["entities"]) < before:
                self._repo.save_document(doc_id, data, ctx)
                deleted = True
        return deleted
