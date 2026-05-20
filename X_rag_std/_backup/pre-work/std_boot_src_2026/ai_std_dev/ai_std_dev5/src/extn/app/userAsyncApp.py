from fastapi import APIRouter, Depends
from extn.biz.userAsyncBiz import UserAsyncService
from extn.schemas.userSch import UserCreate, UserRead, UserSearch

router = APIRouter()
service = UserAsyncService()

@router.get("/users", response_model=list[UserRead])
async def list_users(filters: UserSearch = Depends()):
    """[보완] 이름이 있으면 필터링, 없으면 전체 조회 (UserSearch 객체 활용)"""
    return await service.get_users_list(filters)

@router.post("/users/avoid-key")
async def create_user_avoid(data: UserCreate):
    """[패턴 A] 생성된 ID 없이 단순 성공 메시지만 반환"""
    await service.register_user_avoid(data)
    return {"message": "사용자 정보가 저장되었습니다. (ID 확인 불가)"}

@router.post("/users/return-key", response_model=UserRead)
async def create_user_return_key(data: UserCreate):
    """[패턴 B] 채번된 user_id를 포함한 전체 객체 반환"""
    return await service.register_user_return(data)