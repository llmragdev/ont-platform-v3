# Phase 4 Week 6: Performance Optimization
## Antigravity (Performance) 수행 지시서

**기간**: 2026-07-01 ~ 2026-07-05 (5일)  
**할당**: 80% (주당 24-30시간)  
**목표**: 고급 성능 최적화, 대규모 데이터 처리, 분산 캐싱 아키텍처

---

## Task 6-1: Redis 캐싱 전략 고도화

**기간**: 07-01 ~ 07-02 (1.5일)

### 목표
멀티레벨 캐싱으로 응답시간 70% 감소

### 구현 항목

#### 1) 계층적 캐싱 아키텍처
```python
from redis import Redis
from functools import wraps
import hashlib
import json
from typing import Any, Callable

class MultiLevelCache:
    """L1: 메모리 (로컬) → L2: Redis (공유) → L3: DB"""
    
    def __init__(self, redis_url: str):
        self.redis = Redis.from_url(redis_url)
        self.memory_cache = {}
        self.memory_limit = 1000  # 항목 수
    
    def get(self, key: str) -> Any:
        """캐시 조회 (L1 → L2 → None)"""
        # L1: 로컬 메모리
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # L2: Redis
        redis_value = self.redis.get(key)
        if redis_value:
            value = json.loads(redis_value)
            # L1에 복사
            self._add_to_memory_cache(key, value)
            return value
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """캐시 저장 (L1 + L2)"""
        # L1: 메모리
        self._add_to_memory_cache(key, value)
        
        # L2: Redis (TTL 적용)
        self.redis.setex(
            key,
            ttl,
            json.dumps(value)
        )
    
    def _add_to_memory_cache(self, key: str, value: Any):
        """메모리 캐시에 추가 (LRU)"""
        if len(self.memory_cache) >= self.memory_limit:
            # 가장 오래된 항목 제거 (간단한 FIFO)
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]
        
        self.memory_cache[key] = value

# 데코레이터
def cached(cache: MultiLevelCache, ttl: int = 300):
    """함수 결과 캐싱"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{func.__name__}:{hashlib.md5(str((args, kwargs)).encode()).hexdigest()}"
            
            # 캐시 조회
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 캐시 미스: 함수 실행
            result = await func(*args, **kwargs)
            
            # 캐시 저장
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

# 사용 예
cache = MultiLevelCache('redis://localhost:6379')

@cached(cache, ttl=300)
async def get_sparql_results(query: str):
    return execute_sparql_query(query)
```

#### 2) 캐시 무효화 전략
```python
class CacheInvalidationStrategy:
    """스마트 캐시 무효화"""
    
    def __init__(self, redis: Redis):
        self.redis = redis
    
    def invalidate_by_pattern(self, pattern: str):
        """패턴 기반 무효화"""
        # SPARQL:* → 모든 SPARQL 쿼리 캐시 무효화
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)
    
    def invalidate_on_entity_update(self, entity_id: str):
        """엔티티 업데이트 시 관련 캐시 무효화"""
        # 1. 해당 엔티티의 RDF 캐시 제거
        self.redis.delete(f"rdf:{entity_id}:*")
        
        # 2. 해당 엔티티를 포함한 SPARQL 결과 제거
        # (정확한 추적이 어려우므로 광범위 무효화)
        self.redis.delete(f"sparql:*{entity_id}*")
    
    def invalidate_ttl_based(self, key: str, ttl: int):
        """TTL 기반 무효화"""
        self.redis.expire(key, ttl)
    
    def warm_cache(self, queries: List[str]):
        """자주 사용되는 쿼리 사전 로드"""
        for query in queries:
            # 쿼리 미리 실행 및 캐시
            result = execute_sparql_query(query)
            cache_key = f"sparql:{hashlib.md5(query.encode()).hexdigest()}"
            self.redis.setex(cache_key, 3600, json.dumps(result))
```

### 캐싱 목표
- [ ] L1 히트율: ≥ 90%
- [ ] L2 히트율: ≥ 85%
- [ ] 전체 응답시간: 70% 감소
- [ ] 메모리 사용: < 500MB

---

## Task 6-2: 대규모 RDF 처리 최적화

**기간**: 07-02 ~ 07-04 (2일)

### 목표
1M+ 트리플 처리 시간 50% 단축

### 구현 항목

