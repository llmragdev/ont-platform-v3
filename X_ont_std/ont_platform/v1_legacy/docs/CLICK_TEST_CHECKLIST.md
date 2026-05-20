# Click Test Checklist — 내부 점검용

> **용도**: 개발자/QA가 시연 직전 또는 새 기능 추가 후 사람 눈으로 직접 클릭해서 확인하는 체크리스트.
> **DEMO_SCENARIO.md와의 차이**: DEMO_SCENARIO는 강사가 외부 관객에게 보여주는 흐름(멘트 포함). 이 문서는 짧고 명확한 체크박스.
> 소요 시간: 약 15~20분.

---

## 0. 사전 준비

### 0.1 서버 2개 띄우기

```powershell
# 터미널 1 — 백엔드
conda activate claud_be
cd e:\ontology_edu\claud_통합\backend
$env:DOTENV_PATH = "F:\ai_std_dev\.env"
$env:PYTHONIOENCODING = "utf-8"
python -m uvicorn app.main:app --reload --port 8000
```

```powershell
# 터미널 2 — 프론트엔드
conda activate claud_fe
cd e:\ontology_edu\claud_통합\frontend
npm run dev
```

### 0.2 상태 초기화

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/system/reset
```
→ `status : reset` 응답이면 OK.

### 0.3 헬스 확인

브라우저로 `http://localhost:8000/api/health` 접속 → 다음 필드 확인:
- [ ] `status: "ok"`
- [ ] `llm_provider: "gemini"` (또는 `rule-based`도 OK)
- [ ] `llm.keys` 배열에 키 1개 이상

`http://localhost:3000` 접속 → 대시보드 표시되면 OK.

---

## 1. 기본 5종 시나리오 (기존 검증된 흐름)

> 자동 검증(scenarios.py + Playwright)에서 5/5 통과한 시나리오. 사람 눈으로 한 번 더 확인.

### 1.1 정상 승인 (analyst + O001)
- [ ] 우상단 셀렉터: **Kim Ops (AccountManager)** 선택
- [ ] **대시보드** → O001 클릭 → 우측 패널: Alpha Manufacturing / risk=Low / amount=3,200
- [ ] **승인 워크플로우** → O001 행 → **ApproveOrder** 클릭
- [ ] 토스트 `O001 → Approved` 표시
- [ ] 다음 시나리오 전 `Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/system/reset`

### 1.2 고위험 거부 (analyst + O003)
- [ ] **승인 워크플로우** → O003 행에 **ApproveOrder 버튼이 없음** (Reject/Hold만)

### 1.3 금액 임계 분기 (analyst → finance)
- [ ] analyst 상태에서 O002에 ApproveOrder 없음 (또는 행 자체 없음)
- [ ] 셀렉터 **Finance Lead** 전환 → O002에 ApproveOrder 등장
- [ ] 클릭 → 토스트 표시

### 1.4 지역 거부 (viewer)
- [ ] 셀렉터 **Read Only (Viewer)** → **객체 탐색** → 주문 표에 **O001만 표시** (O002 부산, O003 인천 숨김)

### 1.5 속성 마스킹 (viewer/analyst/finance)
- [ ] viewer로 객체 탐색 → C001 Alpha Manufacturing의 **risk_tier가 "Restricted"**
- [ ] analyst로 전환 → 같은 행 risk=Low, contract_terms=`Custom discount rate: ***`
- [ ] finance로 전환 → contract_terms 원본 노출

---

## 2. AI 질의 (RAG)

- [ ] **AI 질의** 메뉴 → 입력 `O001 주문 승인해도 될까?` → 실행
- [ ] 좌측 LLM 배지 색깔 확인: `gemini` (초록) 또는 `rule-based` (노랑)
- [ ] 답변에 **검색 근거 3개** (D001/D002/D003) 표시
- [ ] trace 펼치면 **8단계** 표시 (객체추출 → 컨텍스트 → 권한 → 검색 → 프롬프트 → LLM)
- [ ] Gemini 응답이면 한국어 자연스럽게 답변 + 정책 인용 정확

---

## 3. ⭐ 워크플로우 그래프 (신규 — WG-1·WG-2·WG-3)

### 3.1 캔버스 + 저장 (WG-1)
- [ ] 좌측 메뉴 **워크플로우 그래프** 클릭
- [ ] 좌측 팔레트에 7종 노드 표시 (Start / LLM / HTTP / Condition / **ApproveOrder** / **RiskAssess** / End)
- [ ] **+ Start** 클릭 → 캔버스에 Start 노드 추가
- [ ] **+ End** 추가
- [ ] Start의 아래쪽 핸들 → End의 위쪽 핸들 드래그로 연결
- [ ] 이름을 "테스트 1" 입력 → **저장** 클릭
- [ ] 토스트 `저장 완료: wfg-xxxxxx` 표시
- [ ] 셀렉트 박스에 "테스트 1 (wfg-xxx)" 등장

### 3.2 서버 측 실행 + SSE (WG-2)
- [ ] **실행** 클릭
- [ ] 노드 색상이 **실시간으로 변경** (회색 → 파랑 running → 초록 success)
- [ ] 하단 결과 테이블에 2행 누적 (Start / End)
- [ ] Status 컬럼이 `success` 배지
- [ ] Duration 컬럼에 ms 수치 표시
- [ ] **감사 로그** 메뉴 → 새로고침 → `GRAPH_RUN_STARTED`, `GRAPH_NODE_SUCCESS`, `GRAPH_RUN_FINISHED` 보임

