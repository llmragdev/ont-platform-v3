# Codex / Antigravity Next Instructions

**Date**: 2026-05-24 18:07  
**Phase**: Phase 2.5  
**Audience**: Codex, Antigravity  
**Source**: Claude coordination note  
**Status**: 전달 완료 문서

---

## Current Position

Claude is ready to proceed after the dependent team outputs are reviewed.

Current coordination state:

```text
1. PHASE2_5_Project_Status_20260524.md needs final synchronization.
2. Before Week 3 starts, Claude Task 3-1 completion should be reflected.
3. Codex and Antigravity should update their own sections only after completion.
4. Claude will then proceed to Task 3-2 and Task 3-3.
```

Important rule:

```text
Do not edit another team's section in PHASE2_5_Project_Status_20260524.md.
Use task logs for detailed handoff and evidence.
```

---

## Codex Instructions

### Target

```text
Codex completion target: 2026-06-07
```

### Week 2 Tasks

```text
UI-1: QueryResult component
UI-2: Performance charts
UI-3: Responsive design
```

### Completion Criteria

Codex should complete and provide:

```text
1. QueryResult UI that can display Claude SPARQL->SQL results
2. Query result table / JSON / debug view
3. Performance chart area
4. Responsive layout
5. Build verification if Node/npm is available
6. Task log
7. PHASE2_5_Project_Status_20260524.md Codex section update only
```

### Handoff Needed From Claude

Codex needs the following from Claude to finish final API binding:

```text
1. /api/sparql/query response shape
2. SELECT variables format
3. Row/binding structure
4. query_time_ms field
5. translator_used field
6. sql_generated / explain debug fields
7. Error response format
```

### Handoff Needed From Antigravity

Codex needs the following from Antigravity for performance charts:

```text
1. Pattern #18-26 latency data
2. Simple / one-hop / two-hop latency targets
3. Response-time distribution
4. Cache hit/miss ratio
5. Any final benchmark labels to display in UI
```

### After Completion

Codex must:

```text
1. Write task log:
   task_logs/claude/YYYYMMDD_HHMM_Codex_Week2_Complete.md

2. Update PHASE2_5_Project_Status_20260524.md Codex section:
   UI-1 / UI-2 / UI-3 -> ✅ DONE

3. Notify:
   [Codex] Week 2 complete - check PHASE2_5_Project_Status_20260524.md and task log.
```

### Claude Review After Codex Completion

Claude should review:

```text
1. Task Log
2. UI integration with Claude SQL result format
3. Build/test result
4. Whether the API response shape needs adjustment
```

---

## Antigravity Instructions

### Target

```text
Antigravity completion target: 2026-06-14
```

### Expected Focus

```text
1. Performance analysis results
2. Query optimization recommendations
3. Index tuning results
4. Cache strategy evidence
5. Load-test report
```

### Completion Criteria

Antigravity should complete and provide:

```text
1. Performance benchmark results
2. Optimization report
3. Applied or recommended index changes
4. Load-test results
5. Cache hit/miss analysis
6. Task log
7. PHASE2_5_Project_Status_20260524.md Antigravity section update only
```

### Claude Review After Antigravity Completion

Claude should review:

```text
1. Performance analysis result
2. Whether recommended indexes should be applied
3. Impact on SPARQL->SQL translator query plans
4. Whether FastAPI endpoint should expose performance metadata
5. Whether cache metrics should be returned to Codex UI
```

### After Completion

Antigravity must:

```text
1. Write task log:
   task_logs/claude/YYYYMMDD_HHMM_Antigravity_Week3_Complete.md

2. Update PHASE2_5_Project_Status_20260524.md Antigravity section:
   PERF tasks -> ✅ DONE

3. Notify:
   [Antigravity] Week 3 complete - check PHASE2_5_Project_Status_20260524.md and performance reports.
```

---

## Claude Next Tasks

After Codex and Antigravity outputs are reviewed, Claude proceeds with:

```text
Task 3-2: FastAPI endpoint integration
Task 3-3: End-to-end integration tests
Phase 2.5 final completion
```

### Task 3-2: FastAPI Integration

Claude should prepare:

```text
1. POST /api/sparql/query
2. POST /api/sparql/explain
3. GET /api/sparql/health
4. Response shape compatible with Codex UI
5. Performance metadata fields compatible with Antigravity metrics
```

Recommended response shape:

```json
{
  "type": "SELECT",
  "head": { "vars": ["part", "cost"] },
  "results": [
    {
      "part": { "type": "uri", "value": "entity:part-001" },
      "cost": { "type": "literal", "value": "1200" }
    }
  ],
  "query_time_ms": 45,
  "translator_used": true,
  "sql_generated": "SELECT ...",
  "explain": "...",
  "cache": {
    "hit": false,
    "key": "sparql:..."
  }
}
```

### Task 3-3: E2E Integration Tests

Claude should prepare:

```text
1. SPARQL query -> SQL translator -> DB result
2. API response -> Codex QueryResult render
3. Performance metadata -> Codex PerformanceChart render
4. Optimized query path -> Antigravity performance target validation
```

---

## Status File Update Reminder

`PHASE2_5_Project_Status_20260524.md` should be updated sequentially:

```text
1. Claude marks Task 3-1 complete before Week 3 starts.
2. Codex updates only Codex section after Week 2 completion.
3. Antigravity updates only Antigravity section after completion.
4. Claude proceeds with Task 3-2/3-3 after review.
```

Do not overwrite another team's section.

---

## Broadcast Messages

For Codex:

```text
[Codex] Please complete Week 2 UI tasks and update only the Codex section in PHASE2_5_Project_Status_20260524.md. Claude will review QueryResult integration after your task log is ready.
```

For Antigravity:

```text
[Antigravity] Please complete performance analysis and update only the Antigravity section in PHASE2_5_Project_Status_20260524.md. Claude will review optimization recommendations before Task 3-2/3-3 integration.
```

For Claude:

```text
[Claude] After Codex and Antigravity handoffs, proceed to Task 3-2 FastAPI endpoint integration and Task 3-3 E2E tests.
```

