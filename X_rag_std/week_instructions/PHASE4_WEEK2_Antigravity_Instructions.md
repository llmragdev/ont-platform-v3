# Phase 4 Week 2-3 Antigravity (성능 최적화) 작업 지시서

**기간**: 2026-06-08 ~ 2026-06-21 (2주)  
**담당**: Antigravity Agent (Performance Optimization)  
**목표**: 청킹 품질 완성 + 벡터DB 캐싱 + 부하 테스트  
**예상시간**: 40~50시간

---

## 🎯 Week 2-3 Antigravity 임무

성능 SLA 달성 (p99 < 200ms, 1000 QPS):
1. **청킹 품질 완성** — 500자+ 보장 (Week 2)
2. **벡터DB 캐싱** — 70%+ hit rate (Week 2-3 초반)
3. **임베딩 캐시 최적화** — 메모리 효율 (Week 3)
4. **부하 테스트** — 1000 QPS 검증 (Week 3)

---

## 📋 Task 분해

### Week 2 (Day 1-5): 청킹 품질 + 캐싱 전략

#### Task 1: PDF 추출 개선 (extractor.py) (2~3시간)

**파일**: `app/services/pipeline/extractor.py`

**목표**: PDF 줄바꿈 정제로 청크 품질 향상

**구현**:
```python
def normalize_text(text: str) -> str:
    """
    PDF 추출 후 텍스트 정규화
    - 단일 \n → 스페이스 (의미 보존)
    - 문단 \n\n → 유지 (문단 구조 보존)
    - 다중 공백 → 단일 공백
    """
    # 문단 구분자 임시 치환
    text = text.replace('\n\n', '\x00PARA\x00')
    
    # 단일 줄바꿈을 스페이스로
    text = text.replace('\n', ' ')
    
    # 문단 구분자 복원
    text = text.replace('\x00PARA\x00', '\n\n')
    
    # 다중 공백 정규화
    text = ' '.join(text.split())
    
    return text

# extractor.py의 extract_pdf_text() 수정
def extract_pdf_text(pdf_path: str) -> str:
    # 기존 PDF 추출 코드
    text = existing_extraction_logic(pdf_path)
    
    # 새로운 정규화
    text = normalize_text(text)
    
    return text
```

**검증**:
- ✅ 테스트 PDF로 정규화 확인
- ✅ 평균 줄바꿈 수 감소 (측정)
- ✅ 의미 손실 없음 (육안 확인)

---

#### Task 2: SemanticChunker 최소 크기 필터 (2~3시간)

**파일**: `app/services/pipeline/chunker.py`

**목표**: 너무 작은 청크 제거

**구현**:
```python
MIN_CHUNK_SIZE = 150  # 최소 150자
MAX_CHUNK_SIZE = 1000  # 최대 1000자 (기존)

class SemanticChunker:
    def chunk(self, text: str) -> list[str]:
        # 기존 semantic chunking 로직
        initial_chunks = self.semantic_split(text)
        
        # 작은 청크 필터링 + 병합
        filtered_chunks = []
        buffer = ""
        
        for chunk in initial_chunks:
            if len(chunk) >= MIN_CHUNK_SIZE:
                if buffer:
                    filtered_chunks.append(buffer)
                    buffer = ""
                filtered_chunks.append(chunk)
            else:
                # 작은 청크는 다음 청크와 병합
                buffer += " " + chunk
        
        # 남은 버퍼 처리
        if buffer and len(buffer) >= MIN_CHUNK_SIZE:
            filtered_chunks.append(buffer)
        
        return [c for c in filtered_chunks if MIN_CHUNK_SIZE <= len(c) <= MAX_CHUNK_SIZE]
```

**검증**:
- ✅ 모든 청크 >= 150자 확인
- ✅ 청크 수 감소 (예: 100개 → 40개)
- ✅ 의미 연결성 유지 (육안 확인)

---

#### Task 3: 벡터DB 쿼리 캐싱 (2~3시간)

**파일**: `app/core/cache.py` (신규), `app/services/rag_service.py` (수정)

