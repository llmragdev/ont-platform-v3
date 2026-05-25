# Phase 4 Week 5: Bug Fix & Test Coverage
## Codex (Frontend) 수행 지시서

**기간**: 2026-06-24 ~ 2026-06-28 (4일)  
**할당**: 80% (주당 24-30시간)  
**목표**: 프론트엔드 테스트 커버리지 ↑, SPARQL/Write-back UI 검증, 엣지 케이스 처리

---

## 🔧 환경 설정 (필수 - 테스트 실행 전 완료)

### npm 환경 초기화

```bash
# Conda 환경 활성화
conda activate claud_fe

# 작업 디렉토리 이동
cd E:\ontology_edu\X_ont_std\ont_platform\v4\frontend

# 의존성 설치 (필수)
npm install

# 개발 서버 시작 (별도 터미널)
npm run dev

# 테스트 실행 (테스트 터미널)
npm test -- --coverage
```

### npm 환경 위치
- **경로**: `C:\Users\nkchoi2\anaconda3\envs\claud_fe`
- **활성화**: `conda activate claud_fe`
- **포트**: 3002 (프론트엔드 개발 서버)
- **테스트**: Jest + React Testing Library

### 자주 발생하는 문제 해결

| 문제 | 해결 방법 |
|------|---------|
| `npm: command not found` | `conda activate claud_fe` 재실행 후 시도 |
| 의존성 에러 | `npm install` 다시 실행 또는 `npm ci` 사용 |
| 포트 3002 사용 중 | `npm run dev -- --port 3003` 로 변경 |
| 테스트 타임아웃 | `npm test -- --testTimeout=10000` |
| 모듈 캐시 문제 | `rm -r node_modules && npm install` |

---

## Task 5-1: Component Test Coverage 향상 (목표: ≥90%)

**기간**: 06-24 ~ 06-25 (1.5일)

### 커버리지 분석 (현재: ~75%)

```bash
# 현재 커버리지 측정
npm run test -- --coverage

# 주요 미커버리지 영역
- components/SPARQLWorkbench.tsx: 70% → 90% 목표
- components/QueryBuilder.tsx: 68% → 90% 목표
- hooks/useSPARQLQuery.ts: 65% → 90% 목표
- components/WriteBackMonitor.tsx: 72% → 90% 목표
```

### 작업 항목

#### 1) SPARQLWorkbench 엣지 케이스
```typescript
// 테스트할 엣지 케이스
describe('SPARQLWorkbench', () => {
  it('renders with empty query', () => {
    const { getByText } = render(<SPARQLWorkbench initialQuery="" />);
    expect(getByText('Enter SPARQL query')).toBeInTheDocument();
  });

  it('handles very long queries (>100KB)', () => {
    const longQuery = 'SELECT * WHERE { ' + '?s ?p ?o . '.repeat(5000) + '}';
    const { container } = render(<SPARQLWorkbench initialQuery={longQuery} />);
    expect(container.querySelector('textarea')).toHaveValue(longQuery);
  });

  it('displays syntax error feedback on invalid SPARQL', async () => {
    const { getByText, getByRole } = render(<SPARQLWorkbench />);
    const queryInput = getByRole('textbox');
    
    fireEvent.change(queryInput, { target: { value: 'INVALID SPARQL QUERY' } });
    fireEvent.click(getByText('Execute'));
    
    await waitFor(() => {
      expect(getByText(/syntax error/i)).toBeInTheDocument();
    });
  });

  it('handles timeout gracefully (30+ seconds)', async () => {
    const { getByText, getByRole } = render(<SPARQLWorkbench />);
    jest.useFakeTimers();
    
    fireEvent.click(getByText('Execute'));
    jest.advanceTimersByTime(31000);
    
    await waitFor(() => {
      expect(getByText(/timeout/i)).toBeInTheDocument();
    });
  });

  it('exports results in multiple formats (JSON, CSV, XML)', async () => {
    const { getByText } = render(<SPARQLWorkbench />);
    
    fireEvent.click(getByText('Execute'));
    await waitFor(() => getByText('Export'));
    
    ['JSON', 'CSV', 'XML'].forEach(format => {
      fireEvent.click(getByText(`Export as ${format}`));
      expect(getByText(`Downloading as ${format}`)).toBeInTheDocument();
    });
  });
});
```

