import uvicorn
from fastapi import FastAPI
from extn.app import userSyncApp

app = FastAPI(
    title="AI Standard Backend API(동기)",
    description="[데이터] 객체기반 RDBMS 연동 실무-동기 방식",
    version="1.1.0"
)

# 4장 핵심 비교 실습 라우터 등록
app.include_router(userSyncApp.router)

if __name__ == "__main__":
    uvicorn.run("mainExtnApp:app", host="0.0.0.0", port=8050, reload=True)