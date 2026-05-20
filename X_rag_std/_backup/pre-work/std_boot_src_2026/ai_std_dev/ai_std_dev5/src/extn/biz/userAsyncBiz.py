from extn.rpo.userAsyncDRpo import UserAsyncRepository
from extn.models.userMdl import User
from extn.schemas.userSch import UserCreate, UserSearch

class UserAsyncService:
    """비동기 비즈니스 로직 (순수 도메인 중심)"""
    
    def __init__(self):
        self.repo = UserAsyncRepository()

    async def get_users_list(self, filters: UserSearch):
        # 검색 조건 객체를 그대로 리포지토리에 전달
        return await self.repo.get_users(filters)

    async def register_user_avoid(self, data: UserCreate):
        """ID를 반환하지 않는 등록 로직"""
        user_obj = User(**data.model_dump())
        return await self.repo.save_user_avoid(user_obj)

    async def register_user_return(self, data: UserCreate):
        """ID를 포함하여 반환하는 등록 로직"""
        user_obj = User(**data.model_dump())
        return await self.repo.save_user_return(user_obj)    