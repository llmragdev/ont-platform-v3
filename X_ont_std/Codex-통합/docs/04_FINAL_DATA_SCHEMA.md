# 04. 최종 데이터 스키마

작성일: 2026-05-13  
대상: `Codex-통합` MVP 구현  
저장 방식: MVP는 JSON 파일, 이후 Repository 계층을 통해 PostgreSQL/Vector DB로 전환 가능

---

## 1. 설계 원칙

본 스키마는 `Master_Architecture_Overview.md`의 DB 상세 설계 축을 MVP 구현에 맞게 축소 적용한다.

| 원칙 | MVP 적용 |
| --- | --- |
| 테넌트 격리 | 모든 업무 레코드에 `company_id`, `project_id`를 저장하고 Repository에서 필수 필터로 사용 |
| 추적 가능성 | 생성자, 생성 시각, 수정 시각, source, audit event를 보존 |
| 검색 복원성 | 문서 registry, chunk, vector id를 분리해 검색 결과에서 원문 위치를 복원 |
| 스키마 유연성 | 객체/관계 타입은 `ontology_schema.json`으로 정의하고 instance는 generic 구조로 저장 |
| 운영 전환성 | JSON 파일명과 필드명을 PostgreSQL 테이블 전환 시 그대로 매핑 가능하게 유지 |

MVP에서는 단일 `data/` 폴더를 사용하되, 운영 전환 시에는 `company_id/project_id` 기준 물리 디렉토리 또는 DB row-level policy로 분리한다.

---

## 2. 저장소 구조

```text
backend/
  data/
    companies.json
    users.json
    projects.json
    role_defaults.json
    ontology_schema.json
    ontology_objects.json
    ontology_relationships.json
    documents_registry.json
    document_chunks.json
    vector_mapping.json
    ontology_candidates.json
    query_runs.jsonl
    audit_log.jsonl
  uploads/
    {company_id}/
      {project_id}/
        {doc_id}.{ext}
  vector_db/
```

운영 전환 매핑:

| JSON 파일 | PostgreSQL 후보 테이블 | 표준 설계 대응 |
| --- | --- | --- |
| `documents_registry.json` | `TB_DOC_MASTER` | 문서 마스터 |
| `document_chunks.json` | `TB_DOC_CHUNK` | 문서 청크 |
| `vector_mapping.json` | `TB_VECTOR_MAPPING` | 벡터 DB 매핑 |
| `ontology_schema.json` | `TB_ONTOLOGY_SCHEMA` | 프로젝트별 온톨로지 정의 |
| `ontology_objects.json` | `TB_ONTOLOGY_OBJECT` | 온톨로지 객체 instance |
| `ontology_relationships.json` | `TB_ONTOLOGY_RELATIONSHIP` | 온톨로지 관계 instance |
| `audit_log.jsonl` | `TB_AUDIT_EVENT` | 운영 감사 로그 |

---

## 3. 공통 필드 규칙

업무 레코드 공통 필드:

| 필드 | 타입 | 규칙 |
| --- | --- | --- |
| `company_id` | string | 사용자의 `TenantContext.company_id`와 일치해야 함 |
| `project_id` | string | 사용자의 허용 프로젝트 안에 있어야 함 |
| `status` | enum | `active`, `disabled`, `deleted` 중 하나를 기본으로 사용 |
| `created_by` | string | 서버가 현재 사용자 ID를 주입 |
| `created_at` | datetime | UTC ISO-8601 |
| `updated_at` | datetime | 변경 시 UTC ISO-8601 |

ID 규칙:

- 회사/프로젝트 ID는 사람이 읽을 수 있는 slug를 허용한다. 예: `acme`, `proj-acme-sales`
- 업무 ID는 prefix와 sequence를 조합한다. 예: `C001`, `REL001`, `doc-001`
- 외부 공개 API에서는 내부 파일 경로 대신 논리 ID를 반환한다.
- 삭제는 기본적으로 물리 삭제가 아니라 `status=deleted` 또는 `status=disabled` tombstone으로 처리한다.

---

## 4. `companies.json`

```json
[
  {
    "id": "acme",
    "name": "ACME Corp",
    "status": "active",
    "created_at": "2026-05-13T00:00:00Z"
  }
]
```

필수 필드:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | string | company 식별자 |
| `name` | string | 표시명 |
| `status` | enum | `active`, `disabled` |
| `created_at` | datetime | 생성 시각 |

