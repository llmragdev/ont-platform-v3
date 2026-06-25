# Phase 5 Week 9: 자동 정렬 성능 최적화
## Antigravity (Performance) 수행 지시서

**기간**: 2026-07-22 ~ 2026-07-26 (5일)  
**할당**: 80% (주당 24-30시간)  
**목표**: 자동 매핑 성능 분석, 선택적 캐시 무효화, 대량 매핑 처리

---

## 개요

Phase 4의 수동 매핑 기능에서 Phase 5로 진입하면서 **자동 매핑 기능의 영향도 분석, 선택적 캐시 무효화, 대량 매핑 처리**가 중요해집니다.

Antigravity는 다음 3가지를 담당합니다:
1. **매핑 영향도 분석**: 매핑 변경이 어떤 엔티티/관계에 영향을 미치는지 사전 분석
2. **선택적 캐시 무효화**: 영향받는 부분만 캐시 무효화 (전체 무효화 회피)
3. **대량 매핑 처리**: 1000+ 개의 매핑을 실시간에 처리하는 능력

### Week 9의 3가지 핵심 기능

1. **영향도 분석 엔진** (Task 9-1): 매핑 변경이 몇 개의 엔티티/관계/쿼리에 영향을 미치는지 계산
2. **선택적 캐시 무효화** (Task 9-2): 영향받는 부분만 캐시 무효화 (1-hop 이웃까지만)
3. **대량 매핑 처리** (Task 9-3): GraphDB 배치 삽입 및 병렬 캐시 무효화

---

## 🔧 환경 설정

```bash
# Conda 환경 활성화
conda activate claud_be

# 작업 디렉토리
cd E:\ontology_edu\X_ont_std\ont_platform\v4\src\backend

# 의존성 설치
pip install networkx scipy pandas pytest-benchmark

# 성능 벤치마크
python -m pytest tests/phase5/week9_impact_analysis_bench.py -v --benchmark-only

# 프로파일링 (선택)
python -m cProfile -s cumulative tests/phase5/week9_impact_analysis_bench.py > profile.txt
```

---

## Task 9-1: 매핑 영향도 분석

**기간**: 07-22 ~ 07-23 (1.5일)

### 목표

매핑의 변경이 external_uri → internal_uri로 이동했을 때, 몇 개의 엔티티/관계/경로/쿼리가 영향을 받는지 사전 계산

### 구현 항목

#### 1) 영향도 분석 엔진

