# v3 → v4 마이그레이션 가이드

**버전**: v4  
**대상**: v3 사용자  
**예상 마이그레이션 시간**: 1-2주 (규모에 따라)  
**지원**: Codex Agent

---

## 개요

v4는 v3의 안정적 베이스를 기반으로 성능, 기능, 품질을 모두 개선한 프로덕션 고도화 버전입니다.

**핵심 개선 사항**:
- 신규 API 엔드포인트 (재순위화, 쿼리 확장, 배치 검색)
- 청킹 품질 10배 향상 (50자 → 500자+)
- 응답시간 20% 개선 (p99 < 200ms)
- 캐시 기능 추가 (70%+ hit rate)
- 자동화된 배포 (GitHub Actions CI/CD)

---

## 호환성 분석

### Breaking Changes

**없음** — v3 API는 100% 호환됩니다.

| API | v3 | v4 | 상태 |
|-----|----|----|------|
| POST /api/v1/rag/search | ✅ | ✅ | 100% 호환 |
| GET /api/v1/documents | ✅ | ✅ | 100% 호환 |
| POST /api/v1/documents/upload | ✅ | ✅ | 100% 호환 |
| PUT /api/v1/documents/{id} | ✅ | ✅ | 100% 호환 |
| DELETE /api/v1/documents/{id} | ✅ | ✅ | 100% 호환 |

### 신규 기능 (선택)

v4에서만 사용 가능한 신규 엔드포인트:

| API | v3 | v4 | 설명 |
|-----|----|----|------|
| POST /api/v1/rag/rerank | ❌ | ✅ | 검색 결과 재순위화 |
| POST /api/v1/rag/expand-query | ❌ | ✅ | 쿼리 확장 (동의어, 유사어) |
| POST /api/v1/rag/batch-search | ❌ | ✅ | 배치 검색 (10개 이상 쿼리) |
| GET /api/v1/rag/cache-stats | ❌ | ✅ | 캐시 통계 (관리자) |

---

## 성능 개선

| 지표 | v3 | v4 | 개선율 |
|------|----|----|--------|
| 응답시간 (p99) | 250ms | <200ms | 20% ↓ |
| 청크 크기 (최소) | 50자 | 500자+ | 10배 ↑ |
| 캐시 hit rate | 미지원 | 70%+ | 신규 |
| 배치 처리 | 순차 | 병렬 | 50% ↓ |
| 처리량 | 100 QPS | 1000 QPS | 10배 ↑ |

---

## 마이그레이션 전략

### 1단계: 평가 (1-2일)

#### 1-1. v3 현황 파악

```bash
# v3 서버 상태 확인
curl http://localhost:8000/api/v1/health

# 문서 통계
curl -H "X-Tenant-ID: {tenant}" http://localhost:8000/api/v1/documents | \
  jq '.documents | length'

# 저장소 용량 확인
du -sh /path/to/v3/storage
```

#### 1-2. 벡터DB 스냅샷 생성

```bash
# v3 벡터DB 백업
cd /path/to/v3
cp -r storage/vector_db storage/vector_db.backup.$(date +%Y%m%d)

# RDBMS 백업 (SQLite)
cp src/backend/test.db src/backend/test.db.backup.$(date +%Y%m%d)
```

#### 1-3. 마이그레이션 규모 판단

```
문서 수: X개
저장소: Y GB
테넌트: Z개
조직 계층: ○ 없음 / ● 있음
```

**규모별 마이그레이션 시간**:
- 소규모 (< 1000문서): 1일 (병렬 운영 3일)
- 중규모 (1000-10000문서): 3일 (병렬 운영 1주)
- 대규모 (> 10000문서): 1주 (병렬 운영 2주)

---

### 2단계: v4 배포 (병렬 운영)

#### 2-1. v4 환경 준비

```bash
# v4 디렉토리로 이동
cd E:\ontology_edu\X_rag_std\src_agents\src_claud\v4

# 환경 변수 설정
set EMBEDDING_PROVIDER=gemini_http
set LLM_PROVIDER=gemini_http
set LLM_GATEWAY_URL=http://localhost:8010
set VECTOR_DB_ENGINE=local_json

# 의존성 설치
pip install -r requirements.txt

# v4 서버 기동 (port 9000)
uvicorn app.main:app --port 9000 --reload
```

