# Phase 4 Week 3: Metadata + Audit System
## Antigravity (Performance) 수행 지시서

**기간**: 2026-08-05 ~ 2026-08-18 (2주)  
**할당**: 10% (주당 3-4시간)  
**목표**: v4 PostgreSQL 성능 기준선 정의, 감시 로그/메타데이터 성능 최적화 설계

---

## Prep 1: v4 PostgreSQL 기준선 분석

**기간**: 08-05 ~ 08-11 (1주)  
**목표**: PostgreSQL 저장소로 전환 후 성능 기준선 수립

### 산출물: PHASE4_POSTGRESQL_BASELINE.md 작성

```markdown
# v4 PostgreSQL 성능 기준선

## v3 vs v4 성능 비교

### 1. 엔티티 조회 (GET /api/entities/{id})
**v3 (JSON)**: 
- 50K 엔티티: ~150ms
- 100K 엔티티: ~300ms
- 500K 엔티티: ~1500ms

**v4 (PostgreSQL + Index)**:
- 50K: <50ms (캐시) / <100ms (DB)
- 100K: <50ms / <150ms
- 500K: <50ms / <300ms
- **예상 개선**: 3-5배

### 2. 감시 로그 쿼리 (GET /api/audit/logs)
**기준선 측정**:
- 10K 로그: <50ms
- 100K 로그: <150ms
- 1M 로그: <500ms (인덱스 활용)

**인덱스 전략**:
- PRIMARY: audit_id
- COMPOSITE: (entity_id, performed_at DESC)
- PARTIAL: (status = 'success')

### 3. 혈통 조회 (GET /api/entities/{id}/lineage)
**기준선 측정**:
- 3단계 혈통 체인: <300ms
- 10단계 체인: <800ms
- 100+ 파생 엔티티: <1000ms

**캐싱 전략**:
- 혈통 결과: Redis 1시간 TTL
- 메타데이터: Redis 30분 TTL

## v4 성능 SLA

### Tier 1: Critical (필수)
1. 메타데이터 조회: <100ms
2. 감시 로그 쿼리: <200ms (100K 로그)
3. 혈통 해석: <500ms (10단계)

### Tier 2: Important (중요)
4. 버전 롤백: <500ms
5. 감시 로그 내보내기: <3초 (100K 로그 CSV)
6. 순환 참조 감지: <1000ms (100 파생)

### Tier 3: Goal (목표)
7. 캐시 히트율: ≥70% (메타데이터)
8. DB 인덱스 효율: ≥95% (쿼리 계획)

## PostgreSQL vs v3 JSON 비교

| 메트릭 | v3 JSON | v4 PostgreSQL | 개선도 |
|--------|---------|---------------|--------|
| 엔티티 조회 | 150-1500ms | 50-300ms | 3-5배 |
| 감시 쿼리 | N/A | <200ms | New |
| 혈통 조회 | N/A | <500ms | New |
| 동시 쓰기 | 45% 실패 | <1% 실패 | 45배 |
| 저장소 크기 | 선형 증가 | JSONB 압축 | 30% 절감 |
```

### 예상 시간: 2-3일

**체크리스트**:
- [ ] v3 v4 성능 비교 테이블
- [ ] PostgreSQL 인덱싱 전략
- [ ] 캐싱 계층 설계
- [ ] SLA 수량화 및 문서화

---

## Prep 2: 메타데이터/감시 성능 최적화 설계

**기간**: 08-12 ~ 08-18 (1주)  
**목표**: Metadata + Audit 테이블 성능 최적화 전략

### 산출물: PHASE4_METADATA_AUDIT_OPTIMIZATION.md

```markdown
# 메타데이터/감시 성능 최적화

## 1. PostgreSQL 인덱싱 전략

### entity_metadata 테이블
```sql
-- PRIMARY KEY
CREATE UNIQUE INDEX idx_entity_metadata_pk 
  ON entity_metadata(entity_id);

-- 자주 조회되는 필터
CREATE INDEX idx_metadata_domain 
  ON entity_metadata(domain_id);

CREATE INDEX idx_metadata_quality 
  ON entity_metadata(data_quality_score DESC);

-- JSON 속성 검색
CREATE INDEX idx_metadata_tags_gin 
  USING gin(tags);

-- 벌크 업데이트 성능
CREATE INDEX idx_metadata_updated_at 
  ON entity_metadata(updated_at DESC);
```

### audit_logs 테이블
```sql
-- 복합 인덱스: 가장 자주 사용되는 쿼리 패턴
CREATE INDEX idx_audit_entity_action_date
  ON audit_logs(entity_id, action, performed_at DESC);

CREATE INDEX idx_audit_performed_by_date
  ON audit_logs(performed_by, performed_at DESC);

