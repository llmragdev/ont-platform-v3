"""System workflow template loading and project clone support."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from app.models.tenant_context import TenantContext
from app.services.workflow import WorkflowGraphService


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "config" / "workflow_templates"


class WorkflowTemplateService:
    def __init__(self, template_dir: Path | None = None, graph_svc: WorkflowGraphService | None = None) -> None:
        self.template_dir = template_dir or TEMPLATE_DIR
        self.graph_svc = graph_svc or WorkflowGraphService()

    def list_templates(self) -> list[dict[str, Any]]:
        templates = [self._load_file(path) for path in sorted(self.template_dir.glob("*.json"))]
        templates.sort(key=lambda item: item.get("name", ""))
        return templates

    def get_template(self, template_id: str) -> dict[str, Any]:
        for template in self.list_templates():
            if template.get("template_id") == template_id:
                return template
        raise KeyError(f"Workflow template not found: {template_id}")

    def clone_template(
        self,
        ctx: TenantContext,
        template_id: str,
        *,
        name: str | None = None,
        default_mode: str | None = None,
    ) -> dict[str, Any]:
        template = self.get_template(template_id)
        graph = copy.deepcopy(template)
        graph.pop("category", None)
        graph.pop("summary", None)
        graph.pop("template_version", None)
        graph["id"] = None
        graph["name"] = name or template.get("name") or "Untitled Workflow"
        graph["graph_kind"] = "template_copy"
        graph["tenant_scope"] = {"company_id": ctx.company_id, "project_id": ctx.project_id}
        graph["source"] = {
            "type": "system_template",
            "source_graph_id": None,
            "cloned_from": template_id,
            "template_id": template_id,
        }
        graph["template_id"] = template_id
        graph["template_version"] = template.get("template_version", "1.0.0")
        if default_mode:
            runtime = dict(graph.get("runtime") or {})
            runtime["default_mode"] = default_mode
            graph["runtime"] = runtime
        return self.graph_svc.save_graph(ctx, graph)

    def _load_file(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))
