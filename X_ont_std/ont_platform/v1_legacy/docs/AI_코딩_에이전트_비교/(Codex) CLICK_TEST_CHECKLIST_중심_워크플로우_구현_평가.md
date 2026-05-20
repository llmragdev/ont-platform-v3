# CLICK_TEST_CHECKLIST 중심 워크플로우 구현 평가

작성일: 2026-05-12  
평가 대상: `E:\ontology_edu\claud_통합`  
중심 문서: `docs/CLICK_TEST_CHECKLIST.md`  
참조 문서: `docs/DEMO_SCENARIO.md`, `docs/기타_분석/WORKFLOW_SOURCES_REVIEW.md`, `docs/FINAL_REPORT.md`, `docs/NEXT_STEPS.md`

## 1. 결론

`CLICK_TEST_CHECKLIST.md` 기준으로 실행했을 때 워크플로우 핵심 기능은 잘 구현된 것으로 평가한다.

특히 이번 구현은 기존의 `승인 워크플로우` 화면을 넘어서, React Flow 기반 그래프 캔버스와 FastAPI 서버 실행 엔진을 연결했다는 점이 중요하다. 사용자가 Start, LLM, HTTP, Condition, ApproveOrder, RiskAssess, End 노드를 배치하고, 저장한 뒤, 서버 측 SSE 스트리밍으로 단계별 실행 결과를 확인할 수 있다.

따라서 현재 상태는 단순 UI 목업이 아니라 **실행 가능한 그래프형 워크플로우 데모**로 볼 수 있다.

다만 완성도 평가는 다음처럼 구분하는 것이 정확하다.

- 교육/시연용 완성도: 높음
- 워크플로우 그래프 기능 완성도: 높음
- 온톨로지/정책 결합 시연 완성도: 높음
- 운영용 범용 워크플로우 엔진 완성도: 중간
- 문서/문자열 정합성: 보강 필요

## 2. 확인된 구현 근거

### 2.1 백엔드 API

`backend/app/main.py`에는 워크플로우 그래프 관련 API가 추가되어 있다.

- `GET /api/workflow-graphs`
- `GET /api/workflow-graphs/{graph_id}`
- `POST /api/workflow-graphs`
- `DELETE /api/workflow-graphs/{graph_id}`
- `POST /api/workflow-graphs/{graph_id}/run`
- `GET /api/workflow-graphs/{graph_id}/runs`
- `GET /api/workflow-runs/{run_id}`

특히 실행 API는 `StreamingResponse`와 `text/event-stream`을 사용한다. 즉, 실행 완료 후 결과만 받는 구조가 아니라 노드 실행 상태를 단계별로 흘려보내는 구조다.

### 2.2 그래프 저장 모델

`backend/app/workflow_graph.py`는 그래프 CRUD와 권한 검사를 담당한다.

확인된 장점:
- 그래프 ID는 `wfg-...` 형태로 발급된다.
- 노드는 `id`, `type`, `position`, `data`를 가진다.
- 엣지는 `source`, `target`, `label`을 가진다.
- 저장, 조회, 삭제 권한이 `PolicyEngine`과 연결된다.
- 저장 시 감사 로그 `WORKFLOW_GRAPH_SAVED`가 남는다.

이 구조는 `WORKFLOW_SOURCES_REVIEW.md`에서 비교했던 외부 워크플로우 소스들의 장점 중 `저장 모델`, `React Flow 노드/엣지 구조`, `권한 연동`을 프로젝트 맥락에 맞게 흡수한 형태다.

### 2.3 서버 측 실행 엔진

`backend/app/workflow_graph_engine.py`는 이번 기능의 핵심이다.