-- 대량 조회용 (로그 export)
CREATE INDEX idx_audit_performed_at
  ON audit_logs(performed_at DESC)
  WHERE retention_days > 0;  -- 만료되지 않은 로그만

-- 감사 보고서용
CREATE INDEX idx_audit_action_status
  ON audit_logs(action, status);
```

### lineage_chains 테이블
```sql
CREATE UNIQUE INDEX idx_lineage_entity_id
  ON lineage_chains(entity_id);

CREATE INDEX idx_lineage_created_at
  ON lineage_chains(created_at DESC);

-- JSON 데이터 검색 (혈통 분석)
CREATE INDEX idx_lineage_sources_gin
  USING gin(source_entities);

CREATE INDEX idx_lineage_transformations_gin
  USING gin(transformation_chain);
```

## 2. 캐싱 전략

### MetadataCache (Redis)
```python
# 전략
Key: metadata:{entity_id}
TTL: 30분
Invalidation: 엔티티 업데이트 시 즉시
Hit Rate 목표: ≥80%

# 구현
class MetadataCache:
    def get(self, entity_id: str) -> Optional[EntityMetadata]:
        # Redis → Cache Hit
        # Otherwise: DB 로드 + 캐시
```

### LineageCache (Redis)
```python
# 전략
Key: lineage:{entity_id}
TTL: 1시간 (혈통은 변경이 적음)
Invalidation: 변환 추가 시만 무효화
Hit Rate 목표: ≥90%

# 구현
class LineageCache:
    def get_lineage(self, entity_id: str) -> LineageInfo:
        # Redis → 혈통 체인
        # Otherwise: DB + 알고리즘 + 캐시
```

### AuditLogCache (Redis, 읽기 최적화용)
```python
# 전략
Key: audit:{entity_id}:{action}:{date}
TTL: 5분 (로그는 자주 조회됨)
Hit Rate 목표: ≥60%
```

## 3. 성능 영향도 추정

| 최적화 항목 | 예상 개선도 | 우선순위 |
|-----------|-----------|---------|
| 감시 로그 복합 인덱스 | 60-70% 쿼리 성능 | 1순위 (필수) |
| 메타데이터 인덱싱 | 50% 조회 개선 | 1순위 (필수) |
| 혈통 캐싱 | 80-90% 혈통 쿼리 | 2순위 (중요) |
| 메타데이터 캐싱 | 70-80% 조회 개선 | 2순위 (중요) |
| JSONB GIN 인덱스 | 40% JSON 필터 | 3순위 (선택) |

**예상 총 개선도**: 기준선 대비 60-70% 응답 시간 단축
```

### 예상 시간: 2-3일

**체크리스트**:
- [ ] PostgreSQL 인덱싱 전략 정의
- [ ] 캐싱 계층 설계
- [ ] 성능 영향도 추정
- [ ] Claude와 최적화 전략 리뷰

---

## 📋 일일 진행 계획

### 08-05 (월) ~ 08-08 (목)
- [ ] v3 vs v4 성능 비교표 작성
- [ ] PostgreSQL 스키마 분석
- [ ] 인덱싱 전략 초안

### 08-09 (금) ~ 08-12 (월)
- [ ] PHASE4_POSTGRESQL_BASELINE.md 완성
- [ ] SLA 정의
- [ ] Claude와 검토

### 08-13 (화) ~ 08-18 (일)
- [ ] 메타데이터/감시 최적화 설계
- [ ] 캐싱 전략 구체화
- [ ] 25개 성능 시나리오 준비 (Week 5-8용)

---

## 🎯 성공 기준

✅ PostgreSQL 성능 기준선 명확히 정의 (7가지 지표)  
✅ 감시 로그/메타데이터 인덱싱 전략 완성  
✅ 캐싱 계층 설계 완료  
✅ v4 성능 SLA 확정  
✅ Week 5-8 벤치마크 설계 80% 완료

---

## 📞 상호작용

**Claude와의 연계**:
- PostgreSQL 스키마 확인 (Task 3-1 완료 후)
- 인덱싱 전략 검증
- 캐싱 레이어 통합 계획

**Codex와의 협력**:
- 메타데이터 조회 성능 기준선
- 혈통 조회 응답 시간 목표

---

**상태**: Prep 1-2 준비 완료  
**예상 완료**: 2026-08-18  
**다음 단계**: Week 5-8 성능 구현 (09-02)

---

## 📝 최종 보고서 작성 가이드

**완료 후 다음 형식으로 최종 보고서를 작성하여 제출하세요.**

