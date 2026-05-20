# Phase 3 — 상태 기계 & Write-back 설계서

> **버전**: 1.0  
> **작성일**: 2026-05-20  
> **목표**: 상태 전이 규칙 정의 + Write-back 메커니즘 상세화  
> **연계 문서**: [PHASE3_ACTION_DEFINITION.md](./PHASE3_ACTION_DEFINITION.md)

---

## 1. 상태 기계 (State Machine)

### 1-1. 상태 기계의 정의

**상태 기계** = 엔티티의 **합법적인 상태** + **허용된 전이** + **조건**

```
예:
  엔티티: PROJECT
  상태: Submitted, UnderReview, Approved, Rejected, InProgress, Completed
  전이: Submitted → UnderReview (RequestReview 액션)
  조건: 담당자 배정됨, 예산 ≥ 1천만원
```

### 1-2. 현재 문제점

현재 `workflow.json`은:
```json
{
  "object_type": "Order",
  "statuses": [...],
  "actions": {
    "ActionName": {
      "from_statuses": [...],
      "to_status": "...",
      "allowed_roles": [...]
    }
  }
}
```

**부족한 부분:**
- [ ] 조건부 권한 (금액에 따라 다른 권한)
- [ ] 전제 조건 (예: 담당자 배정됨)
- [ ] 부수 효과 (Write-back, 알림)
- [ ] 실패 시나리오 (재시도, 롤백)

---

## 2. 확장된 상태 기계 설계 (v3.1)

### 2-1. 새로운 ActionDefinition 구조

```yaml
ActionDefinition:
  id: "approve_project"              # 액션 ID
  display_name: "과제 승인"           # UI 표시명
  
  entity_type: "PROJECT"             # 대상 엔티티
  
  preconditions:                     # 전제 조건
    - field: "properties.status"
      operator: "equals"
      value: "UnderReview"
    
    - field: "properties.manager"
      operator: "not_null"
    
    - field: "properties.budget"
      operator: "gte"
      value: 10000000
  
  permission_rules:                  # 조건부 권한
    - condition:
        field: "properties.budget"
        operator: "lte"
        value: 50000000
      allowed_roles: ["TeamLead", "FinanceManager", "Admin"]
    
    - condition:
        field: "properties.budget"
        operator: "gt"
        value: 50000000
        operator: "lte"
        value: 200000000
      allowed_roles: ["FinanceManager", "Admin"]
    
    - condition:
        field: "properties.budget"
        operator: "gt"
        value: 200000000
      allowed_roles: ["Admin"]
  
  state_transition:                  # 상태 전이
    from: ["UnderReview"]
    to: "Approved"
  
  property_changes:                  # 속성 변경
    - field: "properties.approved_by"
      value: "{{ user_id }}"
    - field: "properties.approved_at"
      value: "{{ timestamp }}"
  
  side_effects:                      # 부수 효과
    - type: "changelog"
      target: "ontology/changelog"
    
    - type: "write_back"
      target: "SAP"
      mapping:
        entity_id: "project_id"
        status: "approved"
        updated_by: "{{ user_id }}"
        updated_at: "{{ timestamp }}"
    
    - type: "notification"
      target: ["applicant", "manager", "admin"]
      message: "과제가 승인되었습니다"
    
    - type: "audit"
      fields: ["all"]
  
  failure_handling:                  # 실패 처리
    on_precondition_failed:
      response: 400
      message: "선행 조건을 만족하지 않습니다"
    
    on_permission_denied:
      response: 403
      message: "이 액션을 실행할 권한이 없습니다"
    
    on_write_back_failed:
      action: "retry"
      max_retries: 3
      retry_interval: 3600  # 1시간
      on_max_retries: "notify_admin"
  
  validation_rules:                  # 추가 검증
    - name: "budget_consistency"
      script: "return entity.budget <= entity.max_budget"
```

### 2-2. 구현 방식

#### 방식 A: JSON 기반 (권장 — 현재)
```
장점:
  - 비개발자도 수정 가능 (설정)
  - 런타임에 동적 로드 가능
  
단점:
  - 복잡한 조건 표현 어려움
  - 복합 계산 불가능

파일 위치:
  app/config/state_machines/{domain}_state_machine.json
  ├── ai-voucher-2025_state_machine.json
  ├── ship-building_state_machine.json (향후)
  └── ...
```

