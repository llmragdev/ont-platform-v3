# Phase 5 Week 10: OWL 추론 성능 최적화
## Antigravity (Performance) 수행 지시서

**기간**: 2026-07-29 ~ 2026-08-02 (5일)  
**할당**: 80% (주당 24-30시간)  
**목표**: OWL 추론 성능 최적화 및 캐싱 (1M~10M triple 추론 최적화)

---

## 개요

OWL 추론은 계산 집약적입니다. Week 10의 목표는 1M~10M 규모의 triple 추론을 효율적으로 처리하는 것입니다. Antigravity는 **증분 추론**, **결과 캐싱**, 그리고 **성능 벤치마킹**을 담당합니다. (1B 규모 처리는 Phase 5 최종 stretch goal)

### Week 10의 3가지 핵심 기능

1. **증분 추론 엔진** (Task 10-1): 전체 재계산 대신 변경 부분만 추론
2. **분산 추론 처리** (Task 10-2): Spark를 활용한 병렬 추론
3. **추론 결과 캐싱** (Task 10-3): 추론 결과 사전 계산 및 캐싱

---

## 🔧 환경 설정

```bash
conda activate claud_be
pip install rdflib sparqlwrapper

# Week 10: 로컬 개발 (Spark 불필요)
uvicorn main:app --reload --port 8001

# [선택] Spark 분산 처리 (Week 12 대규모 벤치마크용)
# pip install pyspark
# $SPARK_HOME/sbin/start-master.sh
# $SPARK_HOME/sbin/start-slave.sh spark://localhost:7077
```

---

## Task 10-1: 증분 추론 엔진

**기간**: 07-29 ~ 07-30 (1.5일)

### 구현 항목

