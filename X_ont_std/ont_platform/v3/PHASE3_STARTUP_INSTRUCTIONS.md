# Phase 3: 의사결정 액션 시스템 3-Agent 병렬 개발 지시서

**작성**: 2026-05-24  
**시작**: 2026-06-24 (Phase 2.5 완료 후)  
**기간**: 4주 (06-24 ~ 07-21)  
**팀**: Claude + Codex + Antigravity  
**상태**: 🚀 준비 완료

---

## 📋 Phase 3 미션

### 핵심 목표
온톨로지 기반 데이터 조회 → **의사결정 → 액션 → 결과 기록** 의 완전한 사이클 구현

### 비즈니스 가치
- 조선/제조 산업의 자동화된 의사결정 지원
- 액션 실행 추적 및 감시
- 규정 준수 (Audit Log)
- SAP/ERP 시스템과의 연동

### 기술 목표
```
Query Result → ActionDefinition → Permission Check → Execute → WriteBack → Audit Log
```

---

## 👥 3-Agent 역할 분담

### 🔴 Claude: 의사결정 엔진 + Action 실행

**주요 책임**:
- ActionDefinition 모델 설계 및 구현
- 6개 핵심 액션 로직 구현
- 권한 검증 시스템 (조건부, 금액별)
- Write-Back 워커 (외부 시스템 동기화)
- Audit Log 기록

**산출물**:
- `app/models/action.py` (ActionDefinition ORM)
- `app/services/action_executor.py` (액션 실행 엔진)
- `app/services/permission_checker.py` (권한 검증)
- `app/workers/writeback_worker.py` (SAP 동기화)
- `app/db/models.py` (Audit Log 모델)

**성공 기준**:
- Unit tests: 50+ 테스트 (90%+ 통과)
- Integration tests: 40+ 테스트
- Write-back 성공률: 95%+
- Audit coverage: 100%

---

### 🟠 Codex: 액션 UI + Audit 대시보드

**주요 책임**:
- QueryResult에 ActionButton 컴포넌트 추가
- 액션 실행 결과 알림
- Audit 로그 대시보드
- 권한 기반 UI (사용자는 실행 가능한 액션만 보임)

**산출물**:
- `src/components/ActionButton.tsx`
- `src/components/ActionResult.tsx`
- `src/pages/audit-log.tsx`
- `src/hooks/useAction.ts`
- E2E 테스트: 15+ 시나리오

**성공 기준**:
- ActionButton 클릭 → 1초 내 응답
- Audit 대시보드: 1000개 로그 100ms 내 렌더링
- E2E 테스트: 15/15 통과

---

### 🟢 Antigravity: 성능 + Write-back 최적화

**주요 책임**:
- 액션 실행 성능 벤치마크 (부하 테스트)
- Write-back 워커 성능 최적화
- SAP API 타임아웃 처리
- 대량 액션 처리 (재시도 로직)

**산출물**:
- `tests/load/action_load_test.py`
- `tests/perf/writeback_performance.py`
- `docs/PERFORMANCE_BASELINE.md`
- 최적화 리포트

**성공 기준**:
- 액션 실행: <500ms (p99)
- Write-back: <1s (p99)
- 동시 1000 사용자 테스트 통과
- 재시도 성공률: 99%+

---

## 📅 4주 상세 일정

### Week 1: ActionDefinition + 6개 액션 구현 (06-24 ~ 06-28)

#### Claude: ActionDefinition 모델 설계 & 액션 구현

**Day 1-2 (06-24 ~ 06-25)**:
```python
# app/models/action.py

class ActionDefinition:
    id: str
    name: str  # "승인", "거절" 등
    description: str
    enabled_condition: str  # SPARQL/SQL WHERE 조건
    executor_role: str  # "CFO", "PM" 등
    
    # 권한 체크
    permission_rules: Dict[str, Any]  # {
        "min_amount": 10000,  # 1만 원 이상만
        "requires_approval": True,
        "approval_count": 2  # 2명 승인 필요
    }
    
    # 실행 결과 처리
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

**주요 구현**:
- ORM 모델 + DB 마이그레이션
- 30개 단위 테스트

**Codex 대기**: 모델 스키마 확인 후 UI 준비

**Antigravity 대기**: 성능 기준선 수립

---

**Day 2-3 (06-25 ~ 06-26)**:

6개 핵심 액션 구현:

```python
# app/services/action_executor.py

