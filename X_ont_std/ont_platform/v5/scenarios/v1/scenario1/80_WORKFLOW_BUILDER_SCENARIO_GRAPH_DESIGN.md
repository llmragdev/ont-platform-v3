# Workflow Builder 기반 Scenario 1 실행 설계

작성일: 2026-06-13  
대상: ont_platform v5 Workflow Builder, Scenario 1 고객 문의 자동댓글  
목적: 시나리오 그래프를 테넌트/프로젝트별로 불러와 수정, 복제, 실행할 수 있는 구조 정의

## 1. 설계 목표

Scenario 1 자동댓글은 단순 API 호출 버튼이 아니라, Workflow Builder에서 관리되는 실행 가능한 그래프여야 한다.

운영자는 다음 흐름으로 사용한다.

```text
Workflow Home
  -> 서비스 요청 자동댓글 시나리오 선택
  -> Workflow Builder에서 그래프 로드
  -> 프로젝트 상황에 맞게 노드/조건/모드 수정
  -> 저장 또는 복제
  -> 실행
  -> 실행 이력/audit 확인
```

핵심 요구사항:

- 시나리오 그래프는 시스템 템플릿으로 제공한다.
- 각 회사/프로젝트는 템플릿을 자기 프로젝트 저장소로 복제해 사용한다.
- 복제본은 수정 가능해야 한다.
- 실행은 mock이 아니라 실제 Scenario 1 executor를 호출해야 한다.
- 모든 저장, 실행, audit은 `company_id`, `project_id` 기준으로 분리해야 한다.

## 2. 현재 구현 상태

현재 이미 있는 기반:

| 항목 | 상태 | 근거 |
| --- | --- | --- |
| TenantContext | 있음 | `X-Company-Id`, `X-Project-Id`, `X-User-Id` 헤더 |
| 프로젝트별 저장소 | 있음 | `storage/{company_id}/{project_id}` |
| WorkflowGraph 저장 | 있음 | `workflow_graphs.json` |
| WorkflowRun 이력 | 있음 | `workflow_runs/` |
| 그래프 저장/불러오기/삭제 API | 있음 | `/api/workflow-graphs` |
| Builder UI | 있음 | 그래프 편집, 저장, 실행 UI |
| Scenario 1 실제 실행 API | 있음 | `/api/extn/customer-questions/events`, `/batch/run-once` |

현재 부족한 부분:

| 항목 | 상태 |
| --- | --- |
| Scenario 1 기본 그래프 seed | 부족 |
| 시스템 템플릿과 프로젝트 복제본의 메타데이터 구분 | 부족 |
| Builder의 Run 버튼과 실제 자동댓글 executor 연결 | 부족 |
| Batch/Webhook 실행 모드 UI | 부족 |
| 실행 결과와 customer_mcp audit의 연결 | 부분 구현 |

## 3. 멀티테넌트 저장 모델

물리 저장 구조:

```text
ont_platform/v5/backend/storage/
  {company_id}/
    {project_id}/
      workflow_graphs.json
      workflow_runs/
      events/
        customer_question_events.jsonl
        customer_question_state.json
      audit/
        customer_mcp_calls.jsonl
      ontology/
      vector_db/
      uploads/
```

현재 `WorkflowGraphService`는 이미 다음 경로에 그래프를 저장한다.

```text
storage/{company_id}/{project_id}/workflow_graphs.json
```

따라서 회사 A의 프로젝트와 회사 B의 프로젝트는 같은 graph id를 사용하더라도 저장 파일이 다르므로 분리된다.

예:

```text
storage/default/proj-default/workflow_graphs.json
storage/acme/support-prod/workflow_graphs.json
storage/globex/helpdesk-poc/workflow_graphs.json
```

## 4. WorkflowGraph 메타데이터 확장

현재 그래프는 `id`, `name`, `nodes`, `edges`, `created_at`, `updated_at`, `created_by` 중심이다.

Scenario 1 실행형 그래프를 위해 다음 메타데이터를 추가한다.

```json
{
  "id": "graph-service-request-auto-reply",
  "name": "서비스 요청 자동댓글",
  "scenario_id": "scenario1",
  "scenario_version": "v1",
  "template_id": "service-request-auto-reply",
  "template_version": "1.0.0",
  "graph_kind": "scenario",
  "execution_mode": "batch",
  "runtime": {
    "executor": "scenario1.customer_question_auto_reply",
    "default_mode": "dry_run",
    "allow_post": true,
    "batch_status": "open",
    "batch_limit": 10
  },
  "tenant_scope": {
    "company_id": "default",
    "project_id": "proj-default"
  },
  "source": {
    "type": "system_template",
    "source_graph_id": null,
    "cloned_from": null
  },
  "nodes": [],
  "edges": []
}
```

