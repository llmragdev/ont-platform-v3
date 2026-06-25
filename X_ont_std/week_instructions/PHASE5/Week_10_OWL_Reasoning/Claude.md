# Phase 5 Week 10: OWL 추론 엔진 (백엔드)
## Claude (Backend) 수행 지시서

**기간**: 2026-07-29 ~ 2026-08-02 (5일)  
**할당**: 80% (주당 24-30시간)  
**목표**: OWL 기반 의미 추론 엔진 구현 및 추론 결과 캐싱

---

## 개요

Phase 5의 자동 매핑 기능을 바탕으로, **OWL(Web Ontology Language) 추론 엔진**을 구현합니다. `rdfs:subClassOf`, `owl:sameAs`, `owl:inverseOf` 등의 관계를 활용하여 명시적이지 않은 새로운 개념 관계를 자동으로 도출합니다.

### Week 10의 3가지 핵심 기능

1. **제한된 OWL 추론** (Task 10-1): RDFS + OWL subset 구현
   - RDFS: subClassOf, subPropertyOf, domain, range
   - OWL: sameAs, inverseOf, TransitiveProperty
   - SKOS: broader, narrower, exactMatch, closeMatch
2. **추론 결과 검증** (Task 10-2): 도출된 추론 결과의 신뢰도 및 증거 제시
3. **추론 성능 최적화** (Task 10-3): 1M~10M triple 대상 추론 (Week 10 목표)

---

## 🔧 환경 설정

```bash
# Conda 환경 활성화
conda activate claud_be

# 의존성 설치
pip install owlrl rdflib sparqlwrapper

# 개발 서버
uvicorn main:app --reload --port 8001

# 테스트
pytest tests/phase5/week10_owl_reasoning_test.py -v
```

---

## Task 10-1: OWL Level 2 추론 엔진

**기간**: 07-29 ~ 07-30 (1.5일)

### 구현 항목

