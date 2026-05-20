from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase): 
    """등록 시 사용되는 스키마"""
    pass

class UserRead(UserBase):
    """[핵심] 외부 노출용 규격 (Alias 적용으로 물리-논리 분리)"""
    # DB의 'id'를 'user_id'로 매핑하여 인터페이스 자산화 [cite: 206, 233]
    user_id: int = Field(validation_alias="id")
    created_at: datetime

    # ORM 모델 속성 참조 허용 설정 [cite: 230, 235]
    model_config = ConfigDict(from_attributes=True)

class UserSearch(BaseModel):
    """[핵심] 조회 파라미터 자산화: 이름 유무에 따른 필터링 지원"""
    name: Optional[str] = Field(None, description="검색할 사용자 이름")

# 기존 코드 호환성 유지
UserResponse = UserRead