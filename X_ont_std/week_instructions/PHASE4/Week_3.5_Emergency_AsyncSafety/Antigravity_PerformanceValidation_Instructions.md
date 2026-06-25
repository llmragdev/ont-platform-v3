# Phase 4 Week 3.5: Antigravity 성능 검증 지시서

**작업명**: WriteBackWorker 비동기 안전장치 성능 검증  
**시작**: 2026-05-25 오후 2시 (Day 1 14:00)  
**소요시간**: 2-3시간 (병렬 테스트)  
**완료 기준**: 4가지 성능 시나리오 모두 통과 + 최종 성능 보고서 제출

---

## 🎯 작업 개요

Claude가 코드 수정을 진행하는 동안, Antigravity는 **동시성**, **복원력**, **데이터 무결성**을 중심으로 WriteBackWorker의 성능을 병렬로 검증합니다.

### 검증 범위
- ✅ 다중 워커 중복 실행률 (목표: 0%)
- ✅ 지수 백오프 적용 시 외부 API 부하 감소 (예상: 60초 주기 → 120s/240s/480s)
- ✅ 트랜잭션 유실 (목표: 0건)
- ✅ 전체 성능 메트릭 집계 (처리량, 레이턴시, 실패율)

---

## 📊 성능 메트릭 정의

### 1. 중복 실행 감지율 (Duplicate Execution Detection)
```
대상: PENDING 상태 아이템 동일 처리 횟수
측정: 2개+ 워커 동시 실행 시 동일 item_id가 몇 번 처리되는가
계산식: (중복 처리된 item 수 / 전체 item 수) × 100%
성공 기준: ≤ 0% (1회만 정확히 처리)
```

### 2. 지수 백오프 준수율 (Exponential Backoff Compliance)
```
대상: TimeoutError 발생 후 재시도 간격
측정: retry_count별 next_retry_at과 실제 재시도 시점 차이
계산식: |예상 재시도 시간 - 실제 재시도 시간| ≤ 5초
성공 기준: ≥ 95% (20개 재시도 중 19개 이상 정확)
```

### 3. 트랜잭션 유실률 (Data Loss Rate)
```
대상: 처리 완료 후 DB 반영 상태
측정: 크래시 전 처리된 item의 상태 변경 여부
계산식: (DB에서 SYNCED/FAILED로 변경된 item 수 / 크래시 전 처리된 수) × 100%
성공 기준: 100% (모든 처리 완료 item이 DB에 반영)
```

### 4. 처리 성능 (Throughput & Latency)
```
대상: WriteBackWorker 처리 속도
측정:
  - 처리량: item/분 (예: 100개 item/분)
  - 평균 레이턴시: ms/item (예: 600ms/item)
  - P95 레이턴시: ms/item
성공 기준: 처리량 ≥ 50 item/분, 레이턴시 ≤ 1000ms
```

---

## 🧪 테스트 시나리오 1: 다중 워커 중복 실행률 검증

**목표**: FOR UPDATE SKIP LOCKED가 정말 중복 실행을 막는가?

**준비**:
```python
# write_back_worker_performance_test.py

import concurrent.futures
import time
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models import WriteBackQueue
from app.services.write_back_worker import WriteBackWorker
from app.config import Config

# 테스트 DB (SQLite in-memory)
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)

# 100개 PENDING 아이템 생성
session = Session(engine)
for i in range(100):
    item = WriteBackQueue(
        id=f"test_item_{i:03d}",
        target_system="SAP",
        payload={"order_id": i},
        status="PENDING",
        retry_count=0
    )
    session.add(item)
session.commit()

# 실행 로그 (item_id 별 처리 횟수)
execution_log = {}

# 워커 함수
def run_worker(worker_id: int, num_iterations: int):
    """워커 인스턴스 실행"""
    worker = WriteBackWorker(config=Config())
    for _ in range(num_iterations):
        result = worker.process_pending()
        for item_id in result.get("processed_ids", []):
            execution_log[item_id] = execution_log.get(item_id, 0) + 1
        time.sleep(1)  # 1초 대기 후 재조회

# 2개 워커 동시 실행 (5번 반복)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    futures = [
        executor.submit(run_worker, worker_id=1, num_iterations=5),
        executor.submit(run_worker, worker_id=2, num_iterations=5),
    ]
    concurrent.futures.wait(futures)
```

