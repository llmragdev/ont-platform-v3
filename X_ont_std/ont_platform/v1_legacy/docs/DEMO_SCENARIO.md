# Claude 통합 — 프로그램 실행 시연 시나리오

> 강사용 시연 가이드. 인쇄해서 옆에 두고 강의 진행 가능하도록 만들었습니다.
> 30분 전체 시연 / 10분 핵심 시연 / 5분 라이트닝 시연 세 모드를 지원합니다.

---

## 0. 시연 모드 선택

| 모드 | 시간 | 다루는 시나리오 | 용도 |
| --- | --- | --- | --- |
| **Full** | 30분 | 5종 전부 + 코드 워크스루 | 정식 교육 |
| **Core** | 10분 | 1, 2, 5 (정상승인·고위험거부·마스킹) | 임원·외부 발표 |
| **Lightning** | 5분 | 1, 5 만 (또는 1, 2) | 데모데이·짧은 소개 |

---

## 1. 시연 사전 준비 (T-30분)

> 강의 시작 30분 전에 끝내야 안전합니다.

### 1.1 환경 점검

```powershell
conda env list                                # claud_be, claud_fe 둘 다 있어야
docker --version                              # 26+ (선택)
node --version                                # 20+ (claud_fe 안에서)
```

### 1.2 백엔드 띄우기

> **스택**: Python 3.11 + FastAPI 0.111 + Pydantic v2 + uvicorn(ASGI) + google-genai SDK.
> 선택 의존성: psycopg[binary] (Postgres), opentelemetry-sdk (관측성).
> conda env `claud_be` 안에 모두 설치되어 있습니다.

```powershell
conda activate claud_be
cd e:\ontology_edu\claud_통합\backend
$env:DOTENV_PATH = "F:\ai_std_dev\.env"       # 또는 직접 .env에 GEMINI_API_KEY
$env:PYTHONIOENCODING = "utf-8"
python -m uvicorn app.main:app --reload --port 8000
```

**확인**: 다른 터미널에서 (PowerShell)
```powershell
Invoke-RestMethod http://localhost:8000/api/health
```
응답에 `status: ok`와 `llm_provider`가 `gemini` 또는 `rule-based`로 나오면 OK.

> ⚠ **PowerShell 주의**: `curl`은 `Invoke-WebRequest`의 별칭이라 진짜 curl 플래그(`-X`, `-d` 등)를 못 받습니다.
> 본 문서는 PowerShell 네이티브 `Invoke-RestMethod`를 기본으로 씁니다.
> 진짜 curl을 쓰고 싶다면 `curl.exe ...`로 호출하세요 (Windows 10/11에 기본 설치됨).

### 1.3 프론트엔드 띄우기

> **스택**: Next.js 14 (App Router) + React 18 + TypeScript 5 + Tailwind CSS 3 + lucide-react.
> Node.js 20은 conda env `claud_fe` 안에 설치되어 있어 시스템 Node와 분리됩니다.
> 빌드러너는 Next 내장(webpack 기반). 테스트는 Playwright (Chromium).

```powershell
conda activate claud_fe
cd e:\ontology_edu\claud_통합\frontend
npm run dev                                   # http://localhost:3000  (dev 모드, 핫리로드)
# 또는 prod 모드로 안정적 시연을 원하면:
# npm run build && npm run start
```

**확인**: 브라우저에서 `http://localhost:3000` 접속 → 대시보드 표시, 우상단 사용자 셀렉터에 `Kim Ops (AccountManager)` 등 4명이 보이면 OK.

### 1.4 데이터 초기화