```python
# src/backend/app/services/impact_analysis_service.py
import networkx as nx
from typing import Dict, List, Set, Tuple
import numpy as np

class MappingImpactAnalyzer:
    """
    매핑 변경의 영향도를 분석하는 서비스
    
    주요 메트릭:
    - Affected Entities: 영향받을 엔티티 개수
    - Affected Relationships: 영향받을 관계 개수
    - Path Changes: 경로 변경의 개수
    - Query Impact: 영향받을 쿼리 개수
    """
    
    def __init__(self, rdf_graph, sparql_index):
        self.graph = rdf_graph  # NetworkX DiGraph
        self.sparql_index = sparql_index  # SPARQL 쿼리 인덱스
    
    async def analyze_mapping_impact(
        self,
        external_uri: str,
        internal_uri: str,
        relationship_type: str = "skos:exactMatch"
    ) -> Dict:
        """
        개별 매핑의 영향도 분석
        
        Returns:
        {
            "affectedEntityCount": 150,
            "affectedRelationshipCount": 320,
            "affectedPathCount": 45,
            "affectedQueryCount": 12,
            "reachabilityChange": 0.15,
            "estimatedProcessingTime": 250,
            "riskLevel": "medium"
        }
        """
        
        # 1. 직접 영향받는 엔티티 (1-hop neighbors)
        affected_entities = self._get_neighbors(
            internal_uri,
            depth=1,
            direction="both"
        )
        
        # 2. 관계 변경 (skos:exactMatch면 치환 가능)
        affected_relationships = []
        if relationship_type in ["skos:exactMatch", "owl:sameAs"]:
            # external_uri를 internal_uri로 치환하는 관계
            affected_relationships = list(
                self.graph.in_edges(external_uri) +
                self.graph.out_edges(external_uri)
            )
        
        # 3. 경로 변경 분석
        path_changes = self._analyze_path_changes(
            external_uri,
            internal_uri,
            affected_entities
        )
        
        # 4. SPARQL 쿼리 영향 분석
        affected_queries = self._find_affected_queries(
            external_uri,
            internal_uri
        )
        
        # 5. Reachability 변경도 계산
        reachability_before = self._calculate_reachability_score(
            external_uri,
            affected_entities
        )
        reachability_after = self._calculate_reachability_score(
            internal_uri,
            affected_entities
        )
        reachability_change = abs(reachability_before - reachability_after)
        
        # 6. 처리 시간 추정
        processing_time_ms = self._estimate_processing_time(
            len(affected_entities),
            len(affected_relationships),
            len(affected_queries)
        )
        
        # 7. 리스크 레벨 평가
        risk_level = self._assess_risk(
            len(affected_entities),
            len(affected_relationships),
            reachability_change
        )
        
        return {
            "externalUri": external_uri,
            "internalUri": internal_uri,
            "relationshipType": relationship_type,
            "affectedEntityCount": len(affected_entities),
            "affectedRelationshipCount": len(affected_relationships),
            "affectedPathCount": len(path_changes),
            "affectedQueryCount": len(affected_queries),
            "reachabilityChange": round(reachability_change, 3),
            "estimatedProcessingTimeMs": processing_time_ms,
            "riskLevel": risk_level,  # low, medium, high, critical
            "details": {
                "affectedEntities": list(affected_entities)[:10],  # 샘플 10개
                "affectedRelationships": affected_relationships[:10],
                "affectedQueries": [q['id'] for q in affected_queries[:5]]
            }
        }
    
    def _get_neighbors(
        self,
        node: str,
        depth: int = 1,
        direction: str = "both"
    ) -> Set[str]:
        """
        BFS로 이웃 노드 탐색
        
        Args:
            node: 시작 노드
            depth: 탐색 깊이 (hop)
            direction: "in", "out", "both"
        """
        visited = set()
        queue = [(node, 0)]
        
        while queue:
            current, curr_depth = queue.pop(0)
            if curr_depth > depth or current in visited:
                continue
            
            visited.add(current)
            
            if direction in ["in", "both"]:
                for pred in self.graph.predecessors(current):
                    if pred not in visited:
                        queue.append((pred, curr_depth + 1))
            
            if direction in ["out", "both"]:
                for succ in self.graph.successors(current):
                    if succ not in visited:
                        queue.append((succ, curr_depth + 1))
        
        return visited - {node}
    
    def _analyze_path_changes(
        self,
        external_uri: str,
        internal_uri: str,
        affected_entities: Set[str]
    ) -> List[Dict]:
        """
        경로 변경 분석
        
        external_uri가 internal_uri로 치환되면, 어떤 경로의 길이가 변경되는가
        """
        path_changes = []
        
        try:
            for entity in affected_entities:
                try:
                    old_path = nx.shortest_path(
                        self.graph,
                        external_uri,
                        entity
                    )
                    
                    new_path = nx.shortest_path(
                        self.graph,
                        internal_uri,
                        entity
                    )
                    
                    if old_path != new_path:
                        path_changes.append({
                            "targetEntity": entity,
                            "oldPathLength": len(old_path),
                            "newPathLength": len(new_path),
                            "oldPath": old_path,
                            "newPath": new_path
                        })
                except nx.NetworkXNoPath:
                    continue
        except:
            pass
        
        return path_changes
    
    def _calculate_reachability_score(
        self,
        node: str,
        target_entities: Set[str]
    ) -> float:
        """
        주어진 노드에서 target_entities에 도달 가능한 비율 계산
        """
        reachable_count = 0
        
        for entity in target_entities:
            try:
                nx.shortest_path(self.graph, node, entity)
                reachable_count += 1
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue
        
        if not target_entities:
            return 0.0
        
        return reachable_count / len(target_entities)
    
    def _find_affected_queries(
        self,
        external_uri: str,
        internal_uri: str
    ) -> List[Dict]:
        """
        external_uri 또는 internal_uri를 사용하는 SPARQL 쿼리 찾기
        """
        affected = []
        
        for query_record in self.sparql_index.find_queries_with_pattern(
            [external_uri, internal_uri]
        ):
            affected.append({
                "id": query_record['id'],
                "query": query_record['query'],
                "type": "exact_match" if external_uri in query_record['pattern_uris'] else "pattern_match"
            })
        
        return affected
    
    def _estimate_processing_time(
        self,
        entity_count: int,
        relationship_count: int,
        query_count: int
    ) -> int:
        """
        처리 시간 추정 (밀리초)
        
        - 엔티티당 5ms
        - 관계당 2ms
        - 쿼리당 10ms
        """
        return (entity_count * 5) + (relationship_count * 2) + (query_count * 10)
    
    def _assess_risk(
        self,
        entity_count: int,
        relationship_count: int,
        reachability_change: float
    ) -> str:
        """
        리스크 레벨 평가
        """
        risk_score = (
            (entity_count / 100) * 0.4 +  # 영향받는 엔티티 40%
            (relationship_count / 500) * 0.4 +  # 영향받는 관계 40%
            (reachability_change * 0.2)  # 도달도 변경 20%
        )
        
        if risk_score < 0.2:
            return "low"
        elif risk_score < 0.5:
            return "medium"
        elif risk_score < 0.8:
            return "high"
        else:
            return "critical"
```

