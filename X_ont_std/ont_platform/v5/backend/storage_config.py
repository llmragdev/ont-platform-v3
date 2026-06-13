"""Storage path configuration — v3.0.

Physical layout:
    storage/
    └── {company_id}/
        └── {project_id}/
            ├── uploads/
            ├── vector_db/V{shard_id}/
            ├── ontology/
            ├── workflow_runs/
            └── audit_log.jsonl
"""
from __future__ import annotations

from pathlib import Path

STORAGE_ROOT = Path(__file__).resolve().parent.parent.parent / "storage"


def get_company_root(company_id: str) -> Path:
    return STORAGE_ROOT / company_id


def get_project_root(company_id: str, project_id: str) -> Path:
    return get_company_root(company_id) / project_id


def get_raw_root(company_id: str, project_id: str) -> Path:
    return get_project_root(company_id, project_id) / "raw"


def get_uploads_path(company_id: str, project_id: str) -> Path:
    return get_project_root(company_id, project_id) / "uploads"


def get_ontology_path(company_id: str, project_id: str) -> Path:
    return get_project_root(company_id, project_id) / "ontology"


def get_vector_db_root(company_id: str, project_id: str) -> Path:
    return get_project_root(company_id, project_id) / "vector_db"


def get_vector_db_path(company_id: str, project_id: str, shard_id: str = "default") -> Path:
    folder = f"V{shard_id}" if not str(shard_id).startswith("V") else str(shard_id)
    return get_vector_db_root(company_id, project_id) / folder


def get_workflow_runs_path(company_id: str, project_id: str) -> Path:
    return get_project_root(company_id, project_id) / "workflow_runs"


def list_shard_paths(company_id: str, project_id: str) -> list[Path]:
    root = get_vector_db_root(company_id, project_id)
    if not root.exists():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("V"))


def ensure_project_dirs(company_id: str, project_id: str) -> None:
    for fn in (get_raw_root, get_uploads_path, get_ontology_path, get_vector_db_root, get_workflow_runs_path):
        fn(company_id, project_id).mkdir(parents=True, exist_ok=True)


DEFAULT_COMPANY = "default"
DEFAULT_PROJECT = "proj-default"
