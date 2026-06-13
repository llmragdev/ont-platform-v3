# v5 Project Demo/Test Data 개선 계획

작성일: 2026-06-12

## 1. 목표

v5 시연과 통합 테스트를 쉽게 하기 위해 다음 흐름을 만든다.

1. Company / Project를 화면에서 선택하거나 생성한다.
2. 선택한 Project 안에 테스트 문서, 온톨로지, 벡터 데이터를 버튼 하나로 등록한다.
3. 등록된 테스트 데이터로 예상 질의를 바로 실행한다.
4. 동일 문서를 다시 등록할 때 기존 벡터 임베딩을 먼저 삭제해 중복을 막는다.
5. 시연 후 데모 데이터를 버튼 하나로 제거한다.
6. 실제 솔루션 데이터와 테스트/데모 데이터를 섞지 않는다.

## 2. 현재 확인된 기반 구조

백엔드는 이미 tenant context를 갖고 있다.

```text
TenantContext
- company_id
- project_id
- user_id
- role
```

API header 기준:

```text
x-company-id
x-project-id
x-user-id
x-role
```

저장소 구조도 Company / Project 단위로 나뉘어 있다.

```text
storage/{company_id}/{project_id}/
  uploads/
  ontology/
  vector_db/
  workflow_runs/
```

따라서 백엔드의 기본 사상은 이미 `Company -> Project` 구조다. 부족한 것은 프론트의 Project 선택/생성 UX와 데모 데이터팩 관리 기능이다.

## 3. 개선 방향

### 3.1 Project Context 기능

프론트에 현재 작업 컨텍스트를 명확히 표시한다.

필요 기능:

- Company 선택
- Project 선택
- Project 생성
- 현재 Company / Project 표시
- 모든 API 요청에 선택된 context header 자동 포함

권장 위치:

- 상단 헤더 오른쪽
- 또는 Sidebar 상단의 workspace selector

프론트 상태:

```ts
{
  companyId: "demo-company",
  projectId: "order-demo-project",
  userId: "demo-user",
  role: "Admin"
}
```

API 요청 header:

```text
x-company-id: demo-company
x-project-id: order-demo-project
x-user-id: demo-user
x-role: Admin
```

### 3.2 Demo/Test Data Pack 분리

현재처럼 기능 화면 안에 임시 seed endpoint를 직접 섞는 방식은 장기적으로 좋지 않다. 별도 모듈로 분리한다.

권장 백엔드 모듈:

```text
app/api/devtools_demo.py
app/services/demo_pack_service.py
app/demo_packs/
  order_approval/
    manifest.json
    ontology.json
    documents/
    expected_queries.json
```

권장 API:

```text
GET    /api/devtools/demo-packs
POST   /api/devtools/demo-packs/{pack_id}/install
DELETE /api/devtools/demo-packs/{pack_id}
GET    /api/devtools/demo-packs/{pack_id}/status
POST   /api/devtools/demo-packs/{pack_id}/run-expected-query
```

운영 보호:

```text
ENABLE_DEVTOOLS_DEMO=true
```

이 env flag가 없으면 devtools demo API는 404 또는 403으로 막는다.

### 3.3 테스트 데이터 입력 버튼

프론트에 버튼 하나를 둔다.

버튼 이름:

```text
테스트 데이터 입력
```

동작:

1. 현재 Project 확인
2. 없으면 demo project 생성 또는 선택 유도
3. Demo Pack install API 호출
4. 문서 등록
5. 벡터화
6. 온톨로지 엔티티/관계 등록
7. 예상 질의 목록 로드
8. 결과 요약 표시

화면 표시 예:

```text
테스트 데이터 입력 완료
- Project: order-demo-project
- 문서: 2건
- 벡터 chunk: 18건
- 온톨로지 엔티티: 6건
- 예상 질의: 5건
```

### 3.4 기존 데이터 입력도 버튼 하나로 처리

사용자가 말한 “기존 데이터 입력”도 별도 복잡한 절차가 아니라 버튼 하나로 처리한다.

권장 버튼:

```text
기존 테스트 데이터 다시 입력
```

또는 하나의 버튼 안에서 mode 선택:

```text
테스트 데이터 입력
- 없으면 신규 등록
- 있으면 기존 demo pack 제거 후 재등록
```

기본 정책:

```text
install_mode = replace
```

즉 동일 demo pack이 이미 있으면 기존 데이터를 제거하고 다시 등록한다.

### 3.5 벡터 DB 임베딩 중복 제거

현재 `DocumentService.delete(doc_id)`는 Chroma에서 `doc_id` 기준 벡터를 삭제하는 기능이 있다.

개선해야 할 점:

- 등록 전 동일 문서인지 판단하는 fingerprint 추가
- 동일 문서가 이미 등록되어 있으면 기존 문서와 벡터를 먼저 삭제
- 그 다음 새 문서 업로드/벡터화 수행

권장 fingerprint:

```text
sha256(file_bytes)
```

문서 registry에 저장:

```json
{
  "doc_id": "doc-xxxx",
  "filename": "order_policy.pdf",
  "content_hash": "sha256...",
  "demo_pack_id": "order-approval-v1",
  "company_id": "demo-company",
  "project_id": "order-demo-project",
  "shard_id": "default"
}
```

등록 전 처리:

```text
1. content_hash 계산
2. registry에서 같은 content_hash 검색
3. 발견되면 DocumentService.delete(existing_doc_id)
4. Chroma metadata where={"doc_id": existing_doc_id} 삭제
5. 파일 삭제
6. registry 삭제
7. 새 문서 등록
```

추가로 Chroma metadata에 다음을 넣는다.

```json
{
  "doc_id": "doc-xxxx",
  "filename": "order_policy.pdf",
  "content_hash": "sha256...",
  "demo_pack_id": "order-approval-v1",
  "company_id": "demo-company",
  "project_id": "order-demo-project"
}
```

이렇게 하면 동일 문서/동일 demo pack 삭제가 쉬워진다.

### 3.6 Demo Pack 제거

반드시 제거 버튼을 둔다.

버튼:

```text
테스트 데이터 제거
```

삭제 대상:

- uploads registry 중 `demo_pack_id` 일치 문서
- 해당 문서의 Chroma vector chunks
- ontology 문서/엔티티 중 `demo_pack_id` 일치 데이터
- workflow graph 중 `demo_pack_id` 일치 데이터
- expected query run history 중 demo pack 관련 데이터

삭제 API:

```text
DELETE /api/devtools/demo-packs/order-approval-v1
```

반환 예:

```json
{
  "pack_id": "order-approval-v1",
  "deleted_documents": 2,
  "deleted_vector_chunks": 18,
  "deleted_ontology_entities": 6,
  "deleted_workflows": 1
}
```

## 4. 프론트 화면 계획

새 화면을 추가한다.

메뉴명:

```text
프로젝트 테스트 데이터
```

또는 운영 그룹 아래:

```text
Demo Data
```

화면 구성:

1. Project Context
   - 현재 Company
   - 현재 Project
   - 생성/선택 버튼

2. Demo Pack 목록
   - Order Approval Demo
   - Service Request Demo
   - Permission Request Demo

3. Action buttons
   - 테스트 데이터 입력
   - 기존 데이터 제거 후 재입력
   - 테스트 데이터 제거

4. 설치 결과
   - 문서 수
   - 벡터 chunk 수
   - 온톨로지 엔티티 수
   - 예상 질의 수

5. 예상 질의
   - 질의 문장
   - 기대 source: ontology/vector/hybrid
   - 실행 버튼
   - 결과 요약

## 5. 예상 질의 예시

Order Approval Demo:

```text
Submitted 상태인 Order를 찾아줘
Approved 상태인 Order를 찾아줘
5000 이상 주문의 승인 정책은?
Project Alpha 관련 주문을 보여줘
승인 대기 주문의 담당자는 누구야?
```

각 질의에는 기대 결과를 둔다.

```json
{
  "query": "Submitted 상태인 Order를 찾아줘",
  "expected_source": "ontology",
  "expected_count_min": 2,
  "expected_entities": ["order-1001", "order-1002"]
}
```

## 6. 구현 단계

### Step 1. Project Context 최소 구현

- frontend context 추가
- 기본값: `demo-company`, `order-demo-project`
- api client가 header 자동 전송
- 화면에 현재 project 표시

