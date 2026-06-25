# PHASE8 - 1. 우선 구현 지시

작성일: 2026-06-12

## 1. 즉시 구현 범위

이번 긴급 구현은 다음 하나의 흐름에 집중한다.

```text
LLM Webhook으로 댓글 메시지 생성
  -> 고객사 MCP 서버 호출
  -> 고객사 MCP 서버가 고객사 API 호출
```

고객사 MCP 서버는 고객사 영역이다. v5는 고객사 MCP 서버를 호출하는 adapter만 구현한다.

## 2. 구현 위치

- 구현: `ont_platform/v5`
- 기준 문서: `ont_platform/v5/SKILL_MCP_WEBHOOK_UPGRADE_PLAN-1-PRIORITY_IMPLEMENTATION.md`
- Phase8 역할: 범위 통제와 검증

## 3. 금지 사항

- 고객사 API를 v5에서 직접 호출하지 않는다.
- 고객사 MCP 서버를 우리 solution으로 분류하지 않는다.
- P0에 RAG, batch, 온톨로지 규칙 엔진, 표준 MCP 전체 구현을 끼워 넣지 않는다.
- 실제 댓글 등록은 기본값으로 켜지지 않는다.

## 4. P0 Acceptance

- LLM webhook으로 댓글 초안 생성
- 고객사 MCP 서버 호출 payload 생성
- dry-run 모드로 댓글 등록 흐름 검증
- audit 저장
- 장애 응답 정규화