필드 의미:

| Field | 의미 |
| --- | --- |
| `scenario_id` | 업무 시나리오 식별자 |
| `template_id` | 시스템 템플릿 식별자 |
| `graph_kind` | `scenario`, `custom`, `template_copy` 등 |
| `execution_mode` | `webhook`, `batch`, `manual_event`, `simulation` |
| `runtime.executor` | 실제 실행할 backend executor |
| `runtime.default_mode` | 기본 실행 모드 `dry_run` 또는 `post` |
| `tenant_scope` | 저장 당시 회사/프로젝트 |
| `source.cloned_from` | 복제 원본 그래프 |

## 5. 시스템 템플릿과 프로젝트 복제본

### 5.1 시스템 템플릿

시스템 템플릿은 제품이 제공하는 기본 시나리오이다.

권장 위치:

```text
ont_platform/v5/backend/app/config/workflow_templates/scenario1_service_request_auto_reply.json
```

특징:

- 직접 수정하지 않는다.
- 모든 프로젝트에서 복제 가능하다.
- 버전 관리 대상이다.
- 기본 노드와 executor metadata를 포함한다.

### 5.2 프로젝트 복제본

프로젝트 복제본은 실제 운영자가 수정하고 실행하는 그래프이다.

권장 저장 위치:

```text
storage/{company_id}/{project_id}/workflow_graphs.json
```

복제 시 처리:

- 새 `graph_id` 발급
- `source.cloned_from`에 원본 template id 기록
- `tenant_scope.company_id`, `tenant_scope.project_id` 기록
- `created_by`, `created_at` 기록
- 기본 실행 모드는 안전하게 `dry_run`

## 6. Scenario 1 기본 그래프

기본 노드:

```text
request_input
  -> question_normalize
  -> intent_classify
  -> knowledge_lookup
  -> evidence_gate
  -> draft_response
  -> customer_mcp_comment_create
  -> audit_write
```

분기:

```text
evidence_gate insufficient
  -> human_handoff
```

그래프 예:

```json
{
  "nodes": [
    {
      "id": "request-input",
      "type": "request_input",
      "data": {
        "label": "문의 입력",
        "source": "customer_board"
      }
    },
    {
      "id": "draft-response",
      "type": "draft_response",
      "data": {
        "label": "답변 초안 생성",
        "api": "/api/extn/customer-replies/draft"
      }
    },
    {
      "id": "post-comment",
      "type": "customer_mcp_comment_create",
      "data": {
        "label": "고객사 댓글 등록",
        "api": "/api/extn/customer-replies/post-via-mcp",
        "mode": "dry_run"
      }
    }
  ],
  "edges": [
    {"id": "e1", "source": "request-input", "target": "draft-response"},
    {"id": "e2", "source": "draft-response", "target": "post-comment"}
  ]
}
```

## 7. 실행 모델

### 7.1 현재 방식

현재 WorkflowGraph 실행 API:

```http
POST /api/workflow-graphs/{graph_id}/run
```

현재 동작:

```text
각 노드를 순회하며 mock output 생성
WorkflowRun 저장
```

### 7.2 목표 방식

목표 동작:

```text
POST /api/workflow-graphs/{graph_id}/run
  -> graph.runtime.executor 확인
  -> executor dispatch
  -> 실제 Scenario 1 API/service 호출
  -> 노드별 실행 결과 SSE emit
  -> WorkflowRun 저장
  -> customer_mcp audit 저장
```

Scenario 1 executor:

```text
scenario1.customer_question_auto_reply
```

지원 실행 타입:

| 실행 타입 | 설명 | 내부 호출 |
| --- | --- | --- |
| `simulation` | 화면 검증용 mock | 기존 mock runner |
| `manual_event` | 특정 문의 payload로 실행 | `_handle_question_event` |
| `batch` | 미처리 문의 조회 후 실행 | `_run_batch_once` |
| `webhook` | 외부 게시판이 event API 호출 | `/api/extn/customer-questions/events` |

Builder Run 버튼은 기본적으로 `graph.runtime.execution_mode`를 따른다.

## 8. API 설계

### 8.1 템플릿 목록 조회

