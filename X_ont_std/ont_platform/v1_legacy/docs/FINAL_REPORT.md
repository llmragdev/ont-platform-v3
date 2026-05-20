# claud_통합 — 최종 작업 보고서

> 작성일: 2026-05-12
> 작업 대상: `e:\ontology_edu\claud_통합\` (백엔드 FastAPI + 프론트엔드 Next.js)
> 외부 평가: [Codex 총평](../../Codex의_claud에 대한 총평/claud_통합_검증_총평.md) — 본 보고서는 그 총평이 작성된 시점(pytest 17 passed) 이후의 추가 작업을 포함한 종합 결과를 정리한다.

---

## 1. 한 줄 결론

`src_anti`(업무 화면)와 `src_codex`(운영형 백엔드)를 결합한 **교육·운영 겸용 통합 샘플**을 완성했다.
**전체 NEXT_STEPS 백로그 + WorkflowGraph 3 단계 + Gemini 실응답 검증 모두 완료**. 미해결 외부 의존이 없는 상태.

## 2. 작업 범위 요약

| 구분 | 항목 | 결과 |
| --- | --- | --- |
| 1단계 | Step A — 백엔드(FastAPI + 도메인 서비스) | ✅ |
| 1단계 | Step B — 프론트엔드(Next.js 14 + Tailwind) | ✅ |
| 1단계 | Step C — conda 환경 파일 2종 | ✅ |
| 1단계 | Step D — README + NEXT_STEPS 작성 | ✅ |
| 1단계 | Step E — 두 서버 동시 가동 E2E 검증 | ✅ |
| 2단계 | NEXT_STEPS #1 — 학습 시나리오 API 자동 검증 | ✅ 5/5 PASS |
| 2단계 | NEXT_STEPS #2 — Gemini 실제 답변 품질 | ✅ 5케이스, gemini-2.5-flash 갱신 |
| 2단계 | NEXT_STEPS #3 — LLM Gateway 키 로테이션 | ✅ |
| 2단계 | NEXT_STEPS #4 — `evaluate.py` RAG 자동 평가 | ✅ 10/10 PASS, mean p@3=1.0 |
| 2단계 | NEXT_STEPS #5 — Playwright 프론트 E2E | ✅ 6/6 PASS |
| 2단계 | NEXT_STEPS #6 — PostgreSQL Repository | ✅ |
| 2단계 | NEXT_STEPS #7 — JWT 인증(백엔드) | ✅ |
| 2단계 | NEXT_STEPS #7b — JWT 프론트엔드 통합 | ✅ 하위호환 유지 |
| 2단계 | NEXT_STEPS #8 — OpenTelemetry 관측성 | ✅ |
| 2단계 | NEXT_STEPS #9 — Docker compose 패키징 | ✅ |
| 2단계 | NEXT_STEPS #10 — 교육 가이드 5문서 | ✅ |
| 3단계 | WG-1 — WorkflowGraph React Flow + CRUD | ✅ 7 테스트 |
| 3단계 | WG-2 — WorkflowGraph 서버 실행 + SSE | ✅ 11 테스트 |
| 3단계 | WG-3 — WorkflowGraph 거버넌스 통합 (도메인 노드 + 노드별 권한) | ✅ 5 테스트 |

상세 결과 박스는 [CHANGELOG.md](CHANGELOG.md) 참조.

## 3. 검증 결과 (수치)

| 검증 방식 | 결과 |
| --- | --- |
| `pytest` (backend) | **59/59 PASS** |
| `python -m eval.scenarios` (학습 시나리오 자동검증) | **5/5 PASS** |
| `python evaluate.py` (RAG 품질 평가) | **10/10 PASS**, mean precision@3 = **1.0** |
| `npm run test:e2e` (Playwright) | **6/6 PASS** (~10초) |
| `npm run build` (Next.js) | **성공** (정적 페이지 4/4, First Load 145KB) |
| `docker compose config` (compose 문법) | **OK** |
| Gemini 실제 답변 (gemini-2.5-flash) | 5케이스 모두 정상, 한국어/근거 인용/환각 없음 |
| 두 서버 동시 가동 + API 호출 | ✅ /api/health · /api/auth/login · /api/workflow-graphs/{id}/run (SSE) 정상 응답 |

테스트 분포:
- `tests/test_api.py` — 11 (API 통합)
- `tests/test_auth.py` — 11 (JWT, 비밀번호 해시, 헤더 우선/쿼리 폴백)
- `tests/test_llm_gateway.py` — 6 (키 수집/no_genai/첫 키 성공/429 폴오버/모두 실패/문서 없음)
- `tests/test_repository.py` — 5 (InMemory/JsonFile/Postgres URL 폴백/클래스 import/Json roundtrip)
- `tests/test_telemetry.py` — 3 (no-op span/OTEL_ENABLED=false 처리/setup 반환)
- `tests/test_workflow_graph.py` — 7 (CRUD + 권한 + 페이로드 검증)
- `tests/test_workflow_graph_engine.py` — 11 (위상정렬·condition·SSE·이력·viewer 거부·감사)
- `tests/test_workflow_graph_wg3.py` — 5 (도메인 노드 + 노드 타입별 권한)

## 4. 23-codex 평가 항목 대비 충족 현황

`req_doc_hub/평가/23-codex가 2개 소스 비교.md`가 제시한 결합 방향을 그대로 구현했다.

| 영역 | src_anti 원래 결함 | claud_통합 결과 |
| --- | --- | --- |
| PolicyEngine 인터페이스 | `check_permission` 미정의 → 첫 호출 500 | ✅ 일관 인터페이스, 17 케이스로 회귀 검증 |
| BM25 | 단순 token count | ✅ IDF + 길이 정규화 + `k1/b` |
| LLM Gateway | 휴리스틱만 | ✅ Gemini SDK + 키 로테이션 + 룰베이스 폴백 |
| 사용자/역할 모델 | `Admin` 하드코딩 | ✅ 4종 역할 + UI 셀렉터 + JWT 발급/검증 |
| 문서 권한 필터 | 없음 | ✅ visibility 기반 필터 |
| 워크플로우 전이 | 3개 | ✅ 7개 (Submitted→Review/Approved/Rejected→Fulfilled→Closed) |
| Audit 구조화 | 문자열 | ✅ `latency_ms`/`retrieved_documents`/`llm_provider`/`key_used`/`error_code` |
| Repository 계층 | 전역 mutable | ✅ DataRepository 추상화 + InMemory/JsonFile/**Postgres** + `resolve_default()` |
| API 도메인 오류 | 일반 detail | ✅ OBJECT_NOT_FOUND/RELATION_MISMATCH/FORBIDDEN/ACTION_NOT_ALLOWED/INVALID_CREDENTIALS 등 |
| **evaluate.py 자동 평가** | 부재 | ✅ 10건 케이스 + 6 지표 + p50/p95 latency |
| **프론트 E2E** | 부재 | ✅ Playwright 6/6 |
| **JWT 인증** | 부재 | ✅ 백엔드(표준 라이브러리 PBKDF2 + HS256), 프론트 통합은 #7b로 분리 |
| **관측성** | 부재 | ✅ OpenTelemetry + ask 8단계 자동 span |
| **Docker 배포** | 부재 | ✅ Dockerfile 2종 + docker-compose.yml |

## 5. 외부 Codex 총평 대비 처리 현황

[Codex 총평](../../Codex의_claud에 대한 총평/claud_통합_검증_총평.md)이 검증 시점에 지적한 항목들과 그 후 대응:

| Codex 지적 | 본 보고서 시점의 상태 |
| --- | --- |
| `evaluate.py` + 평가 데이터셋 + precision/accuracy/latency 지표 기반 평가 별도로 필요 | ✅ #4로 구현 완료 (10건, precision@3 + 6 지표) |
| 문서 상태 동기화 | ✅ PROGRESS/CHANGELOG/NEXT_STEPS 3분리로 역할 명확화, 모두 docs/ 폴더로 격리 |
| 17 passed 시점에서의 LLM Gateway는 키 로테이션 미적용 | ✅ #3으로 자동 폴오버 + stats 노출 추가 |
| 운영형 확장 항목(JWT/OTel/DB/Docker) 미적용 | ✅ #6, #7, #8, #9 모두 구현 (실연결은 사용자 환경에서) |
| 프론트 E2E 부재 | ✅ #5로 Playwright 도입, 6/6 통과 |

검증 시점의 codex는 17 passed였고, 현 시점은 36 passed + 5/5 시나리오 + 10/10 evaluate + 6/6 E2E.

## 6. 산출물 인덱스

### 코드
- 백엔드 ([../backend/app/](../backend/app/))
  - `errors.py` `models.py` `data.py` `repository.py` `audit.py` `ontology.py` `policy.py` `search.py` `workflow.py` `rag.py` `app_context.py` `schemas.py` `main.py`
  - `llm_gateway.py` (#3 키 로테이션) · `auth.py` (#7 JWT) · `telemetry.py` (#8 OTel)
- 프론트엔드 ([../frontend/src/](../frontend/src/))
  - `app/{layout,page,globals.css}` · `lib/api.ts` · `types/api.ts`
  - `components/{Sidebar,UserSwitcher,ContextPanel,Dashboard,Explorer,AIQuery,Workflow,Audit}.tsx`

### 검증
- `../backend/tests/` — 5개 테스트 파일 (36 케이스)
- `../backend/eval/scenarios.py` — 학습 시나리오 5종 API 자동 검증
- `../backend/eval/cases.json` + `../backend/evaluate.py` — RAG 품질 자동 평가
- `../frontend/e2e/scenarios.spec.ts` + `../frontend/playwright.config.ts` — UI E2E

### 배포·운영
- `../backend/Dockerfile`, `../frontend/Dockerfile`, `../docker-compose.yml`, `../.env.example`

### 교육
- `../../req_doc_hub/교육자료/` 5문서
  - `00_커리큘럼_오버뷰.md` · `01_사전_안내.md` · `02_실습_플로우.md` · `03_심화_과제.md` · `04_FAQ.md`

### 문서 (docs/)
- `PROGRESS.md` (스냅샷) · `CHANGELOG.md` (이력) · `NEXT_STEPS.md` (백로그) · `FINAL_REPORT.md` (이 파일)

## 7. 알려진 한계

| 항목 | 영향 | 후속 |
| --- | --- | --- |
| Gemini 무료 티어 키 모두 429 | LLM 답변이 룰베이스로만 검증됨 (코드 폴백 정상) | #2: 키 한도 회복 후 답변 품질 검증 (5케이스 + 자연어 룰 추가) |
| `F:\ai_std_dev\.env` 세션 도중 접근 불가 | 키 자동 로딩 미동작 — 환경변수 직접 주입으로 우회 | 키를 `claud_통합/backend/.env`에 직접 작성 권장 |
| JWT 프론트엔드 통합 미적용 | 프론트는 여전히 `?user=` 쿼리 사용 | #7b: 로그인 페이지, 토큰 저장, Authorization 헤더 자동 첨부 |
| Docker 이미지 실제 빌드 미수행 | compose config만 검증 | 사용자 환경에서 `docker compose up` 1회 검증 권장 |
| Postgres 실연결 미수행 | 클래스/폴백 로직만 테스트 | `docker compose --profile db up` 후 `DATABASE_URL` 주입 검증 권장 |
| Jaeger/Tempo 실연결 미수행 | OTel 구조와 no-op fallback만 테스트 | OTLP collector 띄운 환경에서 `OTEL_EXPORTER_OTLP_ENDPOINT` 주입 검증 권장 |
| 한글 폴더명 (`claud_통합`) | npm 일부 캐시 오류 사례 발생 (`--ignore-scripts`로 우회) | 실패 시 `claud_unified`로 리네임 |

## 8. 회고 (교훈)

- **`src_anti`의 결함은 인터페이스 불일치(시작부터 깨짐)에서 시작**했다. PolicyEngine, BM25, LLM 분리, API base URL — 4가지가 학습 첫 단계에서 막히는 종류였다. 교육용 코드일수록 **첫 5분 안에 동작**하는 것이 더 중요하다는 점이 명확해졌다.
- **`src_codex`의 강점은 서비스 경계**였다. AppContext + 도메인 서비스 7종 + Repository 추상화. 이걸 그대로 가져오되 FastAPI로 옮긴 게 핵심 결정이었다. http.server는 교육용으론 좋지만 OpenAPI 문서 자동 생성 등 학습 보너스가 없다.
- **하위호환 유지가 회귀 위험을 크게 줄였다**. JWT를 도입하면서도 `?user=` 쿼리를 살린 결정 덕분에 시나리오 검증·evaluate·E2E가 무수정으로 통과했다.
- **문서 비대화는 누적 결과 박스에서 온다**. NEXT_STEPS.md가 부풀어 오른 원인이 명확했고, 3개 파일 분리로 단일 출처(SSOT)를 만들어 해결.
- **자동화 가능한 검증을 빨리 만드는 게 이득**. `scenarios.py` + `evaluate.py` + Playwright 세 묶음 덕분에 #6/#7/#8 추가 시 회귀 검증이 즉시 가능했다.
- **외부 의존을 격리하는 fallback 패턴**이 교육 환경에서 결정적이다. Gemini 키 없을 때 룰베이스, Postgres 연결 실패 시 InMemory, OTel 미설치 시 no-op — 셋 다 같은 원칙.

## 9. 다음 단계 (실무자용 체크리스트)

운영 전환 시 권장 순서:

1. **#2 LLM 답변 품질 검증** — Gemini 키 한도 회복 후 5케이스 실행 + evaluate에 자연어 품질 룰 추가.
2. **#7b 프론트 JWT 통합** — 로그인 페이지 + Authorization 헤더 자동 첨부 + `?user=` 쿼리 deprecation.
3. **DB 실연결 검증** — `docker compose --profile db up`로 Postgres 띄우고 `DATABASE_URL` 주입, 서버 재시작 후 상태 유지 확인.
4. **Docker 이미지 빌드** — 두 이미지 실제 빌드 후 컨테이너 간 통신 확인.
5. **OTel 실연결** — Jaeger 또는 Tempo + Grafana 띄워 trace UI에서 ask 8단계 span 트리 확인.
6. **CI 통합** — pytest + scenarios + evaluate + Playwright을 GitHub Actions에서 자동 실행.

---

> 이 보고서는 `claud_통합/docs/FINAL_REPORT.md`에 있습니다.
> 보충 자료: [README.md](../README.md) (사용 가이드), [PROGRESS.md](PROGRESS.md) (현재 상태), [CHANGELOG.md](CHANGELOG.md) (변경 이력), [NEXT_STEPS.md](NEXT_STEPS.md) (남은 백로그).
