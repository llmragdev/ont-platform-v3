# Phase 4 에이전트별 수행 지시서
## 각 에이전트의 역할, 타이밍, 산출물 정의

**작성**: 2026-05-25  
**실행**: 2026-07-21 ~ 2026-09-30  
**상태**: 각 에이전트별 역할 정의 완료

---

## 📋 Phase 4 에이전트 역할 분담

### Claude (Backend) - 60% 시간 할당
**주요 담당**: 스키마, 메타데이터, RDF 변환, API 구현  
**기간**: Week 1-4 (메인), Week 5-8 (성능 최적화)

### Codex (Frontend) - 40% → 100% (Week 5-8)
**주요 담당**: OntologyExplorer UI, 시각화  
**기간**: Week 1-4 (리서치/설계, 10%), Week 5-8 (구현, 100%)

### Antigravity (Performance) - 25% → 100% (Week 5-8)
**주요 담당**: 성능 벤치마크, 캐싱, 인덱싱  
**기간**: Week 1-4 (기준선 수집, 10%), Week 5-8 (최적화, 100%)

---

## 🔵 Claude (Backend) 지시서

### Week 1-2: OntologyStyle + DomainSchema (07-21 ~ 08-04)

#### Task 1-1: OntologyStyle Enum + PropertyDefinition ✅ DONE
**상태**: Commit 5674538 (20/20 테스트 통과)
**다음**: Task 1-2로 진행

#### Task 1-2: DomainSchema + EntityType + RelationType (07-24 ~ 07-27)
**목표**: 도메인별 스키마 정의 모델 완성

**산출물**:
```python
# app/models/domain_schema.py (확장)
- EntityTypeDefinition (상속, 메타필드)
- RelationTypeDefinition (카디널리티, 방향성)
- DomainSchema (스타일별 구성)
```

**테스트**: 10개
- entity_type_with_inheritance
- entity_type_metadata_fields  
- relation_type_cardinality (4가지)
- domain_schema_entity_validation
- domain_schema_relation_validation
- domain_schema_versioning
- domain_schema_style_specific (5가지)

**예상 시간**: 2-3일  
**성공 기준**: 5가지 스타일별 스키마 정의 가능

#### Task 1-3: SchemaRepository 구현 (07-27 ~ 08-01)
**목표**: 스키마 저장소 (CRUD + 검증)

**산출물**:
```python
# app/repositories/schema_repository.py
class SchemaRepository:
    - create_schema()
    - get_schema_by_domain()
    - update_schema()
    - delete_schema()
    - list_schemas(style: OntologyStyle)
    - validate_entity_against_schema()
    - validate_relationship_against_schema()
```

**테스트**: 8개
- schema_crud (create, read, update, delete)
- schema_retrieval_by_domain
- schema_retrieval_by_style
- entity_validation_against_schema
- relationship_validation
- schema_conflicts_detection

**예상 시간**: 2-3일  
**성공 기준**: CRUD 완전 동작, 유효성 검증 100% 정확도

#### Task 1-4: 도메인별 샘플 스키마 (08-01 ~ 08-04)
**목표**: 4개 도메인의 샘플 스키마 생성

**산출물**:
```yaml
# schemas/domain-schemas/
- ai-voucher-2025.yaml (property_graph)
- manufacturing.yaml (hierarchical)
- knowledge-graph.yaml (semantic_web)
- order-tracking.yaml (rdf_triple)
```

**테스트**: 7개
- ai_voucher_schema_validation
- manufacturing_schema_validation
- knowledge_graph_schema_validation
- order_tracking_schema_validation
- multi_typed_entities
- schema_migration_strategy
- sample_data_conformance

**예상 시간**: 1-2일  
**성공 기준**: 4개 도메인 스키마 완성, 샘플 데이터 로드 성공

---

### Week 3: 메타데이터 + 감시 시스템 (08-05 ~ 08-18)

#### Task 3-1: EntityMetadata + LineageInfo (08-05 ~ 08-08)
**목표**: 엔티티 메타데이터 + 혈통 추적

**산출물**:
```python
# app/models/entity_metadata.py
- EntityMetadata
- LineageInfo
- Transformation
- ImportMetadata
```

