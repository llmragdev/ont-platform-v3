from datetime import datetime
from uuid import uuid4
from typing import List, Dict, Any, Optional
from app.repositories.base import BaseRepository

class OntologyRepository(BaseRepository):
    """범용 엔티티 및 관계 인스턴스를 관리하는 저장소"""

    ENTITY_FILE = "ontology_objects.json"
    RELATION_FILE = "ontology_relationships.json"

    def list_entities(self, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """테넌트 내 엔티티 목록 조회"""
        entities = self._load_json(self.ENTITY_FILE)
        if entity_type:
            return [e for e in entities if e.get("type") == entity_type]
        return entities

    def create_entity(self, entity_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """새 엔티티 생성 (메타데이터 자동 주입)"""
        entities = self._load_json(self.ENTITY_FILE)
        
        new_entity = {
            "id": entity_data.get("id", str(uuid4())),
            "company_id": self.company_id,
            "project_id": self.project_id,
            "type": entity_data["type"],
            "values": entity_data.get("values", {}),
            "origin": entity_data.get("origin", "manual"),
            "status": "active",
            "created_by": user_id,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        entities.append(new_entity)
        self._save_json(self.ENTITY_FILE, entities)
        return new_entity

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        entities = self._load_json(self.ENTITY_FILE)
        for e in entities:
            if e["id"] == entity_id:
                return e
        return None

    def list_relationships(self, rel_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """테넌트 내 관계 목록 조회"""
        relations = self._load_json(self.RELATION_FILE)
        if rel_type:
            return [r for r in relations if r.get("type") == rel_type]
        return relations

    def create_relationship(self, rel_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """새 관계 생성"""
        relations = self._load_json(self.RELATION_FILE)
        
        new_rel = {
            "id": str(uuid4()),
            "company_id": self.company_id,
            "project_id": self.project_id,
            "type": rel_data["type"],
            "source_id": rel_data["source_id"],
            "target_id": rel_data["target_id"],
            "properties": rel_data.get("properties", {}),
            "status": "active",
            "created_by": user_id,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        relations.append(new_rel)
        self._save_json(self.RELATION_FILE, relations)
        return new_rel
