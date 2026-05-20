from extn.utility.databaseUtil import SyncSessionLocal 
from extn.rpo.userSyncAntiDRpo import UserSyncAntiRepository

class UserAntiSyncService:
    def __init__(self):
        self.repo = UserSyncAntiRepository()

    def list_users_with_infra_coupling(self, name: str = None):
        # 나쁜 예: 비즈니스 계층에 세션 생성/종료 로직이 노출됨
        print(f"[Biz] 나쁜 사례 로그: 직접 세션을 생성하여 {name} 검색을 처리합니다.")
        db = SyncSessionLocal() 
        try:
            return self.repo.read_orm_with_tech_dep(db, name)
        finally:
            print("[Biz] 나쁜 사례 로그: 직접 세션을 닫습니다.")
            db.close()