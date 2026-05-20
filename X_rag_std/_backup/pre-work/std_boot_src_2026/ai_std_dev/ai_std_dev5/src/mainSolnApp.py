# F:\ai_std_dev\ai_std_dev5\src\mainSolnApp.py 수정본

import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from soln.qabot.app import qaApp

app = FastAPI(
    title="AI Standard Solution",
    description="표준 QA 봇 솔루션 - RAG 서비스 레이어",
    version="1.0.0"
)

# [수정] 호출하시던 URL 구조에 맞게 prefix를 추가합니다.
app.include_router(qaApp.router, prefix="/soln/qabot")

if __name__ == "__main__":
    uvicorn.run("mainSolnApp:app", host="0.0.0.0", port=8002, reload=True)