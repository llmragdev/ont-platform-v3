# Claude 통합 — 변경 이력

> 작업 단위별 완료 이력입니다. 위가 최신.
> 진행 상태 요약은 [PROGRESS.md](PROGRESS.md), 미완료 백로그는 [NEXT_STEPS.md](NEXT_STEPS.md).

## 2026-05-12

### 온톨로지 재설계 Phase 5 — sensitive 자동 마스킹 ✅
**결과**: pytest **67/67 통과** (회귀 0건), 시나리오 5/5 (시나리오 5 마스킹 포함) · evaluate 10/10 유지
- **목표**: `mask_object` if-else 코드 제거 → 스키마 `sensitive: true` 메타데이터 + 외부 정책 파일로 자동 마스킹
- 신규: [backend/app/config/policy.default.json](../../backend/app/config/policy.default.json)
  - `masking_rules` 배열: role × object_type × fields → mask_value 매핑
  - Viewer: `object_type: "*"`, `mask_all_sensitive: true` → 모든 타입의 sensitive 필드 → "Restricted"
  - Analyst/AccountManager: Customer.contract_terms → "Custom discount rate: ***"
  - FinanceManager/Admin: 규칙 없음 → 원본 노출
- 변경: [backend/app/policy.py](../../backend/app/policy.py)
  - `load_masking_policy()` — policy.default.json 로드, `POLICY_MASKING_PATH` 환경변수로 교체 가능
  - `PolicyEngine.__init__(audit, schema?)` — ontology schema 주입, sensitive_fields 캐시 초기화
  - `mask_object()` — if-else 완전 제거. 스키마 sensitive_fields + masking_rules 조합으로 처리
  - `can_manage_ontology()` / `assert_can_manage_ontology()` 추가 (Phase 3에서 추가됨)
- 변경: [backend/app/app_context.py](../../backend/app/app_context.py)
  - `PolicyEngine(self.audit, schema=self.ontology.schema)` — schema 주입
  - `reset()` 도 동일하게 적용
- **확장성 검증**: 새 객체 타입에 `sensitive: true` 속성 추가 + policy.default.json에 규칙 한 줄 → 코드 수정 없이 자동 마스킹.

### 온톨로지 재설계 Phase 4 — 온톨로지 그래프 캔버스 UI ✅
**결과**: Next.js 빌드 대상. 백엔드 API는 Phase 3에서 구현 완료.
- **목표**: 객체-관계를 React Flow 캔버스로 시각화 (워크플로우 그래프와 별개 메뉴)
- 신규: [frontend/src/components/OntologyExplorerCanvas.tsx](../../frontend/src/components/OntologyExplorerCanvas.tsx)
  - 커스텀 노드 타입 `OntologyNodeComp` — 객체 타입별 색상 (Customer=blue, Order=amber, Product=green)
  - `/api/ontology/graph` + `/api/ontology/schema` 동시 로딩
  - 노드 클릭 → 우측 패널에 속성 + incoming/outgoing 관계 목록 + 관계별 삭제(✕) 버튼
  - "+ 관계 추가" 버튼 → 모달 (rel_type + source/target 드롭다운) → POST /api/ontology/relationships
  - 범례 (타입별 색상 뱃지), 토스트 알림, 새로고침 버튼
- 변경: [frontend/src/types/api.ts](../../frontend/src/types/api.ts)
  - `OntologyGraphNode`, `OntologyGraphEdge`, `OntologyGraph`, `OntologySchema` 타입 추가
- 변경: [frontend/src/lib/api.ts](../../frontend/src/lib/api.ts)
  - `api.ontology.schema()`, `api.ontology.graph()`, `api.ontology.createRelationship()`, `api.ontology.deleteRelationship()` 추가
- 변경: [frontend/src/components/Sidebar.tsx](../../frontend/src/components/Sidebar.tsx)
  - `ViewKey`에 `"ontology-graph"` 추가, 사이드바 메뉴 항목 추가 (explorer 바로 아래)
- 변경: [frontend/src/app/page.tsx](../../frontend/src/app/page.tsx)
  - `titles` 맵에 `"ontology-graph"` 항목 추가
  - `{view === "ontology-graph" && <OntologyExplorerCanvas user={currentUserKey} />}` 렌더링 추가

### 온톨로지 재설계 Phase 3 — 관계 CRUD API + 액션 스키마 통합 ✅
**결과**: pytest **67/67 통과** (회귀 0건), 시나리오 5/5 · evaluate 10/10 유지
- **목표**: 관리자가 관계 인스턴스 추가/삭제, 스키마의 `action_types`가 워크플로우 노드 팔레트에 자동 반영
- 변경: [backend/app/config/ontology.default.json](../../backend/app/config/ontology.default.json)
  - `action_types` 배열 추가: ApproveOrder / RejectOrder / HoldOrder / RiskAssess
  - 각 액션에 `node_type_key`, `exposed_as_graph_node`, `required_role` 메타데이터