#### 1) 스트리밍 RDF 로드
```python
from rdflib import Graph
import asyncio
from typing import AsyncIterator

class StreamingRDFLoader:
    """스트리밍 방식의 RDF 로드"""
    
    async def load_large_rdf_file(self, 
                                 file_path: str,
                                 batch_size: int = 1000) -> AsyncIterator[Graph]:
        """대용량 RDF 파일 배치 단위 로드"""
        graph = Graph()
        triple_count = 0
        
        with open(file_path, 'r') as f:
            for line in f:
                # N-Triples 형식: <s> <p> <o> .
                if line.strip() and line.strip().endswith('.'):
                    triple = self._parse_ntriple(line)
                    graph.add(triple)
                    triple_count += 1
                    
                    # 배치 크기 도달 시 yield
                    if triple_count >= batch_size:
                        yield graph
                        graph = Graph()
                        triple_count = 0
                        
                        # 메인 스레드 블로킹 방지
                        await asyncio.sleep(0)
        
        # 남은 트리플 yield
        if triple_count > 0:
            yield graph
    
    def _parse_ntriple(self, line: str) -> tuple:
        """N-Triple 파싱"""
        # <http://example.org/s> <http://example.org/p> <http://example.org/o> .
        parts = line.strip()[:-1].split(' ', 2)  # 마지막 '.' 제거
        return tuple(parts)

# 사용 예
loader = StreamingRDFLoader()

async def process_large_file():
    graphs = []
    async for batch_graph in loader.load_large_rdf_file('large.nt'):
        # 배치별 처리
        optimized_graph = optimize_graph(batch_graph)
        graphs.append(optimized_graph)
    
    # 모든 배치 병합
    merged = merge_graphs(graphs)
```

#### 2) 병렬 그래프 처리
```python
from concurrent.futures import ProcessPoolExecutor, as_completed

class ParallelGraphProcessor:
    """멀티프로세싱 기반 병렬 그래프 처리"""
    
    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
    
    def process_graphs_parallel(self, graphs: List[Graph]) -> List[Graph]:
        """병렬 그래프 처리"""
        results = []
        
        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            # 각 그래프를 별도 프로세스에서 처리
            future_to_graph = {
                executor.submit(self._process_single_graph, g): g
                for g in graphs
            }
            
            for future in as_completed(future_to_graph):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"Error processing graph: {e}")
        
        return results
    
    @staticmethod
    def _process_single_graph(graph: Graph) -> Graph:
        """단일 그래프 처리 (프로세스 내에서 실행)"""
        # 무거운 연산 수행
        # - SPARQL 쿼리
        # - 그래프 최적화
        # - 인덱싱
        
        # 프로세스 간 통신 오버헤드 최소화를 위해
        # 결과만 반환
        return optimize_and_index_graph(graph)
```

#### 3) 메모리 효율 최적화
```python
class MemoryEfficientRDFProcessor:
    """메모리 효율적인 RDF 처리"""
    
    def process_with_generator(self, file_path: str):
        """생성자(Generator) 패턴으로 메모리 절약"""
        def triple_generator():
            with open(file_path, 'r') as f:
                for line in f:
                    if line.strip():
                        yield self._parse_ntriple(line)
        
        # 필요한 만큼만 메모리에 로드
        for triple in triple_generator():
            process_triple(triple)
    
    def merge_graphs_incrementally(self, graph_files: List[str]) -> Graph:
        """증분식 그래프 병합 (메모리 효율)"""
        merged = Graph()
        
        for file_path in graph_files:
            # 파일별로 로드
            batch_graph = Graph()
            batch_graph.parse(file_path, format='ntriples')
            
            # 병합 (중복 제거)
            for s, p, o in batch_graph:
                merged.add((s, p, o))
            
            # 배치 그래프 메모리 해제
            del batch_graph
    
    def get_memory_stats(self) -> Dict:
        """메모리 사용량 통계"""
        import tracemalloc
        
        tracemalloc.start()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        return {
            'current_mb': current / (1024 * 1024),
            'peak_mb': peak / (1024 * 1024)
        }
```

### 대규모 처리 목표
- [ ] 1M 트리플 로드: < 30초
- [ ] 병렬 처리: 4배 병렬화로 3배 속도 향상
- [ ] 메모리 사용: 트리플 수에 비례 (선형)
- [ ] 쿼리 응답: < 500ms (1M 트리플)

---

## Task 6-3: 성능 모니터링 & 분석

**기간**: 07-04 ~ 07-05 (1.5일)

### 1) 성능 메트릭 수집
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict
import time

@dataclass
class PerformanceMetric:
    """성능 메트릭"""
    name: str
    value: float  # ms
    timestamp: datetime
    tags: Dict[str, str] = None