---

## 5. `projects.json`

```json
[
  {
    "id": "proj-acme-sales",
    "company_id": "acme",
    "name": "ACME Sales",
    "status": "active",
    "created_at": "2026-05-13T00:00:00Z"
  }
]
```

검증 규칙:

- `company_id`는 존재하는 company여야 한다.
- `project.company_id`는 사용자의 company와 반드시 일치해야 접근 가능하다.
- 비활성 프로젝트는 기본 프로젝트로 지정할 수 없다.

---

## 6. `role_defaults.json`

```json
{
  "admin": {
    "can_read": true,
    "can_edit_schema": true,
    "can_edit_object": true,
    "can_edit_relationship": true,
    "can_upload_doc": true,
    "can_delete_doc": true,
    "can_run_query": true,
    "can_view_audit": true,
    "can_manage_users": true
  },
  "editor": {
    "can_read": true,
    "can_edit_schema": false,
    "can_edit_object": true,
    "can_edit_relationship": true,
    "can_upload_doc": true,
    "can_delete_doc": false,
    "can_run_query": true,
    "can_view_audit": false,
    "can_manage_users": false
  },
  "viewer": {
    "can_read": true,
    "can_edit_schema": false,
    "can_edit_object": false,
    "can_edit_relationship": false,
    "can_upload_doc": false,
    "can_delete_doc": false,
    "can_run_query": true,
    "can_view_audit": false,
    "can_manage_users": false
  },
  "auditor": {
    "can_read": true,
    "can_edit_schema": false,
    "can_edit_object": false,
    "can_edit_relationship": false,
    "can_upload_doc": false,
    "can_delete_doc": false,
    "can_run_query": false,
    "can_view_audit": true,
    "can_manage_users": false
  }
}
```

권한 병합 순서:

1. role default를 읽는다.
2. user의 `permission_override`를 덮어쓴다.
3. API별 필수 권한을 검사한다.
4. 실패 시 `PERMISSION_DENIED` audit event를 남긴다.

---

## 7. `users.json`

```json
[
  {
    "id": "alice",
    "email": "alice@example.com",
    "name": "Alice",
    "company_id": "acme",
    "role": "editor",
    "project_ids": ["proj-acme-sales"],
    "default_project_id": "proj-acme-sales",
    "password_hash": "pbkdf2$...",
    "permission_override": {},
    "status": "active",
    "created_at": "2026-05-13T00:00:00Z",
    "last_login_at": null
  }
]
```

검증 규칙:

- `project_ids`는 같은 company의 프로젝트만 허용한다.
- `default_project_id`는 `project_ids` 안에 있어야 한다.
- `permission_override`는 boolean 값만 허용한다.
- `status=disabled` 사용자는 로그인할 수 없다.

---

## 8. `ontology_schema.json`

```json
{
  "version": 1,
  "company_id": "acme",
  "project_id": "proj-acme-sales",
  "object_types": [
    {
      "name": "Customer",
      "display_name": "고객",
      "id_prefix": "C",
      "description": "거래 또는 분석 대상 고객",
      "properties": [
        {
          "name": "name",
          "display_name": "이름",
          "type": "string",
          "required": true,
          "searchable": true,
          "sensitive": false,
          "enum_values": null,
          "ref_type": null
        }
      ],
      "unique_keys": ["name"]
    }
  ],
  "relationship_types": [
    {
      "name": "PLACED_ORDER",
      "display_name": "주문함",
      "source_type": "Customer",
      "target_type": "Order",
      "cardinality": "one_to_many",
      "properties": []
    }
  ],
  "action_types": [
    {
      "name": "ApproveOrder",
      "display_name": "주문 승인",
      "target_type": "Order",
      "permission": "can_edit_object",
      "input_schema": {},
      "exposed_as_graph_node": true
    }
  ],
  "updated_by": "alice",
  "updated_at": "2026-05-13T00:00:00Z"
}
```

지원 property type:

```text
string, number, boolean, date, datetime, enum, list, json, object_ref, object_ref_list
```

스키마 검증 규칙:

- `object_types.name`, `relationship_types.name`, `action_types.name`은 프로젝트 내에서 중복될 수 없다.
- `id_prefix`는 object type 간 중복될 수 없다.
- `relationship_types.source_type`, `target_type`은 존재하는 object type이어야 한다.
- `enum` 타입은 `enum_values`를 반드시 가진다.
- `object_ref`, `object_ref_list` 타입은 `ref_type`을 반드시 가진다.
- 스키마 저장 성공 시 `version`을 증가시킨다.

