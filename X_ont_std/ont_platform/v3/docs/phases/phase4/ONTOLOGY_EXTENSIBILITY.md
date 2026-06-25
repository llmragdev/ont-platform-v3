# Phase 4: 온톨로지 데이터 모델링 다양성 지원

**기간**: 2026-07-21 ~ 2026-09-30 (10주)  
**상태**: 📋 계획 (Phase 3 완료 후 시작)  
**근거**: 2026-05-20 온톨로지 데이터 스타일 다양성 이슈

---

## 🎯 배경 및 문제점

### 이슈 제기 (2026-05-20)
> **사용자 피드백**: "온톨로지 기반 데이터 구성할 때 다양한 스타일이 존재하는데 우리 시스템도 그럴까?"

**분석 결과**:
- 현재 시스템은 **Document + Graph 혼합 모델**로 제한됨
- RDF Triple, 계층적 구조, 시맨틱 웹 패턴 미지원
- 도메인별 스키마 유연성 부족
- 메타데이터(버전, 감사, 유효성) 부재

### 영향도
```
현재 제약으로 인한 문제:
├─ 외부 온톨로지 (DBpedia, Wikidata) 통합 불가
├─ 도메인별 복잡한 관계 표현 제한
├─ 데이터 혈통(Lineage) 추적 불가
└─ RDF 기반 시스템과의 상호운용성 없음
```

---

## 🏗️ Phase 4 구조 (4주 단계별 계획)

### Week 1-2 (07-21 ~ 08-04): 온톨로지 스키마 확장

#### 목표
다양한 데이터 모델 지원을 위한 기본 구조 설계

#### 1️⃣ 멀티 온톨로지 스타일 지원

**현재 구조**:
```json
{
  "doc_id": "ai-voucher-2025",
  "entities": [
    {
      "id": "P001",
      "type": "PROJECT",
      "properties": { "name": "...", "budget": 100000000 }
    }
  ],
  "relationships": [
    { "id": "R001", "from_id": "P001", "to_id": "...", "type": "leads" }
  ]
}
```

**개선 계획** (app/models/ontology.py):
```python
class OntologyStyle(str, Enum):
    """온톨로지 데이터 모델 스타일"""
    DOCUMENT = "document"          # 현재 (JSON 문서)
    RDF_TRIPLE = "rdf_triple"      # RDF 삼중쌍
    PROPERTY_GRAPH = "property_graph"  # Property Graph (Neo4j 스타일)
    SEMANTIC_WEB = "semantic_web"  # 시맨틱 웹 (OWL, URI)
    HIERARCHICAL = "hierarchical"  # 계층적 (Tree)
    MULTI_TYPED = "multi_typed"    # 다중 타입 (한 엔티티 여러 타입)

class DomainSchema(BaseModel):
    """도메인별 스키마 정의"""
    domain_id: str
    ontology_style: OntologyStyle
    entity_types: List[EntityType]
    relation_types: List[RelationType]
    constraints: List[SchemaConstraint]
    version: str = "1.0"
    created_at: datetime
    updated_at: datetime

class EntityType(BaseModel):
    """엔티티 타입 정의 (도메인별)"""
    name: str  # e.g., "PROJECT"
    display_name: str
    description: str
    properties: Dict[str, PropertyDefinition]
    parent_types: List[str] = []  # 상속 지원
    metadata_fields: List[str] = ["created_by", "created_at", "version"]

class RelationType(BaseModel):
    """관계 타입 정의"""
    name: str  # e.g., "leads", "manages"
    display_name: str
    from_type: str  # 출발 엔티티 타입
    to_type: str    # 도착 엔티티 타입
    cardinality: str  # "1:1", "1:N", "N:M"
    directed: bool = True
    properties: Dict[str, PropertyDefinition] = {}  # 관계 속성
```

#### 2️⃣ 도메인별 온톨로지 스타일 선택

```yaml
ai-voucher-2025:
  style: property_graph
  reason: "복잡한 다중 주체(PERSON, ORGANIZATION) 관계"
  
manufacturing:
  style: hierarchical
  reason: "조직 구조, BOM(Bill of Materials) 계층"
  
knowledge-graph:
  style: semantic_web
  reason: "외부 온톨로지(DBpedia) 통합 필요"

order-tracking:
  style: rdf_triple
  reason: "Linked Data 호환성 필요"
```

#### 산출물
- [ ] `app/models/ontology_schema.py` (스타일 정의)
- [ ] `app/models/domain_schema.py` (도메인별 스키마)
- [ ] `app/repositories/schema_repository.py` (스키마 저장소)
- [ ] 통합 테스트 10개

---

