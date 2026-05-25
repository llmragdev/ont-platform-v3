# Phase 3 — 비즈니스 액션 정의서

> **버전**: 1.0  
> **작성일**: 2026-05-20  
> **목표**: AI바우처 도메인 + 조선 도메인의 구체적인 액션 정의  
> **기준**: ROADMAP.md Phase 3 Stage 3A~3E

---

## 1. 액션 정의 개요

### 1-1. 액션의 정의
**액션** = 엔티티의 상태를 변경하는 **비즈니스 이벤트** + **권한 검증** + **부수 효과(Write-back)**

```
예) ApproveProject:
    ├─ 엔티티 타입: PROJECT
    ├─ 전제 조건: 현재 상태 = Submitted
    ├─ 권한 필요: FinanceManager (예산 > 100M) 또는 TeamLead (예산 ≤ 100M)
    ├─ 상태 전이: Submitted → Approved
    └─ 부수 효과: 
        ├─ ERP 전송 (예산 반영)
        ├─ 담당자 알림 (승인됨)
        └─ Audit log 기록
```

### 1-2. 액션의 3가지 범주

| 범주 | 설명 | 예시 |
|------|------|------|
| **상태 전이** | 엔티티 상태 변경 | ApproveProject, RejectProject |
| **데이터 변경** | 엔티티 속성 수정 | ChangeDeadline, UpdateBudget |
| **트리거 액션** | 외부 시스템 호출 | RequestProcurement, NotifyTeam |

---

## 2. AI바우처 도메인 — 액션 정의

### 2-1. 도메인 개요

| 속성 | 값 |
|------|-----|
| **도메인명** | AI바우처 2025 |
| **주요 엔티티** | PROGRAM, PROJECT, ORGANIZATION |
| **프로세스** | 신청 → 심사 → 승인 → 지급 → 종료 |
| **주요 액션 수** | 6개 (정의 예정) |

### 2-2. 엔티티 타입별 상태 기계

#### A. PROJECT (과제)

```
상태 정의:
  Submitted    → 신청됨 (초기 상태)
  UnderReview  → 심사 중 (재무팀 검토)
  Approved     → 승인됨 (최종 승인)
  Rejected     → 반려됨 (부적격)
  InProgress   → 진행 중 (자금 지급 시작)
  Completed    → 완료됨 (최종 정산)

상태 전이:
  Submitted → UnderReview  [Action: RequestReview]      (신청사 자체 액션)
  Submitted → Rejected     [Action: RejectSubmission]   (관리자, 조건 미충족)
  
  UnderReview → Approved   [Action: ApproveProject]     (재무팀, 조건부)
  UnderReview → Rejected   [Action: RejectProject]      (재무팀)
  UnderReview → UnderReview [Action: RequestMoreInfo]   (추가 정보 요청)
  
  Approved → InProgress    [Action: StartPayment]       (지급 담당자)
  Approved → Rejected      [Action: CancelApproval]     (관리자, 긴급)
  
  InProgress → Completed   [Action: CompleteProject]    (정산팀)
```

#### B. ORGANIZATION (기관)

```
상태 정의:
  Active, Inactive, Suspended, Closed

액션 예정:
  - ChangeStatus (Active ↔ Inactive)
  - SuspendOrganization (Active → Suspended)
```

---

## 3. AI바우처 — 구체적인 액션 정의 (6개)

### 액션 #1: ApproveProject