```python
# src/backend/app/services/incremental_reasoning.py
from typing import Set, Dict, List, Tuple
import asyncio
import time

class IncrementalReasoningEngine:
    """
    변경된 부분에만 추론을 적용하는 증분 추론 엔진
    
    원리:
    - 새로 추가된 triple만 영향받는 범위 계산
    - 영향받는 노드의 이웃에 대해서만 추론 재계산
    - 기존 추론 결과는 유지
    
    성능 개선 (Week 10 목표):
    - 증분 추론: 1000 new triple 추가 시 < 100ms
    - 캐시 히트: 반복 추론 < 10ms
    - 메모리 효율: 1M triple 당 < 500MB
    """
    
    def __init__(self, graph_db, reasoner):
        self.graph_db = graph_db
        self.reasoner = reasoner
        self.change_log = {}  # 변경 이력 추적
    
    async def apply_incremental_reasoning(
        self,
        new_triples: List[Tuple],
        removed_triples: List[Tuple] = None
    ) -> Dict:
        """
        변경된 triple에 대해서만 추론 적용
        """
        
        start_time = time.time()
        
        if removed_triples is None:
            removed_triples = []
        
        # 1. 영향받을 노드 범위 식별
        affected_nodes = self._identify_affected_scope(
            new_triples,
            removed_triples
        )
        
        # 2. 영향받는 노드에 대해서만 추론 재계산
        new_inferences = []
        invalidated_inferences = []
        
        for node in affected_nodes:
            # 이 노드와 관련된 추론 재계산
            node_inferences = await self._recompute_node_inferences(node)
            new_inferences.extend(node_inferences)
            
            # 제거된 triple로 인해 무효화된 추론 식별
            if removed_triples:
                invalid = await self._identify_invalidated_inferences(
                    node,
                    removed_triples
                )
                invalidated_inferences.extend(invalid)
        
        # 3. 결과 적용
        await self._apply_incremental_changes(
            new_inferences,
            invalidated_inferences
        )
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return {
            "newTriples": len(new_triples),
            "removedTriples": len(removed_triples),
            "affectedNodes": len(affected_nodes),
            "newInferences": len(new_inferences),
            "invalidatedInferences": len(invalidated_inferences),
            "processingTimeMs": round(elapsed_ms),
            "efficiency": round(
                len(new_triples) / (elapsed_ms + 0.1) * 1000,  # triples/sec
                1
            )
        }
    
    def _identify_affected_scope(
        self,
        new_triples: List[Tuple],
        removed_triples: List[Tuple]
    ) -> Set[str]:
        """
        변경된 triple과 1-2 hop 이웃을 영향받는 범위로 식별
        
        효율성:
        - 직접 영향: new/removed triple의 subject, object
        - 간접 영향 (1-hop): 직접 영향 노드의 이웃
        - 2-hop: 제한적으로만 포함 (연쇄 효과 고려)
        """
        affected = set()
        
        # 1. 직접 영향
        for subject, predicate, obj in (new_triples + removed_triples):
            affected.add(subject)
            affected.add(obj)
        
        # 2. 1-hop 이웃 (대규모 그래프에서는 선택적)
        if len(affected) < 100:  # 작은 변경만 1-hop 이웃 포함
            expanded = set(affected)
            for node in list(affected):
                # 이 노드를 포함하는 triple들의 다른 노드
                for neighbor in self._get_one_hop_neighbors(node):
                    expanded.add(neighbor)
            affected = expanded
        
        return affected
    
    def _get_one_hop_neighbors(self, node: str) -> Set[str]:
        """주어진 노드의 1-hop 이웃 반환"""
        neighbors = set()
        
        # Subject로 나가는 edge
        for triple in self.graph_db.get_triples_with_subject(node):
            neighbors.add(triple[2])  # object
        
        # Object로 들어오는 edge
        for triple in self.graph_db.get_triples_with_object(node):
            neighbors.add(triple[0])  # subject
        
        return neighbors
    
    async def _recompute_node_inferences(self, node: str) -> List[Tuple]:
        """
        특정 노드와 관련된 추론 재계산
        """
        inferences = []
        
        # 이 노드를 포함하는 모든 규칙 적용
        
        # 1. Subclass transitivity: A subClassOf B, B subClassOf C => A subClassOf C
        subclass_inferences = self._apply_subclass_transitivity_for_node(node)
        inferences.extend(subclass_inferences)
        
        # 2. SameAs symmetry: A sameAs B => B sameAs A
        sameas_inferences = self._apply_sameas_rules_for_node(node)
        inferences.extend(sameas_inferences)
        
        # 3. Domain/Range constraints
        domain_range_inferences = self._apply_domain_range_for_node(node)
        inferences.extend(domain_range_inferences)
        
        return inferences
    
    def _apply_subclass_transitivity_for_node(self, node: str) -> List[Tuple]:
        """특정 노드에 대한 subclass transitivity 추론"""
        inferences = []
        
        # node의 모든 상위 클래스 찾기
        ancestors = self._find_ancestors(node, predicate="rdfs:subClassOf")
        
        for ancestor in ancestors:
            new_triple = (node, "rdfs:subClassOf", ancestor)
            if not self.graph_db.has_triple(new_triple):
                inferences.append(new_triple)
        
        return inferences
    
    def _find_ancestors(self, node: str, predicate: str) -> Set[str]:
        """BFS로 모든 상위 노드 찾기"""
        ancestors = set()
        visited = set()
        queue = [node]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            # current의 직접 상위 찾기
            for triple in self.graph_db.get_triples_with_subject(current):
                if triple[1] == predicate:
                    parent = triple[2]
                    if parent not in visited:
                        ancestors.add(parent)
                        queue.append(parent)
        
        return ancestors - {node}
    
    async def _identify_invalidated_inferences(
        self,
        node: str,
        removed_triples: List[Tuple]
    ) -> List[Tuple]:
        """제거된 triple 때문에 무효화된 추론 식별"""
        invalidated = []
        
        # 제거된 triple이 이 노드의 추론에 영향을 미치는가?
        for removed in removed_triples:
            if node in removed or removed in self._get_dependent_inferences(node):
                # 이 노드의 추론 중 removed에 의존하는 것들 찾기
                deps = self._find_dependent_inferences(node, removed)
                invalidated.extend(deps)
        
        return invalidated
    
    async def _apply_incremental_changes(
        self,
        new_inferences: List[Tuple],
        invalidated_inferences: List[Tuple]
    ):
        """변경 사항을 그래프에 적용"""
        
        # 새 추론 추가
        for triple in new_inferences:
            await self.graph_db.add_triple(triple, inferred=True)
        
        # 무효화된 추론 제거
        for triple in invalidated_inferences:
            await self.graph_db.remove_triple(triple, inferred=True)
```

### 성공 기준 (Task 10-1)
- [ ] 영향 범위 정확 식별: 변경 부분과 이웃 노드만 대상
- [ ] 부분 재계산: 전체 재계산 대비 10배 이상 빠름
- [ ] 메모리 효율: 변경된 부분만 메모리에 유지

---

## Task 10-2: 분산 추론 처리 (Spark)

**기간**: 07-30 ~ 07-31 (1.5일)

### 구현 항목

