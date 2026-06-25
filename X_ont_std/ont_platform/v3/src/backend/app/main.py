"""ont_platform v3.0 — FastAPI entry point."""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# .env 로드 (프로젝트 루트에서, 없어도 무시)
try:
    from dotenv import load_dotenv
    # 프로젝트 루트의 .env를 읽음 (v3/.env)
    project_root = Path(__file__).resolve().parents[3]  # src/backend/app/main.py → v3/
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
    get_sparql_translator_service,
    get_db,
)
from app.db.models import ChangeLog, WriteBackQueue
from sqlalchemy import and_
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

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

# ── /api/rdf ─────────────────────────────────────────────────────────────────

from app.api import optimized_api
app.include_router(optimized_api.router)

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

# Phase 3: Actions API
from app.api.actions import router as actions_router
app.include_router(actions_router)


# ── /api/ontology/sparql ──────────────────────────────────────────────────────

from app.services.sparql_service_v2 import SPARQLServiceV2

# Singleton 인스턴스 (rdflib 기반 표준 SPARQL)
_sparql_service = SPARQLServiceV2()

def get_sparql_service() -> SPARQLServiceV2:
    """SPARQL 서비스 주입 (rdflib 기반, W3C 표준 호환)"""
    return _sparql_service


def _detect_sparql_query_type(query: str) -> str:
    normalized = _re.sub(r"#[^\n\r]*", " ", query).upper()
    for keyword in ("SELECT", "ASK", "CONSTRUCT", "DESCRIBE"):
        if keyword in normalized:
            return keyword
    return "UNKNOWN"


def _select_vars_for_contract(raw_vars) -> list[str]:
    return [var if str(var).startswith("?") else f"?{var}" for var in (raw_vars or [])]


def _sparql_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    query: str,
    source: str = "error",
    sql_generated: str | None = None,
    error_type: str | None = None,
):
    return JSONResponse(
        status_code=status_code,
        content={
            "source": source,
            "query_type": _detect_sparql_query_type(query),
            "select_vars": [],
            "patterns": 0,
            "pattern_ids": [],
            "results": [],
            "result_count": 0,
            "execution_time_ms": 0,
            "sql_generated": sql_generated,
            "cache_hit": False,
            "warnings": [],
            "error": {
                "code": code,
                "message": message,
                "type": error_type,
            },
        },
    )


@app.post("/api/sparql/query")
@app.post("/api/ontology/sparql")
def execute_sparql_query_contract(
    body: dict,
    tenant: TenantContext = Depends(get_tenant_context),
    translator_svc = Depends(get_sparql_translator_service),
    svc: SPARQLService = Depends(get_sparql_service),
):
    query_string = body.get("query", "").strip()
    limit = body.get("limit", 1000)

    if not query_string:
        return _sparql_error_response(
            status_code=400,
            code="SPARQL_QUERY_REQUIRED",
            message="SPARQL query is required.",
            query=query_string,
        )

    try:
        result = translator_svc.execute_sparql(
            query_string,
            domain_id=tenant.project_id,
            limit=limit,
        )
        if "error" not in result:
            patterns = result.get("patterns", [])
            select_vars = result.get("select_vars", [])
            return {
                "source": "sql_translator",
                "type": result.get("query_type"),
                "query_type": result.get("query_type"),
                "select_vars": select_vars,
                "head": {"vars": [v.lstrip("?") for v in select_vars]},
                "patterns": len(patterns),
                "pattern_ids": result.get("pattern_ids", []),
                "results": result.get("results", []),
                "result_count": result.get("result_count", 0),
                "execution_time_ms": result.get("execution_time_ms"),
                "sql_generated": result.get("sql_generated"),
                "cache_hit": False,
                "warnings": [],
                "translator_used": True,
            }
    except Exception as e:
        import logging
        logging.warning(f"SQL translation failed: {str(e)}")

    fallback_started = time.time()
    result = svc.query(query_string)
    fallback_execution_time_ms = round((time.time() - fallback_started) * 1000, 2)
    if "error" in result:
        return _sparql_error_response(
            status_code=400,
            code="SPARQL_EXECUTION_ERROR",
            message=result.get("error", "SPARQL execution failed."),
            query=query_string,
            source="rdflib",
            error_type="RdflibExecutionError",
        )

    query_type = result.get("type", _detect_sparql_query_type(query_string))
    result_rows = result.get("results", [])
    select_vars = _select_vars_for_contract(result_rows[0].keys() if result_rows else [])
    result_count = result.get("count")
    if result_count is None:
        result_count = 1 if "boolean" in result else len(result.get("results", result.get("triples", [])))
    return {
        "source": "rdflib",
        "type": query_type,
        "query_type": query_type,
        "select_vars": select_vars,
        "head": {"vars": [v.lstrip("?") for v in select_vars]},
        "patterns": 0,
        "pattern_ids": [],
        "results": result.get("results", []),
        "triples": result.get("triples", []),
        "boolean": result.get("boolean"),
        "result_count": result_count,
        "execution_time_ms": result.get("execution_time_ms", fallback_execution_time_ms),
        "sql_generated": None,
        "cache_hit": False,
        "warnings": ["SQL translator did not support this query; rdflib fallback was used."],
        "translator_used": False,
    }


