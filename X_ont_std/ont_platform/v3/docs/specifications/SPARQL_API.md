# SPARQL API Contract

Canonical endpoint:

```http
POST /api/ontology/sparql
```

Compatibility alias:

```http
POST /api/sparql/query
```

Request:

```json
{
  "query": "SELECT ?entity WHERE { ?entity ?p ?o }",
  "limit": 1000
}
```

Success response shape is shared by SQL translator and rdflib fallback:

```json
{
  "source": "sql_translator",
  "type": "SELECT",
  "query_type": "SELECT",
  "select_vars": ["?entity"],
  "head": { "vars": ["entity"] },
  "patterns": 1,
  "pattern_ids": [],
  "results": [],
  "triples": [],
  "boolean": null,
  "result_count": 0,
  "execution_time_ms": 12.4,
  "sql_generated": "SELECT ...",
  "cache_hit": false,
  "warnings": [],
  "translator_used": true
}
```

`source` values:

```text
sql_translator | rdflib | demo | error
```

`demo` is frontend-only and must not be counted as API success in E2E. It is disabled by default and can be enabled only for local UI demos with `NEXT_PUBLIC_ENABLE_SPARQL_DEMO_FALLBACK=true`.

Error response shape:

```json
{
  "source": "rdflib",
  "query_type": "SELECT",
  "select_vars": [],
  "patterns": 0,
  "pattern_ids": [],
  "results": [],
  "result_count": 0,
  "execution_time_ms": 0,
  "sql_generated": null,
  "cache_hit": false,
  "warnings": [],
  "error": {
    "code": "SPARQL_EXECUTION_ERROR",
    "message": "SPARQL execution failed.",
    "type": "RdflibExecutionError"
  }
}
```

Frontend expectations:

- Call `/api/ontology/sparql` directly.
- Accept `/api/sparql/query` only as a backend compatibility alias.
- Treat `source: "sql_translator"` as hot-path SQL success.
- Treat `source: "rdflib"` as valid fallback success only when no `error` exists.
- Treat network/API errors as query failure; do not silently replace them with demo success.
