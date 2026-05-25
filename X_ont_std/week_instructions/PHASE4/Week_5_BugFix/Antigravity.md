# Phase 4 Week 5: Bug Fix & Test Coverage
## Antigravity (Performance) 수행 지시서

**기간**: 2026-06-24 ~ 2026-06-28 (4일)  
**할당**: 80% (주당 24-30시간)  
**목표**: SPARQL 성능 최적화, RDF 그래프 메모리 효율화, 캐싱 전략 검증

---

## Task 5-1: SPARQL 쿼리 성능 분석 (목표: <200ms)

**기간**: 06-24 ~ 06-25 (1.5일)

### 성능 기준선 설정

```bash
# 성능 측정 환경
- 쿼리 데이터셋: 100K 트리플 (DBpedia 부분 수집)
- 메모리 제한: 1GB
- 타임아웃: 30초
- 동시성: 5 클라이언트

# 성능 프로파일링
pytest tests/performance/ --profile=true --html=reports/performance.html
```

### 작업 항목

#### 1) SPARQL SELECT 쿼리 최적화
```python
# 성능 테스트 케이스
import time
from app.services.rdf_converter import RDFConverter
from rdflib import Graph

class TestSPARQLPerformance:
    """SPARQL 성능 벤치마크"""
    
    def test_simple_select_performance(self, benchmark):
        """기본 SELECT 쿼리 (<50ms)"""
        converter = RDFConverter()
        graph = self._load_test_graph(10000)  # 10K 트리플
        
        query = "SELECT ?s ?p WHERE { ?s ?p ?o . } LIMIT 10"
        
        def run():
            return converter.sparql_query(graph, query)
        
        result = benchmark(run)
        assert len(result) <= 10
    
    def test_complex_select_performance(self, benchmark):
        """복잡한 SELECT (FILTER, BIND) (<150ms)"""
        converter = RDFConverter()
        graph = self._load_test_graph(50000)  # 50K 트리플
        
        query = """
        SELECT ?s ?label ?count
        WHERE {
            ?s rdfs:label ?label ;
               rdf:type ?type .
            FILTER (strlen(?label) > 5)
            BIND (strlen(?label) as ?count)
        }
        LIMIT 100
        """
        
        result = benchmark(lambda: converter.sparql_query(graph, query))
        assert len(result) <= 100
    
    def test_aggregate_query_performance(self, benchmark):
        """집계 쿼리 (<200ms)"""
        converter = RDFConverter()
        graph = self._load_test_graph(100000)  # 100K 트리플
        
        query = """
        SELECT ?type (COUNT(?s) as ?count)
        WHERE {
            ?s rdf:type ?type .
        }
        GROUP BY ?type
        """
        
        result = benchmark(lambda: converter.sparql_query(graph, query))
        assert len(result) > 0
    
    def test_join_query_performance(self, benchmark):
        """다중 JOIN (<250ms)"""
        converter = RDFConverter()
        graph = self._load_test_graph(100000)
        
        query = """
        SELECT ?person ?name ?org
        WHERE {
            ?person schema:name ?name ;
                    schema:worksFor ?org .
            ?org rdf:type schema:Organization .
        }
        LIMIT 50
        """
        
        result = benchmark(lambda: converter.sparql_query(graph, query))
    
    def _load_test_graph(self, triple_count: int) -> Graph:
        """테스트 그래프 로드"""
        # 실제 DBpedia 데이터 로드 또는 생성
        graph = Graph()
        # ... 구현
        return graph
```

#### 2) SPARQL CONSTRUCT 쿼리 최적화
```python
def test_construct_query_performance(self, benchmark):
    """CONSTRUCT 쿼리 성능 (<300ms)"""
    converter = RDFConverter()
    graph = self._load_test_graph(50000)
    
    query = """
    CONSTRUCT {
        ?person schema:name ?name ;
                schema:age ?age ;
                schema:knows ?otherPerson .
    }
    WHERE {
        ?person schema:name ?name ;
                schema:age ?age .
        OPTIONAL { ?person schema:knows ?otherPerson . }
    }
    LIMIT 1000
    """
    
    result = benchmark(lambda: converter.sparql_query(graph, query))
    assert len(result) > 0
```