- 변경: [backend/app/models.py](../../backend/app/models.py)
  - `RelationshipInstance`에 `rel_id` 필드 추가 (default: `rel-<uuid10>`) — 삭제 API 기반
- 변경: [backend/app/ontology.py](../../backend/app/ontology.py)
  - `get_full_graph()` — 전체 객체+관계를 React Flow 형식(`nodes`/`edges`)으로 반환. 타입별 열 배치
  - `add_relationship_instance(rel_type, source_id, target_id, values?)` — 스키마 검증 후 `raw["ontology_relationships"]` 영속화
  - `delete_relationship_instance(rel_id)` — in-memory + raw 동시 제거
  - `_build_registry()` — 시작 시 `raw["ontology_relationships"]` 복원
- 변경: [backend/app/policy.py](../../backend/app/policy.py)
  - `can_manage_ontology(user, action)` / `assert_can_manage_ontology()` 추가. write=AccountManager+, delete=Admin
- 변경: [backend/app/schemas.py](../../backend/app/schemas.py)
  - `RelationshipCreateRequest` 추가 (relationship_type, source_id, target_id, values?)
- 변경: [backend/app/main.py](../../backend/app/main.py)
  - `GET /api/ontology/schema` — 스키마 전체 반환
  - `GET /api/ontology/graph` — React Flow nodes+edges
  - `POST /api/ontology/relationships` — 관계 추가 (AccountManager+)
  - `DELETE /api/ontology/relationships/{rel_id}` — 관계 삭제 (Admin)
  - 감사 로그: `ONTOLOGY_RELATIONSHIP_CREATED`, `ONTOLOGY_RELATIONSHIP_DELETED`
- 변경: [backend/app/workflow_graph_engine.py](../../backend/app/workflow_graph_engine.py)
  - `_NODE_TYPE_POLICY_DEFAULT` (모듈 상수) + `_build_node_policy_from_schema(schema)` 함수 분리
  - `WorkflowGraphEngine.__init__`에서 `ontology.schema`의 `action_types[exposed_as_graph_node=true]`를 읽어 `_node_type_policy` 동적 생성
  - 이제 JSON에 새 `action_type` 추가 + `exposed_as_graph_node: true`만 켜면 노드 팔레트에 자동 등장
- **하위호환 보장**: 기존 WG-3 도메인 노드(approve_order, risk_assess) 기본값 폴백 유지. 회귀 0건.

### 온톨로지 재설계 Phase 2 — Generic Graph Traversal + object_context 일반화 ✅
**결과**: pytest **67/67 통과** (회귀 0건), 시나리오 5/5 · evaluate 10/10 유지
- **목표**: `get_order_context` 같은 Order 전용 함수 대신 어떤 객체 타입이든 동작하는 범용 컨텍스트 조회 + RAG 질의 추출 일반화
- 변경: [backend/app/ontology.py](../../backend/app/ontology.py)
  - `OntologyRegistry.find_relationships(source_id?, target_id?, relationship_name?)` — 방향·타입 모두 옵션인 범용 탐색 추가
  - `OntologyService.object_context(object_id)` — 어떤 객체든 `{object, object_type, outgoing, incoming}` 반환
  - `get_order_context()` — 하위호환 유지, 내부 로직 그대로 (Order 교차검증 포함)
- 변경: [backend/app/rag.py](../../backend/app/rag.py)
  - `extract_object_ids(question, schema?)` — `schema`가 있으면 `id_prefix`로 동적 정규식 생성 (`customer_id`, `order_id`, `product_id` 등). schema 없으면 하위호환 고정 정규식 사용
  - `build_search_query()` / `build_prompt()` — `dict.get()` 방어 코드로 범용 컨텍스트 수용
- 변경: [backend/app/app_context.py](../../backend/app/app_context.py) `ask()`
  - `extract_object_ids(question, schema)` 호출로 Product ID 등도 감지
  - `order_id` 있으면 기존 Order 경로(get_order_context + available_actions) 유지
  - `order_id` 없으면 `object_context()` 범용 경로 — Customer/Product/기타 중심 질문 처리
  - 감사 로그 `primary_type` 동적으로 기록
- **하위호환 보장**: 기존 Order 중심 시나리오 / evaluate 케이스 무수정. 회귀 0건.
- **확장성 검증**: 새 객체 타입 추가 시 JSON 스키마에 `id_prefix` 정의만 하면 자동으로 질문에서 ID 추출 + object_context 범용 조회 동작.

