# Customer Mock Infrastructure Design - Scenario 1

작성일: 2026-06-12

## 1. 목적

이 문서는 Scenario 1 검증을 위해 구성한 고객사 mock 인프라의 물리 구성, 데이터 모델, 통신 규격, 실행 방법을 정의한다.

고객사 mock 인프라는 `ont_platform/v5`와 분리된 독립 프로세스로 실행한다.

```text
ont_platform v5
  -> s1_customer_mcp
  -> s1_customer_board
```

`ont_platform v5`는 `s1_customer_board`를 직접 호출하지 않는다.

## 2. 서버 구성

| 구성 요소 | 위치 | 기본 포트 | 역할 |
| --- | --- | ---: | --- |
| `s1_customer_mcp` | `E:\ontology_edu\X_ont_std\s1_customer_mcp` | 8080 | ont_platform의 MCP 호출을 받아 customer_board API로 중계 |
| `s1_customer_board` | `E:\ontology_edu\X_ont_std\s1_customer_board` | 8090 | SQLite 기반 고객사 게시판 mock API/UI |

## 3. 데이터베이스 설계

`s1_customer_board`는 SQLite 파일을 사용한다.

예상 DB 파일:

```text
E:\ontology_edu\X_ont_std\s1_customer_board\s1_customer_board.db
```

### 3.1 posts

고객 문의 게시글을 저장한다.

```sql
CREATE TABLE posts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

예시:

```text
id: q-001
title: [시나리오1] 비밀번호 초기화 요청
author: customer-user
content: 비밀번호 초기화 부탁드립니다.
```

### 3.2 comments

문의 게시글에 등록된 댓글을 저장한다.

```sql
CREATE TABLE comments (
    id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL,
    author TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
);
```

## 4. 통신 규격

`s1_customer_mcp`는 `20_CUSTOMER_MCP_CALL_SPEC.md`를 따른다.

필수 endpoint:

```http
GET /health
POST /mcp/tools/comment.create
```

## 5. Health Check

Request:

```http
GET http://localhost:8080/health
```

Response:

```json
{
  "status": "ok",
  "service": "customer_mcp"
}
```

## 6. comment.create - Dry-run

`mode=dry_run`이면 실제 댓글을 DB에 저장하지 않는다.

Request:

```json
{
  "request_id": "test-uuid-1",
  "company_id": "demo-company",
  "project_id": "demo-project",
  "mode": "dry_run",
  "tool": "comment.create",
  "arguments": {
    "question_id": "q-001",
    "post_id": "q-001",
    "message": "Dry-run 테스트 댓글",
    "author": "ontology-workflow"
  },
  "metadata": {
    "workflow_run_id": "run-001",
    "source": "ont_platform_v5",
    "generated_by": "llm_webhook"
  }
}
```

Response:

```json
{
  "request_id": "test-uuid-1",
  "status": "dry_run",
  "tool": "comment.create",
  "result": {
    "external_comment_id": null,
    "external_thread_id": "q-001",
    "message": "Dry-run 테스트 댓글"
  },
  "error": null
}
```

## 7. comment.create - Post

`mode=post`이면 `s1_customer_mcp`가 `s1_customer_board` API를 호출해 실제 댓글을 등록한다.

Request:

```json
{
  "request_id": "test-uuid-2",
  "company_id": "demo-company",
  "project_id": "demo-project",
  "mode": "post",
  "tool": "comment.create",
  "arguments": {
    "question_id": "q-001",
    "post_id": "q-001",
    "message": "Post 테스트 댓글",
    "author": "ontology-workflow"
  },
  "metadata": {
    "workflow_run_id": "run-001",
    "source": "ont_platform_v5",
    "generated_by": "llm_webhook"
  }
}
```

Response:

```json
{
  "request_id": "test-uuid-2",
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

## 8. 오류 처리

오류 응답은 다음 구조를 따른다.

```json
{
  "request_id": "test-uuid-3",
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

| Code | Retryable | 의미 |
| --- | --- | --- |
| `INVALID_REQUEST` | false | 필수 필드 누락 또는 잘못된 요청 |
| `AUTH_FAILED` | false | 인증 실패 |
| `BOARD_API_ERROR` | true | customer_board 호출 실패 |
| `BOARD_TIMEOUT` | true | customer_board timeout |
| `TOOL_NOT_FOUND` | false | 지원하지 않는 tool |
| `INTERNAL_ERROR` | true | 예상하지 못한 customer_mcp 오류 |

## 9. 실행 방법

### 9.1 customer_board 실행

```powershell
conda activate claud_be
cd E:\ontology_edu\X_ont_std\s1_customer_board
python src/main.py
```

확인:

```text
http://localhost:8090
```

### 9.2 customer_mcp 실행

```powershell
conda activate claud_be
cd E:\ontology_edu\X_ont_std\s1_customer_mcp
python src/main.py
```

확인:

```text
http://localhost:8080/health
```

## 10. Smoke Test

Dry-run:

```powershell
Invoke-RestMethod -Uri "http://localhost:8080/mcp/tools/comment.create" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"request_id":"test-uuid-1","company_id":"demo-company","project_id":"demo-project","mode":"dry_run","tool":"comment.create","arguments":{"question_id":"q-001","post_id":"q-001","message":"Dry-run 테스트 댓글","author":"ontology-workflow"}}'
```

Post:

```powershell
Invoke-RestMethod -Uri "http://localhost:8080/mcp/tools/comment.create" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"request_id":"test-uuid-2","company_id":"demo-company","project_id":"demo-project","mode":"post","tool":"comment.create","arguments":{"question_id":"q-001","post_id":"q-001","message":"Post 테스트 댓글","author":"ontology-workflow"}}'
```

## 11. 향후 확장

Scenario 1-1 batch polling을 위해 P1에서 다음 endpoint를 추가할 수 있다.

```http
GET /mcp/tools/question.list?status=open
GET /mcp/tools/question.get?question_id=q-001
```

이 endpoint는 webhook 누락 보정과 미처리 문의 reconciliation에 사용한다.

