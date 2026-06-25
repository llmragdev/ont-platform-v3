# Phase 4 Week 3.5: Codex DLQ 대시보드 UI 지시서

**작업명**: WriteBackWorker DLQ(Dead Letter Queue) 관리자 대시보드 구현  
**시작**: 2026-05-25 오후 2시 (Day 1 14:00)  
**소요시간**: 1.5-2시간 (병렬 UI 개발)  
**완료 기준**: 3가지 Task + 2-3개 E2E 테스트 통과

---

## 🎯 작업 개요

Claude가 백엔드 코드를 수정하는 동안, Codex는 **관리자가 DLQ 상태의 실패 항목을 모니터링하고 재실행(Replay)할 수 있는 UI**를 구현합니다.

### 구현 범위
- ✅ DLQ 아이템 리스트 페이지 (조회, 필터링, 정렬)
- ✅ Replay 버튼 + 모달 (재실행 확인, API 연결)
- ✅ 상태 표시 (DLQ 이유, 실패 시간, 재시도 기록)
- ✅ E2E 테스트 (2-3개 시나리오)

---

## 📍 파일 위치 및 구조

```
ont_platform/v4/src/frontend/
├── components/
│   ├── WriteBack/
│   │   ├── DLQItemTable.tsx        ← Task 1: 리스트 컴포넌트
│   │   ├── ReplayButton.tsx        ← Task 2: Replay 버튼 + 모달
│   │   └── DLQDetailModal.tsx      ← 상세 정보 모달
│   └── ...
├── pages/
│   ├── writeback/
│   │   ├── dlq-dashboard.tsx       ← Task 1: 메인 페이지
│   │   └── index.tsx
│   └── ...
├── services/
│   ├── writebackApi.ts             ← API 호출 함수 (별도 존재)
│   └── ...
├── __tests__/
│   └── e2e/
│       ├── dlq-dashboard.spec.tsx  ← Task 3: E2E 테스트
│       └── replay-flow.spec.tsx
└── ...
```

---

## Task 1: DLQ 아이템 리스트 컴포넌트 (30분)

### 1-1) 메인 페이지 (`dlq-dashboard.tsx`)

**요구사항**:
- 페이지 제목: "Writeback DLQ 관리"
- 자동 새로고침: 5초마다
- 필터 옵션: 상태별, 날짜 범위, 에러 유형
- 테이블: DLQ 아이템 리스트

**코드 예시**:
```typescript
// pages/writeback/dlq-dashboard.tsx
import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { DLQItemTable } from '@/components/WriteBack/DLQItemTable';
import { ReplayButton } from '@/components/WriteBack/ReplayButton';
import { getWriteBackApi } from '@/services/writebackApi';

interface DLQItem {
  id: string;
  target_system: string;
  payload: Record<string, any>;
  dlq_reason: string;
  dlq_at: string;
  last_error_at: string;
  error_message: string;
  retry_count: number;
}

export default function DLQDashboard() {
  const [items, setItems] = useState<DLQItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState<DLQItem | null>(null);
  const [filterDate, setFilterDate] = useState<string | null>(null);
  
  // 자동 새로고침 (5초)
  useEffect(() => {
    const interval = setInterval(() => {
      fetchDLQItems();
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);
  
  // 초기 로드
  useEffect(() => {
    fetchDLQItems();
  }, [filterDate]);
  
  const fetchDLQItems = async () => {
    setLoading(true);
    try {
      const response = await getWriteBackApi().get('/dlq/items');
      setItems(response.data.items || []);
    } catch (error) {
      console.error('Failed to fetch DLQ items:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleReplay = async (itemId: string) => {
    try {
      await getWriteBackApi().post(`/replay/${itemId}`);
      // 성공 메시지 및 리스트 새로고침
      alert(`Item ${itemId} replayed successfully`);
      fetchDLQItems();
    } catch (error) {
      alert(`Failed to replay: ${error}`);
    }
  };
  
  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold mb-6">Writeback DLQ 관리</h1>
      
      {/* 필터 섹션 */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              날짜 범위
            </label>
            <input
              type="date"
              value={filterDate || ''}
              onChange={(e) => setFilterDate(e.target.value || null)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => setFilterDate(null)}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
            >
              필터 초기화
            </button>
          </div>
        </div>
      </div>
      
      {/* 통계 섹션 */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-red-600">{items.length}</div>
          <div className="text-sm text-gray-600">DLQ 아이템 (대기 중)</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-blue-600">
            {items.filter(i => i.retry_count >= 3).length}
          </div>
          <div className="text-sm text-gray-600">최대 재시도 도달</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-orange-600">
            {items.filter(i => i.dlq_at && (new Date().getTime() - new Date(i.dlq_at).getTime()) < 3600000).length}
          </div>
          <div className="text-sm text-gray-600">1시간 이내 발생</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">마지막 갱신</div>
          <div className="text-sm font-mono text-gray-700">
            {format(new Date(), 'HH:mm:ss')}
          </div>
        </div>
      </div>
      
      {/* 테이블 */}
      <div className="bg-white rounded-lg shadow">
        <DLQItemTable 
          items={items} 
          loading={loading}
          onReplay={handleReplay}
          onSelectItem={setSelectedItem}
        />
      </div>
      
      {/* 로딩 상태 */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center">
          <div className="bg-white rounded-lg p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-700">갱신 중...</p>
          </div>
        </div>
      )}
    </div>
  );
}
```

