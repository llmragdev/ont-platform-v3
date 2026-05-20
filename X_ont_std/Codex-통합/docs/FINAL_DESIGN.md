# Codex-통합 최종 설계서

작성일: 2026-05-13  
대상: `E:\ontology_edu\Codex-통합`  
기준 문서: [FINAL_REQUIREMENTS.md](FINAL_REQUIREMENTS.md)

---

## 1. 설계 목표

이 설계서는 `Codex-통합`을 현재의 작고 선명한 온톨로지/RAG 프로토타입에서, 권한 격리와 하이브리드 질의가 가능한 운영형 교육 MVP로 확장하기 위한 기준 설계다.

핵심 설계 방향은 다음과 같다.

- 저장소는 처음에는 JSON으로 유지하되, Repository 인터페이스로 감싼다.
- 온톨로지는 타입별 하드코딩을 제거하고 generic object/relationship 구조로 통일한다.
- LLM은 Query Plan 생성과 최종 설명에만 사용한다.
- 필터, 비교, 계산, 관계 탐색은 코드가 결정적으로 수행한다.
- company_id/project_id 필터를 모든 데이터 접근 경로에 적용한다.
- 프론트는 권한 상태를 반영하지만, 보안은 백엔드 API에서 강제한다.
- 인증 사용자, 테넌트 사용자, 권한 사용자는 하나의 `User` 모델로 통합한다.

---

## 2. 목표 아키텍처

```text
Frontend (Next.js)
  ├─ Dashboard
  ├─ Ontology Schema Manager
  ├─ Ontology Instance Manager
  ├─ Ontology Graph Editor
  ├─ Document Manager
  ├─ Hybrid Query
  ├─ User / Project Selector
  └─ Audit Viewer

Backend (FastAPI)
  ├─ AuthService
  ├─ TenantService
  ├─ PermissionService
  ├─ OntologySchemaService
  ├─ OntologyInstanceService
  ├─ OntologyQueryEngine
  ├─ DocumentService
  ├─ SearchService (BM25 + Vector)
  ├─ QueryPlanner
  ├─ HybridAnswerService
  ├─ AuditService
  └─ Repository

Storage (MVP)
  ├─ config/schema.default.json
  ├─ data/companies.json
  ├─ data/users.json
  ├─ data/projects.json
  ├─ data/ontology_objects.json
  ├─ data/ontology_relationships.json
  ├─ data/documents_registry.json
  ├─ data/audit_log.jsonl
  └─ vector_db/
```

---

## 3. 백엔드 모듈 설계

### 3.0 `auth.py` + `TenantContext`

역할: 인증 결과를 모든 서비스가 사용할 수 있는 단일 실행 컨텍스트로 변환한다.

```python
class TenantContext(BaseModel):
    user_id: str
    company_id: str
    project_id: str
    project_ids: list[str]
    role: str
    permissions: Permissions
    auth_mode: Literal["jwt", "dev_user"]
```

모든 쓰기/조회 API는 다음 의존성을 통해 컨텍스트를 받는다.

```python
def current_context(
    authorization: str | None = Header(default=None),
    user: str | None = Query(default=None),
    project_id: str | None = Query(default=None),
) -> TenantContext:
    ...
```

규칙:

- JWT가 있으면 JWT를 우선한다.
- `?user=`는 `ALLOW_DEV_USER=true`일 때만 허용한다.
- `company_id`는 클라이언트 입력이 아니라 사용자 레코드에서 결정한다.
- `project_id`가 없으면 사용자 `default_project_id`를 사용한다.
- 사용자가 접근할 수 없는 프로젝트면 403을 반환한다.

### 3.1 `repository.py`

역할: 저장소 접근을 추상화한다.

```python
class Repository(Protocol):
    def load_schema(self) -> dict: ...
    def save_schema(self, schema: dict) -> None: ...
    def list_objects(self, scope: DataScope) -> list[dict]: ...
    def save_object(self, obj: dict) -> dict: ...
    def list_relationships(self, scope: DataScope) -> list[dict]: ...
    def save_relationship(self, rel: dict) -> dict: ...
    def list_documents(self, scope: DataScope) -> list[dict]: ...
    def append_audit(self, event: dict) -> None: ...
```

MVP 구현체:

- `JsonFileRepository`
- 테스트용 `InMemoryRepository`

향후 구현체:

- `PostgresRepository`

### 3.2 `tenant.py`

역할: 사용자, 회사, 프로젝트, 권한을 관리한다.

주요 모델:

```python
class DataScope(BaseModel):
    company_id: str
    project_ids: list[str]
    user_id: str
    role: str

class Permissions(BaseModel):
    can_read: bool
    can_edit_schema: bool
    can_edit_object: bool
    can_edit_relationship: bool
    can_upload_doc: bool
    can_delete_doc: bool
    can_run_query: bool
    can_view_audit: bool
```