**테스트**: 8개 (자세한 내용은 PHASE4_WEEK_BY_WEEK_PLAN.md 참조)

#### Task 3-2: EntityVersion + AuditLog (08-08 ~ 08-13)
**산출물**:
```python
# app/models/audit.py
- EntityVersion
- AuditLog
```

**테스트**: 10개

#### Task 3-3: AuditRepository + LineageService (08-13 ~ 08-18)
**산출물**:
```python
# app/repositories/audit_repository.py
# app/services/lineage_service.py
```

**테스트**: 7개

---

### Week 4: RDF 변환 + 외부 온톨로지 통합 (08-19 ~ 09-01)

#### Task 4-1: RDFConverter 구현 (08-19 ~ 08-23)
#### Task 4-2: OntologyImporter 구현 (08-23 ~ 08-28)  
#### Task 4-3: SPARQL 엔드포인트 (08-28 ~ 09-01)

(자세한 내용은 PHASE4_WEEK_BY_WEEK_PLAN.md 참조)

---

### Week 5-8: 성능 최적화 + 문서화 (09-02 ~ 09-30)

Claude는 Codex와 Antigravity의 작업을 지원하며, 성능 최적화 구현을 돕습니다.

---

## 🟢 Codex (Frontend) 지시서

### Week 1-4: 대기 기간 (07-21 ~ 08-31)
**할당 시간**: 10% (주당 4-5시간)

#### 준비 작업 1: OntologyExplorer 컴포넌트 설계 (07-21 ~ 07-31)
**목표**: 온톨로지 브라우저의 UI/UX 설계

**산출물**:
```
designs/
├── OntologyExplorer_Wireframes.md
│   ├── 레이아웃 (사이드바 + 그래프 + 메타데이터)
│   ├── 4가지 시각화 모드 (RDF, Tree, Graph, List)
│   └── 상호작용 패턴 (zoom, pan, filter)
│
├── Visualization_Requirements.md
│   ├── Cytoscape.js 설정
│   ├── D3.js 계층 시각화
│   ├── Force-Graph 3D (선택)
│   └── 색상/스타일 가이드
│
└── Component_Architecture.md
    ├── OntologyExplorer (root)
    ├── OntologyGraph (시각화)
    ├── MetadataPanel (우측)
    ├── FilterPanel (좌측)
    └── Controls (줌, 팬, 검색)
```

**산출물 형식**: Markdown + Figma/Excalidraw 링크 (선택)  
**예상 시간**: 3-4일  
**검토**: Claude와 리뷰 (설계 피드백)

#### 준비 작업 2: 라이브러리 프로토타입 (08-01 ~ 08-11)
**목표**: Cytoscape, D3, Force-Graph 프로토타입

**산출물**:
```tsx
// prototypes/
├── CytoscapeExample.tsx
│   ├── 그래프 렌더링 테스트
│   ├── 상호작용 (노드 선택, 에지 강조)
│   └── 성능 테스트 (1000+ 노드)
│
├── D3HierarchyExample.tsx
│   ├── 계층 구조 렌더링
│   ├── 접기/펼치기
│   └── 드래그 앤 드롭
│
└── APIIntegration.tsx
    ├── Mock API 호출
    ├── 데이터 로딩
    └── 에러 처리
```

**예상 시간**: 3-4일  
**성공 기준**: 3가지 라이브러리 모두 작동하는 프로토타입

#### 준비 작업 3: Backend API 명세 분석 (08-12 ~ 08-18)
**목표**: Claude의 API 설계 이해

**산출물**:
```markdown
# API_Integration_Plan.md

## OntologyExplorer가 필요한 API
1. GET /api/domains/{domain_id}/schema
   - 도메인 스키마 조회
   
2. GET /api/domains/{domain_id}/entities
   - 엔티티 목록 (필터 지원)
   
3. GET /api/domains/{domain_id}/entities/{entity_id}
   - 엔티티 상세 (메타데이터 포함)
   
4. GET /api/domains/{domain_id}/relationships
   - 관계 목록
   
5. GET /api/entities/{entity_id}/lineage
   - 데이터 혈통
   
6. GET /api/entities/{entity_id}/versions
   - 버전 목록
   
7. GET /api/audit-logs?entity_id=...
   - 감시 로그

## 각 API별 필요 데이터 구조
- Response schema 정의
- Error handling
- Pagination
- Filtering options
```