### 1-2) 리스트 테이블 컴포넌트 (`DLQItemTable.tsx`)

**요구사항**:
- 컬럼: ID, 시스템, 에러 사유, DLQ 시간, 재시도 횟수, 액션
- 정렬: DLQ 시간 역순 (최신부터)
- 행 클릭: 상세 정보 모달 표시
- 상태 배지: Retry_Count=3 이상 시 "⚠️ 최대 도달"

**코드 예시**:
```typescript
// components/WriteBack/DLQItemTable.tsx
import React from 'react';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

interface DLQItem {
  id: string;
  target_system: string;
  dlq_reason: string;
  dlq_at: string;
  retry_count: number;
  error_message: string;
}

interface Props {
  items: DLQItem[];
  loading: boolean;
  onReplay: (itemId: string) => void;
  onSelectItem: (item: DLQItem) => void;
}

export function DLQItemTable({ items, loading, onReplay, onSelectItem }: Props) {
  // 시간순 정렬 (최신부터)
  const sortedItems = [...items].sort(
    (a, b) => new Date(b.dlq_at).getTime() - new Date(a.dlq_at).getTime()
  );
  
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-100">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
              아이템 ID
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
              대상 시스템
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
              DLQ 사유
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
              DLQ 시간
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
              재시도
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
              액션
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {sortedItems.length === 0 ? (
            <tr>
              <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                DLQ 아이템이 없습니다.
              </td>
            </tr>
          ) : (
            sortedItems.map((item) => (
              <tr
                key={item.id}
                onClick={() => onSelectItem(item)}
                className="hover:bg-gray-50 cursor-pointer"
              >
                <td className="px-6 py-4 text-sm font-mono text-gray-900">
                  {item.id}
                </td>
                <td className="px-6 py-4 text-sm text-gray-700">
                  {item.target_system}
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  <div className="max-w-xs truncate" title={item.dlq_reason}>
                    {item.dlq_reason || item.error_message}
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-700">
                  {format(new Date(item.dlq_at), 'yyyy-MM-dd HH:mm:ss', { locale: ko })}
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{item.retry_count}</span>
                    {item.retry_count >= 3 && (
                      <span className="px-2 py-1 text-xs font-semibold text-orange-800 bg-orange-100 rounded-full">
                        ⚠️ 최대 도달
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 text-sm">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onReplay(item.id);
                    }}
                    className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                  >
                    재실행
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
```

---

## Task 2: Replay 버튼 및 확인 모달 (30분)

### 2-1) Replay 버튼 + 모달 (`ReplayButton.tsx`)