### 온톨로지 재설계 Phase 1 — 스키마 외부화 ✅
**결과**: pytest **67/67 통과** (기존 59 + 신규 schema 8), 시나리오 5/5 · evaluate 10/10 · Playwright **6/6 회귀** 모두 유지
- **배경**: 안티그래피티 평가서 + Codex-통합/Antigravity-통합 두 외부 구현을 비교해 작성한 [docs/note/온톨로지_재설계_보고서.md](note/온톨로지_재설계_보고서.md)의 Phase 1 실행
- **목표**: Python 코드에 하드코딩되어 있던 객체/관계 타입 정의를 JSON 스키마로 분리. 코드 수정 없이 새 객체 타입 추가 가능
- 신규: [backend/app/config/ontology.default.json](../../backend/app/config/ontology.default.json) — Customer/Product/Order + PLACED_ORDER/ORDER_CONTAINS_PRODUCT를 JSON으로
  - 스키마 메타데이터 포함: `id_prefix`, `icon`, `display_name`, `reverse_display_name`, `cardinality`, 속성의 `sensitive`/`searchable`/`enum_values`
- 변경: [backend/app/models.py](../../backend/app/models.py) `ObjectType` / `PropertyDefinition` / `RelationshipDefinition` 에 default 값 가진 메타 필드 추가 (하위호환 보장)
- 변경: [backend/app/ontology.py](../../backend/app/ontology.py)
  - `_build_registry()` 의 Python 하드코딩 제거 → `load_ontology_schema()` JSON 로딩으로 교체
  - `SCHEMA_TYPE_MAP`: 11개 타입 문자열 → Python type 매핑 (string/enum/number/float/list/bool 등)
  - `ONTOLOGY_SCHEMA_PATH` 환경변수로 스키마 교체 가능
  - 잘못된 스키마(미정의 type / 미정의 source/target 객체 타입)는 `INVALID_SCHEMA` 오류
- 신규: [backend/tests/test_ontology_schema.py](../../backend/tests/test_ontology_schema.py) — 8 케이스
  - 기본 스키마 로딩 / 메타데이터(id_prefix, sensitive, enum_values, cardinality, reverse_display_name) 확인
  - 잘못된 type, 미정의 관계 source/target → INVALID_SCHEMA
  - 파일 누락 → INVALID_SCHEMA
  - ONTOLOGY_SCHEMA_PATH 환경변수로 Contract 타입 추가 후 자동 등록 확인
  - object_types() API 응답 형식 유지
- **하위호환 보장**: 기존 모든 호출자(workflow / policy / RAG / scenarios / evaluate / Playwright) 무수정. 회귀 0건.
- **확장성 검증**: 새 객체 타입(`Contract` 같은) 추가는 JSON 파일에 한 항목만 넣으면 됨. Python 코드 수정 불필요.

### NEXT_STEPS #2 — Gemini 실제 답변 품질 검증 ✅
**결과**: 5케이스 실행, Gemini 실응답 3건 / 의도된 도메인 오류 2건. 한국어 자연스러움 / 근거 인용 / 환각 없음 모두 ✅.
- 신규: [docs/기타_분석/LLM_EVAL.md](기타_분석/LLM_EVAL.md) — 5케이스 응답 본문 + 평가표 + 발견 사항 + 개선 후보
- **중요 발견**: 기본 모델 `gemini-2.0-flash-001`이 신규 사용자에게 404 NOT_FOUND. [llm_gateway.py](../../backend/app/llm_gateway.py)의 `DEFAULT_MODEL`을 `gemini-2.5-flash`로 갱신
- Latency: 3~12초 (Gemini API 평균 범위, 평균 8.4초)
- 키 로테이션 작동 확인: 4개 키 중 GEMINI_API_KEY 우선 사용, 다른 키 429/404 발생해도 자동 폴오버
- 응답 형식: `Decision / Evidence / Required follow-up` 템플릿 정확히 준수 → evaluate.py 형식 룰 추가 후보
- 약점: 정책이 명확히 통과인 케이스에서 "추가 검토" 권장하는 보수적 편향 — 프롬프트 보강 후보

### NEXT_STEPS #7b — 프론트엔드 JWT 통합 ✅
**결과**: 빌드 OK (145KB), E2E **6/6 회귀 통과** (하위호환 유지)
- 신규: [frontend/src/lib/auth.ts](../../frontend/src/lib/auth.ts) — 토큰 localStorage 보관 + getToken/setToken/getStoredUser/clearSession
- 신규: [frontend/src/components/LoginPanel.tsx](../../frontend/src/components/LoginPanel.tsx) — 로그인 폼 + 4종 데모 계정 빠른선택
- 변경: [frontend/src/lib/api.ts](../../frontend/src/lib/api.ts) — 토큰 있으면 `Authorization: Bearer` 자동 첨부, 없으면 `?user=` 쿼리 (하위호환)
- 변경: [frontend/src/components/UserSwitcher.tsx](../../frontend/src/components/UserSwitcher.tsx) — `authMode="jwt"` 시 로그아웃 버튼 모드, `"demo"` 시 기존 셀렉트
- 변경: [frontend/src/app/page.tsx](../../frontend/src/app/page.tsx) — 마운트 시 토큰 감지 → JWT 모드 자동 진입, `NEXT_PUBLIC_AUTH_REQUIRED=true` 환경변수 시 로그인 화면 강제
- 신규: `api.login(email, password)` 클라이언트 메서드
- **하위호환 보장**: 기본은 데모 모드(셀렉터). 로그인 시 JWT 모드로 전환. Playwright E2E 6/6 무수정 통과 — 시연 시나리오 영향 없음
- 데모 계정 4종: kim.ops@example.com(analyst) / finance.lead@example.com(finance) / viewer@example.com(viewer) / admin@example.com(admin)