```yaml
Action ID: approve_project

엔티티 대상:
  Type: PROJECT
  
전제 조건 (Precondition):
  - 현재 상태: UnderReview
  - 예산 >= 10,000,000원 (1천만원 이상)
  - 담당자 배정됨 (properties.manager != null)
  - 첨부 문서 ≥ 1개
  
권한 모델:
  - Budget <= 50,000,000: TeamLead 이상
  - Budget > 50,000,000: FinanceManager 이상
  - Budget > 200,000,000: Admin만
  
상태 전이:
  UnderReview → Approved
  
속성 변경:
  - approved_by: 승인자 ID (자동 입력)
  - approved_at: 승인 시각 (자동 입력)
  - review_notes: 심사 의견 (선택, 사용자 입력)
  
부수 효과:
  1. Changelog 생성
     {
       entity_id: PROJECT_ID,
       action_type: "APPROVE_PROJECT",
       old_status: "UnderReview",
       new_status: "Approved",
       actor: user_id,
       timestamp: ISO8601,
       sync_status: "pending"
     }
  
  2. Write-back Queue에 추가 (대상: SAP)
     {
       entity_id: PROJECT_ID,
       field: "status",
       old_value: "UnderReview",
       new_value: "Approved",
       target_system: "SAP",
       sync_status: "pending"
     }
  
  3. 알림 발송
     - 신청사: "당신의 과제가 승인되었습니다"
     - 담당자: "PROJECT_ID 승인 완료"
     - NIPA: 운영 대시보드 업데이트
  
  4. 감사 로그 (audit.jsonl)
     {
       timestamp, entity_id, entity_type, action, actor, 
       old_values, new_values, result: "success"
     }

실패 시 처리:
  - 권한 없음 → HTTP 403
  - 상태 불일치 → HTTP 400 + "현재 UnderReview 상태만 가능"
  - Write-back 실패 → Changelog sync_status = "failed" (재시도 예정)

테스트 케이스:
  ✓ Admin이 예산 200M 과제 승인
  ✓ FinanceManager가 예산 150M 과제 승인 (성공)
  ✓ TeamLead가 예산 40M 과제 승인 (성공)
  ✓ TeamLead가 예산 60M 과제 승인 (실패: 권한 부족)
  ✓ UnderReview 상태가 아닐 때 실패
  ✓ 담당자 미배정 시 실패
```

### 액션 #2: RejectProject

```yaml
Action ID: reject_project

엔티티 대상:
  Type: PROJECT

전제 조건:
  - 현재 상태: Submitted 또는 UnderReview
  - 반려 사유 필수 (reason field)

권한 모델:
  - Submitted: AccountManager 이상
  - UnderReview: FinanceManager 이상

상태 전이:
  Submitted → Rejected (사유: 조건 미충족)
  UnderReview → Rejected (사유: 불승인)

속성 변경:
  - rejected_by: 반려자 ID
  - rejected_at: 반려 시각
  - rejection_reason: 반려 사유 (필수)

부수 효과:
  1. Changelog 생성
  2. 신청사에 알림 + 반려 사유 전달
  3. SAP 반영 (선택적 — 미반영)
  4. Audit log 기록

테스트 케이스:
  ✓ FinanceManager가 UnderReview 과제 반려 (성공)
  ✓ 반려 사유 없을 때 실패
  ✓ 잘못된 상태에서 반려 시도 (실패)
```

### 액션 #3: ChangeDeadline

```yaml
Action ID: change_deadline

엔티티 대상:
  Type: PROJECT

전제 조건:
  - 현재 상태: Approved 또는 InProgress
  - 새로운 deadline > 현재 deadline (이전 날짜로 변경 불가)
  - 최대 30일 연장 가능

권한 모델:
  - Manager 이상 가능
  - Admin은 제한 없음

상태 변이:
  상태 변경 없음 (Approved → Approved)

속성 변경:
  - deadline: 새로운 일정
  - deadline_changed_by: 변경자
  - deadline_changed_at: 변경 시각
  - deadline_change_count: 증가

부수 효과:
  1. Changelog
  2. 신청사 + 담당자 알림
  3. SAP 반영 (일정 동기화)

테스트 케이스:
  ✓ Manager가 30일 연장 (성공)
  ✓ 이전 날짜로 변경 시도 (실패)
  ✓ 31일 이상 연장 시도 (실패)
  ✓ Rejected 상태에서 변경 시도 (실패)
```

### 액션 #4: RequestMoreInfo

```yaml
Action ID: request_more_info

엔티티 대상:
  Type: PROJECT

전제 조건:
  - 현재 상태: UnderReview
  - 요청 사항 필수 (info_needed field)

권한 모델:
  - Reviewer (심사자) 이상

상태 변이:
  상태 변경 없음 (UnderReview → UnderReview)

속성 변경:
  - info_needed: 요청 사항 추가
  - info_requested_at: 요청 시각
  - info_requested_by: 요청자

부수 효과:
  1. 신청사에 알림 + 요청 사항 전달
  2. 응답 기한 설정 (e.g., 7일)
  3. 응답 없으면 자동 반려 (향후)

테스트 케이스:
  ✓ 추가 정보 요청 (성공)
  ✓ 신청사 응답 대기
```

### 액션 #5: StartPayment