#### 2) QueryBuilder 복잡한 조건
```typescript
describe('QueryBuilder', () => {
  it('handles deep nesting (5+ levels)', () => {
    const deepQuery = {
      subject: '?s',
      patterns: [
        {
          predicate: 'rdf:type',
          object: 'schema:Person',
          filters: [
            {
              property: 'schema:name',
              operator: 'CONTAINS',
              value: 'John',
              and: [
                { property: 'schema:age', operator: '>', value: '18' }
              ]
            }
          ]
        }
      ]
    };
    
    const { container } = render(<QueryBuilder query={deepQuery} onChange={jest.fn()} />);
    expect(container.querySelectorAll('[data-level]')).toHaveLength(5);
  });

  it('validates duplicate patterns', () => {
    const onChange = jest.fn();
    const { getByText } = render(<QueryBuilder onChange={onChange} />);
    
    // 같은 패턴 2개 추가
    fireEvent.click(getByText('Add Pattern'));
    fireEvent.change(getByDisplayValue(''), { target: { value: '?predicate' } });
    fireEvent.click(getByText('Add Pattern'));
    fireEvent.change(getByDisplayValue(''), { target: { value: '?predicate' } });
    
    expect(getByText(/duplicate pattern/i)).toBeInTheDocument();
  });

  it('handles special characters in values', () => {
    const { getByRole } = render(<QueryBuilder onChange={jest.fn()} />);
    const input = getByRole('textbox', { name: /value/i });
    
    fireEvent.change(input, { target: { value: '"Value with \\"quotes\\" and \\n newlines"' } });
    expect(input).toHaveValue('"Value with \\"quotes\\" and \\n newlines"');
  });
});
```

#### 3) WriteBackMonitor DLQ 처리
```typescript
describe('WriteBackMonitor', () => {
  it('displays DLQ items separately', async () => {
    const mockData = {
      queues: [
        { id: '1', status: 'COMPLETED', retry_count: 0 },
        { id: '2', status: 'DLQ', retry_count: 5, dlq_reason: 'Max retries exceeded' }
      ]
    };
    
    const { getByText } = render(
      <WriteBackMonitor initialData={mockData} />
    );
    
    await waitFor(() => {
      expect(getByText('Dead Letter Queue (1)')).toBeInTheDocument();
      expect(getByText('Max retries exceeded')).toBeInTheDocument();
    });
  });

  it('allows replay of DLQ items', async () => {
    const mockReplay = jest.fn().mockResolvedValue({ success: true });
    const { getByText } = render(
      <WriteBackMonitor onReplay={mockReplay} />
    );
    
    fireEvent.click(getByText('Replay'));
    
    await waitFor(() => {
      expect(mockReplay).toHaveBeenCalled();
      expect(getByText(/replayed successfully/i)).toBeInTheDocument();
    });
  });

  it('handles bulk operations (100+ items)', () => {
    const largeData = {
      queues: Array.from({ length: 150 }, (_, i) => ({
        id: `${i}`,
        status: 'COMPLETED'
      }))
    };
    
    const { getByText, container } = render(
      <WriteBackMonitor initialData={largeData} />
    );
    
    // 페이지네이션 확인
    expect(getByText(/page 1 of 2/i)).toBeInTheDocument();
    expect(container.querySelectorAll('[data-item]')).toHaveLength(100);
  });
});
```

#### 4) useSPARQLQuery Hook 동시성
```typescript
describe('useSPARQLQuery', () => {
  it('cancels previous request when new query issued', async () => {
    const abortSpy = jest.spyOn(AbortController.prototype, 'abort');
    
    const { rerender } = renderHook(
      ({ query }) => useSPARQLQuery(query),
      { initialProps: { query: 'SELECT * WHERE { ?s ?p ?o . }' } }
    );
    
    rerender({ query: 'SELECT ?name WHERE { ?s schema:name ?name . }' });
    
    expect(abortSpy).toHaveBeenCalled();
  });

  it('handles rapid successive queries', async () => {
    const { result } = renderHook(() => useSPARQLQuery(''));
    
    await act(async () => {
      for (let i = 0; i < 10; i++) {
        result.current.executeQuery(`SELECT * WHERE { ?s ?p ?o . LIMIT ${i} }`);
      }
    });
    
    // 마지막 쿼리만 실행되어야 함
    expect(result.current.loading).toBe(true);
  });

  it('retries with exponential backoff on network error', async () => {
    const mockFetch = jest.fn()
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({ ok: true, json: () => ({ results: [] }) });
    
    global.fetch = mockFetch;
    
    const { result } = renderHook(() => useSPARQLQuery('SELECT * WHERE { ?s ?p ?o . }'));
    
    await waitFor(() => {
      expect(result.current.error).toBeNull();
    });
    
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });
});
```

