# src_codex v3 설계서

작성일: 2026-05-15

## 1. 설계 방향

v3는 `RAG_표준_설계_v1.3.md`의 멀티테넌트/조직 격리 정책을 구현하는 운영 후보 구조를 목표로 한다. 핵심 원칙은 다음과 같다.

- RAG 서버는 Gemini API key를 직접 보관하지 않는다.
- RAG 서버는 `LLM_GATEWAY_URL`만 알고, Gemini Gateway가 키·모델·쿼타·감사 로그를 관리한다.
- 모든 저장/검색/삭제/수정 경로는 `tenant_id`를 기준으로 격리한다.
- 조직 범위는 `org_id`, 부서 범위는 `dept_code`로 처리한다.
- Vector DB에는 scalar metadata만 저장한다.
- 문서 embedding과 query embedding은 반드시 동일한 Gateway embedding 서비스를 사용한다.

## 2. 패키지 구조 제안

기존 `src_codex/app` 구조를 유지하되 v3에서 다음 모듈을 추가 또는 정리한다.

```text
app/
  api/
    dependencies.py          # tenant/org/user context resolver
    documents.py
    rag.py
    projects.py
    categories.py
  core/
    errors.py                # 표준 error_code/exception
    time.py                  # timezone-aware UTC helper
    auth_context.py          # UserContext, OrgScope
  db/
    session.py
    migrations/              # Alembic
  models/
    db_models.py
    schemas.py
  repositories/
    company_repository.py
    org_repository.py
    document_repository.py
    dialog_repository.py
    project_repository.py
    category_repository.py
  services/
    document_pipeline.py
    rag_service.py
    tenant_scope.py          # v1.3 scope policy
    vector_adapters.py
    vector_router.py
    gemini_http_embedding.py
    gemini_http_llm.py
```

## 3. Request Context 설계

API 계층은 header를 직접 서비스로 넘기지 않고 `RequestContext`로 정규화한다.

```python
class UserContext(BaseModel):
    user_id: str | None = None
    tenant_id: str
    org_id: str | None = None
    is_admin: bool = False
    is_system: bool = False

class RequestContext(BaseModel):
    tenant_id: str
    requested_org_id: str | None
    resolved_org_id: str | None
    scope_level: Literal["team", "department", "tenant"]
    user: UserContext
```

### 3.1. Tenant 해석

```python
def get_tenant_id(request: Request) -> str:
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise StandardHttpError(400, "tenant_header_required", "X-Tenant-ID header is required")
    return tenant_id
```

`X-Company-ID`는 운영 경로에서 사용하지 않는다. legacy 호환이 필요하면 설정값 `ENABLE_COMPANY_ID_LEGACY_HEADER=false`로 기본 비활성화한다.

### 3.2. Org Scope 해석

```python
def resolve_org_scope(requested_org_id: str | None, user: UserContext) -> OrgScope:
    if requested_org_id:
        if requested_org_id.endswith("00"):
            return OrgScope(level="department", org_id=requested_org_id, dept_code=requested_org_id[:2])
        return OrgScope(level="team", org_id=requested_org_id, dept_code=requested_org_id[:2])

    if user.is_admin or user.is_system:
        return OrgScope(level="tenant", org_id=None, dept_code=None)

    if user.org_id:
        return OrgScope(level="team", org_id=user.org_id, dept_code=user.org_id[:2])

    raise StandardHttpError(403, "org_scope_required", "조직 정보가 없는 사용자는 검색 범위를 지정해야 합니다")
```

## 4. RDBMS 설계 변경

### 4.1. 주요 테이블

```text
ca_company
  tenant_id PK
  company_name
  created_at
  is_active

ca_org_mgnt
  tenant_id PK/FK -> ca_company.tenant_id
  org_id PK
  org_name
  dept_code
  org_level
  parent_tenant_id
  parent_org_id
  created_at
  is_active

ca_user
  user_id PK
  tenant_id FK
  org_id nullable
  user_name
  email
  is_admin
  is_active

wc_project
  project_code PK
  tenant_id FK
  project_name
  vector_db_id
  created_at
  updated_at

wc_project_rag_doc
  doc_id PK
  project_code FK
  tenant_id FK
  org_id nullable
  file_name
  source_url
  category_mid
  category_low
  assigned_vector_db
  tags_json nullable
  pipeline_status
  version
  error_message
  created_at
  updated_at

wc_dialog_history
  dialog_id PK
  tenant_id FK
  org_id nullable
  project_code nullable
  user_id nullable
  query
  answer
  used_chunks_meta JSON
  execution_time_ms
  created_at
```

### 4.2. 복합 FK 원칙

`org_id`는 테넌트 안에서만 고유하다. 따라서 조직 참조는 `(tenant_id, org_id)`를 기준으로 한다.

```text
ca_user.(tenant_id, org_id) -> ca_org_mgnt.(tenant_id, org_id)
wc_project_rag_doc.(tenant_id, org_id) -> ca_org_mgnt.(tenant_id, org_id)
wc_dialog_history.(tenant_id, org_id) -> ca_org_mgnt.(tenant_id, org_id)
```

