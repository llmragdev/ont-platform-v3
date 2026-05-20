from extn.models.userMdl import User
from extn.utility.pgAsyncOrmAdapter import PgAsyncOrmAdapter
from extn.schemas.userSch import UserSearch

class UserAsyncRepository:
    async def get_users(self, filters: UserSearch):
        """[핵심] 스키마 객체를 필터 딕셔너리로 변환하여 어댑터 호출"""
        # None이 아닌 필드만 추출 (이름이 없으면 빈 딕셔너리 반환 -> 전체 조회)
        filter_params = filters.model_dump(exclude_none=True)
        return await PgAsyncOrmAdapter.execute_fetch_all(User, filter_params)

    async def save_user_avoid(self, user: User):
        return await PgAsyncOrmAdapter.execute_save_avoid(user)

    async def save_user_return(self, user: User):
        return await PgAsyncOrmAdapter.execute_save_return(user)