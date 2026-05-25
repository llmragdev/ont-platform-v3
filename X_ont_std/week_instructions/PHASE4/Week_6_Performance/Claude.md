# Phase 4 Week 6: Performance Optimization
## Claude (Backend) 수행 지시서

**기간**: 2026-07-01 ~ 2026-07-05 (5일)  
**할당**: 80% (주당 24-30시간)  
**목표**: SPARQL 고급 최적화, 쿼리 재작성 엔진, 비동기 파이프라인 최적화

---

## Task 6-1: SPARQL 쿼리 재작성 엔진

**기간**: 07-01 ~ 07-02 (1.5일)

### 목표
SPARQL 쿼리를 자동으로 최적화된 형태로 변환하여 실행 시간 50% 단축

### 구현 항목

#### 1) 쿼리 파싱 및 AST 생성
```python
from rdflib.plugins.sparql import prepareQuery, algebra
from typing import Dict, List, Tuple

class SPARQLQueryOptimizer:
    """SPARQL 쿼리 자동 최적화"""
    
    def __init__(self):
        self.stats = {}  # 그래프 통계 캐시
    
    def optimize_query(self, query_str: str) -> str:
        """쿼리 최적화"""
        # 1. 파싱
        parsed = prepareQuery(query_str)
        
        # 2. AST 분석
        algebra_form = algebra.translateQuery(parsed)
        
        # 3. 최적화 규칙 적용
        optimized = self._apply_optimization_rules(algebra_form)
        
        # 4. 쿼리 문자열로 변환
        return str(optimized)
    
    def _apply_optimization_rules(self, algebra_form):
        """최적화 규칙"""
        # 규칙 1: FILTER 푸시다운 (FILTER를 가능한 빨리)
        algebra_form = self._pushdown_filters(algebra_form)
        
        # 규칙 2: 조인 순서 재배열 (선택도 낮은 패턴부터)
        algebra_form = self._reorder_joins(algebra_form)
        
        # 규칙 3: OPTIONAL 패턴 분리
        algebra_form = self._separate_optional_patterns(algebra_form)
        
        return algebra_form
```

#### 2) FILTER 푸시다운 (Filter Pushdown)
```python
def _pushdown_filters(self, algebra_form):
    """FILTER를 가능한 빨리 실행"""
    # 예: SELECT * WHERE { ?s ?p ?o . ?x ?y ?z . FILTER(?s = <uri>) }
    # 최적화: FILTER를 첫 번째 패턴 바로 뒤로 이동
    
    filters = self._extract_filters(algebra_form)
    patterns = self._extract_patterns(algebra_form)
    
    # 각 FILTER가 의존하는 변수 분석
    for filter_expr in filters:
        variables = self._get_filter_variables(filter_expr)
        
        # 해당 변수를 정의하는 패턴 찾기
        for i, pattern in enumerate(patterns):
            pattern_vars = self._get_pattern_variables(pattern)
            if variables.issubset(pattern_vars):
                # FILTER를 패턴 직후로 이동
                patterns.insert(i + 1, filter_expr)
                break
    
    return self._reconstruct_algebra(patterns, filters)
```

#### 3) 조인 순서 최적화
```python
def _reorder_joins(self, algebra_form):
    """선택도(Selectivity) 기반 조인 순서 재배열"""
    patterns = self._extract_patterns(algebra_form)
    
    # 각 패턴의 선택도 추정
    selectivities = []
    for pattern in patterns:
        selectivity = self._estimate_selectivity(pattern)
        selectivities.append((pattern, selectivity))
    
    # 선택도가 낮은 순서대로 정렬 (가장 제한적인 것부터)
    selectivities.sort(key=lambda x: x[1])
    ordered_patterns = [p for p, _ in selectivities]
    
    return self._reconstruct_algebra(ordered_patterns, [])

def _estimate_selectivity(self, pattern: str) -> float:
    """패턴의 선택도 추정 (0~1, 작을수록 선택적)"""
    # 구현: 그래프 통계 기반 추정
    # - 상수 객체를 가진 패턴: 낮은 선택도
    # - 변수만 있는 패턴: 높은 선택도
    # - FILTER가 있는 패턴: 선택도 감소
    
    if self._is_constant_object_pattern(pattern):
        return 0.1  # 10% - 매우 선택적
    elif self._has_filter(pattern):
        return 0.3  # 30%
    else:
        return 0.8  # 80% - 선택도 낮음
```

