# Scenario 1 Requirements - ont_platform

작성일: 2026-06-12

## 1. 목적

이 문서는 Scenario 1에서 `ont_platform v5`가 구현해야 하는 요구사항을 정의한다.

`ont_platform`의 책임은 고객 문의 이벤트를 받아 workflow를 시작하고, 댓글 메시지를 생성하고, `customer_mcp`를 호출하고, 처리 결과를 audit으로 남기는 것이다.

## 2. 관련 문서

- `30_TRIGGER_DESIGN.md`: trigger 방식과 idempotency 설계
- `20_CUSTOMER_MCP_CALL_SPEC.md`: customer_mcp 호출 payload/API 계약

문서 간 충돌이 있을 경우 이 요구사항 정의서를 우선한다.

## 3. 범위

포함:

- 고객 문의 event trigger API
- 5분 batch polling scheduler
- 댓글 draft 생성
- customer_mcp client adapter
- idempotency
- audit 저장
- 처리 상태 조회

제외:

- customer_mcp 서버 구현
- customer_board API 구현
- 고객사 게시판 DB 관리
- 고객사 API 인증/권한 세부 처리

## 4. API 요구사항

### 4.1 고객 문의 이벤트 수신

Scenario 1-2에서 사용한다.

```http
POST /api/extn/customer-questions/events
```

Request:

```json
{
  "event_id": "evt-001",
  "event_type": "question.created",
  "question_id": "q-001",
  "thread_id": "thread-001",
  "post_id": "q-001",
  "title": "비밀번호 초기화 요청",
  "content": "비밀번호 초기화 부탁드립니다.",
  "author": "customer-user",
  "created_at": "2026-06-12T10:00:00Z",
  "mode": "dry_run"
}
```

Response:

```json
{
  "event_id": "evt-001",
  "request_id": "uuid",
  "status": "accepted",
  "workflow_status": "started",
  "duplicate": false
}
```

### 4.2 댓글 초안 생성

```http
POST /api/extn/customer-replies/draft
```

### 4.3 customer_mcp를 통한 댓글 등록

```http
POST /api/extn/customer-replies/post-via-mcp
```

### 4.4 댓글 생성 및 등록 통합 실행

```http
POST /api/extn/customer-replies/generate-and-post
```

## 5. Batch 요구사항

Scenario 1-1에서 사용한다.

- 기본 실행 주기: 5분
- 운영 설정으로 주기를 변경할 수 있어야 한다.
- 미처리 문의 목록은 `customer_mcp`를 통해 조회해야 한다.
- 이미 처리된 `question_id`는 다시 처리하지 않아야 한다.

P1 후보 endpoint:

```http
GET /mcp/tools/question.list?status=open
GET /mcp/tools/question.get?question_id=q-001
```

## 6. customer_mcp 호출 요구사항

`ont_platform`는 공식 스펙에 따라 다음 endpoint를 호출해야 한다.

```http
POST {CUSTOMER_MCP_BASE_URL}/mcp/tools/comment.create
```

기본 설정:

```text
CUSTOMER_MCP_BASE_URL=http://localhost:8080
```

Payload는 `20_CUSTOMER_MCP_CALL_SPEC.md`와 일치해야 한다.

## 7. Idempotency 요구사항

`ont_platform`는 다음 저장소를 가져야 한다.

```text
storage/{company_id}/{project_id}/events/customer_question_events.jsonl
storage/{company_id}/{project_id}/events/customer_question_state.json
```

규칙:

- 동일 `event_id`는 중복 이벤트로 처리한다.
- 동일 `question_id`에 성공 댓글이 있으면 기본적으로 재등록하지 않는다.
- 강제 재처리는 명시적 옵션으로만 허용한다.

## 8. Audit 요구사항

현재 구현된 audit 파일:

```text
storage/{company_id}/{project_id}/audit/customer_mcp_calls.jsonl
```

필수 필드:

- `audit_id`
- `timestamp`
- `company_id`
- `project_id`
- `user_id`
- `request`
- `response`

## 9. 오류 처리 요구사항

`customer_mcp` 오류는 표준 오류 응답으로 변환해야 한다.

필수 오류 필드:

- `code`
- `message`
- `retryable`

## 10. 완료 기준

- event trigger API로 댓글 생성/등록 흐름을 시작할 수 있다.
- batch polling 설계에 따라 미처리 문의를 보정할 수 있다.
- `customer_board` 직접 호출이 없다.
- `20_CUSTOMER_MCP_CALL_SPEC.md`와 호환된다.
- dry-run/post 모두 동작한다.

