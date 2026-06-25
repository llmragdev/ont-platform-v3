"""Write factory repeated fault outcomes into project ontology JSON."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List

from app.models.tenant_context import TenantContext
from app.repositories.ontology import OntologyRepository


FACTORY_DOC_ID = "factory-repeated-faults"
FACTORY_MAPPING_ID = "factory.repeated_fault_response.v1"


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _slug(value: Any) -> str:
    text = str(value or "unknown").strip().lower()
    text = re.sub(r"[^0-9a-zA-Z가-힣]+", "-", text).strip("-")
    return text[:64] or "unknown"


class FactoryOntologyWriter:
    def __init__(self, repo: OntologyRepository | None = None) -> None:
        self.repo = repo or OntologyRepository()

    def write_event_result(
        self,
        *,
        ctx: TenantContext,
        event: Dict[str, Any],
        request_id: str,
        mode: str,
        repeated: bool,
        response_result: Dict[str, Any] | None,
        maintenance_result: Dict[str, Any] | None,
        workflow_run_id: str | None = None,
    ) -> Dict[str, Any]:
        doc = self.repo.load_document(FACTORY_DOC_ID, ctx)
        doc.setdefault("doc_id", FACTORY_DOC_ID)
        doc.setdefault("domain", "manufacturing")
        doc.setdefault("mapping_id", FACTORY_MAPPING_ID)
        doc.setdefault("mapping_version", "1.0.0")
        entities: List[Dict[str, Any]] = doc.setdefault("entities", [])
        relationships: List[Dict[str, Any]] = doc.setdefault("relationships", [])
        before_entities = len(entities)
        before_relationships = len(relationships)

        event_id = event.get("factory_event_id") or event.get("id")
        factory_id = f"factory-{_slug(event.get('factory_name'))}"
        line_id = f"line-{_slug(event.get('factory_name'))}-{_slug(event.get('line_name'))}"
        step_id = f"step-{_slug(event.get('line_name'))}-{_slug(event.get('process_step'))}"
        equipment_id = f"eq-{_slug(event.get('equipment_name'))}"
        fault_id = f"fault-{_slug(event.get('equipment_name'))}-{_slug(event.get('fault_message') or event.get('category'))}"
        request_entity_id = f"sr-{event_id}"
        response_id = ((response_result or {}).get("external_response_id")) or f"dry-response-{event_id}-{request_id}"
        task_id = ((maintenance_result or {}).get("external_task_id")) or (f"dry-task-{event_id}-{request_id}" if repeated else None)

        self._upsert_entity(entities, {"id": factory_id, "type": "Factory", "name": event.get("factory_name"), "properties": {"site_code": "SEJONG-BP", "location": "세종", "owner_team": "생산운영팀"}}, ctx)
        self._upsert_entity(entities, {"id": line_id, "type": "ProductionLine", "name": event.get("line_name"), "properties": {"line_code": "LINE-3", "status": "running"}}, ctx)
        self._upsert_entity(entities, {"id": step_id, "type": "ProcessStep", "name": event.get("process_step"), "properties": {"status": "active"}}, ctx)
        self._upsert_entity(entities, {"id": equipment_id, "type": "Equipment", "name": event.get("equipment_name"), "properties": {"status": "attention" if repeated else "observed", "last_checked_at": _now_iso()}}, ctx)
        self._upsert_entity(
            entities,
            {
                "id": request_entity_id,
                "type": "ServiceRequest",
                "name": event.get("title") or event_id,
                "properties": {
                    "external_id": event_id,
                    "category": event.get("category"),
                    "title": event.get("title"),
                    "content": event.get("content"),
                    "requester": event.get("reporter"),
                    "occurred_at": event.get("occurred_at"),
                    "severity": event.get("severity"),
                    "status": "processed",
                    "mode": mode,
                    "workflow_run_id": workflow_run_id,
                },
            },
            ctx,
        )
        self._upsert_entity(
            entities,
            {
                "id": fault_id,
                "type": "FaultEvent",
                "name": f"{event.get('equipment_name')} {event.get('fault_message') or '이상'}",
                "properties": {
                    "fault_code": _slug(event.get("fault_message") or event.get("category")),
                    "message": event.get("fault_message"),
                    "first_seen_at": event.get("occurred_at"),
                    "last_seen_at": event.get("occurred_at"),
                    "occurrence_count": 2 if repeated else 1,
                    "status": "repeated" if repeated else "observed",
                    "severity": event.get("severity"),
                },
            },
            ctx,
        )
        if task_id:
            self._upsert_entity(entities, {"id": f"mt-{task_id}", "type": "MaintenanceTask", "name": "정비팀 확인 건", "properties": {"task_id": task_id, "assigned_team": "정비팀", "priority": "high" if repeated else "medium", "status": "created" if maintenance_result else "dry_run", "created_at": _now_iso()}}, ctx)
        if event.get("category") == "quality_issue":
            quality_id = f"qi-{event_id}"
            self._upsert_entity(entities, {"id": quality_id, "type": "QualityIssue", "name": event.get("title"), "properties": {"issue_id": event_id, "defect_type": event.get("fault_message") or "불량 증가", "detected_at": event.get("occurred_at"), "severity": event.get("severity"), "status": "observed"}}, ctx)
            self._upsert_relationship(relationships, quality_id, "possibly_caused_by", fault_id)
            self._upsert_relationship(relationships, quality_id, "detected_by", equipment_id)
            self._upsert_relationship(relationships, quality_id, "affects_line", line_id)

        self._upsert_relationship(relationships, factory_id, "has_line", line_id)
        self._upsert_relationship(relationships, line_id, "has_step", step_id)
        self._upsert_relationship(relationships, step_id, "uses", equipment_id)
        self._upsert_relationship(relationships, request_entity_id, "reports", fault_id)
        self._upsert_relationship(relationships, fault_id, "affects", equipment_id)
        if task_id:
            self._upsert_relationship(relationships, fault_id, "creates", f"mt-{task_id}")

        self.repo.save_document(FACTORY_DOC_ID, doc, ctx)
        return {
            "doc_id": FACTORY_DOC_ID,
            "mapping_id": FACTORY_MAPPING_ID,
            "entities_before": before_entities,
            "entities_after": len(entities),
            "relationships_before": before_relationships,
            "relationships_after": len(relationships),
            "factory_event_id": event_id,
            "fault_event_id": fault_id,
            "repeated": repeated,
        }

    def _upsert_entity(self, entities: List[Dict[str, Any]], entity: Dict[str, Any], ctx: TenantContext) -> None:
        now = _now_iso()
        existing = next((item for item in entities if item.get("id") == entity["id"]), None)
        if existing:
            existing["name"] = entity.get("name", existing.get("name"))
            existing["type"] = entity.get("type", existing.get("type"))
            existing.setdefault("properties", {}).update(entity.get("properties") or {})
            existing["updated_at"] = now
            existing["version"] = int(existing.get("version") or 1) + 1
            return
        entity.setdefault("properties", {})
        entity.setdefault("provenance", {"source": "workflow", "scenario": "factory-repeated-fault", "mapping_id": FACTORY_MAPPING_ID, "confidence": 1.0})
        entity.setdefault("status", "active")
        entity.setdefault("version", 1)
        entity.setdefault("created_by", ctx.user_id)
        entity.setdefault("created_at", now)
        entity.setdefault("updated_at", now)
        entities.append(entity)

    def _upsert_relationship(self, relationships: List[Dict[str, Any]], from_id: str, relation: str, to_id: str) -> None:
        rel_id = f"rel-{from_id}-{relation}-{to_id}"
        if any(item.get("id") == rel_id for item in relationships):
            return
        relationships.append({"id": rel_id, "from_id": from_id, "relation": relation, "to_id": to_id, "properties": {"source": "workflow", "scenario": "factory-repeated-fault", "mapping_id": FACTORY_MAPPING_ID}})
