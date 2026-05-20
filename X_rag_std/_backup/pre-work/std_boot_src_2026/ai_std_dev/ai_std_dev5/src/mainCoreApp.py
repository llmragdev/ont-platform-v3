import uvicorn
import os
from dotenv import load_dotenv

# [핵심] 어떤 모듈 import 보다도 최우선으로 실행되어야 합니다.
load_dotenv()

from fastapi import FastAPI
from core.llm.app import llmSrvApp # 이제 안전하게 로드됩니다.

app = FastAPI(
    title="AI Standard Core Infrastructure",
    description="본사 표준 인프라 - Gemini 2.5 Flash 엔진 레이어",
    version="1.0.0"
)

app.include_router(llmSrvApp.router)

@app.get("/", tags=["Root"])
async def root():
    return {
        "module": "Core Infrastructure",
        "status": "Running",
        "engine": os.getenv("LLM_MODEL_NAME")
    }

if __name__ == "__main__":
    uvicorn.run("mainCoreApp:app", host="0.0.0.0", port=8001, reload=True)