from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

import json as _json

from .app_context import AppContext
from .auth import current_user_key, issue_token, verify_password
from .errors import AppError
from .schemas import (AskRequest, EntityCreate, EntityTypeCreate, EntityUpdate,
                      HybridAskRequest, LoginRequest, OntologyExtractRequest,
                      OntologyRelationshipCreate, RagAskRequest,
                      RelationshipCreateRequest, RelationTypeCreate,
                      SearchRequest, WorkflowGraphRequest, WorkflowRequest)
from . import ontology_store, telemetry
from .tenant import TenantManager, get_tenant_manager, require_known_user, require_permission


# .env 탐색 순서: 1) DOTENV_PATH 환경변수  2) backend/.env  3) F:\ai_std_dev\.env
_BACKEND_DIR = Path(__file__).resolve().parents[1]
_candidates = [
    os.environ.get("DOTENV_PATH"),
    str(_BACKEND_DIR / ".env"),
    r"F:\ai_std_dev\.env",
]
for _p in _candidates:
    if _p and Path(_p).exists():
        load_dotenv(_p, override=False)
        break

# Promote GEMINI_API_KEY1 → GEMINI_API_KEY for the SDK
if not os.environ.get("GEMINI_API_KEY"):
    for fallback in ("GEMINI_API_KEY1", "GEMINI_API_KEY2", "GEMINI_API_KEY3"):
        value = os.environ.get(fallback)
        if value:
            os.environ["GEMINI_API_KEY"] = value
            break