#### 4) OPTIONAL 패턴 분리
```python
def _separate_optional_patterns(self, algebra_form):
    """OPTIONAL 패턴을 별도 서브쿼리로"""
    optional_patterns = self._extract_optional_patterns(algebra_form)
    required_patterns = self._extract_required_patterns(algebra_form)
    
    # OPTIONAL 없이 먼저 실행
    required_result = self._execute_patterns(required_patterns)
    
    # 각 OPTIONAL을 별도로 실행하고 LEFT JOIN
    for opt_pattern in optional_patterns:
        opt_result = self._execute_pattern(opt_pattern)
        required_result = self._left_join(required_result, opt_result)
    
    return required_result
```

### 성능 목표
- [ ] 쿼리 재작성 시간: < 50ms (복잡한 쿼리)
- [ ] 최적화 후 실행: 50% 이상 단축
- [ ] 정확성: 100% (쿼리 결과 동일)

---

## Task 6-2: 비동기 파이프라인 최적화

**기간**: 07-02 ~ 07-04 (2일)

### 목표
병렬 처리를 통해 임포트/변환/쿼리 파이프라인의 처리량 2배 증가

### 구현 항목

#### 1) 병렬 임포트 엔진
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.services.ontology_importer import OntologyImporter

class ParallelImportEngine:
    """병렬 임포트 처리"""
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.importer = OntologyImporter()
    
    async def import_multiple_sources(self, 
                                     source_configs: List[Dict]) -> List[Dict]:
        """여러 소스에서 병렬 임포트"""
        tasks = []
        
        for config in source_configs:
            if config['source'] == 'dbpedia':
                task = self.importer.import_from_dbpedia(
                    config['uri'], 
                    config['domain']
                )
            elif config['source'] == 'wikidata':
                task = self.importer.import_from_wikidata(
                    config['qid'],
                    config['domain']
                )
            else:
                task = self.importer.import_from_rdf_file(
                    config['file_path']
                )
            
            tasks.append(task)
        
        # 동시 실행 (최대 5개 동시)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [r for r in results if not isinstance(r, Exception)]
    
    async def import_with_deduplication(self, 
                                       source_configs: List[Dict]) -> Dict:
        """병렬 임포트 + 병렬 중복 제거"""
        # 단계 1: 병렬 임포트
        imported = await self.import_multiple_sources(source_configs)
        
        # 단계 2: 배치 중복 제거
        deduplicated = await self.importer.batch_deduplicate(imported)
        
        # 단계 3: 병렬 병합
        merged = await self._parallel_merge(deduplicated)
        
        return {
            'imported': len(imported),
            'deduplicated': len(deduplicated),
            'merged': merged
        }
    
    async def _parallel_merge(self, entities: List[Dict]) -> Dict:
        """병렬 엔티티 병합"""
        # 엔티티를 배치로 분할
        batch_size = len(entities) // self.max_workers + 1
        batches = [
            entities[i:i+batch_size] 
            for i in range(0, len(entities), batch_size)
        ]
        
        # 각 배치를 병렬로 병합
        tasks = [
            self.importer.batch_merge(batch) 
            for batch in batches
        ]
        
        batch_results = await asyncio.gather(*tasks)
        
        # 배치 결과 통합
        return self.importer.merge_batch_results(batch_results)
```

#### 2) 파이프라인 체이닝
```python
class SPARQLPipeline:
    """SPARQL 처리 파이프라인"""
    
    def __init__(self):
        self.converter = RDFConverter()
        self.importer = OntologyImporter()
    
    async def execute_end_to_end(self, 
                                query: str,
                                import_config: Dict) -> Dict:
        """임포트 → 변환 → 쿼리를 병렬로 처리"""
        # 병렬 실행:
        # - 임포트 작업 진행 중 RDF 변환 준비
        # - 변환 완료 즉시 쿼리 시작
        
        # 단계 1: 임포트 시작 (백그라운드)
        import_task = asyncio.create_task(
            self.importer.import_from_dbpedia(
                import_config['uri'],
                import_config['domain']
            )
        )
        
        # 단계 2: 임포트 완료 기다리면서 변환 준비
        entity = await import_task
        
        # 단계 3: RDF 변환
        graph = self.converter.entity_to_rdf(entity)
        
        # 단계 4: SPARQL 쿼리 실행
        results = self.converter.sparql_query(graph, query)
        
        return {
            'entity': entity,
            'graph': graph,
            'results': results
        }
    
    async def batch_execute_pipeline(self,
                                    queries: List[str],
                                    import_configs: List[Dict]) -> List[Dict]:
        """배치 파이프라인"""
        # 모든 임포트를 병렬 시작
        import_tasks = [
            self.importer.import_from_dbpedia(
                config['uri'],
                config['domain']
            )
            for config in import_configs
        ]
        
        entities = await asyncio.gather(*import_tasks)
        
        # 모든 엔티티를 RDF로 변환 (병렬)
        convert_tasks = [
            asyncio.create_task(
                asyncio.to_thread(
                    self.converter.entity_to_rdf,
                    entity
                )
            )
            for entity in entities
        ]
        
        graphs = await asyncio.gather(*convert_tasks)
        
        # 병합된 그래프로 모든 쿼리 실행
        merged_graph = self.converter.merge_graphs(graphs)
        
        # 쿼리 병렬 실행
        query_tasks = [
            asyncio.create_task(
                asyncio.to_thread(
                    self.converter.sparql_query,
                    merged_graph,
                    query
                )
            )
            for query in queries
        ]
        
        results = await asyncio.gather(*query_tasks)
        
        return results