```python
# src/backend/app/services/owl_reasoning_engine.py
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef
from owlrl import DeductiveClosure, OWLRL_RL_Semantics
from typing import List, Dict, Set, Tuple

class OWLReasoningEngine:
    """
    OWL/RDFS 기반 의미 추론 엔진
    
    지원 추론:
    - RDFS: subClassOf, subPropertyOf, domain, range
    - OWL: sameAs, inverseOf, transitiveProperty
    - SKOS: broader, narrower, related
    """
    
    def __init__(self, rdf_graph: Graph):
        self.graph = rdf_graph
        self.inferred_graph = Graph()
        self.reasoning_rules = self._initialize_rules()
    
    def _initialize_rules(self) -> Dict:
        """추론 규칙 초기화"""
        return {
            "rdfs_subclass_transitivity": self._apply_subclass_transitivity,
            "rdfs_subproperty_transitivity": self._apply_subproperty_transitivity,
            "owl_sameas_symmetry": self._apply_sameas_symmetry,
            "owl_sameas_transitivity": self._apply_sameas_transitivity,
            "owl_inversef_symmetry": self._apply_inverse_symmetry,
            "rdfs_domain_range": self._apply_domain_range,
            "skos_hierarchical": self._apply_skos_hierarchical
        }
    
    async def perform_reasoning(
        self,
        reasoning_level: str = "OWL-Lite-Subset"
    ) -> Dict:
        """
        전체 그래프에 대한 추론 수행
        
        Args:
            reasoning_level: "RDFS", "OWL-Lite-Subset" (권장), "SKOS-Subset"
        
        Returns:
            {
                "inferredTripleCount": 15000,
                "newConceptRelationships": 450,
                "processingTimeMs": 28000,
                "inferenceRules": {
                    "rdfs_subclass_transitivity": 120,
                    "owl_sameas_symmetry": 200,
                    ...
                }
            }
        """
        
        import time
        start_time = time.time()
        
        # 1. RDFS 추론
        rdfs_inferences = await self._apply_rdfs_reasoning()
        
        # 2. OWL 추론 (제한된 subset)
        owl_inferences = {}
        if reasoning_level in ["OWL-Lite-Subset"]:
            owl_inferences = await self._apply_owl_reasoning(reasoning_level)
        
        # 3. SKOS 추론
        skos_inferences = await self._apply_skos_reasoning()
        
        # 4. 추론 결과 통합
        all_inferences = {
            **rdfs_inferences,
            **owl_inferences,
            **skos_inferences
        }
        
        # 5. 통계
        total_inferred = sum(
            len(inferences) for inferences in all_inferences.values()
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "reasoningLevel": reasoning_level,
            "inferredTripleCount": total_inferred,
            "newConceptRelationships": len(all_inferences.get("owl_sameas_symmetry", [])),
            "processingTimeMs": round(processing_time),
            "inferenceRules": {
                name: len(inferences)
                for name, inferences in all_inferences.items()
            },
            "inferenceSamples": self._extract_samples(all_inferences)
        }
    
    async def _apply_rdfs_reasoning(self) -> Dict:
        """RDFS 추론 적용"""
        inferences = {
            "rdfs_subclass_transitivity": [],
            "rdfs_subproperty_transitivity": [],
            "rdfs_domain_range": []
        }
        
        # 1. Transitivity of rdfs:subClassOf
        inferences["rdfs_subclass_transitivity"] = (
            await self._apply_subclass_transitivity()
        )
        
        # 2. Transitivity of rdfs:subPropertyOf
        inferences["rdfs_subproperty_transitivity"] = (
            await self._apply_subproperty_transitivity()
        )
        
        # 3. Domain and Range constraints
        inferences["rdfs_domain_range"] = (
            await self._apply_domain_range()
        )
        
        return inferences
    
    async def _apply_subclass_transitivity(self) -> List[Tuple]:
        """
        rdfs:subClassOf의 추이성 적용
        
        A rdfs:subClassOf B
        B rdfs:subClassOf C
        => A rdfs:subClassOf C
        """
        inferences = []
        
        # 모든 subClassOf 관계 수집
        subclass_relations = list(
            self.graph.subject_objects(RDFS.subClassOf)
        )
        
        # Floyd-Warshall 알고리즘으로 추이성 계산
        closure = self._compute_transitive_closure(subclass_relations)
        
        # 이미 존재하는 관계 제외
        for subject, obj in closure:
            if (subject, RDFS.subClassOf, obj) not in self.graph:
                inferences.append((subject, RDFS.subClassOf, obj))
                self.inferred_graph.add((subject, RDFS.subClassOf, obj))
        
        return inferences
    
    async def _apply_sameas_symmetry(self) -> List[Tuple]:
        """
        owl:sameAs의 대칭성 적용
        
        A owl:sameAs B => B owl:sameAs A
        """
        inferences = []
        
        sameas_relations = list(self.graph.subject_objects(OWL.sameAs))
        
        for subject, obj in sameas_relations:
            # 역방향 관계가 없으면 추가
            if (obj, OWL.sameAs, subject) not in self.graph:
                inferences.append((obj, OWL.sameAs, subject))
                self.inferred_graph.add((obj, OWL.sameAs, subject))
        
        return inferences
    
    async def _apply_sameas_transitivity(self) -> List[Tuple]:
        """
        owl:sameAs의 추이성 적용
        
        A owl:sameAs B
        B owl:sameAs C
        => A owl:sameAs C
        """
        inferences = []
        
        sameas_relations = list(self.graph.subject_objects(OWL.sameAs))
        closure = self._compute_transitive_closure(sameas_relations)
        
        for subject, obj in closure:
            if (subject, OWL.sameAs, obj) not in self.graph:
                inferences.append((subject, OWL.sameAs, obj))
                self.inferred_graph.add((subject, OWL.sameAs, obj))
        
        return inferences
    
    async def _apply_owl_reasoning(self, level: str) -> Dict:
        """OWL 레벨별 추론 (OWL-Lite-Subset만 지원)"""
        inferences = {
            "owl_sameas_symmetry": [],
            "owl_sameas_transitivity": [],
            "owl_inverse_symmetry": []
        }
        
        # OWL-Lite-Subset: sameAs 대칭성/추이성만 지원
        # Phase 5 목표 범위: 1M~10M triple, incremental reasoning
        if level == "OWL-Lite-Subset":
            inferences["owl_sameas_symmetry"] = (
                await self._apply_sameas_symmetry()
            )
            inferences["owl_sameas_transitivity"] = (
                await self._apply_sameas_transitivity()
            )
        
        return inferences
    
    async def _apply_skos_reasoning(self) -> Dict:
        """SKOS 추론"""
        inferences = {
            "skos_hierarchical": [],
            "skos_mapping": []
        }
        
        SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
        
        # broader/narrower의 추이성
        broader_relations = list(
            self.graph.subject_objects(SKOS.broader)
        )
        closure = self._compute_transitive_closure(broader_relations)
        
        for subject, obj in closure:
            if (subject, SKOS.broader, obj) not in self.graph:
                inferences["skos_hierarchical"].append(
                    (subject, SKOS.broader, obj)
                )
        
        return inferences
    
    def _compute_transitive_closure(
        self,
        relations: List[Tuple]
    ) -> Set[Tuple]:
        """Floyd-Warshall로 추이적 폐포 계산"""
        
        # 그래프 구성
        graph_dict = {}
        nodes = set()
        
        for subject, obj in relations:
            if subject not in graph_dict:
                graph_dict[subject] = set()
            graph_dict[subject].add(obj)
            nodes.add(subject)
            nodes.add(obj)
        
        # Floyd-Warshall
        for k in nodes:
            for i in nodes:
                if i in graph_dict:
                    for j in graph_dict.get(i, set()).copy():
                        if j in graph_dict:
                            if i not in graph_dict[j]:
                                graph_dict[j] = graph_dict.get(j, set()) | graph_dict[i]
        
        # 결과 변환
        result = set()
        for source, targets in graph_dict.items():
            for target in targets:
                result.add((source, target))
        
        return result
    
    async def _apply_domain_range(self) -> List[Tuple]:
        """Domain/Range 제약 적용"""
        inferences = []
        
        # rdfs:domain 적용
        domain_triples = list(
            self.graph.subject_objects(RDFS.domain)
        )
        
        for prop, domain_class in domain_triples:
            # prop의 subject는 모두 domain_class의 인스턴스
            for subject, _ in self.graph.subject_objects(prop):
                if (subject, RDF.type, domain_class) not in self.graph:
                    inferences.append((subject, RDF.type, domain_class))
        
        return inferences
    
    async def _apply_inverse_symmetry(self) -> List[Tuple]:
        """owl:inverseOf 대칭성"""
        inferences = []
        
        inverse_props = list(
            self.graph.subject_objects(OWL.inverseOf)
        )
        
        for prop1, prop2 in inverse_props:
            # P1 inverseOf P2 => P2 inverseOf P1
            if (prop2, OWL.inverseOf, prop1) not in self.graph:
                inferences.append((prop2, OWL.inverseOf, prop1))
        
        return inferences
    
    def _extract_samples(self, inferences: Dict, limit: int = 5) -> Dict:
        """추론 결과 샘플 추출"""
        samples = {}
        for rule, triples in inferences.items():
            samples[rule] = [
                {
                    "subject": str(t[0]),
                    "predicate": str(t[1]),
                    "object": str(t[2])
                }
                for t in triples[:limit]
            ]
        return samples
```