app = FastAPI(title="Claude 통합 - 온톨로지 AI 백엔드", version="1.0.0")
telemetry.setup(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_app_context = AppContext()


def get_context() -> AppContext:
    return _app_context


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.get("/api/health")
def health(ctx: AppContext = Depends(get_context)) -> dict:
    return {
        "status": "ok",
        "llm_provider": ctx.llm.provider,
        "llm_model": ctx.llm.model,
        "llm": ctx.llm.health(),
        "telemetry_enabled": telemetry.is_enabled(),
    }


@app.get("/api/me")
def me(user: str = Depends(current_user_key), ctx: AppContext = Depends(get_context)) -> dict:
    return ctx.me(user)


@app.get("/api/users")
def users(ctx: AppContext = Depends(get_context)) -> dict:
    return {"users": ctx.list_users()}


# ── 테넌트 API (Phase 1 — JSON 기반) ─────────────────────────────────────────

@app.get("/api/tenant/companies", tags=["tenant"])
def tenant_companies(tm: TenantManager = Depends(get_tenant_manager)) -> dict:
    """테넌트(회사) 목록."""
    return {"companies": tm.list_companies()}


@app.get("/api/tenant/users", tags=["tenant"])
def tenant_users(tm: TenantManager = Depends(get_tenant_manager)) -> dict:
    """테넌트 사용자 목록 (권한 플래그 포함). UserSwitcher 초기 로드용."""
    return {"users": tm.list_users()}


@app.get("/api/tenant/users/{user_id}", tags=["tenant"])
def tenant_user_detail(
    user_id: str,
    tm: TenantManager = Depends(get_tenant_manager),
) -> dict:
    """테넌트 사용자 상세 + 런타임 권한."""
    user = tm.get_user(user_id)
    return {**user, "permissions": tm.resolve_permissions(user)}


@app.get("/api/tenant/users/{user_id}/permissions", tags=["tenant"])
def tenant_user_permissions(
    user_id: str,
    tm: TenantManager = Depends(get_tenant_manager),
) -> dict:
    """권한 플래그만 반환 (DoD D08~D10 검증용)."""
    return {"user_id": user_id, "permissions": tm.get_permissions(user_id)}


@app.get("/api/tenant/projects", tags=["tenant"])
def tenant_projects(
    user_id: str = Query(...),
    tm: TenantManager = Depends(get_tenant_manager),
) -> dict:
    """사용자 소속 프로젝트 목록."""
    return {"projects": tm.list_projects_for_user(user_id)}


# ── 온톨로지 객체 유형 ─────────────────────────────────────────────────────────

@app.get("/api/ontology/object-types")
def object_types(ctx: AppContext = Depends(get_context)) -> dict:
    return {"object_types": ctx.ontology.object_types()}


@app.get("/api/ontology/schema", tags=["ontology"])
def ontology_schema(ctx: AppContext = Depends(get_context)) -> dict:
    """온톨로지 스키마 전체 반환 (object_types / relationship_types / action_types)."""
    return ctx.ontology.schema


@app.get("/api/ontology/graph", tags=["ontology"])
def ontology_graph(
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
) -> dict:
    """전체 객체+관계를 React Flow 형식으로 반환."""
    ctx.user(user)  # 인증 확인
    return ctx.ontology.get_full_graph()


@app.post("/api/ontology/relationships", tags=["ontology"])
def ontology_relationship_create(
    body: RelationshipCreateRequest,
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
) -> dict:
    """관계 인스턴스 추가 (AccountManager 이상)."""
    user_obj = ctx.user(user)
    ctx.policy.assert_can_manage_ontology(user_obj, "write")
    result = ctx.ontology.add_relationship_instance(
        body.relationship_type, body.source_id, body.target_id, body.values
    )
    ctx.audit.record(
        "ONTOLOGY_RELATIONSHIP_CREATED", user_obj, "OntologyRelationship",
        result["rel_id"], result,
    )
    return {"status": "created", **result}


@app.delete("/api/ontology/relationships/{rel_id}", tags=["ontology"])
def ontology_relationship_delete(
    rel_id: str,
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
) -> dict:
    """관계 인스턴스 삭제 (Admin 전용)."""
    user_obj = ctx.user(user)
    ctx.policy.assert_can_manage_ontology(user_obj, "delete")
    ctx.ontology.delete_relationship_instance(rel_id)
    ctx.audit.record(
        "ONTOLOGY_RELATIONSHIP_DELETED", user_obj, "OntologyRelationship", rel_id, {}
    )
    return {"status": "deleted", "rel_id": rel_id}


@app.get("/api/objects/customers")
def customers(user: str = Depends(current_user_key), ctx: AppContext = Depends(get_context)) -> dict:
    return {"customers": ctx.list_customers(user)}


@app.get("/api/objects/orders")
def orders(user: str = Depends(current_user_key), ctx: AppContext = Depends(get_context)) -> dict:
    return {"orders": ctx.list_orders(user)}


@app.get("/api/objects/orders/{order_id}/context")
def order_context(
    order_id: str,
    customer_id: str | None = Query(default=None),
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
) -> dict:
    return ctx.order_context(order_id, user, customer_id)


@app.post("/api/search")
def search(
    body: SearchRequest,
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
) -> dict:
    return ctx.search_documents(body.query, user, body.top_k)


@app.post("/api/ask")
def ask(
    body: AskRequest,
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
) -> dict:
    return ctx.ask(body.question, user)


@app.post("/api/rag/ask", tags=["documents"])
def rag_ask(
    body: RagAskRequest,
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
) -> dict:
    """업로드된 PDF 문서만으로 답변 (온톨로지 컨텍스트 불필요)."""
    return ctx.ask_rag(body.question, user)


# --- PDF 문서 업로드 + 벡터 RAG -------------------------------------------


@app.post("/api/documents/upload", tags=["documents"])
async def documents_upload(
    file: UploadFile = File(...),
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
    _perm: None = Depends(require_permission("can_upload_doc")),
    _user_check: None = Depends(require_known_user(get_context)),
) -> dict:
    """PDF 파일 업로드 → Chroma 자동 벡터화."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise AppError("INVALID_FILE", "PDF 파일만 업로드할 수 있습니다.", 400)
    contents = await file.read()
    try:
        info = ctx.upload_document(contents, file.filename)
    except Exception as exc:
        raise AppError("INGEST_FAILED", f"벡터화 실패: {exc}", 500) from exc
    return {"status": "ok", **info}


@app.get("/api/documents", tags=["documents"])
def documents_list(
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
    tm: TenantManager = Depends(get_tenant_manager),
    _user_check: None = Depends(require_known_user(get_context)),
) -> dict:
    """업로드된 PDF 문서 목록 (테넌트 격리 적용)."""
    try:
        tenant_user = tm.get_user(user)
        company_id = tenant_user["company_id"]
    except Exception:
        company_id = None  # 테넌트 미등록 사용자 → 전체 반환 (기존 호환)
    docs = ctx.vector_search.list_documents(company_id=company_id)
    return {"documents": docs, "vector_search": ctx.vector_search.health()}


@app.delete("/api/documents/{doc_id}", tags=["documents"])
def documents_delete(
    doc_id: str,
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
    _perm: None = Depends(require_permission("can_delete_doc")),
    _user_check: None = Depends(require_known_user(get_context)),
) -> dict:
    """PDF 문서 삭제 (벡터 DB + 파일)."""
    success = ctx.delete_uploaded_document(doc_id)
    if not success:
        raise AppError("NOT_FOUND", f"문서 {doc_id}를 찾을 수 없습니다.", 404)
    return {"status": "deleted", "doc_id": doc_id}


@app.get("/api/workflow/queue")
def workflow_queue(
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
) -> dict:
    return {"queue": ctx.workflow.queue(ctx.user(user))}


@app.post("/api/workflow/execute")
def workflow_execute(
    body: WorkflowRequest,
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
) -> dict:
    user_obj = ctx.user(user)
    result = ctx.workflow.execute(user_obj, body.action, body.order_id, body.payload or {})
    return {"result": result, "queue": ctx.workflow.queue(user_obj)}


@app.get("/api/audit/events")
def audit_events(ctx: AppContext = Depends(get_context)) -> dict:
    return {"events": ctx.audit.list_events()}


@app.post("/api/system/reset")
def system_reset(ctx: AppContext = Depends(get_context)) -> dict:
    """인메모리 상태를 초기 시드로 되돌린다. 교육·E2E·데모용."""
    ctx.reset()
    return {"status": "reset"}


@app.post("/api/auth/login")
def auth_login(body: LoginRequest, ctx: AppContext = Depends(get_context)) -> dict:
    """이메일+비밀번호 → JWT 발급. 교육용 데모 계정 4종.

    실패 응답: 401 INVALID_CREDENTIALS
    """
    users = ctx.raw.get("users", {})
    target_key: str | None = None
    for key, user in users.items():
        if user.get("email", "").lower() == body.email.lower():
            target_key = key
            break
    if target_key is None or not verify_password(body.password, users[target_key].get("password_hash", "")):
        raise AppError("INVALID_CREDENTIALS", "이메일 또는 비밀번호가 일치하지 않습니다.", 401)
    token = issue_token(target_key)
    user = {k: v for k, v in users[target_key].items() if k != "password_hash"}
    return {"access_token": token, "token_type": "Bearer", "user": user}


# --- 워크플로우 그래프 (Phase 1: CRUD) -------------------------------------


@app.get("/api/workflow-graphs", tags=["workflow-graph"])
def workflow_graphs_list(
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
) -> dict:
    """워크플로우 그래프 목록 (최근 갱신순)."""
    user_obj = ctx.user(user)
    return {"graphs": ctx.workflow_graph.list_graphs(user_obj)}


@app.get("/api/workflow-graphs/{graph_id}", tags=["workflow-graph"])
def workflow_graphs_get(
    graph_id: str,
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
) -> dict:
    """워크플로우 그래프 단건 조회."""
    user_obj = ctx.user(user)
    return ctx.workflow_graph.get_graph(user_obj, graph_id)


@app.post("/api/workflow-graphs", tags=["workflow-graph"])
def workflow_graphs_save(
    body: WorkflowGraphRequest,
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
) -> dict:
    """워크플로우 그래프 저장 (신규 생성 또는 업데이트).

    /docs에서 이 엔드포인트를 열면 example 두 개가 미리 채워져 있어
    'Try it out → Execute' 한 번에 실행됩니다.
    """
    user_obj = ctx.user(user)
    payload = body.model_dump(exclude_none=True)
    return ctx.workflow_graph.save_graph(user_obj, payload)


@app.delete("/api/workflow-graphs/{graph_id}", tags=["workflow-graph"])
def workflow_graphs_delete(
    graph_id: str,
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
) -> dict:
    """워크플로우 그래프 삭제 (Admin 전용)."""
    user_obj = ctx.user(user)
    ctx.workflow_graph.delete_graph(user_obj, graph_id)
    return {"status": "deleted", "id": graph_id}


# --- 워크플로우 실행 (Phase 2: SSE 스트리밍) ---------------------------------


@app.post("/api/workflow-graphs/{graph_id}/run", tags=["workflow-graph"])
async def workflow_graphs_run(
    graph_id: str,
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
):
    """워크플로우 그래프 실행 (Server-Sent Events 스트리밍).

    응답 매체: ``text/event-stream``
    이벤트 종류: run_started / node_started / node_finished / run_finished / run_failed
    각 이벤트의 data는 JSON 한 줄.
    """
    user_obj = ctx.user(user)
    ctx.workflow_graph.assert_can_run(user_obj)
    graph = ctx.workflow_graph.get_graph(user_obj, graph_id)

    engine = ctx.workflow_graph_engine

    async def event_stream():
        async for event in engine.run(user_obj, graph, ctx.raw, ctx.repository.save):
            payload = _json.dumps(event["data"], ensure_ascii=False, default=str)
            yield f"event: {event['event']}\ndata: {payload}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/workflow-graphs/{graph_id}/runs", tags=["workflow-graph"])
def workflow_graphs_runs_list(
    graph_id: str,
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
) -> dict:
    """특정 그래프의 실행 이력 목록 (최근순)."""
    user_obj = ctx.user(user)
    return {"runs": ctx.workflow_graph.list_runs(user_obj, graph_id=graph_id)}


@app.get("/api/workflow-runs/{run_id}", tags=["workflow-graph"])
def workflow_run_detail(
    run_id: str,
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
) -> dict:
    """실행 이력 상세 — run + steps."""
    user_obj = ctx.user(user)
    return ctx.workflow_graph.get_run(user_obj, run_id)


# ── 온톨로지 추출 ─────────────────────────────────────────────────────────────

@app.post("/api/documents/extract-ontology", tags=["ontology"])
def documents_extract_ontology(
    body: OntologyExtractRequest,
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
) -> dict:
    """업로드된 PDF에서 온톨로지(엔티티/관계) 추출."""
    ctx.user(user)
    from . import ontology_extractor
    doc_info = next((d for d in ctx.list_uploaded_documents() if d["doc_id"] == body.doc_id), None)
    if not doc_info:
        raise AppError("NOT_FOUND", f"문서 {body.doc_id}를 찾을 수 없습니다.", 404)
    from .vector_search import UPLOAD_DIR
    file_path = UPLOAD_DIR / doc_info["filename"]
    try:
        from langchain_community.document_loaders import PyPDFLoader
        pages = PyPDFLoader(str(file_path)).load()
        text = "\n".join(p.page_content for p in pages if p.page_content.strip())
    except Exception as exc:
        raise AppError("READ_FAILED", f"PDF 읽기 실패: {exc}", 500) from exc
    try:
        result = ontology_extractor.extract(text, body.doc_id, doc_info["filename"])
    except Exception as exc:
        raise AppError("EXTRACT_FAILED", f"온톨로지 추출 실패: {exc}", 500) from exc
    return {
        "status": "ok",
        "doc_id": body.doc_id,
        "entity_count": len(result["entities"]),
        "relation_count": len(result["relationships"]),
    }


# ── 온톨로지 스키마 관리 (/mgmt/ prefix — 기존 /api/ontology/schema와 충돌 방지) ──

@app.get("/api/ontology/mgmt/schema", tags=["ontology"])
def ontology_mgmt_schema_get(user: str = Depends(current_user_key)) -> dict:
    """엔티티 유형 + 관계 유형 목록 (builtin + domain)."""
    return ontology_store.get_schema()


@app.post("/api/ontology/mgmt/schema/entity-types", tags=["ontology"])
def ontology_mgmt_add_entity_type(
    body: EntityTypeCreate,
    user: str = Depends(current_user_key),
    _perm: None = Depends(require_permission("can_edit_ontology")),
) -> dict:
    """도메인 엔티티 유형 추가."""
    return ontology_store.add_entity_type(body.model_dump())


@app.delete("/api/ontology/mgmt/schema/entity-types/{type_name}", tags=["ontology"])
def ontology_mgmt_delete_entity_type(
    type_name: str,
    user: str = Depends(current_user_key),
    _perm: None = Depends(require_permission("can_edit_ontology")),
) -> dict:
    """도메인 엔티티 유형 삭제 (범용 유형은 삭제 불가)."""
    success = ontology_store.delete_entity_type(type_name)
    if not success:
        raise AppError("NOT_FOUND", f"유형 '{type_name}'을 찾을 수 없거나 범용 유형입니다.", 404)
    return {"status": "deleted", "name": type_name}


@app.post("/api/ontology/mgmt/schema/relation-types", tags=["ontology"])
def ontology_mgmt_add_relation_type(
    body: RelationTypeCreate,
    user: str = Depends(current_user_key),
    _perm: None = Depends(require_permission("can_edit_ontology")),
) -> dict:
    """관계 유형 추가."""
    return ontology_store.add_relation_type(body.model_dump())


@app.delete("/api/ontology/mgmt/schema/relation-types/{type_name}", tags=["ontology"])
def ontology_mgmt_delete_relation_type(
    type_name: str,
    user: str = Depends(current_user_key),
    _perm: None = Depends(require_permission("can_edit_ontology")),
) -> dict:
    """관계 유형 삭제."""
    success = ontology_store.delete_relation_type(type_name)
    if not success:
        raise AppError("NOT_FOUND", f"관계 유형 '{type_name}'을 찾을 수 없습니다.", 404)
    return {"status": "deleted", "name": type_name}


# ── 온톨로지 인스턴스 관리 ────────────────────────────────────────────────────

@app.get("/api/ontology/{doc_id}/entities", tags=["ontology"])
def ontology_entities_list(
    doc_id: str,
    entity_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    user: str = Depends(current_user_key),
) -> dict:
    """엔티티 목록 (유형 필터 + 페이징)."""
    data = ontology_store.load_ontology(doc_id)
    if data is None:
        raise AppError("NOT_FOUND", f"온톨로지 {doc_id}를 찾을 수 없습니다.", 404)
    entities = data.get("entities", [])
    if entity_type:
        entities = [e for e in entities if e.get("type") == entity_type]
    total = len(entities)
    start = (page - 1) * size
    return {"entities": entities[start: start + size], "total": total, "page": page}


@app.post("/api/ontology/{doc_id}/entities", tags=["ontology"])
def ontology_entities_create(
    doc_id: str,
    body: EntityCreate,
    user: str = Depends(current_user_key),
    _perm: None = Depends(require_permission("can_edit_ontology")),
) -> dict:
    """엔티티 수동 추가."""
    return ontology_store.upsert_entity(doc_id, body.model_dump())


@app.put("/api/ontology/{doc_id}/entities/{entity_id}", tags=["ontology"])
def ontology_entities_update(
    doc_id: str,
    entity_id: str,
    body: EntityUpdate,
    user: str = Depends(current_user_key),
    _perm: None = Depends(require_permission("can_edit_ontology")),
) -> dict:
    """엔티티 수정."""
    data = ontology_store.load_ontology(doc_id)
    if not data:
        raise AppError("NOT_FOUND", f"온톨로지 {doc_id}를 찾을 수 없습니다.", 404)
    entity = next((e for e in data["entities"] if e["id"] == entity_id), None)
    if not entity:
        raise AppError("NOT_FOUND", f"엔티티 {entity_id}를 찾을 수 없습니다.", 404)
    if body.name is not None:
        entity["name"] = body.name
    if body.properties is not None:
        entity["properties"] = body.properties
    return ontology_store.upsert_entity(doc_id, entity)


@app.delete("/api/ontology/{doc_id}/entities/{entity_id}", tags=["ontology"])
def ontology_entities_delete(
    doc_id: str,
    entity_id: str,
    user: str = Depends(current_user_key),
    _perm: None = Depends(require_permission("can_edit_ontology")),
) -> dict:
    """엔티티 삭제 (연결된 관계도 함께 삭제)."""
    if not ontology_store.delete_entity(doc_id, entity_id):
        raise AppError("NOT_FOUND", f"엔티티 {entity_id}를 찾을 수 없습니다.", 404)
    return {"status": "deleted", "entity_id": entity_id}


# ── 온톨로지 관계 관리 ────────────────────────────────────────────────────────

@app.get("/api/ontology/{doc_id}/relationships", tags=["ontology"])
def ontology_relationships_list(
    doc_id: str,
    user: str = Depends(current_user_key),
) -> dict:
    """관계 목록."""
    data = ontology_store.load_ontology(doc_id)
    if data is None:
        raise AppError("NOT_FOUND", f"온톨로지 {doc_id}를 찾을 수 없습니다.", 404)
    return {"relationships": data.get("relationships", [])}


@app.post("/api/ontology/{doc_id}/relationships", tags=["ontology"])
def ontology_relationships_create(
    doc_id: str,
    body: OntologyRelationshipCreate,
    user: str = Depends(current_user_key),
    _perm: None = Depends(require_permission("can_edit_ontology")),
) -> dict:
    """관계 추가."""
    return ontology_store.add_relationship(doc_id, body.model_dump())


@app.delete("/api/ontology/{doc_id}/relationships/{rel_id}", tags=["ontology"])
def ontology_relationships_delete(
    doc_id: str,
    rel_id: str,
    user: str = Depends(current_user_key),
    _perm: None = Depends(require_permission("can_edit_ontology")),
) -> dict:
    """관계 삭제."""
    if not ontology_store.delete_relationship(doc_id, rel_id):
        raise AppError("NOT_FOUND", f"관계 {rel_id}를 찾을 수 없습니다.", 404)
    return {"status": "deleted", "rel_id": rel_id}


# ── 온톨로지 그래프 뷰 ────────────────────────────────────────────────────────

@app.get("/api/ontology/{doc_id}/graph", tags=["ontology"])
def ontology_graph(
    doc_id: str,
    user: str = Depends(current_user_key),
) -> dict:
    """React Flow 형식 그래프 데이터."""
    data = ontology_store.load_ontology(doc_id)
    if data is None:
        raise AppError("NOT_FOUND", f"온톨로지 {doc_id}를 찾을 수 없습니다.", 404)
    return ontology_store.get_graph(doc_id)


@app.get("/api/ontology", tags=["ontology"])
def ontology_list(user: str = Depends(current_user_key)) -> dict:
    """추출된 온톨로지 문서 목록."""
    return {"ontologies": ontology_store.list_ontologies()}


# ── 하이브리드 질의 ───────────────────────────────────────────────────────────

@app.post("/api/hybrid/ask", tags=["hybrid"])
def hybrid_ask(
    body: HybridAskRequest,
    user: str = Depends(current_user_key),
    ctx: AppContext = Depends(get_context),
) -> dict:
    """질문 유형을 자동 분류해 온톨로지 구조형 질의 + RAG를 혼합 처리.

    query_type 별 동작:
    - descriptive → 벡터 검색(RAG)만
    - filter / compare / calculate → 온톨로지 JSON 질의만
    - hybrid → 둘 다 + LLM 통합 요약
    """
    return ctx.ask_hybrid(body.question, user, body.doc_ids)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