#### 3) 캐싱 효과 측정
```python
def test_query_cache_hit_ratio(self):
    """캐시 히트율 (목표: ≥80%)"""
    from app.services.cache_service import CacheService
    
    cache = CacheService()
    converter = RDFConverter(cache_service=cache)
    graph = self._load_test_graph(100000)
    
    queries = [
        "SELECT ?s ?p WHERE { ?s ?p ?o . } LIMIT 10",
        "SELECT ?type (COUNT(*) as ?count) WHERE { ?s rdf:type ?type . } GROUP BY ?type",
    ] * 50  # 각 쿼리 50번씩 반복
    
    hit_count = 0
    for query in queries:
        start = time.time()
        result = converter.sparql_query(graph, query)
        elapsed = time.time() - start
        
        # 캐시된 결과는 <10ms
        if elapsed < 10:
            hit_count += 1
    
    hit_ratio = hit_count / len(queries)
    assert hit_ratio >= 0.80, f"Cache hit ratio too low: {hit_ratio}"
```

### 성능 목표
- [ ] Simple SELECT: < 50ms (10K 트리플)
- [ ] Complex SELECT: < 150ms (50K 트리플)
- [ ] Aggregate: < 200ms (100K 트리플)
- [ ] JOIN: < 250ms (100K 트리플)
- [ ] CONSTRUCT: < 300ms (50K 트리플)
- [ ] 캐시 히트율: ≥ 80%

---

## Task 5-2: RDF 그래프 메모리 최적화

**기간**: 06-25 ~ 06-27 (2일)

### 메모리 프로파일링

```python
import tracemalloc
import gc

class TestRDFMemoryOptimization:
    """RDF 그래프 메모리 효율화"""
    
    def test_large_graph_memory_footprint(self):
        """대규모 그래프 메모리 사용량"""
        converter = RDFConverter()
        
        tracemalloc.start()
        gc.collect()
        start_memory = tracemalloc.get_traced_memory()[0]
        
        # 100K 트리플 로드
        graph = self._load_test_graph(100000)
        
        peak_memory = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        
        memory_used_mb = (peak_memory - start_memory) / (1024 * 1024)
        
        # 목표: 100K 트리플당 500MB 이하
        assert memory_used_mb < 500, f"Memory usage too high: {memory_used_mb}MB"
    
    def test_graph_serialization_efficiency(self):
        """그래프 직렬화 효율성"""
        converter = RDFConverter()
        graph = self._load_test_graph(10000)
        
        # RDF/Turtle 형식
        turtle_str = converter.graph_to_rdf(graph, format='turtle')
        turtle_size_mb = len(turtle_str) / (1024 * 1024)
        
        # RDF/N-Triples 형식
        ntriples_str = converter.graph_to_rdf(graph, format='ntriples')
        ntriples_size_mb = len(ntriples_str) / (1024 * 1024)
        
        # Turtle이 더 압축되어야 함
        assert turtle_size_mb < ntriples_size_mb
        assert turtle_size_mb < 2  # 10K 트리플당 2MB 이하
    
    def test_graph_merge_memory_efficiency(self):
        """그래프 병합 메모리 효율"""
        converter = RDFConverter()
        
        tracemalloc.start()
        
        # 10개 그래프 병합 (각 10K 트리플)
        graphs = [self._load_test_graph(10000) for _ in range(10)]
        
        merged = converter.merge_graphs(graphs)
        
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        
        # 원본 그래프 크기의 150% 이하 (버퍼 고려)
        single_graph_size = graphs[0].__sizeof__()
        total_original = single_graph_size * 10
        assert peak < total_original * 1.5
```

### 최적화 전략

#### 1) 인덱싱 전략
```python
def test_sparql_query_index_effectiveness(self, benchmark):
    """인덱싱 효과 측정"""
    converter = RDFConverter()
    graph = self._load_test_graph(100000)
    
    # 인덱싱 없음 쿼리
    query_no_index = "SELECT ?o WHERE { ?s rdfs:label 'Specific Label' . ?s ?p ?o . }"
    
    # 인덱싱을 통한 최적화 가능
    # (rdflib는 자동 인덱싱, 커스텀 인덱스 검토)
    
    result = benchmark(lambda: converter.sparql_query(graph, query_no_index))
```

