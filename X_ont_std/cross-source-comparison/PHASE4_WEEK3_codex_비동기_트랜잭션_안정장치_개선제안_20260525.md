# Phase 4 Week 3 종합보고서 보완 제안: 비동기 트랜잭션 안정장치

**작성일**: 2026-05-25  
**대상 문서**: `cross-source-comparison/PHASE4_WEEK3_에이전트명_종합보고서` 계열  
**관련 지시서**: `week_instructions/PHASE4/Week_4_RDF`  
**요약**: Week 4 RDF 지시서에는 비동기 import, batch SPARQL, 트랜잭션 배치가 언급되어 있으나, 비동기 처리 중 유실될 수 있는 트랜잭션을 감시하고 재수행하는 운영 안전장치는 명시되어 있지 않다. Week 4 수행 범위에 보완 항목으로 추가하는 것을 권장한다.

---

## 1. 왜 필요한가

Phase 4 Week 4 RDF 작업에는 다음과 같은 비동기/배치성 처리가 포함된다.

- DBpedia/Wikidata 외부 온톨로지 import
- RDF file import
- batch SPARQL query
- RDF graph cache/index 생성
- graph optimization/background preprocessing
- 외부 Linked Data describe/fetch

이 처리들은 API 요청과 실제 데이터 반영 시점이 분리될 수 있다. 따라서 API가 성공 응답을 반환했지만 백그라운드 작업이 실패하거나, worker가 중간에 종료되거나, 외부 API 호출 후 DB commit 전에 장애가 발생하면 “요청은 있었지만 최종 상태가 불명확한” 트랜잭션이 생길 수 있다.

운영 관점에서는 이를 방치하면 다음 문제가 생긴다.

- import 일부만 반영되고 완료로 보이는 상태
- RDF triple/index/cache 불일치
- 같은 import/job의 중복 수행
- 외부 시스템에는 반영됐지만 내부 DB는 실패로 남는 상태
- 실패 작업 원인 추적 불가
- 재처리 대상 선별 불가

---

## 2. Week 4 지시서 반영 여부 판단

### 이미 있는 내용

Week 4 RDF 지시서에는 다음 내용이 있다.

- Claude: `async def import_from_dbpedia`, `async def import_from_wikidata`
- Claude: `async def execute_sparql`, `batch_sparql_queries`
- Claude: `cache_rdf_index`, `optimize_graph_structure`
- Antigravity: import 최적화, 병렬 요청, 트랜잭션 배치
- Codex: importer UI, SPARQL workbench UI

### 부족한 내용

다음 안정장치는 명시되어 있지 않다.

- Transactional Outbox
- Job/Import Queue 상태 모델
- worker claim/lock
- idempotency key
- retry/backoff
- dead-letter queue
- stale job reconciler
- import/job monitoring API
- 운영 UI에서 재수행 버튼 및 실패 원인 표시
- 성능/장애 테스트에서 유실 복구 시나리오

따라서 Week 4에 이미 있는 비동기 처리 항목은 “보완”하고, 없다면 “추가 Task”로 편성하는 것이 좋다.

---

## 3. 종합보고서에 추가할 권장 문구

아래 문구를 `PHASE4_WEEK3_에이전트명_종합보고서`의 “Week 4 리스크/보완 제안” 또는 “다음 단계”에 추가하는 것을 권장한다.

```md
### 비동기 트랜잭션 안정장치 보완 필요

Week 4 RDF 작업에는 외부 온톨로지 import, batch SPARQL, RDF index/cache 생성 등 비동기 또는 배치성 처리가 포함된다. 해당 처리에서 API 요청 성공과 실제 데이터 반영 시점이 분리될 수 있으므로, 유실 트랜잭션을 감시하고 재수행할 수 있는 안정장치가 필요하다.

Week 4 지시서에 이미 비동기 처리 항목이 있다면 다음을 보완한다.
- Transactional Outbox 또는 Job Queue 저장
- PENDING/RUNNING/SUCCEEDED/FAILED/DEAD_LETTER 상태 관리
- idempotency key 기반 중복 실행 방지
- retry_count, next_retry_at 기반 재시도
- stale RUNNING 작업 감지 및 재큐잉
- 실패 작업 dead-letter 보관 및 수동 재수행 API
- 모니터링 API 및 운영 UI 노출

Week 4 지시서에 없는 경우 별도 Task로 추가한다.
```

---

## 4. 에이전트별 보완 제안

### Claude 보완 제안

Week 4 Claude 지시서에 다음 backend task를 추가한다.