**구현**:
```python
from functools import lru_cache
from datetime import datetime, timedelta
import hashlib

class VectorDBCache:
    def __init__(self, ttl_seconds=3600):  # 1시간 TTL
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get_cache_key(self, query: str, filters: dict = None) -> str:
        """쿼리 + 필터 기반 캐시 키 생성"""
        key_str = f"{query}:{str(filters)}"
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> dict | None:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                return value
            else:
                del self.cache[key]  # TTL 만료
        return None
    
    def set(self, key: str, value: dict) -> None:
        self.cache[key] = (value, datetime.now())
    
    def clear(self) -> None:
        self.cache.clear()
    
    def stats(self) -> dict:
        return {
            "cache_size": len(self.cache),
            "ttl_seconds": self.ttl
        }

# rag_service.py에서 사용
class RAGService:
    def __init__(self):
        self.cache = VectorDBCache(ttl_seconds=3600)  # 1시간
    
    def search(self, query: str, filters: dict = None) -> dict:
        cache_key = self.cache.get_cache_key(query, filters)
        
        # 캐시 확인
        cached = self.cache.get(cache_key)
        if cached:
            return {**cached, "from_cache": True}
        
        # 벡터DB 검색 (캐시 미스)
        results = self._search_vector_db(query, filters)
        
        # 캐시에 저장
        self.cache.set(cache_key, results)
        
        return {**results, "from_cache": False}
```

**검증**:
- ✅ 캐시 hit rate 70%+ 확인
- ✅ 캐시 hits는 100ms 이내 응답
- ✅ 캐시 miss는 200ms 이내

---

#### Task 4: 성능 측정 기준선 (baseline_v3.py) (2~3시간)

**파일**: `tests/load/baseline_v3.py` (신규)

**목표**: v3 현재 성능 측정 (개선 전/후 비교용)

**내용**:
```python
import time
import requests
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:8000/api/v1"

def measure_search_latency():
    """검색 응답시간 측정"""
    queries = [
        "온톨로지",
        "자연언어처리",
        "knowledge graph",
        "신입사원",
        "급여 규정"
    ]
    
    latencies = []
    for query in queries:
        start = time.time()
        resp = requests.post(
            f"{BASE_URL}/rag/search",
            headers={"X-Tenant-ID": "company_abc"},
            json={"query": query}
        )
        latency = (time.time() - start) * 1000  # ms
        latencies.append(latency)
    
    return {
        "avg": sum(latencies) / len(latencies),
        "p50": sorted(latencies)[len(latencies)//2],
        "p99": sorted(latencies)[int(len(latencies)*0.99)]
    }

def measure_throughput():
    """처리량 측정 (동시 쿼리)"""
    query = "온톨로지"
    num_concurrent = 100
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(
                requests.post,
                f"{BASE_URL}/rag/search",
                headers={"X-Tenant-ID": "company_abc"},
                json={"query": query}
            )
            for _ in range(num_concurrent)
        ]
        results = [f.result() for f in futures]
    
    elapsed = time.time() - start
    qps = num_concurrent / elapsed
    
    return {
        "total_queries": num_concurrent,
        "elapsed_seconds": elapsed,
        "qps": qps
    }

# 결과 예시:
# v3 baseline (현재):
#   latency: {avg: 180ms, p50: 150ms, p99: 250ms}
#   throughput: 550 QPS
#
# v4 target:
#   latency: {avg: 100ms, p50: 80ms, p99: <200ms}
#   throughput: 1000 QPS
```

**검증**:
- ✅ v3 현재 성능 기록
- ✅ 개선 전/후 비교용 기준선 확정

---

### Week 3 (Day 1-5): 부하 테스트 + 임베딩 캐시

#### Task 5: 임베딩 캐시 최적화 (3~4시간)

**파일**: `app/core/embedding_cache.py` (신규), `app/services/embedding/` (수정)

**목표**: 자주 사용되는 임베딩 캐싱 (메모리 + 디스크)

**구현**:
```python
import hashlib
import json
from pathlib import Path
import numpy as np

class EmbeddingCache:
    def __init__(self, cache_dir: str = "./storage/embedding_cache", max_memory_items: int = 10000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 인메모리 캐시 (자주 사용되는 것)
        self.memory_cache = {}
        self.max_memory_items = max_memory_items
    
    def get_key(self, text: str) -> str:
        """SHA256 기반 캐시 키"""
        return hashlib.sha256(text.encode()).hexdigest()
    
    def get(self, text: str) -> np.ndarray | None:
        key = self.get_key(text)
        
        # 메모리 캐시 확인
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # 디스크 캐시 확인
        disk_path = self.cache_dir / f"{key}.npy"
        if disk_path.exists():
            embedding = np.load(disk_path)
            # 디스크에서 읽은 것을 메모리로 로드 (LRU)
            if len(self.memory_cache) < self.max_memory_items:
                self.memory_cache[key] = embedding
            return embedding
        
        return None
    
    def set(self, text: str, embedding: np.ndarray) -> None:
        key = self.get_key(text)
        
        # 메모리 캐시
        self.memory_cache[key] = embedding
        
        # 디스크 캐시
        disk_path = self.cache_dir / f"{key}.npy"
        np.save(disk_path, embedding)
    
    def stats(self) -> dict:
        disk_items = len(list(self.cache_dir.glob("*.npy")))
        memory_items = len(self.memory_cache)
        memory_size_mb = sum(
            v.nbytes for v in self.memory_cache.values()
        ) / (1024*1024)
        
        return {
            "memory_items": memory_items,
            "disk_items": disk_items,
            "memory_size_mb": round(memory_size_mb, 2)
        }

# 사용 예시
class GeminiEmbedding:
    def __init__(self):
        self.cache = EmbeddingCache()
    
    def embed(self, text: str) -> np.ndarray:
        # 캐시 확인
        cached = self.cache.get(text)
        if cached is not None:
            return cached
        
        # Gemini API 호출
        embedding = self._call_gemini_api(text)
        
        # 캐시에 저장
        self.cache.set(text, embedding)
        
        return embedding
```