#### 2) 레이지 로딩 (Lazy Loading)
```python
class LazyRDFGraph:
    """온디맨드 트리플 로드"""
    
    def __init__(self, store_path: str):
        self.store_path = store_path
        self._graph = None
    
    @property
    def graph(self):
        if self._graph is None:
            self._graph = self._load_from_store()
        return self._graph
    
    def _load_from_store(self):
        """필요할 때만 로드"""
        # 구현
        pass
```

#### 3) 캐시 기반 메모리 관리
```python
def test_lru_cache_memory_bounds(self):
    """LRU 캐시 메모리 경계"""
    from functools import lru_cache
    
    cache = {}
    max_cache_size = 500  # 500개 항목
    
    @lru_cache(maxsize=max_cache_size)
    def cached_sparql_query(query_hash):
        # 구현
        pass
    
    # 500개 초과하면 오래된 항목부터 제거
    assert len(cache) <= max_cache_size
```

### 메모리 목표
- [ ] 100K 트리플: < 500MB
- [ ] Turtle 형식 압축률: Turtle < N-Triples
- [ ] 그래프 병합: 150% 이하 메모리 추가 사용
- [ ] 캐시 크기: 500 항목 상한선

---

## Task 5-3: 데이터베이스 인덱싱 & 쿼리 최적화

**기간**: 06-27 ~ 06-28 (1.5일)

### PostgreSQL 인덱싱 전략

```sql
-- rdf_graphs 테이블 인덱싱
CREATE INDEX CONCURRENTLY idx_rdf_graphs_entity_id 
ON rdf_graphs(entity_id);

CREATE INDEX CONCURRENTLY idx_rdf_graphs_created_at 
ON rdf_graphs(created_at DESC);

-- imported_entities 테이블 인덱싱
CREATE INDEX CONCURRENTLY idx_imported_entities_external_uri 
ON imported_entities(external_uri);

CREATE INDEX CONCURRENTLY idx_imported_entities_source 
ON imported_entities(source);

-- entity_mappings 테이블 인덱싱
CREATE INDEX CONCURRENTLY idx_entity_mappings_internal 
ON entity_mappings(internal_entity_id, confidence DESC);

CREATE INDEX CONCURRENTLY idx_entity_mappings_external 
ON entity_mappings(external_entity_id, external_source);

-- sparql_queries 테이블 인덱싱
CREATE INDEX CONCURRENTLY idx_sparql_queries_hash 
ON sparql_queries(MD5(query_text));

CREATE INDEX CONCURRENTLY idx_sparql_queries_executed_at 
ON sparql_queries(executed_at DESC);
```

### 쿼리 최적화 검증

```python
class TestDatabaseQueryOptimization:
    """DB 쿼리 성능 검증"""
    
    def test_entity_lookup_performance(self, db_session):
        """엔티티 조회 성능 (<10ms)"""
        import time
        
        entity_id = 'test-entity-001'
        
        start = time.time()
        entity = db_session.query(Entity).filter_by(id=entity_id).first()
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 10, f"Entity lookup too slow: {elapsed}ms"
    
    def test_batch_entity_lookup_performance(self, db_session):
        """배치 엔티티 조회 (<50ms for 100 items)"""
        entity_ids = [f'entity-{i:04d}' for i in range(100)]
        
        start = time.time()
        entities = db_session.query(Entity).filter(
            Entity.id.in_(entity_ids)
        ).all()
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 50
        assert len(entities) == 100
    
    def test_external_uri_deduplication_performance(self, db_session):
        """중복 제거 조회 성능 (<100ms for 1K URIs)"""
        external_uris = [f'http://example.org/{i}' for i in range(1000)]
        
        start = time.time()
        mappings = db_session.query(EntityMapping).filter(
            EntityMapping.external_entity_id.in_(external_uris)
        ).all()
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 100
    
    def test_import_history_query_performance(self, db_session):
        """임포트 이력 조회 (<50ms)"""
        source = 'dbpedia'
        
        start = time.time()
        imports = db_session.query(ImportedEntity).filter_by(
            source=source
        ).order_by(ImportedEntity.import_timestamp.desc()).limit(100).all()
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 50
```

### Execution Plan 분석