```http
GET /api/workflow-templates
```

응답:

```json
{
  "items": [
    {
      "template_id": "service-request-auto-reply",
      "name": "서비스 요청 자동댓글",
      "scenario_id": "scenario1",
      "version": "1.0.0"
    }
  ]
}
```

### 8.2 템플릿을 프로젝트로 복제

```http
POST /api/workflow-templates/{template_id}/clone
```

Headers:

```text
X-Company-Id: default
X-Project-Id: proj-default
X-User-Id: default-user
```

Request:

```json
{
  "name": "서비스 요청 자동댓글 - 운영본",
  "default_mode": "dry_run"
}
```

Response:

```json
{
  "graph_id": "graph-abc123",
  "company_id": "default",
  "project_id": "proj-default"
}
```

### 8.3 그래프 복제

```http
POST /api/workflow-graphs/{graph_id}/clone
```

Request:

```json
{
  "name": "서비스 요청 자동댓글 - 테스트 복제본"
}
```

동작:

- 같은 프로젝트 안에 새 graph id로 복제
- `source.cloned_from`에 원본 graph id 기록

### 8.4 그래프 실행

```http
POST /api/workflow-graphs/{graph_id}/run
```

Query 또는 Body:

```json
{
  "execution_mode": "batch",
  "mode": "post",
  "limit": 10,
  "status": "open"
}
```

응답:

```text
text/event-stream
```

SSE 이벤트:

```text
node_started
node_finished
run_finished
run_failed
```

## 9. Frontend UX 설계

### 9.1 Workflow Home

표시:

- 시스템 템플릿
- 내 프로젝트 그래프
- 최근 실행 이력
- Scenario 1 quick action

필수 버튼:

- `템플릿에서 만들기`
- `불러오기`
- `복제`
- `실행`

### 9.2 Workflow Builder

상단:

- 회사/프로젝트 표시
- 그래프 이름
- 실행 모드 선택: `simulation`, `batch`, `manual_event`
- 댓글 모드 선택: `dry_run`, `post`
- 저장
- 복제
- 실행

우측 패널:

- 선택 노드 설정
- API endpoint
- mode
- retry
- timeout
- audit 여부

하단:

- 노드별 실행 결과
- WorkflowRun 이력
- customer_mcp audit link

### 9.3 Scenario 1 실행 패널

Builder 안에 전용 패널을 둔다.

필드:

| Field | 기본값 |
| --- | --- |
| `execution_mode` | `batch` |
| `status` | `open` |
| `mode` | `dry_run` |
| `limit` | `10` |
| `force_reprocess` | `false` |

버튼:

- `Dry-run 실행`
- `Post 실행`
- `최근 Audit 보기`

## 10. 권한과 거버넌스

권한:

| 작업 | 허용 역할 |
| --- | --- |
| 템플릿 조회 | Viewer 이상 |
| 프로젝트 그래프 조회 | Viewer 이상 |
| 그래프 수정/저장 | Admin, Manager |
| 그래프 복제 | Admin, Manager |
| dry_run 실행 | Admin, Manager, Operator |
| post 실행 | Admin, Operator |
| 삭제 | Admin |

안전 규칙:

- 템플릿 원본은 직접 수정 금지
- `post` 실행은 명시 선택 필요
- 기본값은 항상 `dry_run`
- 같은 `question_id`에 성공 댓글이 있으면 중복 등록 금지
- 강제 재처리는 별도 옵션 필요
- 실행 결과는 WorkflowRun과 audit 양쪽에 남김

## 11. 실행 이력과 Audit 연결

WorkflowRun:

```text
storage/{company_id}/{project_id}/workflow_runs/run-xxxx.json
```

Customer MCP audit:

```text
storage/{company_id}/{project_id}/audit/customer_mcp_calls.jsonl
```

Event/idempotency:

```text
storage/{company_id}/{project_id}/events/customer_question_events.jsonl
storage/{company_id}/{project_id}/events/customer_question_state.json
```

WorkflowRun에는 다음 필드를 추가하는 것을 권장한다.

```json
{
  "external_audit_refs": [
    {
      "type": "customer_mcp_call",
      "audit_id": "uuid",
      "request_id": "uuid",
      "question_id": "q-001"
    }
  ]
}
```

## 12. 구현 단계

### Step 1. 그래프 메타데이터 확장

- `WorkflowGraph` 타입에 `scenario_id`, `template_id`, `runtime`, `source`, `tenant_scope` 추가
- 저장 API에서 기존 그래프와 호환되게 optional 처리