### Week 3 (08-05 ~ 08-18): 메타데이터 및 감사 시스템

#### 목표
데이터 혈통(Lineage), 버전 관리, 감사 추적 완성도

#### 3️⃣ 엔티티 메타데이터 확장

```python
class EntityMetadata(BaseModel):
    """엔티티 메타데이터"""
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime
    version: int
    status: str  # active, archived, deprecated
    tags: List[str]  # 검색용
    lineage: LineageInfo  # 데이터 출처
    annotations: Dict[str, Any]  # 자유형 메모
    
class LineageInfo(BaseModel):
    """데이터 혈통 추적"""
    source_type: str  # "user_input", "import", "derived"
    source_id: str    # 원본 엔티티/문서 ID
    transformations: List[Transformation]
    import_metadata: Optional[ImportMetadata]  # 외부 소스 정보
    
class Transformation(BaseModel):
    """데이터 변환 기록"""
    operation: str  # "merge", "split", "enrich"
    performed_by: str
    performed_at: datetime
    input_ids: List[str]
    output_id: str
    parameters: Dict[str, Any]
```

#### 4️⃣ 감시 및 버전 관리

```python
class EntityVersion(BaseModel):
    """엔티티 버전 관리"""
    entity_id: str
    version: int
    data: Dict[str, Any]
    changed_fields: List[str]
    change_reason: str
    changed_by: str
    changed_at: datetime
    is_current: bool = True

class AuditLog(BaseModel):
    """감사 로그"""
    entity_id: str
    action: str  # "create", "update", "delete", "export"
    old_value: Optional[Dict]
    new_value: Optional[Dict]
    performed_by: str
    performed_at: datetime
    ip_address: Optional[str]
    reason: Optional[str]  # "사용자 요청", "자동 동기화" 등
```

#### 산출물
- [ ] `app/models/entity_metadata.py`
- [ ] `app/models/audit.py`
- [ ] `app/repositories/audit_repository.py`
- [ ] `app/services/lineage_service.py`
- [ ] 통합 테스트 15개

---

### Week 4 (08-19 ~ 09-01): RDF 변환 및 상호운용성

#### 목표
외부 온톨로지 연동, RDF 임포트/엑스포트

#### 5️⃣ RDF Triple 변환 계층

```python
class RDFConverter(BaseModel):
    """RDF 변환기"""
    
    def entity_to_rdf_triple(self, entity: Dict, domain_schema: DomainSchema) -> List[RDFTriple]:
        """엔티티 → RDF Triple"""
        # P001 (PROJECT, name="AI바우처")
        # → <ai-voucher-2025/P001> rdf:type <ai-voucher-2025/PROJECT>
        # → <ai-voucher-2025/P001> <name> "AI바우처"
        
    def rdf_triple_to_entity(self, triples: List[RDFTriple], domain_schema: DomainSchema) -> Dict:
        """RDF Triple → 엔티티"""

class RDFTriple(BaseModel):
    """RDF 삼중쌍"""
    subject: str      # URI
    predicate: str    # 속성/관계
    object: str       # 값 또는 URI
    context: Optional[str] = None  # 그래프 이름

class RDFNamespace(BaseModel):
    """RDF 네임스페이스"""
    prefix: str  # e.g., "avoucher"
    uri: str     # e.g., "http://nipa.go.kr/ontology/ai-voucher-2025#"
```

#### 6️⃣ 외부 온톨로지 임포트

```python
class OntologyImporter(BaseModel):
    """외부 온톨로지 임포트"""
    
    def import_dbpedia(self, entity_type: str, query: str) -> List[Dict]:
        """DBpedia에서 데이터 임포트"""
        # e.g., SPARQL 쿼리로 회사정보 가져오기
        
    def import_wikidata(self, entity_id: str) -> Dict:
        """Wikidata에서 엔티티 임포트"""
        
    def import_rdf_file(self, file_path: str, domain_id: str) -> ImportResult:
        """RDF 파일 임포트"""
        
class ImportResult(BaseModel):
    """임포트 결과"""
    total_entities: int
    imported_count: int
    failed_count: int
    errors: List[ImportError]
    import_id: str
    timestamp: datetime
```

#### 산출물
- [ ] `app/services/rdf_converter.py`
- [ ] `app/services/ontology_importer.py`
- [ ] SPARQL 엔드포인트 지원 (`/api/ontology/sparql`)
- [ ] 통합 테스트 15개

---

### Week 5-8 (09-02 ~ 09-30): 프론트엔드 + 최적화

#### 7️⃣ 온톨로지 브라우저 (Frontend)

