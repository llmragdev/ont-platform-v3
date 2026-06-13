"""Workflow system template APIs."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.workflow import _ctx
from app.models.tenant_context import TenantContext
from app.services.workflow_template_service import WorkflowTemplateService


router = APIRouter(prefix="/api/workflow-templates", tags=["workflow-templates"])


class CloneTemplateRequest(BaseModel):
    name: str | None = None
    default_mode: Literal["dry_run", "post"] = "dry_run"


def _get_template_svc() -> WorkflowTemplateService:
    return WorkflowTemplateService()


@router.get("")
def list_templates(svc: WorkflowTemplateService = Depends(_get_template_svc)):
    return {"items": svc.list_templates()}


@router.get("/{template_id}")
def get_template(template_id: str, svc: WorkflowTemplateService = Depends(_get_template_svc)):
    try:
        return svc.get_template(template_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{template_id}/clone")
def clone_template(
    template_id: str,
    body: CloneTemplateRequest = CloneTemplateRequest(),
    ctx: TenantContext = Depends(_ctx),
    svc: WorkflowTemplateService = Depends(_get_template_svc),
):
    try:
        return svc.clone_template(ctx, template_id, name=body.name, default_mode=body.default_mode)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
