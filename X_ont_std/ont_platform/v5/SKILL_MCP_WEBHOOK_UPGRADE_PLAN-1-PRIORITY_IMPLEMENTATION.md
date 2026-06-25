# v5 긴급 업그레이드 - 1. 우선 구현 범위

작성일: 2026-06-12

## 1. 이번에 바로 구현할 것

이번 P0의 목표는 복잡한 전체 플랫폼 확장이 아니다. 먼저 다음 흐름 하나를 끝까지 연결한다.

```text
고객 문의 입력
  -> LLM Webhook으로 댓글 메시지 생성
  -> 고객사 MCP 서버 호출
  -> 고객사 API가 댓글 등록
  -> 결과/audit 저장
```

중요한 전제:

- 고객사 MCP 서버는 고객사가 개발/운영한다.
- 고객사 MCP 서버는 우리 `solution` 영역이 아니다.
- 우리 v5는 고객사 MCP 서버를 호출하는 `extn adapter`만 가진다.
- 우리 솔루션 본체는 여전히 워크플로우다.

## 2. 시스템 경계

### Core

v5 내부에서 안정적으로 유지해야 하는 공통 기반이다.

- TenantContext
- auth/audit
- workflow execution contract
- skill execution contract
- approval/dry-run 정책

### Solution

우리 제품의 핵심 사용 경험이다.

- workflow template
- workflow runner
- 고객 문의 처리 workflow
- 댓글 생성/승인/등록 흐름

### Extn

외부 시스템과 붙는 영역이다.

- LLM Webhook adapter
- Customer MCP client adapter
- 고객사 API 연동 결과 정규화

고객사 MCP 서버 자체는 extn에도 포함하지 않는다. 우리 쪽 extn은 “고객사 MCP 서버를 호출하는 adapter”까지만 책임진다.

## 3. P0 기능 범위

### 3.1 LLM Webhook Message Generator

역할:

- 고객 문의 내용을 받아 댓글 초안을 생성한다.
- RAG, 온톨로지, 복잡한 workflow rule은 P0에서 필수로 넣지 않는다.
- 입력/출력 계약을 먼저 고정한다.

입력 예:

```json
{
  "question_id": "q-001",
  "question_text": "비밀번호 초기화는 어떻게 하나요?",
  "customer_context": {
    "company_id": "demo-company",
    "project_id": "demo-project"
  }
}
```

출력 예:

```json
{
  "reply_message": "비밀번호 초기화는 관리자 승인 후 처리됩니다.",
  "confidence": 0.82,
  "reason": "LLM webhook generated draft"
}
```

### 3.2 Customer MCP Client Adapter

역할:

- 고객사 MCP 서버 endpoint를 호출한다.
- 고객사 MCP 서버가 실제 고객사 API를 호출한다.
- v5는 고객사 API를 직접 호출하지 않는다.

호출 예:

```json
{
  "tool": "comment.create",
  "arguments": {
    "question_id": "q-001",
    "message": "비밀번호 초기화는 관리자 승인 후 처리됩니다."
  }
}
```

결과 예:

```json
{
  "status": "success",
  "external_comment_id": "comment-123",
  "external_thread_id": "thread-456"
}
```

### 3.3 Dry-run 우선

초기 구현은 실제 등록보다 안전한 검증을 우선한다.

- 기본 mode: `dry_run`
- `post` mode는 명시적으로 활성화해야 한다.
- 운영에서는 approval 또는 별도 feature flag를 요구한다.

## 4. API 초안

### 4.1 댓글 생성

```http
POST /api/extn/customer-replies/draft
```

요청:

```json
{
  "question_id": "q-001",
  "question_text": "문의 내용",
  "llm_webhook_skill_id": "azure-comment-draft"
}
```

응답:

```json
{
  "reply_message": "댓글 초안",
  "confidence": 0.8,
  "request_id": "uuid"
}
```

### 4.2 고객사 MCP 서버를 통한 댓글 등록

```http
POST /api/extn/customer-replies/post-via-mcp
```

요청:

```json
{
  "question_id": "q-001",
  "reply_message": "댓글 내용",
  "mode": "dry_run"
}
```

응답:

```json
{
  "status": "dry_run",
  "mcp_tool": "comment.create",
  "external_comment_id": null,
  "request_id": "uuid"
}
```

### 4.3 한 번에 실행

```http
POST /api/extn/customer-replies/generate-and-post
```

P0에서는 내부적으로 다음 순서로만 처리한다.

1. LLM webhook 호출
2. 댓글 초안 생성
3. 고객사 MCP 서버 호출
4. audit 저장

## 5. 구현 위치

Backend:

- `backend/app/api/customer_replies.py`
- `backend/app/services/customer_reply_service.py`
- `backend/app/services/skill_adapters/llm_webhook.py`
- `backend/app/services/extn/customer_mcp_client.py`
- `backend/app/models/customer_reply.py`

Config:

- `config/extn.customer_mcp.example.json`
- `config/skills.registry.json`

## 6. 제외할 것

다음은 P0에서 제외하고 `-2 계획 및 설계`로 넘긴다.

- 전체 Skill Manager UI
- Workflow Builder의 범용 `skill_call` 노드
- RAG 문서 업로드 자동화
- 5분 배치 프로세스
- 게시판 mock 사이트
- 온톨로지 기반 시스템 규칙 엔진
- 표준 MCP SSE/HTTP 전체 구현
- async callback/job
- APIM/NAT Gateway 배포 상세

## 7. P0 완료 기준

- LLM webhook으로 댓글 초안을 생성할 수 있다.
- 생성된 댓글을 고객사 MCP 서버 호출 payload로 변환할 수 있다.
- 고객사 API는 v5가 직접 호출하지 않는다.
- dry-run으로 전체 흐름을 검증할 수 있다.
- 모든 실행에 `company_id`, `project_id`, `question_id`, `request_id`, `status`, `duration_ms` audit이 남는다.
- 고객사 MCP 서버 장애 시 사용자에게 실패 원인과 재시도 가능 상태를 반환한다.