---

## 9. `ontology_objects.json`

```json
[
  {
    "id": "C001",
    "type": "Customer",
    "company_id": "acme",
    "project_id": "proj-acme-sales",
    "values": {
      "name": "ACME Korea",
      "risk_tier": "Low"
    },
    "source": {
      "kind": "manual",
      "doc_id": null,
      "chunk_id": null,
      "page": null,
      "confidence": 1.0
    },
    "tags": [],
    "status": "active",
    "created_by": "alice",
    "created_at": "2026-05-13T00:00:00Z",
    "updated_at": "2026-05-13T00:00:00Z"
  }
]
```

상태:

- `candidate`: LLM/문서 추출 후보
- `active`: 승인되어 기본 질의에 포함
- `disabled`: 비활성, 기본 질의에서 제외
- `deleted`: 삭제 tombstone

검증 규칙:

- `type`은 `ontology_schema.object_types`에 존재해야 한다.
- `values`는 타입별 property schema를 통과해야 한다.
- `required=true` 필드는 누락될 수 없다.
- `searchable=true` 필드는 검색 인덱스 대상이다.
- 객체 생성 시 `company_id`, `project_id`, `created_by`는 클라이언트 입력을 무시하고 서버가 주입한다.

---

## 10. `ontology_relationships.json`

```json
[
  {
    "id": "REL001",
    "type": "PLACED_ORDER",
    "source_id": "C001",
    "target_id": "O001",
    "company_id": "acme",
    "project_id": "proj-acme-sales",
    "properties": {},
    "origin": "user-created",
    "status": "active",
    "created_by": "alice",
    "created_at": "2026-05-13T00:00:00Z",
    "updated_at": "2026-05-13T00:00:00Z"
  }
]
```

`origin`:

- `system-derived`
- `llm-extracted`
- `user-created`

검증 규칙:

- `type`은 `relationship_types`에 존재해야 한다.
- `source_id`, `target_id` 객체는 같은 `company_id`, `project_id`에 속해야 한다.
- source/target 객체 type은 관계 schema의 `source_type`, `target_type`과 일치해야 한다.
- 삭제는 기본적으로 `status=disabled`로 처리한다.

---

## 11. `documents_registry.json`

```json
[
  {
    "doc_id": "doc-001",
    "filename": "snowflake.pdf",
    "content_type": "application/pdf",
    "file_size": 412312,
    "company_id": "acme",
    "project_id": "proj-acme-sales",
    "file_path": "uploads/acme/proj-acme-sales/doc-001.pdf",
    "status": "indexed",
    "page_count": 29,
    "chunk_count": 42,
    "created_by": "alice",
    "created_at": "2026-05-13T00:00:00Z",
    "indexed_at": "2026-05-13T00:02:00Z",
    "error_message": null
  }
]
```

상태:

- `uploaded`
- `indexing`
- `indexed`
- `index_failed`
- `deleted`

표준 DB 매핑:

| JSON 필드 | `TB_DOC_MASTER` 컬럼 |
| --- | --- |
| `doc_id` | `DOC_ID` |
| `filename` | `FILE_NAME` |
| `file_path` | `FILE_PATH` |
| `file_size` | `FILE_SIZE` |
| `company_id` + `project_id` | `TENANT_ID` 또는 분리 컬럼 |
| `status` | `STATUS` |
| `created_at` | `REG_DT` |

---

## 12. `document_chunks.json`

```json
[
  {
    "chunk_id": "doc-001:0001",
    "doc_id": "doc-001",
    "company_id": "acme",
    "project_id": "proj-acme-sales",
    "content": "Snowpipe is a serverless feature...",
    "page": 3,
    "chunk_seq": 1,
    "token_count": 612,
    "vector_id": "vec-doc-001-0001",
    "metadata": {
      "section": "Billing",
      "language": "en"
    },
    "created_at": "2026-05-13T00:01:00Z"
  }
]
```

청킹 규칙:

- 기본 chunk size는 500~800 tokens 범위를 사용한다.
- overlap은 10~15%를 기본값으로 한다.
- `chunk_id`는 `doc_id:sequence` 형태로 만들어 원문 위치를 추적한다.
- `content`는 답변 근거로 노출될 수 있으므로 민감정보 마스킹 정책과 연결한다.

