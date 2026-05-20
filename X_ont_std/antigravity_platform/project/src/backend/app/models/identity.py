from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class PermissionSet(BaseModel):
    """사용자 권한 플래그 집합"""
    can_read: bool = True
    can_edit_ontology: bool = False
    can_upload_docs: bool = False
    can_delete_docs: bool = False
    can_manage_users: bool = False

class UserIdentity(BaseModel):
    """인증 및 테넌트 정보를 포함하는 통합 사용자 모델"""
    user_id: str
    username: str
    company_id: str
    current_project_id: str
    role: str  # admin, editor, viewer
    permissions: PermissionSet
    
    # 추가 메타데이터
    project_ids: List[str] = Field(default_factory=list)
    
    class Config:
        frozen = True  # 불변성 유지

class TenantProject(BaseModel):
    """테넌트 내 프로젝트 정보"""
    id: str
    display_name: str
    company_id: str
    description: Optional[str] = None