### Step 2. 시스템 템플릿 파일 추가

- `workflow_templates/scenario1_service_request_auto_reply.json`
- 깨진 프론트 템플릿 문자열 정리

### Step 3. 템플릿 clone API 추가

- `/api/workflow-templates`
- `/api/workflow-templates/{template_id}/clone`
- `/api/workflow-graphs/{graph_id}/clone`

### Step 4. Scenario 1 executor 추가

- `app/services/workflow_executors/scenario1_customer_reply.py`
- 내부에서 `_run_batch_once`, `_handle_question_event`, `_post_to_customer_mcp` 재사용

### Step 5. WorkflowGraph run dispatch

- `/api/workflow-graphs/{graph_id}/run`에서 `graph.runtime.executor` 확인
- 없으면 기존 mock runner 유지
- 있으면 실제 executor 실행

### Step 6. Builder UI 보완

- 회사/프로젝트 표시
- 템플릿/프로젝트 그래프 구분
- 복제 버튼
- Scenario 1 실행 패널
- 실행 결과 요약 표시

## 13. 프로그램 영향도 및 변경 대상

이 장은 실제 구현 시 변경해야 하는 프로그램과 변경 형태를 정의한다.

### 13.1 Backend API

| Program | 현재 역할 | 변경 형태 | 상세 변경 |
| --- | --- | --- | --- |
| `backend/app/api/workflow.py` | WorkflowGraph CRUD, run SSE API | 수정 | `run_graph`가 mock 실행만 하지 않고 `graph.runtime.executor`를 보고 실제 executor로 dispatch하도록 변경 |
| `backend/app/api/workflow.py` | WorkflowGraph CRUD | 수정 | `POST /api/workflow-graphs/{graph_id}/clone` 추가 |
| `backend/app/api/workflow_templates.py` | 없음 | 신규 | 시스템 템플릿 목록 조회와 프로젝트 복제 API 추가 |
| `backend/app/api/extn/customer_questions.py` | Scenario 1 event/batch API | 유지/연동 | Workflow executor에서 `_run_batch_once`, `_handle_question_event`를 재사용할 수 있게 service layer로 분리 검토 |
| `backend/app/api/extn/customer_replies.py` | draft/post/generate-and-post API | 유지/연동 | executor에서 draft/post 기능 재사용. 필요 시 private 함수 의존을 service 함수 의존으로 정리 |
| `backend/app/main.py` | FastAPI router 등록 | 수정 | 신규 `workflow_templates` router 등록 |

권장 변경 방향:

- `workflow.py` 안에 Scenario 1 세부 로직을 직접 넣지 않는다.
- `workflow.py`는 graph load, 권한 확인, SSE stream, executor dispatch만 담당한다.
- 실제 고객 문의 처리 로직은 별도 executor/service로 분리한다.

### 13.2 Backend Service

| Program | 현재 역할 | 변경 형태 | 상세 변경 |
| --- | --- | --- | --- |
| `backend/app/services/workflow.py` | WorkflowGraphService, WorkflowService | 수정 | WorkflowGraph metadata 저장/조회 호환. `scenario_id`, `template_id`, `runtime`, `source`, `tenant_scope` 보존 |
| `backend/app/services/workflow.py` | WorkflowGraphService | 수정 | `clone_graph(ctx, graph_id, name)` 메서드 추가 |
| `backend/app/services/workflow_template_service.py` | 없음 | 신규 | 시스템 템플릿 파일 로드, 목록 조회, 프로젝트 그래프 복제 |
| `backend/app/services/workflow_executors/__init__.py` | 없음 | 신규 | executor registry/export |
| `backend/app/services/workflow_executors/base.py` | 없음 | 신규 | executor 공통 interface 정의 |
| `backend/app/services/workflow_executors/mock_runner.py` | 현재 `workflow.py` 내부 mock | 신규/이관 | 기존 mock 실행 로직을 executor로 분리 |
| `backend/app/services/workflow_executors/scenario1_customer_reply.py` | 없음 | 신규 | Scenario 1 batch/manual event 실행. 고객 게시판 댓글 등록까지 처리 |
| `backend/app/services/customer_question_state.py` | event/idempotency 저장 | 유지/확장 | workflow_run_id, graph_id, run_id reference 저장 가능하도록 확장 |

권장 executor interface:

```python
class WorkflowExecutor(Protocol):
    async def run(
        self,
        graph: dict,
        ctx: TenantContext,
        options: dict,
    ) -> AsyncIterator[dict]:
        ...
```