@app.post("/api/legacy/sparql/query")
@app.post("/api/legacy/ontology/sparql")
def execute_sparql_query(
    body: dict,
    tenant: TenantContext = Depends(get_tenant_context),
    translator_svc = Depends(get_sparql_translator_service),
    svc: SPARQLService = Depends(get_sparql_service),
):
    """SPARQL 쿼리 실행 - SQL 경로 우선, 실패 시 rdflib 폴백"""
    return execute_sparql_query_contract(body, tenant, translator_svc, svc)

    query_string = body.get("query", "").strip()
    limit = body.get("limit", 1000)

    if not query_string:
        raise HTTPException(status_code=400, detail="SPARQL 쿼리가 필요합니다.")

    try:
        # Try fast SQL translation path for hot-path patterns
        result = translator_svc.execute_sparql(
            query_string,
            domain_id=tenant.project_id,
            limit=limit
        )

        # If SQL translation succeeded (no error), return results
        if "error" not in result:
            return {
                "source": "sql_translator",
                "query_type": result.get("query_type"),
                "select_vars": result.get("select_vars"),
                "results": result.get("results", []),
                "result_count": result.get("result_count", 0),
                "execution_time_ms": result.get("execution_time_ms"),
            }
    except Exception as e:
        # Log SQL path error but continue to fallback
        import logging
        logging.warning(f"SQL translation failed: {str(e)}")

    # Fallback to rdflib for unsupported patterns
    result = svc.execute_sparql_query(query_string)
    return {
        "source": "rdflib",
        "query_id": result.query_id,
        "variables": result.variables,
        "results": result.results,
        "result_count": result.result_count,
        "execution_time_ms": result.execution_time_ms,
        "timestamp": result.query_timestamp.isoformat()
    }


@app.post("/api/ontology/entities/add-rdf")
def add_entity_rdf(
    body: dict,
    svc: SPARQLService = Depends(get_sparql_service),
):
    """엔티티를 RDF로 추가"""
    entity_id = body.get("entity_id")
    entity_type = body.get("entity_type")
    properties = body.get("properties", {})

    if not entity_id or not entity_type:
        raise HTTPException(status_code=400, detail="entity_id와 entity_type이 필요합니다.")

    triples = svc.add_entity_rdf(entity_id, entity_type, properties)
    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "triples_added": len(triples),
        "total_triples": svc.get_triple_count()
    }


@app.post("/api/ontology/relationships/add-rdf")
def add_relationship_rdf(
    body: dict,
    svc: SPARQLService = Depends(get_sparql_service),
):
    """관계를 RDF로 추가"""
    from_entity_id = body.get("from_entity_id")
    from_type = body.get("from_type")
    to_entity_id = body.get("to_entity_id")
    to_type = body.get("to_type")
    relation_type = body.get("relation_type")
    relation_props = body.get("relation_props", {})

    if not all([from_entity_id, from_type, to_entity_id, to_type, relation_type]):
        raise HTTPException(status_code=400, detail="필수 필드가 누락되었습니다.")

    triples = svc.add_relationship_rdf(
        from_entity_id, from_type, to_entity_id, to_type, relation_type, relation_props
    )
    return {
        "from": f"{from_type}/{from_entity_id}",
        "to": f"{to_type}/{to_entity_id}",
        "relation": relation_type,
        "triples_added": len(triples),
        "total_triples": svc.get_triple_count()
    }


@app.get("/api/ontology/explore")
def explore_ontology(
    entity_uri: str | None = None,
    svc: SPARQLService = Depends(get_sparql_service),
):
    """온톨로지 탐색"""
    return svc.explore_ontology(entity_uri)


@app.get("/api/ontology/{entity_uri}/relationships")
def find_relationships(
    entity_uri: str,
    svc: SPARQLService = Depends(get_sparql_service),
):
    """엔티티의 관계 찾기"""
    return svc.find_relationships(entity_uri)


@app.get("/api/ontology/entities/by-type")
def query_by_type(
    type_uri: str,
    svc: SPARQLService = Depends(get_sparql_service),
):
    """타입별로 엔티티 조회"""
    return svc.query_by_type(type_uri)