**예상 시간**: 2-3일  
**검토**: Claude와 API 설계 리뷰

---

### Week 5-8: OntologyExplorer 구현 (09-02 ~ 09-30)
**할당 시간**: 100% (주당 30-35시간)

#### Task 5-1: OntologyGraph 컴포넌트 (09-02 ~ 09-11)
**목표**: 4가지 시각화 모드 구현

**산출물**:
```tsx
// src/frontend/src/components/OntologyExplorer/
├── OntologyExplorer.tsx (root container)
├── OntologyGraph.tsx
│   ├── Cytoscape 모드 (Property Graph)
│   ├── D3 Tree 모드 (Hierarchical)
│   ├── Force-Graph 모드 (General Graph)
│   └── List 모드 (Table view)
├── MetadataPanel.tsx
├── FilterPanel.tsx
└── Controls.tsx
```

**테스트**: 8개 E2E
- test_graph_rendering_all_modes
- test_node_selection
- test_edge_highlighting
- test_zoom_pan
- test_filter_application
- test_search_functionality
- test_style_switching
- test_responsive_layout

**예상 시간**: 5-6일  
**성공 기준**: 4가지 시각화 모드 모두 동작, 성능 <1초

#### Task 5-2: 메타데이터 + 혈통 패널 (09-11 ~ 09-18)
**목표**: 우측 메타데이터 패널 + 혈통 그래프

**산출물**:
```tsx
├── MetadataPanel.tsx
│   ├── Entity Information (이름, 타입, 생성자)
│   ├── VersionComparator (버전 비교)
│   └── AuditLog (감사 로그)
│
├── LineageViewer.tsx
│   ├── Data Lineage Graph
│   ├── Transformation Chain
│   └── Impact Analysis
```

**테스트**: 5개 E2E
- test_metadata_display
- test_version_comparison
- test_audit_log_display
- test_lineage_graph_rendering
- test_impact_analysis

**예상 시간**: 4-5일

#### Task 5-3: 검색 + 필터 + 내보내기 (09-18 ~ 09-25)
**목표**: 고급 기능 완성

**산출물**:
```tsx
├── FilterPanel.tsx
│   ├── Entity Type Filter
│   ├── Relationship Type Filter
│   ├── Date Range Filter
│   └── Custom Property Filter
│
├── SearchBar.tsx
│   ├── Full-text Search
│   ├── Property-based Search
│   └── Suggestions
│
└── ExportDialog.tsx
    ├── Export as JSON
    ├── Export as CSV
    └── Export as RDF (optional)
```

**테스트**: 5개 E2E
- test_filter_combinations
- test_search_accuracy
- test_export_formats
- test_export_performance
- test_concurrent_operations

**예상 시간**: 4-5일

#### Task 5-4: 성능 최적화 + 배포 준비 (09-25 ~ 09-30)
**목표**: 성능 튜닝, 문서화

**산출물**:
```
- Code splitting (lazy loading)
- Component memoization
- Virtual scrolling (large lists)
- Performance benchmark report
- 사용자 가이드 (PHASE4_FRONTEND_GUIDE.md)
```

**테스트**: 2개 E2E
- test_performance_sla (성능 목표)
- test_accessibility (a11y)

**예상 시간**: 3-4일

---

## 🔴 Antigravity (Performance) 지시서

### Week 1-4: 기준선 수집 + 설계 (07-21 ~ 08-31)
**할당 시간**: 10% (주당 3-4시간)

#### 준비 작업 1: Phase 3 성능 기준선 분석 (07-21 ~ 07-28)
**목표**: Phase 3의 성능 병목을 바탕으로 Phase 4 기준선 정의

