# PostgreSQL 마이그레이션 4주 구현 로드맵

> **프로젝트**: ont_platform v3 아키텍처 재설계  
> **기간**: 2026-05-27 ~ 2026-06-21 (4주)  
> **작성일**: 2026-05-24  
> **담당**: Claude Code  
> **상태**: 📋 계획 수립 완료, 🔴 구현 준비 대기  

---

## 🎯 목표

| 항목 | 목표 |
|------|------|
| **표준 준수** | rdflib 기반 SPARQL parser + SQL translator (Supported Profile 제한) |
| **성능** | Hot-path 쿼리 class별 목표 달성 (아래 참고) |
| **동시성** | PostgreSQL 트랜잭션 격리 (READ COMMITTED + optimistic locking) |
| **코드** | 번역기 + API + 마이그레이션 도구 완성 |
| **테스트** | 단위(100+) + 통합(50+) + 성능(10+) 테스트 |

---

## Week 1: 기초 구축 (05-27 ~ 05-31)

### 📌 목표
- rdflib 기반 SPARQL parser 통합 + Supported Profile 정의
- PostgreSQL 스키마 설계 완료
- 개발 환경 구성 (로컬 + Neon.tech)

### Task 1-1: rdflib 통합 (05-27 ~ 05-28)

**입력**: 현재 Mock SPARQL 엔진  
**출력**: SPARQLServiceV2 → SPARQLService (표준 호환)

```markdown
- [ ] SPARQLServiceV2 → 메인 서비스로 승격
  - [ ] 임포트 경로 변경 (app/services/sparql_service.py)
  - [ ] V1 정규식 엔진 deprecate 처리
  - [ ] 모든 호출 지점에서 V2 사용 확인

- [ ] 기본 SPARQL 쿼리 패턴 테스트 (Supported Profile)
  - [ ] SELECT (기본 + FILTER + ORDER BY + LIMIT)
  - [ ] 단순 triple pattern (?s ?p ?o)
  - [ ] Type query (?x rdf:type ex:Type)
  - [ ] Property lookup (?x ex:prop "value")
  - [ ] Simple joins (one-hop relation)
  - [ ] Fallback: CONSTRUCT, DESCRIBE, UNION, OPTIONAL은 rdflib 실행

- [ ] 오류 처리 및 검증
  - [ ] 잘못된 SPARQL 문법 감지
  - [ ] 명확한 오류 메시지 반환
  - [ ] 파서 예외 처리

- [ ] 테스트: tests/integration/test_sparql_full_suite.py
  - [ ] 30개 쿼리 패턴 (현재 17개 + 13개 추가)
  - [ ] 예상: 통과율 100%
```

**승인 기준**: 30개 테스트 모두 통과

---

### Task 1-2: PostgreSQL 스키마 설계 (05-28 ~ 05-30)

**입력**: 04_2 문서의 스키마 제안  
**출력**: 실행 가능한 DDL + 마이그레이션 스크립트

```markdown
- [ ] DDL 작성: docs/SCHEMA_DESIGN.md에서
  - [ ] CREATE TABLE entities (5개 컬럼, 인덱스)
  - [ ] CREATE TABLE relationships (6개 컬럼, 인덱스)
  - [ ] CREATE TABLE ontology_metadata
  - [ ] CREATE TABLE audit_log
  - [ ] CREATE VIEW ontology_triples (읽기 시뮬레이션)

- [ ] Alembic 마이그레이션 설정
  - [ ] alembic init app/db/migrations
  - [ ] env.py 구성 (PostgreSQL 연결)
  - [ ] 초기 마이그레이션 파일 생성
  - [ ] upgrade/downgrade 테스트

- [ ] 로컬 PostgreSQL 테스트
  - [ ] Docker Compose 파일 작성 (docker-compose.dev.yml)
  - [ ] 스키마 생성 검증
  - [ ] 더미 데이터 삽입 (10개 엔티티)
  - [ ] 기본 쿼리 동작 확인

- [ ] Neon.tech 계정 준비
  - [ ] Neon.tech 가입 (무료 tier)
  - [ ] 프로젝트 생성
  - [ ] 연결 문자열 획득
  - [ ] 동일 스키마 배포

- [ ] 문서화
  - [ ] docs/SCHEMA_DESIGN.md (완성)
  - [ ] docs/DEPLOYMENT_GUIDE.md (초안)
```