> 시연 직전에 한 번. 이전 클릭으로 O001이 Approved가 되어 있으면 시나리오 1이 깨집니다.

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/system/reset
# (Bash/WSL 환경이라면) curl -X POST http://localhost:8000/api/system/reset
```
응답: `status : reset` 한 줄.

### 1.5 백업 자료 준비

| 위험 | 대응 |
| --- | --- |
| Gemini 429 (키 한도) | 룰베이스 폴백으로 자동 동작. 답변 형식 동일 |
| 서버 죽음 | 위 명령들 재실행 (5초) |
| 브라우저 렌더 지연 | `npm run build` + `npm run start`로 prod 모드 |
| 인터넷 끊김 | 모든 시연이 localhost. 영향 없음 (Gemini만 폴백) |

---

## 2. 시연 흐름 (Full 모드, 30분)

> ⏱ 표시 시간은 누적입니다. 멘트는 예시이니 자기 말로 바꿔도 됩니다.

### 2.1 인트로 (0:00 ~ 2:00)

**화면**: `http://localhost:3000` 대시보드

**멘트 예시**:
> "팔란티어가 한 일을 작게 재현한 통합 콘솔입니다. 고객·주문·제품 같은 **객체**, 그들 사이의 **관계**, 그리고 **AI 질의**·**워크플로우**·**감사 로그**를 한 화면에 묶었습니다.
> 오늘은 다섯 가지 시나리오를 통해 **'AI가 비즈니스 규칙을 어떻게 지키는가'**를 보여드립니다."

**보여줄 것**:
- 좌측 메뉴 5개 (대시보드 / 객체 탐색 / AI 질의 / 워크플로우 / 감사 로그)
- 우측 컨텍스트 패널 (선택한 객체의 정보가 실시간 갱신)
- 우상단 사용자 셀렉터 (4가지 역할)
- 좌측 하단 LLM 배지 (Gemini 또는 rule-based)

---

### 2.2 시나리오 1 — 정상 승인 (2:00 ~ 6:00)

> **학습 포인트**: 정책이 통과될 때 AI는 액션을 추천하고, 사용자가 한 번 클릭으로 실행한다.

| 단계 | 클릭/입력 | 기대 결과 | 강사 멘트 |
| --- | --- | --- | --- |
| 1 | 우상단 셀렉터: **Kim Ops (AccountManager)** 선택 (기본값) | — | "분석가 김 과장 계정입니다. 서울·인천 지역, 5000 미만 결재 권한" |
| 2 | 좌측 **대시보드** → 표에서 **O001** 행 클릭 | 우측 컨텍스트 패널: Alpha Manufacturing / risk=Low / amount=3,200 | "3,200원 주문, 저위험 고객, 서울. 모든 게 통과 조건" |
| 3 | 좌측 **AI 질의** → 입력란에 `O001 주문 승인해도 될까?` → 실행 | 답변 + **검색 근거 3개** + 추천 액션 `[ApproveOrder, RejectOrder, HoldOrder]` | "AI가 정책 문서 3개를 찾아 근거로 인용했습니다. 환각이 아니라 실제 문서 기반" |
| 4 | 답변 아래 trace 펼침 | 8단계 step (객체추출 → 컨텍스트 → 권한확인 → 검색 → 프롬프트 → LLM) | "이게 RAG의 8단계입니다. 각 단계마다 권한 검증이 들어갑니다" |
| 5 | 좌측 **승인 워크플로우** → O001 행 **ApproveOrder** 버튼 클릭 | 토스트 `O001 → Approved` | "한 번의 클릭으로 상태가 바뀌었습니다" |
| 6 | 좌측 **감사 로그** → 새로고침 | `ACTION_EXECUTED` 이벤트 행, latency·retrieved_documents 포함 | "누가·언제·무엇을·왜 했는지 모두 기록됩니다" |

**팁**: 시연 끝나면 `/api/system/reset`을 다시 호출해서 상태 복구.

---

### 2.3 시나리오 2 — 고위험 거부 (6:00 ~ 9:00)

> **학습 포인트**: 같은 사용자라도 고객의 **위험 등급**이 높으면 정책이 막는다.