확인된 장점:
- Kahn 알고리즘 기반 위상 정렬로 실행 순서를 결정한다.
- cycle이 있으면 `cycle_detected`로 실패 처리한다.
- `AsyncGenerator`로 `run_started`, `node_started`, `node_finished`, `run_finished` 이벤트를 yield한다.
- 실행 이력은 `workflow_runs`, `workflow_run_steps`에 저장된다.
- 감사 로그 `GRAPH_RUN_STARTED`, `GRAPH_NODE_SUCCESS`, `GRAPH_RUN_FINISHED`가 남는다.
- 노드별 실행 권한이 `NODE_TYPE_POLICY`로 분리되어 있다.
- `approve_order`, `risk_assess` 도메인 노드는 기존 Ontology/PolicyEngine과 연결된다.

이 지점 때문에 현재 워크플로우는 단순한 "그림 그리기"가 아니라 실제 도메인 정책을 실행하는 그래프가 되었다.

### 2.4 프론트엔드 그래프 UI

`frontend/src/components/WorkflowGraph.tsx`는 React Flow 기반 화면을 제공한다.

확인된 장점:
- 좌측 노드 팔레트 제공
- 캔버스에서 노드 배치와 연결 가능
- 우측 속성 패널 제공
- 그래프 저장/불러오기/삭제 가능
- 실행 버튼으로 서버 SSE 실행 호출
- 노드 상태가 `running`, `success`, `error`로 변한다.
- 하단 결과 테이블에 노드별 실행 결과, duration, output이 표시된다.

스크린샷의 흐름도 이 구현과 일치한다. 특히 LLM 노드가 실제 응답을 생성하고, RiskAssess 노드가 `risk_tier`와 recommendation을 출력하는 점은 `CLICK_TEST_CHECKLIST.md`의 기대와 잘 맞는다.

## 3. CLICK_TEST_CHECKLIST 기준 평가

### 3.1 기본 5개 시나리오

기존 5개 시나리오는 여전히 유효하다.

- 정상 승인
- 고위험 거부
- 금액 임계 분기
- 지역 거부
- 속성 마스킹

이 부분은 기존 `eval.scenarios`, Playwright E2E와도 연결되어 있으며, 그래프 기능이 추가된 뒤에도 프로젝트의 기본 정책 시연 축을 유지한다.

### 3.2 워크플로우 그래프 WG-1

평가: 통과

확인 사항:
- React Flow 캔버스가 있다.
- Start, LLM, HTTP, Condition, ApproveOrder, RiskAssess, End 노드가 있다.
- 노드를 추가하고 연결할 수 있다.
- 저장 후 `wfg-...` ID가 발급된다.
- 저장된 그래프를 다시 불러올 수 있다.

의미:
- 외부 비교 문서에서 추천했던 `prometheus5`식 팔레트/속성 패널/실행 결과 UX가 현재 프로젝트 안에 흡수되었다.

### 3.3 워크플로우 그래프 WG-2

평가: 통과

확인 사항:
- 서버 측 실행 엔진이 있다.
- SSE로 실행 이벤트를 전송한다.
- 노드 상태가 실시간으로 갱신된다.
- 실행 결과가 하단 테이블에 쌓인다.
- 감사 로그가 남는다.

의미:
- 단순 클라이언트 시뮬레이션이 아니라 서버가 실행의 기준점이다.
- 이 점은 교육용 데모의 신뢰도를 크게 올린다.

### 3.4 워크플로우 그래프 WG-3

평가: 부분 통과에서 통과에 가까움

확인 사항:
- `ApproveOrder` 도메인 노드가 있다.
- `RiskAssess` 도메인 노드가 있다.
- `ApproveOrder`는 주문 컨텍스트와 정책 엔진을 사용해 `can_approve`를 산출한다.
- `RiskAssess`는 고객 리스크 등급과 권고 메시지를 산출한다.
- 존재하지 않는 주문 ID는 `OBJECT_NOT_FOUND`로 오류 이벤트를 만든다.

의미:
- 그래프 노드가 단순 generic task가 아니라 온톨로지/정책과 연결된 도메인 노드로 확장되었다.
- 이 부분이 `claud_통합`의 가장 큰 진전이다.

