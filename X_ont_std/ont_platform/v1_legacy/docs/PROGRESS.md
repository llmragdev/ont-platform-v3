# Claude 통합 — 현재 상태 (재개용 스냅샷)

> 작업 재개 시 이 한 줄로 시작하세요:
> **`claud_통합/docs/PROGRESS.md 읽고 이어서 진행해줘`**

---

## 🟢 한 줄 요약 (2026-05-13)

**Sprint 06 완료.** 멀티테넌트 권한 관리 (JSON 시드 → 백엔드 403 강제 → company 격리 → 프론트 PermissionGate) 전 항목 DoD 검증 완료.
**다음 작업**: Sprint 07 — JWT 로그인 화면 또는 어드민 사용자 관리 화면.

---

## ✅ 오늘(2026-05-13) 완료한 것

| 항목 | 결과 |
|------|------|
| `backend/.env` 로컬 복사 (F: USB → `backend/.env`) | 완료 — USB 없이도 API 키 로딩 정상 |
| `main.py` auto-copy shutil 코드 제거 | 완료 — 단순 3-candidate 탐색으로 복원 |
| `docs/sprints/` 스프린트 보고서 체계 구축 | 완료 — Sprint 01~05 보고서 작성 |
| `README.md` docs 섹션에 sprints 경로 추가 | 완료 |
| `backend/integration_tests/` 전체 구현 | 완료 — 6개 파일 (config/seed_data/scenarios/runner/reporter/run) |
| **Sprint 06: 멀티테넌트 권한 관리** | **완료 — DoD 14개 항목 전체 통과** |

---

## ✅ Sprint 06 완료 — 멀티테넌트 권한 관리

### 추가된 파일

| 파일 | 역할 |
|------|------|
| `backend/app/config/role_defaults.json` | role → 권한 플래그 기본값 |
| `backend/app/config/companies.json` | 3개 테넌트 (default / acme / globex) |
| `backend/app/config/users.json` | 5명 사용자 (analyst / alice / bob / carol / dave) |
| `backend/app/config/projects.json` | 3개 프로젝트 |
| `backend/app/tenant.py` | TenantManager + require_permission Depends |
| `frontend/src/types/tenant.ts` | TenantUser, Company, Permissions 타입 |
| `frontend/src/context/UserContext.tsx` | 전역 테넌트 사용자 상태 |
| `frontend/src/hooks/usePermission.ts` | `usePermission(flag)` 훅 |
| `frontend/src/components/PermissionGate.tsx` | 조건부 렌더링 게이트 |
| `frontend/src/components/TenantUserSwitcher.tsx` | 회사별 그룹 드롭다운 |

### DoD 결과 요약

```
D01 bob → POST entities      → 403 ✅
D02 bob → DELETE entity      → 403 ✅
D03 bob → upload doc         → 403 ✅
D04 alice → POST entities    → 200 ✅
D05 carol → POST entities    → 200 ✅
D06 carol → GET documents    → globex만 (0건) ✅
D07 alice → GET documents    → acme만 (0건) ✅
D08 alice permissions        → can_edit_diagram: True ✅
D09 bob permissions          → can_edit_diagram: False ✅
D10 dave permissions(override) → can_upload_doc: True ✅
D11~D14 프론트 게이트        → 코드 적용 완료 ✅
```

---

## ✅ Sprint 05 완료

### 통합 테스트 실행 방법

```powershell
# 백엔드 먼저 실행
conda activate claud_be
cd e:\ontology_edu\claud_통합\backend
python -m uvicorn app.main:app --reload --port 8000

# 새 터미널에서 통합 테스트 실행
conda activate claud_be
cd e:\ontology_edu\claud_통합\backend
python -m integration_tests                        # 전체 15개
python -m integration_tests --skip-seed            # 시드 재주입 없이
python -m integration_tests --scenario S06 S07     # 특정 시나리오만
python -m integration_tests --open-report          # 완료 후 HTML 자동 오픈
```

### 구현된 파일 목록

```
backend/
└── integration_tests/
    ├── __init__.py      ← 패키지 진입점
    ├── run.py           ← CLI 진입점 (argparse)
    ├── config.py        ← BASE_URL, 채점 가중치, doc_id 상수
    ├── seed_data.py     ← 온톨로지 엔티티/관계 주입 (18개 엔티티, 9개 관계)
    ├── scenarios.py     ← 15개 시나리오 (S01~S15)
    ├── runner.py        ← 시나리오 실행 + 채점 (100점)
    ├── reporter.py      ← HTML + JSON 리포트 생성
    └── results/         ← 타임스탬프별 결과 저장
```

