# Phase 4 주간별 실행 계획
## 온톨로지 데이터 모델링 다양성 지원 (2026-07-21 ~ 2026-09-30)

**상태**: 📋 준비 중 (실행: 2026-07-21)  
**목표**: 5가지 온톨로지 스타일 구현 + 메타데이터 + RDF 상호운용성

---

## Phase 4 주간별 마일스톤

```
Week 1-2 (07-21 ~ 08-04):  [Schema] 온톨로지 스타일 + 도메인 스키마
Week 3    (08-05 ~ 08-18):  [Metadata] 메타데이터 + 감사 시스템
Week 4    (08-19 ~ 09-01):  [RDF] RDF 변환 + 외부 온톨로지 통합
Week 5-8  (09-02 ~ 09-30):  [Frontend+Opt] 브라우저 UI + 성능 최적화
```

---

## 📅 Week 1-2: 온톨로지 스타일 지원 구조 (07-21 ~ 08-04)

### 주간 목표
다양한 데이터 모델 지원을 위한 핵심 스키마 계층 구현

### Task 1-1: OntologyStyle 열거형 + 기본 모델 정의

**담당**: Claude Backend  
**기간**: 07-21 ~ 07-24 (3일)

**산출물**:
```python
# app/models/ontology_schema.py
- OntologyStyle (Enum)
- PropertyDefinition
- SchemaConstraint
```

**테스트**: 5개
- test_ontology_style_enum
- test_property_definition_validation
- test_schema_constraint_types
- test_constraint_application
- test_style_specific_rules

**예상 시간**: 1-2일  
**성공 기준**: OntologyStyle 5가지 모두 enum 정의, 유효성 검증

---

### Task 1-2: DomainSchema + EntityType + RelationType

**담당**: Claude Backend  
**기간**: 07-24 ~ 07-27 (3일)

**산출물**:
```python
# app/models/domain_schema.py
- DomainSchema
- EntityType (상속, 메타필드 지원)
- RelationType (다중도, 방향성)
- PropertyType (다양한 데이터 타입)

# Database migrations
- domains 테이블
- entity_types 테이블
- relation_types 테이블
- property_definitions 테이블
```

**테스트**: 10개
- test_domain_schema_creation
- test_entity_type_with_inheritance
- test_relation_type_cardinality
- test_property_type_validation
- test_schema_versioning (v1.0, v1.1 등)
- test_schema_constraint_enforcement
- test_domain_isolation (도메인간 간섭 없음)
- test_metadata_fields_inclusion
- test_schema_export_to_json
- test_schema_import_from_json

**예상 시간**: 2-3일  
**성공 기준**: 5가지 스타일별 스키마 정의 가능, 도메인간 독립성 보장

---

### Task 1-3: SchemaRepository 구현

**담당**: Claude Backend  
**기간**: 07-27 ~ 08-01 (4일)

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

# Database schema version management
```

**테스트**: 8개
- test_schema_crud
- test_schema_retrieval_by_domain
- test_schema_retrieval_by_style
- test_entity_validation_against_schema
- test_relationship_validation
- test_schema_conflicts_detection
- test_schema_history_tracking
- test_concurrent_schema_updates

**예상 시간**: 2-3일  
**성공 기준**: CRUD 완전 동작, 유효성 검증 100% 정확도

---

### Task 1-4: 도메인별 스타일 선택 및 샘플 스키마

**담당**: Claude Backend  
**기간**: 08-01 ~ 08-04 (3일)

**산출물**:
```yaml
# schemas/domain-schemas/ai-voucher-2025.yaml
domain: ai-voucher-2025
style: property_graph
rationale: "복잡한 다중 주체 관계"

entity_types:
  - PROJECT
  - PERSON
  - ORGANIZATION
  - BUDGET_LINE

relation_types:
  - leads (PERSON -> PROJECT)
  - manages (ORGANIZATION -> PERSON)
  - allocates (ORGANIZATION -> BUDGET_LINE)