```markdown
# Phase 4 Week 3: Antigravity (성능 최적화) 완료 보고서

**기간**: 2026-08-05 ~ 2026-08-18 (2주)
**할당**: 10% (주당 3-4시간)
**상태**: ✅ 완료
**날짜**: [실제 보고서 작성 날짜]

---

## 📋 작업 요약

### Prep 1: PostgreSQL 성능 기준선 (PHASE4_POSTGRESQL_BASELINE.md)
- ✅ v3 vs v4 성능 비교 분석 완료
- ✅ 엔티티 조회 성능 예상 (3~5배 개선)
- ✅ 감시 로그 쿼리 성능 기준선 설정
- ✅ 혈통 조회 성능 기준선 설정
- ✅ v4 성능 SLA 3 Tier 정의 (Critical/Important/Goals)

### Prep 2: 최적화 설계 (PHASE4_METADATA_AUDIT_OPTIMIZATION.md)
- ✅ PostgreSQL 인덱싱 전략 3개 테이블 (entity_metadata, audit_logs, lineage_chains)
- ✅ Redis 캐싱 전략 3개 레이어 (MetadataCache, LineageCache, AuditLogCache)
- ✅ TTL 및 Invalidation 정책 정의
- ✅ 성능 영향도 추정 (60~70% 응답 시간 단축)

---

## 📊 설계 검증 결과

| 항목 | 목표 | 달성 |
|------|------|------|
| v3 vs v4 성능 비교 | 3~5배 개선 분석 | ✅ 예상 개선도 확인 |
| PostgreSQL 인덱싱 | 3개 테이블 인덱스 전략 | ✅ [실제 작성된 인덱스 개수] 개 설계 |
| Redis 캐싱 | 3개 캐시 레이어 | ✅ TTL 정책 정의 |
| 성능 SLA | 3 Tier 정의 | ✅ Critical/Important/Goals 설정 |
| 종합 성능 개선도 | 60~70% 응답 시간 단축 | ✅ 설계 검증 완료 |

---

## 📈 주요 성과

**기준선 분석**:
- 엔티티 조회: v3 150~1,500ms → v4 50~300ms (인덱스+캐시)
- 감시 로그: 신규 지원 (v3는 동적 파일 조회 불가), v4 <200ms (100K 로그)
- 혈통 조회: 신규 지원 (v3는 수동 파일 크롤링), v4 <500ms (10단계)
- 동시성: v3 ~45% 실패율 → v4 <1% 미만 (Windows File Lock 해결)

**최적화 설계**:
- PostgreSQL 복합 인덱스로 60~70% 응답 시간 단축
- Redis 캐싱으로 재귀 조회 오버헤드 80~90% 차단
- 메타데이터 단건 조회: 캐시 Hit 시 <10ms

---

## 🔧 생성된 문서

### 생성된 파일
- `ont_platform/v4/PHASE4_POSTGRESQL_BASELINE.md` - v3 vs v4 성능 비교 및 SLA 정의
- `ont_platform/v4/PHASE4_METADATA_AUDIT_OPTIMIZATION.md` - 인덱싱 및 캐싱 전략

---

## ⏭️ 다음 단계

### 즉시 필요 (Week 3.5)
- [ ] PostgreSQL 인덱스 생성 실행 (Alembic 마이그레이션)
- [ ] Redis 캐싱 레이어 구현 및 통합 테스트
- [ ] API 엔드포인트 성능 프로파일링

### Week 4 준비
- [ ] RDF 기반 질의 성능 기준선 설정
- [ ] SPARQL 엔드포인트 응답 시간 목표 설정

---

## 🔗 관련 문서

- 지시서: `week_instructions/PHASE4/Week_3_Metadata/Antigravity.md`
- PostgreSQL 기준선: `ont_platform/v4/PHASE4_POSTGRESQL_BASELINE.md`
- 최적화 설계: `ont_platform/v4/PHASE4_METADATA_AUDIT_OPTIMIZATION.md`

---

**보고자**: Antigravity (성능 최적화)  
**완료 시각**: [실제 완료 시각] KST
```

**⚠️ 반드시 따르기**:

1. **저장 위치** (필수)
   - ✅ 정해진 위치: `task_logs/antigravity/YYYYMMDD_PHASE4_WEEK3_Antigravity_Complete.md`
   - 파일명 형식: `YYYYMMDD_HHMM_작업명.md`
   - 예: `20260818_1530_PHASE4_WEEK3_Antigravity_Complete.md`
   - ❌ 금지: `ont_platform/v3/`, `ont_platform/v4/`, 또는 다른 위치에 저장하지 말 것

2. **템플릿 작성**:
   - "기간", "할당", "상태", "날짜" → 실제 작업 기록으로 채우기
   - "Prep 1-2" 섹션의 체크마크(✅) → 실제 완료 항목만 표시
   - "설계 검증 결과" 테이블의 "달성" 열 → 실제 달성 내용으로 갱신
   - "생성된 파일" → 실제로 생성된 파일 경로와 개수 입력