**승인 기준**: DDL 실행 성공 + 양쪽(로컬/Neon) 환경 동일

---

### Task 1-3: 개발 환경 구성 (05-30 ~ 05-31)

**입력**: 스키마, Docker, 환경 변수  
**출력**: 즉시 개발 가능한 환경

```markdown
- [ ] Docker Compose 작성
  - [ ] PostgreSQL 15 이미지
  - [ ] 포트 5432 바인딩
  - [ ] 환경 변수 (.env)
  - [ ] 볼륨 마운트 (데이터 지속성)
  - [ ] 헬스 체크

- [ ] SQLAlchemy 설정
  - [ ] engine 생성 (로컬/Neon 분기)
  - [ ] session_maker 구성
  - [ ] ORM 모델 정의
    - [ ] Entity (테이블 매핑)
    - [ ] Relationship (테이블 매핑)
    - [ ] AuditLog (테이블 매핑)

- [ ] 환경 변수 관리
  - [ ] .env.local (로컬 PostgreSQL)
  - [ ] .env.neon (Neon.tech)
  - [ ] .env.test (테스트용 in-memory SQLite)
  - [ ] requirements.txt 업데이트
    - [ ] psycopg2-binary
    - [ ] sqlalchemy
    - [ ] alembic

- [ ] 통합 테스트 기초
  - [ ] Pytest fixtures (db_session, db_client)
  - [ ] 트랜잭션 자동 롤백 (테스트 격리)
  - [ ] 더미 데이터 팩토리
```

**승인 기준**: `pytest tests/` 실행 시 DB 연결 성공

---

### 📦 Week 1 산출물

```
ont_platform/v3/
├── docs/
│   ├── SCHEMA_DESIGN.md (완성)
│   ├── DEPLOYMENT_GUIDE.md (초안)
│   └── POSTGRES_SETUP.md (새파일 - Docker 사용법)
├── docker-compose.dev.yml (신규)
├── .env.example (신규)
├── app/
│   ├── db/
│   │   ├── migrations/ (Alembic 폴더)
│   │   └── models.py (ORM 모델)
│   └── services/
│       └── sparql_service.py (V2로 통합)
├── tests/
│   ├── integration/
│   │   └── test_sparql_full_suite.py (30개 테스트)
│   └── fixtures/
│       └── db_fixtures.py (Pytest fixtures)
└── requirements.txt (업데이트)
```

### 📅 마일스톤

| 날짜 | 체크포인트 |
|------|----------|
| **05-28 (금)** | Task 1-1 완료: rdflib 통합 + 30개 테스트 |
| **05-30 (일)** | Task 1-2 완료: DDL + Alembic + Neon 배포 |
| **05-31 (월)** | Task 1-3 완료: 환경 구성 + fixtures |

---

## Week 2: SPARQL→SQL 번역기 (06-03 ~ 06-07)

### 📌 목표
- 핵심 번역 엔진 완성
- 50개 쿼리 패턴 지원
- 성능 기초 확보

### Task 2-1: 번역기 아키텍처 (06-03 ~ 06-04)

**입력**: SPARQL 쿼리  
**출력**: SQL SELECT 문

```markdown
- [ ] SPARQLTranslator 클래스 설계
  - [ ] triple_to_sql() 핵심 메서드
  - [ ] pattern_extractor() (WHERE절 분석)
  - [ ] sql_generator() (JOIN 생성)
  - [ ] filter_translator() (FILTER→WHERE)
  - [ ] optional_translator() (OPTIONAL→LEFT JOIN)

- [ ] Triple Pattern 파서
  - [ ] 패턴 정규화 (?x, predicate, object)
  - [ ] 변수 바인딩 추적
  - [ ] 상수 vs 변수 구분

- [ ] SQL JOIN 생성
  - [ ] 1-1 엔티티 (기본)
  - [ ] 1-N 관계 (relationships 테이블)
  - [ ] 다중 JOIN (3테이블 이상)
  - [ ] 자기참조 (A가 A를 references)

- [ ] 테스트: tests/unit/test_sparql_translator.py
  - [ ] 기본 패턴 10개
  - [ ] JOIN 패턴 10개
  - [ ] FILTER 패턴 10개
  - [ ] 복합 패턴 10개
  - [ ] 예상: 모두 통과
```

