"""
Team0 Validator Configuration
검증 프로젝트의 설정 및 상수 정의

Updated: 2026-06-07 (v1.1)
- 절대 경로로 대상 문서 및 Team0 소스 지정
- Team0 API 엔드포인트 수정 (/api/v1/rag/search)
- 필수 헤더 추가 (X-Tenant-ID, X-Org-ID)
"""

import os
from pathlib import Path

# 경로 설정
BASE_DIR = Path(__file__).resolve().parent
TARGET_DOC_DIR = Path("E:/ai_lab_SIT/target_doc")
TEAM0_SOURCE_DIR = Path("E:/ai_lab_SIT/team0_rag_source")
RESULTS_DIR = BASE_DIR / "results"

# Gemini API 설정 (LLM Gateway)
GEMINI_EMBEDDING_API = "http://localhost:8011/api/v1/embed"
GEMINI_EMBEDDING_DIM = 3072
GEMINI_LLM_API = "http://localhost:8011/api/v1/chat"

# 벡터 DB 설정
VECTOR_DB_PATH = RESULTS_DIR / "vector_db.json"
ONTOLOGY_DB_PATH = RESULTS_DIR / "ontology.json"

# 테스트 설정
TEST_QUERIES = [
    "온톨로지란 무엇인가?",
    "온톨로지 매칭 방법에는 어떤 것들이 있는가?",
    "지식그래프와 온톨로지의 관계는?",
    "RDF는 무엇인가?",
    "생성형 AI와 NLP의 관계는?",
    "문맥 인식 감성 분석이란?",
    "국방 분야에서 온톨로지를 어떻게 활용하는가?",
    "한국근대문인 데이터베이스 구축 방법은?",
    "온톨로지 기반 의미 속성 판별이란?",
    "언어모델의 발전 과정은?",
]

# Team0 API 설정
TEAM0_API_BASE = "http://localhost:8002"
TEAM0_SEARCH_ENDPOINT = "/api/v1/rag/search"
TEAM0_UPLOAD_ENDPOINT = "/api/v1/documents/upload"
TEAM0_TENANT_ID = "company_abc"
TEAM0_ORG_ID = "0200"

# Team0 API 필수 헤더
TEAM0_HEADERS = {
    "X-Tenant-ID": "company_abc",
    "X-Org-ID": "0200",
    "Content-Type": "application/json",
}

# 로깅 설정
LOG_LEVEL = "INFO"

# 평가 기준
ACCURACY_THRESHOLD = 0.5
RELEVANCE_THRESHOLD = 0.6

# 청크 처리 설정
CHUNK_SIZE = 512  # 토큰 기준
CHUNK_OVERLAP = 50  # 겹침 토큰

# 벡터 검색 설정
TOP_K = 5  # 상위 K개 결과 반환

# 온톨로지 설정
ONTOLOGY_CONCEPTS = [
    "온톨로지",
    "지식그래프",
    "RDF",
    "SPARQL",
    "의미론",
    "분류",
    "매칭",
    "임베딩",
    "벡터",
    "LLM",
    "생성형AI",
    "NLP",
    "감성분석",
    "지식표현",
]

# 타임아웃 설정 (초)
TEAM0_TIMEOUT = 30
GEMINI_TIMEOUT = 30

# 재시도 설정
MAX_RETRIES = 3
RETRY_DELAY = 1  # 초

# 검증 설정
VALIDATION_MIN_CHUNKS = 300  # 최소 청크 수
VALIDATION_MIN_RELATIONSHIPS = 20  # 최소 관계 수

if __name__ == "__main__":
    print(f"✅ Config v1.1 loaded: {BASE_DIR}")
    print(f"📁 Target docs: {TARGET_DOC_DIR}")
    print(f"📁 Team0 source: {TEAM0_SOURCE_DIR}")
    print(f"📁 Results: {RESULTS_DIR}")
    print(f"🔗 Team0 API: {TEAM0_API_BASE}")
    print(f"🔗 Gemini Embedding: {GEMINI_EMBEDDING_API}")