주의:
- `ApproveOrder` 노드는 실제 주문 상태를 변경하지 않고 승인 가능 여부를 미리 보는 성격이다.
- 따라서 이름은 시연상 좋지만, 운영 의미로는 `CheckApproveOrder` 또는 `CanApproveOrder`에 더 가깝다.

### 3.5 JWT 로그인 모드

평가: 구현됨, 추가 검증 권장

확인 사항:
- `frontend/src/components/LoginPanel.tsx`가 있다.
- `frontend/src/lib/auth.ts`에서 token과 user를 localStorage에 저장한다.
- `NEXT_PUBLIC_AUTH_REQUIRED=true`일 때 로그인 화면을 강제할 수 있다.
- 백엔드는 `Authorization: Bearer`를 우선 사용하고, 기존 `?user=` fallback을 유지한다.

의미:
- 이전 보고서에서 남은 항목으로 보였던 프론트 JWT 통합이 상당 부분 진행되었다.

주의:
- 운영 전에는 `?user=` fallback을 데모 모드로만 제한해야 한다.
- localStorage token은 교육용으로는 충분하지만 운영 보안 수준은 아니다.

## 4. 테스트 결과

현재 백엔드 테스트는 다음과 같이 통과했다.

```text
59 passed in 3.68s
```

테스트 구성이 좋아진 점:
- 기존 API/Auth/LLM/Repository/Telemetry 테스트 유지
- `test_workflow_graph.py`로 CRUD와 권한 검증
- `test_workflow_graph_engine.py`로 위상 정렬, cycle, SSE, 실행 이력 검증
- `test_workflow_graph_wg3.py`로 ApproveOrder/RiskAssess 도메인 노드 검증

이 테스트 묶음은 `CLICK_TEST_CHECKLIST.md`의 수동 QA 항목과 꽤 잘 맞는다.

## 5. AI 코딩 에이전트 비교 관점 평가

이번 결과물은 AI 코딩 에이전트 비교 문서에 넣을 가치가 있다.

이유:
- 단순 코드 생성이 아니라 여러 소스의 장점을 조합했다.
- 기존 FastAPI 도메인 서비스와 React Flow UI를 결합했다.
- 자동 테스트와 수동 클릭 체크리스트가 함께 있다.
- "AI가 만든 화면" 수준을 넘어 "정책이 붙은 실행 엔진"까지 구현했다.

비교 문서에서 강조할 포인트:

| 평가 항목 | 현재 claud_통합 평가 |
| --- | --- |
| UI 완성도 | React Flow 기반으로 충분히 시연 가능 |
| 실행 모델 | 서버 측 AsyncGenerator + SSE로 우수 |
| 도메인 결합 | Ontology/PolicyEngine과 연결되어 강함 |
| 테스트 | 59개 pytest로 백엔드 신뢰도 높음 |
| 문서화 | 체크리스트와 데모 시나리오가 있으나 인코딩 정리 필요 |
| 운영성 | 아직 demo/fallback 성격이 남아 있음 |

에이전트별 비교 관점에서는 다음처럼 볼 수 있다.

- Antigravity 계열 장점: 시각적 UI 감각
- Prometheus 계열 장점: 실행 엔진과 팔레트/속성 패널 구조
- workflowTwo3Layer 계열 장점: 계층 분리 철학
- 현재 claud_통합 장점: 위 요소를 FastAPI 도메인 백엔드와 결합

따라서 이 문서는 `docs/AI_코딩_에이전트_비교` 아래에 두는 것이 적절하다.

## 6. 남은 개선점

### 6.1 인코딩과 한글 문자열 정리

문서와 일부 UI 문자열이 깨져 보인다.

영향:
- 기능은 동작하지만 시연/교육 자료 신뢰도가 떨어진다.
- 클릭 체크리스트를 외부에 공유하기 어렵다.

권장:
- 모든 `.md`, `.tsx`, `.py` 파일을 UTF-8로 통일한다.
- PowerShell 출력 가이드는 별도로 두되, 원본 문서는 깨지지 않게 한다.
- UI 라벨의 깨진 문자열을 우선 복구한다.