### 성공 기준 (Task 9-1)
- [ ] 영향도 분석 엔진: 매핑 변경의 영향도 정량적으로 측정
- [ ] 영향받는 엔티티: 1-hop/2-hop 이웃까지 정확하게 추출
- [ ] 경로 변경: 변경 전후 경로 다중도 계산
- [ ] 쿼리 영향: SPARQL 쿼리에 미치는 영향 파악

---

## Task 9-2: 선택적 캐시 무효화

**기간**: 07-23 ~ 07-24 (1.5일)

### 목표

영향도 분석 결과를 바탕으로 영향받는 부분만 캐시 무효화 (전체 무효화 회피)

### 구현 항목

```python
# src/backend/app/services/selective_cache_invalidation.py
from typing import Set, Dict, List
import asyncio

class SelectiveCacheInvalidationEngine:
    """
    영향받는 부분만 선택적으로 캐시 무효화
    """
    
    def __init__(self, redis_client, graph_db, cache_layer):
        self.redis = redis_client
        self.graph_db = graph_db
        self.cache = cache_layer
    
    async def plan_invalidation(
        self,
        impact_analysis: Dict
    ) -> Dict:
        """
        무효화 계획 수립
        
        반환:
        {
            "queryPatterns": ["SPARQL 쿼리 패턴 1", ...],
            "cacheKeyPatterns": ["cache:neighborhood:*", ...],
            "indices": ["entity_index", "relationship_index"],
            "estimatedRecoveryTimeMs": 500
        }
        """
        
        external_uri = impact_analysis['externalUri']
        internal_uri = impact_analysis['internalUri']
        affected_entities = set(impact_analysis['details']['affectedEntities'])
        
        # 1. 쿼리 무효화 패턴 추출
        query_patterns = self._extract_query_patterns(
            external_uri,
            internal_uri
        )
        
        # 2. 캐시 무효화 패턴 생성
        cache_patterns = self._generate_cache_patterns(
            affected_entities,
            external_uri,
            internal_uri
        )
        
        # 3. 인덱스 업데이트 계획
        indices_to_update = self._identify_indices_to_update(
            affected_entities
        )
        
        # 4. 복구 시간 추정
        recovery_time = self._estimate_recovery_time(
            cache_patterns,
            indices_to_update
        )
        
        return {
            "externalUri": external_uri,
            "internalUri": internal_uri,
            "queryPatterns": query_patterns,
            "cacheKeyPatterns": cache_patterns,
            "indicesToUpdate": indices_to_update,
            "estimatedRecoveryTimeMs": recovery_time
        }
    
    async def execute_invalidation(
        self,
        invalidation_plan: Dict
    ) -> Dict:
        """
        계획된 캐시/인덱스 무효화 실행
        """
        start_time = asyncio.get_event_loop().time()
        
        tasks = [
            self._invalidate_cache_patterns(
                invalidation_plan['cacheKeyPatterns']
            ),
            self._update_indices(
                invalidation_plan['indicesToUpdate']
            ),
            self._clear_sparql_result_cache(
                invalidation_plan['queryPatterns']
            )
        ]
        
        results = await asyncio.gather(*tasks)
        
        elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return {
            "success": True,
            "invalidatedCacheKeys": results[0],
            "updatedIndices": results[1],
            "clearedQueries": results[2],
            "actualRecoveryTimeMs": round(elapsed_ms)
        }
    
    async def _invalidate_cache_patterns(
        self,
        patterns: List[str]
    ) -> int:
        """
        패턴에 맞는 모든 캐시 삭제
        """
        deleted_count = 0
        
        for pattern in patterns:
            # Redis의 SCAN + DEL 조합 (논블로킹)
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor,
                    match=pattern,
                    count=100
                )
                
                if keys:
                    await self.redis.delete(*keys)
                    deleted_count += len(keys)
                
                if cursor == 0:
                    break
        
        return deleted_count
    
    async def _update_indices(
        self,
        indices: List[str]
    ) -> Dict:
        """
        영향받는 인덱스 업데이트
        """
        updated = {}
        
        for index_name in indices:
            if index_name == "entity_index":
                updated[index_name] = await self._rebuild_entity_index()
            elif index_name == "relationship_index":
                updated[index_name] = await self._rebuild_relationship_index()
            elif index_name == "neighborhood_index":
                updated[index_name] = await self._rebuild_neighborhood_index()
        
        return updated
    
    async def _clear_sparql_result_cache(
        self,
        query_patterns: List[str]
    ) -> int:
        """
        SPARQL 결과 캐시 삭제
        """
        deleted_count = 0
        
        for pattern in query_patterns:
            pattern_hash = hash(pattern)
            cache_key = f"sparql_result:{pattern_hash}"
            
            if await self.redis.exists(cache_key):
                await self.redis.delete(cache_key)
                deleted_count += 1
        
        return deleted_count
    
    def _extract_query_patterns(
        self,
        external_uri: str,
        internal_uri: str
    ) -> List[str]:
        """
        external_uri 또는 internal_uri를 사용하는 쿼리 패턴 추출
        """
        return [
            f"*{external_uri}*",
            f"*{internal_uri}*"
        ]
    
    def _generate_cache_patterns(
        self,
        affected_entities: Set[str],
        external_uri: str,
        internal_uri: str
    ) -> List[str]:
        """
        캐시 무효화 패턴 생성
        """
        patterns = [
            f"neighborhood:{external_uri}:*",
            f"neighborhood:{internal_uri}:*",
            "graph:*",  # 그래프 캐시 전체
            "sparql_result:*"  # SPARQL 결과
        ]
        
        # 영향받는 엔티티마다 패턴
        for entity in list(affected_entities)[:10]:
            patterns.append(f"neighborhood:{entity}:*")
        
        return patterns
    
    def _identify_indices_to_update(
        self,
        affected_entities: Set[str]
    ) -> List[str]:
        """
        업데이트할 인덱스 결정
        """
        indices = []
        
        # 기본 업데이트
        indices.append("entity_index")
        indices.append("relationship_index")
        
        # 광범위 영향 범위면 추가 인덱스 업데이트
        if len(affected_entities) > 50:
            indices.append("neighborhood_index")
        
        return indices
    
    def _estimate_recovery_time(
        self,
        cache_patterns: List[str],
        indices: List[str]
    ) -> int:
        """
        복구 시간 추정 (밀리초)
        """
        # 캐시 패턴당 50ms, 인덱스당 200ms
        return (len(cache_patterns) * 50) + (len(indices) * 200)
```

