# Phase 4 Week 4: RDF + External Ontology
## Claude (Backend) 수행 지시서

**기간**: 2026-08-19 ~ 2026-09-01 (2주)  
**할당**: 80% (주당 24-30시간)  
**목표**: RDF 양방향 변환, 외부 온톨로지 import, SPARQL API 완성

---

## Task 4-1: RDFConverter (양방향 변환)

**기간**: 08-19 ~ 08-25 (4일)  
**목표**: 내부 모델 ↔ RDF 트리플 양방향 변환

### 구현 사항

```python
# app/services/rdf_converter.py

from rdflib import Graph, Namespace, URIRef, Literal
from typing import Dict, List, Any

class RDFConverter:
    """내부 모델 ↔ RDF 양방향 변환"""
    
    def __init__(self, base_uri: str = "http://ont.example.com/"):
        self.base_uri = base_uri
        self.ONT = Namespace(f"{base_uri}ontology/")
        self.SCHEMA = Namespace("http://schema.org/")
    
    def entity_to_rdf(self, entity: Dict[str, Any]) -> Graph:
        """엔티티 → RDF 트리플 변환"""
        g = Graph()
        
        # 기본 트리플: rdf:type, rdfs:label, rdfs:comment
        entity_uri = URIRef(f"{self.base_uri}entities/{entity['entity_id']}")
        
        g.add((
            entity_uri,
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            self.ONT[entity['entity_type']]
        ))
        
        # 메타데이터 추가
        g.add((
            entity_uri,
            URIRef("http://www.w3.org/2000/01/rdf-schema#label"),
            Literal(entity.get('name', ''))
        ))
        
        # 관계 추가
        for relation in entity.get('relationships', []):
            target_uri = URIRef(f"{self.base_uri}entities/{relation['target_id']}")
            g.add((
                entity_uri,
                self.ONT[relation['predicate']],
                target_uri
            ))
        
        return g
    
    def schema_to_rdf(self, schema: Dict[str, Any]) -> Graph:
        """스키마 → RDF 온톨로지 변환"""
        g = Graph()
        
        # EntityTypeDefinition → rdfs:Class
        for entity_type in schema['entity_types']:
            class_uri = self.ONT[entity_type['name']]
            g.add((class_uri, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                   URIRef("http://www.w3.org/2000/01/rdf-schema#Class")))
            
            # 상속 관계
            if 'parent_type' in entity_type:
                parent_uri = self.ONT[entity_type['parent_type']]
                g.add((class_uri,
                       URIRef("http://www.w3.org/2000/01/rdf-schema#subClassOf"),
                       parent_uri))
        
        # PropertyDefinition → rdf:Property
        for entity_type in schema['entity_types']:
            for prop in entity_type['properties']:
                prop_uri = self.ONT[prop['name']]
                g.add((prop_uri,
                       URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                       URIRef("http://www.w3.org/2000/01/rdf-schema#Property")))
        
        return g
    
    def rdf_to_entity(self, graph: Graph, entity_uri: str) -> Dict[str, Any]:
        """RDF 트리플 → 엔티티 변환"""
        uri = URIRef(entity_uri)
        
        entity = {
            'entity_id': str(uri).split('/')[-1],
            'name': str(graph.value(uri, URIRef("http://www.w3.org/2000/01/rdf-schema#label"))),
            'relationships': []
        }
        
        # 관계 추출
        for s, p, o in graph.triples((uri, None, None)):
            if p.startswith(self.base_uri):
                entity['relationships'].append({
                    'predicate': str(p).split('/')[-1],
                    'target_id': str(o).split('/')[-1]
                })
        
        return entity
    
    def sparql_query(self, graph: Graph, query: str) -> List[Dict[str, Any]]:
        """SPARQL 쿼리 실행"""
        results = graph.query(query)
        
        output = []
        for row in results:
            output.append({
                col: str(value) for col, value in zip(results.vars, row)
            })
        
        return output
```

### DB 테이블 설계

