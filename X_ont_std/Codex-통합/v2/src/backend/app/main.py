from __future__ import annotations

from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .errors import AppError
from .models import (
    AskRequest,
    HybridAskRequest,
    OntologyObjectCreate,
    OntologyObjectUpdate,
    OntologyRelationshipCreate,
    RelationshipCreate,
)
from .ontology import OntologyStore
from .repositories import OntologyObjectRepository, OntologyRelationshipRepository
from .tenant import TenantContext, current_context, tenant_me_response, tenant_service


app = FastAPI(title="Codex Ontology Workbench", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

store = OntologyStore()


def get_store() -> OntologyStore:
    return store


def require_permission(ctx: TenantContext, permission: str) -> None:
    if not ctx.permissions.get(permission, False):
        raise AppError("PERMISSION_DENIED", f"Permission required: {permission}", 403)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.get("/api/health")
def health(ctx: OntologyStore = Depends(get_store)) -> dict:
    return {"status": "ok", "overview": ctx.overview()}


@app.get("/api/v1/tenant/me")
def tenant_me(
    include_paths: bool = Query(default=False),
    tenant: TenantContext = Depends(current_context),
) -> dict:
    return tenant_me_response(tenant, include_paths=include_paths)


@app.get("/api/v1/tenant/projects")
def tenant_projects(tenant: TenantContext = Depends(current_context)) -> dict:
    return {"projects": tenant_service.get_projects_for_user(tenant.user_id)}


@app.get("/api/v1/ontology/objects")
def v1_objects(
    type_name: str | None = Query(default=None, alias="type"),
    include_disabled: bool = Query(default=False),
    tenant: TenantContext = Depends(current_context),
) -> dict:
    require_permission(tenant, "can_read")
    return {"objects": OntologyObjectRepository(tenant).list(type_name, include_disabled)}


@app.post("/api/v1/ontology/objects")
def v1_create_object(
    body: OntologyObjectCreate,
    tenant: TenantContext = Depends(current_context),
) -> dict:
    require_permission(tenant, "can_edit_object")
    return OntologyObjectRepository(tenant).create(body.model_dump())


@app.get("/api/v1/ontology/objects/{object_id}")
def v1_object_detail(
    object_id: str,
    tenant: TenantContext = Depends(current_context),
) -> dict:
    require_permission(tenant, "can_read")
    return OntologyObjectRepository(tenant).get(object_id)


@app.put("/api/v1/ontology/objects/{object_id}")
def v1_update_object(
    object_id: str,
    body: OntologyObjectUpdate,
    tenant: TenantContext = Depends(current_context),
) -> dict:
    require_permission(tenant, "can_edit_object")
    return OntologyObjectRepository(tenant).update(object_id, body.model_dump(exclude_unset=True))


@app.delete("/api/v1/ontology/objects/{object_id}")
def v1_disable_object(
    object_id: str,
    tenant: TenantContext = Depends(current_context),
) -> dict:
    require_permission(tenant, "can_edit_object")
    return OntologyObjectRepository(tenant).disable(object_id)


@app.get("/api/v1/ontology/relationships")
def v1_relationships(
    include_disabled: bool = Query(default=False),
    tenant: TenantContext = Depends(current_context),
) -> dict:
    require_permission(tenant, "can_read")
    return {"relationships": OntologyRelationshipRepository(tenant).list(include_disabled)}


@app.post("/api/v1/ontology/relationships")
def v1_create_relationship(
    body: OntologyRelationshipCreate,
    tenant: TenantContext = Depends(current_context),
) -> dict:
    require_permission(tenant, "can_edit_relationship")
    return OntologyRelationshipRepository(tenant).create(body.model_dump())


@app.delete("/api/v1/ontology/relationships/{relationship_id}")
def v1_disable_relationship(
    relationship_id: str,
    tenant: TenantContext = Depends(current_context),
) -> dict:
    require_permission(tenant, "can_edit_relationship")
    return OntologyRelationshipRepository(tenant).disable(relationship_id)


@app.get("/api/ontology/schema")
def ontology_schema(ctx: OntologyStore = Depends(get_store)) -> dict:
    return ctx.schema_dict()


@app.get("/api/ontology/overview")
def ontology_overview(ctx: OntologyStore = Depends(get_store)) -> dict:
    return ctx.overview()


@app.get("/api/ontology/object-types")
def object_types(ctx: OntologyStore = Depends(get_store)) -> dict:
    return {"object_types": ctx.object_types()}


@app.get("/api/ontology/relationship-types")
def relationship_types(ctx: OntologyStore = Depends(get_store)) -> dict:
    return {"relationship_types": ctx.relationship_types()}


@app.get("/api/ontology/actions")
def action_types(ctx: OntologyStore = Depends(get_store)) -> dict:
    return {"action_types": ctx.action_types()}


@app.get("/api/ontology/objects")
def objects(type: str | None = Query(default=None), ctx: OntologyStore = Depends(get_store)) -> dict:  # noqa: A002
    return {"objects": ctx.list_objects(type)}


@app.get("/api/ontology/objects/{object_id}")
def object_detail(object_id: str, ctx: OntologyStore = Depends(get_store)) -> dict:
    return ctx.get_object(object_id)


@app.get("/api/ontology/objects/{object_id}/context")
def object_context(object_id: str, ctx: OntologyStore = Depends(get_store)) -> dict:
    return ctx.object_context(object_id)


@app.get("/api/ontology/relationships")
def relationships(type: str | None = Query(default=None), ctx: OntologyStore = Depends(get_store)) -> dict:  # noqa: A002
    return {"relationships": ctx.list_relationships(type)}


@app.post("/api/ontology/relationships")
def add_relationship(body: RelationshipCreate, ctx: OntologyStore = Depends(get_store)) -> dict:
    return ctx.add_relationship(body)


@app.get("/api/search")
def search(q: str, top_k: int = 5, ctx: OntologyStore = Depends(get_store)) -> dict:
    return {"query": q, "results": ctx.search(q, top_k)}


@app.post("/api/ask")
def ask(body: AskRequest, ctx: OntologyStore = Depends(get_store)) -> dict:
    return ctx.ask(body.question, body.object_id)


@app.post("/api/hybrid/ask")
def hybrid_ask(body: HybridAskRequest, ctx: OntologyStore = Depends(get_store)) -> dict:
    return ctx.hybrid_ask(body.question, object_id=body.object_id, top_k=body.top_k)
