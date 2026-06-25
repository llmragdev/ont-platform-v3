# Demo Project Data Plan Addendum

작성일: 2026-06-12

이 문서는 `DEMO_PROJECT_DATA_PLAN.md`에 대한 분석/평가 의견을 수용해 보완한 설계 Addendum이다.

## 1. 수용한 평가 요약

다음 항목은 계획에 반영한다.

- API client header context는 이미 구현되어 있으므로 신규 구현이 아니라 Project UI와 연결하는 단계로 본다.
- Project CRUD API와 Project Selector UI는 필수 선행 작업이다.
- `DocumentService.delete(doc_id)`는 기본 삭제를 이미 수행하지만, `content_hash`와 `demo_pack_id` 기준 중복 제거는 아직 없다.
- Demo Pack은 버전 관리 전략이 필요하다.
- Expected Query는 pass/fail 판정 기준을 명확히 가져야 한다.
- Demo Pack 번들링 전략을 코드 번들 방식과 외부 저장소 방식으로 나눠야 한다.

## 2. 현재 구현 상태 보정

### 2.1 API Client Header

현재 v5 frontend `src/lib/api.ts`에는 tenant header 전송 기반이 이미 있다.

```text
x-user-id
x-company-id
x-project-id
x-role
```

현재 기본값:

```text
userId: demo-user
companyId: demo-co
projectId: proj-01
role: FinanceManager
```

따라서 구현 단계는 다음처럼 수정한다.

```text
기존: API client header context 적용
수정: API client header context를 ProjectSelector UI와 연결
```

### 2.2 DocumentService.delete 현황

현재 `DocumentService.delete(doc_id)`는 다음을 수행한다.

```text
1. documents_registry.json에서 doc_id 조회
2. Chroma에서 where={"doc_id": doc_id}로 vector ids 조회
3. vector ids 삭제
4. upload 파일 삭제
5. registry entry 삭제
6. audit 기록
```

즉 `doc_id` 기준 삭제는 이미 있다.

부족한 점:

```text
content_hash 저장 없음
content_hash 기준 중복 문서 검색 없음
demo_pack_id 저장 없음
demo_pack_id 기준 일괄 제거 없음
Chroma metadata에 content_hash/demo_pack_id 없음
```

따라서 DocumentService 개선은 다음으로 정의한다.

```text
DocumentService에 content_hash / demo_pack_id 기반 dedupe와 cleanup 확장
```

## 3. Project CRUD 최소 설계

Project를 화면에서 생성/조회하려면 workspace API가 필요하다.

최소 API:

```text
GET  /api/workspaces/companies
POST /api/workspaces/companies
GET  /api/workspaces/projects
POST /api/workspaces/projects
GET  /api/workspaces/current
```

초기 구현은 파일 기반으로 충분하다.

```text
storage/workspace_registry.json
```

Project 생성 API 예:

```python
@router.post("/api/workspaces/projects")
def create_project(body: dict, ctx: TenantContext):
    company_id = body.get("company_id") or ctx.company_id
    project_id = body["project_id"]
    name = body.get("name", project_id)
    ensure_project_dirs(company_id, project_id)
    upsert_workspace_registry(company_id, project_id, name)
    return {"company_id": company_id, "project_id": project_id, "name": name}
```

Project 목록 API 예:

```python
@router.get("/api/workspaces/projects")
def list_projects(company_id: str | None = None, ctx: TenantContext = Depends(get_tenant_context)):
    return load_projects_registry(company_id or ctx.company_id)
```

## 4. Frontend Project Selector 보완

프론트에는 `ProjectContext`와 `ProjectSelector`를 추가한다.

권장 타입:

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

적용 위치:

```text
Sidebar 상단 또는 App Header 오른쪽
```

초기 UX:

```text
1. 프로젝트가 없으면 "데모 프로젝트 만들기" 버튼 표시
2. 버튼 클릭 시 demo-company / order-demo-project 생성
3. 생성한 Project를 current tenant로 설정
4. 이후 모든 API 요청에 해당 company/project header 전송
```

## 5. Demo Pack Registry와 버전 관리

Demo Pack이 늘어나면 단순 폴더 목록만으로는 관리가 어렵다. 별도 registry를 둔다.

권장 파일:

```text
app/demo_packs/registry.json
```

예시:

```json
{
  "packs": {
    "order-approval": {
      "display_name": "Order Approval Demo",
      "current": "1.0.0",
      "versions": {
        "1.0.0": {
          "path": "order_approval/1.0.0/manifest.json",
          "status": "stable"
        },
        "1.1.0": {
          "path": "order_approval/1.1.0/manifest.json",
          "status": "preview"
        }
      }
    },
    "service-request": {
      "display_name": "Service Request Demo",
      "current": "1.0.0",
      "versions": {
        "1.0.0": {
          "path": "service_request/1.0.0/manifest.json",
          "status": "stable"
        }
      }
    }
  }
}
```

권장 디렉터리:

```text
app/demo_packs/
  registry.json
  order_approval/
    1.0.0/
      manifest.json
      ontology.json
      expected_queries.json
      documents/
    1.1.0/
      manifest.json
      ontology.json
      expected_queries.json
      documents/
```