```python
# src/backend/app/services/distributed_reasoning.py
from pyspark.sql import SparkSession
from pyspark.rdd import RDD
from typing import Dict, List

class DistributedReasoningEngine:
    """
    Apache Spark를 활용한 분산 OWL 추론
    
    아키텍처:
    - RDF triple을 Spark RDD로 변환
    - 추론 규칙을 각 파티션에서 병렬 적용
    - 결과 집계 및 저장
    
    성능 (Week 10 로컬 환경):
    - 1M~10M triple: incremental reasoning < 1초
    - Spark 분산 처리: Phase 6 stretch goal (1B 처리 추후 평가)
    - 병렬도: 로컬 4 cores (또는 Spark 8 workers optional)
    """
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.sc = spark.sparkContext
    
    async def perform_distributed_reasoning(
        self,
        rdf_file_path: str,
        reasoning_rules: List[str] = None
    ) -> Dict:
        """
        분산 환경에서 OWL 추론 수행
        """
        
        import time
        start_time = time.time()
        
        if reasoning_rules is None:
            reasoning_rules = [
                "rdfs_subclass_transitivity",
                "owl_sameas_symmetry",
                "rdfs_domain_range"
            ]
        
        # 1. RDF 파일을 RDD로 로드
        rdd = self._load_rdf_as_rdd(rdf_file_path)
        
        # 2. 파티션당 처리 (병렬)
        inferred_rdd = rdd.flatMap(
            lambda triples: self._apply_reasoning_rules(
                triples,
                reasoning_rules
            )
        )
        
        # 3. 중복 제거
        unique_rdd = inferred_rdd.distinct()
        
        # 4. 결과 수집 및 저장
        inferred_count = unique_rdd.count()
        
        # 5. 결과를 파일/DB에 저장
        await self._save_inferred_triples(unique_rdd)
        
        elapsed = time.time() - start_time
        
        return {
            "inferredTripleCount": inferred_count,
            "processingTimeSeconds": round(elapsed),
            "partitionCount": rdd.getNumPartitions(),
            "reasoningRules": reasoning_rules,
            "status": "success" if inferred_count > 0 else "no_inferences"
        }
    
    def _load_rdf_as_rdd(self, file_path: str) -> RDD:
        """
        RDF 파일을 Spark RDD로 로드
        
        형식: NTriples, Turtle, RDF/XML 지원
        """
        # 파일을 텍스트로 로드
        text_rdd = self.sc.textFile(file_path, minPartitions=64)
        
        # 파싱
        parsed_rdd = text_rdd.map(
            lambda line: self._parse_nt_triple(line)
        ).filter(lambda x: x is not None)
        
        return parsed_rdd
    
    def _parse_nt_triple(self, line: str) -> tuple:
        """N-Triples 포맷 파싱"""
        try:
            line = line.strip()
            if not line or line.startswith('#'):
                return None
            
            # N-Triples: <subject> <predicate> <object> .
            parts = line.rstrip(' .').split(' ', 2)
            if len(parts) != 3:
                return None
            
            return tuple(parts)
        except:
            return None
    
    def _apply_reasoning_rules(
        self,
        triples: List[tuple],
        rules: List[str]
    ) -> List[tuple]:
        """
        각 파티션의 triple들에 추론 규칙 적용
        """
        inferred = []
        
        # 파티션 내 triple 인덱싱
        triple_index = {
            "by_subject": {},
            "by_predicate": {},
            "by_object": {}
        }
        
        for s, p, o in triples:
            if s not in triple_index["by_subject"]:
                triple_index["by_subject"][s] = []
            triple_index["by_subject"][s].append((s, p, o))
            
            if p not in triple_index["by_predicate"]:
                triple_index["by_predicate"][p] = []
            triple_index["by_predicate"][p].append((s, p, o))
            
            if o not in triple_index["by_object"]:
                triple_index["by_object"][o] = []
            triple_index["by_object"][o].append((s, p, o))
        
        # 규칙 적용
        for rule in rules:
            if rule == "rdfs_subclass_transitivity":
                inferred.extend(
                    self._apply_subclass_rule(triple_index)
                )
            elif rule == "owl_sameas_symmetry":
                inferred.extend(
                    self._apply_sameas_rule(triple_index)
                )
            elif rule == "rdfs_domain_range":
                inferred.extend(
                    self._apply_domain_range_rule(triple_index)
                )
        
        return triples + inferred
    
    def _apply_subclass_rule(self, triple_index: Dict) -> List[tuple]:
        """Subclass transitivity 규칙"""
        inferred = []
        rdfs_subclass = "<http://www.w3.org/2000/01/rdf-schema#subClassOf>"
        
        predicates = triple_index["by_predicate"].get(rdfs_subclass, [])
        
        # A subClassOf B, B subClassOf C => A subClassOf C
        for s1, p1, o1 in predicates:
            for s2, p2, o2 in predicates:
                if o1 == s2:  # B가 일치
                    inferred.append((s1, rdfs_subclass, o2))
        
        return inferred
    
    def _apply_sameas_rule(self, triple_index: Dict) -> List[tuple]:
        """OWL sameAs symmetry 규칙"""
        inferred = []
        owl_sameas = "<http://www.w3.org/2002/07/owl#sameAs>"
        
        predicates = triple_index["by_predicate"].get(owl_sameas, [])
        
        # A sameAs B => B sameAs A
        for s, p, o in predicates:
            inferred.append((o, owl_sameas, s))
        
        return inferred
    
    def _apply_domain_range_rule(self, triple_index: Dict) -> List[tuple]:
        """Domain/Range 규칙"""
        inferred = []
        # ... 구현 ...
        return inferred
    
    async def _save_inferred_triples(self, rdd: RDD):
        """추론 결과를 DB에 저장"""
        df = rdd.toDF(["subject", "predicate", "object"])
        
        df.write \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://localhost:5432/ontology") \
            .option("dbtable", "inferred_triples") \
            .option("user", "postgres") \
            .option("password", "password") \
            .mode("append") \
            .save()
```

