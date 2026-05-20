"""Storage path configuration — V-ID sharding pattern.

Physical layout:
    storage/
    └── {company_id}/
        └── {project_id}/
            ├── raw/                   raw uploaded files (mid_cat/sub_cat)
            ├── vector_db/
            │   ├── V{shard_id}/       each is an independent Chroma instance
            │   └── ...
            ├── ontology/              entity/relationship JSON store
            │   └── objects.json
            └── uploads/              original PDF files

Shard IDs (V-IDs) allow independent Chroma instances per document group.
Query a specific shard (fast) or scan all shards and re-rank by score.
"""
from __future__ import annotations

from pathlib import Path

# ── Root ──────────────────────────────────────────────────────────────────────

# Storage root is sibling of src/, two levels up from this file
STORAGE_ROOT = Path(__file__).resolve().parent.parent.parent / "storage"


# ── Path helpers ──────────────────────────────────────────────────────────────

def get_company_root(company_id: str) -> Path:
    return STORAGE_ROOT / company_id


def get_project_root(company_id: str, project_id: str) -> Path:
    return get_company_root(company_id) / project_id


def get_raw_root(company_id: str, project_id: str) -> Path:
    """Raw uploaded files: raw/{mid_cat}/{sub_cat}/"""
    return get_project_root(company_id, project_id) / "raw"


def get_uploads_path(company_id: str, project_id: str) -> Path:
    """Original PDF files kept here after upload."""
    return get_project_root(company_id, project_id) / "uploads"


def get_ontology_path(company_id: str, project_id: str) -> Path:
    """Ontology JSON store directory."""
    return get_project_root(company_id, project_id) / "ontology"


def get_vector_db_root(company_id: str, project_id: str) -> Path:
    """Root that contains all V{shard_id} subdirectories."""
    return get_project_root(company_id, project_id) / "vector_db"


def get_vector_db_path(company_id: str, project_id: str, shard_id: str = "default") -> Path:
    """Path to a specific Chroma persist_directory.

    Each shard_id maps to an independent Chroma instance.
    Use 'default' for single-shard projects.
    Use numeric IDs (5001, 5002, ...) for domain-partitioned shards.

    Example:
        get_vector_db_path("acme", "proj-001", "5001")
        → storage/acme/proj-001/vector_db/V5001
    """
    folder = f"V{shard_id}" if not str(shard_id).startswith("V") else str(shard_id)
    return get_vector_db_root(company_id, project_id) / folder


def list_shard_paths(company_id: str, project_id: str) -> list[Path]:
    """Return all existing V{shard_id} directories for cross-shard search."""
    root = get_vector_db_root(company_id, project_id)
    if not root.exists():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("V"))


# ── Directory initialiser ────────────────────────────────────────────────────

def ensure_project_dirs(company_id: str, project_id: str) -> None:
    """Create all required subdirectories for a project on first use."""
    for fn in (get_raw_root, get_uploads_path, get_ontology_path, get_vector_db_root):
        fn(company_id, project_id).mkdir(parents=True, exist_ok=True)


# ── Convenience constants (default tenant for backward compat) ────────────────

DEFAULT_COMPANY = "default"
DEFAULT_PROJECT = "proj-default"
