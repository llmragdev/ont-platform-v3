"""테넌트 · 사용자 · 권한 관리 모듈 (Phase 1 — JSON 파일 기반).

핵심 책임:
  - JSON 파일 로드 (companies / users / projects / role_defaults)
  - 런타임 권한 resolve: role_defaults + permission_override merge
  - company_id 격리 강제: assert_same_company()
  - FastAPI 의존성: require_permission(flag)
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import Depends, HTTPException, Query

_CONFIG_DIR = Path(__file__).parent / "config"


# ── JSON 로드 (프로세스 수명 동안 캐시) ──────────────────────────────────────

@lru_cache(maxsize=1)
def _load_role_defaults() -> dict[str, dict[str, bool]]:
    return json.loads((_CONFIG_DIR / "role_defaults.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_companies() -> list[dict]:
    return json.loads((_CONFIG_DIR / "companies.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_users() -> list[dict]:
    return json.loads((_CONFIG_DIR / "users.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_projects() -> list[dict]:
    return json.loads((_CONFIG_DIR / "projects.json").read_text(encoding="utf-8"))


# ── TenantManager ─────────────────────────────────────────────────────────────

class TenantManager:
    """테넌트 관련 조회·검증을 담당하는 서비스 클래스."""

    # ── 사용자 ──────────────────────────────────────────────────────────────

    def get_user(self, user_id: str) -> dict[str, Any]:
        users = _load_users()
        user = next((u for u in users if u["id"] == user_id), None)
        if user is None:
            raise HTTPException(status_code=404, detail=f"tenant user '{user_id}' not found")
        return user

    def user_exists(self, user_id: str) -> bool:
        return any(u["id"] == user_id for u in _load_users())

    def list_users(self) -> list[dict]:
        users = _load_users()
        # 런타임 권한을 붙여서 반환
        return [
            {**u, "permissions": self.resolve_permissions(u)}
            for u in users
        ]

    # ── 권한 ────────────────────────────────────────────────────────────────

    def resolve_permissions(self, user: dict) -> dict[str, bool]:
        """role_defaults + permission_override를 merge해 최종 권한을 반환."""
        role = user.get("role", "viewer")
        defaults = _load_role_defaults()
        base: dict[str, bool] = dict(defaults.get(role, defaults["viewer"]))
        override: dict[str, bool] = user.get("permission_override", {})
        return {**base, **override}

    def get_permissions(self, user_id: str) -> dict[str, bool]:
        return self.resolve_permissions(self.get_user(user_id))

    def check_permission(self, user_id: str, flag: str) -> bool:
        perms = self.get_permissions(user_id)
        return perms.get(flag, False)

    # ── 회사 ────────────────────────────────────────────────────────────────

    def get_company(self, company_id: str) -> dict:
        companies = _load_companies()
        company = next((c for c in companies if c["id"] == company_id), None)
        if company is None:
            raise HTTPException(status_code=404, detail=f"company '{company_id}' not found")
        return company

    def list_companies(self) -> list[dict]:
        return _load_companies()

    def get_company_for_user(self, user_id: str) -> dict:
        user = self.get_user(user_id)
        return self.get_company(user["company_id"])

    # ── 프로젝트 ─────────────────────────────────────────────────────────────

    def list_projects_for_user(self, user_id: str) -> list[dict]:
        user = self.get_user(user_id)
        project_ids = set(user.get("project_ids", []))
        return [p for p in _load_projects() if p["id"] in project_ids]

    def get_project(self, project_id: str) -> dict:
        projects = _load_projects()
        project = next((p for p in projects if p["id"] == project_id), None)
        if project is None:
            raise HTTPException(status_code=404, detail=f"project '{project_id}' not found")
        return project

    # ── 격리 강제 ────────────────────────────────────────────────────────────

    def assert_same_company(self, user_id: str, resource_company_id: str) -> None:
        """사용자와 리소스의 company_id가 다르면 403을 raise한다."""
        user = self.get_user(user_id)
        user_company = user["company_id"]
        # default 테넌트는 모든 리소스 접근 허용 (기존 호환)
        if user_company == "default":
            return
        if user_company != resource_company_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "company_isolation",
                    "message": f"user '{user_id}' belongs to '{user_company}', "
                               f"cannot access '{resource_company_id}' resource",
                },
            )

    def filter_by_company(self, user_id: str, items: list[dict],
                          company_field: str = "company_id") -> list[dict]:
        """리스트에서 사용자 company에 속하는 항목만 반환."""
        user = self.get_user(user_id)
        user_company = user["company_id"]
        if user_company == "default":
            return items
        return [
            item for item in items
            if item.get(company_field, "default") == user_company
        ]


# ── 싱글톤 ────────────────────────────────────────────────────────────────────

_tenant_manager = TenantManager()


def get_tenant_manager() -> TenantManager:
    return _tenant_manager


# ── FastAPI 의존성 팩토리 ──────────────────────────────────────────────────────

def require_permission(flag: str):
    """FastAPI Depends()에 사용하는 권한 검사 의존성 팩토리.

    - 테넌트 시스템에 등록된 사용자: 권한 플래그로 403 판단
    - 테넌트 시스템에 없는 사용자(기존 워크플로우 데모 사용자): 패스 (하위 호환)

    사용 예:
        @app.post("/api/ontology/{doc_id}/entities")
        def create_entity(
            _: None = Depends(require_permission("can_edit_ontology")),
        ): ...
    """
    def _check(
        user: str = Query(default="analyst"),
        tm: TenantManager = Depends(get_tenant_manager),
    ) -> None:
        try:
            user_obj = tm.get_user(user)
        except HTTPException as exc:
            if exc.status_code == 404:
                return  # 테넌트 미등록 사용자는 기존 시스템에 위임
            raise
        if not tm.resolve_permissions(user_obj).get(flag, False):
            perms = tm.resolve_permissions(user_obj)
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "permission_denied",
                    "required": flag,
                    "user": user,
                    "role": user_obj.get("role"),
                    "resolved_permissions": perms,
                },
            )
    return _check


def current_tenant_user(
    user: str = Query(..., alias="user"),
    tm: TenantManager = Depends(get_tenant_manager),
) -> dict:
    """현재 테넌트 사용자 dict를 반환하는 의존성."""
    return tm.get_user(user)


def require_known_user(ctx_getter):
    """old AppContext 사용자 OR tenant 사용자 중 하나에 속해야 하는 Depends 팩토리.

    사용 예:
        from .app_context import AppContext
        _user: None = Depends(require_known_user(get_context))
    """
    from fastapi import Depends as _Depends

    def _check(
        user: str = Query(default="analyst"),
        ctx=_Depends(ctx_getter),
        tm: TenantManager = _Depends(get_tenant_manager),
    ) -> None:
        if user not in ctx.raw.get("users", {}):
            if not tm.user_exists(user):
                raise HTTPException(
                    status_code=401,
                    detail={"error": "AUTH_REQUIRED", "message": f"Unknown user '{user}'"},
                )
    return _check