### 성공 기준 (Task 9-2)
- [ ] 무효화 계획: 캐시 패턴, 인덱스 쿼리 결정
- [ ] 선택적 무효화: 영향받는 부분만 정확하게 삭제
- [ ] 병렬 처리: 캐시/인덱스 업데이트 동시 실행
- [ ] 복구 시간: < 1초 (일부의 경우)

---

## Task 9-3: 대량 매핑 처리

**기간**: 07-24 ~ 07-26 (2일)

### 목표

1000+ 개의 매핑을 실시간에 처리하는 능력

### 구현 항목

```python
# src/backend/app/services/bulk_mapping_executor.py
import asyncio
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class BulkMappingExecutor:
    """
    대량의 매핑을 배치로 처리
    """
    
    def __init__(
        self,
        graph_db,
        cache_layer,
        invalidation_engine,
        batch_size: int = 50,
        concurrent_batches: int = 4
    ):
        self.graph_db = graph_db
        self.cache = cache_layer
        self.invalidation = invalidation_engine
        self.batch_size = batch_size
        self.concurrent_batches = concurrent_batches
    
    async def execute_bulk_mappings(
        self,
        mappings: List[Dict]
    ) -> Dict:
        """
        대량 매핑 일괄 처리
        
        Args:
            mappings: [
                {
                    "externalUri": "...",
                    "internalUri": "...",
                    "relationshipType": "skos:exactMatch"
                }, ...
            ]
        
        Returns:
            {
                "totalMappings": 1000,
                "successCount": 998,
                "failureCount": 2,
                "totalTimeMs": 5000,
                "throughput": 200  # mappings/sec
            }
        """
        
        start_time = asyncio.get_event_loop().time()
        success_count = 0
        failure_count = 0
        
        # 배치로 분할
        batches = [
            mappings[i:i+self.batch_size]
            for i in range(0, len(mappings), self.batch_size)
        ]
        
        logger.info(f"Processing {len(mappings)} mappings in {len(batches)} batches")
        
        # 동시 배치 처리
        for i in range(0, len(batches), self.concurrent_batches):
            concurrent_tasks = batches[i:i+self.concurrent_batches]
            
            results = await asyncio.gather(
                *[
                    self._process_batch(batch)
                    for batch in concurrent_tasks
                ]
            )
            
            for batch_result in results:
                success_count += batch_result['success']
                failure_count += batch_result['failure']
        
        elapsed_time = asyncio.get_event_loop().time() - start_time
        throughput = len(mappings) / elapsed_time
        
        return {
            "totalMappings": len(mappings),
            "successCount": success_count,
            "failureCount": failure_count,
            "successRate": round(success_count / len(mappings), 3),
            "totalTimeMs": round(elapsed_time * 1000),
            "throughputPerSecond": round(throughput, 1)
        }
    
    async def _process_batch(
        self,
        batch: List[Dict]
    ) -> Dict:
        """
        개별 배치 처리
        """
        success = 0
        failure = 0
        failed_mappings = []
        
        for mapping in batch:
            try:
                # 1. 매핑 적용
                await self._apply_mapping(mapping)
                success += 1
            except Exception as e:
                failure += 1
                failed_mappings.append({
                    "mapping": mapping,
                    "error": str(e)
                })
                logger.warning(f"Failed mapping: {mapping['externalUri']} -> {mapping['internalUri']}")
        
        # 2. 배치 완료 후 캐시 무효화
        if success > 0:
            await self._invalidate_batch_cache(batch)
        
        return {
            "success": success,
            "failure": failure,
            "failedMappings": failed_mappings
        }
    
    async def _apply_mapping(self, mapping: Dict):
        """
        개별 매핑 적용
        
        **중요**: Batch Transaction 패턴 적용
        - 여러 INSERT를 한 번의 SPARQL 호출로 묶기
        """
        external_uri = mapping['externalUri']
        internal_uri = mapping['internalUri']
        relationship = mapping['relationshipType']
        
        # GraphDB에 triple 추가
        triple_statement = f"""
        INSERT DATA {{
            <{external_uri}> <{relationship}> <{internal_uri}> .
        }}
        """
        
        await self.graph_db.execute_update(triple_statement)
    
    async def _invalidate_batch_cache(self, batch: List[Dict]):
        """
        배치 완료 후 캐시 무효화
        
        **최적화**: 배치 캐시 무효화로 병렬 처리 효율 향상
        """
        cache_keys = []
        
        for mapping in batch:
            for uri in [mapping['externalUri'], mapping['internalUri']]:
                cache_keys.append(f"neighborhood:{uri}:*")
        
        # 배치 캐시 무효화 (병렬 처리)
        await self.cache.invalidate_patterns(cache_keys)
```