API는 version을 생략하면 current version을 사용한다.

```text
POST /api/devtools/demo-packs/order-approval/install
POST /api/devtools/demo-packs/order-approval/versions/1.0.0/install
```

설치 상태에는 pack id와 version을 같이 저장한다.

```json
{
  "installed_packs": {
    "order-approval@1.0.0": {
      "pack_id": "order-approval",
      "version": "1.0.0",
      "installed_at": "2026-06-12T00:00:00Z"
    }
  }
}
```

## 6. Expected Query Pass/Fail 기준

Expected Query는 단순 질의 목록이 아니라 판정 기준을 포함해야 한다.

권장 schema:

```json
{
  "query": "Submitted 상태인 Order를 찾아줘",
  "expected_source": "ontology",
  "expected_count_min": 2,
  "expected_entities": ["order-1001", "order-1002"],
  "accept_hybrid": false,
  "pass_criteria": {
    "ontology_hits_min": 2,
    "vector_hits_min": 0,
    "required_entity_ids": ["order-1001", "order-1002"]
  }
}
```

source 판정:

```text
ontology: ontology_hits > 0 and vector_hits == 0
vector: vector_hits > 0 and ontology_hits == 0
hybrid: ontology_hits > 0 and vector_hits > 0
no_evidence: ontology_hits == 0 and vector_hits == 0
```

`accept_hybrid=true`인 경우:

```text
expected_source=ontology 이더라도 hybrid를 PASS로 허용
expected_source=vector 이더라도 hybrid를 PASS로 허용
```

기본 PASS 함수:

```python
def evaluate_expected_query(expected, response):
    qm = response.get("quality_metrics", {})
    ontology_hits = qm.get("ontology_hits", 0)
    vector_hits = qm.get("vector_hits", 0)
    actual_source = classify_source(ontology_hits, vector_hits)

    expected_source = expected["expected_source"]
    if actual_source != expected_source:
        if not (expected.get("accept_hybrid") and actual_source == "hybrid"):
            return False

    criteria = expected.get("pass_criteria", {})
    if ontology_hits < criteria.get("ontology_hits_min", 0):
        return False
    if vector_hits < criteria.get("vector_hits_min", 0):
        return False

    required = set(criteria.get("required_entity_ids", []))
    actual_ids = extract_entity_ids(response)
    return required.issubset(actual_ids)
```

## 7. Demo Pack 번들링 전략

초기 구현은 코드 번들 방식으로 간다.

### Option A. 코드 번들

```text
app/demo_packs/
```

장점:

- 버전 관리가 Git과 함께 된다.
- 테스트 재현성이 높다.
- 오프라인/폐쇄망 시연에 유리하다.
- 초기 구현이 단순하다.

단점:

- 배포 후 Demo Pack만 따로 수정하기 어렵다.

### Option B. 외부 저장소

예:

```text
S3
Nexus
사내 artifact repository
```

장점:

- Demo Pack을 배포 없이 교체할 수 있다.
- 고객/산업별 pack 배포가 쉽다.

단점:

- 무결성 검증과 버전 pinning이 필요하다.
- 네트워크 의존성이 생긴다.
- 운영 보안 검토가 필요하다.

### 최종 방침

Phase 1:

```text
코드 번들 방식
```

Phase 2:

```text
외부 저장소 옵션 추가
manifest 서명/hash 검증 추가
```

외부 pack manifest에는 checksum을 둔다.

```json
{
  "pack_id": "order-approval",
  "version": "1.0.0",
  "checksum": "sha256..."
}
```

## 8. 구현 우선순위 보정

평가 의견을 반영해 우선순위를 다음처럼 조정한다.

1. API client header context와 ProjectSelector 연결
2. Workspace registry 및 Project CRUD API
3. ProjectContext UI
4. DocumentService `content_hash` 추가
5. DocumentService duplicate cleanup
6. DemoPackRegistry 및 manifest 버전 구조
7. DemoPackService install/remove/status
8. `/api/devtools/demo-packs` API
9. Project Test Data 화면
10. Expected Query pass/fail evaluator
11. 기존 임시 seed endpoint deprecated 처리

## 9. 즉시 구현 가능한 MVP 범위

MVP는 아래 범위로 자른다.

```text
1. workspace_registry.json
2. ProjectSelector UI
3. DocumentService content_hash
4. 동일 content_hash 등록 전 doc_id 삭제
5. order-approval-v1 demo pack
6. install/remove/status API
7. 예상 질의 2개
```

MVP에서 제외:

```text
외부 저장소 pack 다운로드
manifest 서명 검증
다중 version UI
복잡한 scoring evaluator
```

## 10. 결론 보정

곧바로 DemoPackService부터 만들기보다 먼저 Project CRUD와 ProjectContext UI를 붙여야 한다. 그래야 demo data가 어느 project에 들어갔는지 사용자가 명확히 알 수 있다.

최우선 결론:

```text
Project를 먼저 보이게 만들고,
그 Project 안에 Demo Pack을 원클릭 설치/제거하게 만든다.
```
