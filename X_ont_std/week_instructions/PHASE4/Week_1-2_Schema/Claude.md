# Phase 4 Week 1-2: OntologyStyle + DomainSchema
## Claude (Backend) 수행 지시서

**기간**: 2026-07-21 ~ 2026-08-04 (2주)  
**할당**: 80% (주당 24-30시간)  
**목표**: 5가지 온톨로지 스타일 지원, 도메인 스키마 구현

---

## Task 1-1: OntologyStyle + PropertyDefinition ✅ DONE

**상태**: Commit 5674538  
**테스트**: 20/20 통과  
**다음**: Task 1-2로 진행

---

## Task 1-2: DomainSchema + EntityType + RelationType

**기간**: 07-24 ~ 07-27 (3일)  
**목표**: 도메인별 스키마 정의 모델 완성

### 구현 사항

```python
# app/models/domain_schema.py (확장)

class EntityTypeDefinition(BaseModel):
    """엔티티 타입 정의"""
    name: str                           # e.g., "PROJECT"
    display_name: str
    description: str = ""
    properties: Dict[str, PropertyDefinition]
    parent_types: List[str] = []        # 상속 지원
    metadata_fields: List[str]          # [created_by, created_at, ...]
    supports_multi_typing: bool = False
    style_specific_config: Optional[Dict[str, Any]] = None

class RelationTypeDefinition(BaseModel):
    """관계 타입 정의"""
    name: str                           # e.g., "leads"
    display_name: str
    description: str = ""
    from_type: str                      # 출발 엔티티 타입
    to_type: str                        # 도착 엔티티 타입
    cardinality: Cardinality             # 1:1, 1:N, N:M
    directed: bool = True
    properties: Dict[str, PropertyDefinition] = {}  # 관계 속성
    constraints: List[SchemaConstraint] = []

# 확장된 DomainSchema
class DomainSchema(BaseModel):
    domain_id: str
    ontology_style: OntologyStyle
    entity_types: Dict[str, EntityTypeDefinition]
    relation_types: Dict[str, RelationTypeDefinition]
    constraints: List[SchemaConstraint] = []
    version: str = "1.0"
    created_by: str
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
```

### 테스트 계획 (10개)

```python
# tests/integration/test_domain_schema.py

def test_entity_type_with_inheritance():
    """엔티티 타입 상속 지원 검증"""
    
def test_entity_type_metadata_fields():
    """메타필드 자동 포함 검증"""
    
def test_relation_type_cardinality_1_1():
    """1:1 관계 검증"""
    
def test_relation_type_cardinality_1_n():
    """1:N 관계 검증"""
    
def test_relation_type_cardinality_n_m():
    """N:M 관계 검증"""
    
def test_domain_schema_entity_validation():
    """도메인 내 엔티티 타입 검증"""
    
def test_domain_schema_relation_validation():
    """도메인 내 관계 타입 검증"""
    
def test_domain_schema_versioning():
    """스키마 버전 관리"""
    
def test_domain_schema_style_specific():
    """스타일별 스키마 구성"""
    
def test_domain_schema_constraints():
    """스키마 레벨 제약 조건"""
```

### 체크리스트

- [ ] EntityTypeDefinition 모델 구현
- [ ] RelationTypeDefinition 모델 구현
- [ ] DomainSchema 확장
- [ ] 10개 테스트 작성
- [ ] 10개 테스트 모두 통과
- [ ] 모든 기능 동작 확인
- [ ] 코드 리뷰 및 머지

---

## Task 1-3: SchemaRepository 구현

**기간**: 07-27 ~ 08-01 (4일)  
**목표**: 스키마 저장소 (CRUD + 검증)

### 구현 사항

```python
# app/repositories/schema_repository.py

class SchemaRepository:
    """도메인 스키마 저장소"""
    
    def create_schema(self, schema: DomainSchema) -> DomainSchema:
        """스키마 생성"""
        # 검증: 모든 엔티티/관계 타입이 정의되어 있는가?
        # 저장: database에 저장
        
    def get_schema_by_domain(self, domain_id: str) -> Optional[DomainSchema]:
        """도메인별 스키마 조회"""
        
    def update_schema(self, domain_id: str, schema: DomainSchema) -> DomainSchema:
        """스키마 수정"""
        # 버전 업데이트
        # 변경 이력 기록
        
    def delete_schema(self, domain_id: str) -> bool:
        """스키마 삭제"""
        
    def list_schemas(self, ontology_style: Optional[OntologyStyle] = None) -> List[DomainSchema]:
        """스키마 목록 조회 (선택: 스타일별 필터링)"""
        
    def validate_entity_against_schema(self, domain_id: str, entity: Dict) -> ValidationResult:
        """엔티티가 스키마를 준수하는지 검증"""
        # 필수 속성 확인
        # 속성 타입 확인
        # 제약 조건 확인
        
    def validate_relationship_against_schema(self, domain_id: str, rel: Dict) -> ValidationResult:
        """관계가 스키마를 준수하는지 검증"""
        # from_type, to_type 확인
        # 카디널리티 확인
```