### WorkflowGraph Phase 3 (WG-3) — 거버넌스 통합 + 도메인 노드 ✅
**결과**: pytest **59/59 통과** (54 + WG-3 5케이스), 빌드 OK, E2E 6/6 회귀
- [backend/app/workflow_graph_engine.py](../../backend/app/workflow_graph_engine.py)에 추가:
  - **노드 타입별 권한 정책** `NODE_TYPE_POLICY` — role 화이트리스트
    - start/end: 모든 사용자, condition/llm: Analyst+, http/approve_order: AccountManager+, risk_assess: Analyst+
  - `_check_node_permission(user, node_type)` — 실행 전 강제 검증, 거부 시 FORBIDDEN
  - **도메인 노드 2종** 추가:
    - `approve_order` — OntologyService + PolicyEngine 호출. 주문 컨텍스트 + 가능한 액션 + can_approve 플래그 반환 (실제 상태 전이는 일으키지 않음)
    - `risk_assess` — 고객 리스크 등급 평가 + 등급별 권고 (Low/Medium/High/Restricted)
- [backend/app/app_context.py](../../backend/app/app_context.py) — `WorkflowGraphEngine`에 `ontology`/`policy` 주입
- 프론트:
  - 팔레트에 도메인 노드 2개 추가 (ApproveOrder · RiskAssess)
  - 속성 패널에 `order_id` / `customer_id` 입력 필드 추가
- 신규 테스트: [backend/tests/test_workflow_graph_wg3.py](../../backend/tests/test_workflow_graph_wg3.py) — 5케이스
  - approve_order: Low risk → can_approve=true / High risk → false
  - risk_assess: viewer 마스킹 + finance 원본
  - viewer http 노드 권한 거부
  - 존재하지 않는 order_id → 응답에 OBJECT_NOT_FOUND 포함
- **이제 그래프가 우리 거버넌스 체계와 결합됨**: 같은 PolicyEngine 4축(역할/지역/리스크/금액)이 그래프 노드 안에서도 동일하게 작동

### WorkflowGraph Phase 2 — 서버 실행 + SSE ✅
**결과**: pytest **54/54 통과** (기존 43 + 신규 engine 11), Next.js 빌드 OK (143KB 동일), Playwright **6/6 회귀**
- 신규 백엔드:
  - [backend/app/workflow_graph_engine.py](../../backend/app/workflow_graph_engine.py) — Kahn 위상정렬 + AsyncGenerator 이벤트 스트림
    - 노드 핸들러 5종: `start`/`end`(즉시), `llm`(LLMGateway 키 로테이션 재활용), `http`(httpx async), `condition`(미니 파서, eval 금지)
    - condition 표현식: `"true"`/`"false"`, `lhs op rhs` (op ∈ {==, !=, >, <, >=, <=}), 알 수 없으면 안전하게 false
  - [backend/app/workflow_graph.py](../../backend/app/workflow_graph.py)에 `list_runs`, `get_run`, `assert_can_run` 추가
  - [backend/app/main.py](../../backend/app/main.py)에 라우트 3개 추가:
    - `POST /api/workflow-graphs/{id}/run` — **SSE 스트림** (`text/event-stream`), 이벤트: run_started/node_started/node_finished/run_finished/run_failed
    - `GET /api/workflow-graphs/{id}/runs` — 그래프별 실행 이력
    - `GET /api/workflow-runs/{run_id}` — 실행 상세 (run + steps 한 번에)
  - 영속화: `raw["workflow_runs"]` + `raw["workflow_run_steps"]` — Repository 추상화 그대로 사용
  - 감사 로그: GRAPH_RUN_STARTED / GRAPH_NODE_SUCCESS|ERROR / GRAPH_RUN_FINISHED
- 신규 프론트:
  - [frontend/src/components/WorkflowGraph.tsx](../../frontend/src/components/WorkflowGraph.tsx) — **클라이언트 시뮬레이션 제거**, fetch + ReadableStream으로 SSE 직접 파싱
  - 노드 색상이 서버에서 푸시되는 단계별 이벤트로 변경 (idle → running → success/error)
  - 결과 테이블에 서버 실제 결과(latency, error 포함) 누적
  - "먼저 워크플로우를 저장한 뒤 실행하세요" 가드 추가 (id 없으면 실행 불가)
- 신규 테스트: [backend/tests/test_workflow_graph_engine.py](../../backend/tests/test_workflow_graph_engine.py) — 11 케이스
  - 단위(6): topo simple/cycle/empty + condition true/false/equality/numeric/unsafe-default-false
  - API(5): SSE 완료 / 이력 조회 / 사이클 거부 / viewer 권한 거부 / 감사 이벤트 기록
