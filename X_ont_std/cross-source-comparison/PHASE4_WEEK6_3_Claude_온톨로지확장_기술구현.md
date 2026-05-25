# PHASE4 WEEK6-3 Claude: 온톨로지 확장 기술 구현 가이드

**작성일**: 2026-05-25  
**대상**: Claude 팀의 온톨로지 확장 백엔드 구현  
**관점**: SPARQL, RDF 처리, API 설계, 성능 최적화

---

## 1. 개요: Claude 팀의 역할

기존 PHASE4 Week 6에서 Claude가 구현한 것:
- ✅ SPARQL 쿼리 최적화 (50ms)
- ✅ 비동기 파이프라인 (30% 성능 개선)
- ✅ 쿼리 캐싱 & 인덱싱 (75% 히트율)

**Week 7/8에 추가할 것**:
- 온톨로지 확장을 위한 **RDF 병합 엔진**
- **외부 온톨로지 임포트 및 스키마 검증**
- **Provenance 추적 및 Lineage 관리**
- **충돌 감지 및 해결 제안 엔진**

**PHASE5에 넘길 것**:
- LLM 기반 자동 매핑 (Claude API 통합)
- OWL Reasoning 엔진 (추론 최적화)
- 대규모 분산 처리 (Spark 통합)

---

## 2. Week 7 Claude의 핵심 구현 (RDF 기반)

### 2.1 온톨로지 확장 API 구현

#### 1) RDF 그래프 이웃 탐색 API
```python
# app/services/rdf_graph_navigator.py

from rdflib import Graph, Namespace
from typing import List, Dict, Tuple
import asyncio

class RDFGraphNavigator:
    """RDF 그래프 기반 1-hop/2-hop 이웃 탐색"""
    
    def __init__(self, graph: Graph, cache_service):
        self.graph = graph
        self.cache = cache_service
        self.visited = set()
    
    async def get_neighborhood(self,
                              entity_uri: str,
                              hops: int = 1,
                              limit: int = 50) -> Dict:
        """
        entity_uri를 중심으로 주변 노드 반환
        
        Args:
            entity_uri: 중심 엔티티 URI
            hops: 탐색 깊이 (1 or 2)
            limit: 반환할 최대 노드 수
        
        Returns:
            {
                "nodes": [{ "id", "uri", "label", "type", "degree", "isExternal" }],
                "edges": [{ "source", "target", "predicate", "isExternal", "confidence" }],
                "loadTime": int (ms)
            }
        """
        import time
        start_time = time.time()
        
        # 캐시 확인
        cache_key = f"neighborhood:{entity_uri}:{hops}:{limit}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # 노드/엣지 수집
        nodes_dict = {}
        edges = []
        
        # BFS로 이웃 탐색
        queue = [(entity_uri, 0)]  # (uri, current_depth)
        visited = {entity_uri}
        
        while queue and len(nodes_dict) < limit:
            current_uri, depth = queue.pop(0)
            
            if depth > hops:
                continue
            
            # 현재 노드 정보 수집
            if current_uri not in nodes_dict:
                node_info = self._get_node_info(current_uri)
                nodes_dict[current_uri] = node_info
            
            # 1-hop 이웃 탐색
            for s, p, o in self.graph.triples((None, None, None)):
                if s == URIRef(current_uri):
                    # Forward edge
                    if o not in visited:
                        visited.add(str(o))
                        queue.append((str(o), depth + 1))
                        edges.append({
                            "source": current_uri,
                            "target": str(o),
                            "predicate": str(p),
                            "isExternal": self._is_external(str(o))
                        })
                
                elif o == URIRef(current_uri):
                    # Backward edge
                    if s not in visited:
                        visited.add(str(s))
                        queue.append((str(s), depth + 1))
                        edges.append({
                            "source": str(s),
                            "target": current_uri,
                            "predicate": str(p),
                            "isExternal": self._is_external(str(s))
                        })
        
        result = {
            "nodes": list(nodes_dict.values()),
            "edges": edges[:limit],
            "loadTime": int((time.time() - start_time) * 1000)
        }
        
        # 캐시 저장 (TTL: 300s)
        self.cache.set(cache_key, result, ttl=300)
        
        return result
    
    def _get_node_info(self, uri: str) -> Dict:
        """노드의 메타데이터 추출"""
        uri_ref = URIRef(uri)
        
        # 라벨 추출
        labels = list(self.graph.objects(uri_ref, RDFS.label))
        label = str(labels[0]) if labels else uri.split('/')[-1]
        
        # 타입 판별
        types = list(self.graph.objects(uri_ref, RDF.type))
        if not types:
            # Blank node 또는 literal인지 확인
            if isinstance(uri_ref, Literal):
                node_type = "literal"
            elif str(uri_ref).startswith("_:"):
                node_type = "bnode"
            else:
                node_type = "resource"
        else:
            node_type = "resource"
        
        # 차수(degree) 계산
        out_degree = len(list(self.graph.triples((uri_ref, None, None))))
        in_degree = len(list(self.graph.triples((None, None, uri_ref))))
        degree = out_degree + in_degree
        
        # 외부 리소스 판별
        is_external = self._is_external(uri)
        
        # 출처 판별
        source = self._determine_source(uri)
        
        return {
            "id": uri,
            "uri": uri,
            "label": label,
            "type": node_type,
            "degree": degree,
            "isExternal": is_external,
            "source": source
        }
    
    def _is_external(self, uri: str) -> bool:
        """외부 URI 판별"""
        external_prefixes = [
            "http://dbpedia.org/",
            "http://www.wikidata.org/",
            "https://www.wikidata.org/"
        ]
        return any(uri.startswith(prefix) for prefix in external_prefixes)
    
    def _determine_source(self, uri: str) -> str:
        """리소스의 출처 판별"""
        if "dbpedia" in uri:
            return "dbpedia"
        elif "wikidata" in uri:
            return "wikidata"
        elif uri.startswith("http://example.com/"):
            return "internal"
        else:
            return "rdf_file"
```

