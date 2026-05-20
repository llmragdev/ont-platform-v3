# Sprint 01 — 통합 기반 구축

> **기간**: 2026-05-11 (초기)
> **상태**: ✅ 완료
> **이전 스프린트**: 없음 (최초)

---

## 1. 스프린트 목표

- [x] `src_anti`(UI) + `src_codex`(백엔드)의 장점을 합쳐 `claud_통합` 프로젝트 생성
- [x] FastAPI 백엔드 기본 골격 + 도메인 서비스 구현
- [x] Next.js 14 프론트엔드 초기 화면 5종 구현
- [x] 학습 시나리오 5종 자동 검증 통과

---

## 2. 백로그 → 완료 항목

| ID | 항목 | 구분 | 결과 |
|----|------|------|------|
| S-01 | src_anti/src_codex 비교 분석 및 통합 방향 결정 | docs | ✅ |
| S-02 | FastAPI 백엔드 기반 구조 (Step A) | feature | ✅ |
| S-03 | Next.js 프론트엔드 초기 구성 (Step B) | feature | ✅ |
| S-04 | conda 환경 파일 (Step C) | infra | ✅ |
| S-05 | 최상위 README 문서 (Step D) | docs | ✅ |
| S-06 | E2E 검증 (Step E) | test | ✅ |
| S-07 | 학습 시나리오 API 자동 검증 (NEXT #1) | test | ✅ |
| S-08 | LLM Gateway 키 로테이션 (NEXT #3) | feature | ✅ |
| S-09 | evaluate.py RAG 자동 평가 (NEXT #4) | test | ✅ |
| S-10 | Gemini 실제 답변 품질 검증 (NEXT #2) | test | ✅ |

---

## 3. 기술 변경 사항

### 신규 파일

| 파일 경로 | 역할 |
|-----------|------|
| `backend/app/errors.py` | 도메인 오류 코드 (AppError) |
| `backend/app/models.py` | 엔티티 모델 (ObjectType 등) |
| `backend/app/data.py` | 인메모리 시드 데이터 |
| `backend/app/repository.py` | 데이터 저장소 추상화 (InMemory) |
| `backend/app/audit.py` | 감사 로그 서비스 |
| `backend/app/ontology.py` | OntologyRegistry + OntologyService |
| `backend/app/policy.py` | PolicyEngine (역할/지역/리스크/금액) |
| `backend/app/search.py` | BM25 (IDF + k1/b) + 권한 필터 |
| `backend/app/workflow.py` | WorkflowEngine + 5 액션 + 7 전이 |
| `backend/app/llm_gateway.py` | Gemini SDK + 키 로테이션 + 룰베이스 폴백 |
| `backend/app/rag.py` | extract_object_ids + RAGService |
| `backend/app/app_context.py` | 서비스 조립 + `ask()` 8단계 파이프라인 |
| `backend/app/main.py` | FastAPI 라우트 12종 |
| `backend/eval/scenarios.py` | 학습 시나리오 5종 자동 검증 |
| `backend/evaluate.py` | RAG 평가 CLI |
| `frontend/src/components/` | Sidebar, Dashboard, Explorer, AIQuery, Workflow, Audit 등 8종 |

### 주요 기술 결정

| 항목 | 선택 | 이유 |
|------|------|------|
| 폴더명 | `claud_통합` (한글) | 기존 프로젝트 일관성 |
| 프론트 | Next.js 14 App Router + TypeScript + Tailwind | 최신 React 패턴 |
| LLM | `google-genai` SDK 직접 호출 | langchain 불필요 의존성 배제 |
| 가상환경 | conda 2개 (`claud_be` / `claud_fe`) | Python/Node 버전 격리 |
| BM25 | IDF + 길이 정규화 + k1/b 파라미터 | src_anti 단순 count 대비 정확도 향상 |

---

## 4. 발견된 문제

### 🐛 버그

| # | 현상 | 원인 | 해결 방법 |
|---|------|------|-----------|
| B-01 | Gemini 모델 `gemini-2.0-flash-001` 404 NOT_FOUND | 신규 사용자에게 해당 모델 미제공 | `DEFAULT_MODEL`을 `gemini-2.5-flash`로 변경 |
| B-02 | LLM 429 쿼터 초과 시 전체 요청 실패 | 단일 키만 사용 | 키 로테이션 구현 (`GEMINI_API_KEY1~4` 자동 수집) |

### 🚧 블로커

| # | 내용 | 해결 방법 |
|---|------|----------|
| BL-01 | `src_anti PolicyEngine.check_permission` 미정의 → 서버 500 | `claud_통합`에서 일관된 인터페이스로 재구현 |

---

## 5. 개선된 점 (vs. 기존 src_anti / src_codex)

- **BM25**: 단순 count → IDF + 길이 정규화 + k1/b
- **LLM Gateway**: 휴리스틱 only → Gemini SDK + 키 로테이션 + 폴백
- **사용자 역할**: `CURRENT_ROLE="Admin"` 하드코딩 → 4종 역할 + UI 셀렉터
- **문서 권한 필터**: 없음 → visibility 기반 필터
- **Audit**: 문자열 → `latency_ms`/`retrieved_documents`/`llm_provider` 구조화
- **Repository**: 전역 mutable → DataRepository 추상 (InMemory)
- **API 오류**: 일반 detail → `OBJECT_NOT_FOUND`/`FORBIDDEN` 등 도메인 코드

---

## 6. 테스트 결과

| 테스트 종류 | 이전 | 현재 | 비고 |
|------------|------|------|------|
| pytest | 0 | 17/17 | API 11 + LLM Gateway 6 |
| 시나리오 자동 검증 | - | 5/5 PASS | |
| evaluate.py | - | 10/10 PASS, p@3=1.0 | |
| 회귀 건수 | - | 0 | |

---

## 7. 다음 스프린트 제안 백로그

- [ ] Playwright E2E 프론트 자동 검증 (High)
- [ ] JWT 인증 백엔드 (Medium)
- [ ] PostgreSQL Repository (Medium)
- [ ] OpenTelemetry 관측성 (Low)
- [ ] Docker compose 패키징 (Medium)

---

## 8. 회고

### 잘 된 것 👍
- `src_anti + src_codex` 비교 분석 → 통합 방향이 명확히 결정됨
- 키 로테이션으로 LLM 안정성 크게 향상
- 시나리오/evaluate 자동화로 회귀 감지 체계 확립

### 아쉬운 것 👎
- 온톨로지 타입이 Python 코드에 하드코딩 → 확장 시 코드 수정 필요 (Sprint 03에서 해결)
- 프론트 E2E 없음 → 클릭 검증은 수동

### 다음에 시도할 것 🔁
- 인증/인프라 강화로 교육 환경 완성도 높이기
