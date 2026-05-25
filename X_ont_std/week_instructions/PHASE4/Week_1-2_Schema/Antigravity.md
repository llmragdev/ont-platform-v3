# Phase 4 Week 1-2: OntologyStyle + DomainSchema
## Antigravity (Performance) 수행 지시서

**기간**: 2026-07-21 ~ 2026-08-04 (2주)  
**할당**: 10% (주당 3-4시간)  
**목표**: Phase 3 성능 병목 분석, Phase 4 기준선 정의, 최적화 설계

---

## 준비 작업 1: Phase 3 성능 기준선 분석

**기간**: 07-21 ~ 07-28 (1주)  
**목표**: Phase 3 병목점을 분석하여 Phase 4 SLA 정의

### 산출물: PHASE4_PERFORMANCE_BASELINE.md 작성

```markdown
# Phase 4 성능 기준선 분석

## Phase 3 문제점 정리

### 1. JSON I/O 락 (Windows 파일 시스템)
**문제**:
- 동시 접근 시 19-45% 실패율
- 원자적 쓰기 실패 (/api/workflow/execute)
- 동시 50명 이상에서 심각한 저하

**근본 원인**:
- JSON 파일 기반 저장소
- Windows 파일 락 경합
- atomic rename 불가능

**Phase 4 솔루션**:
- PostgreSQL 마이그레이션
- 데이터베이스 행 수준 락
- 트랜잭션 안전성

### 2. 읽기 성능 (SQL 기반)
**문제 없음**:
- GET /api/changelog/history: 0% 실패, 184.6ms 평균
- GET /api/writeback/statistics: 0% 실패, 31.5ms 평균

**Phase 4 개선**:
- 캐싱 (Redis): 50ms 이하
- 인덱싱: 복합 쿼리 최적화

## Phase 4 성능 SLA 정의

### Tier 1: 절대 필수 (Critical)
```
1. 스키마 쿼리: <50ms (캐시 히트)
   - Key: schema:{domain_id}
   - Hit rate: ≥80%
   
2. 엔티티 단일 조회: <200ms
   - 인덱스 활용
   - Hot data LRU 캐시
   
3. RDF 변환: <200ms
   - Entity → RDF Triple
   - 메모리 캐시
```

### Tier 2: 중요 (Important)
```
4. SPARQL 쿼리: <500ms (p95)
   - 복합 조건 검색
   - 관계 트래버설
   
5. 외부 온톨로지 임포트: <5초/1000 entities
   - DBpedia, Wikidata
   - RDF 파일
   
6. 동시 사용자 처리: 200+ (<1% 실패)
   - Peak load scenario
```

### Tier 3: 목표 (Goal)
```
7. 캐시 히트율: ≥80%
8. 데이터베이스 쿼리 평균: <100ms
9. 인덱스 효율: ≥90%
```

## Phase 3 vs Phase 4 비교

| 메트릭 | Phase 3 | Phase 4 Target | 개선도 |
|--------|---------|---------------|--------|
| 쓰기 실패율 | 45% | <1% | 45배 |
| Peak 응답시간 | 3670ms | <500ms | 7배 |
| 동시 사용자 | 50 | 200 | 4배 |
| 캐시 히트율 | N/A | ≥80% | New |
| 인덱싱 커버리지 | N/A | ≥90% | New |
```

### 예상 시간: 2-3일

**체크리스트**:
- [ ] Phase 3 성능 리포트 재검토
- [ ] 문제점 분석 (근본 원인)
- [ ] Phase 4 SLA 정의
- [ ] 성능 목표 수량화
- [ ] Claude와 SLA 리뷰

---

## 준비 작업 2: 캐싱 + 인덱싱 설계

**기간**: 08-01 ~ 08-11 (1주)  
**목표**: 성능 최적화 아키텍처 설계

### 산출물: PHASE4_CACHING_INDEXING_DESIGN.md 작성

```markdown
# Phase 4 캐싱 + 인덱싱 전략

## 1. 캐싱 레이어

### 1.1 Schema Cache (Redis)
```python
# 전략
- Key: schema:{domain_id}
- Value: DomainSchema 직렬화
- TTL: 1시간
- Invalidation: 스키마 변경 시 즉시
- Hit rate 목표: ≥95%

# 구현
class SchemaCache:
    def get(self, domain_id: str) -> Optional[DomainSchema]:
        # Redis에서 조회
        # Miss 시 DB에서 로드 + 캐시
        
    def invalidate(self, domain_id: str):
        # 스키마 수정 시 호출