#### 2) Import Preview 생성 API
```python
# app/services/ontology_import_preview.py

from rdflib import Graph, RDF, RDFS, OWL
from typing import List, Dict, Set
import hashlib

class OntologyImportPreview:
    """RDF 임포트 전 미리보기 생성"""
    
    def __init__(self, current_graph: Graph, cache_service):
        self.current_graph = current_graph
        self.cache = cache_service
    
    async def generate_preview(self, 
                               import_file: bytes,
                               file_format: str = "xml") -> Dict:
        """
        임포트할 RDF 파일의 미리보기 생성
        
        Returns:
            {
                "fileInfo": { "name", "size", "triples", "format" },
                "statistics": { "newClasses", "newProperties", "newTriples", "externalUris" },
                "conflicts": [ { "type", "externalUri", "externalValue", "internalUri", "severity" } ],
                "autoMappings": [ { "externalUri", "suggestedInternalId", "confidence" } ]
            }
        """
        
        # 1. 임포트 파일 파싱
        import_graph = Graph()
        import_graph.parse(data=import_file, format=file_format)
        
        # 2. 파일 정보
        file_info = {
            "name": "imported_ontology.rdf",  # 실제로는 filename 전달받음
            "size": len(import_file),
            "triples": len(import_graph),
            "format": file_format
        }
        
        # 3. 통계 계산
        statistics = self._calculate_statistics(import_graph)
        
        # 4. 충돌 감지
        conflicts = self._detect_conflicts(import_graph)
        
        # 5. 자동 매핑 생성
        auto_mappings = self._generate_auto_mappings(import_graph)
        
        return {
            "fileInfo": file_info,
            "statistics": statistics,
            "conflicts": conflicts,
            "autoMappings": auto_mappings
        }
    
    def _calculate_statistics(self, import_graph: Graph) -> Dict:
        """임포트할 데이터의 통계"""
        
        # 새로운 클래스 수
        new_classes = set()
        for s, p, o in import_graph.triples((None, RDF.type, RDFS.Class)):
            if not self._exists_in_current(s):
                new_classes.add(s)
        
        # 새로운 속성 수
        new_properties = set()
        for prop in import_graph.predicates():
            if not self._exists_in_current(None, prop, None):
                new_properties.add(prop)
        
        # 외부 URI 수
        external_uris = 0
        for s, p, o in import_graph.triples((None, None, None)):
            if self._is_external_uri(str(s)):
                external_uris += 1
        
        return {
            "newClasses": len(new_classes),
            "newProperties": len(new_properties),
            "newTriples": len(import_graph),
            "externalUris": external_uris
        }
    
    def _detect_conflicts(self, import_graph: Graph) -> List[Dict]:
        """스키마 충돌 감지"""
        conflicts = []
        
        # 1. Label conflict: 같은 label, 다른 URI
        labels_external = {}
        for s, p, o in import_graph.triples((None, RDFS.label, None)):
            label = str(o)
            if label not in labels_external:
                labels_external[label] = []
            labels_external[label].append(str(s))
        
        for label, uris in labels_external.items():
            if len(uris) > 1:
                conflicts.append({
                    "type": "label_conflict",
                    "externalUri": uris[0],
                    "externalValue": label,
                    "severity": "warning"
                })
        
        # 2. URI conflict: 같은 URI, 다른 타입
        uri_types = {}
        for s, p, o in import_graph.triples((None, RDF.type, None)):
            uri = str(s)
            if uri not in uri_types:
                uri_types[uri] = []
            uri_types[uri].append(str(o))
        
        for uri, types in uri_types.items():
            if self._exists_in_current(uri) and len(set(types)) > 1:
                conflicts.append({
                    "type": "type_conflict",
                    "externalUri": uri,
                    "severity": "error"
                })
        
        return conflicts
    
    def _generate_auto_mappings(self, import_graph: Graph) -> List[Dict]:
        """자동 매핑 제안 생성"""
        mappings = []
        
        # Label 기반 자동 매핑
        for s, p, o in import_graph.triples((None, RDFS.label, None)):
            external_uri = str(s)
            external_label = str(o)
            
            # 내부 엔티티 중 동일 라벨 찾기
            for internal_s, _, internal_o in self.current_graph.triples((None, RDFS.label, None)):
                if str(internal_o) == external_label:
                    confidence = 0.9  # Label exact match
                    mappings.append({
                        "externalUri": external_uri,
                        "externalLabel": external_label,
                        "suggestedInternalId": str(internal_s),
                        "suggestedRelationship": "owl:sameAs",
                        "confidence": confidence
                    })
                    break
        
        return mappings
    
    def _exists_in_current(self, s=None, p=None, o=None) -> bool:
        """현재 그래프에 존재 여부"""
        return len(list(self.current_graph.triples((s, p, o)))) > 0
    
    def _is_external_uri(self, uri: str) -> bool:
        """외부 URI 판별"""
        external_prefixes = [
            "http://dbpedia.org/",
            "http://www.wikidata.org/"
        ]
        return any(uri.startswith(prefix) for prefix in external_prefixes)
```

