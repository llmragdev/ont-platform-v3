from userinfo.repository.userInfoRpo import UserInfoRepository
from userinfo.schemas.userInfoSch import UserInfoRead, UserInfoSearch, UserInfoSummary


class UserInfoBizService:
    def __init__(self):
        self.repo = UserInfoRepository()

    def search_users(self, keyword: str | None, limit: int) -> list[UserInfoRead]:
        search = UserInfoSearch(keyword=keyword, limit=limit)
        return self.repo.list_users(search)

    def get_summary(self, keyword: str | None) -> UserInfoSummary:
        return UserInfoSummary(
            total_count=self.repo.count_users(keyword),
            keyword=(keyword or "").strip() or None,
        )
