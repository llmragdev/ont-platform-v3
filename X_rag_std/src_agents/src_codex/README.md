# src_codex RAG Backend

Codex implementation for `AI_Agent_Mission_Directive.md`.

## Run

For the full Windows/conda workflow, see `RUN_GUIDE.md`.

```bash
cd E:\ontology_edu\X_rag_std\src_agents\src_codex
pip install -r requirements.txt
uvicorn main:app --reload --port 8010
```

By default the app uses embedded SQLite at `storage/metadata.db`, so no RDBMS
server is required for local development and testing.

Provider selection is environment-driven. Local/offline defaults are hash
embeddings and a deterministic mock LLM:

```bash
set EMBEDDING_PROVIDER=hash
set LLM_PROVIDER=mock
```

For Gemini, run the central gateway and point this RAG service at it. Gemini API
keys stay in the gateway; `src_codex` only calls HTTP endpoints:

```bash
set EMBEDDING_PROVIDER=gemini_http
set LLM_PROVIDER=gemini_http
set LLM_GATEWAY_URL=http://localhost:8010
```

Vector DB engine selection:

```bash
# default local JSON store
set VECTOR_DB_ENGINE=local_json

# Chroma HTTP store
set VECTOR_DB_ENGINE=chroma
set CHROMA_HOST=localhost
set CHROMA_PORT=8001
```

To switch databases without code changes, set `DATABASE_URL`:

```bash
# SQLite, default
set DATABASE_URL=sqlite:///./storage/metadata.db

# PostgreSQL example
set DATABASE_URL=postgresql+psycopg://user:password@host:5432/ragdb

# MySQL example
set DATABASE_URL=mysql+pymysql://user:password@host:3306/ragdb
```

Health check:

```bash
GET /api/v1/health
```

## Automated Smoke Test

Run the same endpoint flow used for implementation verification:

```bash
python test_endpoints.py
```

It checks:

- health endpoint
- document upload and pipeline completion
- document list
- RAG search with `debug_mode=false`
- RAG search with `debug_mode=true`
- `candidate_chunks` only appear in debug mode

For the real reference document test:

```bash
python test_ai_voucher_pdf.py
```

This uploads
`E:\ontology_edu\ont_platform\docs\ref_data\01_raw\2025년 AI바우처 사업설명회 발표자료.pdf`
and validates normal/debug RAG search against the uploaded PDF chunks.

## Implemented APIs

### Document Pipeline

`POST /api/v1/documents/upload`

Multipart form fields:

- `file`: PDF or text-like document
- `category_mid`: required routing category
- `category_low`: optional subcategory
- `vector_db_id`: optional forced physical vector DB id

Optional header:

- `X-Company-ID`: tenant id, defaults to `default`

The service stores the raw document, parses text, chunks it, creates deterministic
local or Gemini-gateway embeddings, routes it to a physical vector store, and
records state in `wc_project_rag_doc`.

State transition:

```text
pending -> processing -> completed / error
```

`PUT /api/v1/documents/{doc_id}` performs an incremental update by deleting the
old chunks for that document and inserting the new chunk set.

`DELETE /api/v1/documents/{doc_id}` deletes the RDBMS document row and its vector
chunks.

`GET /api/v1/documents` returns RDBMS metadata records.
The list is scoped by `X-Company-ID`.

### Projects

`POST /api/v1/projects`

```json
{
  "project_code": "123456",
  "project_name": "테스트 프로젝트",
  "vector_db_id": "vdb_policy_01"
}
```

`GET /api/v1/projects` lists projects.

`GET /api/v1/projects/{project_code}` returns one project.

`DELETE /api/v1/projects/{project_code}` deletes the project and removes its
document vectors.

### Categories

`POST /api/v1/categories`

```json
{
  "category_mid": "규정",
  "category_low": "인사",
  "vector_db_id": "vdb_policy_01"
}
```

`GET /api/v1/categories` lists categories.

`DELETE /api/v1/categories/{category_id}` deletes a category row.

### RAG Search

`POST /api/v1/rag/search`

```json
{
  "query": "검색 질의",
  "top_k": 5,
  "debug_mode": true,
  "filters": {
    "category_mid": "규정",
    "vector_db_id": "vdb_policy_01"
  }
}
```

Optional header:

- `X-Company-ID`: tenant id, defaults to `default`; vector search is forcibly
  scoped to this value.

The response follows the standard layout:

- `used_chunks`: chunks selected for answer generation
- `debug_info.candidate_chunks`: returned only when `debug_mode` is `true`
- chunk metadata includes `source_name`, `source_url`, `page_no`,
  `category_mid`, `vector_db_id`, `company_id`, and `doc_id`

`POST /api/v1/rag/search/stream` returns the generated answer as SSE
(`text/event-stream`).

## Architecture Mapping

- Remote Retriever separation:
  `RagSearchService` calls `VectorDbRouter`, which returns an adapter. It does
  not use LangChain retrievers.
- Router/Adapter pattern:
  `VectorDbRouter` loads `storage/vector_routing.json`, resolves `vector_db_id`,
  and creates `LocalJsonVectorDbAdapter`.
- Physical vector DB split:
  each `vector_db_id` is stored separately under `storage/vector_store/*.json`.
- Chroma support:
  set `VECTOR_DB_ENGINE=chroma`. The Chroma adapter stores document embeddings
  from the same embedding provider used for query embeddings, avoiding mixed
  vector spaces.
- Provider boundary:
  `providers.py` selects local hash/mock providers or Gemini gateway HTTP
  clients through environment variables. The RAG service does not read Gemini API
  keys.
- Tenant isolation:
  `X-Company-ID` is stored in RDBMS records and vector chunk metadata, and RAG
  search always injects `company_id` into adapter filters.
- RDBMS schema:
  SQLAlchemy models implement `ca_company`, `ca_org_mgnt`, `ca_user`,
  `wc_project`, `wc_category`, `wc_intent`, `wc_project_rag_doc`, and
  `wc_dialog_history`.
- DB portability:
  the SQLAlchemy engine is configured only through `DATABASE_URL`. Local runs use
  SQLite by default, while PostgreSQL/MySQL can be selected by environment
  variable without changing source code.
- Error naming:
  custom errors include `document_parsing_error`, `embedding_api_timeout`, and
  `vector_db_connection_error`.

## Notes

The local embedding and LLM clients are deterministic stand-ins so the project is
immediately runnable in this isolated workspace. Gemini gateway clients are
available through provider settings without changing the API, router, or adapter
contracts.

## Upgrade Plan

See `UPGRADE_PLAN_GEMINI_GATEWAY_RAG.md` for the staged upgrade plan and
completion notes.
