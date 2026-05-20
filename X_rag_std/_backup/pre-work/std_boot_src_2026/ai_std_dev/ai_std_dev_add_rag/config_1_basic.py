import os
from dotenv import load_dotenv

load_dotenv()

# [업데이트] 최상위 기본 경로 설정
BASE_DATA_DIR = r"F:\ai_std_dev\data\qabot"

def get_project_root(company_id, project_id):
    """결과: F:\ai_std_dev\data\qabot\{company_id}\{project_id}"""
    return os.path.join(BASE_DATA_DIR, company_id, project_id)

def get_raw_path(company_id, project_id, mid="", sub=""):
    """결과: ...\{project_id}\raw\{mid}\{sub}"""
    base = os.path.join(get_project_root(company_id, project_id), "raw")
    if mid and sub:
        return os.path.join(base, mid, sub)
    return base

def get_vector_db_path(company_id, project_id):
    """결과: ...\{project_id}\vector_db"""
    return os.path.join(get_project_root(company_id, project_id), "vector_db")

# 모델 설정 (기존 소스 유지)
EMBEDDING_MODEL = "models/gemini-embedding-001"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
    os.environ["USER_AGENT"] = "QABot_Enterprise/1.0"