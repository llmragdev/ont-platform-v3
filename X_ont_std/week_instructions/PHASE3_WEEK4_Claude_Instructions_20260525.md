# Phase 3 Week 4 Claude (Backend) 작업 지시서

**기간**: 2026-06-17 ~ 2026-06-21 (5일)  
**담당**: Claude (Backend Agent)  
**목표**: Write-back API 확장 + Backend 통합 테스트  
**예상시간**: 8~10시간

---

## 🎯 Week 4 Claude 임무

Backend에서 Frontend와 성능팀을 지원하는 역할:
1. **Changelog 조회 API 구현** (Audit 대시보드 지원)
2. **Write-back 상태 조회 API** (실시간 모니터링)
3. **Backend 통합 테스트** (전체 워크플로우 E2E)

---

## 📋 Task 분해

### Task 1: Changelog 조회 API (3~4시간)
**파일**: `app/main.py` + `app/services/changelog_service.py`

#### API 엔드포인트
```python
GET /api/changelog/history
    query params:
    - entity_id: str (optional)
    - domain_id: str (optional)
    - action_type: str (optional)  # APPROVE, REJECT, etc
    - sync_status: str (optional)  # PENDING, SYNCED, FAILED
    - date_from: str (optional)    # ISO8601
    - date_to: str (optional)      # ISO8601
    - page: int = 1
    - page_size: int = 50
    
    returns: {
        items: [{
            id, entity_id, action_type, actor,
            old_status, new_status, timestamp,
            sync_status, target_system, error_message
        }],
        total: int,
        page: int,
        page_size: int
    }
```

#### 구현 요구사항
- ✅ 페이징 지원 (기본 50개씩)
- ✅ 필터링 (entity_id, action_type, sync_status, 날짜 범위)
- ✅ 정렬 (timestamp 역순)
- ✅ Changelog 모델에서 직접 조회
- ✅ 권한 검증 (없으면 생략)

#### 테스트 (5개)
```python
def test_changelog_list_all(client):
    # 모든 changelog 조회
    
def test_changelog_filter_by_entity(client):
    # entity_id로 필터링
    
def test_changelog_filter_by_status(client):
    # sync_status로 필터링
    
def test_changelog_date_range(client):
    # 날짜 범위로 필터링
    
def test_changelog_pagination(client):
    # 페이징 정상 작동
```

---

### Task 2: WriteBack 상태 조회 API (2~3시간)
**파일**: `app/main.py` + `app/services/write_back_worker.py`

#### API 엔드포인트
```python
GET /api/writeback/queue
    query params:
    - status: str (optional)  # PENDING, CONFIRMED, FAILED
    - domain_id: str (optional)
    - limit: int = 100
    
    returns: {
        pending: int,
        confirmed: int,
        failed: int,
        items: [{
            id, action_execution_id, target_system,
            status, retry_count, created_at, sent_at,
            error_message
        }]
    }

GET /api/writeback/statistics
    returns: {
        total_processed: int,
        success_rate: float,
        failure_count: int,
        avg_retry_attempts: float,
        last_sync_time: str (ISO8601)
    }
```

#### 구현 요구사항
- ✅ WriteBackQueue에서 상태별 조회
- ✅ 실시간 통계 계산
- ✅ 필터링 (status, domain_id)
- ✅ 성공률 계산 (CONFIRMED / TOTAL)
- ✅ 마지막 동기화 시간

#### 테스트 (4개)
```python
def test_writeback_queue_list(client):
    # 큐 상태 조회
    
def test_writeback_filter_by_status(client):
    # 상태별 필터링
    
def test_writeback_statistics(client):
    # 통계 조회
    
def test_writeback_success_rate(client):
    # 성공률 계산 정확성
```

---

### Task 3: Backend 통합 테스트 (3~4시간)
**파일**: `tests/test_phase3_backend_e2e.py`

#### 테스트 시나리오 (10개+)

