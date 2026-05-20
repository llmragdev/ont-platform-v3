"""ont_platform v3.0 — FastAPI entry point."""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# .env 로드 (없어도 무시)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from app.models.tenant_context import TenantContext
from app.services.document import DocumentService
from app.services.ontology import OntologyService
from app.services.vector_search import VectorSearchService
from app.services.query_planner import QueryPlannerService
from app.dependencies import (
    get_document_service,
    get_ontology_service,
    get_vector_search_service,
    get_query_planner_service,
    get_tenant_context,
)

app = FastAPI(title="ont_platform v3.0", version="3.0.0")

# HMAC auth middleware (active only when HMAC_SECRET env var is set)
from app.middleware.auth import HmacAuthMiddleware
app.add_middleware(HmacAuthMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── /api/documents ────────────────────────────────────────────────────────────

@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    shard_id: str = "default",
    ctx: TenantContext = Depends(get_tenant_context),
    svc: DocumentService = Depends(get_document_service),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")
    data = await file.read()
    return svc.upload(data, file.filename, ctx, shard_id)


@app.get("/api/documents")
def list_documents(
    ctx: TenantContext = Depends(get_tenant_context),
    svc: DocumentService = Depends(get_document_service),
):
    return svc.list(ctx)


@app.delete("/api/documents/{doc_id}")
def delete_document(
    doc_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    svc: DocumentService = Depends(get_document_service),
):
    ok = svc.delete(doc_id, ctx)
    if not ok:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
    return {"deleted": doc_id}


# ── /api/ontology ─────────────────────────────────────────────────────────────

@app.get("/api/ontology")
def list_ontology_documents(
    ctx: TenantContext = Depends(get_tenant_context),
    svc: OntologyService = Depends(get_ontology_service),
):
    return svc.list_documents(ctx)


@app.get("/api/ontology/schema")
def get_schema(
    ctx: TenantContext = Depends(get_tenant_context),
    svc: OntologyService = Depends(get_ontology_service),
):
    return svc.get_schema(ctx)


@app.get("/api/ontology/{doc_id}/entities")
def list_entities(
    doc_id: str,
    type_filter: str | None = None,
    offset: int = 0,
    limit: int = 50,
    ctx: TenantContext = Depends(get_tenant_context),
    svc: OntologyService = Depends(get_ontology_service),
):
    return svc.list_entities(doc_id, ctx, type_filter, offset, limit)


@app.post("/api/ontology/{doc_id}/entities")
def create_entity(
    doc_id: str,
    entity: dict,
    ctx: TenantContext = Depends(get_tenant_context),
    svc: OntologyService = Depends(get_ontology_service),
):
    return svc.upsert_entity(doc_id, entity, ctx)


@app.put("/api/ontology/{doc_id}/entities/{entity_id}")
def update_entity(
    doc_id: str,
    entity_id: str,
    entity: dict,
    ctx: TenantContext = Depends(get_tenant_context),
    svc: OntologyService = Depends(get_ontology_service),
):
    entity["id"] = entity_id
    return svc.upsert_entity(doc_id, entity, ctx)


@app.delete("/api/ontology/{doc_id}/entities/{entity_id}")
def delete_entity(
    doc_id: str,
    entity_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    svc: OntologyService = Depends(get_ontology_service),
):
    ok = svc.delete_entity(doc_id, entity_id, ctx)
    if not ok:
        raise HTTPException(status_code=404, detail="엔티티를 찾을 수 없습니다.")
    return {"deleted": entity_id}


@app.get("/api/ontology/{doc_id}/relationships")
def list_relationships(
    doc_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    svc: OntologyService = Depends(get_ontology_service),
):
    return svc.list_relationships(doc_id, ctx)


@app.post("/api/ontology/{doc_id}/relationships")
def create_relationship(
    doc_id: str,
    rel: dict,
    ctx: TenantContext = Depends(get_tenant_context),
    svc: OntologyService = Depends(get_ontology_service),
):
    return svc.add_relationship(doc_id, rel, ctx)


@app.delete("/api/ontology/{doc_id}/relationships/{rel_id}")
def delete_relationship(
    doc_id: str,
    rel_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    svc: OntologyService = Depends(get_ontology_service),
):
    ok = svc.delete_relationship(doc_id, rel_id, ctx)
    if not ok:
        raise HTTPException(status_code=404, detail="관계를 찾을 수 없습니다.")
    return {"deleted": rel_id}


@app.get("/api/ontology/{doc_id}/graph")
def get_graph(
    doc_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    svc: OntologyService = Depends(get_ontology_service),
):
    return svc.get_graph(doc_id, ctx)


# ── /api/search ───────────────────────────────────────────────────────────────

@app.post("/api/search")
def search(
    body: dict,
    ctx: TenantContext = Depends(get_tenant_context),
    svc: VectorSearchService = Depends(get_vector_search_service),
):
    query = body.get("query", "")
    k = int(body.get("top_k", 3))
    shard_id = body.get("shard_id")
    return svc.search(query, ctx, k=k, shard_id=shard_id)


# ── /api/hybrid ───────────────────────────────────────────────────────────────

from app.api import hybrid
app.include_router(hybrid.router)


# ── /api/integration-test ─────────────────────────────────────────────────────

from app.api import integration_test
app.include_router(integration_test.router)


# ── /api/audit ────────────────────────────────────────────────────────────────

from app.services.audit import list_audit_events

@app.get("/api/audit/events")
def audit_events(limit: int = 200, ctx: TenantContext = Depends(get_tenant_context)):
    return {"events": list_audit_events(ctx, limit=limit)}


# ── /api/ontology schema management ──────────────────────────────────────────

import re as _re
from storage_config import get_ontology_path as _get_ontology_path


def _schema_path(ctx: TenantContext) -> Path:
    p = _get_ontology_path(ctx.company_id, ctx.project_id) / "domain_schema.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _load_domain_json(ctx: TenantContext) -> dict:
    p = _schema_path(ctx)
    if not p.exists():
        return {"entity_types": [], "relation_types": []}
    return json.loads(p.read_text(encoding="utf-8"))


def _save_domain_json(data: dict, ctx: TenantContext) -> None:
    _schema_path(ctx).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── /api/ontology (create new namespace) ─────────────────────────────────────

@app.post("/api/ontology")
def create_ontology_namespace(
    body: dict,
    ctx: TenantContext = Depends(get_tenant_context),
):
    doc_id = (body.get("doc_id") or "").strip()
    if not doc_id:
        raise HTTPException(status_code=400, detail="doc_id가 필요합니다.")
    doc_path = _get_ontology_path(ctx.company_id, ctx.project_id) / f"{doc_id}.json"
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    if doc_path.exists():
        raise HTTPException(status_code=409, detail=f"문서 '{doc_id}'가 이미 존재합니다.")
    doc_path.write_text(
        json.dumps({"doc_id": doc_id, "entities": [], "relationships": []}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"doc_id": doc_id, "entity_count": 0, "relationship_count": 0}


@app.post("/api/ontology/mgmt/schema/entity-types")
def add_entity_type(body: dict, ctx: TenantContext = Depends(get_tenant_context)):
    name = (body.get("name") or "").strip().upper()
    if not name or not _re.match(r"^[A-Z][A-Z0-9_]*$", name):
        raise HTTPException(status_code=400, detail="유효한 엔티티 유형명이 필요합니다.")
    data = _load_domain_json(ctx)
    if any(t["name"] == name for t in data.get("entity_types", [])):
        raise HTTPException(status_code=409, detail=f"엔티티 유형 '{name}'이 이미 존재합니다.")
    new_type = {"name": name, "description": body.get("description", ""), "properties": body.get("properties", [])}
    data.setdefault("entity_types", []).append(new_type)
    _save_domain_json(data, ctx)
    return {"name": name, "description": new_type["description"], "is_builtin": False, "properties": new_type["properties"]}


@app.delete("/api/ontology/mgmt/schema/entity-types/{name}")
def delete_entity_type(name: str, ctx: TenantContext = Depends(get_tenant_context)):
    data = _load_domain_json(ctx)
    before = len(data.get("entity_types", []))
    data["entity_types"] = [t for t in data.get("entity_types", []) if t["name"] != name.upper()]
    if len(data["entity_types"]) == before:
        raise HTTPException(status_code=404, detail=f"엔티티 유형 '{name}'을 찾을 수 없습니다.")
    _save_domain_json(data, ctx)
    return {"status": "deleted", "name": name.upper()}


@app.post("/api/ontology/mgmt/schema/relation-types")
def add_relation_type(body: dict, ctx: TenantContext = Depends(get_tenant_context)):
    name = (body.get("name") or "").strip().upper()
    if not name:
        raise HTTPException(status_code=400, detail="관계 유형명이 필요합니다.")
    data = _load_domain_json(ctx)
    if any(r["name"] == name for r in data.get("relation_types", [])):
        raise HTTPException(status_code=409, detail=f"관계 유형 '{name}'이 이미 존재합니다.")
    new_rel = {"name": name, "from_type": (body.get("from_type") or "").strip().upper(),
               "to_type": (body.get("to_type") or "").strip().upper()}
    data.setdefault("relation_types", []).append(new_rel)
    _save_domain_json(data, ctx)
    return new_rel


@app.delete("/api/ontology/mgmt/schema/relation-types/{name}")
def delete_relation_type(name: str, ctx: TenantContext = Depends(get_tenant_context)):
    data = _load_domain_json(ctx)
    before = len(data.get("relation_types", []))
    data["relation_types"] = [r for r in data.get("relation_types", []) if r["name"] != name.upper()]
    if len(data["relation_types"]) == before:
        raise HTTPException(status_code=404, detail=f"관계 유형 '{name}'을 찾을 수 없습니다.")
    _save_domain_json(data, ctx)
    return {"status": "deleted", "name": name.upper()}


# ── /api/workflow, /api/workflow-graphs ───────────────────────────────────────

from app.api.workflow import router as workflow_router, graph_router as wfg_router
app.include_router(workflow_router)
app.include_router(wfg_router)


# ── /api/metrics ──────────────────────────────────────────────────────────────

from app.api.metrics import router as metrics_router
app.include_router(metrics_router)


# ── /api/health ───────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "3.0.0"}
