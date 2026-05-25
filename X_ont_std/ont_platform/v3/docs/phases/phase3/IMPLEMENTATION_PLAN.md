# Phase 3 구현 계획서 (4주 상세 일정)

> **프로젝트**: ont_platform v3  
> **단계**: Phase 3 — 실행형 워크플로우  
> **기간**: 2026-05-27 ~ 2026-07-31 (10주)  
> **작성**: 2026-05-20  
> **상태**: 📋 계획 수립 완료

---

## 📅 Phase 3 전체 일정

```
2026-05월:
  ├─ 05-20 (화): 설계 문서 완성 ✅
  ├─ 05-21 (수): 설계 검토
  └─ 05-24 (토): Phase 2 마무리 (통합 테스트 20/25)

2026-06월:
  ├─ Week 1 (05-27 ~ 05-31): ActionDefinition 모델 + 6개 액션
  ├─ Week 2 (06-03 ~ 06-07): 권한 검증 + API 통합
  ├─ Week 3 (06-10 ~ 06-14): Changelog + Write-back + Worker
  └─ Week 4 (06-17 ~ 06-21): Frontend + 통합 테스트

2026-07월:
  ├─ Week 5-6 (06-24 ~ 07-07): 버그 수정 + 성능 최적화
  ├─ Week 7-8 (07-08 ~ 07-21): 고객 PoC 준비
  └─ 07-31 (목): Phase 3 완료
```

---

## 🔴 Week 1 (05-27 ~ 05-31): ActionDefinition 모델 + 액션 구현

### 목표
- ActionDefinition 모델 구현
- 6개 액션 코드 작성
- 단위 테스트 (6개 액션 모두)

### 산출물 체크리스트

#### 1️⃣ ActionDefinition 모델 (app/models/action.py)
```python
class ActionDefinition:
    id: str                    # approve_project
    display_name: str          # 과제 승인
    entity_type: str           # PROJECT
    from_statuses: list[str]   # [UnderReview]
    to_status: str | None      # Approved
    preconditions: list[dict]  # [조건1, 조건2, ...]
    allowed_roles: list[str]   # [Admin, FinanceManager]
    conditional_permissions: list[dict]  # 조건부 권한
    property_changes: list[dict]  # 속성 변경 규칙
    required_fields: list[str]  # [rejection_reason]
    side_effects: list[dict]   # Changelog, Write-back, 알림
```

**상태**: 설계 완료 (workflow.json 형식 정의됨)  
**예상 시간**: 3~4시간  
**담당**: Backend

#### 2️⃣ 6개 액션 코드 구현
```
approve_project        ← 우선순위: 🔴 High (조건부 권한 테스트 필요)
reject_project         ← 우선순위: 🟠 Medium
change_deadline        ← 우선순위: 🟠 Medium (상태 유지)
request_more_info      ← 우선순위: 🟠 Medium (상태 유지)
start_payment          ← 우선순위: 🟠 Medium
complete_project       ← 우선순위: 🟠 Medium
```

**상태**: 골격 코드 완료 (workflow.py 수정됨)  
**예상 시간**: 8~10시간  
**담당**: Backend

#### 3️⃣ 단위 테스트 (test_phase3_actions.py)
```python
class TestApproveProject:
    def test_approve_by_admin_large_budget(self):
        # 예산 200M 과제를 Admin이 승인 → 성공
        
    def test_approve_by_finance_manager_medium_budget(self):
        # 예산 100M 과제를 FinanceManager가 승인 → 성공
        
    def test_approve_by_teamlead_small_budget(self):
        # 예산 30M 과제를 TeamLead가 승인 → 성공
        
    def test_approve_by_teamlead_large_budget(self):
        # 예산 60M 과제를 TeamLead가 승인 → 실패 (권한 부족)
        
    def test_precondition_failed_no_manager(self):
        # 담당자 미배정 상태에서 승인 시도 → 실패
        
    def test_precondition_failed_low_budget(self):
        # 예산 500만원 과제 승인 시도 → 실패

class TestRejectProject:
    def test_reject_with_reason(self):
        # 반려 사유 포함 → 성공
        
    def test_reject_without_reason(self):
        # 반려 사유 없음 → 실패

# ... 나머지 액션
```

**상태**: 테스트 틀 작성됨 (workflow.py 로직 기반)  
**예상 시간**: 6~8시간  
**담당**: QA / Backend

### 완료 기준
- [ ] ActionDefinition 모델 구현 완료
- [ ] 6개 액션 모두 구현 완료
- [ ] 단위 테스트 30개 이상 작성
- [ ] **테스트 통과율 ≥ 90%**

### 위험 요소
🔴 조건부 권한 로직 복잡 → 충분한 테스트 필요  
🟠 템플릿 변수 치환 (user_id, timestamp) → 테스트 필요

