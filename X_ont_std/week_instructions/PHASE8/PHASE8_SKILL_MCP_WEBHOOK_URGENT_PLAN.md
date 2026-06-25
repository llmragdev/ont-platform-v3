# PHASE8 긴급 지시: Skill Management + Azure Webhook LLM + MCP Relay

작성일: 2026-06-12

> 범위 조정: 2026-06-12 기준으로 우선 구현과 확장 설계를 분리한다.
>
> - 우선 구현 지시: `PHASE8_SKILL_MCP_WEBHOOK_PLAN-1-PRIORITY_IMPLEMENTATION.md`
> - 계획 및 확장 설계: `PHASE8_SKILL_MCP_WEBHOOK_PLAN-2-PLAN_AND_DESIGN.md`
>
> 현재 P0는 "LLM Webhook으로 댓글 메시지 생성 -> 고객사 MCP 서버 호출 -> 고객사 API 댓글 등록" 흐름에 집중한다. 고객사 MCP 서버 자체는 고객사 영역이며, v5는 고객사 MCP 서버를 호출하는 extn adapter만 책임진다.

## 1. Phase8 내 위치

이번 작업은 `PHASE8_V5_UNIFIED_DESIGN_PLAN.md`의 기존 목표를 대체하지 않는다. 별도 긴급 트랙으로 관리한다.

- 구현 대상: `ont_platform/v5`
- 검증/거버넌스 기준: `week_instructions/PHASE8`
- 핵심 원칙: 워크플로우는 solution, 외부 중계/댓글 connector는 extn, 실행 계약/감사/권한은 core

## 2. 왜 v5에 먼저 하는가

v5는 이미 tenant/project, hybrid query, workflow builder, evidence gate, frontend/backend 실행 구조가 있다. 따라서 실제 실행 가능한 POC는 v5에 넣는 것이 맞다.

Phase8은 다음을 담당한다.

- 시스템 경계 검증
- acceptance criteria 관리
- Claude Code 검증 요청 기준
- core/solution/extn 분리 원칙 유지
- 운영 배포 전 위험 항목 정리

## 3. System Boundary

### Core

- TenantContext
- auth/audit
- Workflow execution contract
- Skill execution contract
- approval gate
- EvidenceGate

### Solution

- workflow templates
- workflow builder
- 업무 시나리오
- 고객 문의 대응 workflow
- 승인 후 조치 workflow

### Extn

- Azure LLM webhook adapter
- MCP relay/proxy
- 고객사 문의 시스템 connector
- comment writer/poster
- APIM/NAT/proxy 배포 설정
- 외부 인증 profile

## 4. 금지 사항

- workflow runner가 Azure webhook, MCP transport, 고객사 댓글 API를 직접 호출하면 안 된다.
- Azure webhook 방식을 표준 MCP transport로 명명하면 안 된다.
- secret을 workflow template이나 skill registry에 평문으로 저장하면 안 된다.
- 댓글 등록 같은 side-effect skill을 승인 없이 실행하면 안 된다.
- dev/mock endpoint가 운영에서 기본 활성화되면 안 된다.

## 5. 필수 설계 결정

### 5.1 Skill Manager 우선

모든 추론과 외부 중계는 Skill Manager를 통해 호출한다.

- 일반 LLM도 Skill
- Azure webhook LLM도 Skill
- MCP relay도 Skill
- 댓글 초안/등록도 Skill

### 5.2 Two Inference Modes

- `llm.inference.general`: 기존 LLM client 기반
- `llm.inference.webhook`: Azure webhook 또는 기업형 webhook endpoint 기반

두 방식은 동일한 `SkillRequest`/`SkillResult` 계약을 사용해야 한다.

### 5.3 MCP Relay는 Extn

MCP relay는 외부 시스템 중계 계층이다. workflow와 solution 본체에 녹이면 안 된다.

초기에는 `webhook_proxy` transport를 구현하고, 이후 표준 MCP SSE/HTTP transport를 추가한다.

## 6. P0 Acceptance Criteria

P0는 구현 골격을 검증하는 단계다.

- `/api/skills/execute` 또는 동등한 Skill 실행 API가 있다.
- 일반 LLM Skill과 Azure webhook Skill이 같은 API로 실행된다.
- local mock webhook으로 signature/timeout/audit smoke test가 가능하다.
- Comment Reply Skill은 `draft_only`로 동작한다.
- 실제 댓글 등록은 비활성화되어 있다.
- audit에는 `company_id`, `project_id`, `skill_id`, `request_id`, `status`, `duration_ms`가 남는다.

## 7. P1 Acceptance Criteria

P1은 workflow 연결 단계다.

- WorkflowGraph에 `skill_call` 노드가 있다.
- workflow runner가 Skill Manager를 통해 skill을 실행한다.
- Workflow Builder에서 skill 선택 또는 설정이 가능하다.
- 고객 문의 대응 template이 있다.
- 댓글 등록은 approval gate 이후에만 가능하다.

## 8. P2 Acceptance Criteria

P2는 기업 배포와 표준 MCP 확장 단계다.

- 표준 MCP SSE/HTTP adapter가 있다.
- Azure webhook 장기 작업용 async callback/job 패턴이 있다.
- APIM/NAT Gateway/forward proxy 중 하나를 기준으로 고정 egress/IP 배포 가이드가 있다.
- JWT/HMAC/mTLS 중 운영 권장 조합이 문서화되어 있다.
- 고객사 실제 문의 시스템 connector가 extn으로 분리되어 있다.

## 9. Claude Code 검증 요청 문구

Claude Code에는 다음 기준으로 검증을 요청한다.

```text
ont_platform/v5의 Skill Manager + Azure Webhook LLM + MCP Relay 긴급 업그레이드 계획을 검증해 주세요.

중점 검증:
1. core/solution/extn 경계가 타당한가?
2. MCP relay와 comment reply가 extn으로 분리되어 있는가?
3. 일반 LLM과 Azure webhook LLM이 같은 Skill contract를 쓸 수 있는가?
4. workflow runner가 특정 외부 adapter를 직접 알지 않도록 설계되어 있는가?
5. webhook signature, timeout, audit, replay 방어, secret 관리가 빠지지 않았는가?
6. side-effect skill이 approval gate 없이 실행될 위험이 없는가?
7. P0/P1/P2 순서가 실제 구현 의존성에 맞는가?
```

## 10. 최종 교통정리

바로 진행할 구현은 v5에 둔다.

- `ont_platform/v5`: 코드 구현, API, adapter, workflow integration
- `week_instructions/PHASE8`: 지시서, 검증 기준, 설계 원칙, acceptance criteria

이렇게 나누면 빠르게 만들 수 있고, 동시에 v5가 외부 connector 실험장으로 오염되는 것을 막을 수 있다.