```

### 1.2 Entity Cache (LRU, In-Memory)
```python
# 전략
- 크기: 최근 1000개 엔티티
- TTL: 5분 (선택사항)
- LRU 정책: 가장 오래된 항목 제거
- Hit rate 목표: ≥70%

# 구현
from functools import lru_cache

class EntityCache:
    def __init__(self, maxsize=1000):
        self.cache = {}
        self.access_order = []
        
    @property
    def hit_rate(self):
        return hits / (hits + misses)
```

### 1.3 Query Result Cache
```python
# 전략
- 자주 사용되는 쿼리 결과만 캐싱
- Key: hash(query) + domain_id
- TTL: 30분
- Invalidation: 데이터 변경 시

# 캐싱할 쿼리 패턴:
1. "모든 PROJECT 조회" (필터링)
2. "특정 PERSON의 관계" (자주 조회)
3. "SPARQL 쿼리 결과"
```

## 2. 인덱싱 전략

### 2.1 Property Index (PostgreSQL)
```sql
-- 자주 필터링되는 속성 인덱스화
CREATE INDEX idx_entity_type ON entities(type);
CREATE INDEX idx_entity_created_at ON entities(created_at);
CREATE INDEX idx_property_name ON entity_properties((properties->>'name'));

-- JSON 필드 인덱싱 (GIN)
CREATE INDEX idx_entity_properties_gin ON entities USING gin(properties);
```

### 2.2 Relationship Index
```sql
-- 관계 타입별 빠른 조회
CREATE INDEX idx_relationship_from_to 
  ON relationships(from_type, to_type, type);

-- 특정 엔티티의 모든 관계
CREATE INDEX idx_relationship_entity 
  ON relationships(from_id, type);
```

### 2.3 Full-Text Search (Elasticsearch)
```python
# 전략
- 엔티티 이름, 설명 인덱싱
- 자동완성 지원
- 관련도 랭킹

# 구현 (선택, Week 7+)
class FullTextSearcher:
    def search(self, query: str, domain_id: str):
        # Elasticsearch 쿼리
        # 결과 스코어링
```

## 3. 성능 영향도 추정

| 최적화 항목 | 예상 개선도 | 구현 우선순위 |
|-----------|-----------|------------|
| Schema Cache (Redis) | 80-90% 스키마 쿼리 시간 단축 | 1순위 (필수) |
| Entity LRU Cache | 60-70% 엔티티 조회 개선 | 1순위 (필수) |
| Property Index | 30-50% 필터 쿼리 개선 | 2순위 (중요) |
| Relationship Index | 40-60% 관계 조회 개선 | 2순위 (중요) |
| Full-Text Search | 70-80% 검색 성능 개선 | 3순위 (선택) |

**예상 총 개선도**: 기준선 대비 50% 성능 개선
```

### 예상 시간: 2-3일

**체크리스트**:
- [ ] 3가지 캐싱 전략 정의
- [ ] 3가지 인덱싱 전략 정의
- [ ] PostgreSQL 마이그레이션 영향도 분석
- [ ] 성능 영향도 추정
- [ ] Claude와 설계 검증

---

## 준비 작업 3: 성능 테스트 시나리오 정의

**기간**: 08-12 ~ 08-25 (2주)  
**목표**: Week 5-8 성능 테스트 계획 수립

### 산출물: performance_tests/phase4_scenarios.py 작성

