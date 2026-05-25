# Phase 4 Week 3: Antigravity 성능 및 비동기 처리 종합 분석 보고서

**작성일**: 2026-05-25  
**작성자**: Antigravity (성능 최적화 에이전트)  
**대상**: ont_platform v4.0 비동기 처리 및 트랜잭션 안전성 진단

---

## 1. 개요

Phase 4 Week 3에서 Antigravity는 PostgreSQL(Neon) 전환에 따른 성능 기준선(Baseline)을 정의하고, 메타데이터 및 감시 시스템의성능을 극대화하기 위한 인덱싱 및 Redis 캐싱 아키텍처 설계를 완료하였습니다. 

본 보고서에서는 백엔드 비동기 처리(`WriteBackWorker` 및 Queue 시스템)의 트랜잭션 안전성을 추가로 정밀 검증하고, 파악된 취약점들을 보완하기 위한 개선안을 제안합니다. 상세한 비동기 안전장치 개선 제안은 별도 보고서인 [PHASE4_WEEK3_antigravity_비동기_트랜잭션_안정장치_개선제안_20260525.md](file:///E:/ontology_edu/X_ont_std/cross-source-comparison/PHASE4_WEEK3_antigravity_비동기_트랜잭션_안정장치_개선제안_20260525.md)를 참고해 주시기 바랍니다.

또한, 해당 개선 사항이 다음 주차인 **Phase 4 Week 4 (RDF + External Ontology)** 지시서에 포함되어 있는지 분석하여 추가/보완 방향을 확립합니다.

---

## 2. 현 비동기 처리 아키텍처의 취약점 진단

v3 및 v4 백엔드 서비스 코드(`app/services/write_back_worker.py`) 진단 결과, 다음과 같은 4대 트랜잭션 취약점이 식별되었습니다.

### ① 다중 워커 경쟁 상태 (Race Condition)
* **현상**: `WriteBackWorkerPool`을 통해 다수의 워커가 병렬로 가동될 때, 각각의 워커가 동일한 쿼리 조건으로 `PENDING` 데이터를 긁어옵니다.
* **리스크**: 특정 행에 대한 선점(Locking) 장치가 없기 때문에, 동일한 비동기 전송 항목이 여러 워커에 의해 중복 실행되어 외부 시스템(SAP 등)에 **이중 결제/이중 승인**과 같은 중복 트랜잭션을 발생시킵니다.

### ② 지수 백오프(Exponential Backoff)의 실질적 무력화
* **현상**: 예외 발생 시 `next_retry_delay` 시간(지수 곱 계산)은 연산되지만, 정작 데이터베이스에는 이를 반영할 `next_retry_at` 컬럼이 부재하며, 쿼리 조회 시 시간 필터링이 적용되지 않습니다.
* **리스크**: 실패한 작업이 지수 백오프 지연 시간을 대기하지 않고, 워커의 다음 최소 주기(60초)마다 즉시 재시도되어 외부 시스템에 지속적인 트랜잭션 과부하를 줍니다.

### ③ 배치 커밋에 따른 데이터 유실 및 중복 전송
* **현상**: 대기 큐 루프를 모두 가동한 뒤 마지막 한 번만 `db.commit()`을 수행합니다.
* **리스크**: 처리 루프 도중 서버가 크래시 나면, 이미 외부 시스템에 전송 완료된 성공 내역이 DB에 반영되지 않아(`PENDING` 유지), 재구동 시 동일한 항목이 중복으로 재호출됩니다.

### ④ 일시적 통신 오류의 즉시 실패 처리 (Deadlock & Failure)
* **현상**: 오직 `TimeoutError`만 재시도(Retry)로 분류되고, 나머지 모든 예외(`Exception`)는 즉시 `FAILED` 상태로 차단됩니다.
* **리스크**: 네트워크 일시 단절, 503 Service Unavailable 등 일시적인 물리 오류 발생 시에도 재수행 기회 없이 작업이 영구 실패 처리됩니다.

---

## 3. Phase 4 Week 4 지시서 반영 여부 및 Gap 분석

개선 제안 사항들이 다음 개발 주차인 [Week 4 RDF 지시서(Claude.md)](file:///E:/ontology_edu/X_ont_std/week_instructions/PHASE4/Week_4_RDF/Claude.md) 및 [Week 4 Antigravity 지시서(Antigravity.md)](file:///E:/ontology_edu/X_ont_std/week_instructions/PHASE4/Week_4_RDF/Antigravity.md)에 반영되어 있는지 분석한 결과는 다음과 같습니다.

### 🔍 분석 결과: **계획 내 반영 안 됨 (추가 필요)**

* **Claude (Backend) Week 4**:
  * 외부 API 임포트(`OntologyImporter`)에 `async/await` 및 `httpx.AsyncClient`를 도입하지만, 네트워크 통신 실패에 대응하는 **재시도 큐나 실패 로깅, 멱등성 제어 장치가 전혀 기획되지 않았습니다.**
  * `batch_sparql_queries` API의 파라미터로 `BackgroundTasks`를 선언해 두었으나, 실제 백그라운드 큐나 모니터링 모듈과 연계되지 않고 단순 루프로 순차 실행되는 구조입니다.
* **Antigravity (Performance) Week 4**:
  * RDF 로드 및 SPARQL 쿼리 속도 기준선 수립, Cytoscape.js 렌더링 최적화, 외부 임포트의 동시 5개 병렬 제한 등 속도 향상 위주로만 짜여 있으며, **비동기 안전성에 대한 성능 벤치마크나 지연 모니터링은 누락**되어 있습니다.

> [!IMPORTANT]
> 현재 Phase 4 Week 4 지시서에는 비동기 처리의 유실 방지 및 트랜잭션 복구에 대한 설계/구현 항목이 **부재**하므로, 이를 단순 보완하는 수준이 아니라 **새로운 필수 요건으로 신설(추가)하여 가이드라인에 반영해야 합니다.**

---

## 4. 비동기 처리 개선을 위한 구체적인 제안 사항

동시성 및 유실 방지를 완벽하게 처리하기 위해 다음 4가지 핵심 요건을 차기 아키텍처 태스크로 **추가(Add)**할 것을 제안합니다.

### 1) PostgreSQL 행 수준 락킹 적용 (Skip Locked)
* **구현**: 워커 조회 쿼리에 `with_for_update(skip_locked=True)`를 적용합니다.
* **효과**: 다중 워커 가동 시 다른 워커가 락을 잡은 행은 알아서 스킵하므로 중복 트랜잭션 실행을 원천 차단합니다.

### 2) 개별 트랜잭션 커밋 처리
* **구현**: 루프 전체가 아닌, 루프 내 단일 아이템 처리 완료(`_process_single_item`) 즉시 `db.commit()`을 수행하도록 단위를 축소합니다.
* **효과**: 중간 크래시 시에도 이미 처리된 항목의 성공 상태는 완벽히 보존됩니다.

### 3) 데드 레터 큐(DLQ) 및 수동 재수행(Replay) API 신설
* **구현**: 
  * 3회 초과 실패 시 단순 차단이 아닌 관리자 확인용 격리 상태(`DLQ` 또는 별도 상태)로 격리.
  * `POST /api/writeback/replay/{queue_id}` API를 구현하여 특정 ID의 실패 건을 큐에 재생(Replay) 적재할 수 있는 수단 확보.
* **효과**: 유실되거나 실패한 비동기 건을 완벽하게 모니터링하고 가시화하여 재수행할 수 있습니다.

### 4) 재시도 스케줄링 쿼리 개편
* **구현**: 
  * `WriteBackQueue` 스키마에 `next_retry_at` 컬럼 추가.
  * 워커 쿼리 필터에 `WriteBackQueue.next_retry_at <= datetime.utcnow()` 적용하여 실질적인 지수 백오프 적용.