### Step 2. DocumentService 중복 제거

- `content_hash` 계산
- registry에 저장
- 업로드 전 동일 hash 문서 삭제
- Chroma vector chunk metadata에 `content_hash`, `demo_pack_id` 저장

### Step 3. DemoPackService 추가

- demo pack manifest 로드
- ontology seed
- 문서 seed
- vectorization trigger
- expected queries 반환
- install/remove/status API 제공

### Step 4. 프론트 Demo Data 화면 추가

- demo pack install/remove 버튼
- 설치 결과 표시
- 예상 질의 실행 버튼

### Step 5. 기존 임시 seed 정리

- `/api/ontology/examples/order-submitted`는 devtools demo API로 이동
- 기존 화면의 임시 버튼은 새 Demo Data 화면으로 유도
- 필요하면 `온톨로지 질의` 화면에는 “데모 데이터가 없으면 Demo Data 화면에서 입력” 안내만 표시

## 7. 중요한 설계 원칙

- 테스트 데이터는 실제 솔루션 데이터와 섞지 않는다.
- 모든 테스트 데이터에는 `demo_pack_id`를 붙인다.
- 모든 테스트 문서에는 `content_hash`를 붙인다.
- 동일 문서 등록 전 기존 vector embedding을 삭제한다.
- 시연 후 제거가 가능해야 한다.
- 운영 배포에서는 devtools demo API를 비활성화할 수 있어야 한다.

## 8. 결론

시연을 쉽게 하려면 단순 예시 질문 버튼보다 다음 구조가 맞다.

```text
Project 선택/생성
-> 테스트 데이터 입력
-> 문서 업로드/벡터화/온톨로지 seed 자동화
-> 예상 질의 실행
-> 테스트 데이터 제거
```

이 구조는 현재 백엔드의 Company/Project 저장소 사상과 맞고, 향후 SIT/Unit/Eval 자동화와도 자연스럽게 연결된다.

## 9. 상세 설계 추가

### 9.1 Company / Project 관리 API

현재 `TenantContext`는 header 기반으로 `company_id`, `project_id`를 받지만, project 자체를 생성/조회하는 명시적 API는 부족하다. 프론트에서 프로젝트를 직접 만들고 선택하려면 최소 API가 필요하다.

권장 API:

```text
GET  /api/workspaces/companies
POST /api/workspaces/companies
GET  /api/workspaces/projects
POST /api/workspaces/projects
GET  /api/workspaces/current
```

최소 구현은 파일 기반으로 시작한다.

```text
storage/workspace_registry.json
```

예시:

```json
{
  "companies": [
    {
      "company_id": "demo-company",
      "name": "Demo Company",
      "projects": [
        {
          "project_id": "order-demo-project",
          "name": "Order Demo Project",
          "created_at": "2026-06-12T00:00:00Z"
        }
      ]
    }
  ]
}
```

Project 생성 시 수행:

```text
1. registry에 project 추가
2. ensure_project_dirs(company_id, project_id) 실행
3. 기본 domain_schema.json 생성
4. 빈 demo_pack_status.json 생성
```

### 9.2 Frontend Project Context 설계

프론트에는 전역 `ProjectContext`를 둔다.

```ts
type ProjectContextValue = {
  companyId: string;
  projectId: string;
  userId: string;
  role: string;
  setProject: (next: { companyId: string; projectId: string }) => void;
};
```

저장 위치:

```text
localStorage["ontology:v5:workspace"]
```

API client는 모든 요청에 아래 header를 자동으로 붙인다.

```text
x-company-id
x-project-id
x-user-id
x-role
```

프론트 표시:

```text
Company: Demo Company
Project: Order Demo Project
Role: Admin
```

초기 UX:

1. 프로젝트가 없으면 “데모 프로젝트 만들기” 버튼 표시
2. 버튼 클릭 시 `demo-company / order-demo-project` 생성
3. 생성 후 곧바로 Demo Data 화면으로 이동 가능

### 9.3 Demo Pack Manifest 설계

Demo Pack은 코드에 흩어져 있으면 안 되고 manifest 중심으로 관리한다.

파일 구조:

```text
app/demo_packs/order_approval/
  manifest.json
  ontology.json
  expected_queries.json
  documents/
    order_policy.txt
    approval_guideline.txt
```

`manifest.json`:

```json
{
  "pack_id": "order-approval-v1",
  "name": "Order Approval Demo",
  "description": "Submitted/Approved Order 질의와 승인 정책 검색 시연용 데이터",
  "version": "1.0.0",
  "default_company_id": "demo-company",
  "default_project_id": "order-demo-project",
  "documents": [
    {
      "filename": "order_policy.txt",
      "content_type": "text/plain",
      "shard_id": "demo",
      "vectorize": true
    }
  ],
  "ontology": "ontology.json",
  "expected_queries": "expected_queries.json"
}
```

`ontology.json`:

```json
{
  "doc_id": "order-example",
  "entity_types": [
    {
      "name": "ORDER",
      "properties": ["status", "amount", "customer", "owner", "submitted_at"]
    }
  ],
  "entities": [
    {
      "id": "order-1001",
      "type": "ORDER",
      "name": "Order 1001 - Submitted",
      "properties": {
        "status": "Submitted",
        "amount": 4200
      }
    }
  ],
  "relationships": []
}
```

`expected_queries.json`:

```json
[
  {
    "query": "Submitted 상태인 Order를 찾아줘",
    "expected_source": "ontology",
    "expected_count_min": 2,
    "expected_entities": ["order-1001", "order-1002"]
  },
  {
    "query": "5000 이상 주문의 승인 정책은?",
    "expected_source": "vector",
    "expected_count_min": 1
  }
]
```

### 9.4 Demo Pack 상태 저장

각 프로젝트별 설치 상태를 저장한다.

```text
storage/{company_id}/{project_id}/demo_pack_status.json
```

예시:

```json
{
  "installed_packs": {
    "order-approval-v1": {
      "installed_at": "2026-06-12T00:00:00Z",
      "version": "1.0.0",
      "documents": ["doc-a1b2c3"],
      "ontology_docs": ["order-example"],
      "vector_chunks": 18,
      "content_hashes": ["sha256..."]
    }
  }
}
```

이 파일은 제거/재설치/상태 표시의 기준이 된다.

### 9.5 One Button Install 상세 플로우

버튼:

```text
테스트 데이터 입력
```

Backend flow:

```text
1. pack manifest 로드
2. company/project 확인 또는 생성
3. 기존 동일 pack 설치 상태 조회
4. install_mode 확인
   - skip: 이미 있으면 설치하지 않음
   - replace: 기존 pack 제거 후 재설치
   - merge: 없는 데이터만 추가
5. 문서 content_hash 계산
6. 동일 content_hash 문서가 registry에 있으면 기존 문서 삭제
7. 문서 저장
8. 벡터화
9. ontology schema/entity/relationship 등록
10. demo_pack_status.json 업데이트
11. expected_queries 반환
```

기본값:

```text
install_mode=replace
```

이유:

- 시연자가 같은 버튼을 여러 번 눌러도 결과가 중복되지 않아야 한다.
- 벡터 DB에 동일 chunk가 쌓이지 않아야 한다.
- 화면 결과가 매번 예측 가능해야 한다.

### 9.6 중복 문서/벡터 제거 상세 알고리즘

문서 등록 전:

```python
content_hash = sha256(file_bytes).hexdigest()
registry = load_documents_registry(company_id, project_id)
matches = [
    doc for doc in registry.values()
    if doc.get("content_hash") == content_hash
]
for doc in matches:
    delete_document(doc["doc_id"])
```

`delete_document(doc_id)`는 다음을 수행해야 한다.

```text
1. documents_registry.json에서 doc_id 조회
2. Chroma에서 where={"doc_id": doc_id} 조회
3. 조회된 vector ids 삭제
4. uploads 파일 삭제
5. registry entry 삭제
6. audit 기록
```

추가 권장 삭제 조건:

```text
where={"content_hash": content_hash}
where={"demo_pack_id": pack_id}
```

Chroma metadata:

```json
{
  "doc_id": "doc-a1b2c3",
  "filename": "order_policy.txt",
  "content_hash": "sha256...",
  "demo_pack_id": "order-approval-v1",
  "company_id": "demo-company",
  "project_id": "order-demo-project",
  "shard_id": "demo"
}
```