- 권한 (Phase 1에서 정의된 정책 재활용):
  - run = AccountManager+ (Viewer는 403)
  - 실행 이력 조회 = read 권한 (모든 인증 사용자)
- 보안 결정:
  - **eval/exec 금지**: condition은 화이트리스트 미니 파서. 알 수 없는 토큰/문법은 거부
  - LLM/HTTP 노드는 PolicyEngine을 통과한 사용자만 실행 가능
  - HTTP 노드 응답은 처음 500자만 저장 (페이로드 폭주 방지)
- /docs에서 직접 시연 가능: 워크플로우 저장 후 `POST /api/workflow-graphs/{id}/run` Try it out → SSE 응답이 한 번에 누적되어 표시

### WorkflowGraph Phase 1 — React Flow 캔버스 ✅
**결과**: pytest **43/43 통과** (기존 36 + 신규 graph 7), Next.js 빌드 OK (143KB First Load), Playwright **6/6 회귀 통과**
- **배경**: 사용자 요구 — React Flow로 노드 배치·그리기, 실행 단계 표시, 노드별 결과 테이블, 워크플로우 DB 저장.
- **기존 결재 워크플로우(WorkflowService)와 별도 도메인으로 분리** — 36/5/10/6 회귀 영향 없음.
- 신규 백엔드:
  - [backend/app/workflow_graph.py](../../backend/app/workflow_graph.py) — `WorkflowGraphService` (CRUD + 권한)
  - [backend/app/policy.py](../../backend/app/policy.py) `can_manage_workflow_graph()` — read=전체, write/run=AccountManager+, delete=Admin
  - [backend/app/schemas.py](../../backend/app/schemas.py) `WorkflowGraphRequest` — **/docs에 예제 2개 자동 채움** (사용자 요구 충족)
  - [backend/app/main.py](../../backend/app/main.py) — `/api/workflow-graphs` GET/POST + `/{id}` GET/DELETE
  - 저장은 Repository 추상화 재활용 → InMemory → JsonFile → Postgres 자동 폴백 (사용자 요구 b)
- 신규 프론트:
  - 의존성: `reactflow ^11.11.4` 추가
  - [frontend/src/components/WorkflowGraph.tsx](../../frontend/src/components/WorkflowGraph.tsx) — 좌측 팔레트 + 중앙 React Flow 캔버스 + 우측 속성 패널 + 하단 결과 테이블
  - 노드 타입 5종: Start / End / LLM / HTTP / Condition (사용자 요구 b: 범용 노드)
  - 실행 시 클라이언트 측 위상정렬 → 노드별 status (idle→running→success/error) 색상 변경 + 결과 테이블 누적 (Phase 2에서 서버 SSE로 교체 예정)
  - 워크플로우 저장/불러오기/새로/삭제 + 목록 셀렉트 박스
  - [frontend/src/components/Sidebar.tsx](../../frontend/src/components/Sidebar.tsx) — 새 메뉴 "워크플로우 그래프"
- 신규 테스트: [backend/tests/test_workflow_graph.py](../../backend/tests/test_workflow_graph.py) — 7 케이스 (저장/조회/업데이트/목록정렬/viewer 권한/Admin 삭제/잘못된 페이로드)
- **사용자 결정사항 (Phase 1)**:
  - 노드 타입 1차 셋: **(b) 범용 (LLM/HTTP/Condition + Start/End)**
  - 저장 위치: **(b) Repository 추상화로 InMemory→JsonFile→Postgres 자동 폴백**
  - 실행 권한: **(c) 권한 정책 (역할별 차등)**
  - prometheus5 코드: **(a) 패턴만 참고, 새로 짜기** — 한 줄도 복사 안 함
- **Phase 2 예정** (NEXT_STEPS에 추가): 서버 측 위상정렬 실행 엔진 + SSE 진행률 푸시 + workflow_runs / workflow_run_steps DB 영속화

### NEXT_STEPS #8 — OpenTelemetry 관측성 ✅
**결과**: pytest **36/36 통과** (기존 33 + 신규 telemetry 3건), 시나리오/evaluate/E2E 회귀 없음
- 신규: [backend/app/telemetry.py](../backend/app/telemetry.py) — 의존성 없을 시 자동 no-op fallback
  - `setup(app)` — FastAPI auto-instrumentation + OTLP exporter 자동 설정
  - `span(name, **attrs)` 컨텍스트 매니저 — `with span("rag.build_prompt", q=...)` 형태
  - 환경변수: `OTEL_ENABLED` (기본 true, false면 강제 비활성), `OTEL_EXPORTER_OTLP_ENDPOINT` (Jaeger/Tempo/Collector), `OTEL_CONSOLE_EXPORTER` (디버그용)