### 6.2 그래프 실행 의미 명확화

`ApproveOrder` 노드는 실제 승인 실행이 아니라 승인 가능성 평가다.

권장:
- 노드명을 `CheckApproveOrder`로 바꾸거나,
- 실제 상태 변경 노드 `ExecuteApproveOrder`를 별도로 추가한다.

현재처럼 `ApproveOrder` 이름을 유지할 경우 문서에 "상태 변경 없음, 정책 검증 노드"라고 명확히 적어야 한다.

### 6.3 조건 노드의 분기 실행

현재 조건 노드는 expression을 평가해 결과를 출력하지만, 엣지 label 또는 true/false branch를 기준으로 실행 경로를 분기하는 수준은 아직 약하다.

권장:
- Condition 노드 결과가 `true`이면 true edge만 실행
- `false`이면 false edge만 실행
- edge label 또는 data.condition을 분기 기준으로 사용

이 기능이 들어가면 그래프 워크플로우의 의미가 훨씬 강해진다.

### 6.4 HTTP 노드 보안 제한

HTTP 노드는 임의 URL을 호출할 수 있다.

교육용 localhost에서는 괜찮지만 운영 전에는 다음 제한이 필요하다.

- allowlist 기반 URL 제한
- 내부망 주소 차단 또는 명시 허용
- method 제한
- timeout과 response size 제한

### 6.5 그래프 스키마 검증 강화

현재 노드 필수 필드 검증은 있지만, 더 강한 검증이 필요하다.

권장:
- edge의 source/target이 실제 node id인지 검증
- node type별 필수 data 검증
- 중복 node id 검증
- start/end 개수 검증
- 고아 노드 처리 정책 명확화

## 7. 다음 지시 추천

클로드 코드에 추가로 지시한다면 아래 순서를 추천한다.

1. 한글 인코딩과 UI 라벨 복구
2. Graph schema validation 강화
3. Condition true/false branch 실행 구현
4. `ApproveOrder` 노드 의미 명확화 또는 실제 실행 노드 분리
5. HTTP 노드 보안 allowlist 추가
6. Playwright에 WorkflowGraph 클릭 시나리오 추가
7. `CLICK_TEST_CHECKLIST.md`를 자동화 가능한 항목과 수동 확인 항목으로 분리

짧은 지시문:

```text
CLICK_TEST_CHECKLIST.md 기준 수동 검증 결과 워크플로우 그래프 핵심 기능은 동작한다.
이제 완성도 보강을 위해 다음 작업을 해줘.

1. 문서와 UI의 깨진 한글 문자열을 UTF-8 기준으로 복구
2. workflow graph 저장 시 schema validation 강화: edge source/target 존재, 중복 node id, node type별 필수 data 검증
3. condition 노드가 true/false branch를 실제 실행 경로에 반영하도록 개선
4. ApproveOrder 노드가 현재는 승인 가능성 평가인지 실제 승인 실행인지 명확히 분리
5. HTTP 노드에 URL allowlist와 timeout/response size 제한 추가
6. Playwright에 WorkflowGraph 클릭 테스트를 추가해 CLICK_TEST_CHECKLIST의 WG-1~WG-3 일부를 자동화

기존 59개 pytest는 유지하고, 새 검증 테스트를 추가해줘.
```

## 8. 최종 평가

현재 `claud_통합`의 워크플로우 그래프 구현은 성공적이다.

가장 좋은 점은 그래프 UI, 서버 실행, 감사 로그, 온톨로지/정책 도메인 노드가 한 흐름으로 연결되었다는 점이다. 이 정도면 AI 코딩 에이전트 비교 문서에서 "단순 산출물"이 아니라 "실행 가능한 통합 기능" 사례로 정리할 가치가 충분하다.

남은 작업은 새 기능 확장보다 품질 정리와 의미 명확화다. 특히 인코딩 복구, 조건 분기, 그래프 검증 강화가 다음 단계의 핵심이다.

