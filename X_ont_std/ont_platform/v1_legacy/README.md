# Claude 통합 — 온톨로지 AI 업무 콘솔

`src_anti`(직관적인 업무 화면)와 `src_codex`(운영형 백엔드 구조)의 장점을 합쳐, **FastAPI + Next.js**로 다시 만든 통합 학습 콘솔입니다. `req_doc_hub/평가/23-codex가 2개 소스 비교.md`의 권장 결합 방향을 그대로 구현했습니다.

## 1. 무엇이 들어 있나

| 영역 | 내용 |
| --- | --- |
| 백엔드 | FastAPI, OntologyRegistry/Service, BM25(IDF+k1/b), PolicyEngine, WorkflowEngine, AuditService, Repository(InMemory/JsonFile) |
| LLM | Gemini SDK 직접 호출 + 키 미설정/실패 시 규칙 기반 폴백 (응답에 `provider`/`warning` 노출) |
| 프론트엔드 | Next.js 14 (App Router) + TypeScript + Tailwind |
| 화면 | 대시보드 / 객체 탐색 / AI 질의 / 승인 워크플로우 / 감사 로그 + 우측 컨텍스트 패널 + 사용자 전환 셀렉터 |
| 거버넌스 학습 | 우측 상단 셀렉터로 `analyst / finance / viewer / admin` 즉시 전환 → 마스킹·권한 거부·액션 큐 차이를 눈으로 확인 |

## 2. 폴더 구조

```
claud_통합/
├── README.md            # 이 파일 (사용자/교육생 가이드)
├── docker-compose.yml   # backend + frontend (+ 선택 postgres)
├── .env.example
├── docs/                       # 📚 작업 문서
│   ├── PROGRESS.md             # 현재 상태 스냅샷 (재개용)
│   ├── CHANGELOG.md            # 작업 단위별 완료 이력
│   ├── NEXT_STEPS.md           # 미완료 백로그
│   ├── FINAL_REPORT.md         # 최종 작업 보고서
│   ├── DEMO_SCENARIO.md        # 강사용 시연 시나리오 (Full/Core/Lightning 3모드)
│   ├── CLICK_TEST_CHECKLIST.md # 내부 점검용 체크리스트 (개발자/QA)
│   ├── AI_코딩_에이전트_비교/   # 외부 AI 코딩 에이전트(Codex/Antigravity 등) 평가에 대한 자체 댓글
│   ├── sprints/                 # 📋 에자일 스프린트 보고서 (목표·완료·문제·개선)
│   │   ├── README.md            # 스프린트 인덱스 + ADR 요약
│   │   ├── TEMPLATE.md          # 신규 스프린트 보고서 템플릿
│   │   ├── sprint_01.md         # Sprint 01: 통합 기반 구축
│   │   ├── sprint_02.md         # Sprint 02: 인프라 강화
│   │   ├── sprint_03.md         # Sprint 03: 온톨로지 재설계 Phase 1~5 + RAG
│   │   ├── sprint_04.md         # Sprint 04: 하이브리드 질의 시스템
│   │   └── sprint_05.md         # Sprint 05: 통합 테스트 자동화 (진행 중)
│   ├── note/                    # 자체 분석 보고서·설계서 (예: 온톨로지 재설계)
│   └── 기타_분석/              # 임시 조사·외부 소스 비교 등 (정리되면 위 핵심 문서로 흡수)
├── backend/
│   ├── app/             # FastAPI + 도메인 서비스 (codex 이식)
│   ├── eval/            # 시나리오 자동검증 + RAG 평가
│   ├── tests/           # pytest 36건
│   ├── environment.yml, requirements.txt, .env.example
│   ├── evaluate.py, pytest.ini
│   └── Dockerfile, .dockerignore
└── frontend/
    ├── src/
    │   ├── app/         # layout, page, globals.css
    │   ├── components/  # Sidebar / ContextPanel / Dashboard / Explorer / AIQuery / Workflow / Audit / UserSwitcher
    │   ├── lib/api.ts   # 백엔드 호출 클라이언트
    │   └── types/api.ts
    ├── e2e/             # Playwright 스펙
    ├── environment.yml  # conda env: claud_fe (nodejs=20)
    ├── package.json, playwright.config.ts
    ├── tailwind.config.ts, tsconfig.json
    └── Dockerfile, .dockerignore
```

## 3. 실행 방법

### 3.1 백엔드 (conda `claud_be`)

```powershell
# 1) conda env 생성 (1회)
cd e:\ontology_edu\claud_통합\backend
conda env create -f environment.yml          # 또는: conda create -n claud_be python=3.11 -y && pip install -r requirements.txt
conda activate claud_be

# 2) Gemini 키 연결 (택1)
$env:DOTENV_PATH = "F:\ai_std_dev\.env"      # 기존 .env 그대로 사용
# 또는
copy .env.example .env                        # 후 .env 안에 GEMINI_API_KEY 직접 입력

# 3) 테스트
pytest                                        # 17 passed (API 11 + LLM Gateway 6)

# 4) 학습 시나리오 5종 자동 검증 + RAG 품질 평가
$env:PYTHONIOENCODING="utf-8"
python -m eval.scenarios --json               # 5/5 PASS
python evaluate.py --json                     # 10/10 PASS, mean p@3=1.0

# 5) 서버 기동
python -m uvicorn app.main:app --reload --port 8000

# 헬스: http://localhost:8000/api/health  →  {"status":"ok","llm_provider":"gemini"|"rule-based","llm":{...stats}}
# OpenAPI 문서: http://localhost:8000/docs
```

### 3.2 프론트엔드 (conda `claud_fe`)