- 변경: [backend/app/main.py](../backend/app/main.py) — `telemetry.setup(app)` 호출, `/api/health.telemetry_enabled` 추가
- 변경: [backend/app/app_context.py](../backend/app/app_context.py)의 `_step()` 헬퍼가 8단계 ask 파이프라인을 자동으로 span으로 감쌈 (`ask.질문에서_객체_후보_추출` 등)
- 신규: [backend/tests/test_telemetry.py](../backend/tests/test_telemetry.py) — 3 케이스 (no-op span, OTEL_ENABLED=false 처리, setup return)
- requirements.txt / environment.yml: `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`, `opentelemetry-exporter-otlp-proto-http` (선택 의존성)
- 사용 예:
  ```powershell
  $env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318"
  python -m uvicorn app.main:app --port 8000
  # → Jaeger UI에서 /api/ask trace가 8단계 span 트리로 보임
  ```

### NEXT_STEPS #7 — JWT 인증 (백엔드) ✅
**결과**: pytest **33/33 통과** (기존 22 + 신규 auth 11건), 시나리오 5/5 · evaluate 10/10 회귀 통과
- 신규: [backend/app/auth.py](../backend/app/auth.py) — 표준 라이브러리만으로 PBKDF2-HMAC-SHA256(200K) + HS256 JWT 구현 (외부 라이브러리 의존 없음)
  - `hash_password` / `verify_password` — `pbkdf2_sha256$ITER$SALT$HASH` 포맷
  - `issue_token` / `decode_token` — 만료/서명 검증 포함
  - `current_user_key` FastAPI dependency — Authorization 헤더 우선, `?user=` 쿼리 폴백 (하위호환 유지)
- 신규 라우트: `POST /api/auth/login` (email + password → access_token + Bearer)
- 신규 스키마: [LoginRequest](../backend/app/schemas.py)
- 데이터 시드: 4명 사용자에 평문 password 추가 → AppContext 초기화 시 자동으로 pbkdf2 해시로 변환 후 영속 저장
- 신규: [backend/tests/test_auth.py](../backend/tests/test_auth.py) — 11 케이스 (hash/verify, JWT roundtrip/만료/위조, 로그인 성공/실패, 헤더 우선/쿼리 폴백/잘못된 토큰)
- 환경변수: `JWT_SECRET` (기본 교육용 비밀, 운영 전 반드시 교체), `JWT_TTL_SECONDS` (기본 3600)
- **하위호환 보장**: 기존 `?user=analyst` 쿼리는 그대로 동작 → 시나리오 자동 검증, evaluate, Playwright E2E 모두 무수정 통과
- 데모 계정:
  - kim.ops@example.com / analyst (AccountManager)
  - finance.lead@example.com / finance (FinanceManager)
  - viewer@example.com / viewer (Viewer)
  - admin@example.com / admin (Admin)
- 프론트엔드 통합(로그인 페이지·토큰 저장·Authorization 헤더 자동 첨부)은 별도 후속 항목으로 NEXT_STEPS에 남김 → 큰 변화라 회귀 위험 격리

### NEXT_STEPS #6 — PostgreSQL Repository ✅
**결과**: pytest **22/22 통과** (기존 17 + 신규 Repository 5건)
- 신규: [backend/app/repository.py](../backend/app/repository.py)에 `PostgresDataRepository` 추가 (`psycopg[binary]` 의존, JSONB 한 행 스냅샷)
- 신규: 같은 파일에 `resolve_default()` 헬퍼 추가 — `DATABASE_URL` → Postgres, 없으면 `ONTOLOGY_DATA_PATH` → JsonFile, 최후 InMemory
- 변경: [backend/app/app_context.py](../backend/app/app_context.py)가 `resolve_default()` 사용으로 단순화
- 신규: [backend/tests/test_repository.py](../backend/tests/test_repository.py) — 5 케이스 (InMemory 폴백, JsonFile, Postgres 연결 실패 폴백, 클래스 import 가능, JsonFile roundtrip)
- `requirements.txt` / `environment.yml`에 `psycopg[binary]>=3.2` 추가 (선택 의존성)
- `docker-compose.yml`의 `postgres` 프로필을 활성화하면 즉시 연결 가능: `docker compose --profile db up`
- 안전장치: Postgres 연결 실패 시 자동 InMemory 폴백 + 콘솔 경고로 교육 환경 보호

### NEXT_STEPS #9 — Docker compose 패키징 ✅
**결과**: `docker compose config` 문법 검증 OK, 회귀 pytest 17/17 통과.
- 신규: [backend/Dockerfile](../backend/Dockerfile) (python:3.11-slim, uvicorn)
- 신규: [backend/.dockerignore](../backend/.dockerignore) (venv, pytest cache, eval 산출물 제외)
- 신규: [frontend/Dockerfile](../frontend/Dockerfile) (node:20-alpine multistage build)
- 신규: [frontend/.dockerignore](../frontend/.dockerignore)
- 신규: [docker-compose.yml](../docker-compose.yml) — backend + frontend + 선택적 postgres (profile=`db`)
- 신규: [.env.example](../.env.example) — compose 환경변수 템플릿
- backend 컨테이너에 healthcheck 추가 (`/api/health` 폴링), frontend는 backend healthy 후 기동
- 실행: `docker compose up` (Postgres 포함 시 `docker compose --profile db up`)
- 검증 시점에는 이미지 빌드까지는 수행하지 않음 — 사용자 환경에서 실행 확인 필요