### 테스트 목표
- [ ] SPARQLWorkbench: 90%+ 커버리지
- [ ] QueryBuilder: 90%+ 커버리지
- [ ] WriteBackMonitor: 90%+ 커버리지
- [ ] useSPARQLQuery Hook: 90%+ 커버리지
- [ ] 전체: ≥90% 커버리지 달성
- [ ] 0 ESLint 경고
- [ ] TypeScript strict mode 통과

---

## Task 5-2: UI/UX 엣지 케이스 처리 (20+)

**기간**: 06-25 ~ 06-27 (2일)

### 주요 엣지 케이스

#### 1) 응답성 & 레이아웃
```typescript
// 반응형 레이아웃 테스트
describe('SPARQLWorkbench Responsive', () => {
  it('stacks vertically on mobile (< 640px)', () => {
    global.innerWidth = 640;
    const { container } = render(<SPARQLWorkbench />);
    
    expect(container.querySelector('[data-layout]')).toHaveClass('flex-col');
  });

  it('shows side-by-side on tablet (640px ~ 1024px)', () => {
    global.innerWidth = 800;
    const { container } = render(<SPARQLWorkbench />);
    
    expect(container.querySelector('[data-layout]')).toHaveClass('flex-row');
  });

  it('collapses query panel on desktop when results large', () => {
    const largeResults = Array.from({ length: 1000 }, (_, i) => ({
      id: `result_${i}`,
      values: { s: `?s${i}`, p: `?p${i}`, o: `?o${i}` }
    }));
    
    const { getByText } = render(
      <SPARQLWorkbench results={largeResults} />
    );
    
    fireEvent.click(getByText('Collapse Query'));
    expect(getByText('Expand Query')).toBeInTheDocument();
  });
});
```

#### 2) 데이터 표시 극단값
```typescript
describe('Results Display Edge Cases', () => {
  it('handles NULL/empty values gracefully', () => {
    const results = [
      { s: 'http://example.org/e1', p: 'http://example.org/prop', o: null },
      { s: null, p: null, o: null },
      { s: '', p: '', o: '' }
    ];
    
    const { container } = render(<SPARQLResults data={results} />);
    expect(container.querySelectorAll('[data-empty-cell]')).toHaveLength(7);
  });

  it('truncates extremely long values (>500 chars)', () => {
    const longValue = 'x'.repeat(1000);
    const results = [{ s: longValue, p: 'prop', o: 'obj' }];
    
    const { container } = render(<SPARQLResults data={results} />);
    const cell = container.querySelector('[data-value]');
    
    expect(cell?.textContent?.length).toBeLessThan(520);
    expect(cell).toHaveAttribute('title', longValue);
  });

  it('renders special characters without breaking layout', () => {
    const specialChars = ['<>&"\'', 'مرحبا', '日本語', '🚀⚡️'];
    const results = specialChars.map((char, i) => ({
      s: char,
      p: `prop${i}`,
      o: `obj${i}`
    }));
    
    const { container } = render(<SPARQLResults data={results} />);
    expect(container).toBeInTheDocument();
  });
});
```

#### 3) 폼 검증 및 에러 메시지
```typescript
describe('Form Validation & Error Messages', () => {
  it('shows field-level errors for invalid SPARQL syntax', async () => {
    const { getByText, getByRole } = render(<QueryBuilder />);
    
    fireEvent.change(getByRole('textbox'), { 
      target: { value: 'SELECT * WHEREEE { ?s ?p ?o }' } 
    });
    
    await waitFor(() => {
      expect(getByText(/unexpected keyword "WHEREEE"/i)).toBeInTheDocument();
    });
  });

  it('handles concurrent validation errors', () => {
    const errors = {
      query: 'Invalid syntax',
      filters: ['Missing operator', 'Invalid value'],
      output: 'Unsupported format'
    };
    
    const { getByText } = render(<ErrorSummary errors={errors} />);
    
    expect(getByText('3 errors found')).toBeInTheDocument();
  });

  it('provides recovery suggestions for common mistakes', () => {
    const { getByText } = render(
      <ErrorMessage error="LIMIT must be integer" />
    );
    
    expect(getByText(/did you mean:/i)).toBeInTheDocument();
    expect(getByText('LIMIT 10')).toBeInTheDocument();
  });
});
```