| 단계 | 클릭/입력 | 기대 결과 | 강사 멘트 |
| --- | --- | --- | --- |
| 1 | 좌측 **대시보드** → **O003** 행 클릭 | 우측 컨텍스트: Gamma Logistics / **risk=High** | "감마는 신용 보류 중인 고객입니다" |
| 2 | 좌측 **승인 워크플로우** | O003 행에 **ApproveOrder 버튼이 안 보임** (Reject/Hold만 있음) | "AI가 추천 자체를 안 합니다. 정책이 막은 거죠" |
| 3 | (옵션) 다른 터미널에서 아래 명령으로 직접 호출 | 빨간 에러 + `409 ACTION_NOT_ALLOWED` | "API 단에서도 같은 정책으로 두 번 막힙니다. 이중 방어" |

> **시연 옵션 — API 직접 호출 (PowerShell)**:
> ```powershell
> try {
>   Invoke-RestMethod -Method Post `
>     -Uri http://localhost:8000/api/workflow/execute `
>     -ContentType 'application/json' `
>     -Body '{"action":"ApproveOrder","order_id":"O003"}'
> } catch {
>   Write-Host "HTTP $($_.Exception.Response.StatusCode.value__)"
>   Write-Host $_.ErrorDetails.Message
> }
> ```
> 기대 출력: `HTTP 409` + `{"error":{"code":"ACTION_NOT_ALLOWED",...}}`

---

### 2.4 시나리오 3 — 금액 임계 분기 (9:00 ~ 13:00)

> **학습 포인트**: 같은 주문이라도 **사용자 역할**에 따라 승인 권한이 갈린다.

| 단계 | 클릭/입력 | 기대 결과 | 강사 멘트 |
| --- | --- | --- | --- |
| 1 | analyst 상태에서 좌측 **승인 워크플로우** → O002 확인 | O002에 ApproveOrder 버튼 없음 (또는 행 자체가 큐에 없음) | "8,200원이라 김 과장 권한을 넘었습니다. 5,000 이상은 재무 권한" |
| 2 | 우상단 셀렉터: **Finance Lead (FinanceManager)**로 전환 | 화면 자동 갱신 | "이제 재무 팀장 계정" |
| 3 | 좌측 **승인 워크플로우** | O002 행에 **ApproveOrder 버튼 등장** | "권한이 다르니 같은 주문에서도 다른 액션이 보입니다" |
| 4 | ApproveOrder 클릭 | 토스트 `O002 → Approved` | "재무 팀장은 승인 가능" |

---

### 2.5 시나리오 4 — 지역 거부 (13:00 ~ 16:00)

> **학습 포인트**: 권한은 **속성 단위**까지 내려간다. region이 다르면 객체 자체가 안 보인다.

| 단계 | 클릭/입력 | 기대 결과 | 강사 멘트 |
| --- | --- | --- | --- |
| 1 | 우상단 셀렉터: **Read Only (Viewer)** 전환 | — | "조회 전용 계정, 서울 지역만 권한" |
| 2 | 좌측 **객체 탐색** → 주문 표 | **O001만 보임**, O002(부산)·O003(인천)은 숨김 | "부산·인천 주문은 목록에서 사라졌습니다" |
| 3 | (옵션) 다른 터미널에서 아래 명령으로 직접 호출 | 빨간 에러 + `403 FORBIDDEN` | "API에서도 403입니다. UI만 숨기는 게 아니라 백엔드가 차단" |

> **시연 옵션 — API 직접 호출 (PowerShell)**:
> ```powershell
> try {
>   Invoke-RestMethod "http://localhost:8000/api/objects/orders/O002/context?user=viewer"
> } catch {
>   Write-Host "HTTP $($_.Exception.Response.StatusCode.value__)"
>   Write-Host $_.ErrorDetails.Message
> }
> ```
> 기대 출력: `HTTP 403` + `{"error":{"code":"FORBIDDEN",...}}`

---