#### 방식 B: Python 클래스 (향후 고려)
```python
class ProjectStateMachine(StateMachine):
    STATES = [
        State("Submitted", initial=True),
        State("UnderReview"),
        State("Approved"),
        ...
    ]
    
    TRANSITIONS = [
        {
            "trigger": "request_review",
            "source": "Submitted",
            "dest": "UnderReview",
            "conditions": [
                lambda e: e.manager is not None,
                lambda e: e.budget >= 10_000_000
            ]
        },
        ...
    ]
```

---

## 3. AI바우처 도메인 — 상태 기계 상세 정의

### 3-1. PROJECT 엔티티 상태 기계

#### 상태 정의

| 상태 | 설명 | 진입 조건 | 퇴출 조건 |
|------|------|---------|---------|
| **Submitted** | 신청됨 | 신청사가 신청서 제출 | RequestReview 또는 RejectSubmission 액션 |
| **UnderReview** | 심사 중 | RequestReview 액션 실행 | ApproveProject, RejectProject, CancelReview 액션 |
| **Approved** | 승인됨 | ApproveProject 액션 실행 | StartPayment, CancelApproval 액션 |
| **Rejected** | 반려됨 | RejectProject, RejectSubmission 액션 | (최종 상태, 재신청만 가능) |
| **InProgress** | 진행 중 | StartPayment 액션 실행 | CompleteProject, CancelPayment 액션 |
| **Completed** | 완료됨 | CompleteProject 액션 실행 | (최종 상태) |

#### 전이 규칙

```
Submitted
  ├─ [RequestReview] → UnderReview
  │  조건: manager != null AND budget >= 10M
  │
  ├─ [RejectSubmission] → Rejected
  │  조건: true (항상 가능)
  │  권한: AccountManager, FinanceManager, Admin
  │
  └─ (자동) → Rejected (응답 30일 초과 시)
     타이머: 30일 (향후)

UnderReview
  ├─ [ApproveProject] → Approved
  │  조건: precondition_satisfied AND budget_validated
  │  권한: 조건부 (금액에 따라)
  │
  ├─ [RejectProject] → Rejected
  │  조건: true
  │  권한: FinanceManager, Admin
  │
  ├─ [RequestMoreInfo] → UnderReview (자기 루프)
  │  조건: true
  │  권한: AccountManager, FinanceManager
  │
  └─ [CancelReview] → Submitted
     조건: true
     권한: Admin만

Approved
  ├─ [StartPayment] → InProgress
  │  조건: payment_schedule != null AND bank_account_verified
  │  권한: PaymentManager, FinanceManager, Admin
  │
  └─ [CancelApproval] → Rejected
     조건: true
     권한: Admin만

Rejected
  └─ [Resubmit] → Submitted (향후 구현)
     조건: rejection_reason_addressed = true
     권한: Applicant

InProgress
  ├─ [CompleteProject] → Completed
  │  조건: payment_completed AND final_report_submitted
  │  권한: FinanceManager, Admin
  │
  └─ [CancelPayment] → Approved
     조건: payment_cancellable = true
     권한: PaymentManager, FinanceManager, Admin

Completed
  └─ (최종 상태 — 전이 불가)
```

### 3-2. State Machine JSON (예)