# 4개 도메인별 샘플
- ai-voucher-2025 (property_graph)
- manufacturing (hierarchical)
- knowledge-graph (semantic_web)
- order-tracking (rdf_triple)
```

**테스트**: 7개
- test_ai_voucher_schema_validation
- test_manufacturing_schema_validation
- test_knowledge_graph_schema_validation
- test_order_tracking_schema_validation
- test_multi_typed_entities
- test_schema_migration_strategy
- test_sample_data_conformance

**예상 시간**: 1-2일  
**성공 기준**: 4개 도메인 스키마 완성, 샘플 데이터 로드 성공

---

## 📅 Week 3: 메타데이터 및 감사 시스템 (08-05 ~ 08-18)

### 주간 목표
데이터 혈통(Lineage), 버전 관리, 감사 추적 시스템 완성

### Task 3-1: EntityMetadata + LineageInfo

**담당**: Claude Backend  
**기간**: 08-05 ~ 08-08 (3일)

**산출물**:
```python
# app/models/entity_metadata.py
- EntityMetadata
- LineageInfo
- Transformation
- ImportMetadata

# Database
- entity_metadata 테이블
- lineage_chain 테이블
- transformations 테이블
```

**테스트**: 8개
- test_entity_metadata_creation
- test_lineage_chain_tracking
- test_transformation_recording
- test_lineage_visualization
- test_source_type_classification
- test_import_metadata_recording
- test_lineage_graph_consistency
- test_circular_dependency_detection

**예상 시간**: 2-3일  
**성공 기준**: 3가지 source_type 지원, 혈통 체인 추적 정확도 100%

---

### Task 3-2: EntityVersion + AuditLog

**담당**: Claude Backend  
**기간**: 08-08 ~ 08-13 (4일)

**산출물**:
```python
# app/models/audit.py
- EntityVersion (v1, v2, v3...)
- AuditLog (모든 변경 기록)

# Database
- entity_versions 테이블
- audit_logs 테이블
- audit_log_indices (성능 최적화)
```

**테스트**: 10개
- test_entity_version_creation
- test_version_diff_calculation
- test_audit_log_recording
- test_audit_action_types (create, update, delete, export)
- test_version_rollback
- test_audit_log_query_performance
- test_compliance_audit_trail
- test_concurrent_version_updates
- test_version_branching (실험용 버전)
- test_audit_retention_policy

**예상 시간**: 2-3일  
**성공 기준**: 완전한 감사 증적, 버전 비교 기능

---

### Task 3-3: AuditRepository + LineageService

**담당**: Claude Backend  
**기간**: 08-13 ~ 08-18 (4일)

**산출물**:
```python
# app/repositories/audit_repository.py
- create_audit_log()
- get_audit_history()
- query_by_actor()
- query_by_action()
- query_by_date_range()
- export_audit_trail()

# app/services/lineage_service.py
- get_full_lineage_chain()
- visualize_lineage_graph()
- find_transformation_impact()
- trace_data_quality_issues()
```

**테스트**: 7개
- test_audit_repository_crud
- test_audit_queries_by_filter
- test_lineage_chain_resolution
- test_impact_analysis
- test_data_quality_correlation
- test_audit_export_formats
- test_lineage_visualization_data

**예상 시간**: 2-3일  
**성공 기준**: 감사 쿼리 성능 <200ms, 영향도 분석 정확도 95%

---

## 📅 Week 4: RDF 변환 및 외부 온톨로지 통합 (08-19 ~ 09-01)

### 주간 목표
RDF 표준 지원, DBpedia/Wikidata 통합, SPARQL 쿼리 지원

### Task 4-1: RDFConverter 구현

**담당**: Claude Backend  
**기간**: 08-19 ~ 08-23 (4일)

**산출물**:
```python
# app/services/rdf_converter.py
- RDFTriple (subject, predicate, object)
- RDFNamespace
- RDFConverter
  - entity_to_rdf_triple()
  - rdf_triple_to_entity()
  - relationship_to_rdf()
  - validate_rdf_consistency()
```

**테스트**: 10개
- test_entity_to_rdf_conversion
- test_rdf_to_entity_conversion
- test_relationship_to_rdf
- test_property_graph_to_rdf
- test_hierarchical_to_rdf
- test_rdf_namespace_management
- test_bidirectional_conversion_fidelity
- test_rdf_context_management
- test_rdf_validation
- test_large_graph_conversion_performance

**예상 시간**: 2-3일  
**성공 기준**: 양방향 변환 손실 없음, N3/Turtle 포맷 지원

---

### Task 4-2: OntologyImporter 구현

**담당**: Claude Backend  
**기간**: 08-23 ~ 08-28 (4일)

**산출물**:
```python
# app/services/ontology_importer.py
- DBpediaImporter
  - import_by_sparql_query()
  - import_entity_by_uri()
  
