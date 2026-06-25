# Frontend UI Week 2 Notes

> Team: Codex  
> Scope: Phase 2.5 Week 2, SPARQL query UI foundation  
> Date: 2026-05-24

## Implemented

- Added `SPARQLWorkbench` view under the sidebar item `SPARQL 콘솔`.
- Added reusable query execution hook: `src/hooks/useSparqlQuery.ts`.
- Added `QueryResult` with table, JSON, and debug tabs.
- Added lightweight `PerformanceChart` without new chart dependencies.
- Added `api.sparql.query()` client method for `POST /api/ontology/sparql`.
- Added local query history with duration, status, row count, and query type.
- Demo fallback is disabled by default so API failures remain visible to E2E.

## Files

```text
src/components/SPARQLWorkbench.tsx
src/components/QueryResult.tsx
src/components/PerformanceChart.tsx
src/hooks/useSparqlQuery.ts
src/lib/api.ts
src/types/api.ts
src/components/Sidebar.tsx
src/app/page.tsx
```

## API Contract Assumption

The UI calls:

```http
POST /api/ontology/sparql
Content-Type: application/json

{ "query": "SELECT ?entity WHERE { ... }" }
```

Expected response shape is intentionally tolerant:

```json
{
  "source": "sql_translator",
  "type": "SELECT",
  "query_type": "SELECT",
  "select_vars": ["?entity"],
  "results": [],
  "result_count": 0,
  "execution_time_ms": 45,
  "translator_used": true,
  "sql_generated": "SELECT ...",
  "warnings": []
}
```

If the endpoint is unavailable, the UI records an error result. Local demos can opt in to frontend-only demo data with `NEXT_PUBLIC_ENABLE_SPARQL_DEMO_FALLBACK=true`.

## Verification

Build passed with the `claud_fe` conda environment:

```bash
$env:PATH='C:\Users\nkchoi2\anaconda3\envs\claud_fe;' + $env:PATH
npm run build
```

Result:

```text
✓ Compiled successfully
✓ Generating static pages (4/4)
Route / First Load JS: 168 kB
```

Lint was attempted, but `next lint` opened the interactive ESLint setup prompt because ESLint is not configured yet.

## Remaining

- Replace textarea with Monaco Editor if dependency budget allows.
- Wire graph tab after Claude's result shape stabilizes.
- Add Cypress tests in Week 4.
- Add non-interactive ESLint config.
- Validate in browser screenshot flow.