### 테스트 계획 (8개)

```python
def test_schema_crud():
    """Create, Read, Update, Delete"""
    
def test_schema_retrieval_by_domain():
    """도메인별 스키마 조회"""
    
def test_schema_retrieval_by_style():
    """스타일별 스키마 조회"""
    
def test_entity_validation_passes():
    """엔티티 검증 통과"""
    
def test_entity_validation_fails():
    """엔티티 검증 실패"""
    
def test_relationship_validation_passes():
    """관계 검증 통과"""
    
def test_schema_conflicts_detection():
    """스키마 충돌 감지"""
    
def test_schema_version_tracking():
    """버전 추적"""
```

---

## Task 1-4: 도메인별 샘플 스키마

**기간**: 08-01 ~ 08-04 (3일)  
**목표**: 4개 도메인의 샘플 스키마 생성

### 구현 사항

```yaml
# schemas/domain-schemas/ai-voucher-2025.yaml

domain_id: ai-voucher-2025
ontology_style: property_graph
name: AI Voucher 2025
description: AI 바우처 프로젝트 관리 시스템

entity_types:
  PROJECT:
    display_name: Project
    properties:
      name: {type: string, required: true, indexed: true}
      budget: {type: integer}
      deadline: {type: datetime}
      
  PERSON:
    display_name: Person
    properties:
      email: {type: string, required: true, unique: true}
      
relation_types:
  leads:
    from_type: PERSON
    to_type: PROJECT
    cardinality: 1:N
    properties:
      start_date: {type: datetime}
```

4개 도메인:
1. `ai-voucher-2025.yaml` (property_graph)
2. `manufacturing.yaml` (hierarchical)
3. `knowledge-graph.yaml` (semantic_web)
4. `order-tracking.yaml` (rdf_triple)

### 테스트 계획 (7개)

```python
def test_ai_voucher_schema_validation():
def test_manufacturing_schema_validation():
def test_knowledge_graph_schema_validation():
def test_order_tracking_schema_validation():
def test_multi_typed_entities():
def test_schema_migration_strategy():
def test_sample_data_conformance():
```

---

## 📋 일일 진행 계획

### 07-24 (목)
- [ ] EntityTypeDefinition, RelationTypeDefinition 모델 구현
- [ ] DomainSchema 확장 (entity_types, relation_types)
- [ ] 기본 검증 로직

### 07-25 (금)
- [ ] 10개 테스트 구현
- [ ] 테스트 실행 및 디버깅
- [ ] 테스트 100% 통과

### 07-26 (토)
- [ ] SchemaRepository 기본 구조 (create, get, list)
- [ ] 검증 로직 구현 (validate_entity, validate_relationship)

### 07-27 (일)
- [ ] SchemaRepository 완성 (update, delete)
- [ ] 8개 Repository 테스트 작성 및 실행

### 07-28 (월)
- [ ] 샘플 스키마 4개 작성
- [ ] 샘플 데이터로 검증

### 07-29 (화)
- [ ] 7개 샘플 스키마 테스트 작성 및 실행
- [ ] 마이그레이션 전략 테스트

### 07-30 (수)
- [ ] 코드 리뷰 및 정리
- [ ] 주간 결과 요약

### 07-31 (목) ~ 08-04 (월)
- [ ] Task 1-4 완료
- [ ] 주간별 커밋 생성

---

## 🎯 성공 기준

✅ EntityType + RelationType + DomainSchema 모델 완성  
✅ SchemaRepository CRUD 구현  
✅ 엔티티/관계 검증 로직 100% 정확도  
✅ 4개 도메인 샘플 스키마 완성  
✅ 25개 통합 테스트 모두 통과  
✅ 코드 커버리지 ≥ 90%

---

## 📞 상호작용

**Codex와의 연계**:
- API 설계 리뷰 (Task 1-4 완료 후)
- 엔티티 구조 설명 필요시 동기화

**Antigravity와의 연계**:
- 성능 기준선 정의 (이번 주에 완료할 샘플 스키마 기반)

---

**상태**: Task 1-1 ✅, Task 1-2~1-4 준비 완료  
**예상 완료**: 2026-08-04  
**다음 단계**: Week 3 Metadata 구현