주요 메서드:

```python
get_user(user_id: str) -> dict
list_users() -> list[dict]
get_permissions(user_id: str) -> Permissions
get_scope(user_id: str, project_id: str | None = None) -> DataScope
assert_permission(user_id: str, permission: str, project_id: str | None = None) -> DataScope
```

### 3.3 `ontology_schema.py`

역할: 객체 타입, 관계 타입, 액션 타입을 관리한다.

주요 책임:

- schema JSON 로딩
- 타입명 중복 검증
- 관계 source/target 타입 검증
- 속성 타입 검증
- action input_schema 검증

### 3.4 `ontology_instances.py`

역할: 객체와 관계 인스턴스를 CRUD한다.

객체 저장 형식:

```json
{
  "id": "C001",
  "type": "Customer",
  "company_id": "acme",
  "project_id": "sales-demo",
  "values": {
    "name": "ACME Korea",
    "risk_tier": "Low"
  },
  "source": {
    "kind": "manual",
    "doc_id": null,
    "confidence": 1.0
  },
  "created_by": "alice",
  "updated_at": "2026-05-13T00:00:00Z"
}
```

관계 저장 형식:

```json
{
  "id": "REL001",
  "type": "PLACED_ORDER",
  "source_id": "C001",
  "target_id": "O001",
  "company_id": "acme",
  "project_id": "sales-demo",
  "properties": {},
  "origin": "user-created",
  "status": "active",
  "created_by": "alice",
  "updated_at": "2026-05-13T00:00:00Z"
}
```

`origin` 값:

- `system-derived`
- `llm-extracted`
- `user-created`

`status` 값:

- `active`
- `disabled`
- `deleted`

### 3.5 `ontology_query_engine.py`

역할: Query Plan을 받아 온톨로지 질의를 결정적으로 실행한다.

지원 연산:

```python
filter_entities(plan, scope) -> StructuredData
compare_entities(plan, scope) -> StructuredData
calculate_metrics(plan, scope) -> StructuredData
traverse_relations(plan, scope) -> StructuredData
get_object_context(object_id, scope) -> dict
```

필수 인덱스:

```text
by_id
by_type
by_name
by_property_key
relations_by_source
relations_by_target
documents_by_object_id
```

인덱스는 요청 시점에 repository에서 읽어 메모리로 구성하거나, 변경 시 캐시를 무효화한다.

### 3.6 `query_planner.py`

역할: 자연어 질문을 실행 가능한 Query Plan으로 변환한다.

Query Plan 예:

```json
{
  "intent": "filter",
  "target": {
    "entity_type": "Product"
  },
  "filters": [
    {
      "property": "billing_model",
      "op": "contains",
      "value": "Serverless"
    }
  ],
  "doc_ids": ["doc-001"],
  "needs_vector": true,
  "vector_queries": ["Serverless 과금 근거"]
}
```

설계 원칙:

- LLM output은 JSON Schema로 검증한다.
- 실패하면 규칙 기반 fallback을 사용한다.
- plan에는 사용자의 company/project scope를 직접 넣지 않는다. scope는 서버에서 주입한다.
- 허용되지 않은 entity_type/property는 제거하거나 오류 처리한다.

### 3.7 `document_service.py`

역할:

- 문서 업로드
- 텍스트 추출
- 청크 분할
- 문서 registry 저장
- 온톨로지 추출 요청 연결

문서 registry 예:

```json
{
  "doc_id": "doc-001",
  "filename": "snowflake.pdf",
  "company_id": "acme",
  "project_id": "sales-demo",
  "status": "indexed",
  "chunk_count": 32,
  "created_by": "alice",
  "created_at": "2026-05-13T00:00:00Z"
}
```

### 3.8 `vector_search.py`

역할:

- BM25 검색
- Vector 검색
- hybrid rerank
- company_id/project_id/doc_ids 필터

검색 메서드:

```python
search(query: str, scope: DataScope, doc_ids: list[str] | None, top_k: int) -> list[Evidence]
```

Evidence:

```json
{
  "doc_id": "doc-001",
  "chunk_id": "doc-001:12",
  "page": 4,
  "score": 0.82,
  "text": "...",
  "source": "vector"
}
```

### 3.9 `ontology_extractor.py`

역할: 문서 청크에서 엔티티/관계 후보를 추출한다.

파이프라인:

```text
document chunks
  -> chunk별 LLM extraction
  -> candidate normalization
  -> canonical merge
  -> relation validation
  -> candidate save
  -> user approval
```

후보 객체는 `status=candidate`로 저장하고, 사용자가 승인하면 `active`로 전환한다.

### 3.10 `hybrid_answer.py`

역할: Query Planner, OntologyQueryEngine, SearchService를 조합한다.

실행 순서:

