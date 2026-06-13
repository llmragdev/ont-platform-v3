# v5 긴급 업그레이드 계획: Skill Manager + Azure Webhook LLM + MCP Relay

작성일: 2026-06-12

> 범위 조정: 2026-06-12 기준으로 우선 구현과 확장 설계를 분리한다.
>
> - 우선 구현: `SKILL_MCP_WEBHOOK_UPGRADE_PLAN-1-PRIORITY_IMPLEMENTATION.md`
> - 계획 및 확장 설계: `SKILL_MCP_WEBHOOK_UPGRADE_PLAN-2-PLAN_AND_DESIGN.md`
>
> 현재 P0는 "LLM Webhook으로 댓글 메시지 생성 -> 고객사 MCP 서버 호출 -> 고객사 API 댓글 등록" 흐름에 집중한다. 고객사 MCP 서버 자체는 고객사 영역이며, v5는 고객사 MCP 서버를 호출하는 extn adapter만 책임진다.

## 1. 결론

이번 업그레이드는 `ont_platform/v5`에 바로 구현하되, 시스템 경계는 명확히 분리한다.

- `core`: 테넌트/프로젝트 컨텍스트, 권한, 감사, 워크플로우 실행 계약, Skill 실행 계약
- `solution`: 워크플로우 빌더, 업무 템플릿, 승인/계정/문의 대응 시나리오
- `extn`: Azure LLM webhook adapter, MCP relay, 고객사 문의 시스템 연동, 댓글 작성/등록 connector

즉, 우리의 솔루션 본체는 워크플로우이고, MCP 중계와 댓글 달기는 외부 채널을 붙이는 `extn`이다. 다만 워크플로우에서 안전하게 호출할 수 있도록 Skill 실행 계약과 감사는 `core`에 둔다.

## 2. 중요한 명명 원칙

Azure webhook 방식은 표준 MCP transport로 부르지 않는다.

- 표준 MCP: stdio, SSE/HTTP 기반 세션/도구 호출
- Azure webhook 방식: stateless HTTP webhook/tool-call adapter
- 권장 명칭: `azure_webhook_skill` 또는 `mcp_webhook_proxy`

이렇게 구분해야 나중에 표준 MCP 서버와 기업형 webhook proxy를 동시에 지원할 때 구조가 꼬이지 않는다.

## 3. 목표

1. 기존 일반 LLM 추론을 Skill Manager를 통해 호출한다.
2. Azure webhook 형태의 LLM 추론 Skill을 추가한다.
3. MCP relay를 extn으로 추가할 수 있는 계약을 만든다.
4. 고객사 문의에 대한 답변 초안을 생성하고, 승인 후 댓글을 등록하는 워크플로우를 만든다.
5. 댓글 등록은 초기에는 반드시 `draft_only` 또는 `approval_required` 모드로 제한한다.

## 4. 추론 방식 2종

### 4.1 General LLM Skill

이미 존재하는 일반 추론 경로를 Skill로 감싼다.

- `skill_type`: `llm.inference.general`
- adapter: 기존 `LlmClient`
- 특징: 동기 호출, 내부 설정 기반 provider 사용
- 사용처: 일반 질의, 문서 요약, 워크플로우 노드의 답변 초안 생성

### 4.2 Azure Webhook LLM Skill

Azure 또는 기업형 webhook endpoint로 signed HTTP POST를 보내고 결과를 받는다.

- `skill_type`: `llm.inference.webhook`
- adapter: `AzureWebhookSkillAdapter`
- 특징: stateless HTTP 호출
- 인증: Bearer token, HMAC signature, timestamp, request id
- timeout: 기본 15초, 최대 30초
- 장기 작업: P1 이후 async job/callback 패턴으로 확장

## 5. Skill Manager 설계

Skill Manager는 워크플로우와 외부 실행 adapter 사이의 단일 관문이다.

### 5.1 Skill Registry

