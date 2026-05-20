from fastapi import FastAPI
import uvicorn
from extn.app.userAsyncApp import router as async_user_router

app = FastAPI(
    title="AI Standard Backend API(비동기)",
    description="[데이터] 객체기반 RDBMS 연동 실무-비동기 방식",
    version="1.1.0"
)

# 비동기 전용 라우터만 등록
app.include_router(async_user_router, prefix="/async", tags=["Async-Operations"])

if __name__ == "__main__":
    # 비동기 서버이므로 포트를 달리하여(예: 8001) 동기 서버와 동시 실행 비교도 가능
    uvicorn.run("mainExtnAsyncApp:app", host="0.0.0.0", port=8051, reload=True)