executor event 예:

```json
{
  "event": "node_finished",
  "node_id": "post-comment",
  "status": "success",
  "output": {
    "question_id": "q-001",
    "external_comment_id": "comment-123",
    "audit_id": "uuid"
  }
}
```

### 13.3 Backend Config / Template

| Program | 현재 역할 | 변경 형태 | 상세 변경 |
| --- | --- | --- | --- |
| `backend/app/config/workflow_templates/` | 없음 | 신규 디렉터리 | 시스템 템플릿 JSON 저장 |
| `backend/app/config/workflow_templates/scenario1_service_request_auto_reply.json` | 없음 | 신규 | Scenario 1 기본 그래프 정의 |
| `backend/app/config/workflow.json` | 기존 action workflow config | 영향 없음/검토 | 기존 승인 워크플로우와 Scenario graph template의 책임 분리 |

시스템 템플릿은 코드 배포물로 취급한다. 운영자가 수정하는 프로젝트 복제본은 `storage/{company_id}/{project_id}/workflow_graphs.json`에 저장한다.

### 13.4 Frontend API Client / Types

| Program | 현재 역할 | 변경 형태 | 상세 변경 |
| --- | --- | --- | --- |
| `frontend/src/types/api.ts` | WorkflowGraph 타입 정의 | 수정 | `scenario_id`, `template_id`, `runtime`, `source`, `tenant_scope` optional field 추가 |
| `frontend/src/lib/api.ts` | backend API client | 수정 | `workflowTemplates.list`, `workflowTemplates.clone`, `workflowGraphs.clone`, `workflowGraphs.run` options 지원 |
| `frontend/src/lib/workflowTemplates.ts` | 프론트 내장 템플릿 | 수정/축소 | 시스템 템플릿을 backend API에서 받도록 전환. 임시 mock 템플릿은 fallback으로만 유지 |

권장 타입 확장:

```ts
export interface WorkflowGraph {
  id: string;
  name: string;
  scenario_id?: string;
  scenario_version?: string;
  template_id?: string;
  template_version?: string;
  graph_kind?: "scenario" | "custom" | "template_copy";
  execution_mode?: "simulation" | "batch" | "manual_event" | "webhook";
  runtime?: {
    executor?: string;
    default_mode?: "dry_run" | "post";
    allow_post?: boolean;
    batch_status?: string;
    batch_limit?: number;
  };
  tenant_scope?: {
    company_id: string;
    project_id: string;
  };
  source?: {
    type?: "system_template" | "project_graph";
    source_graph_id?: string | null;
    cloned_from?: string | null;
  };
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}
```

### 13.5 Frontend UI

| Program | 현재 역할 | 변경 형태 | 상세 변경 |
| --- | --- | --- | --- |
| `frontend/src/components/WorkflowHome.tsx` | Workflow 진입 화면 | 수정 | 시스템 템플릿과 프로젝트 그래프를 분리 표시. 회사/프로젝트 scope 표시 |
| `frontend/src/components/TemplateGallery.tsx` | 템플릿 선택/복제 | 수정 | 프론트 내장 템플릿 대신 `/api/workflow-templates` 조회. clone API 호출 |
| `frontend/src/components/WorkflowGraph.tsx` | Builder/runner 화면 | 수정 | 복제 버튼, 실행 옵션 패널, Scenario 1 실행 결과 표시 |
| `frontend/src/components/WorkflowRunHistory.tsx` | 실행 이력 표시 | 수정 | `external_audit_refs`, question_id, comment_id 표시 |
| `frontend/src/components/Sidebar.tsx` | 메뉴 | 영향 낮음 | 명칭이 깨진 경우 정리. 기능 변경은 필수 아님 |

WorkflowGraph UI 변경 상세:

- 상단에 현재 `company_id`, `project_id` 표시
- 그래프 kind badge 표시: `System Template Copy`, `Project Graph`, `Custom`
- `복제` 버튼 추가
- 실행 옵션 추가:
  - `execution_mode`: `simulation`, `batch`, `manual_event`
  - `mode`: `dry_run`, `post`
  - `limit`
  - `status`
  - `force_reprocess`
- `post` 실행 시 확인 dialog 표시
- 실행 결과에 `checked`, `started`, `skipped`, `errors` 표시

### 13.6 Storage / Data Migration

