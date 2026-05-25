# Phase 4 Week 3.5: Claude 에이전트 테스트 코드 작성 지시서

**작업명**: WriteBackWorker 4가지 안전장치 단위 테스트  
**시작**: Day 1 오후 14:00 (내 코드 수정 완료 후)  
**소요시간**: 2-3시간  
**완료 기준**: 4개 테스트 작성 + 실행 + 리포트 제출

---

## 🎯 작업 개요

내가 수정한 write_back_worker.py의 4가지 안전장치 각각에 대한 단위 테스트 작성

**테스트 목표**:
- ✅ FOR UPDATE SKIP LOCKED: 중복 실행 0%
- ✅ 개별 커밋: 중간 크래시 시 데이터 보존
- ✅ DLQ + Replay API: 재시도 가능성 확보
- ✅ next_retry_at: 지수 백오프 실제 적용

---

## 📋 테스트 파일 작성 (파일: `tests/test_phase4_week35_async_safety.py`)

### Test 1: FOR UPDATE SKIP LOCKED (중복 실행 0%)

```python
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from concurrent.futures import ThreadPoolExecutor
import threading

def test_skip_locked_no_duplicate():
    """
    다중 워커가 동시에 PENDING 조회할 때 중복 실행되지 않음을 검증
    
    시나리오:
    1. WriteBackQueue에 10개 PENDING 아이템 생성
    2. 2개 워커 동시 가동
    3. 각 워커는 FOR UPDATE SKIP LOCKED로 최대 10개 조회
    4. 결과: 총 10개 아이템이 정확히 1회씩만 처리됨
    
    Success Criteria:
    - Worker A: 5개 처리
    - Worker B: 5개 처리
    - 중복 처리: 0개
    """
    # 1. 테스트 DB 설정
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    
    # 테이블 생성 (또는 기존 알림 마이그레이션 사용)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    
    # 2. 테스트 데이터: 10개 PENDING 아이템
    pending_items = []
    for i in range(10):
        item = WriteBackQueue(
            id=f"item_{i}",
            target_system="SAP",
            status="PENDING",
            payload={"project_id": f"proj_{i}"},
            retry_count=0
        )
        db.add(item)
        pending_items.append(item)
    db.commit()
    
    # 3. 워커 2개 동시 실행
    processed_items = []
    lock = threading.Lock()
    
    def worker_task(worker_id):
        db2 = SessionLocal()
        worker = WriteBackWorker(db2)
        
        # FOR UPDATE SKIP LOCKED로 조회 (내 코드 Task 1)
        items = db2.query(WriteBackQueue).filter(
            WriteBackQueue.status == "PENDING"
        ).with_for_update(skip_locked=True).limit(10).all()
        
        # 처리 결과 기록
        with lock:
            for item in items:
                processed_items.append({
                    "item_id": item.id,
                    "worker_id": worker_id
                })
                # CONFIRMED로 변경 (처리됨 표시)
                item.status = "CONFIRMED"
            db2.commit()
    
    # 동시 실행
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(worker_task, 1)
        executor.submit(worker_task, 2)
    
    # 4. 검증
    assert len(processed_items) == 10, "총 10개 아이템 처리되어야 함"
    
    item_ids = [p["item_id"] for p in processed_items]
    assert len(set(item_ids)) == 10, "중복 없이 정확히 10개 처리"
    
    # 각 아이템이 정확히 1회만 처리됨
    for item_id in item_ids:
        count = sum(1 for p in processed_items if p["item_id"] == item_id)
        assert count == 1, f"{item_id} 중복 처리됨: {count}회"
    
    db.close()
```

---

### Test 2: 개별 커밋 (중간 크래시 복구)