```powershell
cd e:\ontology_edu\claud_통합\frontend
conda env create -f environment.yml           # nodejs=20 from conda-forge
conda activate claud_fe

copy .env.local.example .env.local            # NEXT_PUBLIC_API_BASE 기본값 http://localhost:8000

npm install
npm run dev                                   # http://localhost:3000

# E2E (백엔드가 8000에서 떠 있어야 함)
npx playwright install chromium               # 최초 1회
npm run test:e2e                              # 6/6 PASS
```

## 4. 학습 시나리오 (실습 5종)

| 시나리오 | 클릭 흐름 | 학습 포인트 |
| --- | --- | --- |
| **1. 정상 승인** | analyst 로그인 → 대시보드 → `O001` 선택 → AI 질의 "O001 주문 승인해도 될까?" → 워크플로우에서 ApproveOrder | Low risk + 5000 미만 + Seoul 지역 → 권한 통과 |
| **2. 고위험 거부** | analyst → `O003`(Gamma, High) 선택 → ApproveOrder 클릭 | `ACTION_NOT_ALLOWED` 도메인 오류 표시 → PolicyEngine이 customer.risk_tier=="High" 차단 |
| **3. 금액 임계 분기** | analyst → `O002`(8200원) ApproveOrder 시도 → 실패 → finance로 사용자 전환 후 재시도 | 5000 이상은 FinanceManager 전용 |
| **4. 지역 거부** | viewer로 전환 → 대시보드 | Seoul 지역만 보임 (`O002`/`O003`는 region 권한으로 가려짐) |
| **5. 속성 마스킹** | viewer/analyst로 객체 탐색 → 고객 상세 | `risk_tier`/`contract_terms` 마스킹 단계 비교 |

## 5. API 매핑

| 화면 | API |
| --- | --- |
| Dashboard | `GET /api/objects/orders?user={role}`, `GET /api/workflow/queue?user={role}` |
| Explorer | `GET /api/objects/customers`, `GET /api/objects/orders`, `GET /api/objects/orders/{id}/context` |
| AI Query | `POST /api/ask` (body `{question}`) |
| Workflow | `GET /api/workflow/queue`, `POST /api/workflow/execute` (body `{action, order_id}`) |
| Audit | `GET /api/audit/events` |
| Sidebar 헬스 | `GET /api/health` |
| 사용자 전환 | `GET /api/users` |

모든 API는 `?user=analyst|finance|viewer|admin` 쿼리로 역할을 바꿉니다. 운영 환경에서는 실제 인증으로 교체하세요.

## 6. 23-codex 평가 항목 해결 현황

| 영역 | src_anti 원래 결함 | claud_통합 |
| --- | --- | --- |
| PolicyEngine 인터페이스 | `check_permission` 미정의 (서버 500) | ✅ `PolicyEngine` 일관 인터페이스 |
| BM25 | 단순 count | ✅ IDF + 길이 정규화 + `k1/b` |
| LLM Gateway | 휴리스틱 only | ✅ Gemini SDK + 키 미설정/실패 자동 폴백 |
| 사용자/역할 | `CURRENT_ROLE="Admin"` 하드코딩 | ✅ 4종 역할 + UI 셀렉터 |
| 문서 권한 필터 | 없음 | ✅ visibility 기반 필터 |
| 워크플로우 전이 | 3가지 | ✅ 7가지 (Submitted→Review/Approved/Rejected→Fulfilled→Closed) |
| Audit 구조화 | 문자열 | ✅ `latency_ms`/`retrieved_documents`/`llm_provider`/`error_code` 포함 |
| Repository | 전역 mutable | ✅ DataRepository 추상 (InMemory/JsonFile) |
| API 도메인 오류 | 일반 detail | ✅ `OBJECT_NOT_FOUND/RELATION_MISMATCH/FORBIDDEN/ACTION_NOT_ALLOWED` |

남은 보강 후보: 실제 LLM 평가 자동화(`evaluate.py`), 프론트 E2E (Playwright), PostgreSQL Repository.

## 7. 문제 해결

- **`/api/health`의 `llm_provider`가 `rule-based`**: `.env`에 `GEMINI_API_KEY[1|2|3]` 중 하나가 있어야 합니다. `DOTENV_PATH`가 올바른지 확인하세요.
- **`/api/ask` 응답의 `warning`에 `429 RESOURCE_EXHAUSTED`**: Gemini 무료 티어 일일 한도 초과. 다른 키로 교체하거나 잠시 후 재시도. 응답 자체는 룰 기반으로 자동 폴백됩니다.
- **`pytest`에서 `ImportError`**: 반드시 `backend/` 디렉토리 안에서 실행 (`from app.main import app` 경로).
- **한글 폴더명으로 npm 오류**: 발생 시 `claud_통합`을 `claud_unified`로 리네임 후 README의 경로도 일괄 변경.

## 8. 다음 단계

- **강의·시연 진행** → [docs/DEMO_SCENARIO.md](docs/DEMO_SCENARIO.md) (Full 30분 / Core 10분 / Lightning 5분 모드)
- **시연 직전 점검 / 새 기능 확인** → [docs/CLICK_TEST_CHECKLIST.md](docs/CLICK_TEST_CHECKLIST.md) (15~20분 체크박스)
- 남은 백로그 → [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md)
- 변경 이력 → [docs/CHANGELOG.md](docs/CHANGELOG.md)
- 빠른 재개용 스냅샷 → [docs/PROGRESS.md](docs/PROGRESS.md)
- 최종 보고서 → [docs/FINAL_REPORT.md](docs/FINAL_REPORT.md)