```md
### 추가 Task: Async Job Reliability Layer

**목표**: RDF import, external ontology fetch, batch SPARQL, RDF index/cache 작업의 유실 방지 및 재수행 체계 구현

**요구사항**:
- `async_jobs` 또는 `rdf_import_jobs` 테이블 추가
- 상태: `PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`, `DEAD_LETTER`
- 필드: `job_id`, `job_type`, `idempotency_key`, `payload`, `status`, `retry_count`, `max_retries`, `next_retry_at`, `locked_by`, `locked_at`, `lock_expires_at`, `last_error`, `created_at`, `updated_at`
- worker claim 시 `SELECT ... FOR UPDATE SKIP LOCKED` 사용
- job 생성과 import 요청 기록을 같은 DB transaction 안에서 처리
- 실패 시 exponential backoff
- max retry 초과 시 dead-letter 처리
- stale RUNNING job reconciler 구현
- 재수행 API:
  - `POST /api/jobs/{job_id}/retry`
  - `POST /api/jobs/{job_id}/cancel`
  - `GET /api/jobs`
  - `GET /api/jobs/statistics`

**DoD**:
- worker 중단 후 재시작 시 PENDING/RUNNING 유실 없이 복구
- 같은 idempotency key 중복 요청 시 중복 import 방지
- 실패 job 재수행 가능
- stale lock 자동 회수
```

### Codex 보완 제안

Week 4 Codex 지시서에 다음 frontend task를 추가한다.

```md
### 추가 Task: Async Job Monitor UI

**목표**: RDF import, SPARQL batch, graph cache/index 작업의 진행 상태와 실패 재처리를 운영자가 확인할 수 있는 UI 제공

**컴포넌트**:
- `JobMonitorPanel`
- `ImportJobStatusBadge`
- `DeadLetterJobTable`
- `RetryJobButton`

**표시 항목**:
- job_id, job_type, status
- progress_percent
- retry_count / max_retries
- next_retry_at
- locked_by / locked_at
- last_error
- created_at / updated_at

**상호작용**:
- 실패 작업 재수행
- stale 작업 재큐잉 요청
- dead-letter 상세 보기
- job type/status 필터

**DoD**:
- mock job 데이터로 PENDING/RUNNING/SUCCEEDED/FAILED/DEAD_LETTER 상태 표시
- retry 버튼 클릭 시 API 호출 또는 mock 상태 변경
- import UI에서 생성된 job_id를 monitor로 연결
```

### Antigravity 보완 제안

Week 4 Antigravity 지시서에 다음 performance/reliability task를 추가한다.

```md
### 추가 Task: Async Reliability Benchmark

**목표**: 비동기 작업 유실 방지 장치가 실제 장애 상황에서 복구 가능한지 검증

**시나리오**:
- worker 처리 중 강제 종료 후 재시작
- 외부 DBpedia/Wikidata timeout
- 같은 import 요청 중복 제출
- PostgreSQL connection failure
- lock 만료 후 stale RUNNING job 복구
- dead-letter 전환 및 수동 retry

**지표**:
- lost_job_count = 0
- duplicate_import_count = 0
- stale_recovered_count
- retry_success_rate
- dead_letter_count
- mean_time_to_recovery

**DoD**:
- 유실 job 0건
- 중복 반영 0건
- worker crash 후 재처리 성공
- retry/backoff 정책 검증
```

---

## 5. 권장 아키텍처

### 최소 안정장치

1. API 요청 수신
2. DB transaction 시작
3. `async_jobs`에 job 저장
4. 필요한 경우 `audit_logs`에도 요청 기록 저장
5. DB commit
6. worker가 PENDING job claim
7. RUNNING 전환
8. 작업 수행
9. 성공 시 SUCCEEDED
10. 실패 시 retry 또는 DEAD_LETTER

### 핵심 원칙

- API 성공 응답은 “job 접수 성공”을 의미해야 한다.
- 실제 처리 성공은 job status로 별도 추적한다.
- 모든 비동기 작업은 idempotency key를 가져야 한다.
- worker는 작업을 가져갈 때 lock을 잡아야 한다.
- RUNNING 상태가 너무 오래 지속되면 stale로 보고 재큐잉해야 한다.
- 실패 원인은 dead-letter에 보존되어야 한다.

---

## 6. Week 4 반영 방식

권장 문구:

```md
Week 4 RDF 지시서에 비동기 import/batch/cache 작업이 이미 포함되어 있으므로, 해당 작업에 “비동기 트랜잭션 안정장치”를 보완한다. 만약 각 에이전트 지시서에 구현 범위가 명시되어 있지 않다면, Week 4 추가 Task로 Async Job Reliability Layer, Async Job Monitor UI, Async Reliability Benchmark를 추가한다.
```

우선순위:

1. Claude: backend job/outbox/retry/reconciler
2. Codex: job monitor/retry UI
3. Antigravity: crash/retry/idempotency benchmark

---

## 7. 결론

`ont_platform/v4`는 PostgreSQL 기반으로 전환되어 트랜잭션 안정성이 좋아졌지만, Week 4 RDF의 비동기 import, batch SPARQL, cache/index 작업은 별도의 유실 감시 및 재수행 체계가 필요하다. Week 4에 이미 비동기 처리 항목이 있으므로 “보완”으로 넣는 것이 자연스럽고, 지시서에 명시가 없으면 별도 추가 Task로 편성하는 것이 좋다.