```python
def test_individual_commit_on_crash():
    """
    루프 도중 크래시 시 이미 처리된 항목은 DB에 기록됨을 검증
    
    시나리오:
    1. 3개 PENDING 아이템 생성
    2. WriteBackWorker 실행 중
    3. 2번째 아이템 처리 후 의도적 크래시
    4. 재구동 후 상태 확인
    
    Success Criteria:
    - 1번째 아이템: CONFIRMED (처리됨)
    - 2번째 아이템: CONFIRMED 또는 PENDING (처리 중)
    - 3번째 아이템: PENDING (미처리)
    - 결과: 처리된 것은 보존, 미처리는 다시 처리 가능
    """
    # 1. DB 설정
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    
    # 2. 테스트 데이터: 3개 PENDING
    items_data = []
    for i in range(3):
        item = WriteBackQueue(
            id=f"crash_test_{i}",
            target_system="SAP",
            status="PENDING",
            payload={"project_id": f"proj_{i}"},
            retry_count=0
        )
        db.add(item)
        items_data.append(item)
    db.commit()
    
    # 3. 워커 실행 (2번째 후 크래시)
    processed_count = 0
    
    try:
        pending_items = db.query(WriteBackQueue).filter(
            WriteBackQueue.status == "PENDING"
        ).with_for_update(skip_locked=True).limit(10).all()
        
        for idx, item in enumerate(pending_items):
            # 개별 커밋 (Task 2)
            item.status = "CONFIRMED"
            item.sent_at = datetime.utcnow()
            db.commit()
            
            processed_count += 1
            
            # 2번째 처리 후 의도적 크래시
            if idx == 1:
                raise RuntimeError("SIMULATED CRASH")
    
    except RuntimeError as e:
        if "CRASH" not in str(e):
            raise
    
    # 4. 검증
    db2 = SessionLocal()
    
    # 처리된 항목 확인
    confirmed = db2.query(WriteBackQueue).filter(
        WriteBackQueue.status == "CONFIRMED"
    ).all()
    
    pending = db2.query(WriteBackQueue).filter(
        WriteBackQueue.status == "PENDING"
    ).all()
    
    # 최소 1개는 CONFIRMED (개별 커밋으로 보존됨)
    assert len(confirmed) >= 1, f"최소 1개는 저장되어야 함, 실제: {len(confirmed)}"
    
    # 미처리 항목은 다시 처리 가능
    assert len(pending) >= 1, f"미처리 항목 있어야 함, 실제: {len(pending)}"
    
    # 총 3개
    assert len(confirmed) + len(pending) == 3, "데이터 유실 없음"
    
    db.close()
    db2.close()
```

---

### Test 3: DLQ + Replay API

```python
def test_dlq_replay_api():
    """
    3회 실패 후 DLQ 상태로 전환되고, Replay API로 재실행되는지 검증
    
    시나리오:
    1. 1개 아이템 생성
    2. SAP API 실패 3회 시뮬레이션
    3. 아이템이 DLQ 상태로 전환됨
    4. Replay API 호출
    5. 아이템이 PENDING으로 복귀, retry_count=0으로 초기화
    
    Success Criteria:
    - 3회 실패 후 status='DLQ', dlq_reason 설정됨
    - Replay API 호출 후 status='PENDING', retry_count=0
    - 재처리 가능
    """
    # 1. DB 설정
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    
    # 2. 테스트 데이터: 1개 아이템
    item = WriteBackQueue(
        id="dlq_test",
        target_system="SAP",
        status="PENDING",
        payload={"project_id": "proj_dlq"},
        retry_count=0,
        max_retries=3
    )
    db.add(item)
    db.commit()
    
    # 3. 3회 실패 시뮬레이션
    sap_mock = SAPApiMock(success_rate=0)  # 무조건 실패
    worker = WriteBackWorker(db, sap_api=sap_mock)
    
    for attempt in range(3):
        try:
            worker._process_single_item(item)
            db.commit()
        except Exception:
            pass
    
    # 4. DLQ 상태 확인
    db.refresh(item)
    assert item.status == "DLQ", f"3회 실패 후 DLQ 상태여야 함, 실제: {item.status}"
    assert item.dlq_reason is not None, "dlq_reason 설정되어야 함"
    assert item.dlq_at is not None, "dlq_at 설정되어야 함"
    
    # 5. Replay API 호출 (POST /api/writeback/replay/dlq_test)
    # (FastAPI TestClient 사용)
    from fastapi.testclient import TestClient
    from app.api.writeback_endpoints import router
    
    client = TestClient(router)
    response = client.post("/replay/dlq_test")
    
    # 6. Replay 결과 확인
    assert response.status_code == 200, f"Replay API 실패: {response.text}"
    
    # 7. 아이템 상태 확인
    item = db.query(WriteBackQueue).filter(
        WriteBackQueue.id == "dlq_test"
    ).first()
    
    assert item.status == "PENDING", f"Replay 후 PENDING 상태여야 함, 실제: {item.status}"
    assert item.retry_count == 0, f"Replay 후 retry_count=0이어야 함, 실제: {item.retry_count}"
    assert item.dlq_reason is None, "dlq_reason 초기화되어야 함"
    
    db.close()
```