### 2.2 온톨로지 매핑 저장 API

```python
# app/services/ontology_mapping_manager.py

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict

class OntologyMappingManager:
    """온톨로지 매핑 저장 및 관리"""
    
    def __init__(self, db: Session, graph_service):
        self.db = db
        self.graph_service = graph_service
    
    async def save_mapping(self, 
                          external_uri: str,
                          internal_entity_id: str,
                          relationship_type: str,  # owl:sameAs, skos:exactMatch, etc.
                          confidence: float,
                          evidence: List[str],
                          created_by: str) -> Dict:
        """
        온톨로지 매핑 저장
        
        매핑 레코드 저장 + RDF 그래프 업데이트 + Provenance 기록
        """
        
        # 1. 매핑 레코드 저장
        from app.models import OntologyMapping
        
        mapping = OntologyMapping(
            external_uri=external_uri,
            internal_entity_id=internal_entity_id,
            relationship_type=relationship_type,
            confidence=confidence,
            evidence=evidence,
            created_by=created_by,
            approval_status="pending",
            created_at=datetime.utcnow()
        )
        self.db.add(mapping)
        self.db.commit()
        
        # 2. RDF 그래프에 매핑 추가
        self._add_to_rdf_graph(external_uri, internal_entity_id, relationship_type)
        
        # 3. Provenance 기록
        self._record_provenance(mapping.id, "mapping_created")
        
        return {
            "id": mapping.id,
            "status": "created",
            "timestamp": mapping.created_at.isoformat(),
            "mappingUri": f"http://example.com/mapping/{mapping.id}"
        }
    
    def _add_to_rdf_graph(self, 
                         external_uri: str,
                         internal_entity_id: str,
                         relationship_type: str):
        """RDF 그래프에 매핑 관계 추가"""
        from rdflib import URIRef, Namespace
        
        # 관계 URI 생성
        relationship_map = {
            "owl:sameAs": "http://www.w3.org/2002/07/owl#sameAs",
            "skos:exactMatch": "http://www.w3.org/2004/02/skos/core#exactMatch",
            "skos:closeMatch": "http://www.w3.org/2004/02/skos/core#closeMatch",
            "skos:broader": "http://www.w3.org/2004/02/skos/core#broader",
            "skos:narrower": "http://www.w3.org/2004/02/skos/core#narrower"
        }
        
        relationship_uri = relationship_map.get(relationship_type, relationship_type)
        
        # 그래프에 triple 추가
        self.graph_service.add_triple(
            URIRef(internal_entity_id),
            URIRef(relationship_uri),
            URIRef(external_uri)
        )
    
    def _record_provenance(self, mapping_id: str, action: str):
        """매핑 변경 이력 기록"""
        from app.models import ProvenanceLog
        
        log = ProvenanceLog(
            entity_id=mapping_id,
            action=action,
            timestamp=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()
```