```yaml
Action ID: start_payment

엔티티 대상:
  Type: PROJECT

전제 조건:
  - 현재 상태: Approved
  - 지급 일정 확정됨 (payment_schedule != null)
  - 신청사 계좌 검증됨

권한 모델:
  - PaymentManager 이상

상태 전이:
  Approved → InProgress

속성 변경:
  - payment_started_at: 지급 시작 시각
  - payment_started_by: 시작자

부수 효과:
  1. SAP: 자동 송금 명령 생성
  2. 신청사: "지급이 시작되었습니다" 알림
  3. 재무팀: 대시보드 업데이트

테스트 케이스:
  ✓ PaymentManager가 지급 시작 (성공)
  ✓ 미승인 과제에서 시작 시도 (실패)
  ✓ 계좌 미검증 시 실패
```

### 액션 #6: CompleteProject

```yaml
Action ID: complete_project

엔티티 대상:
  Type: PROJECT

전제 조건:
  - 현재 상태: InProgress
  - 지급 완료됨 (payment_completed = true)
  - 최종 보고서 제출됨

권한 모델:
  - FinanceManager 이상

상태 전이:
  InProgress → Completed

속성 변경:
  - completed_at: 완료 시각
  - completed_by: 완료자
  - final_status: "completed"

부수 효과:
  1. Audit log: 최종 정산 기록
  2. SAP: 최종 동기화
  3. 신청사: 완료 인증서 발급 (향후)

테스트 케이스:
  ✓ 정상 완료 (성공)
  ✓ 지급 미완료 시 완료 시도 (실패)
```

---

## 4. 권한 모델 (RBAC)

### 4-1. 역할 정의

| 역할 | 설명 | 권한 범위 |
|------|------|---------|
| **Admin** | 시스템 관리자 | 모든 액션 무제한 |
| **FinanceManager** | 재무 담당자 | 승인/반려, 지급, 정산 |
| **TeamLead** | 팀장 | 소속 팀 과제의 승인 (제한적) |
| **AccountManager** | 담당자 | 신청서 검토, 정보 요청 |
| **PaymentManager** | 지급 담당자 | 지급 시작만 |
| **Viewer** | 조회자 | 읽기 전용 |

### 4-2. 액션별 권한 매트릭스

```yaml
ApproveProject:
  Budget <= 50M: TeamLead, FinanceManager, Admin
  50M < Budget <= 200M: FinanceManager, Admin
  Budget > 200M: Admin만

RejectProject:
  Submitted → Submitted: AccountManager, FinanceManager, Admin
  UnderReview: FinanceManager, Admin

ChangeDeadline:
  Manager, FinanceManager, Admin

RequestMoreInfo:
  AccountManager, FinanceManager, Admin

StartPayment:
  PaymentManager, FinanceManager, Admin

CompleteProject:
  FinanceManager, Admin
```

---

## 5. 상태 기계 (State Diagram)

### 5-1. 완전한 상태 전이도

```
                    ┌────────────────┐
                    │  Submitted     │◄─── 초기 상태
                    └───────┬────────┘
                            │
                ┌───────────┼────────────┐
                │           │            │
      [RequestReview]   [Reject]    [RejectSubmission]
                │           │            │
                ▼           ▼            ▼
          ┌──────────┐  ┌────────────────────┐
          │UnderReview    Rejected           │
          └────┬──────┘  └────────────────────┘
               │
    ┌──────────┼──────────┬─────────────────┐
    │          │          │                 │
[Approve]  [Reject] [RequestMoreInfo]  [CancelApproval]
    │          │          │                 │
    ▼          ▼          ▼                 ▼
┌──────────┐ ┌──────────┐ ┌──────────┐   ┌──────────┐
│Approved  │ │Rejected  │ │UnderReview   Rejected  │
└────┬─────┘ └──────────┘ └──────────┘   └──────────┘
     │
[StartPayment]
     │
     ▼
┌──────────┐
│InProgress│
└────┬─────┘
     │
[CompleteProject]
     │
     ▼
┌──────────┐
│Completed │ ◄─── 최종 상태
└──────────┘
```

---

## 6. Write-back 메커니즘

### 6-1. Write-back 흐름

```
액션 실행 (e.g., ApproveProject)
    ↓
온톨로지 상태 변경 (properties.status = "Approved")
    ↓
Changelog 생성
{
  timestamp: ISO8601,
  entity_id: "P001AAA",
  entity_type: "PROJECT",
  action_type: "APPROVE_PROJECT",
  old_status: "UnderReview",
  new_status: "Approved",
  actor: "user@nipa.go.kr",
  source: "web_ui",
  sync_status: "pending",       ◄── 초기: pending
  target_system: "SAP",
  sync_timestamp: null
}
    ↓
WriteBackQueue에 추가
    ↓
[Background Worker] 주기적으로 pending 항목 처리
    ↓
SAP API 호출: POST /sap/project/{id}/status
    {
      status: "Approved",
      updated_by: "ont_platform",
      updated_at: ISO8601
    }
    ↓
성공 → sync_status = "synced", sync_timestamp = 현재
실패 → sync_status = "failed", retry_count++, next_retry_at = 현재 + 1시간
    ↓
최대 3회 재시도 후에도 실패 → 관리자 알림
```

