import json
from typing import List, Dict, Any, Optional
from app.models.identity import UserIdentity
from storage_config import storage_config

class OntologySchemaService:
    """테넌트별 온톨로지 스키마(타입 정의) 관리 서비스"""

    def __init__(self, identity: UserIdentity):
        self.identity = identity
        self.schema_path = storage_config.get_sub_dir(
            identity.company_id, 
            identity.current_project_id, 
            "ontology"
        ) / "schema.json"

    def get_current_schema(self) -> Dict[str, Any]:
        """현재 프로젝트의 스키마 로드 (없으면 기본 스키마 반환)"""
        if not self.schema_path.exists():
            return self._get_default_schema()
            
        try:
            with open(self.schema_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return self._get_default_schema()

    def get_prompt_summary(self) -> str:
        """LLM 프롬프트에 주입할 요약된 스키마 텍스트 생성"""
        schema = self.get_current_schema()
        
        summary = "Available Entity Types:\n"
        for etype, details in schema.get("entity_types", {}).items():
            props = ", ".join(details.get("properties", {}).keys())
            summary += f"- {etype}: properties({props})\n"
            
        summary += "\nAvailable Relationship Types:\n"
        for rtype in schema.get("relationship_types", {}).keys():
            summary += f"- {rtype}\n"
            
        return summary

    def _get_default_schema(self) -> Dict[str, Any]:
        """시스템 기본 스키마 (초기 프로젝트용)"""
        return {
            "entity_types": {
                "EQUIPMENT": {"properties": {"name": "str", "status": "str"}},
                "LOCATION": {"properties": {"name": "str", "address": "str"}}
            },
            "relationship_types": {
                "LOCATED_IN": {"source": "EQUIPMENT", "target": "LOCATION"}
            }
        }
