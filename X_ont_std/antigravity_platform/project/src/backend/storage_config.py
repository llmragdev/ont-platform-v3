import os
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any

# 기본 저장소 루트 설정 (E:\ontology_edu\antigravity_platform\storage)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_ROOT = BASE_DIR / "storage"

class StorageConfig:
    """테넌트 및 프로젝트별 물리적 격리 경로와 설정을 관리하는 팩토리 클래스"""
    
    @staticmethod
    def validate_id(id_str: str):
        """Path Traversal 방지를 위한 ID 검증 (영문, 숫자, 하이픈만 허용)"""
        if not re.match(r"^[a-zA-Z0-9\-_]+$", id_str):
            raise ValueError(f"Invalid ID format (Path Traversal Risk): {id_str}")

    @staticmethod
    def get_tenant_root(company_id: str) -> Path:
        StorageConfig.validate_id(company_id)
        tenant_path = STORAGE_ROOT / company_id
        tenant_path.mkdir(parents=True, exist_ok=True)
        return tenant_path

    @staticmethod
    def get_project_root(company_id: str, project_id: str) -> Path:
        StorageConfig.validate_id(company_id)
        StorageConfig.validate_id(project_id)
        project_path = StorageConfig.get_tenant_root(company_id) / project_id
        project_path.mkdir(parents=True, exist_ok=True)
        return project_path

    @staticmethod
    def get_sub_dir(company_id: str, project_id: str, sub_type: str) -> Path:
        """프로젝트 내 서브 디렉토리(raw, vector_db, ontology, uploads) 경로 반환"""
        if sub_type not in ["raw", "vector_db", "ontology", "uploads"]:
            raise ValueError(f"Invalid storage sub-type: {sub_type}")
            
        sub_path = StorageConfig.get_project_root(company_id, project_id) / sub_type
        sub_path.mkdir(parents=True, exist_ok=True)
        return sub_path

    @staticmethod
    def get_tenant_settings(company_id: str) -> Dict[str, Any]:
        """테넌트 설정 로드 (없을 경우 기본값 반환)"""
        settings_path = StorageConfig.get_tenant_root(company_id) / "tenant_settings.json"
        if not settings_path.exists():
            return {
                "company_id": company_id,
                "display_name": f"Company {company_id}",
                "status": "active",
                "features": {"ontology_editing": True, "hybrid_query": True}
            }
        with open(settings_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def get_project_settings(company_id: str, project_id: str) -> Dict[str, Any]:
        """프로젝트 설정 로드 (없을 경우 기본값 반환)"""
        settings_path = StorageConfig.get_project_root(company_id, project_id) / "project_settings.json"
        if not settings_path.exists():
            return {
                "project_id": project_id,
                "display_name": f"Project {project_id}",
                "rag": {"top_k": 5}
            }
        with open(settings_path, "r", encoding="utf-8") as f:
            return json.load(f)

# 싱글톤 인스턴스 노출
storage_config = StorageConfig()