class ApproveProject(ActionBase):
    """프로젝트 승인"""
    def execute(self, project_id: str, approver: str) -> ActionResult:
        # 1. 권한 체크
        # 2. 프로젝트 상태 변경 (PENDING → APPROVED)
        # 3. Audit log 기록
        # 4. Write-back queue에 추가 (SAP)
        pass

class RejectProject(ActionBase):
    """프로젝트 거절"""
    def execute(self, project_id: str, reason: str) -> ActionResult:
        pass

class ChangeDeadline(ActionBase):
    """기한 변경"""
    def execute(self, project_id: str, new_deadline: date) -> ActionResult:
        pass

class RequestMoreInfo(ActionBase):
    """추가 정보 요청"""
    def execute(self, project_id: str, info_needed: str) -> ActionResult:
        pass

class StartPayment(ActionBase):
    """결제 시작 (금액 기반 권한)"""
    def execute(self, project_id: str, amount: float) -> ActionResult:
        # 금액이 100만원 이상이면 CFO 승인 필요
        # 1000만원 이상이면 CEO 승인 필요
        pass

class CompleteProject(ActionBase):
    """프로젝트 완료"""
    def execute(self, project_id: str) -> ActionResult:
        pass
```

**각 액션마다**:
- Execute 로직 (5-10줄)
- 5-10개 단위 테스트
- 에러 처리

---

**Day 4 (06-27)**:
- 전체 통합 테스트 (30개 테스트 모두 실행)
- 버그 수정
- Codex/Antigravity와 동기화

**Day 5 (06-28)**:
- Code review 및 최적화
- Week 1 완료 리포트 작성

#### Codex: UI 준비 (Day 1-2만)

**Day 1-2 (06-24 ~ 06-25)**:
- ActionButton 컴포넌트 틀 작성
- Props 정의 (action, onClick, disabled 등)
- 스타일 기본 설정
- Claude의 액션 모델 모니터링

**Day 3-5**: 대기 (Claude 액션 구현 완료까지)

#### Antigravity: 성능 기준선 (Day 1-2만)

**Day 1-2 (06-24 ~ 06-25)**:
- 부하 테스트 프레임워크 설정
- 성능 메트릭 정의
  - 액션 실행 시간 (p50, p95, p99)
  - Audit log 쓰기 속도
  - DB 쿼리 시간
- 베이스라인 수집

**Day 3-5**: 대기

---

**✅ Week 1 Success Criteria**:
- Claude: 30+ 테스트 통과, 6개 액션 모두 실행 가능
- Codex: ActionButton 컴포넌트 준비 완료
- Antigravity: 성능 기준선 수립

---

### Week 2: 권한 검증 + API 통합 (07-01 ~ 07-05)

#### Claude: 권한 검증 시스템 + API 엔드포인트

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
        액션 실행 권한 확인
        
        규칙:
        1. 사용자 역할 (Role) 확인
        2. 금액 기반 승인 필요 여부 확인
        3. 필수 승인자 수 확인
        """
        
        # 예시
        if amount > 10_000_000 and user_role != "CEO":
            return False, "CEO 승인 필요"
        
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
    """액션 실행 엔드포인트"""
    # 1. 권한 확인
    allowed, reason = permission_checker.check_action(
        user.id, action_id, context
    )
    if not allowed:
        raise HTTPException(403, reason)
    
    # 2. 액션 실행
    result = action_executor.execute(action_id, context)
    
    # 3. 결과 반환
    return {"status": "success", "data": result}
```

**API 엔드포인트** (3개):
- `POST /api/actions/{action_id}/execute` - 액션 실행
- `GET /api/actions` - 사용 가능한 액션 목록 (권한 기반)
- `GET /api/actions/{action_id}/preview` - 실행 미리보기

**Day 5 (07-05)**:
- API 문서 (Swagger/OpenAPI) 자동 생성
- 15+ 통합 테스트

**✅ 성공 기준**:
- API 엔드포인트 3개 모두 작동
- 통합 테스트 15/15 통과
- Swagger 문서 자동 생성

