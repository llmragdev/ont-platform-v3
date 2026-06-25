# Customer MCP Call Spec

작성일: 2026-06-12

## 1. 개요

이 문서는 v5 solution backend가 고객사 MCP 중계 서버(`customer_mcp`)를 호출하는 API 계약이다.

P0 범위:

```text
LLM 경로로 댓글 메시지 생성
  -> customer_mcp 호출
  -> customer_mcp가 customer_board API 호출
```

고객사 MCP 서버는 고객사 개발/운영 영역이다. v5는 고객사 MCP 서버를 호출하는 client adapter까지만 책임진다.

## 2. 서버 구성

| Server | Directory | Port | Role |
| --- | --- | ---: | --- |
| solution backend | `ont_platform/v5/backend` | 8001 | workflow, LLM draft, customer MCP client adapter |
| solution frontend | `ont_platform/v5/frontend` | 3002 | dashboard and operation UI |
| customer_mcp | `s1_customer_mcp` | 8080 | receives MCP-style calls and calls customer API |
| customer_board | `s1_customer_board` | 8090 | mock customer board API/UI with SQLite |

## 3. Base URL

Local development:

```text
http://localhost:8080
```

Config key:

```text
CUSTOMER_MCP_BASE_URL=http://localhost:8080
```

## 4. Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "service": "customer_mcp"
}
```

## 5. Create Comment Tool

P0에서 필수로 지원할 tool은 하나다.

```http
POST /mcp/tools/comment.create
```

### 5.1 Dry-run Request

`mode` 기본값은 `dry_run`이다.

```json
{
  "request_id": "uuid",
  "company_id": "demo-company",
  "project_id": "demo-project",
  "mode": "dry_run",
  "tool": "comment.create",
  "arguments": {
    "question_id": "q-001",
    "thread_id": "thread-001",
    "post_id": "q-001",
    "message": "LLM 경로로 생성된 댓글 메시지",
    "author": "ontology-workflow"
  },
  "metadata": {
    "workflow_run_id": "run-001",
    "source": "ont_platform_v5",
    "generated_by": "llm_webhook"
  }
}
```

### 5.2 Dry-run Response

```json
{
  "request_id": "uuid",
  "status": "dry_run",
  "tool": "comment.create",
  "result": {
    "external_comment_id": null,
    "external_thread_id": "q-001",
    "message": "LLM 경로로 생성된 댓글 메시지"
  },
  "error": null
}
```

### 5.3 Post Request

실제 등록은 `mode`를 명시적으로 `post`로 지정할 때만 수행한다.

```json
{
  "request_id": "uuid",
  "company_id": "demo-company",
  "project_id": "demo-project",
  "mode": "post",
  "tool": "comment.create",
  "arguments": {
    "question_id": "q-001",
    "thread_id": "thread-001",
    "post_id": "q-001",
    "message": "LLM 경로로 생성된 댓글 메시지",
    "author": "ontology-workflow"
  },
  "metadata": {
    "workflow_run_id": "run-001",
    "source": "ont_platform_v5",
    "generated_by": "llm_webhook"
  }
}
```

### 5.4 Post Response

```json
{
  "request_id": "uuid",
  "status": "success",
  "tool": "comment.create",
  "result": {
    "external_comment_id": "comment-123",
    "external_thread_id": "q-001",
    "url": "http://localhost:8090/posts/q-001#comment-123"
  },
  "error": null
}
```

## 6. Error Response

```json
{
  "request_id": "uuid",
  "status": "error",
  "tool": "comment.create",
  "result": null,
  "error": {
    "code": "BOARD_API_ERROR",
    "message": "customer_board 호출 실패",
    "retryable": true
  }
}
```

권장 error code:

| Code | Meaning | Retryable |
| --- | --- | --- |
| `INVALID_REQUEST` | required field missing or invalid | false |
| `AUTH_FAILED` | authentication failed | false |
| `BOARD_API_ERROR` | customer_board API failed | true |
| `BOARD_TIMEOUT` | customer_board timeout | true |
| `TOOL_NOT_FOUND` | unsupported tool | false |
| `INTERNAL_ERROR` | unexpected customer_mcp error | true |

## 7. Required Rules

- v5 must call only `customer_mcp`.
- v5 must not call `customer_board` directly.
- `request_id` must be returned unchanged.
- `mode` defaults to `dry_run`.
- `post` mode must be explicitly requested.
- P0 supports only `comment.create`.
- `company_id` and `project_id` are required for audit/logging.
- customer_mcp should log inbound request and outbound customer_board result.

## 8. Optional P1 Endpoints

These are useful later but not required for P0.

```http
GET /mcp/tools/question.list?status=open
GET /mcp/tools/question.get?question_id=q-001
```