### 성공 기준 (Task 10-2)
- [ ] Spark RDD 처리: 로컬 4 cores 또는 8+ workers (선택)
- [ ] 분산 추론: 병렬 파티션 처리 (64 파티션 구조)
- [ ] 성능: 1M~10M triple 범위에서 < 1초
  - **참고**: 1B triple 분산 처리는 Phase 6 벤치마크 대상
- [ ] 확장성: 영향받는 파티션만 재계산 (부분 업데이트)

---

## Task 10-3: 추론 결과 캐싱 및 미리 계산

**기간**: 07-31 ~ 08-02 (2일)

### 구현 항목

```python
# src/backend/app/services/reasoning_cache.py
class ReasoningResultCache:
    """
    추론 결과를 사전 계산하고 캐싱하여
    쿼리 시 즉시 응답 가능하게 함
    """
    
    async def precompute_and_cache_inferences(
        self,
        reasoning_level: str = "OWL-RL"
    ) -> Dict:
        """
        전체 추론을 사전 계산하고 캐싱
        
        실행:
        - 매일 자정에 배치로 실행
        - 또는 사용자 요청 시 온디맨드 실행
        """
        
        import time
        start_time = time.time()
        
        # 1. 분산 추론 실행
        reasoning_result = await self.distributed_reasoner.perform_distributed_reasoning(
            rdf_file_path="s3://ontology-data/rdf/full-graph.nt",
            reasoning_rules=self._get_rules_for_level(reasoning_level)
        )
        
        # 2. 추론 결과를 계층적으로 캐싱
        await self._cache_inferences_hierarchically(
            reasoning_result
        )
        
        elapsed = time.time() - start_time
        
        return {
            "status": "precomputed",
            "reasoningLevel": reasoning_level,
            "inferredTripleCount": reasoning_result['inferredTripleCount'],
            "totalComputationTimeSeconds": round(elapsed),
            "cacheSize": await self._get_cache_size()
        }
    
    async def _cache_inferences_hierarchically(self, inferences: Dict):
        """
        계층적으로 캐싱:
        - L1: 메모리 (자주 접근하는 개념)
        - L2: Redis (중간 크기 개념)
        - L3: PostgreSQL (전체 추론 결과)
        """
        
        # 접근 빈도 기반으로 L1/L2 선택
        for concept, inferred_relations in inferences.items():
            access_freq = await self._get_concept_access_frequency(concept)
            
            if access_freq > 100:  # 자주 접근
                await self.l1_cache.set(concept, inferred_relations)
            elif access_freq > 10:  # 가끔 접근
                await self.l2_redis.set(
                    f"inferences:{concept}",
                    json.dumps(inferred_relations),
                    ex=86400  # 24시간 TTL
                )
            else:  # 거의 접근 안 함
                # L3: DB에는 모두 저장 (쿼리 기반 접근)
                pass
```

### 성공 기준 (Task 10-3)
- [ ] 계층적 캐싱: L1(메모리) → L2(Redis) → L3(DB)
- [ ] 미리 계산: 배치 작업으로 사전 계산
- [ ] 캐시 효율: 개념 접근 빈도 기반 계층 배정
- [ ] 조회 성능: 캐시 히트 시 < 50ms

---

## 성능 벤치마크

| 시나리오 | 목표 | 측정 기준 |
|---------|------|----------|
| 1M~10M triple 추론 (Week 10) | < 1초 | 증분 추론 (로컬) |
| 1B triple 추론 (Phase 6 stretch) | < 30초 | 분산 추론 평가 (Spark optional) |
| 캐시 히트 응답 | < 50ms | 쿼리 응답 |
| 메모리 사용 | < 500MB | incremental L1/L2 캐시 |

---

**다음 단계**: Week 11-12 (Streaming & Production Operations)
