"""BaseRepository — Common JSON persistence logic with TenantContext awareness."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.models.tenant_context import TenantContext
from storage_config import ensure_project_dirs, get_project_root

logger = logging.getLogger(__name__)


class BaseRepository:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    def _get_storage_path(self, ctx: TenantContext) -> Path:
        """Get the directory where this collection's data is stored."""
        raise NotImplementedError("Subclasses must implement _get_storage_path")

    def _get_file_path(self, ctx: TenantContext, identifier: str) -> Path:
        """Get the path to a specific JSON file."""
        return self._get_storage_path(ctx) / f"{identifier}.json"

    def _ensure_dir(self, ctx: TenantContext) -> None:
        """Ensure the project directory exists."""
        ensure_project_dirs(ctx.company_id, ctx.project_id)

    def _load_json(self, path: Path, default: Any = None) -> Any:
        if not path.exists():
            return default if default is not None else {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Failed to load JSON from {path}: {e}")
            return default if default is not None else {}

    def _save_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save JSON to {path}: {e}")
            raise
