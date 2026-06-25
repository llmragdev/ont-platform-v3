# Phase 3 Week 4 Codex (Frontend) 작업 지시서

**기간**: 2026-06-17 ~ 2026-06-21 (5일)  
**담당**: Codex (Frontend Agent)  
**목표**: ActionButton 컴포넌트 + Audit 대시보드 구현  
**예상시간**: 10~12시간

---

## 🎯 Week 4 Codex 임무

Frontend에서 사용자가 액션을 실행하고 그 결과를 모니터링하는 UI 구현:
1. **ActionButton 컴포넌트** (액션 실행 UI)
2. **Audit 대시보드** (액션 이력 조회)
3. **QueryResult 통합** (쿼리 결과 + 액션)

---

## 📋 Task 분해

### Task 1: ActionButton 컴포넌트 (4~5시간)
**파일**: `src/frontend/src/components/ActionButton.tsx`

#### 컴포넌트 스펙
```typescript
interface ActionButtonProps {
  entityId: string;
  entityType: string;
  currentStatus: string;
  availableActions: Array<{
    name: string;           // approve_project
    display: string;        // 프로젝트 승인
    required_params: string[]; // ['approver']
  }>;
  onActionClick?: (action: string, params: any) => void;
  loading?: boolean;
  disabled?: boolean;
}

export function ActionButton(props: ActionButtonProps) {
  // 구현
}
```

#### 기능 요구사항
- ✅ 드롭다운/메뉴에서 액션 선택
- ✅ 필수 파라미터 입력 폼 표시
  - approver (텍스트)
  - reason (textarea)
  - new_deadline (날짜)
  - amount (숫자)
  - etc
- ✅ 액션 실행 버튼
- ✅ 로딩 상태 표시
- ✅ 에러 메시지 표시
- ✅ 성공 토스트 메시지
- ✅ API 호출: POST /api/workflow/execute

#### API 호출 형식
```typescript
const response = await fetch('/api/workflow/execute', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    entity_id: props.entityId,
    entity_type: props.entityType,
    domain_id: "ai-voucher-2025",
    action: selectedAction.name,
    params: {
      // 사용자가 입력한 파라미터
      approver: formData.approver,
      amount: formData.amount,
      // etc
    }
  })
});
```

#### UI/UX 요구사항
- ✅ 액션 버튼이 비활성화되면 회색 처리
- ✅ 현재 상태에서 불가능한 액션은 표시 안 함
- ✅ 로딩 중: 스피너 표시
- ✅ 성공: 초록색 토스트 + 자동 닫힘
- ✅ 실패: 빨간색 토스트 + 에러 메시지 표시

#### 테스트 (Cypress E2E)
```javascript
describe('ActionButton', () => {
  it('should render action dropdown', () => {
    // ActionButton 렌더링 확인
    cy.get('[data-testid="action-button"]').should('exist');
  });

  it('should show required params form', () => {
    // 액션 선택 시 파라미터 폼 표시
    cy.get('[data-testid="action-select"]').select('approve_project');
    cy.get('[data-testid="param-approver"]').should('be.visible');
  });

  it('should execute action on button click', () => {
    // 액션 실행
    cy.get('[data-testid="action-select"]').select('approve_project');
    cy.get('[data-testid="param-approver"]').type('pm@example.com');
    cy.get('[data-testid="action-execute"]').click();
    cy.get('[data-testid="success-toast"]').should('be.visible');
  });

  it('should show error toast on failure', () => {
    // 실패 시 에러 표시
    cy.get('[data-testid="action-select"]').select('invalid_action');
    cy.get('[data-testid="action-execute"]').click();
    cy.get('[data-testid="error-toast"]').should('be.visible');
  });

  it('should disable button on loading', () => {
    // 로딩 중 버튼 비활성화
    cy.get('[data-testid="action-execute"]').click();
    cy.get('[data-testid="action-execute"]').should('be.disabled');
  });
});
```

---

### Task 2: Audit 대시보드 (4~5시간)
**파일**: `src/frontend/src/components/AuditDashboard.tsx`

#### 컴포넌트 스펙
```typescript
interface AuditDashboardProps {
  domainId?: string;
  entityId?: string;
}

export function AuditDashboard(props: AuditDashboardProps) {
  // 구현
}
```

