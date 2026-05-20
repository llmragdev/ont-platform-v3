import uvicorn
import os
from dotenv import load_dotenv

# [핵심] 모듈 import 전 환경변수 우선 로드
load_dotenv()

from fastapi import FastAPI
# 비동기 전용 라우터 임포트 (파일명 Suffix 주의)
from core.llm.app.llmSrvAsyncApp import router as llm_async_router

app = FastAPI(
    title="Standard AI Core Async Infrastructure",
    description="전사 공통 LLM 추론 비동기 엔진 (Port 8010)",
    version="1.0.0"
)

# 비동기 전용 라우터 등록
app.include_router(llm_async_router)

@app.get("/", tags=["Root"])
async def root():
    return {
        "module": "Core Async Infrastructure",
        "status": "Running",
        "port": 8010,
        "engine": os.getenv("LLM_MODEL_NAME", "gemini-2.0-flash-lite")
    }

if __name__ == "__main__":
    # 동기(8001)와 겹치지 않게 8010 포트 사용
    print("🚀 Starting Core Async Inference Server on Port 8010...")
    uvicorn.run("mainCoreAsyncApp:app", host="0.0.0.0", port=8010, reload=True)