**실행 및 검증**:
```python
# 중복 실행 계산
duplicates = {item_id: count for item_id, count in execution_log.items() if count > 1}
duplicate_rate = (len(duplicates) / len(execution_log)) * 100

print(f"Total items: {len(execution_log)}")
print(f"Duplicates: {len(duplicates)}")
print(f"Duplicate rate: {duplicate_rate:.2f}%")

# 성공 기준
assert duplicate_rate == 0.0, f"Expected 0% duplicates, got {duplicate_rate}%"
assert len(duplicates) == 0, f"Found {len(duplicates)} duplicated items"
```

**기대 결과**:
```
✅ Total items: 100
✅ Duplicates: 0
✅ Duplicate rate: 0.00%
✅ Test PASSED
```

---

## 🧪 테스트 시나리오 2: 지수 백오프 지연 준수율

**목표**: next_retry_at이 정확한 시간에 조회되는가?

**준비**:
```python
# backoff_compliance_test.py

from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import time

# TimeoutError 유발 설정
def mock_api_call_with_timeout(payload):
    """첫 3회는 TimeoutError 발생"""
    mock_api_call_with_timeout.call_count += 1
    if mock_api_call_with_timeout.call_count <= 3:
        raise TimeoutError("API timeout")
    return {"status": "success"}

mock_api_call_with_timeout.call_count = 0

# 테스트 item 생성
session = Session(engine)
item = WriteBackQueue(
    id="backoff_test_item",
    target_system="SAP",
    payload={"order_id": 999},
    status="PENDING",
    retry_count=0
)
session.add(item)
session.commit()
```

**실행 및 검증**:
```python
# 지수 백오프 검증
config = Config()
worker = WriteBackWorker(config=config)

# 1차 시도: PENDING → TimeoutError → retry_count=1, next_retry_at=now+120s
worker.process_pending()
item = session.query(WriteBackQueue).filter(
    WriteBackQueue.id == "backoff_test_item"
).first()

expected_retry_1 = datetime.utcnow() + timedelta(seconds=120)
assert item.retry_count == 1, f"Expected retry_count=1, got {item.retry_count}"
assert item.status == "PENDING", f"Expected PENDING, got {item.status}"
assert abs((item.next_retry_at - expected_retry_1).total_seconds()) <= 5, \
    f"Retry 1 backoff mismatch: expected {expected_retry_1}, got {item.next_retry_at}"
print(f"✅ Retry 1: {item.next_retry_at} (120s backoff)")

# 2차 시도: 시간 도달 전 조회 → 스킵 확인
earlier_time = datetime.utcnow() - timedelta(seconds=60)
pending_items = session.query(WriteBackQueue).filter(
    WriteBackQueue.status == "PENDING",
    (WriteBackQueue.next_retry_at.is_(None)) |
    (WriteBackQueue.next_retry_at <= earlier_time)
).all()
assert "backoff_test_item" not in [x.id for x in pending_items], \
    "Item should be skipped when next_retry_at not reached"
print(f"✅ Time-based filtering works: item skipped until {item.next_retry_at}")

# 3차 시도: 시간 도달 후 조회 → 재처리 확인
time.sleep(121)  # 121초 대기
pending_items_after = session.query(WriteBackQueue).filter(
    WriteBackQueue.status == "PENDING",
    (WriteBackQueue.next_retry_at.is_(None)) |
    (WriteBackQueue.next_retry_at <= datetime.utcnow())
).all()
assert "backoff_test_item" in [x.id for x in pending_items_after], \
    "Item should be picked up after next_retry_at is reached"
print(f"✅ Backoff 도달 후 재시도 가능: {datetime.utcnow()}")
```