**검증**:
- ✅ 메모리 사용량 < 10GB
- ✅ 디스크 사용량 측정
- ✅ 캐시 hit rate 50%+ (반복되는 텍스트)

---

#### Task 6: 부하 테스트 (load test) (4~5시간)

**파일**: `tests/load/load_test_search.py` (신규)

**목표**: 1000 QPS 달성 검증

**구현**:
```python
import time
from locust import HttpUser, task, between
from locust.stats import StatsEntry

class RAGUser(HttpUser):
    wait_time = between(0.1, 0.5)  # 100ms~500ms 간격
    
    @task
    def search(self):
        queries = [
            "온톨로지", "자연언어처리", "knowledge graph",
            "신입사원", "급여 규정", "취업규칙"
        ]
        import random
        query = random.choice(queries)
        
        self.client.post(
            "/api/v1/rag/search",
            headers={"X-Tenant-ID": "company_abc"},
            json={
                "query": query,
                "limit": 5
            }
        )

# 실행: locust -f load_test_search.py -u 1000 -r 50 --headless
# 결과: 1000 concurrent users, 50 user/sec spawn rate
#       목표: 1000 QPS, p99 <200ms
```

**성능 목표**:
- ✅ 1000 concurrent users 처리
- ✅ Throughput: 1000 QPS
- ✅ Latency p99: < 200ms
- ✅ 에러율: < 1%

---

## 📊 완료 기준

```
✅ Task 1: PDF 추출 개선
  - extractor.py normalize_text() 추가
  - 테스트 통과
  - 평균 줄바꿈 감소 확인

✅ Task 2: 청크 최소 크기 필터
  - chunker.py MIN_CHUNK_SIZE 필터 추가
  - 모든 청크 >= 150자 확인
  - 테스트 통과

✅ Task 3: 벡터DB 캐싱
  - VectorDBCache 구현
  - 캐시 hit rate 70%+
  - 테스트 통과

✅ Task 4: 성능 기준선
  - baseline_v3.py 완성
  - v3 현재 성능 기록
  - 개선 전/후 비교 가능

✅ Task 5: 임베딩 캐시
  - EmbeddingCache 구현 (메모리 + 디스크)
  - 메모리 사용 < 10GB
  - 테스트 통과

✅ Task 6: 부하 테스트
  - locust 기반 부하 테스트
  - 1000 QPS 달성
  - p99 <200ms 달성
  - 에러율 <1%

✅ 전체 성능 SLA 달성
  - 응답시간: p99 <200ms
  - 처리량: 1000 QPS
  - 캐시 hit: 70%+
```

---

## 📁 디렉토리 구조

```
src_claud/v4/
├── app/
│   ├── core/
│   │   ├── cache.py              ← 신규 (VectorDBCache)
│   │   └── embedding_cache.py    ← 신규
│   ├── services/
│   │   ├── pipeline/
│   │   │   ├── extractor.py      ← 수정 (normalize_text)
│   │   │   └── chunker.py        ← 수정 (MIN_CHUNK_SIZE)
│   │   ├── embedding/
│   │   │   └── *.py              ← 수정 (캐시 통합)
│   │   └── rag_service.py        ← 수정 (캐시 적용)
├── tests/
│   ├── load/
│   │   ├── baseline_v3.py        ← 신규
│   │   ├── load_test_search.py   ← 신규
│   │   └── load_test_upload.py   ← 신규 (선택)
└── docs/
    └── PERFORMANCE_REPORT.md     ← 신규
```

---

## 🚀 실행 순서

1. **Task 1: PDF 추출 개선** (2~3시간)
2. **Task 2: 청크 필터링** (2~3시간)
3. **Task 3: 벡터DB 캐싱** (2~3시간)
4. **Task 4: 성능 기준선** (2~3시간)
5. **Task 5: 임베딩 캐시** (3~4시간)
6. **Task 6: 부하 테스트** (4~5시간)

---

**예상 완료**: 2026-06-21  
**최종 검증**: 1000 QPS + p99 <200ms + 캐시 70%+  
**다음**: Codex와 통합