```sql
-- rdf_graphs (RDF 그래프 저장)
CREATE TABLE rdf_graphs (
    graph_id UUID PRIMARY KEY,
    entity_id UUID UNIQUE,
    graph_data TEXT NOT NULL,  -- RDF/Turtle 형식
    format VARCHAR DEFAULT 'turtle',  -- turtle, rdf/xml, n3
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);

-- sparql_queries (SPARQL 쿼리 저장/캐시)
CREATE TABLE sparql_queries (
    query_id UUID PRIMARY KEY,
    query_text TEXT NOT NULL,
    result_format VARCHAR DEFAULT 'json',
    cached_result TEXT,
    cache_valid_until TIMESTAMP,
    executed_at TIMESTAMP,
    execution_time_ms INT
);

CREATE INDEX idx_rdf_entity_id ON rdf_graphs(entity_id);
CREATE INDEX idx_sparql_executed_at ON sparql_queries(executed_at DESC);
```

### 테스트 계획 (8개)

```python
def test_entity_to_rdf_basic():
    """단일 엔티티 → RDF"""

def test_entity_to_rdf_with_relationships():
    """관계 포함 엔티티 → RDF"""

def test_schema_to_rdf_inheritance():
    """상속 관계 포함 스키마 → RDF"""

def test_rdf_to_entity_parsing():
    """RDF → 엔티티 역변환"""

def test_sparql_select_query():
    """SPARQL SELECT 쿼리"""

def test_sparql_construct_query():
    """SPARQL CONSTRUCT 쿼리 (새로운 RDF 생성)"""

def test_rdf_format_conversion():
    """RDF 형식 변환 (Turtle ↔ RDF/XML)"""

def test_circular_relationship_handling():
    """순환 관계 처리"""
```

### 체크리스트

- [ ] RDFConverter 클래스 구현 (entity_to_rdf, schema_to_rdf, rdf_to_entity)
- [ ] SPARQL 쿼리 실행 메서드 구현
- [ ] Alembic 마이그레이션 (rdf_graphs, sparql_queries)
- [ ] 8개 테스트 작성 및 통과

---

## Task 4-2: OntologyImporter (외부 소스)

**기간**: 08-25 ~ 08-31 (4일)  
**목표**: DBpedia, Wikidata, 로컬 RDF 파일 import

### 구현 사항