#### 기능 요구사항

**필터 섹션**:
- ✅ 날짜 범위 (from/to)
- ✅ 액션 유형 (dropdown: APPROVE, REJECT, CHANGE_DEADLINE, etc)
- ✅ 사용자 (텍스트 입력)
- ✅ 동기화 상태 (dropdown: PENDING, SYNCED, FAILED)
- ✅ 필터 적용 버튼
- ✅ 필터 초기화 버튼

**데이터 테이블**:
```
| 액션 | 사용자 | 시간 | 상태 | 상태변화 | 상세 |
|------|--------|------|------|---------|------|
| APPROVE_PROJECT | pm@example.com | 14:30:45 | SYNCED | UnderReview→Approved | ▼ |
| REJECT_PROJECT | reviewer@example.com | 13:20:15 | SYNCED | UnderReview→Rejected | ▼ |
| START_PAYMENT | cfo@example.com | 12:10:05 | FAILED | Approved→PaymentStarted | ▼ |
```

**상세 정보 (클릭 시 펼침)**:
```
액션: APPROVE_PROJECT
프로젝트: proj_001
승인자: pm@example.com
이전상태: UnderReview
변경상태: Approved
시간: 2026-06-20 14:30:45
동기화상태: SYNCED
동기화시간: 2026-06-20 14:30:50
대상시스템: SAP
재시도횟수: 0
```

**통계 섹션** (상단):
```
┌─────────────────┬──────────────┬──────────────┐
│ 오늘 동기화 성공률 │ 실패 항목 수 │ 평균 재시도 │
│     92.5%       │      3       │     1.2     │
└─────────────────┴──────────────┴──────────────┘
```

**추가 기능**:
- ✅ 페이지네이션 (50개씩)
- ✅ 로딩 상태 표시
- ✅ 데이터 없음 메시지
- ✅ CSV 다운로드 버튼

#### API 호출
```typescript
// 필터링된 changelog 조회
const response = await fetch(
  `/api/changelog/history?` +
  `entity_id=${filters.entityId}&` +
  `action_type=${filters.actionType}&` +
  `sync_status=${filters.syncStatus}&` +
  `date_from=${filters.dateFrom}&` +
  `date_to=${filters.dateTo}&` +
  `page=${currentPage}&` +
  `page_size=50`
);
```

#### 테스트 (Cypress E2E)
```javascript
describe('AuditDashboard', () => {
  it('should render dashboard with filter section', () => {
    cy.get('[data-testid="audit-dashboard"]').should('exist');
    cy.get('[data-testid="filter-date-from"]').should('exist');
    cy.get('[data-testid="filter-action-type"]').should('exist');
  });

  it('should filter by action type', () => {
    cy.get('[data-testid="filter-action-type"]').select('APPROVE_PROJECT');
    cy.get('[data-testid="filter-apply"]').click();
    // 테이블에 APPROVE_PROJECT만 표시
    cy.get('[data-testid="table-row"]').each(row => {
      cy.wrap(row).contains('APPROVE_PROJECT');
    });
  });

  it('should show pagination', () => {
    cy.get('[data-testid="pagination"]').should('exist');
    cy.get('[data-testid="pagination-next"]').click();
    // 다음 페이지 데이터 표시
  });

  it('should expand row details', () => {
    cy.get('[data-testid="row-expand"]').first().click();
    cy.get('[data-testid="row-details"]').should('be.visible');
  });

  it('should download CSV', () => {
    cy.get('[data-testid="download-csv"]').click();
    // CSV 파일 다운로드 검증
  });
});
```

---

### Task 3: QueryResult 통합 (2~3시간)
**파일**: `src/frontend/src/components/QueryResult.tsx` (기존 수정)

#### 변경 사항

**현재 상태**:
```typescript
interface QueryResult {
  query: string;
  answer: string;
  quality_metrics: {
    relevance: number;
    completeness: number;
  };
}
```

**목표 상태**:
```typescript
interface QueryResult {
  query: string;
  answer: string;
  quality_metrics: {
    relevance: number;
    completeness: number;
  };
  entity_id?: string;
  entity_type?: string;
  current_status?: string;
  available_actions?: Array<{
    name: string;
    display: string;
    required_params: string[];
  }>;
}
```

