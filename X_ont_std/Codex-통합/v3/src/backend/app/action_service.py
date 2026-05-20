from __future__ import annotations

from typing import Any

from .errors import AppError
from .provenance_service import ProvenanceService
from .repositories import OntologyObjectRepository
from .tenant import TenantContext
from .writeback_service import WriteBackService


class ActionService:
    def __init__(self, ctx: TenantContext) -> None:
        self.ctx = ctx
        self.objects = OntologyObjectRepository(ctx)
        self.provenance = ProvenanceService(ctx.user_id)
        self.writeback = WriteBackService(ctx)

    def execute_action(
        self,
        action_name: str,
        target_id: str,
        params: dict[str, Any] | None = None,
        *,
        write_back: bool = True,
    ) -> dict[str, Any]:
        params = params or {}
        obj = self.objects.get(target_id)

        if action_name == "CHANGE_WC_DATE":
            result = self._change_wc_date(obj, params)
        elif action_name in {"APPROVE_ORDER", "ApproveOrder"}:
            result = self._approve_order(obj, params)
        else:
            raise AppError("INVALID_ACTION", f"Unsupported action: {action_name}", 400)

        writeback_record = None
        if write_back:
            writeback_record = self.writeback.request(
                operation="UPDATE",
                object_id=result["object"]["id"],
                payload=result["object"]["values"],
                metadata={"action_name": action_name},
            )
        return result | {"writeback": writeback_record}

    def _change_wc_date(self, obj: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        new_date = params.get("new_date")
        if not new_date:
            raise AppError("MISSING_PARAMS", "new_date is required", 400)
        updated = self.objects.update(obj["id"], {
            "values": {"wc_date": new_date},
            "provenance": self.provenance.for_action("CHANGE_WC_DATE", params),
        })
        return {
            "status": "success",
            "message": f"WC Date updated to {new_date}.",
            "object": updated,
        }

    def _approve_order(self, obj: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        if obj["type"] != "Order":
            raise AppError("INVALID_TARGET", "Only Order objects can be approved", 400)
        updated = self.objects.update(obj["id"], {
            "values": {"status": "Approved"},
            "provenance": self.provenance.for_action("APPROVE_ORDER", params),
        })
        return {
            "status": "success",
            "message": "Order approved.",
            "object": updated,
        }