Skill 정의에는 다음 필드를 둔다.

```json
{
  "skill_id": "azure-llm-webhook-default",
  "name": "Azure Webhook LLM",
  "skill_type": "llm.inference.webhook",
  "provider": "azure",
  "enabled": true,
  "input_schema": {},
  "output_schema": {},
  "auth_profile": "azure-webhook-dev",
  "timeout_ms": 15000,
  "retry_policy": {
    "max_attempts": 1
  },
  "side_effect": "none",
  "approval_required": false
}
```

### 5.2 Skill Type

초기 타입은 4개로 시작한다.

- `llm.inference.general`: 기존 일반 LLM 추론
- `llm.inference.webhook`: Azure webhook 형태 LLM 추론
- `mcp.relay`: MCP 또는 MCP-like endpoint 중계
- `comment.reply`: 고객사 문의 댓글 초안/등록

### 5.3 Skill Request

```json
{
  "company_id": "demo-company",
  "project_id": "demo-project",
  "run_id": "workflow-run-id",
  "node_id": "node-id",
  "skill_id": "azure-llm-webhook-default",
  "input": {
    "question": "고객 문의 내용",
    "context": []
  },
  "evidence_refs": [],
  "options": {
    "mode": "draft_only"
  }
}
```

### 5.4 Skill Result

```json
{
  "request_id": "uuid",
  "skill_id": "azure-llm-webhook-default",
  "status": "success",
  "output": {
    "answer": "답변 초안"
  },
  "evidence_refs": [],
  "duration_ms": 1234,
  "audit_id": "audit-id"
}
```

## 6. Azure Webhook Adapter 설계

### 6.1 Outbound 호출

v5 P0에서는 우리 플랫폼이 configured webhook endpoint로 요청을 보내는 방식으로 구현한다.

필수 header:

- `Authorization: Bearer <token>`
- `X-Request-Id`
- `X-Timestamp`
- `X-Signature`
- `X-Company-Id`
- `X-Project-Id`

서명 방식:

- payload body + timestamp + request id를 HMAC-SHA256으로 서명
- timestamp 허용 오차 기본 5분
- nonce/request id 중복 방지 기록은 P1에서 강화

### 6.2 Local Mock

개발과 검증을 위해 v5 내부에 mock webhook receiver를 둔다.

- 운영에서는 비활성화
- `ENABLE_DEVTOOLS_DEMO=true` 또는 별도 `ENABLE_EXTN_MOCKS=true`일 때만 활성화
- 실제 Azure 연결 전 Skill Manager 계약 검증에 사용

## 7. MCP Relay 설계

MCP relay는 `extn`이다. 워크플로우 엔진은 MCP 세부 transport를 몰라야 한다.

초기 transport 전략:

- P0: `webhook_proxy`
- P1: `sse_http`
- P2: `stdio` local dev, 표준 MCP client/server 확장

역할:

- Workflow `skill_call` 요청을 받아 MCP 또는 MCP-like endpoint로 변환
- 결과를 표준 `SkillResult`로 정규화
- 실패/timeout/auth error를 감사 로그에 남김

## 8. Comment Reply Extn 설계

고객사 문의에 답변하는 기능은 side-effect가 있으므로 기본은 초안 생성이다.

지원 mode:

- `draft_only`: 답변 초안만 생성
- `post_after_approval`: 승인 후 등록
- `direct_post`: 초기 비활성화

필수 조건:

- company/project/run/node context 포함
- evidence 또는 답변 근거 포함
- 승인자/승인 시각 감사
- 댓글 등록 결과의 external id 저장

## 9. Workflow 통합

워크플로우에는 범용 `skill_call` 노드를 추가한다.

예시 흐름:

1. 고객 문의 수신
2. 문의 유형 분류
3. 온톨로지/문서 근거 검색
4. LLM Skill로 답변 초안 생성
5. EvidenceGate 검증
6. 사람 승인
7. Comment Reply Skill 실행

