"""통합 테스트 설정 상수."""
from __future__ import annotations

BASE_URL = "http://localhost:8000"

# 서버에 이미 업로드된 Snowflake 소개서 (29 청크)
SNOWFLAKE_DOC_ID = "doc-ff68a066"

# 시드 데이터를 심을 온톨로지 doc_id (실제 문서와 분리해 충돌 방지)
SEED_DOC_ID = "doc-integration-seed"

# 기본 인증 사용자 (데모 모드 ?user= 쿼리)
DEFAULT_USER = "analyst"

# 요청 헤더
HEADERS = {"Content-Type": "application/json"}

# 채점 가중치
SCORE_TYPE_MATCH  = 40   # 기대 query_type 일치
SCORE_ANSWER_OK   = 20   # answer 비어있지 않고 100자 이상
SCORE_DATA_COND   = 30   # 시나리오별 데이터 조건
SCORE_LATENCY     = 10   # 15초 미만

PASS_THRESHOLD    = 60   # 이 점수 이상이면 PASS

# 레이턴시 기준 (ms)
LATENCY_OK_MS     = 15_000