| Program/Data | 현재 역할 | 변경 형태 | 상세 변경 |
| --- | --- | --- | --- |
| `storage/{company_id}/{project_id}/workflow_graphs.json` | 프로젝트별 그래프 저장 | 호환 확장 | 기존 그래프가 metadata 없이도 로드되도록 optional 처리 |
| `storage/{company_id}/{project_id}/workflow_runs/*.json` | 실행 이력 | 호환 확장 | `external_audit_refs`, `options`, `executor` 필드 추가 |
| `storage/{company_id}/{project_id}/events/customer_question_state.json` | idempotency | 확장 | `graph_id`, `run_id`, `workflow_run_id` 저장 |
| `storage/{company_id}/{project_id}/audit/customer_mcp_calls.jsonl` | MCP 호출 감사 | 유지/확장 | metadata에 `graph_id`, `run_id` 포함 |

마이그레이션 원칙:

- 기존 `workflow_graphs.json`을 강제 변환하지 않는다.
- 저장 시 새 metadata를 포함하되, 읽을 때 없으면 기본값을 채운다.
- 기존 mock graph는 `runtime.executor`가 없으므로 mock runner로 계속 실행한다.

### 13.7 Tests

| Program | 변경 형태 | 테스트 내용 |
| --- | --- | --- |
| `backend/tests/test_workflow_templates.py` | 신규 | 템플릿 목록 조회, 템플릿 clone, tenant/project 저장 분리 |
| `backend/tests/test_workflow_graph_clone.py` | 신규 | 프로젝트 그래프 복제, source metadata, 원본 불변 |
| `backend/tests/test_workflow_graph_scenario1_run.py` | 신규 | graph runtime executor가 Scenario 1 batch를 호출하는지 |
| `backend/tests/test_customer_question_events.py` | 확장 | workflow_run_id, graph_id가 state/audit에 남는지 |
| Frontend component/e2e | 신규/확장 | 템플릿 복제, Builder 로드, 옵션 선택, 실행 결과 표시 |

필수 회귀 테스트:

- 기존 mock WorkflowGraph 실행이 계속 동작해야 한다.
- 기존 `workflow_graphs.json`에 새 metadata가 없어도 list/get/save/run이 깨지면 안 된다.
- 다른 `X-Company-Id`, `X-Project-Id`로 저장한 그래프가 서로 보이면 안 된다.

### 13.8 API Compatibility

기존 API는 유지한다.

```text
GET /api/workflow-graphs
GET /api/workflow-graphs/{graph_id}
POST /api/workflow-graphs
POST /api/workflow-graphs/{graph_id}/run
```

추가 API:

```text
GET /api/workflow-templates
POST /api/workflow-templates/{template_id}/clone
POST /api/workflow-graphs/{graph_id}/clone
```

`POST /api/workflow-graphs/{graph_id}/run`은 기존처럼 body 없이 호출해도 동작해야 한다. body가 없고 `runtime.executor`도 없으면 기존 mock 실행을 유지한다.

### 13.9 영향도 요약

| 영역 | 영향도 | 이유 |
| --- | --- | --- |
| Backend workflow API | 높음 | run dispatch와 clone API 추가 |
| Backend workflow service | 높음 | metadata, clone, template load 필요 |
| Scenario 1 extn API | 중간 | 기존 기능 재사용. service layer 정리 필요 |
| Frontend Workflow Builder | 높음 | 실행 옵션, clone, scenario 결과 표시 필요 |
| Frontend Template Gallery | 중간 | backend template 기반으로 전환 |
| Storage schema | 중간 | JSON optional 확장. 파괴적 migration 없음 |
| 기존 승인 워크플로우 | 낮음 | 기존 API 유지 시 영향 제한 |
| customer_mcp/customer_board | 낮음 | 계약 유지. 변경 불필요 |

## 14. 완료 기준

- 신규 프로젝트에서 Scenario 1 기본 그래프가 보인다.
- 그래프를 불러와 노드/설정을 수정할 수 있다.
- 수정본을 저장할 수 있다.
- 그래프를 복제할 수 있다.
- 같은 graph id라도 company/project가 다르면 저장소가 분리된다.
- Builder에서 `dry_run` 실행이 가능하다.
- Builder에서 명시적으로 `post` 실행하면 고객 게시판 댓글이 등록된다.
- 실행 결과가 WorkflowRun에 남는다.
- MCP 호출 audit이 `customer_mcp_calls.jsonl`에 남는다.
- 이미 처리된 문의는 중복 등록되지 않는다.
