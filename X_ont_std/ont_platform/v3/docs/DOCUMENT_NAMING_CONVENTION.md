# Document Naming Convention

**작성일**: 2026-05-25  
**적용 범위**: 활성 Phase 문서, 에이전트 작업 로그, 현재 비교/검토 보고서  
**목적**: 문서명만 보고 단계, 주차, 담당 에이전트, 주제, 작성 시점을 파악할 수 있게 한다.

---

## 1. 기본 규칙

```text
{PHASE[_WEEK]}_{Agent}_{Topic}_{YYYYMMDD[_HHMM]}.md
```

에이전트가 없거나 공통 문서인 경우:

```text
{PHASE[_WEEK]}_{Topic}_{YYYYMMDD[_HHMM]}.md
```

## 2. 구성 요소

| 요소 | 규칙 | 예시 |
|---|---|---|
| Phase | `PHASE2_5`, `PHASE3`, `PHASE3_WEEK2`처럼 대문자 사용 | `PHASE3_WEEK3` |
| Agent | `Claude`, `Codex`, `Antigravity` 중 하나를 우선 사용 | `Codex` |
| Topic | 문서 성격을 2~6개 단어로 표현 | `SPARQL_API_Contract_Alignment` |
| Date | 작성일 또는 완료일을 뒤에 배치 | `20260525` |
| Time | 같은 날 여러 산출물이 있으면 선택적으로 추가 | `20260525_0015` |

## 3. 권장 예시

```text
PHASE3_WEEK2_Codex_E2E_Complete_20260607.md
PHASE3_WEEK3_Claude_Changelog_Instructions_20260525.md
PHASE3_WEEK3_Codex_종합분석_20260524.md
PHASE2_5_Project_Status_20260524.md
```

## 4. 제외 대상

다음 문서는 원본성 또는 레거시 추적성이 중요하므로 일괄 변경 대상에서 제외한다.

- `backup_old/**`
- `v1_legacy/**`
- `references/old/**`
- 외부 요구사항 원문, 교육자료, 아카이브 문서
- `README.md`, `CLAUDE.md`, `STATUS.md`처럼 도구나 관례가 직접 참조할 수 있는 루트 고정 문서

## 5. 변경 절차

1. 변경 대상 목록을 먼저 만든다.
2. `기존 파일명 -> 신규 파일명` 매핑을 작업 로그에 남긴다.
3. 파일명을 변경한다.
4. Markdown 문서 안의 상대 링크와 파일명 참조를 함께 수정한다.
5. 옛 파일명이 남아 있는지 `rg`로 확인한다.

---

## 6. 이번 적용 결과

2026-05-25 기준으로 Phase 2.5/Phase 3 활성 문서, Phase 3 Week 3 종합분석 문서, 최근 Claude/Codex/Antigravity 작업 로그에 우선 적용했다.

상세 매핑은 [PHASE3_WEEK3_Codex_Document_Naming_Migration_20260525.md](../../../task_logs/claude/PHASE3_WEEK3_Codex_Document_Naming_Migration_20260525.md)에 기록한다.