**승인 기준**: 40개 기본 패턴 번역 성공

---

### Task 2-2: 번역기 구현 (06-04 ~ 06-06)

**입력**: 설계 (Task 2-1)  
**출력**: 500줄 번역기 코드

```markdown
- [ ] 구현: app/services/sparql_translator.py
  ```python
  class SPARQLTranslator:
      def translate(self, sparql_query: str) -> str:
          """SPARQL→SQL 변환"""
          parsed = self._parse_sparql(sparql_query)
          patterns = self._extract_patterns(parsed)
          sql = self._generate_sql(patterns)
          optimized = self._optimize(sql)
          return optimized
  ```

- [ ] 핵심 메서드 구현
  - [ ] _parse_sparql() (rdflib 활용)
  - [ ] _extract_patterns() (Triple Pattern 추출)
  - [ ] _generate_sql() (SQL JOIN 생성)
  - [ ] _map_predicate() (온톨로지→테이블 매핑)

- [ ] 최적화
  - [ ] 중복 JOIN 제거
  - [ ] 인덱스 힌트 추가
  - [ ] EXPLAIN 분석

- [ ] 고급 기능
  - [ ] FILTER 조건 변환
    - [ ] 비교 연산자 (>, <, =, !=)
    - [ ] 논리 연산자 (&&, ||)
    - [ ] 함수 (STRLEN, UPPER, REGEX)
  - [ ] OPTIONAL 지원 (LEFT JOIN)
  - [ ] UNION 지원

- [ ] 테스트: tests/integration/test_translator_e2e.py
  - [ ] 실제 쿼리 50개
  - [ ] 예상 결과와 비교
```

**승인 기준**: 50개 쿼리 번역 성공 + SQL 실행 결과 일치

---

### Task 2-3: API 레이어 준비 (06-06 ~ 06-07)

```markdown
- [ ] FastAPI 엔드포인트 설계
  - [ ] POST /ontology/query (SPARQL 입력)
  - [ ] POST /ontology/entities (쓰기)
  - [ ] PUT /ontology/entities/{id} (업데이트)
  - [ ] DELETE /ontology/entities/{id} (삭제)

- [ ] 요청/응답 모델
  - [ ] SPARQLQueryRequest (쿼리 + 컨텍스트)
  - [ ] QueryResponse (결과 + 메타데이터)
  - [ ] EntityCreateRequest (엔티티 데이터)

- [ ] 오류 처리
  - [ ] 잘못된 SPARQL (400)
  - [ ] 번역 실패 (500)
  - [ ] DB 연결 실패 (503)

- [ ] 로깅
  - [ ] 쿼리 실행 시간 기록
  - [ ] SQL 변환 결과 로그
  - [ ] 성능 메트릭 수집
```

**승인 기준**: 5개 엔드포인트 Swagger 문서 생성

---

### 📦 Week 2 산출물

```
ont_platform/v3/
├── app/
│   └── services/
│       ├── sparql_translator.py (500줄, 핵심)
│       └── translator_patterns.py (패턴 정의)
├── docs/
│   └── SPARQL_TRANSLATOR_DESIGN.md (완성)
├── tests/
│   ├── unit/
│   │   └── test_sparql_translator.py (40개)
│   └── integration/
│       └── test_translator_e2e.py (50개)
└── requirements.txt (업데이트)
```

### 📅 마일스톤

| 날짜 | 체크포인트 |
|------|----------|
| **06-04 (수)** | Task 2-1 완료: 설계 + 기본 테스트 |
| **06-06 (금)** | Task 2-2 완료: 번역기 구현 + 50개 패턴 |
| **06-07 (토)** | Task 2-3 완료: API 설계 + Swagger |

---

## Week 3: API 통합 + 동시성 (06-10 ~ 06-14)