### 2.6 시나리오 5 — 속성 마스킹 (16:00 ~ 20:00)

> **학습 포인트**: 같은 객체라도 **사용자 역할에 따라 응답이 다르다**. risk_tier·contract_terms 같은 민감 속성이 마스킹됨.

| 단계 | 클릭/입력 | 기대 결과 | 강사 멘트 |
| --- | --- | --- | --- |
| 1 | viewer 상태에서 좌측 **객체 탐색** → 고객 표 | C001 Alpha Manufacturing의 risk가 **Restricted** | "viewer는 위험 등급도 볼 수 없습니다" |
| 2 | 셀렉터: **analyst** 전환 → 같은 행 | risk=**Low**, contract_terms=**Custom discount rate: ***** | "분석가는 위험 등급은 보지만, 할인율 같은 계약 세부는 마스킹" |
| 3 | 셀렉터: **finance** 전환 → 같은 행 | contract_terms=**Standard support terms, custom discount 7%** (원본) | "재무 팀장만 계약 원본을 봅니다" |

**중요**: 세 화면을 빠르게 번갈아 보여주면 마스킹 정책의 단계가 강렬하게 전달됩니다.

---

### 2.7 코드 워크스루 (20:00 ~ 27:00)

> 짧게 코드로 들어가서 "이게 어떻게 가능한지" 보여줍니다. 화면 공유로 IDE 열고 진행.

**보여줄 4개 파일** (각 1~2분):

1. **[backend/app/ontology.py](../backend/app/ontology.py)** — OntologyRegistry가 객체타입/관계를 등록하는 코드
   - 멘트: "여기가 팔란티어의 '온톨로지'에 해당하는 부분입니다. 지금은 Python 코드 안에 있지만, 향후 JSON 파일로 분리할 계획"
2. **[backend/app/policy.py](../backend/app/policy.py)** — PolicyEngine의 `can_execute_action`
   - 멘트: "방금 본 5,000원 임계값이 여기 if문에 있습니다. amount < 5000이면 분석가도 가능, 이상이면 재무만"
3. **[backend/app/app_context.py](../backend/app/app_context.py)** — `ask()`의 8단계 파이프라인
   - 멘트: "이 8줄이 RAG 전체입니다. 각 줄이 화면에서 본 trace의 한 단계"
4. **[backend/app/llm_gateway.py](../backend/app/llm_gateway.py)** — Gemini + 룰베이스 폴백
   - 멘트: "API 한도가 차도 시스템이 죽지 않습니다. 룰베이스로 자동 폴백되고 warning이 사용자에게 전달"

---

### 2.8 자동 검증 보여주기 (27:00 ~ 29:00)

```powershell
# 백엔드 회귀
pytest                                       # 36 passed
python -m eval.scenarios --json              # 5/5 PASS
python evaluate.py --json                    # 10/10 PASS, mean p@3=1.0

# 프론트 회귀
npm run test:e2e                             # 6/6 PASS
```

**멘트**:
> "지금까지 본 5개 시나리오가 매 코드 변경마다 자동으로 검증됩니다. 회귀가 발생하면 즉시 알 수 있습니다."

---

### 2.9 마무리 — 솔루션화 비전 (29:00 ~ 30:00)

**멘트 예시**:
> "오늘 본 것은 **'주문 결재'** 도메인이지만, 같은 골격으로 **인사 결재·의료 차트·계약 심사** 어디에든 적용 가능합니다. 다만 지금은 객체/정책/워크플로우가 Python 코드 안에 있어서, 새 도메인 적용에는 개발자가 필요합니다.
> 다음 단계는 이 셋을 **설정 파일로 분리**해서, 관리자가 GUI로 직접 규칙을 바꿀 수 있는 **온톨로지 관리 솔루션**으로 만드는 것입니다."

→ 청중이 "다음에 뭐가 가능한지" 궁금하게 끝맺기.

---