**기대 결과**:
```
✅ Retry 1: 2026-05-25 14:02:00 (120s backoff)
✅ Time-based filtering works: item skipped until 2026-05-25 14:02:00
✅ Backoff 도달 후 재시도 가능: 2026-05-25 14:02:01
✅ Test PASSED
```

---

## 🧪 테스트 시나리오 3: 트랜잭션 유실 측정

**목표**: 프로세스 크래시 시 처리된 항목이 정말 저장되는가?

**준비**:
```python
# data_loss_test.py

import os
import signal
import multiprocessing
from datetime import datetime

def worker_process_with_crash(item_count: int, crash_at_item: int):
    """item_count 중 crash_at_item번째에서 의도적으로 크래시"""
    from app.services.write_back_worker import WriteBackWorker
    
    session = Session(engine)
    worker = WriteBackWorker(config=Config())
    
    for i in range(item_count):
        # crash_at_item번째에 강제 종료 (이전 아이템은 커밋되어야 함)
        if i == crash_at_item:
            os.kill(os.getpid(), signal.SIGTERM)
        
        try:
            worker._process_single_item(session.query(WriteBackQueue).filter(
                WriteBackQueue.status == "PENDING"
            ).first())
            session.commit()
        except Exception as e:
            session.commit()  # 실패해도 커밋

# 테스트 setup
session = Session(engine)
for i in range(20):
    item = WriteBackQueue(
        id=f"crash_test_{i:02d}",
        target_system="SAP",
        payload={"order_id": i},
        status="PENDING"
    )
    session.add(item)
session.commit()
```

**실행 및 검증**:
```python
# 프로세스 실행 (10번째 아이템에서 크래시)
process = multiprocessing.Process(
    target=worker_process_with_crash,
    args=(20, 10)
)
process.start()
time.sleep(15)  # 크래시 발생 대기
process.terminate()
process.join()

# 크래시 후 상태 확인
session = Session(engine)
synced_items = session.query(WriteBackQueue).filter(
    WriteBackQueue.status == "SYNCED"
).all()
pending_items = session.query(WriteBackQueue).filter(
    WriteBackQueue.status == "PENDING"
).all()

print(f"SYNCED items: {len(synced_items)}")
print(f"PENDING items: {len(pending_items)}")

# 크래시 이전 아이템(0-9)은 모두 SYNCED
synced_ids = [int(x.id.split('_')[2]) for x in synced_items]
assert min(synced_ids) == 0 and max(synced_ids) == 9, \
    f"Expected items 0-9 to be SYNCED, got {synced_ids}"
assert len(pending_items) == 10, \
    f"Expected 10 pending items, got {len(pending_items)}"

print(f"✅ Data loss rate: 0%")
print(f"✅ Crashed items persisted: {len(synced_items)}/{10}")
```

**기대 결과**:
```
✅ SYNCED items: 10
✅ PENDING items: 10
✅ Data loss rate: 0%
✅ Crashed items persisted: 10/10
✅ Test PASSED
```

---

## 📈 테스트 시나리오 4: 성능 메트릭 집계

**목표**: 전체 성능 지표를 수집하여 Week 3.5 최종 보고서에 제출

**준비**:
```python
# performance_metrics_test.py

import time
from datetime import datetime
from statistics import mean, stdev
import json

# 성능 측정을 위한 메트릭 클래스
class PerformanceMetrics:
    def __init__(self):
        self.latencies = []  # ms/item
        self.processed_count = 0
        self.failed_count = 0
        self.start_time = None
        self.end_time = None
    
    def record_item_processing(self, processing_time_ms: float):
        """개별 item 처리 시간 기록"""
        self.latencies.append(processing_time_ms)
        self.processed_count += 1
    
    def calculate_metrics(self) -> dict:
        """메트릭 계산"""
        duration_minutes = (self.end_time - self.start_time).total_seconds() / 60
        throughput = self.processed_count / duration_minutes
        
        return {
            "total_processed": self.processed_count,
            "total_failed": self.failed_count,
            "throughput_items_per_min": round(throughput, 2),
            "avg_latency_ms": round(mean(self.latencies), 2),
            "p95_latency_ms": round(sorted(self.latencies)[int(len(self.latencies)*0.95)], 2),
            "duration_minutes": round(duration_minutes, 2)
        }
```

