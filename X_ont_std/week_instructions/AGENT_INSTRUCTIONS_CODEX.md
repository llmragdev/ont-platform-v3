# ?윝 Codex: Frontend UI ?먯씠?꾪듃 吏?쒖꽌

**???*: Codex (Frontend UI & Workflow ?대떦)  
**?쒖옉**: 2026-05-27 (Phase 2.5 ?꾨즺 ??  
**醫낅즺**: 2026-07-21  
**湲곌컙**: 4二?(蹂묐젹 ?묒뾽 + 理쒖쥌 ?듯빀)

---

## ?렞 Phase 3 誘몄뀡

?⑦넧濡쒖? 湲곕컲 ?섏궗寃곗젙 ?쒖뒪?쒖쓽 **UI/UX** 援ы쁽

```
Backend: Query Result + Action ?뺣낫
             ??Codex:   ActionButton + Audit ??쒕낫??             ??User:    ?≪뀡 ?ㅽ뻾 ??寃곌낵 ?뺤씤 ??湲곕줉 議고쉶
```

---

## ?뱥 ?꾩껜 ?곗텧臾?(4二?

| Week | Task | ?뚯씪 ?꾩튂 | ?뚯뒪??|
|------|------|---------|--------|
| 1 | ActionButton 而댄룷?뚰듃 以鍮?| `src/components/ActionButton.tsx` | - |
| 2 | ActionButton 援ы쁽 + ?뚯뒪??| `src/components/ActionButton.tsx` | E2E 5媛?|
| 3 | Audit ??쒕낫??援ы쁽 | `src/pages/audit-log.tsx` | E2E 5媛?|
| 4 | 理쒖쥌 ?듯빀 + 諛섏쓳???붿옄??| ?꾩껜 Frontend | E2E 15媛?|

---

## ?뱟 二쇱감蹂??곸꽭 ?묒뾽

### **Week 1: UI 而댄룷?뚰듃 ?ㅺ퀎 & 以鍮?(05-27 ~ 05-31)**

#### ?대떦 ?묒뾽
- ActionButton 而댄룷?뚰듃 **?ㅺ퀎** (援ы쁽 ?꾩쭅 X)
- Props ?뺤쓽 諛?API 怨꾩빟 ?뺤씤
- ?ㅽ???媛?대뱶 以鍮?- Claude??ActionDefinition 紐⑤뜽 紐⑤땲?곕쭅

#### ?곗텧臾?```
src/components/ActionButton.tsx
?쒋? Props interface ?뺤쓽
?쒋? ?곹깭 愿由??ㅺ퀎 (loading, disabled, error)
?쒋? ?ㅽ???湲곕낯 ?
?붴? 二쇱꽍: Claude 紐⑤뜽 ?湲?以?
src/components/ActionResult.tsx  (?덈줈 ?앹꽦)
?쒋? ?≪뀡 ?ㅽ뻾 寃곌낵 ?쒖떆
?쒋? Success/Error ?곹깭 ?쒖떆
?붴? Toast/Modal UI

src/hooks/useAction.ts  (?덈줈 ?앹꽦)
?쒋? useAction(actionId, targetEntityId) hook
?쒋? executeAction ?⑥닔
?붴? permission check
```

#### ?묒뾽 ?댁슜
1. **ActionButton Props ?뺤쓽**
```typescript
// src/components/ActionButton.tsx

interface ActionDefinition {
  id: string
  name: string  // "?뱀씤", "嫄곗젅" ??  description: string
  executor_role: string  // "CFO", "PM"
  enabled_condition?: string
}

interface ActionButtonProps {
  action: ActionDefinition
  targetEntityId: string
  onSuccess?: (result: any) => void
  onError?: (error: Error) => void
  disabled?: boolean
}

export function ActionButton({
  action,
  targetEntityId,
  onSuccess,
  onError,
  disabled
}: ActionButtonProps) {
  // 而댄룷?뚰듃 ?留??묒꽦 (濡쒖쭅? Week 2)
  return (
    <button disabled={disabled}>
      {action.name}
    </button>
  )
}
```

2. **ActionResult 而댄룷?뚰듃 ?ㅺ퀎**
- ?깃났/?ㅽ뙣 ?곹깭 ?쒖떆
- ?ㅽ뻾 ?쒓컙 ?쒖떆
- ?ъ떆??踰꾪듉 (?ㅽ뙣 ??

3. **useAction Hook ?ㅺ퀎**
- `executeAction(actionId, context)` ?⑥닔 signature ?뺤씤
- permission check 濡쒖쭅 ?ㅺ퀎
- error handling ?ㅺ퀎

4. **?ㅽ???媛?대뱶**
- 踰꾪듉 ?됱긽 (?≪뀡 ??낅퀎)
- 濡쒕뵫 ?곹깭 ?좊땲硫붿씠??- ?먮윭 硫붿떆吏 ?ㅽ???
#### ??Week 1 Success Criteria
- [ ] ActionButton Props ?뺤쓽 ?꾨즺
- [ ] ActionResult 而댄룷?뚰듃 ?ㅺ퀎 ?꾨즺
- [ ] useAction Hook ?ㅺ퀎 ?꾨즺
- [ ] ?ㅽ???媛?대뱶 臾몄꽌??- [ ] Claude??API ?붾뱶?ъ씤???뺤씤 (?湲?以?

#### ?뱷 Task Log ?묒꽦
```
task_logs/claude/{YYYYMMDD}_Codex_Phase3_Week1_Design.md
- 寃곌낵: ActionButton Props ?뺤쓽 ?꾨즺
- API ?湲??ы빆: Claude??POST /api/actions/{action_id}/execute ?뺤씤 ?꾩슂
- 釉붾줈而? ?놁쓬
```

---

### **Week 2: ActionButton 援ы쁽 & E2E ?뚯뒪??(06-03 ~ 06-07)**

#### ?대떦 ?묒뾽
- ActionButton ?꾩껜 援ы쁽
- useAction Hook 援ы쁽
- 沅뚰븳 ?뺤씤 濡쒖쭅
- E2E ?뚯뒪???묒꽦 (5媛??쒕굹由ъ삤)

#### ?곗텧臾?```
src/components/ActionButton.tsx  (?꾩꽦)
?쒋? State management (loading, disabled, error)
?쒋? onClick handler
?쒋? Permission check
?붴? Error handling

src/hooks/useAction.ts  (?꾩꽦)
?쒋? executeAction ?⑥닔
?쒋? permission check
?쒋? retry logic
?붴? error formatting

e2e/action.spec.ts  (?덈줈 ?앹꽦)
?쒋? Test 1: ?≪뀡 ?대┃ ???ㅽ뻾
?쒋? Test 2: 沅뚰븳 ?놁쓣 ??disabled
?쒋? Test 3: ?깃났 ??onSuccess 肄쒕갚
?쒋? Test 4: ?ㅽ뙣 ???먮윭 ?쒖떆
?붴? Test 5: 濡쒕뵫 ?곹깭 ?쒖떆
```

#### ?묒뾽 ?댁슜
1. **ActionButton 援ы쁽**
```typescript
// src/components/ActionButton.tsx

import { useState, useEffect } from 'react'
import { useAction } from '@/hooks/useAction'

export function ActionButton({
  action,
  targetEntityId,
  onSuccess,
  onError,
  disabled
}: ActionButtonProps) {
  const [loading, setLoading] = useState(false)
  const [isDisabled, setIsDisabled] = useState(disabled ?? false)
  const { executeAction, checkPermission } = useAction()
  
  // 沅뚰븳 ?뺤씤
  useEffect(() => {
    checkPermission(action.id).then(allowed => {
      setIsDisabled(!allowed)
    })
  }, [action.id])
  
  const handleClick = async () => {
    setLoading(true)
    try {
      const result = await executeAction(action.id, {
        target_entity_id: targetEntityId
      })
      onSuccess?.(result)
    } catch (error) {
      onError?.(error as Error)
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <button
      onClick={handleClick}
      disabled={isDisabled || loading}
      className="action-button"
    >
      {loading ? '?ㅽ뻾 以?..' : action.name}
    </button>
  )
}
```

2. **useAction Hook 援ы쁽**
```typescript
// src/hooks/useAction.ts

export function useAction() {
  const executeAction = async (actionId: string, context: any) => {
    // 1. 沅뚰븳 ?뺤씤
    const { allowed, reason } = await checkPermission(actionId)
    if (!allowed) {
      throw new Error(`沅뚰븳 ?놁쓬: ${reason}`)
    }
    
    // 2. ?≪뀡 ?ㅽ뻾
    const response = await fetch(
      `/api/actions/${actionId}/execute`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(context)
      }
    )
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail)
    }
    
    return await response.json()
  }
  
  const checkPermission = async (actionId: string) => {
    const response = await fetch(
      `/api/actions/${actionId}/permission-check`,
      { method: 'GET' }
    )
    return await response.json()
  }
  
  return { executeAction, checkPermission }
}
```

3. **E2E ?뚯뒪??(5媛??쒕굹由ъ삤)**
```typescript
// e2e/action.spec.ts

