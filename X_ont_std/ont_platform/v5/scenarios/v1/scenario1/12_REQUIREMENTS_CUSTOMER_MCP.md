# Scenario 1 Requirements - Customer MCP

작성일: 2026-06-12

## 1. 목적

이 문서는 Scenario 1에서 고객사 MCP 서버가 만족해야 하는 요구사항을 정의한다.

고객사 MCP 서버는 `ont_platform`의 요청을 받아 고객사 게시판 API(`customer_board`) 호출로 변환하는 고객사 측 중계 서버다.

## 2. 관련 문서

- `20_CUSTOMER_MCP_CALL_SPEC.md`: `POST /mcp/tools/comment.create` 공식 호출 계약
- `30_TRIGGER_DESIGN.md`: Scenario 1-1/1-2 트리거 연계 구조
- `40_CUSTOMER_MOCK_INFRA_DESIGN.md`: 고객사 mock MCP/게시판 인프라 설계

문서 간 충돌이 있을 경우 이 요구사항 정의서와 `20_CUSTOMER_MCP_CALL_SPEC.md`를 우선한다.

## 3. 범위

포함:

- health check
- comment.create tool
- dry_run 처리
- post 처리
- customer_board API 호출
- 오류 응답 정규화
- P1용 question.list/question.get 후보

제외:

- ont_platform workflow 구현
- LLM webhook 구현
- ont_platform audit 저장

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

## 5. Comment Create Tool

필수 endpoint:

```http
POST /mcp/tools/comment.create
```

Request:

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
    "message": "LLM webhook으로 생성된 댓글 메시지",
    "author": "ontology-workflow"
  },
  "metadata": {
    "workflow_run_id": "run-001",
    "source": "ont_platform_v5",
    "generated_by": "llm_webhook"
  }
}
```

## 6. Dry-run 요구사항

`mode=dry_run`인 경우 실제 댓글을 DB에 저장하지 않아야 한다.

처리:

- 요청 payload 검증
- 대상 게시글 존재 여부 확인
- 성공 시 dry_run 응답 반환

## 7. Post 요구사항

`mode=post`인 경우 customer_board API를 호출해 실제 댓글을 등록해야 한다.

## 8. Error 요구사항

오류 응답은 다음 구조를 따라야 한다.

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

| Code | Retryable | Meaning |
| --- | --- | --- |
| `INVALID_REQUEST` | false | 필수 필드 누락 또는 잘못된 요청 |
| `AUTH_FAILED` | false | 인증 실패 |
| `BOARD_API_ERROR` | true | customer_board 호출 실패 |
| `BOARD_TIMEOUT` | true | customer_board timeout |
| `TOOL_NOT_FOUND` | false | 지원하지 않는 tool |
| `INTERNAL_ERROR` | true | 예기치 않은 customer_mcp 오류 |

## 9. Scenario 1-2 Trigger 연계 요구사항

고객사 측에서 webhook/API trigger를 구현하는 경우, 새 문의 등록 시 `ont_platform` trigger API를 호출해야 한다.

호출 대상:

```http
POST http://localhost:8001/api/extn/customer-questions/events
```

고객사 측은 다음 값을 전달해야 한다.

- `event_id`
- `event_type`
- `question_id`
- `post_id`
- `thread_id`
- `title`
- `content`
- `author`
- `created_at`
- `mode`

## 10. Scenario 1-1 Batch 연계 요구사항

P1 이후 customer_mcp는 미처리 문의 조회 API를 제공할 수 있다.

후보 endpoint:

```http
GET /mcp/tools/question.list?status=open
GET /mcp/tools/question.get?question_id=q-001
```

## 11. 완료 기준

- `GET /health`가 정상 응답한다.
- `POST /mcp/tools/comment.create` dry_run이 성공한다.
- `POST /mcp/tools/comment.create` post가 customer_board에 실제 댓글을 등록한다.
- 오류 응답이 표준 구조를 따른다.
- `request_id`를 그대로 반환한다.