---

## 🟡 Week 2 (06-03 ~ 06-07): 권한 검증 + API 통합

### 목표
- 조건부 권한 검증 완벽화
- API 엔드포인트 통합
- Frontend와 연동 준비
- Swagger 문서화

### 산출물 체크리스트

#### 1️⃣ 권한 검증 강화
```python
def check_permission_with_conditions(
    user_role: str,
    entity: dict,
    action_cfg: dict
) -> tuple[bool, str]:
    """
    조건부 권한 검증
    예: 예산 5천만원 이하 → TeamLead 가능
        예산 5천~2억원 → FinanceManager 만 가능
    """
```

**상태**: 골격만 있음  
**예상 시간**: 4~6시간

#### 2️⃣ API 엔드포인트 확장
```
POST /api/workflow/execute
├─ Request: {
│   doc_id: "ai-voucher-2025",
│   entity_id: "P001AAA",
│   action: "approve_project",
│   domain_id: "ai-voucher-2025",
│   params: {
│     rejection_reason: "... (필수 필드)"
│   }
│ }
└─ Response: {
    entity_id, action, from_status, to_status,
    approved_by, approved_at
  }

GET /api/workflow/queue?domain_id=ai-voucher-2025
├─ Query params: domain_id, entity_type
└─ Response: { count, items: [...available actions...] }
```

**상태**: 기본 구조 완료 (domain_id 파라미터 추가됨)  
**예상 시간**: 3~4시간

#### 3️⃣ Swagger/OpenAPI 문서
```yaml
paths:
  /api/workflow/execute:
    post:
      summary: 액션 실행
      parameters:
        - name: domain_id
          in: query
          type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ActionRequest'
      responses:
        '200':
          description: 액션 실행 성공
        '400':
          description: 전제 조건 미충족
        '403':
          description: 권한 부족
```

**상태**: 미작성  
**예상 시간**: 2~3시간

#### 4️⃣ 통합 테스트 (test_phase3_api.py)
```python
def test_approve_endpoint_success(client):
    # POST /api/workflow/execute with approve_project
    
def test_approve_endpoint_permission_denied(client):
    # TeamLead이 큰 예산 과제 승인 시도 → 403
    
def test_queue_endpoint_shows_available_actions(client):
    # GET /api/workflow/queue → 역할별로 다른 액션 목록
```

**상태**: 미작성  
**예상 시간**: 4~5시간

### 완료 기준
- [ ] 조건부 권한 검증 100% 구현
- [ ] API 엔드포인트 통합 테스트 통과
- [ ] Swagger 문서 완성
- [ ] **API 통합 테스트 ≥ 15개**

---

## 🟠 Week 3 (06-10 ~ 06-14): Changelog + Write-back + Worker

### 목표
- Changelog 저장소 구현
- WriteBackQueue 모델 구현
- WriteBackWorker (백그라운드) 구현
- Write-back 통합 테스트

### 산출물 체크리스트

#### 1️⃣ Changelog 모델 (app/models/changelog.py)
```python
class ChangeLog:
    timestamp: str           # ISO8601
    entity_id: str          # P001AAA
    entity_type: str        # PROJECT
    action_type: str        # APPROVE_PROJECT
    old_status: str | None  # UnderReview
    new_status: str | None  # Approved
    actor: str              # user@nipa.go.kr
    source: str             # web_ui
    sync_status: str        # pending | synced | failed
    target_system: str      # SAP
    sync_timestamp: str | None
    retry_count: int
    error_message: str | None
```

**저장 위치**: `storage/{company}/{project}/ontology/changelog/{domain}_changes.jsonl`  
**예상 시간**: 3~4시간

#### 2️⃣ WriteBackQueue 모델 (app/models/write_back_queue.py)
```python
class WriteBackQueueItem:
    id: str                 # wbq_20260520_001
    created_at: str
    entity: {id, type, document_id}
    change: {field, old_value, new_value}
    target: {system, endpoint, payload}
    sync: {status, attempts, max_attempts, next_retry_at}
```

**저장 위치**: `storage/{company}/{project}/write_back_queue/{status}/`  
**예상 시간**: 2~3시간

#### 3️⃣ WriteBackWorker (app/services/write_back_worker.py)
```python
class WriteBackWorker:
    async def run(self):
        """주기적 실행 (1분 주기)"""
        while True:
            self.process_pending()  # pending 항목 처리
            await asyncio.sleep(60)
    
    def process_pending(self):
        """SAP API 호출 + 재시도 로직"""
        # 1. pending 폴더 읽기
        # 2. SAP API POST
        # 3. 성공: synced로 이동
        # 4. 재시도 가능 실패: 1시간 뒤 재시도
        # 5. 재시도 불가 실패: failed로 이동 + 알림
```