### 📌 목표
- FastAPI 엔드포인트 완성
- Write-back 기초 (트랜잭션)
- 동시성 테스트

### Task 3-1: FastAPI 엔드포인트 (06-10 ~ 06-11)

```markdown
- [ ] 읽기 엔드포인트
  - [ ] POST /api/v1/ontology/query (SPARQL)
  - [ ] GET /api/v1/ontology/entities (목록)
  - [ ] GET /api/v1/ontology/entities/{id} (조회)

- [ ] 쓰기 엔드포인트
  - [ ] POST /api/v1/ontology/entities (생성)
  - [ ] PUT /api/v1/ontology/entities/{id} (업데이트)
  - [ ] DELETE /api/v1/ontology/entities/{id} (삭제)

- [ ] 관계 엔드포인트
  - [ ] POST /api/v1/ontology/relationships (생성)
  - [ ] GET /api/v1/ontology/relationships (목록)
  - [ ] DELETE /api/v1/ontology/relationships/{id} (삭제)

- [ ] 테스트: tests/integration/test_api_endpoints.py (15개)
```

---

### Task 3-2: 트랜잭션 + Changelog (06-11 ~ 06-13)

```markdown
- [ ] PostgreSQL 트랜잭션 설정
  - [ ] SERIALIZABLE 격리 레벨 (기본)
  - [ ] 낙관적 잠금 (version 컬럼)
  - [ ] 충돌 감지 + 재시도

- [ ] Changelog 구현
  - [ ] 모든 쓰기 작업 자동 기록
  - [ ] Operation (INSERT, UPDATE, DELETE)
  - [ ] old_state, new_state 저장
  - [ ] 변경 이력 조회 API

- [ ] Audit Log
  - [ ] 사용자 (actor) 기록
  - [ ] 타임스탬프 자동 저장
  - [ ] 감사 대시보드 데이터 제공

- [ ] 테스트: tests/integration/test_concurrency.py (10개)
  - [ ] 동시 쓰기 5개 스레드
  - [ ] 충돌 해결 확인
  - [ ] 데이터 일관성 검증
```

---

### Task 3-3: 문서화 (06-13 ~ 06-14)

```markdown
- [ ] API 문서
  - [ ] Swagger/OpenAPI (자동 생성)
  - [ ] API 엔드포인트 요약
  - [ ] 요청/응답 예제

- [ ] 마이그레이션 가이드
  - [ ] JSONL→PostgreSQL 단계
  - [ ] 무중단 전환 방법
  - [ ] 롤백 계획

- [ ] 운영 가이드
  - [ ] 백업/복구
  - [ ] 성능 튜닝
  - [ ] 모니터링
```

---

### 📦 Week 3 산출물

```
ont_platform/v3/
├── app/
│   └── api/
│       └── routes.py (v1 엔드포인트, 150줄)
├── docs/
│   └── MIGRATION_GUIDE.md (완성)
└── tests/
    └── integration/
        ├── test_api_endpoints.py (15개)
        └── test_concurrency.py (10개)
```

### 📅 마일스톤

| 날짜 | 체크포인트 |
|------|----------|
| **06-11 (수)** | Task 3-1 완료: API 엔드포인트 |
| **06-13 (금)** | Task 3-2 완료: 트랜잭션 + Changelog |
| **06-14 (토)** | Task 3-3 완료: 문서 완성 |

---

## Week 4: 성능 검증 (06-17 ~ 06-21)

### 📌 목표
- 100K-1M 성능 벤치마크
- 최적화 완료
- 프로덕션 준비

### Task 4-1: 벤치마크 스위트 (06-17 ~ 06-18)