### 6-2. Changelog 저장 위치

```
storage/{company_id}/{project_id}/ontology/changelog/
  ├── ai-voucher-2025_changes.jsonl  (행별 JSONL 형식)
  └── ...

각 행 예시:
{
  "timestamp": "2026-05-20T10:30:00Z",
  "entity_id": "P001AAA",
  "entity_type": "PROJECT",
  "action_type": "APPROVE_PROJECT",
  "old_status": "UnderReview",
  "new_status": "Approved",
  "actor": "user@nipa.go.kr",
  "source": "web_ui",
  "sync_status": "pending",
  "target_system": "SAP",
  "sync_timestamp": null,
  "retry_count": 0,
  "next_retry_at": null,
  "error_message": null
}
```

### 6-3. WriteBackQueue 저장 위치

```
storage/{company_id}/{project_id}/write_back_queue/
  ├── pending/
  │   ├── 2026-05-20_0001.json
  │   ├── 2026-05-20_0002.json
  │   └── ...
  └── failed/
      ├── 2026-05-20_0001_retry3.json
      └── ...
```

---

## 7. 구현 로드맵 (Phase 3)

### 7-1. 단계별 구현

#### Week 1 (5월 27 ~ 5월 31)
- [ ] ActionDefinition 모델 작성 (app/models/action.py)
- [ ] WorkflowTransition 로직 추가 (app/services/workflow.py)
- [ ] workflow.json을 "ai-voucher-2025" 도메인으로 확장
- [ ] 테스트: approve_project 액션 단일 구현 + 테스트

#### Week 2 (6월 3 ~ 6월 7)
- [ ] 나머지 5개 액션 구현 (reject, deadline, info, payment, complete)
- [ ] RBAC 체크 로직 추가
- [ ] API 엔드포인트 업데이트 (/api/actions)
- [ ] 테스트: 6개 액션 모두 PASS

#### Week 3 (6월 10 ~ 6월 14)
- [ ] Changelog 모델 및 저장 로직 (app/models/changelog.py)
- [ ] WriteBackQueue 구현 (app/services/write_back.py)
- [ ] SAP API Mock 구현 (테스트용)
- [ ] Write-back Worker (백그라운드 작업)

#### Week 4 (6월 17 ~ 6월 21)
- [ ] Frontend ActionButton 컴포넌트 (React)
- [ ] Action UI 통합 (쿼리 결과 + 액션 버튼)
- [ ] Audit 대시보드 (액션 이력 조회)
- [ ] Phase 3 통합 테스트 (25개 케이스 목표)

### 7-2. 성공 기준

```
□ 6개 액션 모두 구현 + 단위 테스트 통과
□ RBAC 검증 완벽
□ Write-back 성공률 ≥ 95%
□ 통합 테스트 20/25 이상 통과
□ Frontend 액션 버튼 렌더링 + 실행 가능
□ Audit log 완전 추적
□ SAP/ERP 연동 준비 완료 (Mock)
```

---

## 8. 부록: 조선 도메인 액션 스케치 (향후)

### 8-1. 조선 도메인 개요

```
주요 엔티티: SHIP, BLOCK, WORKER, MATERIAL, SENSOR
```

### 8-2. 액션 (우선순위)

| 액션 | 대상 | 상태 전이 | 우선순위 |
|------|-----|---------|--------|
| **ChangeWCDate** | BLOCK | ScheduledReady → Delayed | 🔴 High |
| **RequestMaterial** | MATERIAL | Available → Ordered | 🔴 High |
| **NotifyWorker** | WORKER | - (알림만) | 🟠 Medium |
| **SyncToERP** | SHIP | - (ERP 반영) | 🔴 High |

---

## 9. 참고 자료

- [ROADMAP.md — Phase 3 전체 계획](./ROADMAP.md#4-phase-3--실행형-워크플로우)
- [ARCHITECTURE.md — Write-back 메커니즘](./ARCHITECTURE.md#5-현재-구현-단계-vs-로드맵)
- [workflow.py — 현재 액션 서비스](../src/backend/app/services/workflow.py)

---

**다음 단계**: 이 문서 검토 → workflow.json 수정 → ActionDefinition 모델 작성 시작

