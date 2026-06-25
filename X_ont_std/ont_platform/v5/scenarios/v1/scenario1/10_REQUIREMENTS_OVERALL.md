# Scenario 1 Requirements - Overall

작성일: 2026-06-12

## 1. 목적

Scenario 1은 고객사 게시판에 등록된 문의를 `ont_platform v5`가 인식하고, LLM 기반 댓글 메시지를 생성한 뒤, 고객사 MCP 서버를 통해 고객사 게시판에 댓글을 등록하는 흐름을 검증한다.

## 2. 관련 문서

- `11_REQUIREMENTS_ONT_PLATFORM.md`: ont_platform v5 요구사항
- `12_REQUIREMENTS_CUSTOMER_MCP.md`: 고객사 MCP 요구사항
- `20_CUSTOMER_MCP_CALL_SPEC.md`: v5에서 customer_mcp로 호출하는 API 계약
- `30_TRIGGER_DESIGN.md`: Scenario 1-1/1-2 트리거 상세 설계

문서 간 충돌이 있을 경우 `10`, `11`, `12` 요구사항 문서를 우선한다.

## 3. 시스템 구성

| 시스템 | 포트 | 책임 |
| --- | ---: | --- |
| ont_platform backend | 8001 | workflow 시작, 댓글 초안 생성, customer_mcp 호출, audit 저장 |
| ont_platform frontend | 3002 | 운영/시연 UI |
| customer_mcp | 8080 | ont_platform 요청 수신, customer_board API 호출로 변환 |
| customer_board | 8090 | 고객사 게시판 mock, 문의/댓글 저장 |

## 4. 책임 경계

- `ont_platform`는 고객사 게시판 API를 직접 호출하지 않는다.
- `ont_platform`는 `customer_mcp`만 호출한다.
- `customer_mcp`와 `customer_board`는 고객사 영역이다.
- `customer_mcp`는 고객사 API 호출과 프로토콜 변환을 책임진다.
- `ont_platform`는 댓글 생성, 처리 상태, audit, idempotency를 책임진다.

## 5. 시나리오 분리

### Scenario 1-1: 5분 배치 Polling

`ont_platform`가 주기적으로 `customer_mcp`를 통해 미처리 문의를 조회한다.

역할:

- webhook 누락 보정
- 장애 복구
- missed-event reconciliation

운영 우선순위:

- fallback

### Scenario 1-2: 고객사 Webhook/API Trigger

고객사 시스템이 새 문의 등록 이벤트를 `ont_platform` trigger API로 전달한다.

역할:

- 실시간 처리
- 이벤트 기반 workflow 시작

운영 우선순위:

- primary

## 6. 공통 처리 흐름

```text
question detected
  -> ont_platform starts event/workflow
  -> LLM path generates reply message
  -> ont_platform calls customer_mcp /mcp/tools/comment.create
  -> customer_mcp calls customer_board
  -> ont_platform stores result and audit
```

## 7. 공통 데이터 키

- `event_id`: 이벤트 중복 방지
- `question_id`: 고객 문의 식별
- `post_id`: 고객사 게시글 식별
- `thread_id`: 고객사 스레드 식별
- `request_id`: end-to-end 추적
- `workflow_run_id`: ont_platform workflow 실행 식별

## 8. 필수 기능 요구사항

- FR-001: 고객 문의 내용으로 댓글 메시지를 생성해야 한다.
- FR-002: 댓글 등록 시 `customer_mcp`의 `POST /mcp/tools/comment.create`만 호출해야 한다.
- FR-003: 모든 등록 흐름은 `dry_run` 모드를 지원해야 한다.
- FR-004: 명시적으로 `mode=post`가 전달된 경우에만 실제 댓글 등록을 시도해야 한다.
- FR-005: 요청/응답 결과를 audit으로 저장해야 한다.
- FR-006: 동일 `event_id` 또는 이미 처리된 `question_id`에 대해 중복 댓글이 등록되지 않아야 한다.

## 9. 비기능 요구사항

- NFR-001: 고객사 API 직접 호출은 금지한다.
- NFR-002: customer_mcp/customer_board 장애가 ont_platform 전체 장애로 전파되지 않아야 한다.
- NFR-003: 모든 요청은 `request_id`로 추적 가능해야 한다.
- NFR-004: 실패한 요청은 retry 또는 batch reconciliation으로 재처리 가능해야 한다.

## 10. 완료 기준

- Scenario 1-2 webhook/API trigger로 댓글 처리 workflow를 시작할 수 있다.
- Scenario 1-1 batch polling으로 누락 문의를 보정할 수 있다.
- `ont_platform`는 `customer_board`를 직접 호출하지 않는다.
- `customer_mcp` 호출 payload가 `20_CUSTOMER_MCP_CALL_SPEC.md`와 일치한다.
- dry-run과 post가 모두 검증된다.

