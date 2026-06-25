# Phase 4 Week 3.5: Claude (나) 코드 수정 지시서

**작업명**: WriteBackWorker 비동기 안전장치 구현  
**시작**: 지금 바로  
**소요시간**: 3-4시간 (집중)  
**완료 기준**: 4가지 Task 모두 수정 완료 + 테스트 코드 제공

---

## 🎯 작업 개요

현재 `write_back_worker.py`의 4가지 심각한 취약점을 수정:

1. **다중 워커 경쟁 상태** (Race Condition) → 중복 트랜잭션 위험
2. **지수 백오프 무력화** → 외부 API 과부하
3. **배치 커밋** → 데이터 유실
4. **일시적 오류 즉시 실패** → 트랜잭션 유실

---

## 📄 현재 코드 상태 분석

### 파일 위치
`ont_platform/v4/backend/app/services/write_back_worker.py`

### 현재 문제점

#### ❌ 문제 1: Race Condition (Line 85-87)
```python
# 현재 코드
pending_items = self.db.query(WriteBackQueue).filter(
    WriteBackQueue.status == "PENDING"
).all()  # ← 행 락킹 없음! 여러 워커가 동일 행 조회 가능
```

#### ❌ 문제 2: 배치 커밋 (Line 100)
```python
# 현재 코드
for item in pending_items:
    try:
        self._process_single_item(item)
    except Exception as e:
        errors.append(...)

self.db.commit()  # ← 루프 끝 후 한 번만 커밋 (데이터 유실 위험)
```

#### ❌ 문제 3: next_retry_at 미구현 (Line 148-153)
```python
# 현재 코드
next_retry_delay = (...)  # 계산만 하고
# 재시도 예정 시간은 현재 계산하지 않음 (Worker가 주기적으로 재시도)
# ← 지수 백오프 실제 적용 안 됨
```

#### ❌ 문제 4: DLQ 상태 없음
```python
# 현재: FAILED로 끝남
# 필요: DLQ 상태 추가 + Replay API 추가
```

---

## ✅ 구현 순서 (각 Task별)

### Task 1: PostgreSQL 행 락킹 (FOR UPDATE SKIP LOCKED)

**파일**: `app/services/write_back_worker.py`  
**라인**: 85-87 수정  
**시간**: 30분

**변경 사항**:
```python
# Before
pending_items = self.db.query(WriteBackQueue).filter(
    WriteBackQueue.status == "PENDING"
).all()

# After
pending_items = self.db.query(WriteBackQueue).filter(
    WriteBackQueue.status == "PENDING"
).with_for_update(skip_locked=True).limit(10).all()
```

**코드 작성**:
```python
def process_pending(self) -> dict:
    """
    Pending 항목 처리
    
    Changes:
    - FOR UPDATE SKIP LOCKED 적용
    - LIMIT 10으로 배치 크기 제한
    """
    # Pending 항목 조회 (FOR UPDATE SKIP LOCKED 적용)
    pending_items = self.db.query(WriteBackQueue).filter(
        WriteBackQueue.status == "PENDING"
    ).with_for_update(skip_locked=True).limit(10).all()
    # ... 나머지 코드
```

**테스트 코드 힌트** (Claude 에이전트에 전달):
- 2개 워커 동시 실행
- 동일한 item을 조회하지 않음 확인

---

### Task 2: 개별 트랜잭션 커밋

**파일**: `app/services/write_back_worker.py`  
**라인**: 77-109 수정  
**시간**: 30분

**변경 사항**:
```python
# Before
for item in pending_items:
    try:
        self._process_single_item(item)
    except Exception as e:
        errors.append(...)

self.db.commit()  # 루프 끝 후 한 번만

# After
for item in pending_items:
    try:
        self._process_single_item(item)
        self.db.commit()  # 각 아이템마다 즉시 커밋
    except Exception as e:
        errors.append(...)
        self.db.commit()  # 실패해도 커밋 (실패 상태 기록)
```