```text
1. user_id -> DataScope 생성
2. QueryPlanner로 plan 생성
3. plan 검증
4. OntologyQueryEngine 실행
5. needs_vector=true이면 SearchService 실행
6. 결과 병합
7. LLM 또는 템플릿으로 최종 설명 생성
8. audit 기록
9. 응답 반환
```

---

## 4. API 설계

### 4.1 Tenant

```text
GET /api/tenant/users
GET /api/tenant/users/{user_id}
GET /api/tenant/users/{user_id}/permissions
GET /api/tenant/projects?user_id=alice
GET /api/tenant/scope?user_id=alice&project_id=sales-demo
```

### 4.2 Ontology Schema

```text
GET    /api/ontology/schema
PUT    /api/ontology/schema
POST   /api/ontology/schema/object-types
PUT    /api/ontology/schema/object-types/{type_name}
DELETE /api/ontology/schema/object-types/{type_name}
POST   /api/ontology/schema/relationship-types
POST   /api/ontology/schema/action-types
```

권한:

- 조회: `can_read`
- 수정: `can_edit_schema`

### 4.3 Ontology Instances

```text
GET    /api/ontology/objects?type=Customer&project_id=sales-demo&user_id=alice
POST   /api/ontology/objects
GET    /api/ontology/objects/{object_id}
PUT    /api/ontology/objects/{object_id}
DELETE /api/ontology/objects/{object_id}
GET    /api/ontology/objects/{object_id}/context

GET    /api/ontology/relationships?type=PLACED_ORDER&project_id=sales-demo
POST   /api/ontology/relationships
PUT    /api/ontology/relationships/{relationship_id}
DELETE /api/ontology/relationships/{relationship_id}
```

권한:

- 조회: `can_read`
- 객체 편집: `can_edit_object`
- 관계 편집: `can_edit_relationship`

### 4.4 Documents

```text
GET    /api/documents?project_id=sales-demo
POST   /api/documents/upload
DELETE /api/documents/{doc_id}
POST   /api/documents/{doc_id}/extract-ontology
GET    /api/documents/{doc_id}/chunks
```

### 4.5 Hybrid Query

```text
POST /api/hybrid/plan
POST /api/hybrid/ask
POST /api/hybrid/evaluate
```

`POST /api/hybrid/ask` request:

```json
{
  "question": "Serverless 과금 기능만 표로 보여주고 근거도 알려줘",
  "user_id": "alice",
  "project_id": "sales-demo",
  "doc_ids": ["doc-001"],
  "top_k": 5
}
```

response:

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

### 4.6 Audit

```text
GET /api/audit?user_id=alice&project_id=sales-demo
GET /api/audit/{event_id}
```

---

## 5. 프론트엔드 설계

### 5.1 상태 구조

```text
UserContext
  ├─ currentUser
  ├─ permissions
  ├─ currentProject
  ├─ setUser()
  ├─ setProject()
  └─ refreshPermissions()
```

`usePermission(permissionName)`은 현재 사용자와 프로젝트 기준으로 boolean을 반환한다.

`PermissionGate`:

```tsx
<PermissionGate permission="can_edit_relationship">
  <button>관계 추가</button>
</PermissionGate>
```

### 5.2 화면 구성

| 화면 | 주요 컴포넌트 |
| --- | --- |
| Dashboard | `DashboardSummary`, `RecentQueries`, `DataScopeBadge` |
| Ontology Schema | `ObjectTypeEditor`, `RelationTypeEditor`, `ActionTypeEditor` |
| Ontology Instances | `ObjectTable`, `ObjectForm`, `RelationshipTable`, `CandidateReview` |
| Graph | `OntologyGraphEditor`, `NodeDetailPanel`, `EdgeDetailPanel` |
| Documents | `DocumentUploader`, `DocumentTable`, `ExtractionStatus` |
| Hybrid Query | `QueryInput`, `QueryPlanViewer`, `StructuredResultTable`, `EvidencePanel`, `TracePanel` |
| Tenant | `UserSwitcher`, `ProjectSelector`, `PermissionMatrix` |
| Audit | `AuditTable`, `AuditDetail` |

### 5.3 UX 원칙

- 현재 company/project scope를 항상 상단에 표시한다.
- 권한이 없어 숨긴 버튼에는 필요 시 읽기 전용 상태를 표시한다.
- Query Plan은 접을 수 있는 패널로 제공한다.
- 구조형 결과와 문서 근거를 분리해서 보여준다.
- 온톨로지 노드/관계 근거는 클릭 시 상세 패널로 연결한다.

---

## 6. 테스트 설계

### 6.1 Backend Unit

```text
tests/test_tenant.py
tests/test_permissions.py
tests/test_ontology_schema.py
tests/test_ontology_instances.py
tests/test_query_planner.py
tests/test_ontology_query_engine.py
tests/test_hybrid_answer.py
```

