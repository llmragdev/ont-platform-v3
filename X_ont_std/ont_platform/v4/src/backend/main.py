"""ont_platform v4 — FastAPI entry point (Week 7 Ontology Extension)"""
import logging
import sys
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

# 경로 설정
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers.ontology_api import router as ontology_router

# FastAPI 앱 생성
app = FastAPI(
    title="ont_platform v4 - Ontology Extension API",
    description="Week 7 UI - RDF Graph Traversal, Mapping, Import Preview",
    version="0.4.0"
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모두 허용, 프로덕션에서는 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 루트 경로
@app.get("/")
async def root():
    """API 루트 정보"""
    return {
        "name": "ont_platform v4 - Ontology Extension",
        "version": "0.4.0",
        "features": [
            "RDF Graph Neighborhood Traversal (Task 7-1)",
            "Ontology Mapping (Task 7-2)",
            "RDF Import Preview (Task 7-3)"
        ],
        "endpoints": {
            "health": "/api/ontology/health",
            "neighborhood": "/api/ontology/rdf/neighborhood/{uri}",
            "create_mapping": "POST /api/ontology/mappings",
            "mapping_candidates": "/api/ontology/mapping-candidates",
            "import_preview": "POST /api/ontology/import/preview",
            "import": "POST /api/ontology/import"
        }
    }


# 라우터 등록
app.include_router(ontology_router)


# 예외 처리
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """일반 예외 처리"""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn

    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║ ont_platform v4 - Ontology Extension API               ║
    ║ Week 7: RDF Graph Traversal, Mapping, Import Preview   ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
