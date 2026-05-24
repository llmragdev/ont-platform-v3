# Phase 3 Week 3 Codex Document Naming Migration

**작성일**: 2026-05-25  
**담당**: Codex  
**상태**: Complete  
**근거 문서**: [DOCUMENT_NAMING_CONVENTION.md](../../ont_platform/v3/docs/DOCUMENT_NAMING_CONVENTION.md)

---

## 1. 목적

Phase/Week/Agent 정보가 빠진 문서명을 정리해, 문서명만으로 작업 단계와 담당 에이전트를 파악할 수 있게 한다.

적용 규칙:

```text
{PHASE[_WEEK]}_{Agent}_{Topic}_{YYYYMMDD[_HHMM]}.md
```

공통 문서는 Agent를 생략한다.

---

## 2. 변경 완료 매핑

| 기존 파일 | 신규 파일 |
|---|---|
| `PHASE2_5_STATUS.md` | `PHASE2_5_Project_Status_20260524.md` |
| `PHASE2_5_READINESS_REPORT.md` | `PHASE2_5_Readiness_Report_20260524.md` |
| `PHASE3_PARALLEL_EXECUTION_PLAN.md` | `PHASE3_Parallel_Execution_Plan_20260525.md` |
| `PHASE3_WEEK2_INSTRUCTIONS.md` | `PHASE3_WEEK2_Instructions_20260525.md` |
| `PHASE3_WEEK2_READINESS_REPORT.md` | `PHASE3_WEEK2_Readiness_Report_20260525.md` |
| `PHASE3_WEEK3_SUMMARY.md` | `PHASE3_WEEK3_Claude_Summary_20260525.md` |
| `cross-source-comparison/05_안티그래피티_종합_분석.md` | `cross-source-comparison/PHASE3_WEEK3_Antigravity_종합분석_20260524.md` |
| `cross-source-comparison/05_kodex_종합분석.md` | `cross-source-comparison/PHASE3_WEEK3_Codex_종합분석_20260524.md` |
| `cross-source-comparison/05_claude_종합분석.md` | `cross-source-comparison/PHASE3_WEEK3_Claude_종합분석_20260524.md` |
| `cross-source-comparison/05_2_안티그래피티_보완_종합_분석.md` | `cross-source-comparison/PHASE3_WEEK3_Antigravity_보완종합분석_20260524.md` |
| `cross-source-comparison/05_3_모니터링_및_성능검증_종합분석.md` | `cross-source-comparison/PHASE3_WEEK3_Monitoring_Performance_종합분석_20260524.md` |
| `ont_platform/v3/PHASE3_WEEK3_CHANGELOG_INSTRUCTIONS.md` | `ont_platform/v3/PHASE3_WEEK3_Claude_Changelog_Instructions_20260525.md` |
| `ont_platform/v3/PHASE3_WEEK4_CLAUDE_INSTRUCTIONS.md` | `week_instructions/PHASE3_WEEK4_Claude_Instructions_20260525.md` |
| `week_instructions/PHASE3_WEEK4_CODEX_INSTRUCTIONS.md` | `week_instructions/PHASE3_WEEK4_Codex_Instructions_20260525.md` |
| `week_instructions/PHASE3_WEEK4_ANTIGRAVITY_INSTRUCTIONS.md` | `week_instructions/PHASE3_WEEK4_Antigravity_Instructions_20260525.md` |
| `task_logs/claude/20260524_1930_Task3_2_FastAPIIntegration.md` | `task_logs/claude/PHASE2_5_TASK3_2_Claude_FastAPIIntegration_20260524_1930.md` |
| `task_logs/claude/20260524_2104_Antigravity_Week4_LoadTest_Complete.md` | `task_logs/claude/PHASE2_5_WEEK4_Antigravity_LoadTest_Complete_20260524_2104.md` |
| `task_logs/claude/20260524_2105_Codex_Week3_E2E_Complete.md` | `task_logs/claude/PHASE2_5_WEEK3_Codex_E2E_Complete_20260524_2105.md` |
| `task_logs/claude/20260525_0015_Codex_SPARQL_API_Contract_Alignment.md` | `task_logs/claude/PHASE3_WEEK3_Codex_SPARQL_API_Contract_Alignment_20260525_0015.md` |
| `task_logs/claude/20260525_0030_Antigravity_Phase3_Week1_Baseline_Setup.md` | `task_logs/claude/PHASE3_WEEK1_Antigravity_Baseline_Setup_20260525_0030.md` |
| `task_logs/claude/20260525_Claude_Week2_Integration_Tests_Complete.md` | `task_logs/claude/PHASE3_WEEK2_Claude_Integration_Tests_Complete_20260525.md` |
| `task_logs/claude/20260525_Claude_Week3_Task1_Changelog_Complete.md` | `task_logs/claude/PHASE3_WEEK3_Claude_Task1_Changelog_Complete_20260525.md` |
| `task_logs/claude/20260525_Claude_Week3_Task2_SAP_API_Mock_Complete.md` | `task_logs/claude/PHASE3_WEEK3_Claude_Task2_SAP_API_Mock_Complete_20260525.md` |
| `task_logs/claude/20260525_Claude_Week3_Task3_WriteBackWorker_Complete.md` | `task_logs/claude/PHASE3_WEEK3_Claude_Task3_WriteBackWorker_Complete_20260525.md` |
| `task_logs/claude/20260525_Claude_Week3_Task4_Integration_Test_Complete.md` | `task_logs/claude/PHASE3_WEEK3_Claude_Task4_Integration_Test_Complete_20260525.md` |
| `task_logs/claude/20260525_Phase3_Final_Integration_Report.md` | `task_logs/claude/PHASE3_Final_Integration_Report_20260525.md` |
| `task_logs/claude/20260607_Codex_Week2_E2E_Complete.md` | `task_logs/claude/PHASE3_WEEK2_Codex_E2E_Complete_20260607.md` |

---

## 3. 링크 수정

Markdown 문서 내부의 기존 파일명 참조를 신규 파일명으로 일괄 치환했다.

제외 경로:

- `backup_old/**`
- `v1_legacy/**`
- `references/old/**`

이 경로들은 원본 보존 성격이 강해 rename 및 링크 치환 대상에서 제외했다.

---

## 4. 검증

다음 주요 옛 파일명은 Markdown 문서 기준으로 더 이상 검색되지 않음을 확인했다.

```text
PHASE2_5_STATUS.md
PHASE3_WEEK2_INSTRUCTIONS.md
PHASE3_WEEK2_READINESS_REPORT.md
PHASE3_WEEK3_SUMMARY.md
05_kodex_종합분석.md
05_claude_종합분석.md
05_안티그래피티_종합_분석.md
20260607_Codex_Week2_E2E_Complete.md
20260525_Claude_Week2_Integration_Tests_Complete.md
20260524_2105_Codex_Week3_E2E_Complete.md
20260524_1930_Task3_2_FastAPIIntegration.md
```

---

## 5. 보류 대상

다음 문서군은 단계 정보가 불명확하거나 원본 보존 가치가 높아 이번 변경에서 제외했다.

- `cross-source-comparison/01_*` ~ `04_*`
- `requirements/**`
- `references/**`
- `Codex-통합/backup_old/**`
- `ont_platform/v1_legacy/**`
- 일반 고정 문서: `README.md`, `CLAUDE.md`, `STATUS.md`, `FINAL_STATUS.md`

필요하면 별도 마이그레이션 표를 만든 뒤 2차 정리 대상으로 진행한다.
