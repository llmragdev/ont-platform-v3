import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, TypeVar, Generic
from app.models.identity import UserIdentity
from storage_config import storage_config

T = TypeVar("T")

class BaseRepository:
    """테넌트 격리가 내장된 JSON 기반 영속성 베이스 클래스 (원자적 쓰기 강화)"""
    
    def __init__(self, company_id: str, project_id: str):
        self.company_id = company_id
        self.project_id = project_id
        self.root_path = storage_config.get_project_root(company_id, project_id)

    def _get_file_path(self, filename: str) -> Path:
        """지정된 파일명에 대한 물리적 경로 반환 (테넌트 디렉토리 내)"""
        if "ontology" in filename:
            path = storage_config.get_sub_dir(self.company_id, self.project_id, "ontology") / filename
        elif "audit" in filename:
            path = self.root_path / filename  # Audit은 루트에 바로 기록
        else:
            path = self.root_path / filename
        return path

    def _load_json(self, filename: str) -> List[Dict[str, Any]]:
        path = self._get_file_path(filename)
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def _save_json(self, filename: str, data: List[Dict[str, Any]]):
        """원자적(Atomic) 쓰기를 통한 파일 손상 방지"""
        path = self._get_file_path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 임시 파일에 먼저 쓰고 이동 (Atomic Rename)
        fd, temp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, str(path))
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