```json
{
  "domain": "ai-voucher-2025",
  "entity_type": "PROJECT",
  "states": [
    {
      "name": "Submitted",
      "display": "신청됨",
      "type": "initial",
      "color": "#gray"
    },
    {
      "name": "UnderReview",
      "display": "심사 중",
      "type": "intermediate",
      "color": "#yellow"
    },
    {
      "name": "Approved",
      "display": "승인됨",
      "type": "intermediate",
      "color": "#blue"
    },
    {
      "name": "Rejected",
      "display": "반려됨",
      "type": "final",
      "color": "#red"
    },
    {
      "name": "InProgress",
      "display": "진행 중",
      "type": "intermediate",
      "color": "#purple"
    },
    {
      "name": "Completed",
      "display": "완료됨",
      "type": "final",
      "color": "#green"
    }
  ],
  
  "transitions": [
    {
      "id": "submit_to_review",
      "name": "ReviewRequest",
      "from": "Submitted",
      "to": "UnderReview",
      "action_id": "request_review",
      "preconditions": [
        {
          "field": "properties.manager",
          "operator": "not_null"
        },
        {
          "field": "properties.budget",
          "operator": "gte",
          "value": 10000000
        }
      ],
      "permissions": ["Admin", "FinanceManager", "AccountManager"]
    },
    
    {
      "id": "submitted_to_rejected",
      "name": "RejectSubmission",
      "from": "Submitted",
      "to": "Rejected",
      "action_id": "reject_submission",
      "preconditions": [],
      "permissions": ["Admin", "FinanceManager", "AccountManager"],
      "required_fields": ["rejection_reason"]
    },
    
    {
      "id": "review_to_approved",
      "name": "ApproveProject",
      "from": "UnderReview",
      "to": "Approved",
      "action_id": "approve_project",
      "preconditions": [
        {
          "field": "properties.budget",
          "operator": "gte",
          "value": 10000000
        }
      ],
      "conditional_permissions": [
        {
          "condition": {
            "field": "properties.budget",
            "operator": "lte",
            "value": 50000000
          },
          "allowed_roles": ["TeamLead", "FinanceManager", "Admin"]
        },
        {
          "condition": {
            "field": "properties.budget",
            "operator": "gt",
            "value": 50000000,
            "operator": "lte",
            "value": 200000000
          },
          "allowed_roles": ["FinanceManager", "Admin"]
        },
        {
          "condition": {
            "field": "properties.budget",
            "operator": "gt",
            "value": 200000000
          },
          "allowed_roles": ["Admin"]
        }
      ],
      "required_fields": []
    },
    
    {
      "id": "approved_to_inprogress",
      "name": "StartPayment",
      "from": "Approved",
      "to": "InProgress",
      "action_id": "start_payment",
      "preconditions": [
        {
          "field": "properties.payment_schedule",
          "operator": "not_null"
        },
        {
          "field": "properties.bank_account_verified",
          "operator": "equals",
          "value": true
        }
      ],
      "permissions": ["PaymentManager", "FinanceManager", "Admin"]
    },
    
    {
      "id": "inprogress_to_completed",
      "name": "CompleteProject",
      "from": "InProgress",
      "to": "Completed",
      "action_id": "complete_project",
      "preconditions": [
        {
          "field": "properties.payment_completed",
          "operator": "equals",
          "value": true
        },
        {
          "field": "properties.final_report_submitted",
          "operator": "equals",
          "value": true
        }
      ],
      "permissions": ["FinanceManager", "Admin"]
    }
  ]
}
```

---

## 4. Write-back 메커니즘 상세 설계

### 4-1. Write-back 흐름 (상세)

```
┌──────────────────────────────────────────────────────────────┐
│ 1. 액션 실행 (e.g., ApproveProject)                          │
│    ├─ 권한 검증 ✓                                            │
│    ├─ 전제 조건 검증 ✓                                       │
│    └─ 속성 변경 (ontology)                                   │
└────────────────────┬─────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│ 2. Changelog 생성                                             │
│    └─ storage/.../ontology/changelog/PROJECT_changes.jsonl  │
│       {                                                       │
│         timestamp, entity_id, action_type,                  │
│         old_status, new_status, actor,                      │
│         sync_status: "pending",                             │
│         target_system: "SAP"                                │
│       }                                                       │
└────────────────────┬─────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│ 3. WriteBackQueue에 추가                                     │
│    └─ storage/.../write_back_queue/pending/{timestamp}.json │
│       {                                                       │
│         entity_id, field, old_value, new_value,             │
│         target_system: "SAP",                               │
│         api_endpoint: "/sap/project/{id}/status",           │
│         sync_status: "pending",                             │
│         created_at, next_retry_at: null                     │
│       }                                                       │
└────────────────────┬─────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│ 4. Background Worker 시작                                    │
│    (주기: 1분 또는 5분)                                       │
│                                                               │
│    4-1) pending 항목 읽기                                     │
│    4-2) SAP API 호출                                          │
│          POST /sap/project/{id}/status                       │
│          {                                                    │
│            "status": "Approved",                             │
│            "updated_by": "ont_platform",                     │
│            "updated_at": "2026-05-20T10:30:00Z"              │
│          }                                                    │
│    4-3) 응답 처리                                             │
│          ├─ 성공 (200)                                       │
│          │  └─ sync_status = "synced"                       │
│          │     sync_timestamp = 현재                         │
│          │     항목 → synced/ 폴더로 이동                     │
│          │                                                    │
│          ├─ 재시도 가능한 실패 (500, timeout)                │
│          │  └─ retry_count++                                │
│          │     next_retry_at = 현재 + 1시간                  │
│          │     max_retries = 3                              │
│          │                                                    │
│          └─ 재시도 불가능한 실패 (400, 401, 403)            │
│             └─ sync_status = "failed"                       │
│                error_message = 상세 메시지                    │
│                관리자 알림 발송                                │
│                항목 → failed/ 폴더로 이동                      │
└────────────────────┬─────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│ 5. 감시 & 알림                                               │
│    ├─ 실시간 모니터링 (Sentry/DataDog)                      │
│    ├─ 실패 항목 자동 알림 (관리자 이메일/Slack)              │
│    └─ 일일 리포트 (동기화 성공/실패 통계)                     │
└──────────────────────────────────────────────────────────────┘
```