- WikidataImporter
  - import_entity_by_qid()
  - import_property_chain()
  
- RDFFileImporter
  - import_rdf_file()
  - import_from_url()
  - validate_import_compatibility()

# ImportResult, ImportError models
```

**테스트**: 10개
- test_dbpedia_sparql_import
- test_wikidata_import
- test_rdf_file_import
- test_import_conflict_resolution
- test_import_progress_tracking
- test_import_error_recovery
- test_import_data_quality_checks
- test_duplicate_detection
- test_import_rollback
- test_import_performance_batch

**예상 시간**: 2-3일  
**성공 기준**: DBpedia/Wikidata 통합 성공률 ≥95%, 충돌 해결 자동화

---

### Task 4-3: SPARQL 엔드포인트

**담당**: Claude Backend  
**기간**: 08-28 ~ 09-01 (3일)

**산출물**:
```python
# app/api/ontology_endpoints.py
POST /api/ontology/sparql
  - SPARQL 쿼리 실행
  - 결과 JSON-LD 반환
  
GET /api/ontology/export?domain_id=&format=turtle
  - RDF 파일 다운로드
  
POST /api/ontology/import
  - RDF 파일 업로드
  - DBpedia/Wikidata 임포트
```

**테스트**: 5개
- test_sparql_query_execution
- test_sparql_performance
- test_rdf_export_formats
- test_rdf_import_validation
- test_concurrent_ontology_queries

**예상 시간**: 1-2일  
**성공 기준**: SPARQL 쿼리 응답 <500ms, 표준 준수

---

## 📅 Week 5-8: Frontend UI + 최적화 (09-02 ~ 09-30)

### 주간 목표
온톨로지 브라우저 UI, 캐싱, 인덱싱, 성능 최적화

### Task 5-1: OntologyExplorer React 컴포넌트

**담당**: Codex Frontend  
**기간**: 09-02 ~ 09-11 (8일)

**산출물**:
```tsx
// src/frontend/src/components/OntologyExplorer.tsx
<OntologyExplorer
  domainId="ai-voucher-2025"
  style="property_graph"
  showMetadata={true}
/>

Features:
- 스타일별 시각화 (RDF: Triple 뷰, Hierarchical: Tree)
- 메타데이터 패널
- 혈통 추적 (Lineage Graph)
- 버전 비교
- 관계 강도 표시

Components:
- OntologyGraph.tsx (D3/Cytoscape)
- MetadataPanel.tsx (버전/감사)
- LineageViewer.tsx (데이터 혈통)
- VersionComparator.tsx (버전 비교)
```

**테스트**: 12개 E2E
- test_ontology_graph_rendering
- test_style_specific_visualization
- test_metadata_panel_display
- test_lineage_graph_interaction
- test_version_comparison
- test_entity_search
- test_relationship_filtering
- test_zoom_pan_controls
- test_export_to_formats
- test_concurrent_exploration
- test_responsive_layout
- test_accessibility

**예상 시간**: 5-6일  
**성공 기준**: 4가지 시각화 스타일 모두 동작, 성능 <1초

---

### Task 5-2: 캐싱 + 인덱싱

**담당**: Claude Backend  
**기간**: 09-11 ~ 09-18 (6일)

**산출물**:
```python
# app/services/ontology_cache.py
- SchemaCache (Redis, 1시간 TTL)
- EntityCache (도메인별 LRU)
- RDFConversionCache

# app/services/ontology_indexing.py
- PropertyIndex
- RelationshipIndex
- FullTextSearch (Elasticsearch)

# Benchmark 결과
Before: 평균 응답 2000ms
After: 평균 응답 800ms (60% 개선)
```

**테스트**: 8개
- test_schema_cache_hit_rate
- test_entity_cache_invalidation
- test_index_consistency
- test_fulltext_search_accuracy
- test_cache_concurrent_access
- test_index_update_performance
- test_memory_usage
- test_cache_warm_up_strategy

**예상 시간**: 4-5일  
**성공 기준**: 쿼리 성능 50% 개선, 캐시 히트율 >80%

---

### Task 5-3: 성능 최적화 + 문서화

**담당**: Antigravity Performance + Claude  
**기간**: 09-18 ~ 09-30 (10일)

**산출물**:
```
1. 성능 벤치마크 (locustfile.py 업데이트)
   - SPARQL 쿼리: <500ms
   - RDF 변환: <200ms
   - 캐시 히트: <50ms

