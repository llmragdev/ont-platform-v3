# 03. 운영 표준 및 개발 가이드 (SOP & Development Guide)

## 1. 스프린트 운영 표준 (Sprint Standard)

모든 개발은 에자일 스프린트 단위로 진행하며, 다음의 표준을 준수합니다.

### 1.1 완료 정의 (Definition of Done: DoD)
기능이 '완료'되었다고 판단하기 위한 최소 조건입니다.
- [ ] 소스 코드가 Git 저장소의 대상 브랜치에 Merge됨.
- [ ] 해당 기능에 대한 Unit Test(`pytest`) 작성 및 pass.
- [ ] `docs/sprints`에 관련 결과 및 회고 기록.
- [ ] API 변경 시 `schemas.py` 및 Swagger(OpenAPI) 문서 업데이트.
- [ ] 프론트엔드 빌드 오류 및 린트 오류 없음.

### 1.2 수용 기준 (Acceptance Criteria)
각 기능(Issue/Ticket)은 사전에 합의된 수용 기준을 통과해야 합니다.
- **예시 (멀티테넌트)**:
    - `user_a` (Company A)가 `user_b` (Company B)의 문서 목록 API를 호출했을 때 `403` 에러가 발생하는가?
    - 로그아웃 후 재접속 시 이전 테넌트 컨텍스트가 유지되는가?

---

## 2. 개발 환경 및 기술 스택

### 2.1 Backend
- **Framework**: FastAPI (Asynchronous)
- **Security**: PyJWT (JWT based RBAC)
- **Testing**: Pytest, TestClient
- **Logging**: Loguru (Audit & Error tracing)

### 2.2 Frontend
- **Framework**: Next.js (App Router)
- **State Management**: React Context (User/Tenant context)
- **Visualization**: React Flow (Knowledge Graph)
- **Styling**: Vanilla CSS (Premium design system)

---

## 3. 통합 테스트 및 배포 프로세스 (CI/CD)

### 3.1 자동화 테스트 파이프라인
1. **Linter**: `flake8` / `black` (Code style check)
2. **Backend Test**: `pytest` (API & Logic check)
3. **Frontend Test**: `npm run build` (Build check)
4. **Integration Test**: `evaluate.py` (LLM answer quality check)

### 3.2 배포 전 체크리스트
- [ ] `.env.example`에 신규 환경 변수가 반영되었는가?
- [ ] `ontology.default.json` 스키마 변경 사항이 하위 호환성을 유지하는가?
- [ ] DB 마이그레이션(JSON/File 구조 변경) 스크립트가 준비되었는가?

---

## 4. 품질 지표 (Quality Metrics)

- **Test Coverage**: 최소 80% 이상 유지.
- **Response Time**: 일반 API 200ms 이내, LLM 질의 5s 이내 (Streaming 적용).
- **Security Score**: 모든 엔드포인트에 Auth 미들웨어 적용 필수.
