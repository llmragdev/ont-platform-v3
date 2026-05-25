# Phase 4 Week 2-3 Claude (API 고도화) 작업 지시서

**기간**: 2026-06-08 ~ 2026-06-21 (2주)  
**담당**: Claude Agent (API Enhancement)  
**목표**: 재순위화 + 쿼리 확장 + 고급 필터링 구현  
**예상시간**: 40~50시간

---

## 🎯 Week 2-3 Claude 임무

API 기능을 프로덕션 수준으로 고도화:
1. **검색 결과 재순위화** — 관련성 재계산 (Week 2)
2. **쿼리 확장** — 동의어/유사어 자동 확장 (Week 2)
3. **고급 필터링** — 멀티 조건 필터 (Week 2-3 초반)
4. **배치 API** — 다중 쿼리 한 번에 처리 (Week 3)

---

## 📋 Task 분해

### Week 2 (Day 1-5): 재순위화 + 쿼리 확장 + 고급 필터링

#### Task 1: 검색 결과 재순위화 API (3~4시간)

**파일**: `app/api/reranking.py` (신규), `app/services/reranking_service.py` (신규)

**엔드포인트**:
```python
POST /api/v1/rag/rerank
    body: {
        query: str
        chunks: [{
            id: str
            content: str
            initial_score: float
        }],
        method: str = "relevance"  # relevance, bm25, ml
    }
    
    returns: {
        reranked_chunks: [{
            id, content, initial_score, reranked_score
        }],
        ranking_method: str
    }
```

**구현 요구사항**:
- ✅ 3가지 재순위화 방식 지원:
  - `relevance`: 쿼리-청크 코사인 유사도 재계산
  - `bm25`: BM25 스코어 계산 (전통적 정보 검색)
  - `ml`: 간단한 ML 모델 (선택사항)
- ✅ 초기 점수 + 재순위화 점수 모두 반환
- ✅ 상위 5개 청크만 재순위화 (성능)
- ✅ 테스트 5개

**테스트**:
```python
def test_rerank_by_relevance(client):
    # 쿼리 유사도 기반 재순위화
    
def test_rerank_by_bm25(client):
    # BM25 스코어 계산
    
def test_rerank_preserves_top_results(client):
    # 상위 결과 순서 개선 확인
    
def test_rerank_empty_chunks(client):
    # 빈 청크 처리
    
def test_rerank_requires_query(client):
    # 필수 파라미터 검증
```

---

#### Task 2: 쿼리 확장 API (3~4시간)

**파일**: `app/services/query_expansion.py` (신규)

**엔드포인트**:
```python
POST /api/v1/rag/expand-query
    body: {
        query: str
        language: str = "ko"  # ko, en
        max_expansions: int = 5
    }
    
    returns: {
        original_query: str,
        expanded_queries: [
            {query: str, weight: float, type: str}
        ],
        total_weight: float
    }
```

**구현 요구사항**:
- ✅ 3가지 확장 전략:
  - `synonym`: 동의어 확장
  - `decompose`: 질문 분해 (예: "회사 정책과 규정" → ["회사 정책", "규정"])
  - `generalize`: 일반화 (예: "Python" → ["프로그래밍", "개발"])
- ✅ 한글/영문 지원
- ✅ 가중치 기반 확장 (원본 = 1.0, 동의어 = 0.8 등)
- ✅ 테스트 5개

**테스트**:
```python
def test_expand_query_synonyms(client):
    # 동의어 확장 확인
    
def test_expand_query_decomposition(client):
    # 질문 분해 동작 확인
    
def test_expand_query_korean(client):
    # 한글 확장
    
def test_expand_query_english(client):
    # 영문 확장
    
def test_expand_preserves_original(client):
    # 원본 쿼리 항상 포함
```

---

#### Task 3: 고급 필터링 (다중 조건) (2~3시간)

**파일**: `app/api/search.py` (확장), `app/services/rag_service.py` (확장)

**엔드포인트** (기존 /search 확장):
```python
POST /api/v1/rag/search
    body: {
        query: str,
        filters: {  # 신규
            org_ids: [str] (또는, OR 조건)
            categories: {
                large: [str],
                mid: [str]
            }
            date_range: {
                from: str (ISO8601),
                to: str (ISO8601)
            },
            doc_ids: [str]  # 특정 문서만
        },
        limit: int = 10,
        offset: int = 0
    }
```

**구현 요구사항**:
- ✅ AND 조건으로 여러 필터 조합
- ✅ org_ids만 OR 조건 (계층적 접근)
- ✅ 날짜 범위 필터 (metadata에 created_at 저장)
- ✅ 카테고리 필터 (category_large, category_mid)
- ✅ 테스트 6개

**테스트**:
```python
def test_search_with_category_filter(client):
    # 카테고리 필터링
    
def test_search_with_org_filter(client):
    # org_id 필터링 (OR 조건)
    
def test_search_with_date_range(client):
    # 날짜 범위 필터
    
def test_search_combined_filters(client):
    # 다중 필터 조합
    
def test_search_no_results_with_strict_filter(client):
    # 필터로 인해 결과 없음
    
def test_search_filter_optimization(client):
    # 필터 적용 후 응답시간 (< 100ms)
```