**상태**: 의사코드만 있음  
**예상 시간**: 6~8시간

#### 4️⃣ SAP API Mock (for testing)
```python
class SAPApiMock:
    def post(self, endpoint: str, payload: dict) -> dict:
        """테스트용 Mock API"""
        if endpoint == "/sap/project/{id}/status":
            # 90% 확률로 성공
            # 10% 확률로 timeout (재시도 대상)
            return {"status": "ok", "sync_id": "sync_123"}
```

**예상 시간**: 2~3시간

#### 5️⃣ 통합 테스트 (test_phase3_write_back.py)
```python
def test_changelog_created_on_action(self):
    # 액션 실행 → Changelog 자동 생성
    
def test_write_back_queue_item_created(self):
    # 액션 실행 → WriteBackQueue 항목 추가
    
def test_worker_syncs_to_sap(self):
    # Worker 실행 → SAP API 호출 → synced 상태 변경
    
def test_worker_retries_on_timeout(self):
    # 타임아웃 시 3회 재시도
    
def test_worker_marks_failed_after_max_retries(self):
    # 3회 실패 후 failed 상태
```

**예상 시간**: 4~5시간

### 완료 기준
- [ ] Changelog 저장소 구현 완료
- [ ] WriteBackQueue 모델 구현 완료
- [ ] WriteBackWorker 실행 가능
- [ ] **Write-back 통합 테스트 ≥ 10개**
- [ ] **Write-back 성공률 ≥ 95%** (Mock 기준)

---

## 🟢 Week 4 (06-17 ~ 06-21): Frontend + 통합 테스트

### 목표
- Frontend ActionButton 컴포넌트 구현
- 쿼리 결과 + 액션 버튼 통합
- Audit 대시보드 (액션 이력 조회)
- Phase 3 최종 통합 테스트

### 산출물 체크리스트

#### 1️⃣ Frontend ActionButton 컴포넌트
```typescript
interface ActionButtonProps {
  entityId: string;
  entityType: string;
  currentStatus: string;
  availableActions: string[];
  onActionClick: (action: string, params?: dict) => void;
  loading?: boolean;
}

export function ActionButton(props: ActionButtonProps) {
  // 액션별 버튼 렌더링
  // 필수 입력칸 표시 (params 필요 시)
  // 클릭 → /api/workflow/execute 호출
}
```

**파일**: `src/frontend/src/components/ActionButton.tsx`  
**예상 시간**: 4~5시간

#### 2️⃣ QueryResult 통합 (AI 쿼리 결과 + 액션)
```typescript
// 현재:
{
  query: "...",
  answer: "지연 위험: HIGH",
  quality_metrics: {...}
}

// 목표:
{
  query: "...",
  answer: "지연 위험: HIGH",
  quality_metrics: {...},
  available_actions: [
    {
      name: "change_deadline",
      display: "일정 변경",
      required_params: ["new_deadline"]
    },
    {
      name: "request_material",
      display: "자재 발주",
      required_params: []
    }
  ]
}
```

**예상 시간**: 3~4시간

#### 3️⃣ Audit 대시보드
```
[Audit Dashboard]
├─ 필터: 날짜, 액션, 사용자, 상태 (성공/실패)
├─ 테이블:
│  ├─ 시간 | 액션 | 사용자 | 엔티티 | 상태 | 상세
│  ├─ 2026-06-17 10:30 | ApproveProject | user@nipa.go.kr | P001AAA | ✅ 성공
│  └─ 2026-06-17 10:31 | RejectProject | user@nipa.go.kr | P001BBB | ✅ 성공
└─ 상세 보기: 액션 전후 상태, Write-back 상태 등
```

**파일**: `src/frontend/src/components/AuditDashboard.tsx`  
**예상 시간**: 5~6시간

#### 4️⃣ 최종 통합 테스트 (e2e)
```
시나리오 1: ApproveProject 전체 흐름
  1. 신청사가 과제 신청 (상태: Submitted)
  2. 심사자가 상태 → UnderReview로 변경
  3. 재무팀이 과제 승인 (조건부 권한 검증)
  4. Changelog 생성 확인
  5. WriteBackQueue 생성 확인
  6. Worker가 SAP 동기화 완료
  7. Audit 로그에 기록됨 확인
  
시나리오 2: 조건부 권한 검증
  - TeamLead이 60M 예산 과제 승인 시도 → 실패
  - FinanceManager가 승인 → 성공
  
시나리오 3: 전제 조건 검증
  - 담당자 미배정 상태에서 승인 시도 → 실패 메시지 표시
  
... (추가 10개 시나리오)
```

**예상 시간**: 8~10시간

