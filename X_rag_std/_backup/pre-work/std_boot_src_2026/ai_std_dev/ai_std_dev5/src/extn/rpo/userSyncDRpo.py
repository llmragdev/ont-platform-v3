from extn.models.userMdl import User
from extn.utility.pgSyncOrmAdapter import PgSyncOrmAdapter

class UserSyncRepository:
    def list_users(self, name: str = None):
        print(f"[Rpo] 좋은 사례 로그: 어댑터에 {name} 필터 조회를 요청합니다.")
        filter_params = {"name": name} if name else None
        return PgSyncOrmAdapter.execute_fetch_filter(User, filter_params)