### NEXT_STEPS #10 — 교육 가이드 ✅
**결과**: 강사용 5문서 작성 (커리큘럼 + 사전 안내 + 실습 + 심화 과제 + FAQ)
- 신규: [req_doc_hub/교육자료/00_커리큘럼_오버뷰.md](../req_doc_hub/교육자료/00_커리큘럼_오버뷰.md) — 4시간 시간 배분, 학습 목표 5개, 평가 방법
- 신규: [req_doc_hub/교육자료/01_사전_안내.md](../req_doc_hub/교육자료/01_사전_안내.md) — conda env 셋업, Gemini 키 연결, 흔히 막히는 7가지
- 신규: [req_doc_hub/교육자료/02_실습_플로우.md](../req_doc_hub/교육자료/02_실습_플로우.md) — 시나리오 5종 클릭 흐름 + 8단계 ask 파이프라인 코드 매핑
- 신규: [req_doc_hub/교육자료/03_심화_과제.md](../req_doc_hub/교육자료/03_심화_과제.md) — 6개 과제 (Invoice 객체 추가, RequestRevision 액션, 가격대 필터, 마스킹 확장, evaluate 케이스 확장, SQLite Repository)
- 신규: [req_doc_hub/교육자료/04_FAQ.md](../req_doc_hub/교육자료/04_FAQ.md) — 환경/백엔드/프론트/코드/학습 16개 Q&A

### NEXT_STEPS #5 — Playwright 프론트 E2E ✅
**결과**: 시나리오 5종 + 헬스 배지 = **6/6 PASS** (~12초)
- 신규: [frontend/playwright.config.ts](../frontend/playwright.config.ts) — webServer 자동 기동(포트 3100), baseURL 자동
- 신규: [frontend/e2e/scenarios.spec.ts](../frontend/e2e/scenarios.spec.ts) — `beforeEach`에서 `/api/system/reset` 호출로 테스트 격리
- 백엔드 [POST /api/system/reset](../backend/app/main.py) + `AppContext.reset()` 신규 — 교육 데모 중 초기화 용도로도 활용 가능
- `package.json`: `test:e2e`, `test:e2e:headed` 스크립트 추가
- `@playwright/test ^1.45.0` + Chromium 바이너리만 설치
- 실행 방법:
  ```powershell
  # 터미널 1
  cd backend && python -m uvicorn app.main:app --port 8000
  # 터미널 2
  cd frontend && npm run test:e2e
  ```

### NEXT_STEPS #4 — evaluate.py RAG 자동 평가 ✅
**결과**: **10/10 PASS, mean precision@3 = 1.0**
- 신규: [backend/evaluate.py](../backend/evaluate.py) — CLI 평가기
- 신규: [backend/eval/cases.json](../backend/eval/cases.json) — 평가 케이스 10건 (정상승인/고위험/금액임계/관계불일치/객체없음/계약/리스크/finance전용/viewer필터)
- 신규: [backend/eval/evaluate-20260511-234146.json](../backend/eval/evaluate-20260511-234146.json) — 첫 실행 결과
- 지표 6종: detection_ok, precision_at_3, action_match, error_match, latency_ms, llm_provider
- 요약 통계: pass_rate, mean_precision_at_3, p50/p95 latency, gemini_success_rate, fallback_warning_count
- 실행: `cd backend && python evaluate.py --json`
- 개선 후보: 케이스 20개 이상 확장, Gemini 복구 후 자연어 품질 룰 추가

### NEXT_STEPS #3 — LLM Gateway 키 로테이션 ✅
**결과**: 17/17 pytest 통과 (API 11 + LLM Gateway 6 신규)
- 업그레이드: [backend/app/llm_gateway.py](../backend/app/llm_gateway.py)
  - `_collect_keys()`가 `GEMINI_API_KEY` + `GEMINI_API_KEY1~4` 자동 수집(중복 제거)
  - 429/RESOURCE_EXHAUSTED 감지 시 다음 키로 자동 폴오버
  - 키별 `success`/`quota_fail`/`other_fail` 카운터 → `/api/health.llm.stats` 노출
  - 응답에 `key_used` 필드 추가
  - 모든 키 실패 시 룰베이스 폴백 + `warning`에 최근 3개 오류
- 신규: [backend/tests/test_llm_gateway.py](../backend/tests/test_llm_gateway.py) — 6 케이스 (collect/no_genai/first_key/rotation/all_fail/no_results)

