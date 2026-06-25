# Phase 3: ?섏궗寃곗젙 ?≪뀡 ?쒖뒪??3-Agent 蹂묐젹 媛쒕컻 吏?쒖꽌

**?묒꽦**: 2026-05-24  
**?쒖옉**: 2026-06-24 (Phase 2.5 ?꾨즺 ??  
**湲곌컙**: 4二?(06-24 ~ 07-21)  
**?**: Claude + Codex + Antigravity  
**?곹깭**: ?? 以鍮??꾨즺

---

## ?뱥 Phase 3 誘몄뀡

### ?듭떖 紐⑺몴
?⑦넧濡쒖? 湲곕컲 ?곗씠??議고쉶 ??**?섏궗寃곗젙 ???≪뀡 ??寃곌낵 湲곕줉** ???꾩쟾???ъ씠??援ы쁽

### 鍮꾩쫰?덉뒪 媛移?- 議곗꽑/?쒖“ ?곗뾽???먮룞?붾맂 ?섏궗寃곗젙 吏??- ?≪뀡 ?ㅽ뻾 異붿쟻 諛?媛먯떆
- 洹쒖젙 以??(Audit Log)
- SAP/ERP ?쒖뒪?쒓낵???곕룞

### 湲곗닠 紐⑺몴
```
Query Result ??ActionDefinition ??Permission Check ??Execute ??WriteBack ??Audit Log
```

---

## ?뫁 3-Agent ??븷 遺꾨떞

### ?뵶 Claude: ?섏궗寃곗젙 ?붿쭊 + Action ?ㅽ뻾

**二쇱슂 梨낆엫**:
- ActionDefinition 紐⑤뜽 ?ㅺ퀎 諛?援ы쁽
- 6媛??듭떖 ?≪뀡 濡쒖쭅 援ы쁽
- 沅뚰븳 寃利??쒖뒪??(議곌굔遺, 湲덉븸蹂?
- Write-Back ?뚯빱 (?몃? ?쒖뒪???숆린??
- Audit Log 湲곕줉

**?곗텧臾?*:
- `app/models/action.py` (ActionDefinition ORM)
- `app/services/action_executor.py` (?≪뀡 ?ㅽ뻾 ?붿쭊)
- `app/services/permission_checker.py` (沅뚰븳 寃利?
- `app/workers/writeback_worker.py` (SAP ?숆린??
- `app/db/models.py` (Audit Log 紐⑤뜽)

**?깃났 湲곗?**:
- Unit tests: 50+ ?뚯뒪??(90%+ ?듦낵)
- Integration tests: 40+ ?뚯뒪??- Write-back ?깃났瑜? 95%+
- Audit coverage: 100%

---

### ?윝 Codex: ?≪뀡 UI + Audit ??쒕낫??
**二쇱슂 梨낆엫**:
- QueryResult??ActionButton 而댄룷?뚰듃 異붽?
- ?≪뀡 ?ㅽ뻾 寃곌낵 ?뚮┝
- Audit 濡쒓렇 ??쒕낫??- 沅뚰븳 湲곕컲 UI (?ъ슜?먮뒗 ?ㅽ뻾 媛?ν븳 ?≪뀡留?蹂댁엫)

**?곗텧臾?*:
- `src/components/ActionButton.tsx`
- `src/components/ActionResult.tsx`
- `src/pages/audit-log.tsx`
- `src/hooks/useAction.ts`
- E2E ?뚯뒪?? 15+ ?쒕굹由ъ삤

**?깃났 湲곗?**:
- ActionButton ?대┃ ??1珥????묐떟
- Audit ??쒕낫?? 1000媛?濡쒓렇 100ms ???뚮뜑留?- E2E ?뚯뒪?? 15/15 ?듦낵

---

### ?윟 Antigravity: ?깅뒫 + Write-back 理쒖쟻??
**二쇱슂 梨낆엫**:
- ?≪뀡 ?ㅽ뻾 ?깅뒫 踰ㅼ튂留덊겕 (遺???뚯뒪??
- Write-back ?뚯빱 ?깅뒫 理쒖쟻??- SAP API ??꾩븘??泥섎━
- ????≪뀡 泥섎━ (?ъ떆??濡쒖쭅)

**?곗텧臾?*:
- `tests/load/action_load_test.py`
- `tests/perf/writeback_performance.py`
- `docs/PERFORMANCE_BASELINE.md`
- 理쒖쟻??由ы룷??
**?깃났 湲곗?**:
- ?≪뀡 ?ㅽ뻾: <500ms (p99)
- Write-back: <1s (p99)
- ?숈떆 1000 ?ъ슜???뚯뒪???듦낵
- ?ъ떆???깃났瑜? 99%+

---

## ?뱟 4二??곸꽭 ?쇱젙

### Week 1: ActionDefinition + 6媛??≪뀡 援ы쁽 (06-24 ~ 06-28)

#### Claude: ActionDefinition 紐⑤뜽 ?ㅺ퀎 & ?≪뀡 援ы쁽

**Day 1-2 (06-24 ~ 06-25)**:
```python
# app/models/action.py

class ActionDefinition:
    id: str
    name: str  # "?뱀씤", "嫄곗젅" ??    description: str
    enabled_condition: str  # SPARQL/SQL WHERE 議곌굔
    executor_role: str  # "CFO", "PM" ??    
    # 沅뚰븳 泥댄겕
    permission_rules: Dict[str, Any]  # {
        "min_amount": 10000,  # 1留????댁긽留?        "requires_approval": True,
        "approval_count": 2  # 2紐??뱀씤 ?꾩슂
    }
    
    # ?ㅽ뻾 寃곌낵 泥섎━
    on_success: Dict[str, Any]
    on_failure: Dict[str, Any]

class ActionExecution:
    id: str
    action_id: str
    target_entity_id: str
    status: "PENDING" | "APPROVED" | "EXECUTED" | "FAILED"
    requested_by: str
    executed_at: datetime
    result: Dict[str, Any]
```

**二쇱슂 援ы쁽**:
- ORM 紐⑤뜽 + DB 留덉씠洹몃젅?댁뀡
- 30媛??⑥쐞 ?뚯뒪??
**Codex ?湲?*: 紐⑤뜽 ?ㅽ궎留??뺤씤 ??UI 以鍮?
**Antigravity ?湲?*: ?깅뒫 湲곗????섎┰

---

**Day 2-3 (06-25 ~ 06-26)**:

6媛??듭떖 ?≪뀡 援ы쁽:

```python
# app/services/action_executor.py

class ApproveProject(ActionBase):
    """?꾨줈?앺듃 ?뱀씤"""
    def execute(self, project_id: str, approver: str) -> ActionResult:
        # 1. 沅뚰븳 泥댄겕
        # 2. ?꾨줈?앺듃 ?곹깭 蹂寃?(PENDING ??APPROVED)
        # 3. Audit log 湲곕줉
        # 4. Write-back queue??異붽? (SAP)
        pass

class RejectProject(ActionBase):
    """?꾨줈?앺듃 嫄곗젅"""
    def execute(self, project_id: str, reason: str) -> ActionResult:
        pass

class ChangeDeadline(ActionBase):
    """湲고븳 蹂寃?""
    def execute(self, project_id: str, new_deadline: date) -> ActionResult:
        pass

class RequestMoreInfo(ActionBase):
    """異붽? ?뺣낫 ?붿껌"""
    def execute(self, project_id: str, info_needed: str) -> ActionResult:
        pass

class StartPayment(ActionBase):
    """寃곗젣 ?쒖옉 (湲덉븸 湲곕컲 沅뚰븳)"""
    def execute(self, project_id: str, amount: float) -> ActionResult:
        # 湲덉븸??100留뚯썝 ?댁긽?대㈃ CFO ?뱀씤 ?꾩슂
        # 1000留뚯썝 ?댁긽?대㈃ CEO ?뱀씤 ?꾩슂
        pass

class CompleteProject(ActionBase):
    """?꾨줈?앺듃 ?꾨즺"""
    def execute(self, project_id: str) -> ActionResult:
        pass
```

**媛??≪뀡留덈떎**:
- Execute 濡쒖쭅 (5-10以?
- 5-10媛??⑥쐞 ?뚯뒪??- ?먮윭 泥섎━

---

**Day 4 (06-27)**:
- ?꾩껜 ?듯빀 ?뚯뒪??(30媛??뚯뒪??紐⑤몢 ?ㅽ뻾)
- 踰꾧렇 ?섏젙
- Codex/Antigravity? ?숆린??
**Day 5 (06-28)**:
- Code review 諛?理쒖쟻??- Week 1 ?꾨즺 由ы룷???묒꽦

#### Codex: UI 以鍮?(Day 1-2留?

**Day 1-2 (06-24 ~ 06-25)**:
- ActionButton 而댄룷?뚰듃 ? ?묒꽦
- Props ?뺤쓽 (action, onClick, disabled ??
- ?ㅽ???湲곕낯 ?ㅼ젙
- Claude???≪뀡 紐⑤뜽 紐⑤땲?곕쭅

**Day 3-5**: ?湲?(Claude ?≪뀡 援ы쁽 ?꾨즺源뚯?)

#### Antigravity: ?깅뒫 湲곗???(Day 1-2留?

**Day 1-2 (06-24 ~ 06-25)**:
- 遺???뚯뒪???꾨젅?꾩썙???ㅼ젙
- ?깅뒫 硫뷀듃由??뺤쓽
  - ?≪뀡 ?ㅽ뻾 ?쒓컙 (p50, p95, p99)
  - Audit log ?곌린 ?띾룄
  - DB 荑쇰━ ?쒓컙
- 踰좎씠?ㅻ씪???섏쭛

**Day 3-5**: ?湲?
---

**??Week 1 Success Criteria**:
- Claude: 30+ ?뚯뒪???듦낵, 6媛??≪뀡 紐⑤몢 ?ㅽ뻾 媛??- Codex: ActionButton 而댄룷?뚰듃 以鍮??꾨즺
- Antigravity: ?깅뒫 湲곗????섎┰

---

### Week 2: 沅뚰븳 寃利?+ API ?듯빀 (07-01 ~ 07-05)

#### Claude: 沅뚰븳 寃利??쒖뒪??+ API ?붾뱶?ъ씤??
**Day 1-2 (07-01 ~ 07-02)**:

```python
# app/services/permission_checker.py

class PermissionChecker:
    def check_action(
        self,
        user_id: str,
        action_id: str,
        context: Dict[str, Any]  # {"amount": 1500000, ...}
    ) -> Tuple[bool, str]:  # (allowed, reason)
        """
        ?≪뀡 ?ㅽ뻾 沅뚰븳 ?뺤씤
        
        洹쒖튃:
        1. ?ъ슜????븷 (Role) ?뺤씤
        2. 湲덉븸 湲곕컲 ?뱀씤 ?꾩슂 ?щ? ?뺤씤
        3. ?꾩닔 ?뱀씤?????뺤씤
        """
        
        # ?덉떆
        if amount > 10_000_000 and user_role != "CEO":
            return False, "CEO ?뱀씤 ?꾩슂"
        
        return True, "OK"
```

**Day 3-4 (07-03 ~ 07-04)**:

```python
# app/api/actions.py

@router.post("/actions/{action_id}/execute")
async def execute_action(
    action_id: str,
    context: Dict[str, Any],
    user: User = Depends(get_current_user)
):
    """?≪뀡 ?ㅽ뻾 ?붾뱶?ъ씤??""
    # 1. 沅뚰븳 ?뺤씤
    allowed, reason = permission_checker.check_action(
        user.id, action_id, context
    )
    if not allowed:
        raise HTTPException(403, reason)
    
    # 2. ?≪뀡 ?ㅽ뻾
    result = action_executor.execute(action_id, context)
    
    # 3. 寃곌낵 諛섑솚
    return {"status": "success", "data": result}
```

**API ?붾뱶?ъ씤??* (3媛?:
- `POST /api/actions/{action_id}/execute` - ?≪뀡 ?ㅽ뻾
- `GET /api/actions` - ?ъ슜 媛?ν븳 ?≪뀡 紐⑸줉 (沅뚰븳 湲곕컲)
- `GET /api/actions/{action_id}/preview` - ?ㅽ뻾 誘몃━蹂닿린

**Day 5 (07-05)**:
- API 臾몄꽌 (Swagger/OpenAPI) ?먮룞 ?앹꽦
- 15+ ?듯빀 ?뚯뒪??
**???깃났 湲곗?**:
- API ?붾뱶?ъ씤??3媛?紐⑤몢 ?묐룞
- ?듯빀 ?뚯뒪??15/15 ?듦낵
- Swagger 臾몄꽌 ?먮룞 ?앹꽦

#### Codex: ActionButton 援ы쁽

**Day 1-3 (07-01 ~ 07-03)**:

```tsx
// src/components/ActionButton.tsx

interface ActionButtonProps {
  action: ActionDefinition
  targetEntityId: string
  onSuccess?: (result: ActionResult) => void
  onError?: (error: Error) => void
}

export function ActionButton({
  action,
  targetEntityId,
  onSuccess,
  onError
}: ActionButtonProps) {
  const [loading, setLoading] = useState(false)
  const [disabled, setDisabled] = useState(false)
  
  // 沅뚰븳 ?뺤씤
  useEffect(() => {
    checkPermission(action.id).then(allowed => {
      setDisabled(!allowed)
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
    <button onClick={handleClick} disabled={disabled || loading}>
      {loading ? "?ㅽ뻾 以?.." : action.name}
    </button>
  )
}
```

**Day 4-5 (07-04 ~ 07-05)**:
- ?≪뀡 寃곌낵 ?뚮┝ (toast/modal)
- E2E ?뚯뒪??5媛?
**???깃났 湲곗?**:
- ActionButton ?대┃ ??1珥????묐떟
- 沅뚰븳 ?녿뒗 踰꾪듉? disabled ?쒖떆
- E2E 5/5 ?듦낵

#### Antigravity: API ?깅뒫 ?뚯뒪??
**Day 1-5 (07-01 ~ 07-05)**:

```python
# tests/load/action_api_load_test.py

class ActionAPILoadTest:
    def test_execute_action_performance(self):
        """?≪뀡 ?ㅽ뻾 API ?깅뒫"""
        # 100紐??숈떆 ?ㅽ뻾
        # 紐⑺몴: ?됯퇏 <300ms, p99 <500ms
        pass
    
    def test_permission_check_performance(self):
        """沅뚰븳 ?뺤씤 ?깅뒫"""
        # 1000媛?洹쒖튃 ?숈떆 ?뺤씤
        # 紐⑺몴: <50ms
        pass
```

**???깃났 湲곗?**:
- ?≪뀡 ?ㅽ뻾 API: <500ms (p99)
- 沅뚰븳 ?뺤씤: <50ms

---

**??Week 2 Success Criteria**:
- Claude: 3媛?API ?붾뱶?ъ씤?? 15+ ?듯빀 ?뚯뒪??- Codex: ActionButton UI, E2E 5媛??쒕굹由ъ삤
- Antigravity: API ?깅뒫 踰ㅼ튂留덊겕 ?꾨즺

---

### Week 3: Changelog + Write-back Worker (07-08 ~ 07-12)

#### Claude: Audit Log + Write-Back ?뚯빱

**Day 1-2 (07-08 ~ 07-09)**:

```python
# app/db/models.py

class AuditLog:
    id: int
    entity_id: str
    action_id: str
    user_id: str
    old_state: JSON  # 蹂寃????곹깭
    new_state: JSON  # 蹂寃????곹깭
    executed_at: datetime
    status: "SUCCESS" | "FAILED"
    error_message: str = None

# app/models/writeback.py

class WriteBackQueue:
    id: str
    action_execution_id: str
    target_system: str  # "SAP", "ERP", "JIRA"
    payload: JSON
    status: "PENDING" | "SENT" | "CONFIRMED" | "FAILED"
    retry_count: int
    created_at: datetime
    sent_at: datetime = None
```

**Day 3-4 (07-10 ~ 07-11)**:

```python
# app/workers/writeback_worker.py

class WriteBackWorker:
    async def process_queue(self):
        """Write-back ??泥섎━"""
        while True:
            pending = db.query(WriteBackQueue).filter(
                status="PENDING"
            ).limit(100)
            
            for item in pending:
                try:
                    if item.target_system == "SAP":
                        await self.send_to_sap(item)
                    elif item.target_system == "ERP":
                        await self.send_to_erp(item)
                    
                    item.status = "SENT"
                    db.commit()
                except Exception as e:
                    if item.retry_count < 3:
                        item.retry_count += 1
                    else:
                        item.status = "FAILED"
                        item.error_message = str(e)
                    db.commit()
            
            await asyncio.sleep(5)  # 5珥덈쭏??泥댄겕
    
    async def send_to_sap(self, item: WriteBackQueue):
        """SAP API ?몄텧"""
        response = await sap_client.post(
            "/api/actions",
            json=item.payload,
            timeout=5
        )
        item.status = "CONFIRMED"
```

**Day 5 (07-12)**:
- 40媛??듯빀 ?뚯뒪??(Audit log ?ы븿)
- ?ъ떆??濡쒖쭅 ?뚯뒪??
**???깃났 湲곗?**:
- Audit log 100% 湲곕줉
- Write-back ?깃났瑜?95%+
- ?듯빀 ?뚯뒪??40/40 ?듦낵

#### Codex: Audit ??쒕낫??
**Day 1-5 (07-08 ~ 07-12)**:

```tsx
// src/pages/audit-log.tsx

export function AuditLogDashboard() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [filter, setFilter] = useState({
    action: "ALL",
    user: "ALL",
    status: "ALL",
    dateRange: [7]  // 理쒓렐 7??  })
  
  // 1000媛?濡쒓렇??鍮좊Ⅴ寃??뚮뜑留?  // 媛???ㅽ겕濡ㅻ쭅 ?ъ슜
  
  return (
    <div>
      <FilterBar onChange={setFilter} />
      <VirtualScroll
        items={logs}
        renderItem={(log) => <LogRow log={log} />}
      />
    </div>
  )
}
```

**湲곕뒫**:
- ?≪뀡蹂??꾪꽣留?- ?ъ슜?먮퀎 ?꾪꽣留?- ?좎쭨 踰붿쐞 ?좏깮
- ?곹깭蹂??됱긽 援щ텇 (SUCCESS/FAILED)
- CSV ?ㅼ슫濡쒕뱶

**???깃났 湲곗?**:
- 1000媛?濡쒓렇 100ms ???뚮뜑留?- ?꾪꽣留??ㅼ떆媛??묐룞
- E2E 5媛??쒕굹由ъ삤

#### Antigravity: Write-back ?깅뒫 理쒖쟻??
**Day 1-5 (07-08 ~ 07-12)**:

```python
# tests/perf/writeback_performance.py

class WriteBackPerformanceTest:
    def test_writeback_throughput(self):
        """Write-back 泥섎━??""
        # 1000媛???ぉ ?숈떆 泥섎━
        # 紐⑺몴: <1s (p99)
        pass
    
    def test_sap_api_timeout_handling(self):
        """SAP API ??꾩븘??泥섎━"""
        # SAP媛 10珥?嫄몃젮??graceful?섍쾶 ?ъ떆??        pass
    
    def test_database_write_performance(self):
        """DB ?곌린 ?깅뒫"""
        # 10K audit log/min 泥섎━
        # 紐⑺몴: <100ms per batch
        pass
```

**???깃났 湲곗?**:
- Write-back 泥섎━?? 100+ items/sec
- API ??꾩븘??泥섎━: ?ъ떆???깃났瑜?99%
- DB ?곌린: <100ms per 100 logs

---

**??Week 3 Success Criteria**:
- Claude: Audit log + Write-back worker ?꾩꽦, 40+ ?듯빀 ?뚯뒪??- Codex: Audit ??쒕낫?? ?꾪꽣留?+ ?깅뒫 ?꾩꽦
- Antigravity: Write-back ?깅뒫 理쒖쟻???꾨즺

---

### Week 4: Frontend ?듯빀 + 理쒖쥌 ?뚯뒪??(07-15 ~ 07-21)

#### Claude: 理쒖쥌 ?듯빀 ?뚯뒪??
**Day 1-3 (07-15 ~ 07-17)**:
- 50媛??듯빀 ?뚯뒪??(紐⑤뱺 feature ?ы븿)
- E2E ?쒕굹由ъ삤: 荑쇰━ ???≪뀡 ??Write-back ??Audit 湲곕줉
- ?깅뒫 ?쒕떇

**Day 4-5 (07-18 ~ 07-21)**:
- Production 以鍮?- Documentation
- Performance tuning

**???깃났 湲곗?**:
- ?듯빀 ?뚯뒪??50/50 ?듦낵
- 紐⑤뱺 ?깅뒫 紐⑺몴 ?ъ꽦
- 0 security issues

#### Codex: E2E ?뚯뒪??+ Polish

**Day 1-3 (07-15 ~ 07-17)**:
- E2E ?뚯뒪??15媛??쒕굹由ъ삤
  1. ?≪뀡 ?ㅽ뻾 ?깃났
  2. 沅뚰븳 遺議깆쑝濡??ㅽ뻾 ?ㅽ뙣
  3. ?≪뀡 寃곌낵 ?뺤씤
  4. Audit log 議고쉶
  5. CSV ?ㅼ슫濡쒕뱶
  ... (10媛???

**Day 4-5 (07-18 ~ 07-21)**:
- 諛섏쓳???붿옄??(紐⑤컮??
- Dark mode
- ?묎렐??(WCAG)

**???깃났 湲곗?**:
- E2E 15/15 ?듦낵
- 紐⑤컮???꾨꼍?섍쾶 ?묐룞
- Dark mode ?꾩꽦

#### Antigravity: 理쒖쥌 踰ㅼ튂留덊겕

**Day 1-5 (07-15 ~ 07-21)**:
- 100K ?숈떆 荑쇰━ + ?≪뀡
- 理쒖쥌 ?깅뒫 由ы룷??- Production readiness check

**???깃났 湲곗?**:
- 100K QPS 泥섎━ 媛??- 99.9% uptime
- 紐⑤뱺 SLA ?ъ꽦

---

## ?렞 Phase 3 ?꾩껜 Success Criteria

| ??ぉ | Target | Owner |
|------|--------|-------|
| Unit tests | 50+ ?듦낵 | Claude |
| Integration tests | 40+ ?듦낵 | Claude |
| E2E tests | 15+ ?듦낵 | Codex |
| Code coverage | 85%+ | Claude |
| ?≪뀡 ?ㅽ뻾 ?깅뒫 | <500ms (p99) | Antigravity |
| Write-back ?깃났瑜?| 95%+ | Claude+Antigravity |
| Audit coverage | 100% | Claude |
| UI 諛섏쓳??| <1s | Codex |
| Production readiness | 100% | All |

---

## ?뮲 媛숈? PC ?묒뾽 諛⑹떇

**???꾨줈?앺듃??3紐낆씠 媛숈? PC?먯꽌 ?묒뾽?⑸땲??**

```
蹂닿???援ъ“:
E:\ontology_edu\X_ont_std\
?쒋?? ont_platform\v3\
??  ?붴?? src\backend\, src\frontend\  ??紐⑤몢媛 ?숈떆???묎렐
?쒋?? task_logs\claude\
??  ?쒋?? YYYYMMDD_HHMM_Claude_Week1_Day1.md
??  ?쒋?? YYYYMMDD_HHMM_Codex_Week1_Day1.md
??  ?붴?? YYYYMMDD_HHMM_Antigravity_Week1_Day1.md
?붴?? PHASE2_5_Project_Status_20260524.md  ??以묒븰 吏묒쨷???곹깭 ?뚯씪
```

**?묒뾽 諛⑹떇**:
- ?뱚 **?뚯씪 怨듭쑀**: 媛숈? ?대뜑 ???먮룞 怨듭쑀 (Git X)
- ?뱥 **?곹깭 異붿쟻**: PHASE2_5_Project_Status_20260524.md ?댁슜
- ?뱷 **?묒뾽 湲곕줉**: Task log (?쇱씪 ?묒꽦)
- ?좑툘 **?뚯씪 異⑸룎 諛⑹?**: 媛?????ㅻⅨ ?대뜑/?뚯씪?먯꽌 ?묒뾽
  - Claude: `app/services/action_executor.py`
  - Codex: `src/components/ActionButton.tsx`
  - Antigravity: `tests/load/`

**PHASE2_5_Project_Status_20260524.md 愿由?*:
- ?숈떆 ?몄쭛 湲덉? (?뚯씪 ??뼱?곌린 ?꾪뿕)
- 李⑤??濡??낅뜲?댄듃: Claude ??Codex ??Antigravity
- 媛?????먯떊???됰쭔 ?섏젙

---

## ?뱥 ?쒖옉 ??泥댄겕由ъ뒪??
**Claude**:
- [ ] Phase 2.5 ?꾨즺 諛?紐⑤뱺 ?뚯뒪???듦낵
- [ ] SPARQL?뭆QL 踰덉뿭湲??덉젙??- [ ] ActionDefinition ?ㅽ궎留??ㅺ퀎 ?꾨즺
- [ ] 媛쒕컻 ?섍꼍 以鍮?
**Codex**:
- [ ] Phase 2.5 Frontend ?꾨즺
- [ ] QueryResult 而댄룷?뚰듃 ?덉젙??- [ ] ActionButton 而댄룷?뚰듃 ?ㅺ퀎 ?꾨즺

**Antigravity**:
- [ ] Phase 2.5 ?깅뒫 踰ㅼ튂留덊겕 ?꾨즺
- [ ] 遺???뚯뒪???꾨젅?꾩썙??以鍮?- [ ] SAP API 紐?Mock) 援ы쁽

---

## ?뵕 愿??臾몄꽌

- **?ㅺ퀎**: `PHASE3_ACTION_DEFINITION.md` (6媛??≪뀡 ?곸꽭 ?뺤쓽)
- **?곹깭 湲곌퀎**: `PHASE3_STATE_MACHINE.md` (?≪뀡 ?곹깭 ?꾩씠)
- **援ы쁽 怨꾪쉷**: `PHASE3_IMPLEMENTATION_PLAN.md` (?곸꽭 ?쇱젙)

---

## ?뮠 ?묒뾽 洹쒖튃 (媛숈? PC 理쒖쟻??

**李멸퀬**: 媛숈? PC?먯꽌 ?묒뾽?섎?濡?Git commit ???**Task Log + ?곹깭 ?뚯씪**留??ъ슜?⑸땲??

### 留ㅼ씪
1. ?묒뾽 吏꾪뻾 (媛숈? ?대뜑?먯꽌 ?먮룞 怨듭쑀)
2. 臾몄젣 諛쒖깮 ??Task log??湲곕줉 ????먯뿉寃??뚮┝

### Task ?꾨즺???뚮쭏??1. **Task log ?묒꽦**: `task_logs/claude/YYYYMMDD_HHMM_Phase3_Week[N]_Day[M]_TaskName.md`
   ```
   - 臾댁뾿???덈뒗媛?
   - ?뚯뒪??寃곌낵
   - ?댁뒋/釉붾줈而?(?덉쑝硫?
   ```

2. **PHASE2_5_Project_Status_20260524.md ?낅뜲?댄듃** (李⑤??濡?
   - Status ?댁뿉 ??DONE + ?좎쭨 ?낅젰
   - **二쇱쓽**: ?숈떆 ?몄쭛 ?쇳븯湲?(媛?????쒖꽌?濡?

### 湲덉슂??5??(二쇨컙 泥댄겕)
1. 洹?二쇱쓽 紐⑤뱺 Task log ?꾩꽦?섏뿀?붿? ?뺤씤
2. PHASE2_5_Project_Status_20260524.md媛 理쒖떊 ?곹깭?몄? ?뺤씤
3. ?ㅼ쓬 二?以鍮??곹깭 ?뺤씤

### Week ?꾨즺 ??1. **理쒖쥌 由ы룷???묒꽦**: `task_logs/claude/YYYYMMDD_HHMM_Phase3_Week[N]_Complete.md`
   ```markdown
   # Phase 3 Week [N] ?꾨즺 蹂닿퀬??   
   ## Summary
   - Task N-1: ???꾨즺
   - Task N-2: ???꾨즺
   
   ## ?뚯뒪??寃곌낵
   - Unit tests: N/N passing
   - Integration tests: N/N passing
   
   ## ?ㅼ쓬 二?以鍮??곹빆
   - [泥댄겕由ъ뒪??
   ```

2. PHASE2_5_Project_Status_20260524.md?먯꽌 Week ?뱀뀡 理쒖쥌 ?뺤씤

---

## ?? ?쒖옉 ?좏샇

**Phase 3 ?쒖옉 議곌굔**:
- ??Phase 2.5 紐⑤뱺 ?묒뾽 ?꾨즺 (2026-06-21)
- ??3媛?? 紐⑤몢 以鍮??꾨즺
- ????吏?쒖꽌 由щ럭 ?꾨즺

**?쒖옉 ?쇱떆**: 2026-06-24 09:00 (?붿슂???꾩묠)  
**理쒖쥌 ?꾨즺**: 2026-07-21 17:00 (湲덉슂?????

---

**Questions?** ??吏?쒖꽌???댁븘?덈뒗 臾몄꽌?낅땲?? 媛?Week媛 ?쒖옉?섎㈃ `PHASE3_WEEKLY_DETAILS.md`?????먯꽭??Task媛 ?낅뜲?댄듃?⑸땲??

以鍮??꾨즺! ??