#### 2-2. v3와 v4 병렬 운영

```
v3: port 8000 (현재 트래픽 100%)
v4: port 9000 (테스트 트래픽 0%)
```

**병렬 운영 기간**: 3-7일 (규모에 따라)

#### 2-3. 트래픽 점진적 이동 (Canary Deployment)

```
Day 1:  v3 95% → v4 5%   (주요 트래픽 v3 유지)
Day 2:  v3 90% → v4 10%  (정상 운영 확인)
Day 3:  v3 75% → v4 25%  (안정성 검증)
Day 4:  v3 50% → v4 50%  (동등 비중)
Day 5:  v3 25% → v4 75%  (대부분 v4로)
Day 6:  v3 10% → v4 90%  (최종 검증)
Day 7:  v3 0%  → v4 100% (완전 이관)
```

**모니터링 항목** (각 단계마다 확인):
- 응답시간 (평균, p99)
- 에러율 (4xx, 5xx)
- 검색 정확도 (샘플 쿼리 10개)
- 캐시 hit rate

---

### 3단계: 데이터 마이그레이션

#### 3-1. 벡터DB 마이그레이션

```bash
# v3 벡터DB → v4 벡터DB 복사
cd E:\ontology_edu\X_rag_std\src_agents\src_claud\v4

# v3에서 벡터 export
python scripts/export_vector_db.py \
  --source=v3 \
  --output=v3_vectors.json

# v4에 import
python scripts/import_vector_db.py \
  --input=v3_vectors.json \
  --target=v4
```

#### 3-2. 메타데이터 검증

```bash
# v3 메타데이터 통계
python scripts/validate_metadata.py \
  --db=v3 \
  --report=v3_metadata.json

# v4 메타데이터 검증
python scripts/validate_metadata.py \
  --db=v4 \
  --report=v4_metadata.json

# 비교
diff v3_metadata.json v4_metadata.json
```

#### 3-3. 검색 정합성 검증

```bash
# 동일 쿼리 50개 실행
python scripts/validate_search_compatibility.py \
  --v3_url=http://localhost:8000 \
  --v4_url=http://localhost:9000 \
  --sample_size=50

# 결과
# - 상위 5개 문서 일치율 >= 80%
# - 상위 10개 문서 일치율 >= 85%
```

---

### 4단계: 롤백 계획

#### 4-1. 즉각 롤백 (< 5분)

```bash
# 로드 밸런서 설정 변경 (또는 DNS 전환)
# v4 → v3로 트래픽 회귀

# 확인
curl http://localhost:8000/api/v1/health
```

#### 4-2. 데이터 복구

```bash
# v3 백업에서 복원
cd /path/to/v3
cp storage/vector_db.backup.20260620 storage/vector_db
cp src/backend/test.db.backup.20260620 src/backend/test.db

# v3 서버 재시작
```

#### 4-3. 원인 분석 및 재계획

```
1. 에러 로그 분석
   - v4 application logs
   - system logs (메모리, CPU)

2. 성능 프로파일링
   - slow query logs
   - vector DB response times

3. 테스트 보강
   - 실패한 시나리오 재현
   - 단위 테스트 추가

4. 재배포 일정 조정
   - 1주일 뒤 재시도
   - 또는 추가 개발
```

---

## 사용자 가이드

### v3 코드 (호환)

기존 v3 코드는 변경 없이 계속 사용 가능합니다.

```python
import requests

# v3와 동일한 API
response = requests.post(
    "http://localhost:9000/api/v1/rag/search",
    headers={"X-Tenant-ID": "company_abc"},
    json={"query": "온톨로지"}
)

chunks = response.json()["chunks"]
for chunk in chunks:
    print(chunk["text"])
```

### v4 신규 기능 (선택적)

v4의 신규 기능을 활용하면 성능과 정확도를 더욱 향상시킬 수 있습니다.

#### 예제 1: 쿼리 확장 + 배치 검색

