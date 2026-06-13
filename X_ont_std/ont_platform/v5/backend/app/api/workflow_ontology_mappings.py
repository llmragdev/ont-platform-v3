"""Workflow-to-ontology mapping APIs."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.workflow import _ctx
from app.models.tenant_context import TenantContext
from app.services.workflow_ontology_mapping_service import WorkflowOntologyMappingService


router = APIRouter(prefix="/api/workflow-ontology-mappings", tags=["workflow-ontology-mappings"])


def _get_mapping_svc() -> WorkflowOntologyMappingService:
    return WorkflowOntologyMappingService()


@router.get("")
def list_mappings(svc: WorkflowOntologyMappingService = Depends(_get_mapping_svc)):
    return {"items": svc.list_mappings()}


@router.get("/{mapping_id}")
def get_mapping(mapping_id: str, svc: WorkflowOntologyMappingService = Depends(_get_mapping_svc)):
    try:
        return svc.get_mapping(mapping_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{mapping_id}/install-schema")
def install_mapping_schema(
    mapping_id: str,
    ctx: TenantContext = Depends(_ctx),
    svc: WorkflowOntologyMappingService = Depends(_get_mapping_svc),
):
    try:
        return svc.install_schema(ctx, mapping_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