### 성공 기준 (Task 10-1)
- [ ] RDFS 추론: subClassOf, subPropertyOf, domain/range
- [ ] OWL 추론: sameAs 대칭성/추이성, inverseOf
- [ ] SKOS 추론: broader/narrower 추이성
- [ ] 추론 결과: 명시적으로 도출된 새로운 관계

---

## Task 10-2: 추론 결과 검증 및 증거

**기간**: 07-30 ~ 07-31 (1.5일)

### 구현 항목

```python
# src/backend/app/services/inference_validation.py
from typing import Dict, List

class InferenceValidator:
    """
    도출된 추론 결과의 신뢰도 및 근거 제시
    """
    
    async def validate_inferred_triple(
        self,
        subject: str,
        predicate: str,
        obj: str,
        inference_chain: List[str]
    ) -> Dict:
        """
        추론된 triple의 신뢰도 계산
        
        inference_chain: 추론 규칙의 체인
            ["rdfs_subclass_transitivity", "owl_sameas_symmetry", ...]
        """
        
        # 신뢰도 = 1.0 / (체인 길이 + 1)
        # 직접 triple: 1.0, 1-hop 추론: 0.5, 2-hop: 0.33, ...
        confidence = 1.0 / (len(inference_chain) + 1)
        
        return {
            "subject": subject,
            "predicate": predicate,
            "object": obj,
            "confidence": round(confidence, 3),
            "inferenceChain": inference_chain,
            "evidence": self._explain_inference(
                inference_chain
            ),
            "isExplicit": len(inference_chain) == 0
        }
    
    def _explain_inference(self, chain: List[str]) -> List[str]:
        """추론 과정 설명"""
        explanations = {
            "rdfs_subclass_transitivity": "상위 클래스의 상위 클래스",
            "owl_sameas_symmetry": "동일 개념의 역방향 관계",
            "owl_sameas_transitivity": "동일 개념의 추이적 관계",
            "rdfs_domain_range": "속성의 정의역/치역 규칙",
            "skos_hierarchical": "개념 계층 구조의 추이성"
        }
        
        return [
            explanations.get(rule, rule)
            for rule in chain
        ]
```

### 성공 기준 (Task 10-2)
- [ ] 신뢰도 계산: 추론 체인 길이 기반
- [ ] 증거 제시: 어떤 규칙으로 도출됐는지 명확
- [ ] 추론 근거: 명시적 vs 추론된 구분

---

## Task 10-3: 추론 성능 최적화

**기간**: 07-31 ~ 08-02 (2일)

### 구현 항목