```python
class TestPhase3BackendE2E:
    """Backend 전체 워크플로우 E2E 테스트"""
    
    def test_full_workflow_approve_to_confirmed(self):
        # 1. ApproveProject 실행
        # 2. Changelog + WriteBackQueue 생성 확인
        # 3. Worker 실행
        # 4. SAP Mock 호출 (성공)
        # 5. CONFIRMED + SYNCED 확인
        
    def test_full_workflow_with_retry(self):
        # 1. StartPayment 실행
        # 2. Worker 1차 실행 (실패)
        # 3. WriteBackQueue PENDING 확인
        # 4. Worker 2차 실행 (성공)
        # 5. CONFIRMED 확인
        
    def test_multiple_actions_in_parallel(self):
        # 여러 액션 동시 실행
        # 각각 Changelog + WriteBackQueue 생성
        # Worker 한 번에 모두 처리
        
    def test_api_changelog_query(self):
        # GET /api/changelog/history 정상 작동
        
    def test_api_writeback_stats(self):
        # GET /api/writeback/statistics 정상 작동
        
    def test_permissions_on_actions(self):
        # CFO만 가능한 액션 권한 검증
        
    def test_error_handling_invalid_status(self):
        # 불가능한 상태 변경 시도
        
    def test_audit_log_completeness(self):
        # 모든 액션이 AuditLog에 기록
        
    def test_changelog_completeness(self):
        # 모든 액션이 Changelog에 기록
        
    def test_writeback_queue_cleanup(self):
        # CONFIRMED된 항목 처리 확인
```

#### 요구사항
- ✅ 10개 이상의 E2E 테스트
- ✅ 성공/실패/재시도 모든 경로
- ✅ API 엔드포인트 통합 테스트
- ✅ 권한 검증 포함
- ✅ 전체 통과율 ≥ 85%

---

## 🔧 구현 가이드

### Changelog 조회 API
```python
from sqlalchemy import and_, or_
from datetime import datetime

@app.get("/api/changelog/history")
def get_changelog_history(
    entity_id: Optional[str] = None,
    domain_id: Optional[str] = None,
    action_type: Optional[str] = None,
    sync_status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    """Changelog 조회"""
    query = db.query(ChangeLog)
    
    # 필터 적용
    if entity_id:
        query = query.filter(ChangeLog.entity_id == entity_id)
    if domain_id:
        query = query.filter(ChangeLog.domain_id == domain_id)
    if action_type:
        query = query.filter(ChangeLog.action_type == action_type)
    if sync_status:
        query = query.filter(ChangeLog.sync_status == sync_status)
    if date_from:
        query = query.filter(ChangeLog.timestamp >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(ChangeLog.timestamp <= datetime.fromisoformat(date_to))
    
    # 정렬 + 페이징
    total = query.count()
    items = query.order_by(ChangeLog.timestamp.desc())\
                 .offset((page-1)*page_size)\
                 .limit(page_size)\
                 .all()
    
    return {
        "items": [item.to_dict() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size
    }
```

### WriteBack 통계 API
```python
@app.get("/api/writeback/statistics")
def get_writeback_statistics(db: Session = Depends(get_db)):
    """Write-back 통계"""
    total = db.query(WriteBackQueue).count()
    confirmed = db.query(WriteBackQueue).filter(
        WriteBackQueue.status == "CONFIRMED"
    ).count()
    failed = db.query(WriteBackQueue).filter(
        WriteBackQueue.status == "FAILED"
    ).count()
    
    success_rate = confirmed / total if total > 0 else 0
    
    return {
        "total_processed": total,
        "success_rate": round(success_rate, 4),
        "failure_count": failed,
        "pending_count": total - confirmed - failed
    }
```

---

## 📊 완료 기준

```
✅ Task 1: Changelog 조회 API
  - GET /api/changelog/history 구현
  - 필터링, 페이징, 정렬
  - 5개 테스트 통과

✅ Task 2: WriteBack 상태 API
  - GET /api/writeback/queue
  - GET /api/writeback/statistics
  - 4개 테스트 통과

✅ Task 3: Backend E2E 테스트
  - 10개+ E2E 테스트
  - 모든 워크플로우 검증
  - 통과율 ≥ 85%

✅ 전체 9개 테스트 통과 (Task 1+2: 9개)
✅ 10개+ E2E 테스트 (Task 3)
✅ API 문서화 완료
```

---

## 📁 디렉토리 구조

```
ont_platform/v3/src/backend/
├── app/
│   ├── main.py                       ← API 엔드포인트 추가
│   └── services/
│       └── changelog_service.py      ← to_dict() 메서드 추가
├── tests/
│   ├── test_changelog_api.py         ← 신규 (5 테스트)
│   ├── test_writeback_api.py         ← 신규 (4 테스트)
│   └── test_phase3_backend_e2e.py    ← 신규 (10+ E2E 테스트)
```

---

## 🚀 실행 순서

1. **Task 1 구현** (Changelog API) → 테스트 (5개)
2. **Task 2 구현** (WriteBack API) → 테스트 (4개)
3. **Task 3 구현** (E2E 테스트) → 10개+

---

**예상 완료**: 2026-06-21  
**최종 검증**: 모든 API 정상 작동 + E2E 85% 이상 통과  
**다음**: Codex/Antigravity와 통합