---

## 13. `vector_mapping.json`

```json
[
  {
    "vector_id": "vec-doc-001-0001",
    "chunk_id": "doc-001:0001",
    "company_id": "acme",
    "project_id": "proj-acme-sales",
    "engine_type": "FAISS",
    "collection_name": "acme_proj_acme_sales",
    "model_id": "bge-m3",
    "dimension": 1024,
    "created_at": "2026-05-13T00:01:00Z"
  }
]
```

검색 복원 규칙:

- Vector DB 검색 결과의 ID는 `vector_mapping.vector_id`와 매칭한다.
- `chunk_id`를 통해 `document_chunks`의 본문과 위치를 복원한다.
- `doc_id`를 통해 `documents_registry`의 파일명과 상태를 확인한다.
- `company_id`, `project_id`가 현재 컨텍스트와 다르면 결과에서 제외한다.

---

## 14. `ontology_candidates.json`

```json
[
  {
    "candidate_id": "cand-001",
    "doc_id": "doc-001",
    "kind": "entity",
    "company_id": "acme",
    "project_id": "proj-acme-sales",
    "payload": {
      "type": "Product",
      "values": {
        "name": "Snowpipe"
      }
    },
    "source_page": 3,
    "source_chunk_id": "doc-001:0001",
    "source_text": "Snowpipe is ...",
    "confidence": 0.82,
    "status": "pending",
    "reviewed_by": null,
    "reviewed_at": null,
    "created_at": "2026-05-13T00:00:00Z"
  }
]
```

상태:

- `pending`
- `approved`
- `rejected`
- `edited`

승인 규칙:

- entity 후보 승인 시 `ontology_objects`에 object를 생성하거나 기존 object와 merge한다.
- relationship 후보 승인 시 source/target 객체가 먼저 존재해야 한다.
- 승인/거절/수정은 audit event로 기록한다.

---

## 15. `query_runs.jsonl`

하이브리드 질의의 운영 품질을 측정하기 위한 실행 로그다.

```json
{
  "run_id": "qry-001",
  "timestamp": "2026-05-13T00:05:00Z",
  "user_id": "alice",
  "company_id": "acme",
  "project_id": "proj-acme-sales",
  "question": "Serverless 과금 기능과 근거를 알려줘",
  "intent": "hybrid",
  "top_k": 5,
  "planner_mode": "llm",
  "fallback_used": false,
  "document_evidence_count": 3,
  "ontology_evidence_count": 1,
  "latency_ms": 1480,
  "warnings": []
}
```

---

## 16. `audit_log.jsonl`

한 줄에 하나의 JSON event를 저장한다.

```json
{
  "event_id": "evt-001",
  "timestamp": "2026-05-13T00:00:00Z",
  "user_id": "alice",
  "company_id": "acme",
  "project_id": "proj-acme-sales",
  "action": "CREATE_OBJECT",
  "resource_type": "OntologyObject",
  "resource_id": "C001",
  "before": null,
  "after": {},
  "result": "success",
  "error_code": null,
  "latency_ms": 12
}
```

필수 audit action:

- `LOGIN_SUCCESS`
- `LOGIN_FAILED`
- `PERMISSION_DENIED`
- `CREATE_OBJECT`
- `UPDATE_OBJECT`
- `DISABLE_RELATIONSHIP`
- `UPLOAD_DOCUMENT`
- `DELETE_DOCUMENT`
- `EXTRACT_ONTOLOGY`
- `HYBRID_QUERY`
- `PLANNER_FALLBACK`

---

## 17. Repository 검증 체크리스트

- [ ] 모든 list/get 쿼리는 `TenantContext.company_id`, `project_id`로 필터링한다.
- [ ] create/update 요청 body의 `company_id`, `project_id`, `created_by`는 신뢰하지 않는다.
- [ ] 다른 company/project의 ID를 직접 요청하면 403 또는 404를 반환한다.
- [ ] 문서 검색 결과는 registry 상태가 `indexed`인 문서만 포함한다.
- [ ] `deleted`, `disabled` 데이터는 기본 조회에서 제외한다.
- [ ] 모든 쓰기 작업은 audit event를 남긴다.
- [ ] JSON 저장 실패 시 partial write가 남지 않도록 임시 파일 후 원자적 교체를 사용한다.
