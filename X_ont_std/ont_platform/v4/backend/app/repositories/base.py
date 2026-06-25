"""BaseRepository — Common JSON persistence logic."""
from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from app.models.tenant_context import TenantContext
from storage_config import ensure_project_dirs, get_project_root

logger = logging.getLogger(__name__)


class BaseRepository:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    def _get_storage_path(self, ctx: TenantContext) -> Path:
        raise NotImplementedError

    def _get_file_path(self, ctx: TenantContext, identifier: str) -> Path:
        return self._get_storage_path(ctx) / f"{identifier}.json"

    def _ensure_dir(self, ctx: TenantContext) -> None:
        ensure_project_dirs(ctx.company_id, ctx.project_id)

    def _load_json(self, path: Path, default: Any = None) -> Any:
        if not path.exists():
            return default if default is not None else {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error("Failed to load JSON from %s: %s", path, e)
            return default if default is not None else {}

    def _save_json(self, path: Path, data: Any) -> None:
        """Save JSON file atomically using rename pattern (safe for concurrent writes)"""
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = None
        try:
            # Priority 3: Atomic Rename pattern
            # Write to temporary file, then atomic rename
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=path.parent,
                delete=False,
                suffix='.tmp',
                encoding='utf-8'
            ) as tmp_file:
                json.dump(data, tmp_file, ensure_ascii=False, indent=2)
                tmp_path = tmp_file.name

            # Atomic rename (race-condition safe on both Unix and Windows)
            # On Windows, must remove target first if it exists
            if path.exists():
                path.unlink()
            os.replace(tmp_path, path)
        except Exception as e:
            # Clean up temp file if rename fails
            try:
                if tmp_path and Path(tmp_path).exists():
                    os.unlink(tmp_path)
            except:
                pass
            logger.error("Failed to save JSON to %s: %s", path, e)
            raise
