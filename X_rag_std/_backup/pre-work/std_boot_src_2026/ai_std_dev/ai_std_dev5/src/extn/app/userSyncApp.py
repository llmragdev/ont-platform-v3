from fastapi import APIRouter
from extn.biz.userAntiSyncBiz import UserAntiSyncService
from extn.biz.userSyncBiz import UserSyncService

router = APIRouter(prefix="/sync", tags=["04. RDBMS-Sync-Architecture"])

anti_service = UserAntiSyncService()
best_service = UserSyncService()

@router.get("/coupled-infra-logic")
def list_users_anti_pattern(name: str = None):
    print(f"\n[App] API 호출: coupled-infra-logic (검색어: {name})")
    # [Anti-Pattern] 기술 결합 사례 호출
    return anti_service.list_users_with_infra_coupling(name)

@router.get("/isolated-adapter-logic")
def list_users_best_practice(name: str = None):
    print(f"\n[App] API 호출: isolated-adapter-logic (검색어: {name})")
    # [Best-Practice] 기술 격리 사례 호출
    return best_service.list_users(name)