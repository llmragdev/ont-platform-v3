from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import AppError


_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_STORAGE_ROOT = _PROJECT_ROOT / "storage"


DEFAULT_TENANT_SETTINGS: dict[str, Any] = {
    "display_name": "Default Tenant",
    "status": "active",
    "limits": {
        "max_users": 10,
        "max_projects": 3,
        "max_documents": 50,
    },
    "features": {
        "ontology_editing": True,
        "hybrid_query": True,
        "graph_editor": True,
    },
    "ui": {
        "theme": "light",
        "logo_url": None,
    },
    "llm": {
        "provider": "system_default",
        "prompt_policy": "strict_grounded",
    },
}


DEFAULT_PROJECT_SETTINGS: dict[str, Any] = {
    "display_name": "Default Project",
    "default_language": "ko",
    "rag": {
        "top_k": 5,
        "chunk_size": 1000,
        "chunk_overlap": 150,
    },
    "hybrid_query": {
        "require_citations": True,
        "allow_fallback_planner": True,
    },
}


@dataclass(frozen=True)
class ProjectPaths:
    tenant_root: Path
    project_root: Path
    raw: Path
    vector_db: Path
    ontology: Path
    uploads: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "tenant_root": str(self.tenant_root),
            "project_root": str(self.project_root),
            "raw": str(self.raw),
            "vector_db": str(self.vector_db),
            "ontology": str(self.ontology),
            "uploads": str(self.uploads),
        }


def validate_storage_id(value: str, field_name: str) -> str:
    """Reject path traversal, absolute paths, drive letters, and separators."""
    if not value or not _SAFE_ID.fullmatch(value):
        raise AppError(
            "INVALID_STORAGE_ID",
            f"{field_name} must use only letters, numbers, '_' or '-' and cannot contain path separators.",
            400,
        )
    return value


def get_storage_root() -> Path:
    configured = os.environ.get("STORAGE_ROOT")
    root = Path(configured) if configured else _DEFAULT_STORAGE_ROOT
    return root.resolve()


def get_tenant_root(company_id: str) -> Path:
    safe_company = validate_storage_id(company_id, "company_id")
    root = get_storage_root()
    tenant_root = (root / safe_company).resolve()
    _assert_inside(root, tenant_root)
    return tenant_root


def get_project_root(company_id: str, project_id: str) -> Path:
    safe_project = validate_storage_id(project_id, "project_id")
    tenant_root = get_tenant_root(company_id)
    project_root = (tenant_root / safe_project).resolve()
    _assert_inside(tenant_root, project_root)
    return project_root


def resolve_project_paths(company_id: str, project_id: str) -> ProjectPaths:
    tenant_root = get_tenant_root(company_id)
    project_root = get_project_root(company_id, project_id)
    return ProjectPaths(
        tenant_root=tenant_root,
        project_root=project_root,
        raw=project_root / "raw",
        vector_db=project_root / "vector_db",
        ontology=project_root / "ontology",
        uploads=project_root / "uploads",
    )


def get_tenant_settings(company_id: str) -> dict[str, Any]:
    tenant_root = get_tenant_root(company_id)
    settings = _load_json(tenant_root / "tenant_settings.json", DEFAULT_TENANT_SETTINGS)
    return _deep_merge(DEFAULT_TENANT_SETTINGS, settings)


def get_project_settings(company_id: str, project_id: str) -> dict[str, Any]:
    project_root = get_project_root(company_id, project_id)
    settings = _load_json(project_root / "project_settings.json", DEFAULT_PROJECT_SETTINGS)
    return _deep_merge(DEFAULT_PROJECT_SETTINGS, settings)


def _load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AppError("INVALID_SETTINGS", f"Invalid JSON settings file: {path.name}", 500) from exc
    if not isinstance(loaded, dict):
        raise AppError("INVALID_SETTINGS", f"Settings file must contain a JSON object: {path.name}", 500)
    return loaded


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _assert_inside(parent: Path, child: Path) -> None:
    try:
        child.relative_to(parent)
    except ValueError as exc:
        raise AppError("INVALID_STORAGE_PATH", "Resolved storage path escaped its parent.", 400) from exc