---

### Week 3 (Day 1-5): 배치 API + API 문서 완성

#### Task 4: 배치 API (Bulk Search) (3~4시간)

**파일**: `app/api/search.py` (신규 엔드포인트)

**엔드포인트**:
```python
POST /api/v1/rag/batch-search
    body: {
        queries: [{
            query: str,
            filters: {...}  # 선택
        }],
        method: str = "parallel"  # parallel, sequential
    }
    
    returns: {
        results: [{
            query: str,
            chunks: [...],
            elapsed_ms: float
        }],
        total_queries: int,
        total_elapsed_ms: float,
        avg_time_per_query: float
    }
```

**구현 요구사항**:
- ✅ 최소 2개 ~ 최대 100개 쿼리 지원
- ✅ Parallel 모드: concurrent.futures.ThreadPoolExecutor
- ✅ Sequential 모드: 순차 처리 (테스트용)
- ✅ 개별 쿼리 응답시간 측정
- ✅ 효율성 50% 향상 검증 (10개 쿼리 기준)
- ✅ 테스트 5개

**테스트**:
```python
def test_batch_search_10_queries(client):
    # 10개 쿼리 배치 처리
    
def test_batch_search_parallel_vs_sequential(client):
    # Parallel이 Sequential보다 빠름
    
def test_batch_search_mixed_filters(client):
    # 쿼리별 다른 필터
    
def test_batch_search_limits(client):
    # 최대 쿼리 수 검증
    
def test_batch_search_error_handling(client):
    # 일부 쿼리 실패 시 처리
```

---

#### Task 5: API 문서 완성 (2시간)

**파일**: `docs/API_v4_DESIGN.md` (신규), OpenAPI 주석 추가

**내용**:
- ✅ OpenAPI 3.0 스펙 (Swagger UI 자동 생성)
- ✅ 모든 엔드포인트 상세 설명:
  - /rag/search (기존)
  - /rag/rerank (신규)
  - /rag/expand-query (신규)
  - /rag/batch-search (신규)
  - /documents/* (기존)
- ✅ 요청/응답 예시
- ✅ 에러 코드 정의
- ✅ 성능 기준 (응답시간 SLA)

---

## 🔧 구현 가이드

### 재순위화 예제
```python
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

def rerank_by_relevance(query: str, chunks: list[str], top_k=5):
    model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
    query_emb = model.encode(query)
    chunk_embs = model.encode(chunks)
    
    scores = cosine_similarity([query_emb], chunk_embs)[0]
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
    return ranked
```

### 쿼리 확장 예제
```python
SYNONYMS_KO = {
    "회사": ["조직", "기업"],
    "규정": ["규칙", "정책"],
    "임직원": ["직원", "사원"]
}

def expand_query(query: str, language: str = "ko"):
    synonyms_dict = SYNONYMS_KO if language == "ko" else SYNONYMS_EN
    expanded = [query]  # 원본 포함
    
    for word, syns in synonyms_dict.items():
        if word in query:
            expanded.extend([query.replace(word, s) for s in syns])
    
    return expanded[:5]  # 최대 5개
```

---

## 📊 완료 기준

```
✅ Task 1: 재순위화 API
  - POST /api/v1/rag/rerank 구현
  - 3가지 방식 (relevance, bm25, ml) 지원
  - 5개 테스트 통과

✅ Task 2: 쿼리 확장 API
  - POST /api/v1/rag/expand-query 구현
  - 3가지 전략 지원
  - 5개 테스트 통과

✅ Task 3: 고급 필터링
  - POST /api/v1/rag/search 확장
  - 다중 필터 조합 지원
  - 6개 테스트 통과

✅ Task 4: 배치 API
  - POST /api/v1/rag/batch-search 구현
  - Parallel/Sequential 모드
  - 5개 테스트 통과

✅ Task 5: API 문서
  - OpenAPI 3.0 스펙 완성
  - Swagger UI 정상 동작

✅ 전체: 21개 테스트 통과
✅ 응답시간: 각 API < 200ms (p99)
```

---

## 📁 디렉토리 구조

```
src_claud/v4/app/
├── api/
│   ├── search.py          ← 고급 필터링, 배치 API 추가
│   └── reranking.py       ← 신규 (재순위화 엔드포인트)
├── services/
│   ├── rag_service.py     ← 필터링 로직 추가
│   ├── reranking_service.py    ← 신규
│   └── query_expansion.py      ← 신규
└── main.py                ← OpenAPI 주석 추가

docs/
├── API_v4_DESIGN.md       ← 신규 (OpenAPI 스펙)
```

---

## 🚀 실행 순서

1. **Task 1: 재순위화** (3~4시간) → 테스트
2. **Task 2: 쿼리 확장** (3~4시간) → 테스트
3. **Task 3: 고급 필터링** (2~3시간) → 테스트
4. **Task 4: 배치 API** (3~4시간) → 테스트
5. **Task 5: API 문서** (2시간)

---

**예상 완료**: 2026-06-21  
**최종 검증**: 모든 API 정상 작동 + 21개 테스트 통과  
**다음**: Antigravity/Codex와 통합

