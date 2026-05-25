# 메타데이터/감시 성능 최적화 설계

본 문서는 `ont_platform v4.0` 백엔드의 데이터 볼륨 증가 시 발생할 수 있는 쿼리 지연을 예방하고, 처리 성능을 극대화하기 위한 PostgreSQL 인덱싱 및 Redis 캐싱 아키텍처 설계를 다룹니다.

---

## 1. PostgreSQL 인덱싱 전략

### A. `entity_metadata` 테이블
엔티티의 생성 정보, 품질 평가 점수 및 상태 필터 조회를 가속화하기 위한 인덱스 레이아웃입니다.

```sql
-- 1. PRIMARY KEY 고유 인덱스 (기본 생성되나 조회 목적 명시)
CREATE UNIQUE INDEX idx_entity_metadata_pk 
  ON entity_metadata(entity_id);

-- 2. 도메인 단위의 메타데이터 조회 및 집계 성능 최적화
CREATE INDEX idx_metadata_domain 
  ON entity_metadata(domain_id);

-- 3. 데이터 품질 점수 정렬 및 상위 품질 엔티티 필터링 가속
CREATE INDEX idx_metadata_quality 
  ON entity_metadata(quality_score DESC);

-- 4. JSONB 형식의 태그 배열 검색 가속화 (GIN 인덱스 활용)
-- 예: WHERE tags @> '["production"]'
CREATE INDEX idx_metadata_tags_gin 
  ON entity_metadata USING gin(tags);

-- 5. 증분 동기화 및 최근 수정된 데이터 수집 가속화
CREATE INDEX idx_metadata_updated_at 
  ON entity_metadata(updated_at DESC);
```

### B. `audit_logs` 테이블 (또는 기존 `audit_log`)
감사 데이터는 시스템의 모든 쓰기 작업이 기록되는 쓰기 집약적(Write-Heavy) 테이블이며, 특정 엔티티 혹은 사용자별 이력 조회가 빈번히 일어납니다.

```sql
-- 1. 특정 엔티티의 최신 이력을 내림차순(최신순)으로 탐색하는 복합 인덱스
-- 예: WHERE entity_id = 'P001AAA' ORDER BY timestamp DESC
CREATE INDEX idx_audit_entity_operation_date
  ON audit_log(entity_id, operation, timestamp DESC);

-- 2. 특정 사용자가 수행한 작업 내역을 역순으로 조회
-- 예: WHERE actor = 'pm@example.com' ORDER BY timestamp DESC
CREATE INDEX idx_audit_actor_date
  ON audit_log(actor, timestamp DESC);

-- 3. 감사 로그 내보내기(Export) 및 배치 만료 처리를 위한 시간 필터링 인덱스
CREATE INDEX idx_audit_timestamp
  ON audit_log(timestamp DESC);

-- 4. 특정 도메인 단위의 변경 작업 필터링
CREATE INDEX idx_audit_domain_op
  ON audit_log(domain_id, operation);
```

### C. `lineage_chains` (또는 변환 기록 `transformations`, `lineage_chains`)
데이터의 상하위 종속 관계를 재귀적으로 추적하기 위한 최적화 인덱스입니다.

```sql
-- 1. 엔티티 기준 일대일 고유 인덱스
CREATE UNIQUE INDEX idx_lineage_entity_id
  ON lineage_chains(entity_id);

-- 2. 소스 식별자 기준 검색
CREATE INDEX idx_lineage_source_lookup
  ON lineage_chains(source_type, source_id);

-- 3. JSONB GIN 인덱스: direct_parent_ids 내에 특정 상위 엔티티가 포함되어 있는지 고속 조회
-- 예: WHERE direct_parent_ids @> '["P001AAA"]'
CREATE INDEX idx_lineage_parents_gin
  ON lineage_chains USING gin(direct_parent_ids);
```

---

## 2. 캐싱 전략 (Redis)

메타데이터 및 혈통 분석은 연산 강도가 높지만 변경 빈도는 상대적으로 낮아, Redis 캐싱 도입 시 극적인 성능 향상을 얻을 수 있습니다.

```
                          ┌──────────────────────────┐
                          │    FastAPI API Server    │
                          └─────────────┬────────────┘
                                        │
                         ┌──────────────┴──────────────┐
                   Cache Hit                     Cache Miss
                         │                             │
             ┌───────────▼───────────┐     ┌───────────▼───────────┐
             │      Redis Cache      │     │  PostgreSQL Database  │
             └───────────────────────┘     └───────────┬───────────┘
                                                       │
                                           ┌───────────▼───────────┐
                                           │  Write to Redis Cache │
                                           └───────────────────────┘
```

### A. MetadataCache
* **용도**: 엔티티의 품질 점수, 소유자 및 공유 설정 정보 즉시 조회
* **Key 구조**: `metadata:{entity_id}`
* **적용 전략**:
  * **TTL(Time To Live)**: **30분**
  * **Invalidation(무효화) 정책**: 엔티티 메타데이터 업데이트 (`UPDATE/DELETE` 발생) 시 즉시 해당 Redis Key 삭제 (Cache Eviction).
* **목표 히트율(Cache Hit Rate)**: **≥ 80%**

### B. LineageCache
* **용도**: 재귀 쿼리 실행을 회피하기 위한 혈통 종속 그래프 결과 조회
* **Key 구조**: `lineage:{entity_id}`
* **적용 전략**:
  * **TTL**: **1시간** (혈통 관계 데이터는 빈번히 변경되지 않는 특성 반영)
  * **Invalidation 정책**: 새로운 변환 작업(`Transformation`) 추가 또는 상속 관계 구조 변경 시 무효화.
* **목표 히트율**: **≥ 90%**

### C. AuditLogCache (조회 빈도가 높은 최신 로그 전용)
* **용도**: 대시보드의 최신 이벤트 통계 및 감사 로그 실시간 조회 캐싱
* **Key 구조**: `audit:recent:{entity_id}`
* **적용 전략**:
  * **TTL**: **5분** (최신 로그 갱신 빈도가 높아 짧은 수명 주기 설정)
* **목표 히트율**: **≥ 60%**

---

## 3. 성능 영향도 추정

| 최적화 설계 항목 | 대상 쿼리 / API | 예상 성능 개선도 | 우선순위 |
| :--- | :--- | :--- | :--- |
| **감사 로그 복합 인덱스** | `GET /api/audit/logs` | 쿼리 응답 시간 **60 ~ 70% 단축** | **1순위 (필수)** |
| **메타데이터 인덱싱 및 GIN** | `GET /api/entities/{id}` (메타데이터 조회) | 조회 응답 시간 **50% 이상 단축** | **1순위 (필수)** |
| **혈통(Lineage) Redis 캐싱** | `GET /api/entities/{id}/lineage` | 재귀 조회 오버헤드 **80 ~ 90% 차단** | **2순위 (중요)** |
| **메타데이터 Redis 캐싱** | `GET /api/entities/{id}` (단건 로드) | 캐시 Hit 시 응답 시간 **10ms 미만**으로 단축 | **2순위 (중요)** |

### 종합 기대 효과
PostgreSQL 인덱싱과 Redis 캐시를 병행 도입함으로써, 동시 사용자가 200명 이상인 극한 상황에서도 시스템 전체의 API 평균 응답 시간을 **기준선 대비 60% ~ 70% 단축**하고 데이터베이스 커넥션 풀 경합을 방지할 수 있습니다.