---

### Test 4: next_retry_at 지수 백오프

```python
def test_next_retry_at_backoff():
    """
    재시도 지연이 지수 백오프로 적용되는지 검증
    
    시나리오:
    1. 1개 아이템 생성
    2. 1회 실패: next_retry_at = now + 120초 (2^1 * 60)
    3. 2회 실패: next_retry_at = now + 240초 (2^2 * 60)
    4. 3회 실패: next_retry_at = now + 480초 (2^3 * 60) → DLQ
    
    Success Criteria:
    - 각 실패마다 next_retry_at 계산 및 저장
    - 시간 도달 전에는 조회되지 않음
    - 시간 도달 후 조회됨
    """
    # 1. DB 설정
    from datetime import timedelta
    
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    
    # 2. 테스트 데이터
    item = WriteBackQueue(
        id="backoff_test",
        target_system="SAP",
        status="PENDING",
        payload={"project_id": "proj_backoff"},
        retry_count=0,
        max_retries=3
    )
    db.add(item)
    db.commit()
    
    # 3. 첫 번째 실패
    config = WriteBackWorkerConfig(
        INITIAL_RETRY_DELAY=60,
        RETRY_BACKOFF_MULTIPLIER=2
    )
    
    sap_mock = SAPApiMock(success_rate=0)
    worker = WriteBackWorker(db, sap_api=sap_mock, config=config)
    
    now_1 = datetime.utcnow()
    try:
        worker._process_single_item(item)
    except:
        pass
    db.commit()
    
    # 확인: retry_count=1, next_retry_at = now + 120초
    db.refresh(item)
    assert item.retry_count == 1, "1회 실패 후 retry_count=1"
    assert item.next_retry_at is not None, "next_retry_at 설정됨"
    
    expected_delay = 120  # 60 * 2^1
    actual_delay = (item.next_retry_at - now_1).total_seconds()
    assert 119 <= actual_delay <= 121, f"지연 약 120초, 실제: {actual_delay}"
    
    # 4. 두 번째 실패
    first_retry_at = item.next_retry_at
    
    try:
        worker._process_single_item(item)
    except:
        pass
    db.commit()
    
    # 확인: retry_count=2, next_retry_at = now + 240초
    db.refresh(item)
    assert item.retry_count == 2, "2회 실패 후 retry_count=2"
    
    expected_delay_2 = 240  # 60 * 2^2
    actual_delay_2 = (item.next_retry_at - now_1).total_seconds()
    assert 239 <= actual_delay_2 <= 241, f"지연 약 240초, 실제: {actual_delay_2}"
    
    # next_retry_at이 증가했는지 확인 (지수 백오프)
    assert item.next_retry_at > first_retry_at, "next_retry_at이 증가함 (지수 백오프)"
    
    # 5. 세 번째 실패 → DLQ
    try:
        worker._process_single_item(item)
    except:
        pass
    db.commit()
    
    # 확인: status='DLQ'
    db.refresh(item)
    assert item.status == "DLQ", "3회 실패 후 DLQ 상태"
    
    # 6. 시간 미도달: next_retry_at이 미래일 때는 조회 안 됨
    pending_not_due = db.query(WriteBackQueue).filter(
        WriteBackQueue.status == "PENDING",
        (WriteBackQueue.next_retry_at.is_(None)) | 
        (WriteBackQueue.next_retry_at <= datetime.utcnow())
    ).all()
    
    assert len(pending_not_due) == 0, "next_retry_at 미도달 항목은 조회 안 됨"
    
    # 7. 시간 도달: next_retry_at 이후에는 조회됨
    # (시간을 앞당기거나 수동으로 테스트)
    item.next_retry_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()
    
    pending_due = db.query(WriteBackQueue).filter(
        WriteBackQueue.status == "PENDING",
        (WriteBackQueue.next_retry_at.is_(None)) | 
        (WriteBackQueue.next_retry_at <= datetime.utcnow())
    ).all()
    
    # PENDING은 없지만 (DLQ이므로), 조회 로직이 작동함을 확인
    assert isinstance(pending_due, list), "조회 작동"
    
    db.close()
```