```python
# app/services/ontology_importer.py

from rdflib import Graph, URIRef
from typing import Optional, List, Dict, Any
import httpx

class OntologyImporter:
    """외부 온톨로지 import"""
    
    async def import_from_dbpedia(
        self, 
        resource_uri: str,
        domain_id: str
    ) -> Dict[str, Any]:
        """DBpedia 리소스 import
        
        Example:
            import_from_dbpedia("http://dbpedia.org/resource/Machine_Learning", "ai_domain")
        """
        async with httpx.AsyncClient() as client:
            # DBpedia SPARQL 엔드포인트
            query = f"""
            SELECT ?property ?object
            WHERE {{
                <{resource_uri}> ?property ?object
            }}
            LIMIT 100
            """
            
            response = await client.get(
                "http://dbpedia.org/sparql",
                params={"query": query, "format": "json"}
            )
            
            bindings = response.json()["results"]["bindings"]
            
            # 엔티티 생성
            entity = {
                'entity_id': resource_uri.split('/')[-1],
                'domain_id': domain_id,
                'source': 'dbpedia',
                'external_uri': resource_uri,
                'properties': {}
            }
            
            for binding in bindings:
                prop_name = binding['property']['value'].split('#')[-1]
                prop_value = binding['object']['value']
                entity['properties'][prop_name] = prop_value
            
            return entity
    
    async def import_from_wikidata(
        self,
        wikidata_id: str,  # Q123456
        domain_id: str
    ) -> Dict[str, Any]:
        """Wikidata 아이템 import"""
        async with httpx.AsyncClient() as client:
            # Wikidata JSON API
            response = await client.get(
                f"https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.json"
            )
            
            data = response.json()["entities"][wikidata_id]
            
            entity = {
                'entity_id': wikidata_id,
                'domain_id': domain_id,
                'source': 'wikidata',
                'label': data['labels']['en']['value'],
                'description': data.get('descriptions', {}).get('en', {}).get('value'),
                'properties': {}
            }
            
            # 속성 추출
            for prop_id, claims in data.get('claims', {}).items():
                for claim in claims:
                    if claim['type'] == 'statement':
                        prop_name = claim['mainsnak'].get('property', '')
                        entity['properties'][prop_name] = str(claim['mainsnak'].get('datavalue'))
            
            return entity
    
    def import_from_rdf_file(
        self,
        file_path: str,
        domain_id: str,
        format: str = 'turtle'
    ) -> List[Dict[str, Any]]:
        """로컬 RDF 파일 import
        
        Args:
            file_path: RDF 파일 경로
            domain_id: 도메인
            format: 'turtle', 'rdf/xml', 'n3'
        """
        graph = Graph()
        graph.parse(file_path, format=format)
        
        entities = []
        
        # 각 리소스를 엔티티로 변환
        for subject in graph.subjects():
            entity = {
                'entity_id': str(subject).split('/')[-1],
                'domain_id': domain_id,
                'source': f'rdf_file:{file_path}',
                'external_uri': str(subject),
                'properties': {}
            }
            
            for predicate, obj in graph.predicate_objects(subject):
                prop_name = str(predicate).split('#')[-1]
                entity['properties'][prop_name] = str(obj)
            
            entities.append(entity)
        
        return entities
    
    async def merge_entities(
        self,
        primary_entity: Dict[str, Any],
        secondary_entity: Dict[str, Any],
        merge_rule: str = 'primary_first'  # 'primary_first' | 'secondary_first' | 'merge_all'
    ) -> Dict[str, Any]:
        """두 엔티티 merge (중복 제거)"""
        merged = primary_entity.copy()
        
        if merge_rule == 'merge_all':
            # 모든 속성 병합 (충돌 시 primary 우선)
            for key, value in secondary_entity['properties'].items():
                if key not in merged['properties']:
                    merged['properties'][key] = value
        
        merged['sources'] = [
            primary_entity.get('source'),
            secondary_entity.get('source')
        ]
        
        return merged
```

### DB 테이블 설계

```sql
-- imported_entities (외부 source 엔티티)
CREATE TABLE imported_entities (
    imported_id UUID PRIMARY KEY,
    entity_id UUID,
    source VARCHAR NOT NULL,  -- dbpedia, wikidata, rdf_file
    external_uri VARCHAR UNIQUE,
    metadata JSONB,  -- 추가 메타데이터
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);

-- entity_mappings (내부 엔티티 ↔ 외부 리소스 매핑)
CREATE TABLE entity_mappings (
    mapping_id UUID PRIMARY KEY,
    internal_entity_id UUID NOT NULL,
    external_entity_id VARCHAR NOT NULL,
    external_source VARCHAR NOT NULL,  -- dbpedia, wikidata
    confidence FLOAT,  -- 0-1 매칭 신뢰도
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (internal_entity_id) REFERENCES entities(id)
);

CREATE INDEX idx_imported_source ON imported_entities(source);
CREATE INDEX idx_entity_mappings_internal ON entity_mappings(internal_entity_id);
CREATE INDEX idx_entity_mappings_external ON entity_mappings(external_entity_id);
```

### 테스트 계획 (9개)

```python
def test_import_from_dbpedia():
    """DBpedia 리소스 import"""

def test_import_from_wikidata():
    """Wikidata 아이템 import"""

def test_import_from_rdf_file():
    """로컬 RDF 파일 import"""

def test_import_schema_hierarchy():
    """상속 관계 있는 스키마 import"""

def test_merge_duplicate_entities():
    """중복 엔티티 merge"""

def test_import_with_conflict_resolution():
    """속성 충돌 해결"""

def test_batch_import_performance():
    """대량 import 성능 (1000+ 엔티티)"""

def test_import_invalid_rdf():
    """잘못된 RDF 파일 처리"""

def test_external_uri_deduplication():
    """외부 URI 중복 제거"""
```

### 체크리스트