#### Codex: ActionButton 구현

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
  
  // 권한 확인
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
      {loading ? "실행 중..." : action.name}
    </button>
  )
}
```

**Day 4-5 (07-04 ~ 07-05)**:
- 액션 결과 알림 (toast/modal)
- E2E 테스트 5개

**✅ 성공 기준**:
- ActionButton 클릭 → 1초 내 응답
- 권한 없는 버튼은 disabled 표시
- E2E 5/5 통과

#### Antigravity: API 성능 테스트

**Day 1-5 (07-01 ~ 07-05)**:

```python
# tests/load/action_api_load_test.py

class ActionAPILoadTest:
    def test_execute_action_performance(self):
        """액션 실행 API 성능"""
        # 100명 동시 실행
        # 목표: 평균 <300ms, p99 <500ms
        pass
    
    def test_permission_check_performance(self):
        """권한 확인 성능"""
        # 1000개 규칙 동시 확인
        # 목표: <50ms
        pass
```

**✅ 성공 기준**:
- 액션 실행 API: <500ms (p99)
- 권한 확인: <50ms

---

**✅ Week 2 Success Criteria**:
- Claude: 3개 API 엔드포인트, 15+ 통합 테스트
- Codex: ActionButton UI, E2E 5개 시나리오
- Antigravity: API 성능 벤치마크 완료

---

### Week 3: Changelog + Write-back Worker (07-08 ~ 07-12)

#### Claude: Audit Log + Write-Back 워커

**Day 1-2 (07-08 ~ 07-09)**:

```python
# app/db/models.py

class AuditLog:
    id: int
    entity_id: str
    action_id: str
    user_id: str
    old_state: JSON  # 변경 전 상태
    new_state: JSON  # 변경 후 상태
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
        """Write-back 큐 처리"""
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
            
            await asyncio.sleep(5)  # 5초마다 체크
    
    async def send_to_sap(self, item: WriteBackQueue):
        """SAP API 호출"""
        response = await sap_client.post(
            "/api/actions",
            json=item.payload,
            timeout=5
        )
        item.status = "CONFIRMED"
```

**Day 5 (07-12)**:
- 40개 통합 테스트 (Audit log 포함)
- 재시도 로직 테스트

**✅ 성공 기준**:
- Audit log 100% 기록
- Write-back 성공률 95%+
- 통합 테스트 40/40 통과

#### Codex: Audit 대시보드

**Day 1-5 (07-08 ~ 07-12)**:

```tsx
// src/pages/audit-log.tsx

export function AuditLogDashboard() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [filter, setFilter] = useState({
    action: "ALL",
    user: "ALL",
    status: "ALL",
    dateRange: [7]  // 최근 7일
  })
  
  // 1000개 로그도 빠르게 렌더링
  // 가상 스크롤링 사용
  
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

**기능**:
- 액션별 필터링
- 사용자별 필터링
- 날짜 범위 선택
- 상태별 색상 구분 (SUCCESS/FAILED)
- CSV 다운로드

**✅ 성공 기준**:
- 1000개 로그 100ms 내 렌더링
- 필터링 실시간 작동
- E2E 5개 시나리오

#### Antigravity: Write-back 성능 최적화

**Day 1-5 (07-08 ~ 07-12)**:

```python
# tests/perf/writeback_performance.py

class WriteBackPerformanceTest:
    def test_writeback_throughput(self):
        """Write-back 처리량"""
        # 1000개 항목 동시 처리
        # 목표: <1s (p99)
        pass
    
    def test_sap_api_timeout_handling(self):
        """SAP API 타임아웃 처리"""
        # SAP가 10초 걸려도 graceful하게 재시도
        pass
    
    def test_database_write_performance(self):
        """DB 쓰기 성능"""
        # 10K audit log/min 처리
        # 목표: <100ms per batch
        pass
```

**✅ 성공 기준**:
- Write-back 처리량: 100+ items/sec
- API 타임아웃 처리: 재시도 성공률 99%
- DB 쓰기: <100ms per 100 logs

---

**✅ Week 3 Success Criteria**:
- Claude: Audit log + Write-back worker 완성, 40+ 통합 테스트
- Codex: Audit 대시보드, 필터링 + 성능 완성
- Antigravity: Write-back 성능 최적화 완료

---

### Week 4: Frontend 통합 + 최종 테스트 (07-15 ~ 07-21)

#### Claude: 최종 통합 테스트

