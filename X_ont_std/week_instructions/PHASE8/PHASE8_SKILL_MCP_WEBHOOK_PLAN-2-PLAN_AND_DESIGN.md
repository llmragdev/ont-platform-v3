# PHASE8 - 2. 계획 및 확장 설계

작성일: 2026-06-12

## 1. 목적

P0 이후 검토할 확장 계획을 보관한다. 지금 긴급 구현 범위에는 넣지 않는다.

상세 설계:

- `ont_platform/v5/SKILL_MCP_WEBHOOK_UPGRADE_PLAN-2-PLAN_AND_DESIGN.md`

## 2. 확장 후보

- Workflow `skill_call` 노드
- Skill Manager 일반화
- RAG 문서 업로드/검색
- 온톨로지 규칙 기반 workflow
- 고객 문의 batch trigger
- 승인 workflow
- 표준 MCP SSE/HTTP transport
- async callback/job
- 운영 배포 guide

## 3. Phase8 검증 기준

- 고객사 MCP 서버는 고객사 책임으로 유지한다.
- v5는 MCP client adapter까지만 책임진다.
- workflow와 extn adapter를 분리한다.
- side-effect 호출에는 dry-run/approval 정책을 둔다.
- 확장 설계가 P0 구현을 지연시키지 않는다.