이 구조에서는 Azure webhook, 일반 LLM, MCP relay를 모두 같은 워크플로우 노드 모델로 호출할 수 있다.

## 10. 보안과 운영 원칙

- secret은 workflow template에 저장하지 않고 `auth_profile` 이름만 저장한다.
- webhook은 HMAC/JWT/mTLS 중 최소 하나를 사용한다.
- timestamp/replay 방어를 둔다.
- side-effect skill은 승인 없이는 실행하지 않는다.
- 모든 skill 실행은 audit에 남긴다.
- Azure outbound 고정 IP 문제는 app core가 아니라 deployment/extn 문서에서 APIM, NAT Gateway, forward proxy 중 하나로 해결한다.

## 11. v5 구현 위치 제안

Backend:

- `backend/app/api/skills.py`
- `backend/app/services/skill_manager.py`
- `backend/app/services/skill_registry.py`
- `backend/app/services/skill_adapters/base.py`
- `backend/app/services/skill_adapters/general_llm.py`
- `backend/app/services/skill_adapters/azure_webhook.py`
- `backend/app/services/skill_adapters/mcp_relay.py`
- `backend/app/services/skill_adapters/comment_reply.py`
- `backend/app/extn/` 또는 `backend/app/services/extn/` 아래 connector 구현

Frontend:

- P0: 별도 화면 없이 API 검증 우선
- P1: Skill Manager 화면 추가
- P1: Workflow Builder의 `skill_call` 노드에서 skill 선택
- P1: 고객 문의 대응 template 추가

Config:

- `config/skills.registry.json`
- `config/extn.auth.example.json`
- 실제 secret은 `.env` 또는 secret manager 사용

## 12. 단계별 계획

### P0: 긴급 골격 구현

목표 기간: 1~2일

- Skill registry 파일 로딩
- Skill Manager API
- General LLM Skill adapter
- Azure Webhook Skill adapter
- local mock webhook receiver
- Comment Reply dry-run adapter
- audit log 최소 기록
- 단위 테스트 또는 smoke script

완료 기준:

- 일반 LLM과 webhook LLM이 같은 `/api/skills/execute` 계약으로 호출된다.
- 댓글 skill은 실제 등록 없이 초안 결과를 반환한다.
- 모든 실행 결과에 request_id, skill_id, status, duration_ms가 남는다.

### P1: 워크플로우 연결

목표 기간: 2~4일

- WorkflowGraph에 `skill_call` 노드 추가
- workflow runner에서 Skill Manager 호출
- Skill 실행 history 조회 API
- Skill selector UI
- 고객 문의 답변 template 추가
- 승인 후 댓글 등록 flow 설계 반영

완료 기준:

- 문의 대응 workflow template에서 LLM Skill을 선택해 실행할 수 있다.
- 댓글 등록은 approval gate 이후에만 가능하다.

### P2: 표준 MCP와 Azure 배포 강화

목표 기간: 1~2주

- 표준 MCP SSE/HTTP client adapter
- async webhook callback/job pattern
- APIM/NAT Gateway/forward proxy 배포 가이드
- mTLS/JWT 강화
- 고객사 실제 문의 시스템 connector

## 13. 클로드 코드 검증 포인트

1. `core`, `solution`, `extn` 경계가 코드상 섞이지 않았는가?
2. workflow runner가 특정 Azure/MCP 구현을 직접 알지 않는가?
3. Skill Manager의 요청/응답 계약이 일반 LLM과 webhook LLM에 공통 적용되는가?
4. side-effect skill이 승인 없이 실행될 수 없는가?
5. secret이 registry/template에 평문 저장되지 않는가?
6. webhook timeout, signature, audit이 빠지지 않았는가?
7. Azure webhook 방식을 표준 MCP transport로 오해하게 만드는 명명이 없는가?
