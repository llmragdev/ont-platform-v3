# Phase 4 Week 3: Antigravity 비동기 트랜잭션 안전장치 개선 제안서

**작성일**: 2026-05-25  
**작성자**: Antigravity (성능 및 안정성 최적화 에이전트)  
**대상**: v4 백엔드 비동기 처리(`WriteBackWorker` 및 Queue) 트랜잭션 복구 및 예외 모니터링 강화

---

## 1. 제안 배경

Phase 3 및 Phase 4의 비동기 처리 핵심 컴포넌트인 `WriteBackWorker`는 SQLite/JSON 기반 프로토타입에서 PostgreSQL(Neon) 기반으로 전환되는 과도기에 있습니다. 동시성 부하 테스트 결과, 높은 동시 요청 상황에서 시스템 정합성을 유지하기 위해 **비동기 트랜잭션 유실 방지, 장애 모니터링, 수동 복구(Replay) 장치** 도입이 필수적인 것으로 판단되었습니다.

이에 따라, 다음 주차인 **Phase 4 Week 4 (RDF + External Ontology)** 개발 범위에 연계하여 비동기 트랜잭션 안전장치를 신설(추가)할 것을 제안합니다.

---

## 2. 핵심 취약점 및 개선 방안 (Action Items)

### [개선안 ①] PostgreSQL 행 수준 락킹 적용 (`SKIP LOCKED`)
* **현 구조의 문제**: 다중 워커(`WriteBackWorkerPool`) 가동 시 동일한 `PENDING` 데이터를 동시에 긁어와 중복 API 호출(이중 전송)이 일어납니다.
* **개선 제안**: 
  * PostgreSQL의 행 락킹 문법을 도입하여, 작업 조회 시 특정 워커가 잡은 행은 다른 워커가 자동으로 스킵하게 만듭니다.
  ```sql
  -- 개념 DDL 및 쿼리 최적화
  SELECT * FROM writeback_queue 
  WHERE status = 'PENDING' 
  FOR UPDATE SKIP LOCKED 
  LIMIT 10;
  ```
* **성능 효과**: 동시성 쓰기 상황에서 중복 트랜잭션 발생률을 0%로 통제합니다.

### [개선안 ②] 지수 백오프(Exponential Backoff) 컬럼 신설 및 쿼리 최적화
* **현 구조의 문제**: 다음 시도 대기 시간만 계산하고 DB에 반영하지 않아 60초 주기마다 즉시 재시도되는 무한 루프가 발생합니다.
* **개선 제안**: 
  * `WriteBackQueue` 테이블 스키마에 `next_retry_at (TIMESTAMP)` 컬럼을 추가합니다.
  * 워커의 Pending 조회 대상 조건에 시간 필터링을 결합합니다.
  ```sql
  SELECT * FROM writeback_queue 
  WHERE status = 'PENDING' 
    AND (next_retry_at IS NULL OR next_retry_at <= CURRENT_TIMESTAMP);
  ```
* **성능 효과**: 외부 API(SAP 등) 장애 시 즉시 재시도로 인한 대상 서버 과부하(DDOS 효과)를 예방하고 순차적 대기 시간을 보장합니다.

### [개선안 ③] 개별 트랜잭션 커밋 처리 (Commit Granularity)
* **현 구조의 문제**: 큐 내의 모든 작업 루프가 완전히 종료된 후 일괄적으로 `db.commit()`을 수행하여 중간 크래시 시 데이터 불일치가 일어납니다.
* **개선 제안**: 
  * 비동기 작업 루프 내부에서 개별 아이템 처리(`_process_single_item`)마다 즉시 트랜잭션을 Commit 처리합니다.
* **성능 효과**: 서버 장애 혹은 예외 크래시 시에도 이미 전송에 성공한 항목들의 성공 상태가 완벽히 DB에 기록되어 이중 전송의 빈틈을 차단합니다.

### [개선안 ④] 데드 레터 큐(DLQ) 적재 및 수동 재수행(Replay) 시스템 구축
* **현 구조의 문제**: 최대 재시도(3회) 초과 시 FAILED 상태로 정체되며, 수동 복구나 재전송을 위한 인터페이스가 부재합니다.
* **개선 제안**:
  * 3회 실패 시 격리용 상태값 `DLQ`(Dead Letter Queue) 또는 별도 격리 테이블로 이관합니다.
  * `POST /api/writeback/replay/{queue_id}` 형태로 관리자가 실패한 특정 트랜잭션을 다시 큐에 강제 투입할 수 있는 **Replay API**를 신설합니다.
  * 프론트엔드 AuditDashboard UI에 Replay 실행 버튼을 추가 배치합니다.

---

## 3. Phase 4 Week 4 지시서 반영 방안 (Gap 분석)

Week 4 RDF 지시서([Claude.md](file:///E:/ontology_edu/X_ont_std/week_instructions/PHASE4/Week_4_RDF/Claude.md) 및 [Antigravity.md](file:///E:/ontology_edu/X_ont_std/week_instructions/PHASE4/Week_4_RDF/Antigravity.md))를 정밀 분석한 결과, 외부 API 임포트 기능 및 대량 SPARQL 질의 처리에 `async/await`가 도입될 뿐 **장애 재시도, DLQ 격리, 멱등성 보장은 기획되어 있지 않습니다.**

따라서 다음 조치를 건의합니다.

* **조치 제안**: **추가(Add)**
  * Week 4의 외부 API 임포트(`OntologyImporter`) 및 배치 쿼리 엔드포인트 구현 시, 본 개선 제안서의 **트랜잭션 락킹(`SKIP LOCKED`) 및 Replay API/UI** 요건을 신규 구현 범위로 지정하여 개발할 것을 강력하게 권고합니다.