`org_id IS NULL`은 전사 공유 문서 또는 전사 검색 이력을 의미한다.

## 5. Vector Metadata 설계

### 5.1. 저장 필드

```json
{
  "doc_id": "uuid",
  "tenant_id": "company_abc",
  "org_id": "0102",
  "dept_code": "01",
  "source_name": "policy.pdf",
  "source_url": "storage://...",
  "created_at": "2026-05-15T10:30:00+09:00",
  "vector_db_id": "vdb_policy_01",
  "category_mid": "policy",
  "category_low": "hr",
  "page_no": 12,
  "chunk_type": "text"
}
```

`tags`는 Vector DB metadata에 저장하지 않는다. API 응답에서 필요하면 RDBMS `tags_json`을 조합한다.

### 5.2. Chroma 필터 표현

표준 정책은 OR 조건을 요구한다. Chroma where syntax를 지원하는 adapter에서는 다음 형태로 변환한다.

팀 검색:

```json
{
  "$and": [
    {"tenant_id": "company_abc"},
    {
      "$or": [
        {"org_id": "0102"},
        {"org_id": null}
      ]
    }
  ]
}
```

부서 검색:

```json
{
  "$and": [
    {"tenant_id": "company_abc"},
    {
      "$or": [
        {"dept_code": "01"},
        {"org_id": null}
      ]
    }
  ]
}
```

Local JSON adapter도 동일 의미로 평가한다.

## 6. RAG 검색 흐름

```text
1. API receives POST /api/v1/rag/search
2. dependencies resolve RequestContext
3. RagSearchService builds vector filters from RequestContext + user filters
4. EmbeddingService.embed_text(query, tenant_id)
5. VectorDbRouter resolves adapter by vector_db_id/category_mid
6. Adapter.search(query_vector, filters)
7. LLM client generate/stream with tenant_id and selected chunks
8. Dialog history saved with tenant_id/resolved_org_id
9. Response includes used_chunks and optional debug_info
```

사용자 filters가 `tenant_id`, `org_id`, `dept_code`를 직접 덮어쓰는 것은 금지한다. 서비스 계층에서 강제 필터가 항상 우선한다.

## 7. 문서 pipeline 흐름

```text
1. API receives upload/update with X-Tenant-ID and optional X-Org-ID
2. RequestContext resolved
3. RDBMS document row inserted as pending
4. Background pipeline starts with fresh DB Session
5. Parser extracts page-aware chunks
6. Metadata builder injects tenant_id/org_id/dept_code/vector_db_id/created_at
7. EmbeddingService embeds chunks through Gemini Gateway with tenant_id
8. Vector adapter stores documents with explicit embeddings=
9. Document row status becomes completed or error
```

DB Session은 request thread와 worker thread 간 공유하지 않는다. worker는 session factory를 받아 내부에서 새 Session을 생성한다.

## 8. Gateway 계약

### 8.1. Embedding

```json
POST /v1/embed
{
  "text": "chunk text",
  "tenant_id": "company_abc"
}
```

### 8.2. Generate

```json
POST /v1/generate
{
  "query": "question",
  "context": "...",
  "tenant_id": "company_abc"
}
```

### 8.3. Stream

```json
POST /v1/generate/stream
{
  "query": "question",
  "context": "...",
  "tenant_id": "company_abc"
}
```

Gateway 실패 시 더미 응답 또는 더미 벡터를 만들지 않는다. 표준 오류로 전파한다.

## 9. Index Swap 설계

`vector_db_id`는 논리 ID로 유지하고 실제 collection 이름은 routing registry에서 관리한다.

```json
{
  "vdb_policy_01": {
    "engine": "chroma",
    "collection_name": "company_abc_policy_v2",
    "embedding_model": "gemini-gateway-default",
    "tenant_id": "company_abc",
    "active": true
  }
}
```

조직 개편 또는 재색인 시 신규 collection을 만들고 검증 후 `collection_name`만 교체한다. 애플리케이션 코드는 `vector_db_id`만 사용한다.

## 10. 표준 오류 설계

```json
{
  "status": "error",
  "error_code": "tenant_header_required",
  "message": "X-Tenant-ID header is required",
  "data": null
}
```

주요 error code:

- `tenant_header_required`
- `org_scope_required`
- `document_parsing_error`
- `embedding_api_timeout`
- `llm_generation_error`
- `vector_db_connection_error`
- `document_not_found`
- `tenant_access_denied`
- `routing_not_found`

## 11. v3 수용 기준

v3는 다음 조건을 만족해야 한다.

- `company_id` 운영 경로 제거
- `X-Tenant-ID` 필수화
- `tenant_id` 전 저장/검색 경로 강제
- `org_id`/`dept_code` 검색 정책 구현
- 전사 공유 문서 포함 정책 구현
- Chroma embedding 일관성 유지
- PDF 실제 page_no 보존
- Alembic migration 도입
- Session thread safety 보장
- v1.3 compliance 테스트 통과

