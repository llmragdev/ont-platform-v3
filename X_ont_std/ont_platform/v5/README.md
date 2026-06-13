# ont_platform v5

`v5` is the PHASE8 development version. `v4` is preserved as the baseline.

## Read This First

If you are a new agent or reviewer, use this order. This prevents confusion between status reports, original plans, and narrowed implementation plans.

1. `README.md`
   - Entry point and document map.

2. `RUNBOOK.md`
   - How to start backend/frontend and verify the local environment.

3. `WORKFLOW_V5_PROGRESS_REPORT.md`
   - Current implementation status. Read this to understand what has already been changed.

4. `SKILL_MCP_WEBHOOK_UPGRADE_PLAN-1-PRIORITY_IMPLEMENTATION.md`
   - Current implementation target.
   - This is the active P0 scope for LLM webhook comment generation and customer MCP server integration.

5. `SKILL_MCP_WEBHOOK_UPGRADE_PLAN-2-PLAN_AND_DESIGN.md`
   - Future design backlog.
   - RAG, batch, ontology rule engine, generic Skill Manager UI, workflow `skill_call`, standard MCP transport, and async callback belong here for now.

6. `SKILL_MCP_WEBHOOK_UPGRADE_PLAN.md`
   - Original high-level upgrade plan.
   - Keep it as background context, but do not treat it as the active implementation scope.

## Current Active Scope

The active P0 scope is intentionally narrow:

```text
customer question
  -> LLM webhook generates reply message
  -> v5 calls customer MCP server
  -> customer MCP server calls customer API
  -> v5 stores result/audit
```

Boundary rule:

- Customer MCP server is owned by the customer, not by this solution.
- v5 owns only the extn adapter that calls the customer MCP server.
- v5 must not call the customer API directly.
- Workflow remains the solution core.

Core additions:

- `/api/v5/hybrid/ask`
- `SearchMode`: `auto`, `ontology_only`, `vector_only`, `hybrid`
- `QuestionAnalyzer`
- `EvidenceGate`
- no-answer policy before LLM synthesis
- `answer_policies.jsonl` as the shared policy source

Rule:

```text
Do not modify v4 for PHASE8 work. Develop and evaluate v5 separately.
```

## Document Roles

| Document | Role | Active? |
| --- | --- | --- |
| `WORKFLOW_V5_PROGRESS_REPORT.md` | Current v5 progress/status report | Reference |
| `SKILL_MCP_WEBHOOK_UPGRADE_PLAN-1-PRIORITY_IMPLEMENTATION.md` | Immediate implementation plan | Yes |
| `SKILL_MCP_WEBHOOK_UPGRADE_PLAN-2-PLAN_AND_DESIGN.md` | Future design and backlog | Not P0 |
| `SKILL_MCP_WEBHOOK_UPGRADE_PLAN.md` | Original broad upgrade plan | Background |
| `scenarios/v1/scenario1/10_REQUIREMENTS_OVERALL.md` | Scenario 1 overall requirements | Active requirements |
| `scenarios/v1/scenario1/11_REQUIREMENTS_ONT_PLATFORM.md` | Scenario 1 ont_platform requirements | Active requirements |
| `scenarios/v1/scenario1/12_REQUIREMENTS_CUSTOMER_MCP.md` | Scenario 1 customer MCP requirements | Active requirements |
| `scenarios/v1/scenario1/20_CUSTOMER_MCP_CALL_SPEC.md` | Customer MCP call contract for P0 Scenario 1 | Active contract |
| `scenarios/v1/scenario1/30_TRIGGER_DESIGN.md` | Scenario 1-1 batch polling and Scenario 1-2 webhook/API trigger design | Next design |
| `DEMO_PROJECT_DATA_PLAN.md` | Demo/test data project plan | Separate track |
| `DEMO_PROJECT_DATA_PLAN_ADDENDUM.md` | Demo/test data plan addendum | Separate track |
| `CLAUDE_VALIDATION_FOLLOWUP.md` | Claude validation follow-up report | Reference |