**코드 작성**:
```python
def process_pending(self) -> dict:
    """
    Pending 항목 처리
    
    Changes:
    - 개별 아이템마다 db.commit() 수행
    - 실패한 경우에도 커밋 (실패 상태 보존)
    """
    pending_items = self.db.query(WriteBackQueue).filter(
        WriteBackQueue.status == "PENDING"
    ).with_for_update(skip_locked=True).limit(10).all()

    errors = []
    self.processed_count += len(pending_items)

    for item in pending_items:
        try:
            self._process_single_item(item)
            self.db.commit()  # ← 성공 시 즉시 커밋
        except Exception as e:
            self.db.commit()  # ← 실패 시에도 커밋 (실패 상태 저장)
            errors.append({
                "item_id": item.id,
                "error": str(e)
            })

    return {
        "processed": len(pending_items),
        "succeeded": self.success_count,
        "failed": self.failure_count,
        "errors": errors
    }
```

**테스트 코드 힌트**:
- 루프 도중 의도적 크래시 시뮬레이션
- 크래시 전 처리된 항목만 SYNCED/FAILED 상태 유지 확인

---

### Task 3: DLQ + Replay API

**파일**:
- `app/models/write_back_queue.py` (모델 확장, 파일 없으면 생성)
- `app/services/write_back_worker.py` (DLQ 로직)
- `app/api/writeback_endpoints.py` (API, 파일 없으면 생성)

**시간**: 1.5시간

#### 3-1) WriteBackQueue 모델 확장

**파일 위치**: `app/models/write_back_queue.py` (또는 `app/db/models.py`에 추가)

```python
from sqlalchemy import Column, String, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class WriteBackQueue(Base):
    __tablename__ = "writeback_queue"
    
    # ... 기존 필드 ...
    id: str                              # Primary Key
    target_system: str                   # SAP, etc.
    payload: dict                        # JSON 데이터
    status: str                          # PENDING, CONFIRMED, FAILED, DLQ ← DLQ 추가
    
    # 재시도 관련
    retry_count: int = 0
    max_retries: int = 3
    last_error_at: Optional[datetime]
    error_message: Optional[str]
    
    # 다음 재시도 시간 (Task 4에서 추가)
    next_retry_at: Optional[datetime]
    
    # DLQ 관련 (Task 3에서 추가)
    dlq_reason: Optional[str]            # DLQ 이유 기록
    dlq_at: Optional[datetime]           # DLQ 전환 시간
    
    sent_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
```

#### 3-2) DLQ 로직 추가 (write_back_worker.py)

**Line 155-162 수정**:

```python
# Before
else:
    # 재시도 횟수 초과 → FAILED 상태로 변경
    item.status = "FAILED"
    item.last_error_at = datetime.utcnow()
    item.error_message = f"Max retries ({self.config.MAX_RETRIES}) exceeded: {str(e)}"
    self.failure_count += 1

# After
else:
    # 재시도 횟수 초과 → DLQ 상태로 격리
    item.status = "DLQ"  # ← FAILED 대신 DLQ
    item.dlq_reason = f"Max retries ({self.config.MAX_RETRIES}) exceeded: {str(e)}"
    item.dlq_at = datetime.utcnow()
    item.last_error_at = datetime.utcnow()
    item.error_message = str(e)
    self.failure_count += 1
```

#### 3-3) Replay API 추가 (writeback_endpoints.py)

**새로운 파일 또는 기존 파일에 추가**:

```python
# app/api/writeback_endpoints.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

router = APIRouter(prefix="/api/writeback", tags=["writeback"])

@router.post("/replay/{queue_id}")
async def replay_queue_item(
    queue_id: str,
    db: Session = Depends(get_db)
):
    """
    실패한 (DLQ) 아이템을 다시 큐에 투입
    
    Args:
        queue_id: 재실행할 아이템 ID
        
    Returns:
        {status: "replayed", queue_id: "..."}
        
    Errors:
        - 400: Item not in DLQ
        - 404: Item not found
    """
    # 아이템 조회
    item = db.query(WriteBackQueue).filter(
        WriteBackQueue.id == queue_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item.status != "DLQ":
        raise HTTPException(
            status_code=400, 
            detail=f"Item is {item.status}, not DLQ"
        )
    
    # 상태 재설정
    item.status = "PENDING"
    item.retry_count = 0  # 재시도 횟수 초기화
    item.dlq_reason = None
    item.dlq_at = None
    
    db.commit()
    
    return {
        "status": "replayed",
        "queue_id": queue_id
    }

@router.get("/dlq/items")
async def get_dlq_items(db: Session = Depends(get_db)):
    """
    DLQ 상태의 모든 아이템 조회
    
    Returns:
        {items: [...], count: int}
    """
    items = db.query(WriteBackQueue).filter(
        WriteBackQueue.status == "DLQ"
    ).order_by(WriteBackQueue.dlq_at.desc()).all()
    
    return {
        "items": items,
        "count": len(items)
    }
```

