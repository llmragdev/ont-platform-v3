from extn.rpo.userSyncDRpo import UserSyncRepository

class UserSyncService:
    def __init__(self):
        self.repo = UserSyncRepository()

    def list_users(self, name: str = None):
        print(f"[Biz] 좋은 사례 로그: {name} 검색 요청을 리포지토리에 전달합니다.")
        return self.repo.list_users(name)