---

## 3. Week 8 Claude의 핵심 구현 (E2E 통합)

### 3.1 온톨로지 병합 엔진

```python
# app/services/ontology_merge_engine.py

class OntologyMergeEngine:
    """외부 온톨로지를 내부 그래프에 병합"""
    
    async def merge(self,
                   import_graph: Graph,
                   mappings: List[Dict],
                   conflict_resolutions: Dict) -> Dict:
        """
        1. 매핑 적용
        2. 충돌 해결
        3. 그래프 병합
        4. Provenance 기록
        """
        
        merge_result = {
            "newNodes": 0,
            "newEdges": 0,
            "conflictsResolved": 0,
            "jobId": self._generate_job_id()
        }
        
        # 1. 매핑 적용
        for mapping in mappings:
            external_uri = mapping["externalUri"]
            internal_id = mapping["internalEntityId"]
            
            # 외부 URI의 모든 triple을 내부 엔티티로 리매핑
            for s, p, o in import_graph.triples((URIRef(external_uri), None, None)):
                # 내부 엔티티로 대체
                self.current_graph.add((
                    URIRef(internal_id),
                    p,
                    o
                ))
                merge_result["newEdges"] += 1
        
        # 2. 충돌 해결
        for conflict_id, resolution in conflict_resolutions.items():
            if resolution == "use_external":
                # 외부 값 사용
                pass
            elif resolution == "use_internal":
                # 내부 값 유지
                pass
            merge_result["conflictsResolved"] += 1
        
        # 3. 그래프 저장
        self.current_graph.serialize(destination=self.graph_path)
        
        # 4. Provenance 기록
        self._record_merge(merge_result)
        
        return merge_result
```

### 3.2 SPARQL 검증 API