#### 4) 상태 관리 & 메모리 누수
```typescript
describe('State Management Edge Cases', () => {
  it('cleans up event listeners on unmount', () => {
    const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');
    
    const { unmount } = render(<SPARQLWorkbench />);
    unmount();
    
    expect(removeEventListenerSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function));
  });

  it('prevents memory leaks with large datasets', () => {
    const { rerender, unmount } = render(
      <SPARQLResults data={Array.from({ length: 10000 }, (_, i) => ({ id: i }))} />
    );
    
    rerender(
      <SPARQLResults data={Array.from({ length: 10000 }, (_, i) => ({ id: i + 10000 }))} />
    );
    
    unmount();
    expect(performance.memory?.usedJSHeapSize).toBeLessThan(100 * 1024 * 1024);
  });

  it('handles rapid component mounting/unmounting', async () => {
    for (let i = 0; i < 50; i++) {
      const { unmount } = render(<SPARQLWorkbench />);
      unmount();
    }
    
    expect(() => render(<SPARQLWorkbench />)).not.toThrow();
  });
});
```

### 성공 기준
- [ ] 20+ 엣지 케이스 테스트
- [ ] 응답형 레이아웃 전체 테스트 (mobile/tablet/desktop)
- [ ] 데이터 극단값 처리 (NULL, 매우 긴 문자열, 특수문자)
- [ ] 메모리 누수 검증 완료

---

## Task 5-3: E2E 통합 테스트 & Regression Tests

**기간**: 06-27 ~ 06-28 (1.5일)

### E2E 시나리오 (10개)

```typescript
// E2E 테스트 (Playwright)
describe('SPARQL Workbench E2E', () => {
  // 시나리오 1: 완전한 쿼리 실행 흐름
  test('complete query execution flow', async ({ page }) => {
    await page.goto('http://localhost:3002/sparql-workbench');
    
    // 1. 쿼리 입력
    await page.fill('textarea[name="query"]', 
      'SELECT ?s ?p ?o WHERE { ?s ?p ?o . } LIMIT 10');
    
    // 2. 실행
    await page.click('button:has-text("Execute")');
    
    // 3. 결과 확인
    await page.waitForSelector('[data-results-table]');
    const rows = await page.locator('[data-results-row]').count();
    expect(rows).toBeGreaterThan(0);
  });

  // 시나리오 2: 배치 쿼리 처리
  test('batch query execution with mixed success/failure', async ({ page }) => {
    await page.goto('http://localhost:3002/sparql-workbench');
    
    await page.fill('textarea[name="query"]', 
      'SELECT * WHERE { ?s ?p ?o . }\n---\nINVALID SPARQL\n---\nSELECT ?s WHERE { ?s rdf:type rdfs:Class . }');
    
    await page.click('button:has-text("Execute Batch")');
    
    await page.waitForSelector('[data-batch-results]');
    expect(await page.textContent('[data-success-count]')).toContain('2');
    expect(await page.textContent('[data-failed-count]')).toContain('1');
  });

  // 시나리오 3: 대량 결과 내보내기
  test('export large result set as CSV', async ({ page }) => {
    await page.goto('http://localhost:3002/sparql-workbench');
    
    await page.fill('textarea[name="query"]', 
      'SELECT * WHERE { ?s ?p ?o . } LIMIT 1000');
    
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Export as CSV")');
    
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/results.*\.csv/);
  });
});

describe('WriteBack Monitor E2E', () => {
  // 시나리오 4: DLQ 항목 재시도
  test('replay DLQ item successfully', async ({ page }) => {
    await page.goto('http://localhost:3002/write-back-monitor');
    
    // DLQ 탭으로 이동
    await page.click('text=Dead Letter Queue');
    
    // 첫 번째 DLQ 항목 찾기
    const dlqItem = page.locator('[data-dlq-item]').first();
    const itemId = await dlqItem.getAttribute('data-id');
    
    // Replay 버튼 클릭
    await page.click(`[data-dlq-item][data-id="${itemId}"] button:has-text("Replay")`);
    
    // 성공 메시지 확인
    await page.waitForSelector('text=Replayed successfully');
  });

  // 시나리오 5: 대량 항목 모니터링
  test('handle 100+ queue items with pagination', async ({ page }) => {
    await page.goto('http://localhost:3002/write-back-monitor');
    
    // 페이지 1
    let items = await page.locator('[data-queue-item]').count();
    expect(items).toBeLessThanOrEqual(100);
    
    // 다음 페이지
    await page.click('button:has-text("Next Page")');
    await page.waitForLoadState('networkidle');
    
    items = await page.locator('[data-queue-item]').count();
    expect(items).toBeGreaterThan(0);
  });
});
```