### 4-2. 저장소 구조

```
storage/{company_id}/{project_id}/

├── ontology/
│   ├── domain_schema.json
│   ├── ai-voucher-2025.json
│   ├── materialized/
│   │   └── program_snapshot.json
│   └── changelog/
│       └── PROJECT_changes.jsonl          ◄─ 변경 이력
│
└── write_back_queue/
    ├── pending/
    │   ├── 2026-05-20T103000_001.json     ◄─ 미동기화
    │   ├── 2026-05-20T103100_002.json
    │   └── ...
    ├── synced/
    │   ├── 2026-05-20T102900_001.json     ◄─ 동기화 완료
    │   └── ...
    └── failed/
        ├── 2026-05-20T103000_001_retry3.json  ◄─ 3회 실패
        └── ...
```

### 4-3. Changelog 항목 상세

```json
{
  "timestamp": "2026-05-20T10:30:00.123456Z",
  "entity_id": "P001AAA",
  "entity_type": "PROJECT",
  "document_id": "ai-voucher-2025",
  
  "action_type": "APPROVE_PROJECT",
  "action_id": "approve_project",
  "triggered_by": "user@nipa.go.kr",
  "source": "web_ui",
  
  "old_state": {
    "status": "UnderReview",
    "approved_by": null,
    "approved_at": null
  },
  "new_state": {
    "status": "Approved",
    "approved_by": "user@nipa.go.kr",
    "approved_at": "2026-05-20T10:30:00Z"
  },
  
  "metadata": {
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "session_id": "sess_abc123"
  },
  
  "write_back": {
    "status": "pending",
    "target_system": "SAP",
    "api_endpoint": "/sap/project/P001AAA/status",
    "mapping": {
      "status": "Approved",
      "updated_by": "ont_platform",
      "updated_at": "2026-05-20T10:30:00Z"
    },
    "sync_timestamp": null,
    "retry_count": 0,
    "next_retry_at": null,
    "error_message": null
  }
}
```

### 4-4. WriteBackQueue 항목 상세

```json
{
  "id": "wbq_20260520_001",
  "created_at": "2026-05-20T10:30:00Z",
  
  "entity": {
    "id": "P001AAA",
    "type": "PROJECT",
    "document_id": "ai-voucher-2025"
  },
  
  "change": {
    "field": "status",
    "old_value": "UnderReview",
    "new_value": "Approved"
  },
  
  "target": {
    "system": "SAP",
    "endpoint": "POST /sap/project/{entity.id}/status",
    "payload": {
      "status": "Approved",
      "updated_by": "ont_platform",
      "updated_at": "2026-05-20T10:30:00Z",
      "entity_id": "P001AAA"
    }
  },
  
  "sync": {
    "status": "pending",
    "attempts": 0,
    "max_attempts": 3,
    "next_retry_at": null,
    "last_attempt_at": null,
    "last_error": null
  }
}
```

---

## 5. Worker 구현 (의사 코드)

### 5-1. WriteBackWorker