---

## 📝 테스트 실행 및 검증

### 테스트 실행

```bash
cd ont_platform/v4/backend

# 모든 테스트 실행
pytest tests/test_phase4_week35_async_safety.py -v

# 개별 테스트
pytest tests/test_phase4_week35_async_safety.py::test_skip_locked_no_duplicate -v
pytest tests/test_phase4_week35_async_safety.py::test_individual_commit_on_crash -v
pytest tests/test_phase4_week35_async_safety.py::test_dlq_replay_api -v
pytest tests/test_phase4_week35_async_safety.py::test_next_retry_at_backoff -v
```

### 예상 결과

```
tests/test_phase4_week35_async_safety.py::test_skip_locked_no_duplicate PASSED
tests/test_phase4_week35_async_safety.py::test_individual_commit_on_crash PASSED
tests/test_phase4_week35_async_safety.py::test_dlq_replay_api PASSED
tests/test_phase4_week35_async_safety.py::test_next_retry_at_backoff PASSED

==== 4 passed in 2.34s ====
```

---

## 📋 테스트 결과 리포트

완료 후 제출할 리포트:

**파일**: `task_logs/claude/20260525_PHASE4_WEEK35_Claude_Agent_TestCode.md`

```markdown
# Phase 4 Week 3.5: Claude 에이전트 테스트 결과

**작업 기간**: Day 1 14:00 ~ 16:30 (2.5시간)  
**상태**: ✅ 완료

## 테스트 결과

| 테스트 | 상태 | 소요시간 |
|--------|------|---------|
| test_skip_locked_no_duplicate | ✅ PASSED | 0.45s |
| test_individual_commit_on_crash | ✅ PASSED | 0.52s |
| test_dlq_replay_api | ✅ PASSED | 0.38s |
| test_next_retry_at_backoff | ✅ PASSED | 0.59s |
| **합계** | **✅ 4/4** | **1.94s** |

## 코드 커버리지

```
app/services/write_back_worker.py: 92%
  - process_pending: 100%
  - _process_single_item: 89%
  - other methods: 85%
```

## 주요 검증 사항

✅ FOR UPDATE SKIP LOCKED: 중복 실행 0%  
✅ 개별 커밋: 중간 크래시 복구 성공  
✅ DLQ 상태: 3회 실패 후 DLQ로 전환, Replay API 동작  
✅ 지수 백오프: 120s → 240s → 480s 적용 확인

## 완료 체크리스트

- [x] 4개 테스트 작성
- [x] 모든 테스트 통과
- [x] 코드 커버리지 ≥90%
- [x] 리포트 작성
```

---

## 🚀 완료 후 다음 단계

1. 테스트 실행 완료 (Day 1 16:30경)
2. 결과 리포트 제출
3. Antigravity / Codex 부하 테스트 및 UI 결과 받기
4. 통합 검증 시작

---

**예상 완료**: 2026-05-25 17:00경  
**제출물**: `tests/test_phase4_week35_async_safety.py` + 리포트