#### 구현 요구사항
- ✅ 기존 답변 영역은 유지
- ✅ ActionButton 컴포넌트 추가 (있을 때만)
- ✅ 액션이 없으면 버튼 표시 안 함
- ✅ 액션 성공 후 자동 새로고침 (선택사항)

#### 레이아웃
```
┌─────────────────────────────────┐
│ Query Result                    │
├─────────────────────────────────┤
│ 질문: 현재 프로젝트 상태는?      │
│                                  │
│ 답변: 지연 위험: HIGH           │
│ 원인: 예산 부족 + 자재 딜레이   │
│                                  │
│ 신뢰도: 92% | 완성도: 85%      │
├─────────────────────────────────┤
│ 💡 권장 액션:                   │
│  [▼ 액션 선택▼]                │
└─────────────────────────────────┘
```

#### 테스트 (Cypress E2E)
```javascript
describe('QueryResult with Actions', () => {
  it('should show action button when actions available', () => {
    cy.get('[data-testid="query-result"]').should('exist');
    cy.get('[data-testid="action-button"]').should('exist');
  });

  it('should hide action button when no actions', () => {
    cy.get('[data-testid="query-result"]').should('exist');
    cy.get('[data-testid="action-button"]').should('not.exist');
  });

  it('should execute action and refresh result', () => {
    cy.get('[data-testid="action-select"]').select('change_deadline');
    cy.get('[data-testid="param-deadline"]').type('2026-07-31');
    cy.get('[data-testid="action-execute"]').click();
    cy.get('[data-testid="success-toast"]').should('be.visible');
    // 새로고침 검증 (optional)
  });
});
```

---

## 🎨 디자인 가이드

### 색상 스키마
- 성공 (SYNCED): 초록색 (#10B981)
- 실패 (FAILED): 빨간색 (#EF4444)
- 대기 (PENDING): 주황색 (#F59E0B)
- 버튼 활성: 파란색 (#3B82F6)
- 버튼 비활성: 회색 (#D1D5DB)

### 컴포넌트 라이브러리
- React Hook Form (폼 관리)
- shadcn/ui 또는 Tailwind CSS (스타일)
- React Query (데이터 페칭)
- Axios (HTTP 요청)

---

## 📁 디렉토리 구조

```
src/frontend/src/
├── components/
│   ├── ActionButton.tsx           ← 신규 (Task 1)
│   ├── AuditDashboard.tsx         ← 신규 (Task 2)
│   ├── QueryResult.tsx            ← 수정 (Task 3)
│   └── ...
├── pages/
│   └── audit.tsx                  ← 신규 (대시보드 페이지)
├── hooks/
│   └── useChangelog.ts            ← 신규 (데이터 페칭)
└── types/
    └── changelog.ts               ← 신규 (타입 정의)
```

---

## 🧪 테스트 전략

### 구성
- **Cypress E2E**: 5개 (ActionButton)
- **Cypress E2E**: 5개 (AuditDashboard)
- **Cypress E2E**: 3개 (QueryResult 통합)
- **합계**: 13개 E2E 테스트

### 실행 환경
```bash
# 개발 서버 시작
npm run dev

# Cypress 테스트 실행
npm run cypress:e2e

# 또는 헤드리스 모드
npm run cypress:run
```

---

## 📊 완료 기준

```
✅ Task 1: ActionButton 컴포넌트
  - 드롭다운, 파라미터 입력, 실행
  - 5개 E2E 테스트 통과

✅ Task 2: Audit 대시보드
  - 필터, 테이블, 상세정보, 통계
  - 5개 E2E 테스트 통과

✅ Task 3: QueryResult 통합
  - ActionButton 통합
  - 3개 E2E 테스트 통과

✅ 전체 13개 E2E 테스트 통과
✅ UI/UX 가이드 준수
✅ 반응형 디자인 (모바일 포함)
```

---

## 🚀 실행 순서

1. **Task 1 구현** (ActionButton) → E2E 테스트 (5개)
2. **Task 2 구현** (AuditDashboard) → E2E 테스트 (5개)
3. **Task 3 수정** (QueryResult 통합) → E2E 테스트 (3개)

---

**예상 완료**: 2026-06-21  
**최종 검증**: 모든 E2E 테스트 통과 (13/13)  
**다음**: Claude/Antigravity와 통합