```markdown
- [ ] 테스트 데이터 생성
  - [ ] 100K 엔티티 생성 스크립트
  - [ ] 500K 엔티티 생성 스크립트
  - [ ] 1M 엔티티 생성 스크립트
  - [ ] 각 세트별 관계 50% 비율

- [ ] Hot-path 쿼리 벤치마크 (100K entities, 1M relationships 기준)
  - [ ] Simple lookup by ID (목표: < 50ms)
  - [ ] Entity by type filter (목표: < 100ms)
  - [ ] Indexed property filter (목표: < 200ms)
  - [ ] One-hop relation (목표: < 300ms)
  - [ ] Two-hop relation (목표: < 1s)
  
- [ ] 복잡 쿼리 (async/batch 처리)
  - [ ] RDF export, impact analysis
  - [ ] Aggregate query (COUNT, GROUP BY)

- [ ] 테스트: tests/performance/test_scale_validation.py
  - [ ] 각 케이스 3회 반복 (평균 계산)
  - [ ] 결과 CSV 저장
  - [ ] 그래프 생성 (100K vs 500K vs 1M)
```

---

### Task 4-2: 쿼리 최적화 (06-18 ~ 06-20)

```markdown
- [ ] EXPLAIN ANALYZE 분석
  - [ ] 느린 쿼리 식별
  - [ ] 실행 계획 분석
  - [ ] Index Scan vs Sequential Scan 확인

- [ ] 인덱스 최적화
  - [ ] 누락된 인덱스 추가 (필요 시)
  - [ ] Composite Index 고려
  - [ ] JSONB GIN 인덱스 + Expression index 검증

- [ ] 쿼리 튜닝
  - [ ] JOIN 순서 조정
  - [ ] WHERE 절 최적화
  - [ ] 통계 갱신 (ANALYZE)

- [ ] 결과 비교
  - [ ] Before/After 성능 비교
  - [ ] 개선율 계산
```

---

### Task 4-3: 문서화 + 마무리 (06-20 ~ 06-21)

```markdown
- [ ] 성능 보고서
  - [ ] 벤치마크 결과 정리
  - [ ] 목표 달성 여부 평가
  - [ ] 미달 원인 분석 및 계획

- [ ] 아키텍처 최종 문서
  - [ ] ARCHITECTURE_V2.md 작성
  - [ ] Phase 5 완료 선언
  - [ ] Phase 6 제안 (선택)

- [ ] 마이그레이션 최종 체크
  - [ ] JSONL→PostgreSQL 자동화 스크립트 완성
  - [ ] 롤백 계획 검증
  - [ ] 문서 최종 검토

- [ ] 배포 준비
  - [ ] Neon.tech 프로덕션 설정
  - [ ] CI/CD 파이프라인 (선택)
  - [ ] 모니터링 대시보드 (선택)
```

---

### 📦 Week 4 산출물

```
ont_platform/v3/
├── docs/
│   ├── PERFORMANCE_REPORT.md (최종)
│   └── ARCHITECTURE_V2.md (최종)
├── tests/
│   └── performance/
│       ├── test_scale_validation.py
│       ├── benchmark_results.csv
│       └── performance_graphs/
└── scripts/
    └── benchmark_generator.py (데이터 생성)
```

### 📅 마일스톤

| 날짜 | 체크포인트 |
|------|----------|
| **06-18 (수)** | Task 4-1 완료: 벤치마크 결과 |
| **06-20 (금)** | Task 4-2 완료: 최적화 완료 |
| **06-21 (토)** | Task 4-3 완료: 최종 문서 + 배포 준비 |

---

## 📊 전체 일정 (Gantt Chart)

```
Week 1 (05-27 ~ 05-31):
├─ Task 1-1: ███████████ rdflib 통합 (05-27~05-28)
├─ Task 1-2: ███████████ PostgreSQL 스키마 (05-28~05-30)
└─ Task 1-3: ███████████ 환경 구성 (05-30~05-31)

Week 2 (06-03 ~ 06-07):
├─ Task 2-1: ███████ 번역기 설계 (06-03~06-04)
├─ Task 2-2: ███████████ 번역기 구현 (06-04~06-06)
└─ Task 2-3: ███████ API 설계 (06-06~06-07)

Week 3 (06-10 ~ 06-14):
├─ Task 3-1: ███████ API 구현 (06-10~06-11)
├─ Task 3-2: ███████████ 트랜잭션 (06-11~06-13)
└─ Task 3-3: ███████ 문서화 (06-13~06-14)

Week 4 (06-17 ~ 06-21):
├─ Task 4-1: ███████ 벤치마크 (06-17~06-18)
├─ Task 4-2: ███████████ 최적화 (06-18~06-20)
└─ Task 4-3: ███████ 최종화 (06-20~06-21)
```