@app.post("/api/ontology/import")
def import_external_ontology(
    body: dict,
    svc: SPARQLService = Depends(get_sparql_service),
):
    """외부 온톨로지 임포트"""
    source = body.get("source")
    source_id = body.get("source_id")

    if not source or not source_id:
        raise HTTPException(status_code=400, detail="source와 source_id가 필요합니다.")

    result = svc.import_external_ontology(source, source_id, **body)
    return result


@app.get("/api/ontology/query-history")
def get_query_history(
    limit: int = 100,
    svc: SPARQLService = Depends(get_sparql_service),
):
    """쿼리 이력 조회"""
    return {"queries": svc.get_query_history(limit)}


@app.get("/api/ontology/stats")
def get_ontology_stats(
    svc: SPARQLService = Depends(get_sparql_service),
):
    """온톨로지 통계"""
    return {
        "total_triples": svc.get_triple_count(),
        "last_updated": None
    }


# ── /api/changelog ────────────────────────────────────────────────────────────

@app.get("/api/changelog/history")
def get_changelog_history(
    entity_id: Optional[str] = None,
    domain_id: Optional[str] = None,
    action_type: Optional[str] = None,
    sync_status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    """
    Changelog 조회

    **필터**:
    - entity_id: 엔티티 ID
    - domain_id: 도메인 ID
    - action_type: 액션 유형
    - sync_status: 동기화 상태 (PENDING, SYNCED, FAILED)
    - date_from: 시작 날짜 (ISO8601)
    - date_to: 종료 날짜 (ISO8601)

    **페이징**:
    - page: 페이지 번호 (기본값: 1)
    - page_size: 페이지당 항목 수 (기본값: 50)
    """
    query = db.query(ChangeLog)

    if entity_id:
        query = query.filter(ChangeLog.entity_id == entity_id)
    if domain_id:
        query = query.filter(ChangeLog.domain_id == domain_id)
    if action_type:
        query = query.filter(ChangeLog.action_type == action_type)
    if sync_status:
        query = query.filter(ChangeLog.sync_status == sync_status)
    if date_from:
        query = query.filter(ChangeLog.timestamp >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(ChangeLog.timestamp <= datetime.fromisoformat(date_to))

    total = query.count()
    items = query.order_by(ChangeLog.timestamp.desc())\
                 .offset((page - 1) * page_size)\
                 .limit(page_size)\
                 .all()

    return {
        "items": [
            {
                "id": item.id,
                "entity_id": item.entity_id,
                "entity_type": item.entity_type,
                "domain_id": item.domain_id,
                "action_type": item.action_type,
                "actor": item.actor,
                "old_status": item.old_status,
                "new_status": item.new_status,
                "timestamp": item.timestamp.isoformat(),
                "sync_status": item.sync_status,
                "target_system": item.target_system,
                "sync_timestamp": item.sync_timestamp.isoformat() if item.sync_timestamp else None,
                "error_message": item.error_message,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ── /api/writeback ────────────────────────────────────────────────────────────

@app.get("/api/writeback/queue")
def get_writeback_queue(
    status: Optional[str] = None,
    domain_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    WriteBack 큐 상태 조회

    **필터**:
    - status: 상태 (PENDING, SENT, CONFIRMED, FAILED)
    - domain_id: 도메인 ID (옵션)
    - limit: 반환할 최대 항목 수 (기본값: 100)
    """
    query = db.query(WriteBackQueue)

    if status:
        query = query.filter(WriteBackQueue.status == status)

    total = query.count()
    items = query.limit(limit).all()

    pending = db.query(WriteBackQueue).filter(WriteBackQueue.status == "PENDING").count()
    confirmed = db.query(WriteBackQueue).filter(WriteBackQueue.status == "CONFIRMED").count()
    failed = db.query(WriteBackQueue).filter(WriteBackQueue.status == "FAILED").count()

    return {
        "pending": pending,
        "confirmed": confirmed,
        "failed": failed,
        "items": [
            {
                "id": item.id,
                "action_execution_id": item.action_execution_id,
                "target_system": item.target_system,
                "status": item.status,
                "retry_count": item.retry_count,
                "created_at": item.created_at.isoformat(),
                "sent_at": item.sent_at.isoformat() if item.sent_at else None,
                "error_message": item.error_message,
            }
            for item in items
        ],
    }


@app.get("/api/writeback/statistics")
def get_writeback_statistics(db: Session = Depends(get_db)):
    """
    WriteBack 통계 조회
    """
    total = db.query(WriteBackQueue).count()
    confirmed = db.query(WriteBackQueue).filter(WriteBackQueue.status == "CONFIRMED").count()
    failed = db.query(WriteBackQueue).filter(WriteBackQueue.status == "FAILED").count()
    pending = total - confirmed - failed

    success_rate = (confirmed / total) if total > 0 else 0

    avg_retry = 0
    if total > 0:
        retry_sum = sum(item.retry_count for item in db.query(WriteBackQueue).all())
        avg_retry = retry_sum / total

    last_sync = db.query(WriteBackQueue).filter(
        WriteBackQueue.status == "CONFIRMED"
    ).order_by(WriteBackQueue.sent_at.desc()).first()

    return {
        "total_processed": total,
        "success_rate": round(success_rate, 4),
        "failure_count": failed,
        "pending_count": pending,
        "avg_retry_attempts": round(avg_retry, 2),
        "last_sync_time": last_sync.sent_at.isoformat() if last_sync and last_sync.sent_at else None,
    }


# ── /api/changelog / /api/writeback ─────────────────────────────────────────────

@app.get("/api/changelog/history", tags=["monitoring"])
def get_changelog_history(
    entity_id: str | None = None,
    domain_id: str | None = None,
    action_type: str | None = None,
    sync_status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db = Depends(get_db)
):
    from app.db.models import ChangeLog
    from datetime import datetime

    query = db.query(ChangeLog)
    
    if entity_id:
        query = query.filter(ChangeLog.entity_id == entity_id)
    if domain_id:
        query = query.filter(ChangeLog.domain_id == domain_id)
    if action_type:
        query = query.filter(ChangeLog.action_type == action_type)
    if sync_status:
        query = query.filter(ChangeLog.sync_status == sync_status)
    if date_from:
        try:
            query = query.filter(ChangeLog.timestamp >= datetime.fromisoformat(date_from.replace('Z', '+00:00')))
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(ChangeLog.timestamp <= datetime.fromisoformat(date_to.replace('Z', '+00:00')))
        except ValueError:
            pass

    total = query.count()
    items = query.order_by(ChangeLog.timestamp.desc())\
                 .offset((page - 1) * page_size)\
                 .limit(page_size)\
                 .all()

    formatted_items = []
    for item in items:
        formatted_items.append({
            "id": item.id,
            "entity_id": item.entity_id,
            "entity_type": item.entity_type,
            "domain_id": item.domain_id,
            "action_type": item.action_type,
            "actor": item.actor,
            "source": item.source,
            "timestamp": item.timestamp.isoformat() if item.timestamp else None,
            "sync_status": item.sync_status,
            "target_system": item.target_system,
            "error_message": item.error_message
        })

    return {
        "items": formatted_items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@app.get("/api/writeback/queue", tags=["monitoring"])
def get_writeback_queue(
    status: str | None = None,
    domain_id: str | None = None,
    limit: int = 100,
    db = Depends(get_db)
):
    from app.db.models import WriteBackQueue, ActionExecution

    pending = db.query(WriteBackQueue).filter(WriteBackQueue.status == "PENDING").count()
    confirmed = db.query(WriteBackQueue).filter(WriteBackQueue.status == "CONFIRMED").count()
    failed = db.query(WriteBackQueue).filter(WriteBackQueue.status == "FAILED").count()

    query = db.query(WriteBackQueue)
    if status:
        query = query.filter(WriteBackQueue.status == status)
    if domain_id:
        query = query.join(ActionExecution).filter(ActionExecution.domain_id == domain_id)

    items = query.order_by(WriteBackQueue.created_at.desc()).limit(limit).all()

    formatted_items = []
    for item in items:
        formatted_items.append({
            "id": item.id,
            "action_execution_id": item.action_execution_id,
            "target_system": item.target_system,
            "status": item.status,
            "retry_count": item.retry_count,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "sent_at": item.sent_at.isoformat() if item.sent_at else None,
            "error_message": item.error_message
        })

    return {
        "pending": pending,
        "confirmed": confirmed,
        "failed": failed,
        "items": formatted_items
    }


@app.get("/api/writeback/statistics", tags=["monitoring"])
def get_writeback_statistics(db = Depends(get_db)):
    from app.db.models import WriteBackQueue
    from sqlalchemy import func

    total = db.query(WriteBackQueue).count()
    confirmed = db.query(WriteBackQueue).filter(WriteBackQueue.status == "CONFIRMED").count()
    failed = db.query(WriteBackQueue).filter(WriteBackQueue.status == "FAILED").count()

    success_rate = confirmed / total if total > 0 else 0.0

    avg_retry = db.query(func.avg(WriteBackQueue.retry_count)).scalar() or 0.0
    avg_retry = float(avg_retry)

    last_sync = db.query(func.max(WriteBackQueue.sent_at)).scalar()
    last_sync_time = last_sync.isoformat() if last_sync else None

    return {
        "total_processed": total,
        "success_rate": round(success_rate, 4),
        "failure_count": failed,
        "avg_retry_attempts": round(avg_retry, 2),
        "last_sync_time": last_sync_time
    }



# ── /api/health ───────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "3.0.0"}