문서 registry:

```json
{
  "doc-a1b2c3": {
    "doc_id": "doc-a1b2c3",
    "filename": "order_policy.txt",
    "content_hash": "sha256...",
    "demo_pack_id": "order-approval-v1",
    "shard_id": "demo",
    "chunk_count": 18
  }
}
```

### 9.7 Demo Pack Remove 상세 플로우

버튼:

```text
테스트 데이터 제거
```

Backend flow:

```text
1. demo_pack_status.json 조회
2. pack_id로 설치된 document ids 조회
3. 각 document id에 대해 DocumentService.delete 실행
4. ontology docs에서 demo_pack_id 일치 entity/relationship 삭제
5. 필요 시 ontology doc 전체 삭제
6. workflow graph에서 demo_pack_id 일치 항목 삭제
7. demo_pack_status.json에서 pack 제거
8. audit 기록
```

삭제 결과:

```json
{
  "pack_id": "order-approval-v1",
  "deleted_documents": 2,
  "deleted_vector_chunks": 18,
  "deleted_ontology_entities": 6,
  "deleted_ontology_relationships": 2,
  "deleted_workflows": 1
}
```

### 9.8 API와 실제 솔루션 기능의 경계

Demo API는 일반 제품 API와 섞지 않는다.

권장 prefix:

```text
/api/devtools/demo-packs
```

금지:

```text
/api/ontology/examples/...
```

위 형태는 임시 검증에는 괜찮지만, 장기 구조에서는 실제 ontology API와 demo helper가 섞인다.

운영 보호:

```python
if os.getenv("ENABLE_DEVTOOLS_DEMO") != "true":
    raise HTTPException(status_code=404)
```

추가 보호:

```text
x-role: Admin
```

또는:

```text
permission: devtools.demo.manage
```

### 9.9 시연 UX 설계

시연 화면 이름:

```text
프로젝트 테스트 데이터
```

화면 흐름:

```text
[1] 프로젝트 선택/생성
    Company: demo-company
    Project: order-demo-project

[2] 데모팩 선택
    Order Approval Demo

[3] 테스트 데이터 입력
    문서 등록 -> 벡터화 -> 온톨로지 생성

[4] 예상 질의 실행
    Submitted 상태인 Order를 찾아줘
    5000 이상 주문의 승인 정책은?

[5] 테스트 데이터 제거
```

버튼:

```text
데모 프로젝트 만들기
테스트 데이터 입력
기존 데이터 제거 후 재입력
테스트 데이터 제거
예상 질의 전체 실행
```

상태 표시:

```text
설치됨
- 문서 2건
- 벡터 chunk 18건
- 온톨로지 엔티티 6건
- 예상 질의 5건
```

### 9.10 예상 질의 실행 결과 UX

각 예상 질의는 실행 결과를 바로 보여준다.

표시 항목:

```text
질의
기대 source
실제 source
ontology_hits
vector_hits
pass/fail
주요 근거
```

예시:

```text
질의: Submitted 상태인 Order를 찾아줘
기대: ontology
실제: ontology
ontology_hits: 2
결과: PASS
근거: order-1001, order-1002
```

### 9.11 구현 우선순위

1. API client header context 적용
2. ProjectContext UI 추가
3. DocumentService content_hash / duplicate cleanup 추가
4. DemoPackService 추가
5. `/api/devtools/demo-packs` 추가
6. Project Test Data 화면 추가
7. 기존 `/api/ontology/examples/order-submitted` 제거 또는 deprecated 처리
8. 예상 질의 자동 실행 추가

### 9.12 마이그레이션 방침

현재 임시 구현:

```text
POST /api/ontology/examples/order-submitted
온톨로지 질의 화면의 예시 데이터 입력 버튼
```

향후 구조:

```text
POST /api/devtools/demo-packs/order-approval-v1/install
DELETE /api/devtools/demo-packs/order-approval-v1
프로젝트 테스트 데이터 화면
```

마이그레이션 후:

- 기존 버튼은 새 화면으로 이동 안내
- 임시 endpoint는 제거하거나 `deprecated` 표시
- demo data는 모두 `demo_pack_id` 기준으로 관리
