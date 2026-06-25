# v5 긴급 업그레이드 - 2. 계획 및 확장 설계

작성일: 2026-06-12

## 1. 이 문서의 목적

이 문서는 P0 우선 구현에 넣지 않을 확장 아이디어를 보관한다. 지금 바로 구현할 대상은 아니다.

우선 구현 문서:

- `SKILL_MCP_WEBHOOK_UPGRADE_PLAN-1-PRIORITY_IMPLEMENTATION.md`

## 2. 확장 목표

P0 이후에는 고객 문의 자동 대응을 더 큰 workflow 기반 솔루션으로 확장할 수 있다.

확장 후보:

- workflow `skill_call` 노드
- 고객 문의 수집 batch
- RAG 문서 업로드/검색
- 온톨로지 기반 시스템 규칙
- 승인 workflow
- 표준 MCP SSE/HTTP transport
- async callback/job
- 운영 배포 guide

## 3. 장기 아키텍처

```text
Workflow
  -> Skill Manager
    -> General LLM Skill
    -> LLM Webhook Skill
    -> Customer MCP Client Adapter
    -> Comment Reply Adapter
```

단, 고객사 MCP 서버 자체는 우리 솔루션이 아니다.

```text
v5 extn adapter -> customer MCP server -> customer API
```

우리 책임:

- 요청 정규화
- 인증 profile 관리
- timeout/retry 정책
- audit
- dry-run/approval 정책

고객사 책임:

- MCP 서버 구현
- 고객사 API 호출
- 고객사 API 인증/권한
- 댓글 등록 최종 처리

## 4. Scenario 확장

### Scenario 1: RAG 기반 정보 제공

질문에 대해 문서 근거를 찾고 답변한다.

- 문서 업로드
- 벡터화
- project 범위 검색
- 근거 기반 답변 생성
- 댓글 초안 생성

### Scenario 2: 온톨로지 규칙 + Workflow

요청 유형과 대상 시스템에 따라 승인 필요 여부를 판단한다.

예:

- 개발 서버 비밀번호 초기화: 승인 없이 처리 가능
- 운영 서버 비밀번호 초기화: 책임자 승인 후 처리

### Scenario 3: Hybrid

RAG 설명, 온톨로지 데이터 조회, workflow action을 조합한다.

예:

- 정책 설명은 RAG
- 대상 시스템/사용자 확인은 온톨로지
- 실제 조치는 workflow와 고객사 MCP 서버 호출

## 5. Batch 설계

P0에서는 batch를 구현하지 않는다.

P1 이후 후보:

- 고객사 문의 목록 polling
- 미처리 문의 감지
- workflow run 생성
- 답변 초안 생성
- 승인 대기 또는 자동 등록

주의:

- batch가 고객사 API를 직접 호출하지 않는다.
- 고객사 API 연동은 고객사 MCP 서버를 통해 수행한다.
- batch는 workflow run을 생성하는 trigger 역할만 한다.

## 6. Skill Manager 확장

P0에서는 최소 service 함수로 시작할 수 있다. P1 이후에는 Skill Manager로 일반화한다.

Skill type 후보:

- `llm.inference.general`
- `llm.inference.webhook`
- `customer_mcp.tool_call`
- `comment.reply`
- `rag.retrieve`
- `ontology.query`

## 7. Frontend 확장

P0에서는 backend API 검증을 우선한다.

P1 이후 후보:

- 고객 문의 테스트 화면
- 댓글 초안 생성 버튼
- dry-run 등록 버튼
- 고객사 MCP 호출 결과 표시
- workflow run history
- approval 화면

## 8. 운영 배포 설계

P2 이후 정리한다.

검토 항목:

- webhook HMAC/JWT/mTLS
- customer MCP server allowlist
- timeout/retry/circuit breaker
- APIM/NAT Gateway/forward proxy
- secret manager
- audit export
- 장애 재처리 queue

## 9. Phase8 관리 기준

Phase8에서는 다음을 검증한다.

- P0 범위가 과도하게 커지지 않았는가?
- 고객사 MCP 서버를 우리 solution으로 오해하지 않았는가?
- workflow가 외부 고객사 API를 직접 호출하지 않는가?
- extn adapter와 solution workflow가 분리되어 있는가?
- side-effect 호출에 dry-run/approval 정책이 있는가?