**Day 1-3 (07-15 ~ 07-17)**:
- 50개 통합 테스트 (모든 feature 포함)
- E2E 시나리오: 쿼리 → 액션 → Write-back → Audit 기록
- 성능 튜닝

**Day 4-5 (07-18 ~ 07-21)**:
- Production 준비
- Documentation
- Performance tuning

**✅ 성공 기준**:
- 통합 테스트 50/50 통과
- 모든 성능 목표 달성
- 0 security issues

#### Codex: E2E 테스트 + Polish

**Day 1-3 (07-15 ~ 07-17)**:
- E2E 테스트 15개 시나리오
  1. 액션 실행 성공
  2. 권한 부족으로 실행 실패
  3. 액션 결과 확인
  4. Audit log 조회
  5. CSV 다운로드
  ... (10개 더)

**Day 4-5 (07-18 ~ 07-21)**:
- 반응형 디자인 (모바일)
- Dark mode
- 접근성 (WCAG)

**✅ 성공 기준**:
- E2E 15/15 통과
- 모바일 완벽하게 작동
- Dark mode 완성

#### Antigravity: 최종 벤치마크

**Day 1-5 (07-15 ~ 07-21)**:
- 100K 동시 쿼리 + 액션
- 최종 성능 리포트
- Production readiness check

**✅ 성공 기준**:
- 100K QPS 처리 가능
- 99.9% uptime
- 모든 SLA 달성

---

## 🎯 Phase 3 전체 Success Criteria

| 항목 | Target | Owner |
|------|--------|-------|
| Unit tests | 50+ 통과 | Claude |
| Integration tests | 40+ 통과 | Claude |
| E2E tests | 15+ 통과 | Codex |
| Code coverage | 85%+ | Claude |
| 액션 실행 성능 | <500ms (p99) | Antigravity |
| Write-back 성공률 | 95%+ | Claude+Antigravity |
| Audit coverage | 100% | Claude |
| UI 반응성 | <1s | Codex |
| Production readiness | 100% | All |

---

## 📋 시작 전 체크리스트

**Claude**:
- [ ] Phase 2.5 완료 및 모든 테스트 통과
- [ ] SPARQL→SQL 번역기 안정화
- [ ] ActionDefinition 스키마 설계 완료
- [ ] 개발 환경 준비

**Codex**:
- [ ] Phase 2.5 Frontend 완료
- [ ] QueryResult 컴포넌트 안정화
- [ ] ActionButton 컴포넌트 설계 완료

**Antigravity**:
- [ ] Phase 2.5 성능 벤치마크 완료
- [ ] 부하 테스트 프레임워크 준비
- [ ] SAP API 목(Mock) 구현

---

## 🔗 관련 문서

- **설계**: `PHASE3_ACTION_DEFINITION.md` (6개 액션 상세 정의)
- **상태 기계**: `PHASE3_STATE_MACHINE.md` (액션 상태 전이)
- **구현 계획**: `PHASE3_IMPLEMENTATION_PLAN.md` (상세 일정)

---

## 💬 협업 규칙 (Phase 2.5와 동일)

### 매일
1. 자신의 feature branch에서 작업
2. 커밋: `[Team] Week N Day M - 설명`
3. 문제 발생 → Slack #dev-ont-platform 즉시 공유

### 금요일 5시
1. Feature branch 최신화
2. Main 으로 merge (conflict 확인)
3. PHASE2_5_STATUS.md 업데이트

### Week 완료 후
1. Task log 작성: `task_logs/claude/YYYYMMDD_HHMM_Phase3_Week[N]_Complete.md`
2. PR 생성 (제목: `[Team] Phase 3 Week N 완료 - 산출물 요약`)

---

## 🚀 시작 신호

**Phase 3 시작 조건**:
- ✅ Phase 2.5 모든 작업 완료 (2026-06-21)
- ✅ 3개 팀 모두 준비 완료
- ✅ 이 지시서 리뷰 완료

**시작 일시**: 2026-06-24 09:00 (월요일 아침)  
**최종 완료**: 2026-07-21 17:00 (금요일 저녁)

---

**Questions?** 이 지시서는 살아있는 문서입니다. 각 Week가 시작되면 `PHASE3_WEEKLY_DETAILS.md`에 더 자세한 Task가 업데이트됩니다.

준비 완료! 🚀

