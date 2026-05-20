import os
from dotenv import load_dotenv

load_dotenv()

BASE_DATA_DIR = r"F:\ai_std_dev\data\qabot"

def get_project_root(company_id, project_id):
    return os.path.join(BASE_DATA_DIR, company_id, project_id)

def get_raw_root(company_id, project_id):
    """원천 파일들이 담긴 raw 최상위 경로"""
    return os.path.join(get_project_root(company_id, project_id), "raw")

def get_vector_db_path(company_id, project_id, target_group):
    """지정한 target_group(예: 5001)에 맞는 V폴더 경로 반환"""
    folder_name = f"V{target_group}" if not str(target_group).startswith('V') else target_group
    return os.path.join(get_project_root(company_id, project_id), "vector_db", folder_name)

EMBEDDING_MODEL = "models/gemini-embedding-001"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
    os.environ["USER_AGENT"] = "QABot_Expert_V3/1.0"