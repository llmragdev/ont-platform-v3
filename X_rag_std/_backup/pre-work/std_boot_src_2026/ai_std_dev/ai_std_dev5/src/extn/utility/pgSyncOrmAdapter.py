from extn.utility.databaseUtil import SyncSessionLocal

class PgSyncOrmAdapter:
    @staticmethod
    def execute_fetch_filter(model_class, filter_dict: dict = None):
        # 기술 상세를 이 메서드 하나로 완전히 캡슐화함
        db = SyncSessionLocal()
        try:
            query = db.query(model_class)
            if filter_dict:
                print(f"[Adapter] 좋은 사례 로그: 전문 어댑터가 {filter_dict} 조건으로 필터링을 격리 처리합니다.")
                for key, value in filter_dict.items():
                    query = query.filter(getattr(model_class, key) == value)
            else:
                print("[Adapter] 좋은 사례 로그: 검색 조건 없이 전체 데이터를 조회합니다.")
            return query.all()
        finally:
            db.close()