### Regression Tests (8개)

```typescript
// Week 4 RDF API 호환성
test('regression: SPARQL API 응답 형식 호환성', async ({ page }) => {
  const response = await page.request.post('/api/sparql/query', {
    data: { query: 'SELECT * WHERE { ?s ?p ?o . } LIMIT 1' }
  });
  
  const data = await response.json();
  expect(data).toHaveProperty('source');
  expect(data).toHaveProperty('data');
  expect(data).toHaveProperty('execution_time_ms');
});

// Week 3.5 WriteBack API 호환성
test('regression: Write-back DLQ replay API 작동', async ({ page }) => {
  const response = await page.request.post('/api/writeback/replay/test-id');
  
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data).toHaveProperty('status');
});

// Week 2 프로젝트 관리 UI 호환성
test('regression: ActionButton 컴포넌트 프로젝트 액션 실행', async ({ page }) => {
  await page.goto('http://localhost:3002/projects');
  
  const projectRow = page.locator('[data-project-row]').first();
  const actionButton = projectRow.locator('button').first();
  
  await actionButton.click();
  await page.waitForSelector('[data-action-modal]');
});
```

---

## 🎯 성공 기준

- [x] Component 테스트 커버리지 ≥ 90%
- [x] 20+ UI 엣지 케이스 테스트
- [x] 10개 E2E 시나리오
- [x] 8개 회귀 테스트
- [x] 0 ESLint 경고
- [x] TypeScript strict 모드 통과
- [x] 전체 38+ 새 테스트

---

## 📊 테스트 실행

```bash
# 유닛 + 통합 테스트
npm run test

# 커버리지 리포트
npm run test -- --coverage

# ESLint
npm run lint

# E2E 테스트 (Playwright)
npm run test:e2e

# 전체 검증
npm run test:all
```

---

## ⏭️ 다음 주차 준비

- Week 6 성능 최적화 지표 정의
- 번들 크기 분석 도구 설정
- Core Web Vitals 모니터링 구성

---

## 🔗 관련 문서

- 지시서: `week_instructions/PHASE4/Week_5_BugFix/Codex.md`
- 테스트: `src/frontend/tests/phase4_week5_*.test.tsx`

---

**⚠️ 반드시 따르기**:

1. **저장 위치** (필수)
   - ✅ 정해진 위치: `task_logs/codex/YYYYMMDD_PHASE4_WEEK5_Codex_Complete.md`
   - 파일명 형식: `YYYYMMDD_HHMM_작업명.md`
   - 예: `20260628_1830_PHASE4_WEEK5_Codex_Complete.md`
   - ❌ 금지: `ont_platform/` 폴더에 저장하지 말 것

2. **템플릿 작성**:
   - "기간", "할당", "상태", "날짜" → 실제 작업 기록으로 채우기
   - "Task 5-1~5-3" 섹션 → 실제 완료 항목만 체크
   - "테스트 결과" 표 → 실제 테스트 통과 결과 입력
   - "커버리지" → 실제 npm run test 결과 입력

---

**상태**: Task 5-1~5-3 준비 완료  
**예상 완료**: 2026-06-28 (금요일 오후)  
**다음 주차**: Week 6 Performance Optimization

---

## 📋 보고서 저장 지시

**작업 완료 후 다음 경로에 보고서를 저장하세요:**

**저장 경로**: `task_logs/codex/YYYYMMDD_HHMM_PHASE4_WEEK5_Codex_Complete.md`

**예시**: `20260628_1830_PHASE4_WEEK5_Codex_Complete.md`

**완료 후**: Claude가 3개 보고서를 취합하여 통합 보고서를 작성합니다.
(`task_logs/consolidated/YYYYMMDD_HHMM_PHASE4_WEEK5_Consolidated_Report.md`)
