from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from app.models.identity import UserIdentity
from app.repositories.ontology import OntologyRepository
from app.services.audit import AuditService

class OntologyService:
    """온톨로지 비즈니스 로직 및 무결성 검증 담당"""

    def __init__(self, identity: UserIdentity):
        self.identity = identity
        self.repo = OntologyRepository(identity.company_id, identity.current_project_id)
        self.audit = AuditService(identity)

    def get_all_entities(self, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.repo.list_entities(entity_type)

    def create_new_entity(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """엔티티 생성 (비즈니스 규칙 검증 가능)"""
        if "type" not in entity_data:
            raise HTTPException(status_code=422, detail="Entity type is required")
        
        new_entity = self.repo.create_entity(entity_data, self.identity.user_id)
        
        # 감사 로그 기록
        self.audit.log_action("CREATE_ENTITY", new_entity["id"], {"type": new_entity["type"]})
        
        return new_entity

    def create_new_relationship(self, rel_data: Dict[str, Any]) -> Dict[str, Any]:
        """관계 생성 및 무결성 검증"""
        # 1. 필수 필드 체크
        required = ["type", "source_id", "target_id"]
        for field in required:
            if field not in rel_data:
                raise HTTPException(status_code=422, detail=f"Field {field} is required")
        
        # 2. Source/Target 엔티티 존재 여부 확인 (Referential Integrity)
        if not self.repo.get_entity(rel_data["source_id"]):
            raise HTTPException(status_code=404, detail=f"Source entity {rel_data['source_id']} not found")
        if not self.repo.get_entity(rel_data["target_id"]):
            raise HTTPException(status_code=404, detail=f"Target entity {rel_data['target_id']} not found")

        new_rel = self.repo.create_relationship(rel_data, self.identity.user_id)
        
        # 감사 로그 기록
        self.audit.log_action("CREATE_RELATIONSHIP", new_rel["id"], {
            "type": new_rel["type"],
            "source": new_rel["source_id"],
            "target": new_rel["target_id"]
        })
        
        return new_rel

    def get_all_relationships(self, rel_type: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.repo.list_relationships(rel_type)