2. 문서
   - PHASE4_ONTOLOGY_DEVELOPER_GUIDE.md
   - PHASE4_SCHEMA_DESIGN_PATTERNS.md
   - API 문서 (Swagger)
   - 마이그레이션 가이드
```

**테스트**: 10개
- test_query_performance_sla
- test_conversion_throughput
- test_concurrent_load (100+ users)
- test_memory_scaling
- test_disk_usage_optimization
- test_network_latency_impact
- test_database_query_plans
- test_cache_effectiveness
- test_index_usage
- test_end_to_end_performance

**예상 시간**: 6-8일  
**성공 기준**: 모든 성능 SLA 달성, 문서 완성도 100%

---

## 🎯 Phase 4 완료 기준

### Code 완성도
```
✅ 5가지 스타일 구현 (Document, RDF, Property Graph, Semantic Web, Hierarchical)
✅ 메타데이터 시스템 (LineageInfo, EntityVersion, AuditLog)
✅ RDF 변환 (entity ↔ RDF triple, 양방향)
✅ 외부 온톨로지 임포트 (DBpedia, Wikidata, RDF 파일)
✅ SPARQL 엔드포인트
✅ 온톨로지 브라우저 UI
✅ 캐싱 + 인덱싱
```

### 테스트 커버리지
```
✅ 단위 테스트: 50+ (각 기능 100%)
✅ 통합 테스트: 40+ (워크플로우별)
✅ E2E 테스트: 20+ (사용자 시나리오)
✅ 성능 테스트: 10+ (SLA 검증)
✅ 전체 커버리지: ≥ 85%
```

### 성능 목표
```
✅ 스타일별 쿼리: <500ms
✅ RDF 변환: <200ms
✅ 외부 온톨로지 임포트: 성공률 ≥95%
✅ 캐시 히트율: ≥80%
✅ 동시 사용자 100+: 응답 시간 <1s
```

### 문서화
```
✅ 개발자 가이드
✅ 스키마 설계 패턴
✅ API 문서 (Swagger)
✅ 마이그레이션 가이드
✅ 문제 해결 가이드
```

---

## 📊 주간별 커밋 계획

| 주간 | 마일스톤 | 커밋 메시지 |
|------|---------|-----------|
| 1-2 | Schema 구현 | [Phase 4 Week 1-2] Ontology Styles + Domain Schema |
| 3 | Metadata 구현 | [Phase 4 Week 3] Entity Metadata + Audit System |
| 4 | RDF 구현 | [Phase 4 Week 4] RDF Converter + External Ontology Import |
| 5-8 | Frontend+Opt | [Phase 4 Week 5-8] OntologyExplorer UI + Performance |

---

## 🔧 기술 스택 검증

### 필수 라이브러리 (Week 1-2 전에 확인)
```
✅ rdflib (RDF 처리)
✅ redis (캐싱)
✅ elasticsearch (검색)
✅ SPARQLWrapper (SPARQL 클라이언트)
```

### 설치 예정
```bash
pip install rdflib SPARQLWrapper redis elasticsearch
npm install cytoscape d3 react-query
```

---

## ⚠️ 위험 요소 및 완화책

### 위험 1: RDF 라이브러리 학습 곡선
**영향**: Week 4 지연 가능성  
**완화**: Week 1부터 rdflib 프로토타입 작성

### 위험 2: DBpedia/Wikidata API 변경
**영향**: 임포터 수정 필요  
**완화**: API 문서 정기 검토, 폴백 메커니즘

### 위험 3: 대규모 그래프 성능
**영향**: 캐싱/인덱싱 필수  
**완화**: Week 5부터 조기 성능 테스트

---

## 📝 다음 단계 (2026-07-20)

- [ ] 개발 환경 설정 (rdflib 등)
- [ ] Week 1-2 API 설계 리뷰
- [ ] 팀 분할: Claude (Backend), Codex (Frontend), Antigravity (Performance)
- [ ] 일일 스탠드업 일정 확정

---

**작성**: 2026-05-25  
**상태**: READY FOR PHASE 4 EXECUTION (2026-07-21)