- [ ] DBpedia importer 구현
- [ ] Wikidata importer 구현
- [ ] RDF 파일 importer 구현
- [ ] 엔티티 merge 로직
- [ ] Alembic 마이그레이션 (imported_entities, entity_mappings)
- [ ] 9개 테스트 작성 및 통과

---

## Task 4-3: SPARQL API 엔드포인트

**기간**: 08-31 ~ 09-01 (2일)  
**목표**: SPARQL 쿼리 API 및 성능 최적화

### 구현 사항

```python
# app/api/sparql_endpoints.py

from fastapi import APIRouter, Query, BackgroundTasks
from app.services.rdf_converter import RDFConverter
from typing import Optional
import time

router = APIRouter(prefix="/api/sparql", tags=["sparql"])

@router.post("/query")
async def execute_sparql(
    query: str = Query(..., description="SPARQL 쿼리"),
    format: str = Query("json", description="json | xml | csv"),
    timeout: int = Query(30, description="쿼리 타임아웃 (초)"),
    cache: bool = Query(True, description="캐시 사용 여부")
) -> Dict[str, Any]:
    """SPARQL SELECT/CONSTRUCT/DESCRIBE 쿼리 실행"""
    
    # 캐시 확인
    if cache:
        cached_result = await cache_service.get(f"sparql:{query}")
        if cached_result:
            return {"source": "cache", "data": cached_result}
    
    # 쿼리 실행
    start = time.time()
    try:
        converter = RDFConverter()
        # 현재 모든 엔티티의 RDF 그래프 병합
        merged_graph = await merge_all_rdf_graphs()
        results = converter.sparql_query(merged_graph, query)
        elapsed = time.time() - start
        
        # 캐시 저장 (5분 TTL)
        if cache:
            await cache_service.set(f"sparql:{query}", results, ttl=300)
        
        return {
            "source": "query",
            "data": results,
            "execution_time_ms": int(elapsed * 1000)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/batch")
async def batch_sparql_queries(
    queries: List[str],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """여러 SPARQL 쿼리 일괄 실행"""
    
    results = []
    
    for query in queries:
        try:
            result = await execute_sparql(query=query)
            results.append({"query": query, "status": "success", "data": result})
        except Exception as e:
            results.append({"query": query, "status": "failed", "error": str(e)})
    
    return {"batch_results": results}

@router.get("/describe/{entity_id}")
async def describe_entity(entity_id: str) -> Dict[str, Any]:
    """엔티티 RDF 설명 (SPARQL DESCRIBE)"""
    
    query = f"""
    DESCRIBE <http://ont.example.com/entities/{entity_id}>
    """
    
    return await execute_sparql(query=query, format="rdf/xml")

@router.post("/suggest")
async def suggest_query(
    entity_id: str,
    query_type: str = Query("related", description="related | lineage | properties")
) -> Dict[str, Any]:
    """SPARQL 쿼리 제안 생성"""
    
    suggestions = {
        "related": f"""
            SELECT ?related WHERE {{
                ?related ?predicate <http://ont.example.com/entities/{entity_id}> .
            }} LIMIT 10
        """,
        "lineage": f"""
            SELECT ?source ?target WHERE {{
                ?source ?p* <http://ont.example.com/entities/{entity_id}> .
            }} LIMIT 10
        """,
        "properties": f"""
            SELECT ?property ?value WHERE {{
                <http://ont.example.com/entities/{entity_id}> ?property ?value .
            }}
        """
    }
    
    query = suggestions.get(query_type, suggestions["related"])
    return await execute_sparql(query=query)
```

### 성능 최적화

```python
# app/services/sparql_cache_service.py

class SPARQLCacheService:
    """SPARQL 쿼리 캐싱 및 인덱싱"""
    
    async def cache_rdf_index(self):
        """RDF 인덱스 사전 생성"""
        # 주요 쿼리 패턴 사전 계산
        # - 엔티티별 관계 (degree)
        # - 혈통 깊이
        # - 속성 빈도
    
    async def optimize_graph_structure(self):
        """RDF 그래프 구조 최적화"""
        # 자주 사용되는 triple 패턴 사전 인덱싱
        # quad-store 구조 활용
```