**산출물**:
```markdown
# PHASE4_PERFORMANCE_BASELINE.md

## Phase 3 결과 (문제점)
- JSON I/O lock: 19-45% 실패율
- Peak load (200 users): 3670ms 평균
- SQL 읽기: 0% 실패 (안정적)

## Phase 4 목표 (해결책)
- PostgreSQL 마이그레이션으로 동시성 문제 해결
- 캐싱으로 쿼리 성능 50% 개선
- 인덱싱으로 복합 쿼리 최적화

## Phase 4 성능 SLA
1. 스키마 쿼리: <50ms (캐시 히트)
2. 엔티티 조회: <200ms (인덱스 활용)
3. RDF 변환: <200ms (메모리 캐시)
4. SPARQL 쿼리: <500ms (p95)
5. 외부 온톨로지 임포트: <5초/1000 entities
6. 동시 사용자: 200+ (실패율 <1%)
```

**예상 시간**: 2-3일  
**검토**: Claude와 SLA 정의 리뷰

#### 준비 작업 2: 캐싱 + 인덱싱 설계 (08-01 ~ 08-11)
**목표**: 성능 최적화 아키텍처 설계

**산출물**:
```markdown
# PHASE4_CACHING_INDEXING_DESIGN.md

## 캐싱 전략
1. Schema Cache (Redis)
   - Key: schema:{domain_id}
   - TTL: 1시간
   - Invalidation: 스키마 변경 시

2. Entity Cache (LRU, in-memory)
   - 최근 1000개 엔티티
   - TTL: 5분
   - Eviction: LRU

3. Query Result Cache
   - 자주 사용되는 쿼리
   - TTL: 30분

## 인덱싱 전략
1. Property Index
   - Entity.properties (JSON 필드)
   - 자주 필터링되는 속성
   
2. Relationship Index
   - from_type, to_type 복합 인덱스
   - 빠른 관계 조회

3. Full-text Index (선택)
   - Elasticsearch 통합
   - 텍스트 검색 성능
```

**예상 시간**: 2-3일  
**검토**: Claude와 설계 검증

#### 준비 작업 3: 성능 테스트 시나리오 정의 (08-12 ~ 08-25)
**목표**: Week 5-8 성능 테스트 계획

**산출물**:
```python
# performance_tests/phase4_scenarios.py

class Phase4BenchmarkScenarios:
    """Phase 4 성능 테스트 시나리오"""
    
    # Scenario 1: Schema Query Performance
    - baseline_schema_retrieval()
    - schema_with_caching()
    - schema_cache_hit_rate()
    
    # Scenario 2: Entity Operations
    - entity_create_bulk()
    - entity_update_concurrent()
    - entity_query_with_filters()
    
    # Scenario 3: RDF Conversion
    - convert_entities_to_rdf()
    - convert_rdf_to_entities()
    - large_graph_conversion()
    
    # Scenario 4: External Ontology Import
    - import_from_dbpedia()
    - import_from_wikidata()
    - import_rdf_file()
    
    # Scenario 5: Load Testing
    - concurrent_users_100()
    - concurrent_users_200()
    - spike_test_500_to_50()
    
    # Scenario 6: Memory & Scalability
    - cache_memory_usage()
    - index_size_analysis()
    - database_growth_impact()
```

**예상 시간**: 3-4일  
**검토**: Claude와 시나리오 타당성 검증

---

### Week 5-8: 성능 최적화 + 벤치마크 (09-02 ~ 09-30)
**할당 시간**: 100% (주당 30-35시간)

#### Task 5-1: 캐싱 구현 (09-02 ~ 09-11)
**목표**: Redis 캐싱 + LRU 메모리 캐시 구현

**산출물**:
```python
# app/services/ontology_cache.py
- SchemaCache (Redis)
- EntityCache (LRU)
- QueryResultCache

# Test: 5개
- test_schema_cache_hit_rate
- test_entity_cache_eviction
- test_cache_invalidation
- test_concurrent_cache_access
- test_memory_usage
```

**예상 시간**: 4-5일

#### Task 5-2: 인덱싱 구현 (09-11 ~ 09-18)
**목표**: 데이터베이스 인덱싱 + 전문 검색

**산출물**:
```python
# app/services/ontology_indexing.py
- PropertyIndex
- RelationshipIndex
- FullTextSearch (Elasticsearch)

# Test: 5개
- test_index_consistency
- test_query_performance
- test_fulltext_accuracy
- test_index_size
- test_maintenance
```