```bash
# 쿼리 실행 계획 검토
EXPLAIN ANALYZE
SELECT e.id, e.name, ie.external_uri, em.confidence
FROM entities e
LEFT JOIN imported_entities ie ON e.id = ie.entity_id
LEFT JOIN entity_mappings em ON e.id = em.internal_entity_id
WHERE e.created_at > NOW() - INTERVAL '7 days'
ORDER BY em.confidence DESC
LIMIT 100;

# 인덱스 효율 검증
SELECT * FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

### DB 최적화 목표
- [ ] 엔티티 조회: < 10ms (단건)
- [ ] 배치 조회: < 50ms (100개)
- [ ] 외부 URI 중복 제거: < 100ms (1000개)
- [ ] 임포트 이력: < 50ms
- [ ] 모든 인덱스 활성: idx_scan > 0

---

## 📊 성능 리포트 생성

```bash
# 성능 벤치마크 실행
pytest tests/performance/ --benchmark-only --html=reports/benchmarks.html

# 메모리 프로파일링
python -m memory_profiler app/services/rdf_converter.py

# DB 쿼리 로그 분석
psql -U postgres -d ontology_db -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 20;"
```

---

## 🎯 성공 기준

- [x] SPARQL 쿼리 성능 < 300ms (모든 타입)
- [x] RDF 그래프 메모리: < 500MB (100K 트리플)
- [x] 캐시 히트율: ≥ 80%
- [x] DB 인덱싱: 모든 주요 쿼리 커버
- [x] 단건 쿼리: < 10ms
- [x] 배치 쿼리: < 50ms

---

## 📈 성능 대시보드 설정

```python
# app/services/performance_monitor.py
class PerformanceMonitor:
    """성능 모니터링"""
    
    @staticmethod
    def record_sparql_query(query: str, elapsed_ms: int):
        """SPARQL 쿼리 기록"""
        # 메트릭: 쿼리 유형, 실행 시간, 캐시 여부
        
    @staticmethod
    def record_db_query(table: str, operation: str, elapsed_ms: int):
        """DB 쿼리 기록"""
        # 메트릭: 테이블, 작업, 실행 시간
        
    @staticmethod
    def get_performance_stats() -> Dict[str, Any]:
        """성능 통계 조회"""
        return {
            'avg_sparql_time': 0,
            'p95_sparql_time': 0,
            'cache_hit_rate': 0,
            'db_query_count': 0,
            'avg_db_time': 0
        }
```

---

## 🔗 관련 문서

- 지시서: `week_instructions/PHASE4/Week_5_BugFix/Antigravity.md`
- 성능 테스트: `tests/performance/test_sparql_performance.py`
- 메모리 분석: `tests/performance/test_memory_optimization.py`
- DB 최적화: `tests/performance/test_database_optimization.py`

---

**⚠️ 반드시 따르기**:

1. **저장 위치** (필수)
   - ✅ 정해진 위치: `task_logs/antigravity/YYYYMMDD_PHASE4_WEEK5_Antigravity_Complete.md`
   - 파일명 형식: `YYYYMMDD_HHMM_작업명.md`
   - 예: `20260628_1830_PHASE4_WEEK5_Antigravity_Complete.md`
   - ❌ 금지: `ont_platform/` 폴더에 저장하지 말 것

2. **템플릿 작성**:
   - "기간", "할당", "상태", "날짜" → 실제 작업 기록으로 채우기
   - "Task 5-1~5-3" 섹션 → 실제 완료 항목만 체크
   - "성능 결과" 표 → 실제 벤치마크 결과 입력
   - "메모리/DB 지표" → 실제 측정값 입력

---

**상태**: Task 5-1~5-3 준비 완료  
**예상 완료**: 2026-06-28 (금요일 오후)  
**다음 주차**: Week 6 Performance Optimization (고급 최적화)

---

## 📋 보고서 저장 지시

**작업 완료 후 다음 경로에 보고서를 저장하세요:**

**저장 경로**: `task_logs/antigravity/YYYYMMDD_HHMM_PHASE4_WEEK5_Antigravity_Complete.md`

**예시**: `20260628_1830_PHASE4_WEEK5_Antigravity_Complete.md`

**완료 후**: Claude가 3개 보고서를 취합하여 통합 보고서를 작성합니다.
(`task_logs/consolidated/YYYYMMDD_HHMM_PHASE4_WEEK5_Consolidated_Report.md`)