**요구사항**:
- 버튼 클릭 시 확인 모달 표시
- 모달에 아이템 ID, 에러 메시지, 마지막 실패 시간 표시
- "확인" 클릭 시 `/api/writeback/replay/{id}` POST 호출
- 로딩 상태 표시
- 성공/실패 메시지

**코드 예시**:
```typescript
// components/WriteBack/ReplayButton.tsx
import React, { useState } from 'react';
import { format } from 'date-fns';

interface DLQItem {
  id: string;
  error_message: string;
  last_error_at: string;
}

interface Props {
  item: DLQItem;
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

export function ReplayButton({ item, onSuccess, onError }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{
    status: 'pending' | 'success' | 'error';
    message?: string;
  }>({ status: 'pending' });
  
  const handleReplay = async () => {
    setIsLoading(true);
    setResult({ status: 'pending' });
    
    try {
      const response = await fetch(`/api/writeback/replay/${item.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setResult({
        status: 'success',
        message: `아이템 ${item.id}이(가) PENDING 상태로 복구되었습니다.`
      });
      
      if (onSuccess) onSuccess();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류';
      setResult({
        status: 'error',
        message: `재실행 실패: ${errorMessage}`
      });
      
      if (onError) onError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50"
        disabled={isLoading}
      >
        {isLoading ? '처리 중...' : '재실행'}
      </button>
      
      {/* 모달 */}
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            {/* 헤더 */}
            <div className="bg-gray-100 px-6 py-4 border-b">
              <h2 className="text-lg font-bold text-gray-900">
                아이템 재실행 확인
              </h2>
            </div>
            
            {/* 콘텐츠 */}
            <div className="px-6 py-4">
              {result.status === 'pending' && (
                <>
                  <div className="mb-4">
                    <p className="text-sm text-gray-600 font-medium">아이템 ID</p>
                    <p className="text-sm font-mono text-gray-900">{item.id}</p>
                  </div>
                  
                  <div className="mb-4">
                    <p className="text-sm text-gray-600 font-medium">마지막 오류</p>
                    <p className="text-sm text-gray-700">
                      {format(new Date(item.last_error_at), 'yyyy-MM-dd HH:mm:ss')}
                    </p>
                  </div>
                  
                  <div className="mb-6">
                    <p className="text-sm text-gray-600 font-medium">오류 메시지</p>
                    <p className="text-xs bg-gray-50 p-2 rounded text-gray-700 max-h-20 overflow-auto font-mono">
                      {item.error_message}
                    </p>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-6">
                    이 아이템을 PENDING 상태로 복구하시겠습니까?
                    <br />
                    <strong>재시도 횟수는 0으로 초기화됩니다.</strong>
                  </p>
                </>
              )}
              
              {result.status === 'success' && (
                <div className="text-center">
                  <div className="text-4xl text-green-600 mb-2">✓</div>
                  <p className="text-sm font-medium text-gray-900">
                    {result.message}
                  </p>
                </div>
              )}
              
              {result.status === 'error' && (
                <div className="text-center">
                  <div className="text-4xl text-red-600 mb-2">✕</div>
                  <p className="text-sm font-medium text-gray-900">
                    {result.message}
                  </p>
                </div>
              )}
            </div>
            
            {/* 푸터 */}
            <div className="bg-gray-50 px-6 py-4 border-t flex justify-end gap-3">
              <button
                onClick={() => setIsOpen(false)}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded hover:bg-gray-300 text-sm font-medium"
                disabled={isLoading}
              >
                {result.status === 'pending' ? '취소' : '닫기'}
              </button>
              
              {result.status === 'pending' && (
                <button
                  onClick={handleReplay}
                  className="px-4 py-2 text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
                  disabled={isLoading}
                >
                  {isLoading ? '처리 중...' : '확인'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
```

---

## Task 3: E2E 테스트 (30분)

### 3-1) DLQ 대시보드 E2E 테스트 (`dlq-dashboard.spec.tsx`)

**요구사항**:
- Playwright 기반 브라우저 자동화
- 시나리오 1: 페이지 로드 → DLQ 아이템 표시
- 시나리오 2: Replay 버튼 클릭 → 모달 표시 → 확인

**코드 예시**:
```typescript
// __tests__/e2e/dlq-dashboard.spec.tsx
import { test, expect } from '@playwright/test';

test.describe('DLQ Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // 테스트 DB에 DLQ 아이템 3개 생성
    await fetch('http://localhost:8002/api/writeback/test/setup-dlq-items', {
      method: 'POST',
      body: JSON.stringify({
        count: 3,
        target_system: 'SAP'
      })
    });
    
    await page.goto('http://localhost:3002/writeback/dlq-dashboard');
  });
  
  test('Scenario 1: 페이지 로드 및 DLQ 아이템 표시', async ({ page }) => {
    // 제목 확인
    await expect(page.locator('h1')).toContainText('Writeback DLQ 관리');
    
    // 통계 섹션 확인
    const dlqCount = page.locator('text=DLQ 아이템');
    await expect(dlqCount).toBeVisible();
    
    // 테이블 로드 대기
    await page.waitForLoadState('networkidle');
    
    // 테이블 행 확인
    const rows = page.locator('table tbody tr');
    await expect(rows).toHaveCount(3);
    
    // 각 행의 컬럼 확인
    const firstRow = rows.first();
    await expect(firstRow.locator('td').nth(0)).not.toBeEmpty(); // ID
    await expect(firstRow.locator('td').nth(1)).toContainText('SAP'); // 시스템
  });
  
  test('Scenario 2: Replay 버튼 클릭 및 확인 모달', async ({ page }) => {
    // 테이블 로드 대기
    await page.waitForLoadState('networkidle');
    
    // 첫 번째 행의 Replay 버튼 클릭
    const replayButton = page.locator('table tbody tr').first().locator('button:has-text("재실행")');
    await replayButton.click();
    
    // 모달 표시 확인
    const modal = page.locator('text=아이템 재실행 확인');
    await expect(modal).toBeVisible();
    
    // 모달 콘텐츠 확인
    await expect(page.locator('text=아이템 ID')).toBeVisible();
    await expect(page.locator('text=마지막 오류')).toBeVisible();
    await expect(page.locator('text=오류 메시지')).toBeVisible();
    
    // 확인 버튼 클릭
    const confirmButton = page.locator('button:has-text("확인")');
    await confirmButton.click();
    
    // 성공 메시지 표시 확인
    await page.waitForTimeout(1000);
    const successMessage = page.locator('text=복구되었습니다');
    await expect(successMessage).toBeVisible();
  });
  
  test('Scenario 3: 자동 새로고침 (5초마다)', async ({ page }) => {
    // 초기 아이템 수 기록
    await page.waitForLoadState('networkidle');
    let initialCount = (await page.locator('table tbody tr').count());
    
    // 새 아이템 추가 (서버 API 호출)
    await fetch('http://localhost:8002/api/writeback/test/add-dlq-item', {
      method: 'POST',
      body: JSON.stringify({
        target_system: 'SAP',
        error_message: 'New error'
      })
    });
    
    // 5초 이상 대기 (자동 새로고침 트리거)
    await page.waitForTimeout(6000);
    
    // 아이템 수 증가 확인
    let updatedCount = (await page.locator('table tbody tr').count());
    expect(updatedCount).toBe(initialCount + 1);
  });
});
```

### 3-2) Replay API 통합 테스트 (`replay-flow.spec.tsx`)

**요구사항**:
- DLQ 아이템 → Replay API 호출 → PENDING 상태 복구 검증
- 상태 변경 확인 (DLQ → PENDING)
- 재시도 횟수 초기화 (retry_count → 0)

**코드 예시**:
```typescript
// __tests__/e2e/replay-flow.spec.tsx
import { test, expect } from '@playwright/test';
import axios from 'axios';

test.describe('Replay Flow Integration', () => {
  let dlqItemId: string;
  
  test.beforeEach(async () => {
    // 테스트 DLQ 아이템 생성
    const response = await axios.post(
      'http://localhost:8002/api/writeback/test/create-dlq-item',
      {
        target_system: 'SAP',
        dlq_reason: 'Max retries exceeded',
        error_message: 'Timeout after 3 attempts',
        retry_count: 3
      }
    );
    dlqItemId = response.data.id;
  });
  
  test('DLQ 아이템이 PENDING으로 복구되는지 확인', async ({ page }) => {
    // 1. DLQ 대시보드에서 아이템 확인
    await page.goto('http://localhost:3002/writeback/dlq-dashboard');
    await page.waitForLoadState('networkidle');
    
    const itemRow = page.locator(`text=${dlqItemId}`).first().locator('..');
    await expect(itemRow).toContainText('Max retries exceeded');
    
    // 2. Replay 버튼 클릭
    const replayButton = itemRow.locator('button:has-text("재실행")');
    await replayButton.click();
    
    // 3. 모달 확인 후 확인 버튼 클릭
    const modal = page.locator('text=아이템 재실행 확인');
    await expect(modal).toBeVisible();
    await page.locator('button:has-text("확인")').click();
    
    // 4. 성공 메시지 확인
    const successMessage = page.locator('text=PENDING 상태로 복구');
    await expect(successMessage).toBeVisible();
    
    // 5. API 직접 호출로 상태 확인
    const itemResponse = await axios.get(
      `http://localhost:8002/api/writeback/item/${dlqItemId}`
    );
    expect(itemResponse.data.status).toBe('PENDING');
    expect(itemResponse.data.retry_count).toBe(0);
    expect(itemResponse.data.dlq_reason).toBeNull();
  });
});
```

---

## 📋 최종 체크리스트

구현 완료 후 확인:

- [ ] Task 1: DLQ 아이템 리스트 페이지
  - `dlq-dashboard.tsx` 생성됨
  - `DLQItemTable.tsx` 생성됨
  - 자동 새로고침 (5초) 작동 확인
  - 필터 기능 작동 확인
  - 통계 섹션 표시됨

- [ ] Task 2: Replay 버튼 및 모달
  - `ReplayButton.tsx` 생성됨
  - 모달 표시/숨김 작동 확인
  - API 호출 성공 시 성공 메시지 표시
  - API 호출 실패 시 에러 메시지 표시

- [ ] Task 3: E2E 테스트
  - `dlq-dashboard.spec.tsx` 생성됨
  - `replay-flow.spec.tsx` 생성됨
  - Playwright 테스트 3개 시나리오 모두 통과

---

## 🚀 최종 보고서 제출 형식

모든 Task 및 테스트 완료 후, 다음 형식으로 `task_logs/codex/` 폴더에 보고서 작성:

**파일명**: `20260525_HHMM_Week3.5_DLQDashboard_Complete.md`

**내용 구성**:
```markdown
# Week 3.5 DLQ 대시보드 UI 구현 완료 보고서

## 구현 요약
- Task 1: DLQ 아이템 리스트 페이지 ✅
- Task 2: Replay 버튼 및 모달 ✅
- Task 3: E2E 테스트 (3개 시나리오) ✅

## 생성된 파일
- components/WriteBack/DLQItemTable.tsx
- components/WriteBack/ReplayButton.tsx
- pages/writeback/dlq-dashboard.tsx
- __tests__/e2e/dlq-dashboard.spec.tsx
- __tests__/e2e/replay-flow.spec.tsx

## E2E 테스트 결과
- Scenario 1: 페이지 로드 및 DLQ 아이템 표시 ✅
- Scenario 2: Replay 버튼 클릭 및 모달 ✅
- Scenario 3: 자동 새로고침 확인 ✅

## 주요 기능
- 5초마다 자동 새로고침
- 필터 및 정렬 기능
- Replay API 통합
- 실시간 통계 표시

## 완료 일시
2026-05-25 오후 XX:XX
```

---

**예상 완료**: 2026-05-25 오후 5시경  
**준비**: Day 1 14:00에 Claude 코드 수정과 병렬 UI 개발 진행
