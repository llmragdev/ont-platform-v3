from __future__ import annotations

from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .errors import AppError
from .models import AskRequest, HybridAskRequest, RelationshipCreate
from .ontology import OntologyStore


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


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.get("/api/health")
def health(ctx: OntologyStore = Depends(get_store)) -> dict:
    return {"status": "ok", "overview": ctx.overview()}


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