```python
# app/services/sparql_validation.py

class SPARQLValidator:
    """병합 후 SPARQL로 검증"""
    
    async def validate(self, job_id: str, queries: List[str]) -> Dict:
        """
        병합된 그래프에서 SPARQL 쿼리 실행
        모든 쿼리가 성공하면 병합 완료
        """
        
        results = {
            "queriesRun": len(queries),
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        for query in queries:
            try:
                result = self.graph.query(query)
                results["passed"] += 1
                results["details"].append({
                    "query": query[:100],  # 처음 100자만
                    "status": "success",
                    "resultCount": len(result)
                })
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "query": query[:100],
                    "status": "error",
                    "error": str(e)
                })
        
        return results
```

---

## 4. PHASE5 Claude의 준비 (LLM 기반 자동 매핑)

### 4.1 LLM 기반 매핑 추천 엔진 (PHASE5 Week 9)

```python
# app/services/llm_mapping_recommender.py (PHASE5)

class LLMMapingRecommender:
    """Claude API를 이용한 자동 매핑 추천"""
    
    def __init__(self, openai_client):
        self.llm = openai_client
    
    async def recommend_mappings(self,
                                external_ontology: Graph,
                                internal_ontology: Graph,
                                top_k: int = 10) -> List[Dict]:
        """
        LLM을 이용해 외부 온톨로지의 각 개념에 대해
        내부 엔티티와의 의미 매핑 추천
        
        Returns:
            [
                {
                    "externalUri": "...",
                    "externalLabel": "...",
                    "suggestedInternalId": "...",
                    "suggestedRelationship": "owl:sameAs",
                    "confidence": 0.92,
                    "evidence": ["Label similarity", "Semantic description", ...]
                }
            ]
        """
        
        recommendations = []
        
        # 외부 온톨로지의 모든 클래스/엔티티 추출
        external_entities = self._extract_entities(external_ontology)
        
        for external_entity in external_entities:
            # LLM 호출
            prompt = f"""
            외부 온톨로지의 개념: {external_entity['label']}
            설명: {external_entity.get('description', 'N/A')}
            
            내부 온톨로지의 후보 엔티티들:
            {self._format_candidates(internal_ontology)}
            
            가장 유사한 내부 엔티티를 선택하고, 관계 유형(owl:sameAs, skos:exactMatch 등)을 제시하시오.
            신뢰도 점수(0-1)도 함께 제시하시오.
            """
            
            response = await self.llm.call(prompt)
            
            recommendation = self._parse_llm_response(response, external_entity)
            if recommendation["confidence"] >= 0.7:  # 신뢰도 70% 이상만
                recommendations.append(recommendation)
        
        return sorted(recommendations, key=lambda x: x["confidence"], reverse=True)[:top_k]
    
    def _extract_entities(self, graph: Graph) -> List[Dict]:
        """온톨로지에서 엔티티 추출"""
        entities = []
        
        for s, p, o in graph.triples((None, RDFS.label, None)):
            entity = {
                "uri": str(s),
                "label": str(o)
            }
            
            # description 추출
            descriptions = list(graph.objects(s, RDFS.comment))
            if descriptions:
                entity["description"] = str(descriptions[0])
            
            entities.append(entity)
        
        return entities
    
    def _format_candidates(self, internal_ontology: Graph) -> str:
        """내부 온톨로지의 후보 엔티티들을 텍스트로 포맷"""
        candidates = []
        
        for s, p, o in internal_ontology.triples((None, RDFS.label, None)):
            candidates.append(f"- {str(o)} ({str(s)})")
        
        return "\n".join(candidates[:20])  # 처음 20개만
    
    def _parse_llm_response(self, response: str, external_entity: Dict) -> Dict:
        """LLM 응답 파싱"""
        # 실제 구현에서는 정규식이나 JSON 파싱으로 추출
        return {
            "externalUri": external_entity["uri"],
            "externalLabel": external_entity["label"],
            "suggestedInternalId": "...",  # LLM 응답에서 추출
            "suggestedRelationship": "owl:sameAs",
            "confidence": 0.85,  # LLM 응답에서 추출
            "evidence": ["LLM semantic analysis"]
        }
```