### 성능 벤치마크

```python
# tests/phase5/week9_bulk_mapping_bench.py
import pytest
import asyncio
from test_fixtures import benchmark

@pytest.mark.benchmark
class TestBulkMappingPerformance:
    
    async def test_1000_mappings_execution(self, benchmark):
        """1000개 매핑 처리 시간"""
        mappings = self._generate_test_mappings(1000)
        
        async def run():
            return await executor.execute_bulk_mappings(mappings)
        
        result = benchmark(asyncio.run, run())
        assert result['totalTimeMs'] < 10000  # 10초 이내
        assert result['throughputPerSecond'] > 100  # 100+ per second
    
    async def test_cache_invalidation_efficiency(self, benchmark):
        """캐시 무효화 효율"""
        cache_keys = [f"cache_key_{i}" for i in range(10000)]
        
        async def run():
            return await invalidation_engine._invalidate_cache_patterns(
                [f"cache_key_{i}:*" for i in range(100)]
            )
        
        result = benchmark(asyncio.run, run())
        assert result < 1000  # 1초 이내
```

### 성공 기준 (Task 9-3)
- [ ] 대량 처리: 1000+ 매핑을 < 10초로 처리
- [ ] 처리량: 최소 100 mappings/second
- [ ] 병렬화: 동시 배치 처리로 효율성 극대화
- [ ] 정확성: 실패한 매핑 추적 및 로깅