### 테스트 계획 (8개)

```python
def test_sparql_select_endpoint():
    """SELECT 쿼리 API"""

def test_sparql_construct_endpoint():
    """CONSTRUCT 쿼리 API"""

def test_sparql_describe_endpoint():
    """DESCRIBE 쿼리 API"""

def test_sparql_query_caching():
    """쿼리 캐시 동작"""

def test_batch_query_execution():
    """배치 쿼리 실행"""

def test_sparql_timeout_handling():
    """타임아웃 처리"""

def test_complex_sparql_performance():
    """복합 SPARQL 성능 (< 500ms)"""

def test_sparql_error_handling():
    """잘못된 쿼리 에러 처리"""
```

### 체크리스트

- [ ] SPARQL Query API 구현
- [ ] Batch Query API 구현
- [ ] SPARQL 캐싱 전략
- [ ] 8개 테스트 작성 및 통과
- [ ] 성능 벤치마크 (< 500ms)

---

## 📋 일일 진행 계획

### 08-19 (화) ~ 08-25 (월)
- [ ] RDFConverter 클래스 구현
- [ ] Alembic 마이그레이션 (rdf_graphs, sparql_queries)
- [ ] 8개 RDF 변환 테스트

### 08-26 (화) ~ 08-31 (일)
- [ ] DBpedia/Wikidata/RDF 파일 importer 구현
- [ ] Alembic 마이그레이션 (imported_entities, entity_mappings)
- [ ] 9개 import 테스트

### 09-01 (월)
- [ ] SPARQL API 엔드포인트 구현
- [ ] 8개 API 테스트
- [ ] 성능 벤치마크 및 최적화

---

## 🎯 성공 기준

✅ RDFConverter 양방향 변환 완성 (8개 테스트)  
✅ OntologyImporter 3가지 소스 모두 구현 (9개 테스트)  
✅ SPARQL API 엔드포인트 5개 구현 (8개 테스트)  
✅ 전체 25개 통합 테스트 통과  
✅ SPARQL 쿼리 성능 < 500ms  
✅ 코드 커버리지 ≥ 90%

---

## 📞 상호작용

**Codex와의 연계**:
- SPARQL Workbench UI 설계 (Task 4-3 완료 후)
- RDF 그래프 시각화 프로토타입

**Antigravity와의 연계**:
- SPARQL 성능 벤치마크 (Task 4-3 완료 후)
- 25개 성능 시나리오 검증

---

**상태**: Task 4-1~4-3 준비 완료  
**예상 완료**: 2026-09-01  
**다음 단계**: Week 5-8 Frontend + Performance Implementation

---

## 📝 최종 보고서 작성 가이드

**완료 후 다음 형식으로 최종 보고서를 작성하여 제출하세요.**