### NEXT_STEPS #1 — 학습 시나리오 API 자동 검증 ✅
**결과**: **5/5 PASS** (~수십 ms)
- 신규: [backend/eval/scenarios.py](../backend/eval/scenarios.py) + [backend/eval/__init__.py](../backend/eval/__init__.py)
- 시나리오 5종: 정상 승인 / 고위험 거부 / 금액 임계 분기 / 지역 거부 / 속성 마스킹
- 결과 JSON: [backend/eval/results-20260511-233143.json](../backend/eval/results-20260511-233143.json)
- 실행: `cd backend && python -m eval.scenarios --json`
- **주의**: API 레벨 검증만. 브라우저 UI 시각 검토는 사람 몫 → #5에서 보강됨

### Step E — End-to-End 검증 ✅
- 두 서버 동시 가동 (uvicorn:8000 + Next.js dev:3000)
- `/api/objects/orders/O001/context?user=analyst` 정상 응답 확인 (order=O001 Submitted 3200, customer Alpha Manufacturing, actions=[ApproveOrder, RejectOrder, HoldOrder])

### Step D — 최상위 문서 ✅
- 신규: [README.md](../README.md) — 실행 방법, 학습 시나리오 5종, API 매핑, 23-codex 평가 항목 해결 현황
- 신규: [NEXT_STEPS.md](NEXT_STEPS.md) — 추가 작업 백로그 10개

### Step C — conda 환경 파일 ✅
- 신규: [backend/environment.yml](../backend/environment.yml) — `claud_be` (python 3.11 + pip 의존성)
- 신규: [frontend/environment.yml](../frontend/environment.yml) — `claud_fe` (nodejs 20)

### Step B — Next.js 프론트엔드 ✅
- `npm install --ignore-scripts` (386 packages) + `npm run build` 성공
- 신규: `package.json`, `tsconfig.json`, `next.config.js`, `tailwind.config.ts`, `postcss.config.js`
- 신규: `.env.local.example`, `.gitignore`
- 신규: `src/app/{layout,page,globals.css}`
- 신규: `src/lib/api.ts` — 백엔드 호출 클라이언트 + 도메인 오류 매핑
- 신규: `src/types/api.ts` — 응답 타입
- 신규 컴포넌트 8종: Sidebar, UserSwitcher, ContextPanel, Dashboard, Explorer, AIQuery, Workflow, Audit

### Step A — 백엔드 (FastAPI + 도메인 서비스) ✅
**결과**: pytest 11/11 통과, uvicorn 가동, Gemini 호출 시도 + 폴백 검증
- 신규 conda env `claud_be` (python 3.11)
- 신규 디렉토리 [backend/app/](../backend/app/) — codex 서비스 구조를 FastAPI로 이식
  - `errors.py`, `models.py`, `data.py`, `repository.py`, `audit.py`
  - `ontology.py` — OntologyRegistry + OntologyService
  - `policy.py` — PolicyEngine (역할 + 지역 + 마스킹 + 액션 권한)
  - `search.py` — BM25 (IDF/k1/b) + 권한 필터
  - `workflow.py` — WorkflowEngine + 5 액션 + 7 전이
  - `llm_gateway.py` — Gemini SDK + 룰베이스 폴백 (#3에서 키 로테이션으로 업그레이드)
  - `rag.py` — extract_object_ids + RAGService
  - `app_context.py` — 서비스 조립 + `ask()` 8단계 파이프라인
  - `schemas.py`, `main.py` — FastAPI 라우트, CORS, `.env` 자동 로딩
- 신규: `requirements.txt`, `pytest.ini`, `.env.example`
- 신규: [backend/tests/test_api.py](../backend/tests/test_api.py) — 11 케이스 (health, me, 마스킹, 권한, 관계 불일치, ask, workflow, audit)

### 분석/평가 문서 작성 ✅
- `req_doc_hub/평가/` 폴더에 src_anti vs src_codex 비교 보고서 작성
- 통합 결합 방향 도출: "src_anti UI + src_codex Backend"

### 통합 결정 ✅
- 신규 폴더 `claud_통합/` 생성
- 의사결정 기록 ([PROGRESS.md](PROGRESS.md) §1):
  - 폴더명: `claud_통합` (한글)
  - 프론트엔드: Next.js 14 (App Router, TypeScript, Tailwind)
  - 가상환경: conda 두 개 (`claud_be`, `claud_fe`)
  - LLM: Gemini, `google-genai` SDK
  - 참고 구현: `F:\ai_std_dev\ai_std_dev5\src\core\utility\geminiAdapter.py`
  - 구조 방침: src_codex 서비스 구조 → FastAPI 이식, src_anti UI 레이아웃 → Next.js 재구현

### 문서 구조 분리 ✅
- 문서 비대화 문제 해결: `CHANGELOG.md`(이력) / `PROGRESS.md`(스냅샷) / `NEXT_STEPS.md`(백로그) 3개 파일로 역할 분리
