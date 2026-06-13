"""Write Scenario 1 workflow outcomes into project ontology JSON."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from app.models.tenant_context import TenantContext
from app.repositories.ontology import OntologyRepository


SERVICE_REQUEST_DOC_ID = "service-requests"
SCENARIO1_MAPPING_ID = "scenario1.customer_question_auto_reply.v1"


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


class WorkflowOntologyWriter:
    """Upserts service request workflow trace objects and relationships."""

    def __init__(self, repo: OntologyRepository | None = None) -> None:
        self.repo = repo or OntologyRepository()

    def write_scenario1_batch_result(
        self,
        *,
        ctx: TenantContext,
        graph: Dict[str, Any],
        run_id: str,
        run_started_at: str,
        run_finished_at: str,
        mode: str,
        batch_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        document = self.repo.load_document(SERVICE_REQUEST_DOC_ID, ctx)
        document.setdefault("doc_id", SERVICE_REQUEST_DOC_ID)
        document.setdefault("domain", "scenario1")
        document.setdefault("mapping_id", SCENARIO1_MAPPING_ID)
        document.setdefault("mapping_version", "1.0.0")
        entities: List[Dict[str, Any]] = document.setdefault("entities", [])
        relationships: List[Dict[str, Any]] = document.setdefault("relationships", [])

        before_entities = len(entities)
        before_relationships = len(relationships)
        touched_questions: list[str] = []

        workflow_execution_id = f"wfe-{run_id}"
        self._upsert_entity(
            entities,
            {
                "id": workflow_execution_id,
                "type": "WorkflowExecution",
                "name": f"{graph.get('name', 'Workflow')} 실행",
                "properties": {
                    "run_id": run_id,
                    "graph_id": graph.get("id"),
                    "graph_name": graph.get("name"),
                    "executor": (graph.get("runtime") or {}).get("executor"),
                    "mode": mode,
                    "status": "succeeded" if batch_result.get("errors", 0) == 0 else "failed",
                    "checked": batch_result.get("checked"),
                    "started": batch_result.get("started"),
                    "skipped": batch_result.get("skipped"),
                    "errors": batch_result.get("errors"),
                    "started_at": run_started_at,
                    "finished_at": run_finished_at,
                    "ontology_mapping_id": SCENARIO1_MAPPING_ID,
                },
            },
            ctx,
        )

        for item in batch_result.get("items") or []:
            question_id = item.get("draft", {}).get("question_id") or _question_id_from_event(item)
            if not question_id:
                continue
            touched_questions.append(question_id)
            service_request_id = f"sr-{question_id}"
            auto_reply_id = f"reply-{question_id}-{run_id}"
            mcp = item.get("mcp") or {}
            draft = item.get("draft") or {}
            event_title = _event_title(item)
            external_comment_id = ((mcp.get("result") or {}).get("external_comment_id"))
            external_comment_entity_id = f"ext-{external_comment_id}" if external_comment_id else f"ext-dryrun-{question_id}-{run_id}"

            self._upsert_entity(
                entities,
                {
                    "id": service_request_id,
                    "type": "ServiceRequest",
                    "name": event_title or question_id,
                    "properties": {
                        "external_id": question_id,
                        "source_system": "customer_board",
                        "status": "replied" if mcp.get("status") == "success" else "drafted",
                        "title": event_title,
                        "content": _event_content(item),
                        "requester": _event_author(item),
                        "mode": mode,
                        "last_processed_at": run_finished_at,
                    },
                },
                ctx,
            )
            self._upsert_entity(
                entities,
                {
                    "id": auto_reply_id,
                    "type": "AutoReply",
                    "name": "자동 답변",
                    "properties": {
                        "message": draft.get("reply_message"),
                        "mode": mode,
                        "status": "posted" if mcp.get("status") == "success" else mcp.get("status", "drafted"),
                        "confidence": draft.get("confidence"),
                        "generated_by": "llm_webhook",
                        "request_id": item.get("request_id"),
                        "created_at": draft.get("created_at"),
                    },
                },
                ctx,
            )
            self._upsert_entity(
                entities,
                {
                    "id": external_comment_entity_id,
                    "type": "ExternalComment",
                    "name": "customer_board 댓글",
                    "properties": {
                        "external_comment_id": external_comment_id,
                        "external_thread_id": ((mcp.get("result") or {}).get("external_thread_id")),
                        "url": ((mcp.get("result") or {}).get("url")),
                        "source_system": "customer_board",
                        "status": mcp.get("status"),
                        "audit_id": mcp.get("audit_id"),
                        "posted_at": run_finished_at if mcp.get("status") == "success" else None,
                    },
                },
                ctx,
            )

            self._upsert_relationship(relationships, service_request_id, "handled_by", workflow_execution_id)
            self._upsert_relationship(relationships, workflow_execution_id, "generated", auto_reply_id)
            self._upsert_relationship(relationships, auto_reply_id, "posted_as", external_comment_entity_id)
            self._upsert_relationship(relationships, service_request_id, "has_reply", auto_reply_id)

        self.repo.save_document(SERVICE_REQUEST_DOC_ID, document, ctx)
        return {
            "doc_id": SERVICE_REQUEST_DOC_ID,
            "entities_before": before_entities,
            "entities_after": len(entities),
            "relationships_before": before_relationships,
            "relationships_after": len(relationships),
            "entities_upserted": len(entities) - before_entities,
            "relationships_upserted": len(relationships) - before_relationships,
            "question_ids": touched_questions,
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
        entity.setdefault(
            "provenance",
            {"source": "workflow", "scenario": "scenario1", "mapping_id": SCENARIO1_MAPPING_ID, "confidence": 1.0},
        )
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
        relationships.append(
            {
                "id": rel_id,
                "from_id": from_id,
                "relation": relation,
                "to_id": to_id,
                "properties": {"source": "workflow", "scenario": "scenario1", "mapping_id": SCENARIO1_MAPPING_ID},
            }
        )


def _question_id_from_event(item: Dict[str, Any]) -> str | None:
    event_id = str(item.get("event_id") or "")
    if event_id.startswith("batch-"):
        parts = event_id.split("-")
        if len(parts) >= 2:
            return "-".join(parts[1:3]) if parts[1] == "q" and len(parts) > 2 else parts[1]
    return None


def _event_title(item: Dict[str, Any]) -> str | None:
    draft = item.get("draft") or {}
    return draft.get("question_id") or item.get("event_id")


def _event_content(item: Dict[str, Any]) -> str | None:
    draft = item.get("draft") or {}
    return draft.get("reply_message")


def _event_author(item: Dict[str, Any]) -> str | None:
    return "customer"
