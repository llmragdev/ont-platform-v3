from __future__ import annotations

import json
from typing import Any

from .governance_service import GovernanceService
from .provenance_service import utc_now
from .repositories import OntologyObjectRepository
from .storage_config import resolve_project_paths
from .tenant import TenantContext


class MaterializeService:
    def __init__(self, ctx: TenantContext) -> None:
        self.ctx = ctx
        self.paths = resolve_project_paths(ctx.company_id, ctx.project_id)
        self.objects = OntologyObjectRepository(ctx)
        self.governance = GovernanceService()

    def materialize(
        self,
        *,
        dataset_name: str,
        object_type: str | None = None,
        include_disabled: bool = False,
    ) -> dict[str, Any]:
        self.governance.validate_dataset_name(dataset_name)
        rows = self.objects.list(type_name=object_type, include_disabled=include_disabled)
        dataset = {
            "dataset_name": dataset_name,
            "company_id": self.ctx.company_id,
            "project_id": self.ctx.project_id,
            "object_type": object_type,
            "include_disabled": include_disabled,
            "materialized_at": utc_now(),
            "materialized_by": self.ctx.user_id,
            "row_count": len(rows),
            "rows": rows,
        }
        path = self.paths.ontology / "materialized" / f"{dataset_name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
        return dataset | {"path": str(path)}
