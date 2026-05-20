from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.middleware import IdentityMiddleware
from app.api.deps import get_current_identity
from app.models.identity import UserIdentity
from storage_config import storage_config

app = FastAPI(
    title="Antigravity Platform API",
    description="Enterprise Hybrid Ontology & RAG Platform",
    version="0.1.0"
)

# 1. CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1 import ontology, documents, hybrid

# 2. Identity 미들웨어 등록 (가장 먼저 실행되도록)
app.add_middleware(IdentityMiddleware)

# 3. Router 등록
app.include_router(ontology.router, prefix="/api/v1/ontology", tags=["Ontology"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(hybrid.router, prefix="/api/v1/hybrid", tags=["Hybrid"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Antigravity Platform",
        "status": "operational"
    }

@app.get("/api/v1/tenant/me")
async def get_my_tenant_info(identity: UserIdentity = Depends(get_current_identity)):
    """현재 로그인된 사용자의 테넌트/프로젝트 정보 및 물리적 설정을 확인"""
    # 1. 테넌트 및 프로젝트 설정 로드
    tenant_settings = storage_config.get_tenant_settings(identity.company_id)
    project_settings = storage_config.get_project_settings(identity.company_id, identity.current_project_id)
    
    return {
        "identity": identity,
        "tenant_config": tenant_settings,
        "project_config": project_settings,
        "physical_paths": {
            "project_root": str(storage_config.get_project_root(identity.company_id, identity.current_project_id)),
            "ontology_db": str(storage_config.get_ontology_db_path(identity.company_id, identity.current_project_id)),
            "vector_db": str(storage_config.get_vector_db_dir(identity.company_id, identity.current_project_id))
        }
    }

# 향후 여기에 각 도메인별 Router 추가 예정
# app.include_router(ontology.router, prefix="/api/v1/ontology", tags=["Ontology"])
