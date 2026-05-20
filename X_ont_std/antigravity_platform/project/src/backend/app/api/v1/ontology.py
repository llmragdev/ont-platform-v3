from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_current_identity, PermissionChecker
from app.models.identity import UserIdentity
from app.services.ontology import OntologyService

router = APIRouter()

@router.get("/entities")
async def list_entities(
    type: Optional[str] = Query(None),
    identity: UserIdentity = Depends(get_current_identity)
):
    """현재 테넌트/프로젝트 내의 엔티티 목록 조회"""
    service = OntologyService(identity)
    return service.get_all_entities(type)

@router.post("/entities", status_code=201)
async def create_entity(
    entity_data: Dict[str, Any],
    identity: UserIdentity = Depends(PermissionChecker("can_edit_ontology"))
):
    """새 엔티티 생성 (권한 필요)"""
    service = OntologyService(identity)
    return service.create_new_entity(entity_data)

@router.get("/relationships")
async def list_relationships(
    type: Optional[str] = Query(None),
    identity: UserIdentity = Depends(get_current_identity)
):
    """현재 테넌트/프로젝트 내의 관계 목록 조회"""
    service = OntologyService(identity)
    return service.get_all_relationships(type)

@router.post("/relationships", status_code=201)
async def create_relationship(
    rel_data: Dict[str, Any],
    identity: UserIdentity = Depends(PermissionChecker("can_edit_ontology"))
):
    """새 관계 생성 (권한 필요)"""
    service = OntologyService(identity)
    return service.create_new_relationship(rel_data)