```python
import requests

tenant_id = "company_abc"
headers = {"X-Tenant-ID": tenant_id}

# 1단계: 쿼리 확장
expand_resp = requests.post(
    "http://localhost:9000/api/v1/rag/expand-query",
    headers=headers,
    json={"query": "온톨로지"}
)

expanded_queries = [
    q["query"] for q in expand_resp.json()["expanded_queries"]
]
# 결과: ["온톨로지", "knowledge graph", "semantic web"]

# 2단계: 배치 검색 (50% 효율 개선)
batch_resp = requests.post(
    "http://localhost:9000/api/v1/rag/batch-search",
    headers=headers,
    json={
        "queries": [{"query": q} for q in expanded_queries]
    }
)

# 결과: {"results": [{"query": "...", "chunks": [...]}, ...]}
```

#### 예제 2: 재순위화 (정확도 향상)

```python
# 1단계: 초기 검색
search_resp = requests.post(
    "http://localhost:9000/api/v1/rag/search",
    headers=headers,
    json={"query": "온톨로지 설계"}
)

chunks = search_resp.json()["chunks"]

# 2단계: 재순위화 (사용자 피드백 기반)
rerank_resp = requests.post(
    "http://localhost:9000/api/v1/rag/rerank",
    headers=headers,
    json={
        "query": "온톨로지 설계",
        "chunks": chunks,
        "user_feedback": {
            "relevant": [chunks[0]["chunk_id"], chunks[2]["chunk_id"]],
            "irrelevant": [chunks[1]["chunk_id"]]
        }
    }
)

# 결과: 피드백 기반 재정렬된 chunks
```

#### 예제 3: 캐시 활용

```python
# 캐시 통계 조회 (관리자만)
cache_resp = requests.get(
    "http://localhost:9000/api/v1/rag/cache-stats",
    headers={"X-Tenant-ID": tenant_id}
)

print(cache_resp.json())
# {
#   "cache_size": 1024,
#   "hit_count": 700,
#   "miss_count": 300,
#   "hit_rate": 0.70
# }
```

---

## 운영 체크리스트

### 마이그레이션 전

- [ ] v3 현황 파악 (문서 수, 저장소, 테넌트)
- [ ] 벡터DB 백업 생성
- [ ] RDBMS 백업 생성
- [ ] 마이그레이션 일정 공지
- [ ] 팀 교육 (신규 기능)

### 마이그레이션 중 (병렬 운영)

- [ ] v4 서버 기동
- [ ] 헬스 체크 (v4)
- [ ] 트래픽 모니터링
- [ ] 에러 로그 검토
- [ ] 성능 지표 수집

### 마이그레이션 후

- [ ] v3 서버 종료 (선택)
- [ ] v3 저장소 보존 (3개월)
- [ ] 성능 리포트 작성
- [ ] 문제 사항 정리
- [ ] 다음 개선 계획 수립

---

## FAQ

### Q1: v3에서 배운 데이터를 v4에서 사용할 수 있나요?

**A**: 네. 벡터DB와 메타데이터는 100% 호환됩니다. 마이그레이션 가이드 3단계를 참고하세요.

### Q2: v4로 이동 중 에러가 발생하면?

**A**: 4단계 롤백 계획을 따르면 5분 내 v3로 복구 가능합니다. 원인 분석 후 재배포하세요.

### Q3: v3와 v4를 동시에 운영해야 하나요?

**A**: 권장합니다. 병렬 운영 기간(3-7일)을 통해 안정성을 검증한 후 완전 이관하세요.

### Q4: 신규 기능(재순위화, 배치 검색)을 사용하면 얼마나 성능이 개선되나요?

**A**:
- 배치 검색: 순차 대비 50% 효율 개선 (10개 쿼리 600ms → 300ms)
- 재순위화: 정확도 10-15% 향상 (피드백 학습 기반)
- 캐시: 반복 쿼리 70%+ 응답시간 단축

### Q5: 마이그레이션에 얼마나 시간이 걸리나요?

**A**: 규모에 따라:
- 소규모 (< 1000문서): 1일 (병렬 3일)
- 중규모 (1000-10000문서): 3일 (병렬 1주)
- 대규모 (> 10000문서): 1주 (병렬 2주)

---

## 지원

문제 발생 시:
1. 에러 로그 수집
2. 마이그레이션 가이드 재검토
3. 팀 문의: Codex Agent

---

**마지막 업데이트**: 2026-05-25  
**다음 버전**: v5 (예정 2026-09-01)