### 6.2 API Integration

```text
tests/test_api_tenant.py
tests/test_api_ontology.py
tests/test_api_documents.py
tests/test_api_hybrid.py
```

### 6.3 시나리오 테스트

필수 시나리오:

| ID | 시나리오 | 기대 |
| --- | --- | --- |
| P01 | viewer가 객체 생성 API 호출 | 403 |
| P02 | editor가 허용 프로젝트 객체 생성 | 200 |
| P03 | 다른 회사 객체 직접 조회 | 403 또는 404 |
| H01 | 필터 질문 | 구조형 결과 반환 |
| H02 | 비교 질문 | 비교 테이블 반환 |
| H03 | 계산 질문 | 계산 결과 반환 |
| H04 | 관계 질문 | 관계 경로 반환 |
| H05 | hybrid 질문 | 구조형 결과 + 문서 근거 반환 |

### 6.4 Frontend E2E

```text
e2e/tenant.spec.ts
e2e/ontology.spec.ts
e2e/hybrid-query.spec.ts
e2e/permissions.spec.ts
```

---

## 7. 구현 순서

### Phase 1: 권한과 저장소 기반

1. `repository.py` 추가
2. `tenant.py` 추가
3. companies/users/projects JSON 추가
4. DataScope와 permission 검사 추가
5. API에 user_id/project_id scope 적용
6. 권한 테스트 작성

### Phase 2: 온톨로지 일반화

1. `ontology_objects.json`, `ontology_relationships.json` 구조 도입
2. 기존 `data.default.json` 마이그레이션
3. object/relationship CRUD 일반화
4. context API 재구현
5. 관계 origin/status 정책 추가

### Phase 3: 하이브리드 질의 고도화

1. `query_planner.py` 추가
2. Query Plan schema 정의
3. `ontology_query_engine.py` 분리
4. `hybrid_answer.py` 추가
5. `/api/hybrid/plan`, `/api/hybrid/ask` 재구성
6. 시나리오 테스트 추가

### Phase 4: 문서/RAG 강화

1. 문서 registry에 company/project 필드 추가
2. BM25/Vector 검색에 scope filter 적용
3. document evidence 표준화
4. 온톨로지 추출 후보 저장
5. 후보 승인 UI 추가

### Phase 5: 프론트 완성

1. UserContext, ProjectSelector
2. PermissionGate
3. Schema/Instance/Graph/Documents/Hybrid 화면 분리
4. QueryPlanViewer, EvidencePanel, TracePanel
5. E2E 테스트

### Phase 6: 검증과 문서화

1. 통합 테스트 runner
2. HTML/JSON 리포트
3. README 업데이트
4. 운영 가이드
5. 교육 실습 플로우

---

## 8. 마이그레이션 전략

현재 구현은 작고 명확하므로 한 번에 갈아엎기보다 다음 순서로 옮긴다.

1. 현재 `OntologyStore`를 유지한다.
2. 내부 데이터 접근만 Repository로 감싼다.
3. 기존 API 응답 형식은 최대한 유지한다.
4. 새 generic object 구조를 추가하고 기존 Customer/Order/Product 데이터를 변환한다.
5. 기존 `/api/hybrid/ask`는 새 `HybridAnswerService`로 내부 위임한다.
6. 프론트는 기존 단일 페이지에서 기능별 컴포넌트로 점진 분리한다.

---

## 9. 위험과 대응

| 위험 | 대응 |
| --- | --- |
| 기능 범위 과대 | Phase 1~3을 MVP로 고정 |
| 권한 누락 | API dependency로 공통 검사 |
| LLM JSON 실패 | schema validation + fallback planner |
| 온톨로지 추출 품질 낮음 | 후보 상태 + 사용자 승인 |
| JSON 저장소 한계 | Repository 인터페이스 유지 후 Postgres 전환 |
| 테스트 복잡도 증가 | 시나리오 runner와 fixture 데이터 표준화 |

---

## 10. 최종 완료 기준

다음이 모두 만족되면 고도화 완료로 본다.

- 사용자/프로젝트 전환이 가능하다.
- viewer/editor/admin 권한 차이가 UI와 API에서 모두 적용된다.
- 다른 회사 데이터 접근이 차단된다.
- 객체/관계/문서가 company/project scope로 필터링된다.
- 새 객체 타입을 추가해도 객체 목록, 컨텍스트, 질의가 동작한다.
- 하이브리드 질의가 Query Plan을 생성하고 구조형 결과를 반환한다.
- 문서 근거와 온톨로지 근거가 함께 표시된다.
- 필터/비교/계산은 LLM 없이 코드가 수행한다.
- 최소 20개 하이브리드 시나리오와 15개 권한 시나리오가 자동 통과한다.
- 프론트 E2E가 주요 화면과 권한 상태를 검증한다.