**예상 시간**: 4-5일

#### Task 5-3: 성능 벤치마크 + 튜닝 (09-18 ~ 09-28)
**목표**: 모든 시나리오 벤치마크 실행 및 결과 분석

**산출물**:
```
PHASE4_PERFORMANCE_BENCHMARK_RESULTS.md
├── Schema Query Performance
├── Entity Operations
├── RDF Conversion
├── External Ontology Import
├── Load Testing Results
├── Memory & Scalability Analysis
└── Optimization Recommendations
```

**테스트**: 10개
- test_all_scenario_sla_compliance
- test_cache_effectiveness
- test_query_optimization
- test_concurrent_load
- test_memory_scaling
- test_index_effectiveness
- test_database_optimization
- test_network_latency
- test_end_to_end_performance
- test_regression_detection

**예상 시간**: 5-6일

#### Task 5-4: 문서화 + 최종 검증 (09-28 ~ 09-30)
**산출물**:
```
PHASE4_PERFORMANCE_TUNING_GUIDE.md
├── 캐싱 설정 가이드
├── 인덱싱 최적화
├── 쿼리 튜닝
├── 문제 해결
└── 모니터링 설정
```

**예상 시간**: 2-3일

---

## 📊 에이전트별 시간 할당표

| 주간 | Claude (%) | Codex (%) | Antigravity (%) | 총 시간/주 |
|------|-----------|----------|-----------------|----------|
| W1-2 | 80% (24h) | 10% (3h) | 10% (3h) | 30시간 |
| W3   | 80% (24h) | 10% (3h) | 10% (3h) | 30시간 |
| W4   | 80% (24h) | 10% (3h) | 10% (3h) | 30시간 |
| W5-8 | 40% (12h) | 100%(30h)| 100%(30h)| 72시간 |
| **총** | **192h** | **80h** | **80h** | **총 352h** |

---

## 🎯 의존성 및 블로킹 사항

### Codex의 블로킹 항목
```
W1-4 (기준선 수집):
  ✓ OntologyStyle enum (Claude)
  → EntityType, RelationType (Claude Task 1-2)
  → Entity metadata API (Claude Task 3)
  → Audit log API (Claude Task 3)

W5-8 (OntologyExplorer 구현):
  ✓ Schema API (Claude W1-2)
  → Entity query API (Claude W1-2)
  → Relationship query API (Claude W1-4)
  → Metadata API (Claude W3)
  → Lineage API (Claude W3)
  → RDF export API (Claude W4)
```

### Antigravity의 블로킹 항목
```
W1-4 (설계):
  ✓ Phase 3 벤치마크 결과
  → Phase 4 API 설계 (Claude W1-2)

W5-8 (구현):
  ✓ PostgreSQL 마이그레이션 (Claude W2)
  → Database indices (Claude W2)
  → RDF conversion API (Claude W4)
  → Full-text search API (Claude W4)
```

---

## ✅ 체크리스트 (각 에이전트별)

### Claude
- [ ] Week 1-2: OntologyStyle + DomainSchema (Task 1-1 ✓, 1-2, 1-3, 1-4)
- [ ] Week 3: Metadata + Audit System (Task 3-1, 3-2, 3-3)
- [ ] Week 4: RDF + Import (Task 4-1, 4-2, 4-3)
- [ ] Week 5-8: Performance support (협력)

### Codex
- [ ] Week 1-4: UI/UX 설계 + 프로토타입
- [ ] Week 5-8: OntologyExplorer 구현 (5-1, 5-2, 5-3, 5-4)
- [ ] 성능 목표: <1초 렌더링

### Antigravity
- [ ] Week 1-4: 기준선 분석 + 설계
- [ ] Week 5-8: 캐싱 + 인덱싱 + 벤치마크
- [ ] 성능 목표: 모든 SLA 달성

---

**최종 상태**: 각 에이전트별 역할 명확, 의존성 맵핑 완료  
**다음 단계**: 2026-07-21 Phase 4 Week 1 공식 시작