```python
# src/backend/app/services/incremental_reasoning.py
class IncrementalReasoningEngine:
    """
    증분 추론: 전체 그래프 재계산 대신 변경된 부분만 추론
    """
    
    async def apply_incremental_reasoning(
        self,
        new_triples: List[Tuple],
        removed_triples: List[Tuple]
    ) -> Dict:
        """
        변경된 triple에만 추론 적용 (전체 재계산 회피)
        
        목표: 1M~10M triple 범위에서 증분 추론 < 1초
        Week 10 Phase 5 목표: 변경 영향 범위만 재계산
        """
        
        import time
        start_time = time.time()
        
        # 1. 영향받을 노드 식별
        affected_nodes = self._identify_affected_nodes(
            new_triples,
            removed_triples
        )
        
        # 2. 부분 재계산
        new_inferences = await self._recompute_affected_inferences(
            affected_nodes
        )
        
        elapsed = time.time() - start_time
        
        return {
            "newTriples": len(new_triples),
            "removedTriples": len(removed_triples),
            "affectedNodes": len(affected_nodes),
            "newInferences": len(new_inferences),
            "processingTimeMs": round(elapsed * 1000)
        }
    
    def _identify_affected_nodes(
        self,
        new_triples: List[Tuple],
        removed_triples: List[Tuple]
    ) -> Set[str]:
        """영향받을 노드 식별 (연쇄 영향 1-2 hop)"""
        affected = set()
        
        for s, p, o in new_triples + removed_triples:
            affected.add(s)
            affected.add(o)
            
            # 1-hop 이웃
            for neighbor in self.graph.successors(s):
                affected.add(neighbor)
            for neighbor in self.graph.predecessors(o):
                affected.add(neighbor)
        
        return affected
    
    async def _recompute_affected_inferences(
        self,
        affected_nodes: Set[str]
    ) -> List[Tuple]:
        """영향받는 노드에 대해서만 추론 재계산"""
        new_inferences = []
        
        for node in affected_nodes:
            # 이 노드를 포함하는 추론 재계산
            local_inferences = await self._compute_local_inferences(node)
            new_inferences.extend(local_inferences)
        
        return new_inferences
```

### 성공 기준 (Task 10-3)
- [ ] 증분 추론: 변경된 부분만 재계산 (affected_nodes 식별)
- [ ] 성능: 1M~10M triple 범위에서 증분 추론 < 1초
  - **참고**: 1B triple 성능은 Phase 6 stretch goal (기술 검증 후 평가)
  - **구현 초점**: Incremental/Delta reasoning으로 영향받는 노드만 처리
- [ ] 메모리: < 500MB (incremental, 전체 재계산 회피)

---

## 엔터프라이즈 아키텍처 패턴

### 1. 증분 추론 (Incremental Reasoning)
- **Full Reasoning의 문제**: 매번 전체 그래프 재처리 → O(V+E) 복잡도
- **Incremental Reasoning의 이점**: 변경 영향 범위만 식별 → O(neighbors) 복잡도
- **구현**: `_identify_affected_nodes()`로 1-2 hop 이웃만 재계산
- **효과**: 1M~10M triple에서도 1초 이내 성능 달성

### 2. Named Graph 기반 추론 결과 격리
```sparql
-- Staging 그래프에 추론 결과 저장
INSERT DATA {
    GRAPH <http://ontology.platform/graphs/inferred/session_{id}> {
        ?inferredTriple rdf:type rdf:Statement ;
            rdf:subject ?s ;
            rdf:predicate ?p ;
            rdf:object ?o ;
            ont:confidenceScore ?conf ;
            prov:wasGeneratedBy <owl_reasoning_engine> ;
            prov:generatedAtTime ?timestamp
    }
}
-- 검증 후 production 그래프로 MOVE (Phase 5 Week 11)
```

### 3. 배치 트랜잭션 (Batch Transaction)
- 추론 결과 저장 시 1000개 triple 단위 배치 처리
- `apply_incremental_reasoning()` 결과를 SPARQL INSERT DATA 한 번으로 처리
- 개별 INSERT 루프 회피 → 네트워크 라운드 트립 500배 감소

---

## 데이터베이스 스키마

```sql
CREATE TABLE inferred_triples (
    id VARCHAR(36) PRIMARY KEY,
    subject VARCHAR(500) NOT NULL,
    predicate VARCHAR(500) NOT NULL,
    object VARCHAR(500) NOT NULL,
    confidence FLOAT,
    inference_chain JSONB,
    evidence TEXT,
    reasoning_level VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_subject (subject),
    INDEX idx_predicate (predicate),
    INDEX idx_confidence (confidence)
);
```

---

**다음 단계**: Week 11 (Streaming & 거버넌스)
