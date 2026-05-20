from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from extn.utility.databaseUtil import AsyncSessionLocal 

class PgAsyncOrmAdapter:
    @staticmethod
    async def execute_fetch_all(model_class, filter_dict: dict = None):
        """[핵심] 이름 유무에 따른 동적 조회 및 인프라 격리 """
        async with AsyncSessionLocal() as db:  
            query = select(model_class).order_by(model_class.id.desc())
            
            # filter_dict가 존재하고 내용이 있으면 동적 필터링 적용 
            if filter_dict:
                for key, value in filter_dict.items():
                    if value is not None:
                        query = query.filter(getattr(model_class, key) == value)
            
            result = await db.execute(query)  
            return result.scalars().all()  

    @staticmethod
    async def execute_save_avoid(model_instance):
        """[패턴 A] ID 미반환: 단순 저장만 수행 (채번 정보 누락)"""
        async with AsyncSessionLocal() as db:
            db.add(model_instance)
            await db.commit()
            return None # 또는 성공 여부만 반환

    @staticmethod
    async def execute_save_return(model_instance):
        """[패턴 B] ID 반환: DB 채번 값을 객체에 동기화"""
        async with AsyncSessionLocal() as db:
            db.add(model_instance)
            await db.commit()
            await db.refresh(model_instance) # 핵심: DB 생성 ID를 메모리 객체로 확보
            return model_instance