```python
class WriteBackWorker:
    def __init__(self):
        self.queue_dir = get_queue_path()
        self.retry_interval = 3600  # 1시간
        self.max_retries = 3
    
    async def run(self):
        """주기적으로 pending 항목 처리"""
        while True:
            self.process_pending()
            await asyncio.sleep(60)  # 1분마다 체크
    
    def process_pending(self):
        """pending 폴더의 모든 항목 처리"""
        pending_dir = self.queue_dir / "pending"
        for item_file in pending_dir.glob("*.json"):
            item = self.load_item(item_file)
            result = self.sync_to_target_system(item)
            
            if result["success"]:
                self.mark_synced(item, item_file)
            else:
                self.handle_failure(item, item_file, result["error"])
    
    def sync_to_target_system(self, item: dict) -> dict:
        """외부 시스템(SAP) API 호출"""
        target = item["target"]
        try:
            response = requests.post(
                url=self.build_url(target["system"], target["endpoint"]),
                json=target["payload"],
                timeout=10,
                headers={"Authorization": f"Bearer {get_api_key()}"}
            )
            
            if response.status_code == 200:
                return {"success": True}
            elif response.status_code in [500, 502, 503]:
                return {"success": False, "error": f"Server error: {response.status_code}", "retryable": True}
            else:
                return {"success": False, "error": f"Client error: {response.text}", "retryable": False}
        
        except (ConnectionError, Timeout) as e:
            return {"success": False, "error": str(e), "retryable": True}
    
    def handle_failure(self, item: dict, item_file: Path, error: str):
        """실패 항목 처리"""
        sync = item["sync"]
        sync["attempts"] += 1
        sync["last_error"] = error
        sync["last_attempt_at"] = datetime.utcnow().isoformat()
        
        if sync["attempts"] < self.max_retries:
            sync["status"] = "pending"
            sync["next_retry_at"] = (
                datetime.utcnow() + timedelta(seconds=self.retry_interval)
            ).isoformat()
            self.save_item(item_file, item)
        else:
            sync["status"] = "failed"
            failed_file = self.queue_dir / "failed" / item_file.name
            self.save_item(failed_file, item)
            self.notify_admin(item, error)
            item_file.unlink()
    
    def mark_synced(self, item: dict, item_file: Path):
        """동기화 완료 항목 처리"""
        item["sync"]["status"] = "synced"
        item["sync"]["sync_timestamp"] = datetime.utcnow().isoformat()
        synced_file = self.queue_dir / "synced" / item_file.name
        self.save_item(synced_file, item)
        item_file.unlink()
```

---

## 6. 모니터링 & 대시보드

### 6-1. 실시간 모니터링 지표

```
□ 동기화 성공률 (daily)
  - 대상: ≥ 95%
  
□ 동기화 지연 시간
  - 대상: p95 < 5분, p99 < 30분
  
□ 실패 항목 수
  - Alert: > 5개 미동기화 항목이 1시간 이상 지속

□ 재시도 횟수
  - 모니터링: 각 항목별 재시도 횟수 추적
```

### 6-2. 관리자 대시보드 (향후)

```
Write-back Dashboard
  ├─ 실시간 상태
  │  ├─ Pending: 5개
  │  ├─ Synced (오늘): 142개
  │  ├─ Failed: 2개
  │  └─ Syncing: 1개 (진행 중)
  │
  ├─ 시스템별 동기화
  │  ├─ SAP: 142/145 (98%)
  │  ├─ ERP: 10/10 (100%)
  │  └─ Slack: 150/150 (100%)
  │
  ├─ 최근 실패
  │  └─ [2026-05-20 10:45] P001AAA → SAP (timeout)
  │     재시도: 2/3
  │     다음 재시도: 11:45
  │
  └─ 이력 조회 (7일 필터)
     └─ 성공/실패별 필터링
```

---

## 7. 구현 체크리스트

### 7-1. Phase 3 Week 1~2 (상태 기계)

- [ ] ActionDefinition 모델 구현 (app/models/action.py)
- [ ] StateTransition 로직 (app/services/workflow.py 확장)
- [ ] ai-voucher-2025_state_machine.json 작성
- [ ] 조건부 권한 검증 로직
- [ ] 전제 조건 검증 로직
- [ ] 단위 테스트 (10개 이상)

### 7-2. Phase 3 Week 3 (Write-back)

- [ ] Changelog 모델 (app/models/changelog.py)
- [ ] WriteBackQueue 모델 (app/models/write_back_queue.py)
- [ ] WriteBackWorker 구현 (app/services/write_back_worker.py)
- [ ] SAP API Mock (테스트용)
- [ ] 통합 테스트 (Write-back 성공률 검증)

### 7-3. Phase 3 Week 4 (Frontend)

- [ ] Frontend ActionButton 컴포넌트
- [ ] Action 실행 UI 통합
- [ ] Audit 대시보드
- [ ] 통합 테스트 (25개 케이스)

---

## 8. 참고 자료

- [PHASE3_ACTION_DEFINITION.md](./PHASE3_ACTION_DEFINITION.md)
- [ARCHITECTURE.md — Write-back 개요](./ARCHITECTURE.md)
- [workflow.py — 현재 워크플로우 서비스](../src/backend/app/services/workflow.py)

---

**다음 단계**: workflow.json 확장 → ActionDefinition 모델 구현 → 단위 테스트