---

## ✅ Success Criteria

### Code Quality
- [ ] 번역기 500줄 (주석 포함)
- [ ] API 150줄
- [ ] 마이그레이션 도구 100줄
- **총 1,000줄 핵심 코드**

### Testing
- [ ] 단위 테스트: 100개+
- [ ] 통합 테스트: 50개+
- [ ] 성능 테스트: 10개+
- **통과율: ≥ 95%**

### Performance
- [ ] 100K SELECT: < 100ms ✅
- [ ] 1M SELECT: < 1s ✅
- [ ] 동시 쓰기 10개: 격리 보장 ✅

### Documentation
- [ ] SPARQL 번역기 설계서 ✅
- [ ] PostgreSQL 스키마 ✅
- [ ] 마이그레이션 가이드 ✅
- [ ] API 문서 (Swagger) ✅
- [ ] 성능 보고서 ✅

### Deployment
- [ ] 로컬 PostgreSQL 테스트 ✅
- [ ] Neon.tech 배포 테스트 ✅
- [ ] 롤백 계획 ✅

---

## 🔄 의존성 및 위험 요소

### 의존성
```
Task 1-1 (rdflib) 
  ↓
Task 1-2 (스키마) → Task 1-3 (환경)
  ↓
Task 2-1 (설계) → Task 2-2 (구현) → Task 2-3 (API)
  ↓
Task 3-1,2,3 (병렬)
  ↓
Task 4-1,2,3 (순차)
```

### 위험 요소

| 위험 | 영향 | 완화책 |
|------|------|--------|
| SPARQL 파싱 복잡도 | Week 2 연장 | 패턴 축소 (50→30개로 시작) |
| PostgreSQL 성능 저하 | Week 4 지연 | Neon.tech 로컬 마이그레이션 (빠름) |
| 마이그레이션 실패 | 데이터 손실 | JSONL 백업 + dry run 필수 |
| 동시성 버그 | Phase 6 延期 | PostgreSQL SERIALIZABLE 기본값 |

---

## 📋 체크리스트 (Master Checklist)

### Week 1
- [ ] Task 1-1: rdflib 통합 완료
- [ ] Task 1-2: PostgreSQL 스키마 완료
- [ ] Task 1-3: 환경 구성 완료
- [ ] 모든 테스트 통과 (≥ 95%)
- [ ] 로컬 + Neon.tech 양쪽 동작 확인

### Week 2
- [ ] Task 2-1: 번역기 설계 완료
- [ ] Task 2-2: 번역기 구현 완료 (50개 패턴)
- [ ] Task 2-3: API 설계 완료
- [ ] 50개 번역 쿼리 모두 성공
- [ ] Swagger 문서 생성

### Week 3
- [ ] Task 3-1: API 엔드포인트 완료
- [ ] Task 3-2: 트랜잭션 + Changelog 완료
- [ ] Task 3-3: 문서 완성
- [ ] 25개 통합 테스트 통과
- [ ] 10개 동시성 테스트 통과

### Week 4
- [ ] Task 4-1: 벤치마크 완료 (100K, 500K, 1M)
- [ ] Task 4-2: 최적화 완료
- [ ] Task 4-3: 최종 문서 작성
- [ ] 모든 성능 목표 달성
- [ ] 배포 준비 완료

---

## 📞 의사결정 포인트

| 시점 | 결정사항 | 옵션 |
|------|---------|------|
| **06-07 (토)** | Week 2 완료 후 | 번역기 50개 충분한가? |
| **06-14 (토)** | Week 3 완료 후 | 성능 목표 달성 확신 있는가? |
| **06-21 (토)** | Week 4 완료 후 | 프로덕션 배포할 것인가? |

---

## 🚀 Next Steps

1. **Day 1 (05-27)**: 이 로드맵 승인 → 작업 시작
2. **Day 2-3**: Task 1-1 rdflib 통합 시작
3. **일일 스탠드업**: 매일 오후 3시 진행상황 체크

**준비되셨으면 5월 27일 시작 신호를 주세요.**