describe('ActionButton', () => {
  test('?≪뀡 ?대┃ ???ㅽ뻾', async ({ page }) => {
    await page.goto('/project/123')
    await page.click('button:has-text("?뱀씤")')
    await page.waitForSelector('text=?ㅽ뻾 以?..')
    await page.waitForSelector('text=?깃났')
  })
  
  test('沅뚰븳 ?놁쓣 ??disabled', async ({ page }) => {
    // 沅뚰븳 ?녿뒗 ?ъ슜?먮줈 濡쒓렇??    await page.goto('/project/123')
    const button = page.locator('button:has-text("CFO ?뱀씤")')
    await expect(button).toBeDisabled()
  })
  
  test('?깃났 ??onSuccess 肄쒕갚', async ({ page }) => {
    // ...
  })
  
  test('?ㅽ뙣 ???먮윭 ?쒖떆', async ({ page }) => {
    // ...
  })
  
  test('濡쒕뵫 ?곹깭 ?쒖떆', async ({ page }) => {
    // ...
  })
})
```

#### ??Week 2 Success Criteria
- [ ] ActionButton 援ы쁽 ?꾨즺 (紐⑤뱺 湲곕뒫)
- [ ] useAction Hook 援ы쁽 ?꾨즺
- [ ] E2E ?뚯뒪??5/5 ?듦낵
- [ ] API 怨꾩빟 ?쇱튂 ?뺤씤 (Claude?)
- [ ] 沅뚰븳 湲곕컲 UI ?묐룞 ?뺤씤

#### ?뱷 Task Log ?묒꽦
```
task_logs/claude/{YYYYMMDD}_Codex_Phase3_Week2_Implementation.md
- 寃곌낵: ActionButton + useAction Hook ?꾩꽦
- ?뚯뒪?? E2E 5/5 ?듦낵
- API 寃利? /api/actions/{action_id}/execute ?뺤씤 ?꾨즺
- 釉붾줈而? ?놁쓬
```

---

### **Week 3: Audit ??쒕낫??援ы쁽 (06-10 ~ 06-14)**

#### ?대떦 ?묒뾽
- Audit 濡쒓렇 ??쒕낫??援ы쁽
- ?꾪꽣留?湲곕뒫 (?≪뀡/?ъ슜???좎쭨)
- ?깅뒫 理쒖쟻??(媛???ㅽ겕濡ㅻ쭅)
- E2E ?뚯뒪??(5媛??쒕굹由ъ삤)

#### ?곗텧臾?```
src/pages/audit-log.tsx  (?덈줈 ?앹꽦)
?쒋? Audit 濡쒓렇 議고쉶
?쒋? FilterBar 而댄룷?뚰듃
?쒋? LogRow 而댄룷?뚰듃
?쒋? VirtualScroll (???濡쒓렇 理쒖쟻??
?붴? CSV ?ㅼ슫濡쒕뱶 湲곕뒫

e2e/audit-log.spec.ts  (?덈줈 ?앹꽦)
?쒋? Test 1: 濡쒓렇 議고쉶
?쒋? Test 2: ?≪뀡蹂??꾪꽣留??쒋? Test 3: ?좎쭨 踰붿쐞 ?좏깮
?쒋? Test 4: CSV ?ㅼ슫濡쒕뱶
?붴? Test 5: 1000媛?濡쒓렇 ?뚮뜑留?(?깅뒫)
```

#### ?묒뾽 ?댁슜
1. **Audit ??쒕낫??湲곕낯 援ъ“**
```typescript
// src/pages/audit-log.tsx

import { useState, useEffect } from 'react'
import VirtualScroll from '@/components/VirtualScroll'

interface AuditLog {
  id: string
  action_id: string
  action_name: string
  user_id: string
  executed_at: string
  status: 'SUCCESS' | 'FAILED'
  old_state?: any
  new_state?: any
}

export function AuditLogDashboard() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [filter, setFilter] = useState({
    action: 'ALL',
    user: 'ALL',
    status: 'ALL',
    dateRange: [7]  // 理쒓렐 7??  })
  const [loading, setLoading] = useState(false)
  
  // 濡쒓렇 議고쉶
  useEffect(() => {
    fetchLogs(filter)
  }, [filter])
  
  const fetchLogs = async (filter: any) => {
    setLoading(true)
    const params = new URLSearchParams({
      action: filter.action,
      user: filter.user,
      status: filter.status,
      days: filter.dateRange[0].toString()
    })
    
    const response = await fetch(`/api/audit-logs?${params}`)
    const data = await response.json()
    setLogs(data.logs)
    setLoading(false)
  }
  
  const exportCSV = () => {
    const csv = logs
      .map(log => `${log.id},${log.action_name},${log.user_id},${log.status}`)
      .join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit-logs-${new Date().toISOString()}.csv`
    a.click()
  }
  
  return (
    <div className="audit-dashboard">
      <h1>Audit Log</h1>
      
      <FilterBar
        actions={['ALL', '?뱀씤', '嫄곗젅', '湲고븳蹂寃?, '寃곗젣?쒖옉', '?꾨즺']}
        filter={filter}
        onChange={setFilter}
      />
      
      {loading ? (
        <div>濡쒕뵫 以?..</div>
      ) : (
        <div>
          <button onClick={exportCSV}>CSV ?ㅼ슫濡쒕뱶</button>
          <VirtualScroll
            items={logs}
            height={600}
            itemHeight={40}
            renderItem={(log) => (
              <LogRow key={log.id} log={log} />
            )}
          />
        </div>
      )}
    </div>
  )
}

function LogRow({ log }: { log: AuditLog }) {
  const statusColor = log.status === 'SUCCESS' ? 'green' : 'red'
  
  return (
    <div className="log-row" style={{ borderLeft: `4px solid ${statusColor}` }}>
      <span className="action">{log.action_name}</span>
      <span className="user">{log.user_id}</span>
      <span className="time">{new Date(log.executed_at).toLocaleString()}</span>
      <span className="status">{log.status}</span>
    </div>
  )
}
```

2. **FilterBar 而댄룷?뚰듃**
- ?≪뀡 ?꾪꽣 ?쒕∼?ㅼ슫
- ?ъ슜???꾪꽣 ?낅젰
- ?좎쭨 踰붿쐞 ?좏깮湲?- ?곹깭 ?꾪꽣 (SUCCESS/FAILED)

3. **?깅뒫 理쒖쟻??*
- 媛???ㅽ겕濡ㅻ쭅 (1000媛?濡쒓렇??鍮좊Ⅴ寃?
- ?꾪꽣 debouncing
- 臾댄븳 ?ㅽ겕濡?(??留롮? 濡쒓렇 濡쒕뱶)

#### ??Week 3 Success Criteria
- [ ] Audit ??쒕낫??援ы쁽 ?꾨즺
- [ ] ?꾪꽣留?湲곕뒫 紐⑤몢 ?묐룞
- [ ] E2E ?뚯뒪??5/5 ?듦낵
- [ ] 1000媛?濡쒓렇 100ms ???뚮뜑留?(?깅뒫)
- [ ] CSV ?ㅼ슫濡쒕뱶 湲곕뒫 ?뺤씤

#### ?뱷 Task Log ?묒꽦
```
task_logs/claude/{YYYYMMDD}_Codex_Phase3_Week3_AuditDashboard.md
- 寃곌낵: Audit ??쒕낫???꾩꽦
- ?깅뒫: 1000媛?濡쒓렇 95ms ???뚮뜑留???- ?뚯뒪?? E2E 5/5 ?듦낵
- 釉붾줈而? ?놁쓬
```

---

### **Week 4: 理쒖쥌 ?듯빀 & 諛섏쓳???붿옄??(06-17 ~ 06-21)**

#### ?대떦 ?묒뾽
- ?꾩껜 Frontend ?듯빀
- E2E 理쒖쥌 ?뚯뒪??(15媛??쒕굹由ъ삤)
- 諛섏쓳???붿옄??(紐⑤컮??
- Dark mode 援ы쁽
- ?묎렐??(WCAG 以??

#### ?곗텧臾?```
src/components/  (湲곗〈 + 理쒖쟻??
?쒋? ActionButton.tsx  (?꾩꽦)
?쒋? ActionResult.tsx  (?꾩꽦)
?쒋? AuditLog.tsx      (?꾩꽦)
?붴? (湲고? 而댄룷?뚰듃 理쒖쟻??

styles/  (?덈줈 ?앹꽦)
?쒋? dark-mode.css  (Dark mode)
?붴? responsive.css  (諛섏쓳???붿옄??

e2e/final.spec.ts  (?덈줈 ?앹꽦)
?쒋? Test 1-5: ActionButton (Week 2 ?ы솗??
?쒋? Test 6-10: Audit Dashboard (Week 3 ?ы솗??
?쒋? Test 11-13: 紐⑤컮??諛섏쓳???쒋? Test 14: Dark mode
?붴? Test 15: ?묎렐??(WCAG)
```

#### ?묒뾽 ?댁슜
1. **諛섏쓳???붿옄??(紐⑤컮??**
- 紐⑤컮???붾㈃?먯꽌??ActionButton ?묐룞
- Audit ??쒕낫?쒕? 紐⑤컮??移쒗솕?곸쑝濡?- ?곗튂 ?대깽??泥섎━

2. **Dark mode 援ы쁽**
```typescript
// src/context/ThemeContext.tsx

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light')
  
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      <div className={`theme-${theme}`}>
        {children}
      </div>
    </ThemeContext.Provider>
  )
}

// styles/dark-mode.css
.theme-dark {
  background-color: #1a1a1a;
  color: #fff;
}

.theme-dark .action-button {
  background-color: #333;
  color: #fff;
}
```

3. **?묎렐??(WCAG)**
- 踰꾪듉??aria-label 異붽?
- ?됱긽 ?鍮?媛쒖꽑
- ?ㅻ낫???ㅻ퉬寃뚯씠??吏??- ?ㅽ겕由?由щ뜑 ?뚯뒪??
4. **E2E 理쒖쥌 ?뚯뒪??(15媛?**
```typescript
// e2e/final.spec.ts

describe('Full Stack Integration', () => {
  test('01: ?≪뀡 ?대┃ ???ㅽ뻾', async ({ page }) => {
    // Week 2 ?ы솗??  })
  
  // ... 4-5媛???  
  test('06: Audit ??쒕낫??濡쒕뱶', async ({ page }) => {
    // Week 3 ?ы솗??  })
  
  // ... 4-5媛???  
  test('11: 紐⑤컮??ActionButton', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/project/123')
    await expect(page.locator('button:has-text("?뱀씤")')).toBeVisible()
  })
  
  test('12: 紐⑤컮??Audit Dashboard', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/audit-log')
    // ?꾪꽣媛 stack?섏뼱????  })
  
  test('13: ?곗튂 ?대깽??, async ({ page }) => {
    // Tap event simulation
  })
  
  test('14: Dark mode ?좉?', async ({ page }) => {
    await page.click('button:has-text("Dark Mode")')
    await expect(page).toHaveCSS('background-color', 'rgb(26, 26, 26)')
  })
  
  test('15: ?묎렐??(WCAG)', async ({ page }) => {
    // axe accessibility testing
  })
})
```

#### ??Week 4 Success Criteria
- [ ] E2E 理쒖쥌 ?뚯뒪??15/15 ?듦낵
- [ ] 紐⑤컮???꾨꼍?섍쾶 ?묐룞
- [ ] Dark mode 援ы쁽 ?꾨즺
- [ ] ?묎렐??(WCAG) 以??- [ ] Production 以鍮??꾨즺

#### ?뱷 Task Log ?묒꽦
```
task_logs/claude/{YYYYMMDD}_Codex_Phase3_Week4_Final.md
- 寃곌낵: Frontend 理쒖쥌 ?꾩꽦
- ?뚯뒪?? E2E 15/15 ?듦낵
- ?깅뒫: 紐⑤컮??<1s ?묐떟
- 釉붾줈而? ?놁쓬
- ?ㅼ쓬: Phase 4 以鍮?```

---

## ?봽 ?뚯씪 援ъ“ & ?꾩튂

```
ont_platform/v3/src/frontend/
?쒋?? src/
??  ?쒋?? components/
??  ??  ?쒋?? ActionButton.tsx          ???듭떖 (Week 1-2)
??  ??  ?쒋?? ActionResult.tsx          ???덈줈 (Week 1-2)
??  ??  ?붴?? (湲곗〈 而댄룷?뚰듃)
??  ?쒋?? pages/
??  ??  ?붴?? audit-log.tsx             ???덈줈 (Week 3)
??  ?쒋?? hooks/
??  ??  ?붴?? useAction.ts              ???덈줈 (Week 1-2)
??  ?쒋?? context/
??  ??  ?붴?? ThemeContext.tsx          ???덈줈 (Week 4)
??  ?붴?? styles/
??      ?쒋?? dark-mode.css             ???덈줈 (Week 4)
??      ?붴?? responsive.css            ???덈줈 (Week 4)
?붴?? e2e/
    ?쒋?? action.spec.ts               ???덈줈 (Week 2)
    ?쒋?? audit-log.spec.ts            ???덈줈 (Week 3)
    ?붴?? final.spec.ts                ???덈줈 (Week 4)
```

---

## ?뱷 留ㅼ씪 ????
### 留ㅼ씪 ?꾩묠 (10:00)
1. Claude??Task log ?뺤씤 (?덈줈??API ?덈뒗吏)
2. ?댁젣 Task log ?뺣━
3. ?ㅻ뒛 紐⑺몴 ?뺤씤

### 留ㅼ씪 ???(17:00)
1. Task log ?묒꽦
2. ?뚯뒪???ㅽ뻾 諛?寃곌낵 湲곕줉
3. 釉붾줈而??덉쑝硫?湲곕줉
4. PHASE2_5_Project_Status_20260524.md ?낅뜲?댄듃 (?먯떊???됰쭔)

---

## ?슚 二쇱쓽?ы빆

### API ?섏〈??- **?湲?*: Claude??`/api/actions/{action_id}/execute` ?붾뱶?ъ씤??- **?湲?*: Backend??`/api/audit-logs` ?붾뱶?ъ씤??- **?뺤씤**: ?쇱＜?쇱뿉 ??踰?(湲덉슂??5??

### ?뚯씪 異⑸룎 諛⑹?
- Codex??`src/components/`, `src/pages/`, `src/hooks/` ?대떦
- Claude??`app/` (backend) ?대떦
- Antigravity??`tests/load/` ?대떦

### Task Log 洹쒖튃
- 留ㅼ씪 ????묒꽦 (?묒뾽 ?꾨즺 ??
- ?뚯씪紐? `{YYYYMMDD}_{TIME}_Codex_Phase3_Week{N}_Day{M}_TaskName.md`
- ?꾩닔 ?ы븿: Summary, Test Results, Blockers

---

## ??泥댄겕由ъ뒪??
**?쒖옉 ??(2026-05-27)**
- [ ] 媛쒕컻 ?섍꼍 以鍮?(Node.js, npm ?뺤씤)
- [ ] Frontend ?꾨줈?앺듃 鍮뚮뱶 ?뺤씤
- [ ] E2E ?뚯뒪???섍꼍 以鍮?(Playwright)
- [ ] PHASE2_5_Project_Status_20260524.md 理쒖떊 ?곹깭 ?뺤씤

**留ㅼ＜ 湲덉슂??5??*
- [ ] 二쇨컙 Task log 紐⑤몢 ?꾩꽦
- [ ] ?뚯뒪???듦낵???뺤씤
- [ ] 釉붾줈而??닿껐 ?щ? ?뺤씤
- [ ] PHASE2_5_Project_Status_20260524.md ?낅뜲?댄듃

**Phase ?꾨즺 ??(2026-07-21)**
- [ ] E2E ?뚯뒪??15/15 ?듦낵
- [ ] 紐⑤컮???꾨꼍 ?묐룞
- [ ] Dark mode + ?묎렐???꾩꽦
- [ ] 理쒖쥌 由ы룷???묒꽦

---

## ?뮠 臾몄쓽

- **Claude ?**: Backend/API 愿??吏덈Ц
- **Antigravity ?**: ?깅뒫/遺??愿??吏덈Ц
- **Claude Code**: 理쒖쥌 ?듯빀 諛??곹깭 ?뚯씪 愿由?
---

**以鍮??꾨즺! ??**

**吏덈Ц**: ??吏?쒖꽌媛 紐낇솗?쒓??? 遺遺꾩쟻???섏젙???꾩슂?섎㈃ ?뚮젮二쇱꽭??

