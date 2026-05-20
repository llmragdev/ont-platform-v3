from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import Header, Query

from .errors import AppError
from .storage_config import (
    get_project_settings,
    get_tenant_settings,
    resolve_project_paths,
    validate_storage_id,
)


_DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@dataclass(frozen=True)
class TenantContext:
    user_id: str
    company_id: str
    project_id: str
    project_ids: list[str]
    role: str
    permissions: dict[str, bool]
    auth_mode: str
    tenant_settings: dict[str, Any]
    project_settings: dict[str, Any]


class TenantService:
    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or _DATA_DIR

    def users(self) -> list[dict[str, Any]]:
        return self._load_list("users.json")

    def companies(self) -> list[dict[str, Any]]:
        return self._load_list("companies.json")

    def projects(self) -> list[dict[str, Any]]:
        return self._load_list("projects.json")

    def role_defaults(self) -> dict[str, dict[str, bool]]:
        path = self.data_dir / "role_defaults.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def get_user(self, user_id: str) -> dict[str, Any]:
        validate_storage_id(user_id, "user_id")
        user = next((item for item in self.users() if item["id"] == user_id), None)
        if user is None:
            raise AppError("AUTH_REQUIRED", f"Unknown user: {user_id}", 401)
        if user.get("status", "active") != "active":
            raise AppError("AUTH_REQUIRED", f"Disabled user: {user_id}", 401)
        return user

    def get_projects_for_user(self, user_id: str) -> list[dict[str, Any]]:
        user = self.get_user(user_id)
        allowed = set(user.get("project_ids", []))
        return [project for project in self.projects() if project["id"] in allowed]

    def create_context(self, user_id: str, project_id: str | None, auth_mode: str) -> TenantContext:
        user = self.get_user(user_id)
        company_id = validate_storage_id(user["company_id"], "company_id")
        project_ids = [validate_storage_id(item, "project_id") for item in user.get("project_ids", [])]
        selected_project = validate_storage_id(
            project_id or user.get("default_project_id") or (project_ids[0] if project_ids else ""),
            "project_id",
        )
        if selected_project not in project_ids:
            raise AppError("PROJECT_FORBIDDEN", f"User {user_id} cannot access project {selected_project}.", 403)
        project = next((item for item in self.projects() if item["id"] == selected_project), None)
        if project is None:
            raise AppError("PROJECT_FORBIDDEN", f"Unknown project: {selected_project}.", 403)
        if project.get("company_id") != company_id:
            raise AppError("TENANT_FORBIDDEN", "Project does not belong to the user's company.", 403)

        permissions = self.resolve_permissions(user)
        tenant_settings = get_tenant_settings(company_id)
        project_settings = get_project_settings(company_id, selected_project)
        return TenantContext(
            user_id=user_id,
            company_id=company_id,
            project_id=selected_project,
            project_ids=project_ids,
            role=user["role"],
            permissions=permissions,
            auth_mode=auth_mode,
            tenant_settings=tenant_settings,
            project_settings=project_settings,
        )

    def resolve_permissions(self, user: dict[str, Any]) -> dict[str, bool]:
        defaults = self.role_defaults()
        role = user.get("role", "viewer")
        permissions = dict(defaults.get(role, defaults["viewer"]))
        permissions.update(user.get("permission_override", {}))
        return permissions

    def _load_list(self, name: str) -> list[dict[str, Any]]:
        path = self.data_dir / name
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, list):
            raise AppError("INVALID_CONFIG", f"{name} must contain a JSON array.", 500)
        return loaded


tenant_service = TenantService()


def current_context(
    authorization: str | None = Header(default=None),
    user_id: str | None = Query(default=None),
    project_id: str | None = Query(default=None),
) -> TenantContext:
    # JWT parsing is intentionally left for the next auth sprint. For Phase 1,
    # dev-user mode proves that API identity and TenantContext are unified.
    if authorization:
        raise AppError("AUTH_NOT_IMPLEMENTED", "JWT auth is defined but not implemented in Phase 1.", 501)
    if os.environ.get("ALLOW_DEV_USER", "true").lower() != "true":
        raise AppError("AUTH_REQUIRED", "Developer user mode is disabled.", 401)
    selected_user = user_id or "alice"
    return tenant_service.create_context(selected_user, project_id, auth_mode="dev_user")


def tenant_me_response(ctx: TenantContext, include_paths: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "user": {
            "id": ctx.user_id,
            "company_id": ctx.company_id,
            "project_id": ctx.project_id,
            "project_ids": ctx.project_ids,
            "role": ctx.role,
            "permissions": ctx.permissions,
            "auth_mode": ctx.auth_mode,
        },
        "tenant_settings": ctx.tenant_settings,
        "project_settings": ctx.project_settings,
    }
    if include_paths:
        payload["paths"] = resolve_project_paths(ctx.company_id, ctx.project_id).as_dict()
    return payload
