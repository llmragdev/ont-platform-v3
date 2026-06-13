# Scenario 1 Integration Smoke Test Result

작성일: 2026-06-12

## 1. 테스트 범위

v5 solution backend가 공식 스펙에 따라 `customer_mcp`를 호출하는지 확인했다.

공식 스펙:

- `20_CUSTOMER_MCP_CALL_SPEC.md`

테스트 대상:

- v5 backend: `http://127.0.0.1:8001`
- customer_mcp: `http://localhost:8080`
- customer_board: `http://localhost:8090`

## 2. 사전 상태

고객사 mock infra는 이미 실행 중인 상태로 확인했다.

```text
GET http://localhost:8080/health
=> 200 {"status":"ok","service":"customer_mcp"}
```

Codex는 고객사 프로세스(`8080`, `8090`)를 시작하거나 종료하지 않았다.

## 3. v5 Backend

Codex가 테스트를 위해 v5 backend만 임시 실행했다.

```powershell
cd E:\ontology_edu\X_ont_std\ont_platform\v5\backend
python -m uvicorn app.main:app --port 8001
```

테스트 후 v5 backend 프로세스는 종료했다.

## 4. 테스트 1: post-via-mcp dry_run

Endpoint:

```http
POST /api/extn/customer-replies/post-via-mcp
```

Request:

```json
{
  "request_id": "codex-dryrun-001",
  "question_id": "q-001",
  "reply_message": "Codex dry-run integration test",
  "mode": "dry_run",
  "post_id": "q-001",
  "author": "ontology-workflow"
}
```

Result:

```json
{
  "request_id": "codex-dryrun-001",
  "status": "dry_run",
  "tool": "comment.create",
  "result": {
    "external_comment_id": null,
    "external_thread_id": "q-001",
    "message": "Codex dry-run integration test"
  },
  "error": null,
  "status_code": 200
}
```

판정: PASS

## 5. 테스트 2: post-via-mcp post

Endpoint:

```http
POST /api/extn/customer-replies/post-via-mcp
```

Request:

```json
{
  "request_id": "codex-post-001",
  "question_id": "q-001",
  "reply_message": "Codex post integration test",
  "mode": "post",
  "post_id": "q-001",
  "author": "ontology-workflow"
}
```

Result:

```json
{
  "request_id": "codex-post-001",
  "status": "success",
  "tool": "comment.create",
  "result": {
    "external_comment_id": "comment-ed10550c",
    "external_thread_id": "q-001",
    "url": "http://localhost:8090/posts/q-001#comment-comment-ed10550c"
  },
  "error": null,
  "status_code": 200
}
```

판정: PASS

주의: 이 테스트는 customer_board mock DB에 실제 테스트 댓글 1건을 생성했다.

## 6. 테스트 3: generate-and-post dry_run

Endpoint:

```http
POST /api/extn/customer-replies/generate-and-post
```

Result:

```json
{
  "draft": {
    "request_id": "codex-generate-dryrun-001",
    "question_id": "q-001",
    "confidence": 0.5,
    "source": "llm_webhook",
    "intent": "descriptive"
  },
  "mcp": {
    "request_id": "codex-generate-dryrun-001",
    "status": "dry_run",
    "tool": "comment.create",
    "error": null,
    "status_code": 200
  }
}
```

판정: PASS

주의: 현재 draft 생성은 기존 v5 hybrid/LLM 경로를 사용한다. 근거가 없으면 fallback 답변이 생성될 수 있다.

## 7. Audit

Audit 파일이 생성되었다.

```text
ont_platform/v5/backend/storage/default/proj-default/audit/customer_mcp_calls.jsonl
```

## 8. 최종 판정

Scenario 1 P0의 핵심 연동은 통과했다.

```text
v5 backend
  -> POST /api/extn/customer-replies/post-via-mcp
  -> customer_mcp /mcp/tools/comment.create
  -> customer_board
```

남은 작업:

- frontend 시연 버튼 또는 화면 연결
- 실제 Azure LLM webhook adapter로 draft 생성 경로 교체
- 고객사 mock DB 테스트 데이터 정리 여부 결정

## 9. 재수행 결과 - 2026-06-12

고객사 mock infra가 이미 실행 중인 상태에서 v5 backend만 임시 기동해 통합 테스트를 재수행했다.

사전 확인:

```text
GET http://localhost:8080/health
=> 200 {"status":"ok","service":"customer_mcp"}
```

테스트 결과:

| Test | Request ID | Result |
| --- | --- | --- |
| post-via-mcp dry_run | `codex-it-dryrun-20260612-001` | PASS |
| post-via-mcp post | `codex-it-post-20260612-001` | PASS |
| generate-and-post dry_run | `codex-it-generate-20260612-001` | PASS |

실제 post 결과:

```json
{
  "request_id": "codex-it-post-20260612-001",
  "status": "success",
  "tool": "comment.create",
  "result": {
    "external_comment_id": "comment-06a54df3",
    "external_thread_id": "q-001",
    "url": "http://localhost:8090/posts/q-001#comment-comment-06a54df3"
  },
  "error": null,
  "status_code": 200
}
```

Audit 확인:

```text
ont_platform/v5/backend/storage/default/proj-default/audit/customer_mcp_calls.jsonl
```

프로세스 정리:

- Codex가 임시 기동한 v5 backend `8001`은 테스트 후 종료했다.
- 고객사 mock infra `8080`, `8090`은 건드리지 않았다.