```

#### 3) 동시성 제어 & 리소스 풀링
```python
class AsyncResourcePool:
    """비동기 리소스 풀"""
    
    def __init__(self, max_connections: int = 10):
        self.semaphore = asyncio.Semaphore(max_connections)
        self.active_tasks = set()
    
    async def acquire(self):
        """리소스 획득"""
        await self.semaphore.acquire()
    
    def release(self):
        """리소스 해제"""
        self.semaphore.release()
    
    async def run_with_limit(self, coro):
        """제한된 동시성으로 코루틴 실행"""
        async with self.semaphore:
            task = asyncio.create_task(coro)
            self.active_tasks.add(task)
            
            try:
                return await task
            finally:
                self.active_tasks.discard(task)
    
    async def wait_all(self):
        """모든 작업 완료 기다리기"""
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks, return_exceptions=True)

# 사용 예
pool = AsyncResourcePool(max_connections=5)

async def import_batch(sources: List[str]):
    tasks = [
        pool.run_with_limit(
            importer.import_from_dbpedia(source, 'domain')
        )
        for source in sources
    ]
    
    results = await asyncio.gather(*tasks)
    await pool.wait_all()
```

### 성능 목표
- [ ] 병렬 임포트: 3개 소스 동시, 처리시간 30% 단축
- [ ] 파이프라인 오버헤드: < 5%
- [ ] 메모리 사용: 선형 증가 (동시성 N배 → 메모리 1.2배 이하)

---

## Task 6-3: 인덱싱 전략 & 쿼리 캐싱

**기간**: 07-04 ~ 07-05 (1.5일)

### 1) RDF 그래프 인덱싱
```python
class RDFGraphIndexer:
    """RDF 그래프 인덱싱"""
    
    def __init__(self, graph):
        self.graph = graph
        self.indexes = {}
    
    def build_indexes(self):
        """전체 인덱스 구축"""
        # 인덱스 1: Subject 기반
        self.indexes['subject'] = self._build_subject_index()
        
        # 인덱스 2: Predicate 기반
        self.indexes['predicate'] = self._build_predicate_index()
        
        # 인덱스 3: Object 기반
        self.indexes['object'] = self._build_object_index()
        
        # 인덱스 4: SPO 조합 (자주 함께 나타나는 패턴)
        self.indexes['spo'] = self._build_spo_index()
    
    def _build_subject_index(self) -> Dict:
        """Subject → Predicates 인덱스"""
        index = {}
        for s, p, o in self.graph.triples((None, None, None)):
            if s not in index:
                index[s] = []
            index[s].append((p, o))
        return index
    
    def _build_predicate_index(self) -> Dict:
        """Predicate → Subjects 인덱스"""
        index = {}
        for s, p, o in self.graph.triples((None, None, None)):
            if p not in index:
                index[p] = set()
            index[p].add(s)
        return index
    
    def _build_object_index(self) -> Dict:
        """Object → Subjects 인덱스"""
        index = {}
        for s, p, o in self.graph.triples((None, None, None)):
            if o not in index:
                index[o] = set()
            index[o].add(s)
        return index
    
    def _build_spo_index(self) -> Dict:
        """자주 함께 나타나는 (S, P, O) 패턴 인덱스"""
        pattern_counts = {}
        for s, p, o in self.graph.triples((None, None, None)):
            key = (type(s), type(p), type(o))
            pattern_counts[key] = pattern_counts.get(key, 0) + 1
        return pattern_counts
    
    def lookup_by_subject(self, subject) -> List:
        """Subject로 조회"""
        return self.indexes['subject'].get(subject, [])
    
    def lookup_by_predicate(self, predicate) -> Set:
        """Predicate로 조회"""
        return self.indexes['predicate'].get(predicate, set())
```

### 2) 쿼리 결과 캐싱 & 무효화
```python
from functools import lru_cache
from datetime import datetime, timedelta
import hashlib