### 3.3 도메인 노드 — ApproveOrder (WG-3) ⭐
- [ ] 셀렉터 **Kim Ops** 확인
- [ ] **+ ApproveOrder** 추가 → 클릭 → 우측 패널에 "Order ID" 입력란 등장
- [ ] **O001** 입력
- [ ] 기존 Start → 이 노드로 연결 → 실행
- [ ] 결과 테이블에 `can_approve: true` 또는 비슷한 내용 표시
- [ ] **+ ApproveOrder** 노드 추가하고 **O003** 입력 → 실행
- [ ] 같은 셀렉터(analyst)에서 결과에 `can_approve: false` (고위험 차단)

### 3.4 도메인 노드 — RiskAssess (WG-3) ⭐
- [ ] **+ RiskAssess** 추가 → Customer ID에 **C001** → 실행
- [ ] 결과에 `risk_tier: Low` + 권고 메시지 "정상 승인 프로세스 가능"
- [ ] 셀렉터 **viewer** 전환 → 같은 그래프 실행
- [ ] 결과에 `risk_tier: Restricted` (마스킹 작동)

### 3.5 권한 거부 (WG-3) ⭐
- [ ] 셀렉터 **viewer** 상태에서 워크플로우 실행 시도
- [ ] **HTTP 403 FORBIDDEN** 토스트 (Viewer는 그래프 실행 권한 없음)

### 3.6 잘못된 입력 처리
- [ ] ApproveOrder 노드에 **존재하지 않는 O999** 입력 → 실행
- [ ] 노드 색상이 **빨강 (error)** + 결과 테이블에 `OBJECT_NOT_FOUND` 표시

### 3.7 사이클 감지
- [ ] Start와 End를 양방향으로 연결 시도 (Start→End, End→Start)
- [ ] 실행 → 토스트 `실행 실패: cycle_detected`

---

## 4. ⭐ JWT 로그인 모드 (신규 — #7b)

### 4.1 로그인 강제 모드 활성화
- [ ] `claud_통합/frontend/.env.local`에 다음 추가:
  ```
  NEXT_PUBLIC_AUTH_REQUIRED=true
  ```
- [ ] `Ctrl+C`로 `npm run dev` 종료 후 다시 실행
- [ ] `http://localhost:3000` 접속 → **로그인 화면 표시**

### 4.2 로그인 흐름
- [ ] 데모 계정 4개 빠른선택 버튼 표시
- [ ] **kim.ops@example.com / analyst** 입력 → 로그인
- [ ] 대시보드 진입 + 우상단에 **녹색 배지 "Kim Ops (AccountManager)"** + **로그아웃** 버튼

### 4.3 권한 동작
- [ ] 시나리오 1.1처럼 O001 ApproveOrder 작동 (Authorization 헤더 자동 첨부됨)
- [ ] 브라우저 개발자도구(F12) → Network 탭에서 요청 헤더에 `Authorization: Bearer ...` 확인

### 4.4 로그아웃
- [ ] 우상단 **로그아웃** 클릭
- [ ] 로그인 화면으로 돌아감
- [ ] localStorage 비워짐 (F12 → Application → Local Storage → `claud_token` 없음)

### 4.5 잘못된 비밀번호
- [ ] `kim.ops@example.com / wrong` 시도 → **401 에러** + "이메일 또는 비밀번호가 일치하지 않습니다"

### 4.6 데모 모드로 복귀
- [ ] `.env.local`의 `NEXT_PUBLIC_AUTH_REQUIRED=true`를 주석 처리 또는 삭제
- [ ] `npm run dev` 재시작 → 셀렉터 모드로 복귀

---

## 5. /docs Swagger 빠른 검증

브라우저 `http://localhost:8000/docs` 접속.

- [ ] `POST /api/workflow-graphs` 펼침 → **Try it out** → Examples 셀렉트에서 첫 번째 예제 자동 채워짐
- [ ] **Execute** → 200 + 워크플로우 저장됨 (응답에 `id` 표시)
- [ ] `GET /api/workflow-graphs` Try → 방금 만든 워크플로우 1개 보임
- [ ] `POST /api/workflow-graphs/{id}/run` Try → SSE 응답이 누적되어 표시 (Stream content)
- [ ] `GET /api/audit/events` → 그래프 실행 이벤트 보임

---

## 6. 회귀 자동 검증 (선택 — 시간 있으면)

```powershell
# 백엔드
cd e:\ontology_edu\claud_통합\backend
pytest                              # 59 passed
python -m eval.scenarios --json     # 5/5
python evaluate.py --json           # 10/10

# 프론트 (백엔드 떠 있는 상태에서)
cd ..\frontend
npm run test:e2e                    # 6/6
```

모두 통과하면 코드/도메인 검증은 끝.

---

## 7. 발견된 이슈 기록란

테스트 중 막힌 부분을 여기에 기록해두면 다음 점검 때 도움이 됩니다. 형식:

```
[ ] (날짜) (어떤 메뉴/단계) (현상) (해결 또는 임시 우회)
```

### 예시
- [ ] 2026-05-12 / 워크플로우 그래프 / "실행" 누르니 SSE가 도착하지만 노드 색이 안 바뀜 → 새로고침 후 정상 (브라우저 캐시)

### 기록
- [ ] (여기에 발견 사항 추가)

---

## 8. 관련 문서

- 외부 관객용 시연 가이드: [DEMO_SCENARIO.md](DEMO_SCENARIO.md)
- 강의·교육 자료: [../../req_doc_hub/교육자료/](../../req_doc_hub/교육자료/)
- 변경 이력: [CHANGELOG.md](CHANGELOG.md)
- 남은 백로그 후보: [NEXT_STEPS.md](NEXT_STEPS.md)