**테스트 코드 힌트**:
- 3회 실패 후 DLQ 상태 확인
- Replay API 호출 후 PENDING 상태로 복귀 확인

---

### Task 4: next_retry_at 스케줄링

**파일**: `app/services/write_back_worker.py`  
**라인**: 85-87 (조회) + 141-160 (재시도 로직)  
**시간**: 1시간

#### 4-1) 모델에 컬럼 추가 (Task 3 모델 확장 사항)

```python
class WriteBackQueue(Base):
    # ... 기타 필드 ...
    next_retry_at: Optional[datetime] = None  # ← 다음 재시도 시간
```

#### 4-2) 조회 쿼리 수정

**Line 85-87 완전 재작성**:

```python
# Before
pending_items = self.db.query(WriteBackQueue).filter(
    WriteBackQueue.status == "PENDING"
).with_for_update(skip_locked=True).limit(10).all()

# After
from datetime import datetime

pending_items = self.db.query(WriteBackQueue).filter(
    WriteBackQueue.status == "PENDING",
    (WriteBackQueue.next_retry_at.is_(None)) | 
    (WriteBackQueue.next_retry_at <= datetime.utcnow())
).with_for_update(skip_locked=True).limit(10).all()
# ↑ next_retry_at이 None이거나 현재 시간 이하인 경우만 조회
```

#### 4-3) 재시도 시간 계산 로직 (Line 141-160)

```python
# Before
except TimeoutError as e:
    if item.retry_count < self.config.MAX_RETRIES:
        item.retry_count += 1
        item.last_error_at = datetime.utcnow()
        item.error_message = str(e)
        # 재시도 예정 시간은 현재 계산하지 않음

# After
except TimeoutError as e:
    if item.retry_count < self.config.MAX_RETRIES:
        item.retry_count += 1
        item.last_error_at = datetime.utcnow()
        item.error_message = str(e)
        
        # 지수 백오프 계산 및 DB에 저장 ← 추가
        next_retry_delay = (
            self.config.INITIAL_RETRY_DELAY *
            (self.config.RETRY_BACKOFF_MULTIPLIER ** item.retry_count)
        )
        item.next_retry_at = (
            datetime.utcnow() + timedelta(seconds=next_retry_delay)
        )
```

**지수 백오프 예시**:
- 1회 실패: 60 * 2^1 = 120초 (2분)
- 2회 실패: 60 * 2^2 = 240초 (4분)
- 3회 실패: 60 * 2^3 = 480초 (8분) → DLQ

**테스트 코드 힌트**:
- 1회 실패 시 next_retry_at = now + 120초 확인
- 2회 실패 시 next_retry_at = now + 240초 확인
- 시간 도달 전 조회하면 스킵되는지 확인

---

## 📋 최종 체크리스트

구현 완료 후 확인:

- [ ] Task 1: FOR UPDATE SKIP LOCKED 적용
  - `with_for_update(skip_locked=True)` 추가됨
  - LIMIT 10 추가됨

- [ ] Task 2: 개별 트랜잭션 커밋
  - 루프 내부에서 `db.commit()` 호출
  - 예외 발생 시에도 `db.commit()` 실행

- [ ] Task 3: DLQ + Replay API
  - WriteBackQueue 모델: `status="DLQ"`, `dlq_reason`, `dlq_at` 필드 추가
  - write_back_worker.py: DLQ 로직 추가
  - writeback_endpoints.py: `/replay/{id}` API 추가

- [ ] Task 4: next_retry_at 스케줄링
  - WriteBackQueue 모델: `next_retry_at` 필드 추가
  - 조회 쿼리: time filter 추가
  - 재시도 로직: `next_retry_at` 계산 및 저장

---

## 🚀 완료 후 다음 단계

1. **코드 수정 완료** (Day 1 오후 2시경)
   ↓
2. **Claude 에이전트에 테스트 코드 전달**
   ↓
3. **Antigravity에 부하 테스트 지시**
   ↓
4. **Codex에 UI 구현 지시**

---

**예상 완료**: 2026-05-25 오후 5시경  
**준비**: 지금 바로 Task 1부터 시작