### 완료 기준
- [ ] ActionButton 컴포넌트 완성 + 테스트
- [ ] QueryResult 액션 통합 완성
- [ ] Audit 대시보드 완성
- [ ] **e2e 통합 테스트 ≥ 15개**
- [ ] **최종 통합 테스트 통과율 ≥ 85%**

---

## 📊 전체 진행도 추적

### Week 1 (05-27 ~ 05-31)
```
[████░░░░░░░░░░░░░░] 20% (ActionDefinition + 6개 액션)
- ActionDefinition 모델
- 6개 액션 구현
- 단위 테스트 (30개+)
```

### Week 2 (06-03 ~ 06-07)
```
[████████░░░░░░░░░░] 40% (권한 검증 + API)
- 조건부 권한 완벽화
- API 엔드포인트 통합
- Swagger 문서
- 통합 테스트 (15개+)
```

### Week 3 (06-10 ~ 06-14)
```
[████████████░░░░░░] 60% (Write-back)
- Changelog 구현
- WriteBackQueue 구현
- WriteBackWorker 구현
- 통합 테스트 (10개+)
```

### Week 4 (06-17 ~ 06-21)
```
[████████████████░░] 80% (Frontend + 최종)
- ActionButton 컴포넌트
- QueryResult 통합
- Audit 대시보드
- e2e 테스트 (15개+)
```

### Week 5-8 (06-24 ~ 07-21)
```
[██████████████████] 100% (버그 수정 + PoC)
- 성능 최적화
- 버그 수정
- 고객 PoC 준비
```

---

## 🎯 Success Criteria (Phase 3 종료 시)

```
Code Quality:
  ✓ 6개 액션 모두 구현 + 테스트 통과
  ✓ 코드 커버리지 ≥ 80%
  ✓ 타입 힌트 100% (mypy 통과)

Functional:
  ✓ RBAC 검증 완벽 (조건부 권한 포함)
  ✓ Write-back 성공률 ≥ 95%
  ✓ Audit 로그 완전 추적
  ✓ Frontend 액션 버튼 렌더링 + 실행 가능

Testing:
  ✓ 단위 테스트 ≥ 30개 (Week 1)
  ✓ API 통합 테스트 ≥ 15개 (Week 2)
  ✓ Write-back 테스트 ≥ 10개 (Week 3)
  ✓ e2e 테스트 ≥ 15개 (Week 4)
  ✓ 최종 통합 테스트 통과율 ≥ 85%

Documentation:
  ✓ API 문서 (Swagger) 완성
  ✓ 액션 가이드 문서 작성
  ✓ Audit 대시보드 사용 가이드
```

---

## 📌 주간 회고 (매주 금요일)

### Week 1 회고 (05-31)
```
□ ActionDefinition 모델 검토
□ 액션 구현 완성도 확인
□ 단위 테스트 커버리지 확인
□ Week 2 준비 (예상 이슈 파악)
```

### Week 2 회고 (06-07)
```
□ 권한 검증 로직 검토
□ API 통합 완성도 확인
□ Swagger 문서 품질 확인
□ Week 3 준비 (Write-back 리스크 분석)
```

### Week 3 회고 (06-14)
```
□ Changelog 저장소 안정성 확인
□ WriteBackWorker 성능 테스트
□ Write-back 성공률 확인
□ Week 4 준비 (Frontend 리소스 확인)
```

### Week 4 회고 (06-21)
```
□ Frontend 컴포넌트 완성도 확인
□ e2e 테스트 결과 분석
□ 최종 통합 테스트 통과율
□ Phase 3 완료 선언 (또는 연장 필요 판단)
```

---

## 🚨 위험 요소 & 대응 방안

| 위험 | 확률 | 영향 | 대응 |
|------|------|------|------|
| 조건부 권한 로직 복잡 | 높음 | 중간 | 테스트 충분 |
| Write-back SAP API 통신 실패 | 중간 | 높음 | Mock으로 테스트, 재시도 로직 강화 |
| Frontend 컴포넌트 지연 | 중간 | 중간 | Week 4에서 충분한 시간 확보 |
| 데이터베이스 성능 (Changelog JSONL) | 낮음 | 중간 | 인덱싱 고려 |

---

## 📞 의존성 & 협업

### 필요한 것
- [ ] SAP API 명세 (또는 Mock 스펙)
- [ ] AI바우처 팀 인터뷰 (실제 워크플로우)
- [ ] Frontend 팀과의 정기 회의

### 담당자
- **Backend**: 단위 테스트, ActionDefinition, 6개 액션, Changelog, Worker
- **QA**: 통합 테스트, e2e 테스트, 성능 테스트
- **Frontend**: ActionButton, Audit 대시보드, QueryResult 통합

---

**시작 날짜**: 2026-05-27 (화)  
**예상 완료**: 2026-07-31 (목)  
**총 소요 기간**: 10주

🚀 준비 완료!