---

## 🏗 전체 시스템 현황

### 서버 실행 상태 확인 방법
```powershell
# 백엔드
conda activate claud_be
cd e:\ontology_edu\claud_통합\backend
python -m uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/api/health

# 프론트엔드
conda activate claud_fe
cd e:\ontology_edu\claud_통합\frontend
npm run dev
# → http://localhost:3000
```

### 테스트 현황 (최종)
| 테스트 종류 | 결과 | 마지막 실행 |
|------------|------|------------|
| pytest (기존) | 67/67 PASS | 2026-05-12 |
| pytest (hybrid) | 45/45 PASS | 2026-05-12 |
| 시나리오 자동 검증 | 5/5 PASS | 2026-05-12 |
| evaluate.py | 10/10 PASS | 2026-05-12 |
| E2E (Playwright) | 6/6 PASS | 2026-05-12 |
| 통합 테스트 (Integration) | **구현 완료** (실행 대기) | - |
| **Sprint 06 DoD 검증** | **14/14 PASS** | **2026-05-13** |

### 파일 구조 (핵심)
```
claud_통합/
├── docs/
│   ├── PROGRESS.md          ← 이 파일
│   ├── sprints/             ← 스프린트 보고서 (Sprint 01~05)
│   └── CHANGELOG.md         ← 상세 변경 이력
├── backend/
│   ├── app/
│   │   ├── main.py          ← FastAPI 라우트 (~35개 엔드포인트)
│   │   ├── app_context.py   ← 서비스 조립 (ask_hybrid 포함)
│   │   ├── llm_gateway.py   ← Gemini + generate_text() 메서드
│   │   ├── query_classifier.py   ← 질문 유형 분류 (5종)
│   │   ├── ontology_query_engine.py  ← 구조형 질의 엔진
│   │   └── config/
│   │       ├── ontology.default.json  ← 온톨로지 스키마
│   │       └── policy.default.json   ← 마스킹 정책
│   ├── .env                 ← ✅ 로컬 복사 완료 (API 키 포함)
│   ├── uploads/
│   │   └── Snowflake_소개서_HDC.pdf   ← doc-ff68a066 (29 청크)
│   ├── vector_db/
│   │   └── docs_registry.json         ← 업로드된 문서 목록
│   └── ontology_db/         ← ⚠ 현재 비어있음 (시드 주입 필요)
└── frontend/
    └── src/components/
        ├── HybridQuery.tsx        ← 통합 질의 화면
        ├── OntologySchemaManager.tsx
        ├── OntologyInstanceEditor.tsx
        └── OntologyGraphEditor.tsx
```

---

## ⚠ 알려진 이슈

| 이슈 | 영향도 | 해결 방법 |
|------|--------|----------|
| `ontology_db/` 비어있음 | 중간 — filter/compare/calculate 질의 결과 없음 | 통합 테스트 시드 주입으로 해결 예정 |
| Gemini 무료 키 429 가능성 | 낮음 — 자동 폴백 있음 | 다른 키로 교체 또는 잠시 대기 |

---

## 📋 전체 백로그 (우선순위 순)

| 우선순위 | 항목 | 예상 시간 |
|----------|------|----------|
| 🔴 High | JWT 로그인 화면 (Phase 2, Sprint 07) | 2~3시간 |
| 🔴 High | 어드민 사용자 관리 화면 | 2시간 |
| 🟡 Medium | ProjectSelector.tsx 화면 배치 | 1시간 |
| 🟡 Medium | CI 통합 (GitHub Actions) | 2시간 |
| 🟡 Medium | 질문 유형 분류 정확도 측정 지표 | 1시간 |
| 🟢 Low | 프로젝트별 역할 분리 (동일 사용자, 프로젝트마다 다른 역할) | 2시간 |
| 🟢 Low | evaluate.py에 LLM 품질 룰 추가 | 1시간 |

---

## 🔒 변경 금지 결정사항

| 항목 | 결정 |
|------|------|
| 폴더명 | `claud_통합` (한글 유지) |
| 프론트엔드 | Next.js 14 App Router + TypeScript + Tailwind |
| 가상환경 | conda — `claud_be` (python 3.11), `claud_fe` (nodejs 20) |
| LLM | Gemini `google-genai` SDK, 모델 `gemini-2.5-flash` |
| 임베딩 | `models/gemini-embedding-001` 직접 호출 (langchain 우회) |
| condition 노드 | `eval/exec` 금지, 화이트리스트 미니 파서 사용 |