**실행 및 검증**:
```python
# 500개 아이템으로 성능 테스트
metrics = PerformanceMetrics()
metrics.start_time = datetime.utcnow()

session = Session(engine)
for i in range(500):
    item = WriteBackQueue(
        id=f"perf_item_{i:04d}",
        target_system="SAP",
        payload={"order_id": i},
        status="PENDING"
    )
    session.add(item)
session.commit()

# 워커 실행
worker = WriteBackWorker(config=Config())
start = time.time()
result = worker.process_pending()
processing_time = (time.time() - start) * 1000  # ms

metrics.record_item_processing(processing_time / len(result['processed_ids']))
metrics.end_time = datetime.utcnow()

# 메트릭 출력
final_metrics = metrics.calculate_metrics()
print("=" * 60)
print("PERFORMANCE METRICS (500 items)")
print("=" * 60)
for key, value in final_metrics.items():
    print(f"{key}: {value}")

# 성공 기준
assert final_metrics["throughput_items_per_min"] >= 50, \
    f"Throughput too low: {final_metrics['throughput_items_per_min']}"
assert final_metrics["avg_latency_ms"] <= 1000, \
    f"Latency too high: {final_metrics['avg_latency_ms']}"
```

**기대 결과**:
```
============================================================
PERFORMANCE METRICS (500 items)
============================================================
total_processed: 500
total_failed: 0
throughput_items_per_min: 125.45
avg_latency_ms: 480.30
p95_latency_ms: 820.15
duration_minutes: 3.99
✅ All metrics within acceptable ranges
✅ Test PASSED
```

---

## 📋 최종 체크리스트

구현 완료 후 4가지 테스트 모두 실행:

- [ ] 테스트 1: 다중 워커 중복 실행률 ≤ 0%
  - 2개 워커, 5반복, 100개 item
  - 결과: 중복 건수 = 0

- [ ] 테스트 2: 지수 백오프 준수율 ≥ 95%
  - 1회 실패: next_retry_at = now+120s
  - 2회 실패: next_retry_at = now+240s
  - 3회 실패: next_retry_at = now+480s → DLQ
  - 시간 도달 전 조회: 스킵 확인

- [ ] 테스트 3: 트랜잭션 유실률 = 0%
  - 20개 item 중 10번째 크래시
  - 크래시 전 처리된 10개 모두 SYNCED

- [ ] 테스트 4: 성능 메트릭
  - 처리량 ≥ 50 item/분
  - 평균 레이턴시 ≤ 1000ms
  - P95 레이턴시 ≤ 1500ms

---

## 🚀 최종 보고서 제출 형식

모든 테스트 완료 후, 다음 형식으로 `task_logs/antigravity/` 폴더에 보고서 작성:

**파일명**: `20260525_HHMM_Week3.5_AsyncSafety_Performance_Report.md`

**내용 구성**:
```markdown
# Week 3.5 비동기 안전장치 성능 검증 보고서

## 테스트 결과 요약
- 다중 워커 중복 실행률: 0% ✅
- 지수 백오프 준수율: 95%+ ✅
- 트랜잭션 유실률: 0% ✅
- 성능 메트릭: 모두 통과 ✅

## 상세 테스트 결과
[각 테스트별 상세 결과 + 로그]

## 권장사항
[성능 최적화 제안 또는 추가 개선사항]

## 완료 일시
2026-05-25 오후 XX:XX
```

---

**예상 완료**: 2026-05-25 오후 5시경  
**준비**: Day 1 14:00에 Claude 코드 수정 시작과 병렬 실행
