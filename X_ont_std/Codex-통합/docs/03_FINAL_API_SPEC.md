# 03. 최종 API 명세서

작성일: 2026-05-13  
대상: `Codex-통합` MVP 구현

---

## 1. 공통 규칙

### 1.1 Base URL

```text
/api/v1
```

### 1.2 인증

운영 모드의 모든 API는 다음 헤더를 요구한다.

```text
Authorization: Bearer <JWT>
```

로컬 개발 모드에서는 `ALLOW_DEV_USER=true`일 때만 `?user_id=alice&project_id=proj-acme-sales`를 허용한다.

### 1.3 TenantContext

서버는 모든 요청에서 다음 컨텍스트를 생성한다.

```json
{
  "user_id": "alice",
  "company_id": "acme",
  "project_id": "proj-acme-sales",
  "project_ids": ["proj-acme-sales"],
  "role": "editor",
  "permissions": {}
}
```

클라이언트가 body에 넣은 `company_id`는 신뢰하지 않는다. 생성/수정 리소스의 `company_id`, `project_id`, `created_by`는 서버가 주입한다.

### 1.4 오류 형식

```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "can_edit_ontology permission is required",
    "details": {
      "required": "can_edit_ontology"
    }
  }
}
```

공통 오류:

| HTTP | code | 의미 |
| --- | --- | --- |
| 401 | AUTH_REQUIRED | 인증 없음 |
| 401 | TOKEN_EXPIRED | 토큰 만료 |
| 403 | PERMISSION_DENIED | 권한 부족 |
| 403 | PROJECT_FORBIDDEN | 허용되지 않은 프로젝트 |
| 403 | TENANT_FORBIDDEN | 다른 회사 리소스 접근 |
| 404 | NOT_FOUND | 리소스 없음 |
| 409 | CONFLICT | 중복 또는 상태 충돌 |
| 422 | VALIDATION_ERROR | 입력 스키마 오류 |

---

## 2. Auth / Tenant

### POST `/auth/login`

권한: 공개

Request:

```json
{
  "email": "alice@example.com",
  "password": "alice"
}
```

Response 200:

```json
{
  "access_token": "...",
  "token_type": "Bearer",
  "user": {
    "id": "alice",
    "name": "Alice",
    "company_id": "acme",
    "default_project_id": "proj-acme-sales",
    "role": "editor",
    "permissions": {
      "can_edit_ontology": true
    }
  }
}
```

### GET `/tenant/me`

권한: 인증 사용자

Response 200:

```json
{
  "user_id": "alice",
  "company_id": "acme",
  "project_id": "proj-acme-sales",
  "role": "editor",
  "permissions": {
    "can_read": true,
    "can_edit_schema": false,
    "can_edit_object": true,
    "can_edit_relationship": true,
    "can_upload_doc": true,
    "can_delete_doc": false,
    "can_run_query": true,
    "can_view_audit": false
  }
}
```

### GET `/tenant/projects`

권한: 인증 사용자

Response 200:

```json
{
  "projects": [
    {
      "id": "proj-acme-sales",
      "name": "ACME Sales",
      "company_id": "acme"
    }
  ]
}
```

---

## 3. Ontology Schema

### GET `/ontology/schema`

권한: `can_read`

Response 200: `04_FINAL_DATA_SCHEMA.md`의 `ontology_schema.json` 형식.

### PUT `/ontology/schema`

권한: `can_edit_schema`

Request:

```json
{
  "object_types": [],
  "relationship_types": [],
  "action_types": []
}
```

Response 200:

```json
{
  "status": "saved",
  "version": 3
}
```

### POST `/ontology/schema/object-types`

권한: `can_edit_schema`

Request:

```json
{
  "name": "Contract",
  "display_name": "계약",
  "id_prefix": "CT",
  "properties": [
    {
      "name": "title",
      "type": "string",
      "required": true,
      "searchable": true
    }
  ]
}
```

---

## 4. Ontology Instances

### GET `/ontology/objects`

권한: `can_read`

Query:

| 이름 | 필수 | 설명 |
| --- | --- | --- |
| `type` | no | 객체 타입 |
| `q` | no | 이름/속성 검색 |
| `page` | no | 기본 1 |
| `size` | no | 기본 50 |

Response 200:

```json
{
  "items": [
    {
      "id": "C001",
      "type": "Customer",
      "company_id": "acme",
      "project_id": "proj-acme-sales",
      "values": {
        "name": "ACME Korea"
      }
    }
  ],
  "total": 1,
  "page": 1
}
```

### POST `/ontology/objects`

권한: `can_edit_object`

Request:

```json
{
  "type": "Customer",
  "values": {
    "name": "ACME Korea",
    "risk_tier": "Low"
  }
}
```

Response 201: 생성된 object.

### GET `/ontology/objects/{object_id}/context`

권한: `can_read`

Response 200:

```json
{
  "object": {},
  "incoming": [],
  "outgoing": [],
  "documents": [],
  "available_actions": []
}
```

### POST `/ontology/relationships`

권한: `can_edit_relationship`

Request:

```json
{
  "type": "PLACED_ORDER",
  "source_id": "C001",
  "target_id": "O001",
  "properties": {}
}
```

### DELETE `/ontology/relationships/{relationship_id}`

권한: `can_edit_relationship`

Response 200:

```json
{
  "status": "disabled",
  "relationship_id": "REL001"
}
```

삭제는 물리 삭제가 아니라 `status=disabled` tombstone을 기본으로 한다.

---

## 5. Documents

### GET `/documents`

권한: `can_read`

Response 200:

```json
{
  "documents": [
    {
      "doc_id": "doc-001",
      "filename": "snowflake.pdf",
      "company_id": "acme",
      "project_id": "proj-acme-sales",
      "status": "indexed",
      "chunk_count": 42
    }
  ]
}
```

### POST `/documents/upload`

권한: `can_upload_doc`

Request: `multipart/form-data`

Response 201:

```json
{
  "status": "uploaded",
  "doc_id": "doc-001",
  "filename": "snowflake.pdf",
  "chunk_count": 42
}
```

### POST `/documents/{doc_id}/extract-ontology`

권한: `can_edit_object`

Response 202:

```json
{
  "status": "candidate_created",
  "entity_candidates": 24,
  "relationship_candidates": 12
}
```

---

## 6. Hybrid Query

### POST `/hybrid/plan`

권한: `can_run_query`

Request:

```json
{
  "question": "Serverless 과금 기능만 표로 보여줘",
  "doc_ids": ["doc-001"]
}
```

Response 200:

```json
{
  "query_plan": {
    "intent": "filter",
    "ontology_filters": [],
    "needs_vector": true
  }
}
```

### POST `/hybrid/ask`

권한: `can_run_query`

Request:

```json
{
  "question": "Serverless 과금 기능만 표로 보여주고 근거도 알려줘",
  "doc_ids": ["doc-001"],
  "top_k": 5
}
```

Response 200:

```json
{
  "question": "...",
  "query_plan": {},
  "answer": "...",
  "structured_data": {
    "headers": [],
    "rows": []
  },
  "ontology_evidence": [],
  "document_evidence": [],
  "trace": [],
  "warnings": []
}
```

---

## 7. Audit

### GET `/audit/events`

권한: `can_view_audit`

Query:

| 이름 | 설명 |
| --- | --- |
| `action` | 액션 필터 |
| `resource_type` | 리소스 타입 |
| `from` | 시작 시각 |
| `to` | 종료 시각 |

Response 200:

```json
{
  "events": []
}
```
