from dataclasses import dataclass

from fastapi import Request

from app.core.errors import http_error


@dataclass(frozen=True)
class RequestContext:
    tenant_id: str
    org_id: str | None
    scope_level: str
    dept_code: str | None


def get_request_context(request: Request) -> RequestContext:
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise http_error(400, "tenant_header_required", "X-Tenant-ID header is required")

    org_id = request.headers.get("X-Org-ID")
    if not org_id:
        return RequestContext(
            tenant_id=tenant_id,
            org_id=None,
            scope_level="tenant",
            dept_code=None,
        )

    dept_code = org_id[:2]
    scope_level = "department" if len(org_id) >= 4 and org_id[2:] == "00" else "team"
    return RequestContext(
        tenant_id=tenant_id,
        org_id=org_id,
        scope_level=scope_level,
        dept_code=dept_code,
    )