class SPARQLQueryCache:
    """SPARQL 쿼리 결과 캐싱"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds
        self.hit_count = 0
        self.miss_count = 0
    
    def _hash_query(self, query: str) -> str:
        """쿼리 정규화 및 해싱"""
        # 1. 공백 정규화
        normalized = ' '.join(query.split())
        
        # 2. 대소문자 정규화
        normalized = normalized.upper()
        
        # 3. 해시
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get(self, query: str, graph_hash: str):
        """캐시 조회"""
        cache_key = f"{self._hash_query(query)}:{graph_hash}"
        
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            
            # TTL 확인
            if datetime.utcnow() - timestamp < timedelta(seconds=self.ttl):
                self.hit_count += 1
                return result
            else:
                # 만료된 항목 제거
                del self.cache[cache_key]
        
        self.miss_count += 1
        return None
    
    def set(self, query: str, graph_hash: str, result):
        """캐시 저장"""
        cache_key = f"{self._hash_query(query)}:{graph_hash}"
        self.cache[cache_key] = (result, datetime.utcnow())
    
    def invalidate_by_graph(self, graph_hash: str):
        """특정 그래프 캐시 무효화"""
        keys_to_remove = [
            k for k in self.cache.keys() 
            if k.endswith(f":{graph_hash}")
        ]
        for k in keys_to_remove:
            del self.cache[k]
    
    def get_stats(self) -> Dict:
        """캐시 통계"""
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total > 0 else 0
        
        return {
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'total': total,
            'hit_rate': f"{hit_rate:.1f}%",
            'cache_size': len(self.cache)
        }
```

### 성능 목표
- [ ] 인덱싱 구축: < 1초 (100K 트리플)
- [ ] 인덱스 조회: < 10ms (평균)
- [ ] 캐시 히트율: ≥ 75%
- [ ] 캐시 메모리: < 500MB (1000 항목)

---

## 🎯 성공 기준

- [x] SPARQL 쿼리 재작성: 50% 성능 개선
- [x] 병렬 임포트: 처리량 2배 증가
- [x] 비동기 파이프라인: 5% 오버헤드
- [x] RDF 인덱싱: < 1초 구축
- [x] 쿼리 캐싱: 75% 히트율

---

## 📊 측정 및 리포팅

```bash
# 성능 개선 측정
pytest tests/performance/test_query_optimization.py -v --benchmark-only

# 비동기 처리 검증
pytest tests/async/test_parallel_pipeline.py -v

# 인덱싱 성능
pytest tests/performance/test_indexing.py -v
```

---

**⚠️ 반드시 따르기**:

1. **저장 위치** (필수)
   - ✅ 정해진 위치: `task_logs/claude/YYYYMMDD_PHASE4_WEEK6_Claude_Complete.md`
   - 예: `20260705_1830_PHASE4_WEEK6_Claude_Complete.md`
   - ❌ 금지: `ont_platform/` 폴더에 저장하지 말 것

---

**상태**: Task 6-1~6-3 준비 완료  
**예상 완료**: 2026-07-05 (토요일)  
**다음 주차**: Week 7 Advanced UI & Visualization

---

## 📋 보고서 저장 & 통합 지시

### 개별 보고서 경로 (필수)

| 에이전트 | 저장 경로 | 예시 |
|---------|---------|------|
| **Claude** | `task_logs/claude/YYYYMMDD_HHMM_PHASE4_WEEK6_Claude_Complete.md` | `20260705_1830_PHASE4_WEEK6_Claude_Complete.md` |
| **Codex** | `task_logs/codex/YYYYMMDD_HHMM_PHASE4_WEEK6_Codex_Complete.md` | `20260705_1830_PHASE4_WEEK6_Codex_Complete.md` |
| **Antigravity** | `task_logs/antigravity/YYYYMMDD_HHMM_PHASE4_WEEK6_Antigravity_Complete.md` | `20260705_1830_PHASE4_WEEK6_Antigravity_Complete.md` |

### 통합 보고서 (Claude 담당) ⭐

**Claude는 3개 에이전트 보고서를 모니터링하다가 모두 완료되면 최종 통합 보고서를 작성합니다:**

| 항목 | 내용 |
|------|------|
| **저장 경로** | `task_logs/consolidated/YYYYMMDD_HHMM_PHASE4_WEEK6_Consolidated_Report.md` |
| **작성 시기** | 3개 에이전트 보고서 모두 제출 후 |
| **예시** | `20260705_2000_PHASE4_WEEK6_Consolidated_Report.md` |

**⚠️ Claude의 모니터링 체크리스트:**
- [ ] Claude 보고서 생성됨
- [ ] Codex 보고서 생성됨
- [ ] Antigravity 보고서 생성됨
- [ ] 통합 보고서 작성 완료
