# Frontend UI Week 2 Notes

> Team: Codex  
> Scope: Phase 2.5 Week 2, SPARQL query UI foundation  
> Date: 2026-05-24

## Implemented

- Added `SPARQLWorkbench` view under the sidebar item `SPARQL 콘솔`.
- Added reusable query execution hook: `src/hooks/useSparqlQuery.ts`.
- Added `QueryResult` with table, JSON, and debug tabs.
- Added lightweight `PerformanceChart` without new chart dependencies.
- Added `api.sparql.query()` client method for `POST /api/sparql/query`.
- Added local query history with duration, status, row count, and query type.
- Added demo fallback response when the backend SPARQL endpoint is not ready.

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
POST /api/sparql/query
Content-Type: application/json

{ "query": "SELECT ?entity WHERE { ... }" }
```

Expected response shape is intentionally tolerant:

```json
{
  "type": "SELECT",
  "results": [],
  "query_time_ms": 45,
  "translator_used": true,
  "sql_generated": "SELECT ...",
  "explain": "..."
}
```

If the endpoint is unavailable, the UI shows a demo response and preserves the error message for debugging.

## Verification

Attempted:

```bash
npm run build
```

Result: not run in the current shell because `npm` is not available on PATH.

## Remaining

- Replace textarea with Monaco Editor if dependency budget allows.
- Wire graph tab after Claude's result shape stabilizes.
- Add Cypress tests in Week 4.
- Validate in browser once `npm` is available.

