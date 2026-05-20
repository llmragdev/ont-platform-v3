# Sprint 02 — 인프라 강화

> **기간**: 2026-05-11
> **상태**: ✅ 완료
> **이전 스프린트**: [Sprint 01](sprint_01.md)

---

## 1. 스프린트 목표

- [x] Playwright E2E 자동 테스트로 프론트 회귀 감지 체계 구축
- [x] JWT 인증 도입 (백엔드 + 프론트 통합)
- [x] PostgreSQL Repository + Docker compose 패키징
- [x] OpenTelemetry 관측성 레이어 추가
- [x] 교육 가이드 문서 완성

---

## 2. 백로그 → 완료 항목

| ID | 항목 | 구분 | 결과 |
|----|------|------|------|
| S-01 | Playwright E2E 테스트 6종 (NEXT #5) | test | ✅ |
| S-02 | PostgreSQL Repository + resolve_default() (NEXT #6) | infra | ✅ |
| S-03 | JWT 인증 백엔드 — 표준 라이브러리 구현 (NEXT #7) | feature | ✅ |
| S-04 | 프론트엔드 JWT 통합 (NEXT #7b) | feature | ✅ |
| S-05 | OpenTelemetry 관측성 (NEXT #8) | infra | ✅ |
| S-06 | Docker compose 패키징 (NEXT #9) | infra | ✅ |
| S-07 | 교육 가이드 5문서 (NEXT #10) | docs | ✅ |
| S-08 | WorkflowGraph Phase 1~3 (React Flow + SSE + 거버넌스 통합) | feature | ✅ |

---

## 3. 기술 변경 사항

### 신규 파일

| 파일 경로 | 역할 |
|-----------|------|
| `backend/app/auth.py` | JWT (PBKDF2 + HS256) — 표준 라이브러리만 |
| `backend/app/telemetry.py` | OTel span 래퍼 + no-op 폴백 |
| `backend/app/workflow_graph.py` | WorkflowGraphService CRUD |
| `backend/app/workflow_graph_engine.py` | Kahn 위상정렬 + SSE 실행 엔진 |
| `frontend/src/lib/auth.ts` | 토큰 localStorage 관리 |
| `frontend/src/components/LoginPanel.tsx` | 로그인 폼 + 4종 데모 계정 |
| `frontend/e2e/scenarios.spec.ts` | Playwright 6종 시나리오 |
| `backend/Dockerfile` + `frontend/Dockerfile` | 컨테이너 이미지 |
| `docker-compose.yml` | backend + frontend + postgres 프로필 |

### 변경 파일

| 파일 경로 | 변경 내용 요약 |
|-----------|---------------|
| `backend/app/main.py` | `POST /api/auth/login`, WorkflowGraph 라우트 추가 |
| `backend/app/app_context.py` | telemetry span 적용, WorkflowGraphEngine 주입 |
| `backend/app/policy.py` | `can_manage_workflow_graph()` 추가 |
| `frontend/src/lib/api.ts` | Authorization 헤더 자동 첨부 (JWT/데모 모드 분기) |

---

## 4. 발견된 문제

### 🐛 버그

| # | 현상 | 원인 | 해결 방법 |
|---|------|------|-----------|
| B-01 | WorkflowGraph condition 노드에서 `eval()` 사용 검토 | 보안 취약점 | 화이트리스트 미니 파서 구현, `eval/exec` 완전 금지 |
| B-02 | Playwright E2E에서 백엔드 상태 오염 | 테스트 간 데이터 공유 | `/api/system/reset` 엔드포인트 + `AppContext.reset()` 신규 추가 |
| B-03 | JWT 외부 라이브러리(PyJWT) 교육 환경 의존성 문제 | 패키지 설치 실패 가능성 | 표준 라이브러리(`hmac`, `hashlib`, `base64`)만으로 HS256 직접 구현 |

### 🚧 블로커

없음

---

## 5. 개선된 점

- **테스트 완성도**: pytest 17 → 59 (+42건), E2E 6/6 추가
- **실행 엔진**: 클라이언트 시뮬레이션 → 서버 SSE 실시간 스트림
- **거버넌스 연결**: 워크플로우 그래프 노드에 PolicyEngine 동일 적용
- **관측성**: OTel span으로 `ask()` 8단계 자동 추적 가능
- **배포**: Docker compose 한 명령으로 전체 스택 실행
- **보안**: condition 노드 eval 금지 → 화이트리스트 파서

---

## 6. 테스트 결과

| 테스트 종류 | Sprint 01 | Sprint 02 | 비고 |
|------------|-----------|-----------|------|
| pytest | 17/17 | 59/59 | +42건 (auth 11, repository 5, telemetry 3, workflow_graph 7+11+5) |
| 시나리오 자동 검증 | 5/5 | 5/5 | 회귀 없음 |
| evaluate.py | 10/10 | 10/10 | 회귀 없음 |
| E2E (Playwright) | 없음 | 6/6 PASS | 신규 |
| 회귀 건수 | 0 | 0 | |

---

## 7. 다음 스프린트 제안 백로그

- [ ] 온톨로지 스키마 외부화 (Python 하드코딩 제거) (High)
- [ ] Vector RAG 통합 (PDF 업로드 + 임베딩) (High)
- [ ] sensitive 필드 자동 마스킹 정책 (Medium)

---

## 8. 회고

### 잘 된 것 👍
- JWT를 외부 라이브러리 없이 구현 → 교육 환경 이식성 향상
- Playwright E2E로 "클릭 수동 확인" 단계를 자동화
- WorkflowGraph SSE로 실시간 실행 시각화 완성

### 아쉬운 것 👎
- Docker 이미지 빌드는 검증하지 못함 (사용자 환경 의존)
- PostgreSQL 연결 실패 폴백 로직은 있지만 실제 DB 연동 테스트 미진행

### 다음에 시도할 것 🔁
- 온톨로지를 코드가 아닌 데이터(JSON)로 관리하는 구조로 전환