```markdown
# Phase 4 Week 4: Claude (Backend - RDF) 완료 보고서

**기간**: 2026-08-19 ~ 2026-09-01 (2주)
**할당**: 80% (주당 24-30시간)
**상태**: ✅ 완료
**날짜**: [실제 보고서 작성 날짜]

---

## 📋 작업 요약

### Task 4-1: RDFConverter 양방향 변환 (8개 테스트)
- ✅ RDFConverter 클래스 구현
- ✅ entity_to_rdf() 메서드 구현
- ✅ rdf_to_entity() 메서드 구현
- ✅ 복잡한 관계 변환 처리
- ✅ 8개 통합 테스트 작성 및 통과

### Task 4-2: OntologyImporter (3가지 소스, 9개 테스트)
- ✅ DBpediaImporter 구현
- ✅ WikidataImporter 구현
- ✅ RDFFileImporter 구현
- ✅ ImportMetadata 저장 (entity_mappings 테이블)
- ✅ 9개 통합 테스트 작성 및 통과

### Task 4-3: SPARQL API 엔드포인트 (8개 테스트)
- ✅ SPARQL Query API 구현 (GET /api/sparql/query)
- ✅ SPARQL Batch Query API 구현 (POST /api/sparql/batch)
- ✅ SPARQL 캐싱 전략 적용
- ✅ 성능 벤치마크 < 500ms 달성
- ✅ 8개 통합 테스트 작성 및 통과

---

## 📊 테스트 결과

| Task | 테스트 개수 | 결과 | 커버리지 |
|------|-----------|------|---------|
| Task 4-1 RDFConverter | 8개 | ✅ 8/8 통과 | ≥90% |
| Task 4-2 OntologyImporter | 9개 | ✅ 9/9 통과 | ≥90% |
| Task 4-3 SPARQL API | 8개 | ✅ 8/8 통과 | ≥90% |
| **합계** | **25개** | **✅ 25/25 통과** | **≥90%** |

**성능 벤치마크**:
- RDFConverter 변환 시간: < 50ms (100K 트리플)
- SPARQL SELECT 쿼리: < 200ms
- SPARQL CONSTRUCT 쿼리: < 400ms
- DBpedia 임포트: < 2초 (1000 엔티티)

---

## 🔧 생성/수정 파일

### 생성된 파일
- `app/services/rdf_converter.py` - RDFConverter 클래스
- `app/services/ontology_importer.py` - OntologyImporter 및 3가지 Importer 구현
- `app/api/sparql_endpoints.py` - SPARQL API 엔드포인트
- `tests/test_phase4_week4_rdf.py` - 25개 통합 테스트

### Alembic 마이그레이션 (DB)
- `alembic/versions/004_create_rdf_tables.py` - rdf_graphs 테이블 및 인덱스
- `alembic/versions/005_create_ontology_import_tables.py` - imported_entities, entity_mappings 테이블
- `alembic/versions/006_create_sparql_cache_tables.py` - sparql_query_cache 테이블

---

## 📈 주요 성과

✅ **양방향 RDF 변환**: 내부 모델 ↔ RDF 트리플 100% 호환
✅ **3가지 외부 온톨로지 임포트**: DBpedia, Wikidata, 로컬 RDF 파일
✅ **SPARQL 쿼리 지원**: SELECT, CONSTRUCT, ASK, DESCRIBE 모두 지원
✅ **성능 기준 달성**: 모든 쿼리 < 500ms (100K 트리플 기준)
✅ **테스트 커버리지**: 25/25 통과, ≥90% 코드 커버리지

---

## ⏭️ 다음 단계

### 즉시 필요 (Week 4.5)
- [ ] Alembic 마이그레이션 실행 (PostgreSQL 테이블 생성)
- [ ] 외부 온톨로지 import 배치 작업 (DBpedia/Wikidata)
- [ ] SPARQL 쿼리 캐싱 레이어 Redis 통합

### Week 5-8 준비
- [ ] SPARQL Workbench 프론트엔드 (Codex)
- [ ] 대규모 RDF 시각화 최적화 (Antigravity)

---

## 🔗 관련 문서

- 지시서: `week_instructions/PHASE4/Week_4_RDF/Claude.md`
- RDF 성능 기준선: `ont_platform/v4/PHASE4_RDF_PERFORMANCE_BASELINE.md` (Antigravity 산출물)

---

**보고자**: Claude (Backend - RDF)
**완료 시각**: [실제 완료 시각] KST
```

**⚠️ 반드시 따르기**:

1. **저장 위치** (필수)
   - ✅ 정해진 위치: `task_logs/claude/YYYYMMDD_PHASE4_WEEK4_Claude_Complete.md`
   - 파일명 형식: `YYYYMMDD_HHMM_작업명.md`
   - 예: `20260901_1830_PHASE4_WEEK4_Claude_Complete.md`
   - ❌ 금지: `ont_platform/` 폴더에 저장하지 말 것

2. **템플릿 작성**:
   - "기간", "할당", "상태", "날짜" → 실제 작업 기록으로 채우기
   - "Task 4-1~4-3" 섹션 → 실제 완료 항목만 체크
   - "테스트 결과" 테이블 → 실제 테스트 통과 결과 입력
   - "생성된 파일" → 실제로 생성된 파일 경로 입력
