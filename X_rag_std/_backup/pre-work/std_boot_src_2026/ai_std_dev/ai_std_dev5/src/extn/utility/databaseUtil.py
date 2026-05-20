import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

# 비동기 설정 (asyncpg)
ASYNC_DB_URL = DB_URL.replace("postgresql://", "postgresql+asyncpg://")
async_engine = create_async_engine(ASYNC_DB_URL, echo=True, connect_args={"statement_cache_size": 0})
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# 동기 설정 (psycopg2)
sync_engine = create_engine(DB_URL, echo=False)
engine = sync_engine  # ✅ mainApp.py에서 'engine'으로 찾을 수 있도록 추가
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

Base = declarative_base()

def get_sync_db():
    db = SyncSessionLocal()
    try: yield db
    finally: db.close()

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session