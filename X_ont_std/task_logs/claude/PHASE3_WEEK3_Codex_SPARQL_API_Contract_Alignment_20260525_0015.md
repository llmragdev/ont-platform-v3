# Codex SPARQL API Contract Alignment

**Date**: 2026-05-25 00:15  
**Team**: Codex  
**Scope**: Frontend/backend SPARQL endpoint and response contract alignment  
**Status**: CODE DONE, frontend build pass

## Summary

Aligned the SPARQL workbench with a fixed contract centered on `POST /api/ontology/sparql`, with `POST /api/sparql/query` retained as a backend compatibility alias.

## Changes

- Added `ont_platform/v3/docs/SPARQL_API_CONTRACT.md`.
- Backend now exposes a normalized contract response for SQL translator and rdflib fallback paths.
- Backend SQL translator result includes `sql_generated`.
- Frontend `api.sparql.query()` now calls `/api/ontology/sparql`.
- Frontend `SparqlQueryResponse` type accepts `sql_translator | rdflib | demo | error` sources and contract fields.
- Demo fallback is disabled by default; API/network failures no longer appear as successful demo results.
- `QueryResult` now displays SQL/rdflib/demo source badges and reads `query_type`, `warnings`, and `sql_generated`.

## Verification

Frontend:

```powershell
cd ont_platform/v3/src/frontend
$env:PATH='C:\Users\nkchoi2\anaconda3\envs\claud_fe;' + $env:PATH
npm run build
```

Result: pass.

Backend:

```powershell
cd ont_platform/v3/src/backend
$env:PATH='C:\Users\nkchoi2\anaconda3\envs\claud_be;' + $env:PATH
python -m py_compile app/main.py app/services/sparql_translator.py app/services/sparql_translator_service.py
```

Result: pass.

`python -m pytest tests/test_sparql_translator_integration.py -q` still fails in setup because the existing SQLite fixture inserts `relationships` rows without required `domain_id` values. This is separate from the SPARQL contract changes.

## Remaining

- Update SQLite/PostgreSQL fixtures so SPARQL translator integration tests can run cleanly.
- Add executable browser E2E once backend test fixtures are stable.