class PerformanceCollector:
    """성능 데이터 수집"""
    
    def __init__(self, redis: Redis):
        self.redis = redis
        self.metrics = []
    
    def record_metric(self, 
                     name: str, 
                     value: float, 
                     tags: Dict[str, str] = None):
        """메트릭 기록"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {}
        )
        
        self.metrics.append(metric)
        
        # Redis에 저장 (시계열)
        key = f"metric:{name}:{datetime.utcnow().timestamp()}"
        self.redis.setex(key, 3600, json.dumps({
            'value': value,
            'tags': tags
        }))
    
    def get_statistics(self, metric_name: str) -> Dict:
        """메트릭 통계"""
        values = [m.value for m in self.metrics if m.name == metric_name]
        
        if not values:
            return {}
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'p95': sorted(values)[int(len(values) * 0.95)],
            'p99': sorted(values)[int(len(values) * 0.99)]
        }

# 사용 예
collector = PerformanceCollector(redis)

# 쿼리 성능 기록
start = time.time()
results = execute_sparql_query(query)
elapsed = (time.time() - start) * 1000

collector.record_metric(
    'sparql_query_time',
    elapsed,
    {'query_type': 'SELECT', 'result_count': len(results)}
)

# 통계 조회
stats = collector.get_statistics('sparql_query_time')
print(f"SPARQL Query Time - P95: {stats['p95']:.1f}ms, P99: {stats['p99']:.1f}ms")
```

### 2) 성능 대시보드
```python
# API 엔드포인트
from fastapi import APIRouter

router = APIRouter(prefix="/api/performance", tags=["performance"])

@router.get("/metrics/{metric_name}")
async def get_metric_stats(metric_name: str) -> Dict:
    """메트릭 통계 조회"""
    return collector.get_statistics(metric_name)

@router.get("/dashboard")
async def get_performance_dashboard() -> Dict:
    """전체 성능 대시보드"""
    return {
        'sparql_query': collector.get_statistics('sparql_query_time'),
        'rdf_load': collector.get_statistics('rdf_load_time'),
        'graph_merge': collector.get_statistics('graph_merge_time'),
        'cache_hit_rate': cache.get_hit_rate(),
        'db_query': collector.get_statistics('db_query_time'),
        'api_response': collector.get_statistics('api_response_time')
    }
```

### 3) Prometheus/Grafana 통합
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ontology-platform'
    static_configs:
      - targets: ['localhost:8002']
    metrics_path: '/metrics'

# 메트릭 노출
from prometheus_client import Counter, Histogram, generate_latest

sparql_query_duration = Histogram(
    'sparql_query_duration_seconds',
    'SPARQL query duration',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

@sparql_query_duration.time()
def execute_sparql_query(query: str):
    # SPARQL 실행
    pass

# /metrics 엔드포인트
@app.get("/metrics")
async def metrics():
    return generate_latest()
```

### 성능 모니터링 목표
- [ ] 모든 주요 작업 메트릭 수집 (10+)
- [ ] 실시간 대시보드 (Grafana)
- [ ] P95/P99 추적
- [ ] 성능 이상 자동 감지

---

## 🎯 성공 기준

- [x] 캐싱: 70% 응답시간 감소
- [x] 대규모 처리: 1M 트리플 < 30초
- [x] 병렬 처리: 3배 속도 향상
- [x] 모니터링: 10+ 메트릭 수집
- [x] 대시보드: Grafana 실시간 추적

---

**⚠️ 반드시 따르기**:

1. **저장 위치** (필수)
   - ✅ 정해진 위치: `task_logs/antigravity/YYYYMMDD_PHASE4_WEEK6_Antigravity_Complete.md`
   - 예: `20260705_1830_PHASE4_WEEK6_Antigravity_Complete.md`
   - ❌ 금지: `ont_platform/` 폴더에 저장하지 말 것

---

**상태**: Task 6-1~6-3 준비 완료  
**예상 완료**: 2026-07-05 (토요일)  
**다음 주차**: Week 7 Advanced UI & Visualization

---

## 📋 보고서 저장 지시

**저장 경로**: `task_logs/antigravity/YYYYMMDD_HHMM_PHASE4_WEEK6_Antigravity_Complete.md`

**예시**: `20260705_1830_PHASE4_WEEK6_Antigravity_Complete.md`

**완료 후**: Claude가 3개 보고서를 취합하여 통합 보고서를 작성합니다.
(`task_logs/consolidated/YYYYMMDD_HHMM_PHASE4_WEEK6_Consolidated_Report.md`)