## 3. Core 모드 (10분, 짧은 발표)

생략하고 시나리오 1, 2, 5만 진행. 각 2~3분.
코드 워크스루는 `policy.py` 한 파일만 30초.
마무리는 솔루션화 비전 1문장.

## 4. Lightning 모드 (5분, 데모데이)

시나리오 1만 진행 + 시나리오 5의 viewer 화면 1번 보여주기.
"역할에 따라 시스템 응답이 달라진다"가 핵심 메시지.

---

## 5. 시연 중 자주 받는 질문 (FAQ 즉답)

| 질문 | 즉답 |
| --- | --- |
| 진짜 AI가 답하는 거예요? | Gemini가 답하면 좌측 LLM 배지가 초록(`gemini`). 키 한도면 룰베이스로 폴백되고 노란 경고가 답변 위에 떠요. |
| 새 객체 타입 추가하려면? | 지금은 Python 코드 수정 + 재배포. 향후 설정 파일로 분리할 계획입니다. |
| 사용자가 100명이면? | 인메모리 모드는 한계가 있고, 환경변수 `DATABASE_URL`만 주면 PostgreSQL로 전환됩니다. |
| 토큰 인증은요? | 백엔드는 JWT 발급 가능 (`POST /api/auth/login`). 프론트엔드는 데모 편의를 위해 셀렉터 방식 유지. |
| 검색은 어떤 알고리즘? | BM25 (IDF + k1/b 정규화). 한글 키워드는 토크나이저에서 영어 동의어로 확장. |
| 답변이 환각인지 어떻게 알아요? | 모든 답변 아래 **검색 근거** 카드가 표시됩니다. 클릭하면 원문 확인 가능. |
| 우리 회사 데이터로 바꾸려면? | `backend/app/data.py`의 RAW_* 데이터를 교체 + JSON Repository 사용. 향후 GUI 편집기 추가 예정. |

---

## 6. 시연 후 정리

```powershell
# 두 서버 종료 (Ctrl+C)
# 다음 시연 전 데이터 초기화
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/system/reset
```

브라우저 캐시가 남아 있을 수 있으니 **Shift+F5** 로 강제 새로고침 1회.

---

## 7. 시연 자료 인덱스

- 사전 안내: [../../req_doc_hub/교육자료/01_사전_안내.md](../../req_doc_hub/교육자료/01_사전_안내.md)
- 실습 흐름 상세: [../../req_doc_hub/교육자료/02_실습_플로우.md](../../req_doc_hub/교육자료/02_실습_플로우.md)
- 심화 과제: [../../req_doc_hub/교육자료/03_심화_과제.md](../../req_doc_hub/교육자료/03_심화_과제.md)
- FAQ: [../../req_doc_hub/교육자료/04_FAQ.md](../../req_doc_hub/교육자료/04_FAQ.md)
- 솔루션화 다음 단계: [NEXT_STEPS.md](NEXT_STEPS.md), [FINAL_REPORT.md](FINAL_REPORT.md)

---

## 8. 빠른 명령 참조 (한 페이지 출력용)

```powershell
# === 사전 (T-30분) ===
conda activate claud_be
cd e:\ontology_edu\claud_통합\backend
$env:DOTENV_PATH = "F:\ai_std_dev\.env"
$env:PYTHONIOENCODING = "utf-8"
python -m uvicorn app.main:app --reload --port 8000

# (새 터미널)
conda activate claud_fe
cd e:\ontology_edu\claud_통합\frontend
npm run dev

# === 시연 직전 초기화 ===
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/system/reset

# === 시연 중 자동 검증 (선택) ===
cd ..\backend
pytest                                      # 36 passed
python -m eval.scenarios --json             # 5/5
python evaluate.py --json                   # 10/10
cd ..\frontend
npm run test:e2e                            # 6/6

# === 시연 후 ===
# 두 서버 Ctrl+C
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/system/reset    # 다음을 위해
```