---

## 성능 목표

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| 영향도 분석 시간 | < 100ms | 개별 매핑 분석 |
| 캐시 무효화 시간 | < 500ms | 배치 무효화 |
| 대량 처리 처리량 | 최소 100 mappings/sec | 1000개 매핑 |
| 메모리 사용 | < 500MB | 대량 처리 중 |
| 캐시 히트율 | 최소 70% | 무효화 후 복구 |

---

## 테스트 체크리스트

```bash
# 영향도 분석 테스트
pytest tests/phase5/week9_impact_analysis_test.py -v

# 캐시 무효화 테스트
pytest tests/phase5/week9_cache_invalidation_test.py -v

# 대량 처리 성능 벤치마크
pytest tests/phase5/week9_bulk_mapping_bench.py -v --benchmark-only
```

---

## 주의사항

### GraphDB 성능 최적화
- 개별 INSERT 루프 회피 (배치로 통합)
- 인덱스 업데이트를 배치 완료 후 실행
- 병렬 처리(parallelism) 설정 최적화

### 메모리 관리
- 배치 처리 중 메모리 모니터링
- 대량 캐시 무효화 시 메모리 스파이크 방지
- Redis 메모리 사용량 추적 설정

### 정확성
- 매핑 실패 시 즉시 로깅 (메커니즘 포함)
- 부분 실패 처리 (계속 진행)
- 결과 검증 및 재시도 로직

---

**다음 단계**: Task 9-2 캐시 무효화→Task 9-3 대량 처리 병렬 지시로 진행