```tsx
<OntologyExplorer
  domainId="ai-voucher-2025"
  style="property_graph"
/>

// 특징:
// - 스타일별 시각화 (RDF는 Triple 뷰, Hierarchical은 Tree 뷰)
// - 메타데이터 패널 (버전, 감사로그)
// - 혈통 추적 (Lineage Graph)
// - 버전 비교
// - 관계 강도 시각화
```

#### 8️⃣ 성능 최적화

```python
class OntologyCache(BaseModel):
    """온톨로지 캐싱"""
    - 스키마 캐싱 (Redis, 1시간 TTL)
    - 엔티티 쿼리 캐싱 (도메인별)
    - RDF 변환 캐시
    
class OntologyIndexing(BaseModel):
    """인덱싱"""
    - 속성 기반 인덱스
    - 관계 기반 인덱스
    - 전문 검색 (Elasticsearch)
```

#### 산출물
- [ ] `src/frontend/OntologyExplorer.tsx`
- [ ] 성능 최적화 (쿼리 시간 50% 감소)
- [ ] e2e 테스트 20개
- [ ] 사용 가이드 문서

---

## 📊 기대 효과

### 기능 확장
```
현재: Document + Graph 혼합 (단일 스타일)
→ Phase 4: 5가지 스타일 + 메타데이터 + RDF

데이터 표현 범위:
  ├─ 금융 도메인: Property Graph (복잡 관계)
  ├─ 조직도: Hierarchical (계층 구조)
  ├─ 지식그래프: Semantic Web (외부 통합)
  ├─ 공급망: RDF Triple (Linked Data)
  └─ 제조 데이터: Multi-typed (다중 역할)
```

### 상호운용성
```
✅ 외부 온톨로지 (DBpedia, Wikidata) 통합
✅ SPARQL 쿼리 지원
✅ RDF/Turtle 임포트/엑스포트
✅ 시맨틱 웹 표준 준수
```

### 거버넌스 강화
```
✅ 데이터 혈통 완전 추적
✅ 감사 로그 자동 기록
✅ 버전 관리 및 비교
✅ 정책 기반 접근 제어 (스키마별)
```

---

## 🎯 성공 기준

```
Code:
  ✅ 5가지 스타일 모두 구현
  ✅ 메타데이터 시스템 완성
  ✅ RDF 변환 100% 호환
  
Testing:
  ✅ 50개 이상 통합 테스트
  ✅ 커버리지 ≥ 85%
  
Functional:
  ✅ 스타일별 쿼리 성능 < 500ms
  ✅ 외부 온톨로지 임포트 성공률 ≥ 95%
  ✅ 데이터 혈통 추적 100% 정확도
  
Documentation:
  ✅ 스타일별 사용 가이드
  ✅ 스키마 설계 모범 사례
  ✅ API 문서 (Swagger)
```

---

## 📋 의존성 및 준비사항

### Phase 3 선행 요구사항
```
✅ Workflow 서비스 완성 (Phase 3 Week 4 완료)
✅ API 구조 정의 (Phase 3 Week 2 완료)
✅ 저장소 아키텍처 (Phase 3 내 완성)
```

### 외부 의존성
```
- RDF 라이브러리: rdflib (Python)
- SPARQL 엔드포인트: Apache Jena (또는 GraphDB)
- 외부 API: DBpedia, Wikidata SPARQL
- 시각화: D3.js, Cytoscape.js (Graph 렌더링)
```

### 선택 사항
```
⚠️ Neo4j 통합 (Property Graph 원격 저장)
⚠️ Elasticsearch 전문 검색 (선택, Phase 4 후반)
⚠️ GraphQL API (REST와 병행)
```

---

## 🔗 관련 문서

- [PHASE3_ACTION_DEFINITION.md](./PHASE3_ACTION_DEFINITION.md) — 액션 정의
- [PHASE3_STATE_MACHINE.md](./PHASE3_STATE_MACHINE.md) — 상태 관리
- [ARCHITECTURE.md](./ARCHITECTURE.md) — 아키텍처

---

## 📝 히스토리

| 날짜 | 이벤트 | 상태 |
|------|--------|------|
| 2026-05-20 | 온톨로지 다양성 이슈 제기 | ✅ 인식 |
| 2026-05-20 | Phase 4 계획 수립 | ✅ 이 문서 |
| 2026-07-21 | Phase 4 개발 시작 (예정) | ⏳ 대기 |
| 2026-09-30 | Phase 4 완료 (목표) | ⏳ 대기 |

---

**결론**: Phase 3에서 기본 액션/워크플로우를 완성하고, Phase 4에서 온톨로지의 **다양한 표현 방식**을 지원하여 enterprise-grade 확장성을 확보합니다.