```python
# performance_tests/phase4_scenarios.py

class Phase4BenchmarkScenarios:
    """Phase 4 성능 테스트 시나리오"""
    
    # Scenario 1: Schema Query Performance
    def baseline_schema_retrieval(self):
        """기준선: DB에서 매번 조회"""
        # 100회 반복, 응답시간 측정
        # 예상: ~200ms
        
    def schema_with_caching(self):
        """캐싱 적용: Redis 캐시"""
        # 100회 반복 (캐시 히트)
        # 예상: ~50ms (80% 개선)
        
    def schema_cache_hit_rate(self):
        """캐시 히트율 측정"""
        # 1000회 요청 중 캐시 히트 비율
        # 목표: ≥80%
    
    # Scenario 2: Entity Operations (10개)
    def entity_create_bulk(self):
        """대량 엔티티 생성"""
        # 1000개 엔티티 생성
        # 트랜잭션 안전성 검증
        
    def entity_update_concurrent(self):
        """동시 엔티티 업데이트"""
        # 50개 스레드 × 20개 업데이트
        # 데이터 일관성 검증
        
    def entity_query_with_filters(self):
        """필터링된 엔티티 조회"""
        # 다양한 필터 조합
        # 인덱스 활용도 측정
    
    # Scenario 3: RDF Conversion (5개)
    def convert_entities_to_rdf(self):
        """엔티티 → RDF Triple 변환"""
        # 1000개 엔티티 변환
        # 메모리 사용량 모니터링
        
    def convert_rdf_to_entities(self):
        """RDF Triple → 엔티티 변환"""
        # 양방향 변환 성능 검증
        
    def large_graph_conversion(self):
        """대규모 그래프 변환"""
        # 10000개 노드 변환
        # 타임아웃 없음 검증
    
    # Scenario 4: External Ontology Import (3개)
    def import_from_dbpedia(self):
        """DBpedia 임포트"""
        # 100개 엔티티 임포트
        # 성공률 95% 이상
        
    def import_from_wikidata(self):
        """Wikidata 임포트"""
        
    def import_rdf_file(self):
        """RDF 파일 임포트"""
        # 대용량 파일 처리
    
    # Scenario 5: Load Testing (4개)
    def concurrent_users_100(self):
        """100 동시 사용자"""
        # 5분 지속
        # 응답시간 p95 < 500ms
        
    def concurrent_users_200(self):
        """200 동시 사용자 (목표)"""
        # 응답시간 p95 < 500ms
        
    def spike_test_100_to_200(self):
        """트래픽 급증 (스파이크)"""
        # 100 → 200 유저로 급증
        # 안정성 검증
        
    def spike_test_200_to_50(self):
        """트래픽 급감"""
        # 복구 속도 측정
    
    # Scenario 6: Memory & Scalability (3개)
    def cache_memory_usage(self):
        """캐시 메모리 사용량"""
        # 100,000개 엔티티 로드
        # LRU 메모리 관리 검증
        
    def index_size_analysis(self):
        """인덱스 크기 분석"""
        # 데이터 증가에 따른 인덱스 크기
        
    def database_growth_impact(self):
        """데이터베이스 성능 영향"""
        # 100만개 엔티티에서의 쿼리 성능

# 시나리오 메타데이터
SCENARIO_METADATA = {
    'baseline_schema_retrieval': {
        'name': 'Schema Query (기준선)',
        'duration_seconds': 30,
        'expected_latency_ms': 200,
        'priority': 'critical'
    },
    'schema_with_caching': {
        'name': 'Schema Query (캐시)',
        'duration_seconds': 30,
        'expected_latency_ms': 50,
        'priority': 'critical'
    },
    # ... 모든 시나리오 메타데이터
}
```

### 예상 시간: 3-4일

**체크리스트**:
- [ ] 25개 시나리오 정의 (코드 스켈레톤)
- [ ] 각 시나리오별 expected metrics 정의
- [ ] Locust 스크립트 템플릿 준비
- [ ] 데이터 생성 스크립트 작성
- [ ] Claude와 시나리오 검증

---

## 📋 일일 진행 계획

### 07-21 (월) ~ 07-24 (목)
- [ ] Phase 3 성능 리포트 재분석
- [ ] Phase 4 SLA 초안 작성
- [ ] Claude와 미팅 (SLA 리뷰)

### 07-25 (금) ~ 07-28 (월)
- [ ] PHASE4_PERFORMANCE_BASELINE.md 완성
- [ ] 성능 기준선 수치화
- [ ] SLA 최종 확정

### 07-29 (화) ~ 08-04 (월)
- [ ] 캐싱 전략 설계
- [ ] 인덱싱 전략 설계
- [ ] 시나리오 정의 시작

### 08-05 (화) ~ 08-11 (월)
- [ ] PHASE4_CACHING_INDEXING_DESIGN.md 완성
- [ ] 25개 시나리오 정의 완료
- [ ] 테스트 데이터 생성 스크립트

### 08-12 (화) ~ 08-18 (월)
- [ ] Locust 스크립트 작성
- [ ] 시나리오 시뮬레이션 테스트
- [ ] Claude와 최종 리뷰

---

## 🎯 성공 기준

✅ Phase 4 SLA 명확히 정의 (8가지 지표)  
✅ 캐싱 + 인덱싱 아키텍처 설계 완료  
✅ 25개 성능 테스트 시나리오 정의  
✅ 시나리오별 expected metrics 수량화  
✅ Week 5-8 벤치마크 준비 100% 완료

---

## 📞 상호작용

**Claude와의 연계**:
- SLA 정의 (Task 1-4 완료 후 샘플 데이터 기반)
- PostgreSQL 마이그레이션 영향도 평가
- 인덱싱 전략 검증

**Codex와의 협력**:
- 프로토타입 성능 측정 (선택)
- UI 응답시간 기준선

---

**상태**: 기준선 분석 → 설계 단계  
**예상 완료**: 2026-08-25  
**다음 단계**: Week 5-8 성능 구현 (09-02)