---

## 5. 성능 고려사항 (Week 7/8)

### 5.1 캐싱 전략

| 캐시 레벨 | 대상 | TTL | 크기 제한 |
|------|------|-----|----------|
| L1 (메모리) | 최근 이웃 조회 (1k 노드 이상) | 300s | 100MB |
| L2 (Redis) | 임포트 preview 결과 | 3600s | 1GB |
| L3 (GraphDB) | 병합된 그래프의 인덱스 | 영구 | 그래프 크기 |

### 5.2 응답 시간 목표

| 작업 | 목표 | 달성 방법 |
|------|------|----------|
| 1-hop 이웃 조회 | < 300ms | 메모리 캐시 + 인덱스 |
| Import preview | < 2s | 스트리밍 파싱 + 비동기 처리 |
| 그래프 병합 | < 5s (1M triple) | 배치 처리 + 병렬화 |
| SPARQL 검증 | < 10s | 최적화된 쿼리 |

---

## 6. 데이터 모델 (PostgreSQL + RDF)

### 6.1 온톨로지 매핑 테이블

```sql
CREATE TABLE ontology_mappings (
    id SERIAL PRIMARY KEY,
    external_uri VARCHAR(1024) NOT NULL,
    internal_entity_id VARCHAR(256) NOT NULL,
    relationship_type VARCHAR(100),  -- owl:sameAs, skos:exactMatch, etc.
    confidence FLOAT,  -- 0.0 ~ 1.0
    evidence JSONB,  -- ["evidence1", "evidence2", ...]
    created_by VARCHAR(256),
    approval_status VARCHAR(32),  -- pending, approved, rejected
    created_at TIMESTAMP,
    approved_at TIMESTAMP,
    created_hash VARCHAR(64) UNIQUE  -- 중복 방지
);

CREATE TABLE provenance_logs (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(256),
    action VARCHAR(50),  -- imported, mapped, updated, approved, rejected
    performed_by VARCHAR(256),
    details TEXT,
    timestamp TIMESTAMP,
    import_job_id VARCHAR(256)
);

CREATE TABLE import_jobs (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(256),
    file_size INT,
    triple_count INT,
    status VARCHAR(32),  -- pending, in_progress, completed, failed
    result JSONB,  -- preview, statistics, conflicts
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

---

## 7. PHASE4 vs PHASE5 역할 분담

### Claude의 역할 확대

| 단계 | 주요 기능 | 기술 스택 |
|------|---------|----------|
| **PHASE4 Week 7** | RDF 이웃 조회, 매핑 저장, Import preview | RDFlib, PostgreSQL, Async |
| **PHASE4 Week 8** | 병합 엔진, SPARQL 검증, Provenance | 위 + GraphDB 인덱싱 |
| **PHASE5 Week 9** | LLM 매핑 추천 | 위 + OpenAI/Claude API |
| **PHASE5 Week 10** | OWL Reasoning | 위 + Owlready2 또는 Pellet |
| **PHASE5 Week 11** | 대규모 분산 처리 | 위 + Spark RDD |

---

## 8. 요약: Claude 팀의 온톨로지 확장 기술 로드맵

### PHASE4 목표
> **RDF/SPARQL 기반 온톨로지 확장의 핵심 백엔드 엔진 구축**

- 이웃 탐색 API (1-hop/2-hop)
- Import preview + 자동 매핑
- 온톨로지 병합 엔진
- SPARQL 기반 검증
- Provenance 추적

### PHASE5 목표
> **자동화·추론·대규모 처리로 고도화**

- LLM 기반 자동 매핑 (정확도 85%+)
- OWL Reasoning 엔진
- 분산 SPARQL 쿼리 (Spark)
- 실시간 스트리밍 처리
- 자동 성능 튜닝

---

**다음 단계**: Week 7/8 지시서 (Claude.md)에서 이 기술 구현을 구체적으로 명시
