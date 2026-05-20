# Ontology Manager 화면 기획

작성일: 2026-05-12  
대상 프로젝트: `E:\ontology_edu\claud_통합`  
목표: 현재 하드코딩된 `Customer`, `Order`, `Product` 중심 온톨로지를 팔란티어 Foundry식 "관리 가능한 운영 온톨로지"에 가깝게 확장하기 위한 화면 기획

## 1. 기획 방향

현재 `claud_통합`의 워크플로우 그래프는 비교적 유연하다. 사용자가 노드를 추가하고, 연결하고, 저장하고, 서버에서 실행할 수 있다.

반면 온톨로지는 내부 클래스 구조는 유연하지만 실제 구성은 코드에 고정되어 있다.

- `Customer`, `Product`, `Order` 타입이 `backend/app/ontology.py`에 직접 정의되어 있다.
- `PLACED_ORDER`, `ORDER_CONTAINS_PRODUCT` 관계도 코드에 직접 정의되어 있다.
- 관계 인스턴스는 `orders.customer_id`, `order_items.product_id`를 읽어서 코드가 조립한다.
- 사용자가 화면에서 새 객체 타입, 속성, 관계, 액션을 추가할 수 없다.

따라서 다음 단계의 핵심은 **워크플로우 그래프처럼 온톨로지도 화면에서 관리 가능하게 만드는 것**이다.

## 2. 팔란티어식 참고 개념

팔란티어 Foundry의 Ontology는 조직의 데이터를 객체, 링크, 액션, 로직, 권한과 연결하는 운영 레이어에 가깝다. 공식 문서 기준으로 중요한 개념은 다음이다.

- Object Type: Customer, Order, Product 같은 업무 객체 타입
- Property: 객체가 가지는 속성
- Link Type: 객체 간 관계 타입
- Action Type: 사용자가 객체, 속성, 링크를 변경하거나 의사결정 프로세스를 실행하는 동작
- Object View: 객체 타입별 표준 조회 화면
- Ontology Manager: object type, link type, action type, data 연결을 관리하는 화면

참고:
- Palantir Ontology overview: https://www.palantir.com/docs/foundry/ontology/overview
- Palantir Ontology Manager overview: https://palantirfoundation.org/docs/foundry/ontology-manager/overview
- Palantir Action types overview: https://www.palantir.com/docs/foundry/action-types/overview
- Palantir Object edits overview: https://www.palantir.com/docs/foundry/object-edits/overview//

## 3. 제품 내 메뉴 구조

기존 좌측 메뉴에 다음 메뉴를 추가한다.

```text
대시보드
객체 탐색
AI 질의
문서 검색
승인 워크플로우
워크플로우 그래프
온톨로지 관리
설정
감사 로그
```

이번 기획의 중심은 `온톨로지 관리`다.

## 4. 온톨로지 관리 화면 IA

`온톨로지 관리`는 탭 기반으로 구성한다.

```text
온톨로지 관리
  ├─ 개요
  ├─ 객체 타입
  ├─ 관계 타입
  ├─ 객체 데이터
  ├─ 관계 데이터
  ├─ 액션 타입
  ├─ 뷰 구성
  ├─ 권한
  └─ 검증/배포
```

각 탭은 “정의 → 미리보기 → 검증 → 저장” 흐름을 가진다.

## 5. 개요 탭

목적:
- 현재 온톨로지 전체 구조를 한눈에 보여준다.

구성:
- 객체 타입 수
- 관계 타입 수
- 액션 타입 수
- 객체 인스턴스 수
- 관계 인스턴스 수
- 최근 변경 이력
- 온톨로지 그래프 미리보기

중앙 영역:
- 객체 타입 노드와 관계 타입 엣지를 그래프로 표시
- 예: `Customer --PLACED_ORDER--> Order --ORDER_CONTAINS_PRODUCT--> Product`

우측 패널:
- 선택한 객체 타입 또는 관계 타입의 요약
- 속성 목록
- 연결된 액션
- 사용 중인 화면/워크플로우

## 6. 객체 타입 탭

목적:
- 사용자가 새 업무 객체 타입을 정의한다.

주요 기능:
- 객체 타입 생성
- 객체 타입 이름 변경
- 설명 입력
- 아이콘/색상 지정
- 표시 이름 템플릿 지정
- 고유 ID 규칙 지정
- 속성 추가/수정/삭제
- 속성 타입 지정
- 필수 여부 지정
- 민감 정보 여부 지정
- 검색 가능 여부 지정
- 화면 표시 여부 지정

속성 타입:

```text
string
number
boolean
date
datetime
enum
json
object_ref
object_ref_list
```

예시:

```json
{
  "name": "Customer",
  "display_name": "고객",
  "id_prefix": "C",
  "properties": [
    {"name": "name", "type": "string", "required": true, "searchable": true},
    {"name": "segment", "type": "enum", "values": ["SMB", "Enterprise"], "required": true},
    {"name": "region", "type": "string", "required": true},
    {"name": "risk_tier", "type": "enum", "values": ["Low", "Medium", "High"], "sensitive": true}
  ]
}
```

완료 조건:
- 저장하면 `backend/config/ontology.default.json` 또는 Repository에 반영된다.
- `GET /api/ontology/object-types`에서 조회된다.
- 객체 탐색 화면에서 새 타입이 나타난다.

## 7. 관계 타입 탭

목적:
- 객체 간 관계를 정의한다.

주요 기능:
- 관계 타입 생성
- source object type 선택
- target object type 선택
- 방향성 설정
- cardinality 설정
- 관계 속성 추가
- 역방향 표시 이름 지정
- 관계 필수 여부 지정
- 관계 삭제 정책 지정

Cardinality:

```text
one_to_one
one_to_many
many_to_one
many_to_many
```

예시:

```json
{
  "name": "PLACED_ORDER",
  "display_name": "주문함",
  "source_type": "Customer",
  "target_type": "Order",
  "cardinality": "one_to_many",
  "reverse_display_name": "주문 고객"
}
```

관계 속성 예시:

```json
{
  "name": "ORDER_CONTAINS_PRODUCT",
  "source_type": "Order",
  "target_type": "Product",
  "cardinality": "many_to_many",
  "properties": [
    {"name": "quantity", "type": "number", "required": true}
  ]
}
```

완료 조건:
- 사용자가 새 관계 타입을 만들 수 있다.
- 객체 상세 화면에서 관계 목록이 자동으로 표시된다.
- AI 질의 컨텍스트 생성 시 관계를 따라갈 수 있다.

## 8. 객체 데이터 탭

목적:
- 정의된 객체 타입의 인스턴스를 조회하고 최소한의 수정을 한다.

주요 기능:
- 객체 타입 선택
- 객체 목록 조회
- 속성 필터
- 검색
- 객체 생성
- 객체 상세 조회
- 객체 속성 수정
- 객체 삭제
- CSV/JSON import
- JSON export

초기 범위:
- 읽기 중심으로 시작
- 생성/수정/삭제는 Admin만 허용

## 9. 관계 데이터 탭

목적:
- 객체 사이의 링크 인스턴스를 관리한다.

주요 기능:
- 관계 타입 선택
- source 객체 선택
- target 객체 선택
- 관계 생성
- 관계 속성 입력
- 관계 삭제
- 관계 그래프 보기

예시:

```text
Customer C001 --PLACED_ORDER--> Order O001
Order O001 --ORDER_CONTAINS_PRODUCT(quantity=10)--> Product P001
```

중요:
- 이 화면이 있어야 진짜로 “관계를 넣을 수 있는 온톨로지”가 된다.
- 현재 구현은 관계를 코드가 자동 생성하므로, 이 탭이 다음 핵심 보강이다.

## 10. 액션 타입 탭

목적:
- 객체에 대해 수행 가능한 동작을 정의한다.

액션 타입은 팔란티어식 온톨로지에서 “명사에 붙는 동사” 역할을 한다.

주요 기능:
- 액션 타입 생성
- 대상 객체 타입 선택
- 입력 파라미터 정의
- 실행 결과 정의
- 상태 전이 연결
- 정책 조건 연결
- 감사 로그 필드 정의
- 워크플로우 그래프 노드로 노출 여부 설정

예시:

```json
{
  "name": "ApproveOrder",
  "display_name": "주문 승인",
  "target_type": "Order",
  "parameters": [
    {"name": "comment", "type": "string", "required": false}
  ],
  "preconditions": [
    {"type": "status_in", "values": ["Submitted", "Review"]},
    {"type": "policy", "name": "can_approve_order"}
  ],
  "effects": [
    {"type": "set_property", "property": "status", "value": "Approved"},
    {"type": "set_property", "property": "approved_by", "value_from": "actor.email"}
  ],
  "audit_event": "ACTION_EXECUTED"
}
```

완료 조건:
- 액션 타입이 `WorkflowService`와 `WorkflowGraphEngine`에서 공통으로 사용된다.
- `ApproveOrder`가 코드 하드코딩이 아니라 액션 타입 정의로 동작한다.

## 11. 뷰 구성 탭

목적:
- 객체 타입별 표준 Object View를 정의한다.

주요 기능:
- 목록 컬럼 선택
- 상세 화면 섹션 구성
- 우측 ContextPanel 표시 항목 선택
- 관계 표시 방식 선택
- 민감 속성 표시 규칙 연결
- 기본 정렬 지정

예시:

```json
{
  "object_type": "Order",
  "list_columns": ["id", "customer_id", "order_date", "amount", "status"],
  "detail_sections": [
    {"title": "주문 정보", "properties": ["status", "amount", "order_date"]},
    {"title": "고객", "relationship": "PLACED_ORDER", "direction": "incoming"},
    {"title": "상품", "relationship": "ORDER_CONTAINS_PRODUCT", "direction": "outgoing"}
  ]
}
```

## 12. 권한 탭

목적:
- 역할별 객체/속성/관계/액션 권한을 설정한다.

범위:
- 객체 타입 조회 권한
- 속성 마스킹 권한
- 관계 조회 권한
- 액션 실행 권한
- 워크플로우 그래프 실행 권한

예시:

```json
{
  "role": "Viewer",
  "object_permissions": {
    "Customer": {"read": true},
    "Order": {"read": true}
  },
  "property_masks": {
    "Customer.risk_tier": "Restricted",
    "Customer.contract_terms": "Restricted"
  },
  "action_permissions": {
    "ApproveOrder": false
  }
}
```

## 13. 검증/배포 탭

목적:
- 온톨로지 변경 전후의 안전성을 검증한다.

검증 항목:
- 객체 타입 이름 중복
- 속성 이름 중복
- 필수 속성 누락
- 관계 source/target 타입 존재 여부
- 관계 인스턴스의 source/target 존재 여부
- 삭제 예정 타입이 기존 데이터에서 사용 중인지 여부
- 액션 타입의 target object type 존재 여부
- 액션 effect가 실제 속성을 참조하는지 여부
- 권한 규칙이 존재하지 않는 role/action/property를 참조하는지 여부

배포 방식:
- Draft 저장
- Validate
- Preview impact
- Publish
- Rollback

초기 MVP에서는 Publish 버튼이 `repository.save()`로 JSON snapshot을 저장하는 수준이면 충분하다.

## 14. API 설계

초기 API:

```text
GET    /api/ontology/schema
PUT    /api/ontology/schema
GET    /api/ontology/object-types
POST   /api/ontology/object-types
GET    /api/ontology/relationship-types
POST   /api/ontology/relationship-types
GET    /api/ontology/objects?type=Customer
POST   /api/ontology/objects
GET    /api/ontology/relationships?type=PLACED_ORDER
POST   /api/ontology/relationships
GET    /api/ontology/actions
POST   /api/ontology/actions
POST   /api/ontology/validate
POST   /api/ontology/publish
```

관리 화면 전용으로 시작하고, 기존 업무 화면은 점진적으로 이 API를 사용하도록 바꾼다.

## 15. 백엔드 설정 파일 구조

권장 파일:

```text
backend/config/
  ontology.default.json
  actions.default.json
  views.default.json
  policies.default.json
```

`ontology.default.json` 예시:

```json
{
  "object_types": [
    {
      "name": "Customer",
      "properties": [
        {"name": "name", "type": "string", "required": true},
        {"name": "segment", "type": "string", "required": true},
        {"name": "region", "type": "string", "required": true},
        {"name": "risk_tier", "type": "string", "required": true},
        {"name": "contract_terms", "type": "string"},
        {"name": "owner", "type": "string"}
      ]
    },
    {
      "name": "Product",
      "properties": [
        {"name": "name", "type": "string", "required": true},
        {"name": "category", "type": "string", "required": true},
        {"name": "unit_price", "type": "number", "required": true}
      ]
    },
    {
      "name": "Order",
      "properties": [
        {"name": "customer_id", "type": "string", "required": true},
        {"name": "order_date", "type": "string", "required": true},
        {"name": "status", "type": "string", "required": true},
        {"name": "amount", "type": "number", "required": true},
        {"name": "product_ids", "type": "list", "required": true}
      ]
    }
  ],
  "relationship_types": [
    {
      "name": "PLACED_ORDER",
      "source_type": "Customer",
      "target_type": "Order",
      "cardinality": "one_to_many"
    },
    {
      "name": "ORDER_CONTAINS_PRODUCT",
      "source_type": "Order",
      "target_type": "Product",
      "cardinality": "many_to_many",
      "properties": [
        {"name": "quantity", "type": "number", "required": true}
      ]
    }
  ]
}
```

## 16. 프론트 컴포넌트 설계

신규 컴포넌트:

```text
frontend/src/components/ontology/
  OntologyManager.tsx
  OntologyOverview.tsx
  ObjectTypeEditor.tsx
  PropertyEditor.tsx
  RelationshipTypeEditor.tsx
  ObjectDataTable.tsx
  RelationshipDataTable.tsx
  ActionTypeEditor.tsx
  ObjectViewEditor.tsx
  PermissionRuleEditor.tsx
  OntologyValidationPanel.tsx
```

기존 `Explorer`, `ContextPanel`, `AIQuery`, `WorkflowGraph`는 온톨로지 설정을 읽어 렌더링하도록 점진적으로 바꾼다.

## 17. 구현 우선순위

### Phase 1: 읽기형 Ontology Manager

목표:
- 현재 하드코딩된 온톨로지를 JSON 설정으로 추출하고 화면에서 읽기 표시한다.

작업:
- `backend/config/ontology.default.json` 추가
- `OntologyService`가 설정 파일로 ObjectType/RelationshipDefinition 등록
- `GET /api/ontology/schema`
- `GET /api/ontology/relationship-types`
- `OntologyManager` 읽기 화면

완료 조건:
- 기존 59개 pytest 통과
- 객체 탐색/AI 질의/워크플로우 기존 동작 유지

### Phase 2: 관계 데이터 관리

목표:
- 화면에서 관계 인스턴스를 조회하고 추가한다.

작업:
- `GET /api/ontology/relationships`
- `POST /api/ontology/relationships`
- 관계 source/target 검증
- 관계 데이터 탭 구현

완료 조건:
- 새 관계를 추가하면 객체 상세/AI 컨텍스트에 반영된다.

### Phase 3: 객체 타입/관계 타입 편집

목표:
- Admin이 객체 타입과 관계 타입을 추가/수정할 수 있다.

작업:
- draft schema 저장
- validate
- publish
- rollback

완료 조건:
- 새 객체 타입을 추가하고 객체 탐색에서 볼 수 있다.
- 새 관계 타입을 추가하고 관계 데이터 탭에서 사용할 수 있다.

### Phase 4: 액션 타입 설정화

목표:
- `ApproveOrder`, `RiskAssess` 같은 도메인 액션을 코드가 아니라 Action Type으로 관리한다.

작업:
- `actions.default.json`
- 액션 타입 탭
- WorkflowService/WorkflowGraphEngine이 action definition 사용

완료 조건:
- 워크플로우 그래프 팔레트에 action type이 자동 노출된다.

### Phase 5: 화면 구성/권한 설정화

목표:
- 객체 타입별 표준 뷰와 역할별 권한을 관리한다.

작업:
- `views.default.json`
- `policies.default.json`
- Object View Editor
- Permission Rule Editor

## 18. 기획상 중요한 판단

### 18.1 워크플로우 그래프와 온톨로지 관리는 분리하되 연결한다

워크플로우 그래프는 "실행 흐름"을 다루고, 온톨로지 관리는 "업무 세계의 객체/관계/액션 정의"를 다룬다.

둘을 완전히 합치면 복잡해진다. 대신 Action Type을 연결점으로 둔다.

```text
Ontology Action Type
  -> WorkflowGraph node palette에 노출
  -> WorkflowService 상태 전이에 사용
  -> PolicyEngine 권한 검사에 사용
  -> AuditService 이벤트 기록에 사용
```

### 18.2 get_order_context는 유지하되 범용 context API를 추가한다

기존 학습 시나리오와 테스트를 깨지 않기 위해 `get_order_context()`는 유지한다.

동시에 다음 API를 추가한다.

```text
GET /api/ontology/objects/{object_id}/context
```

응답 예시:

```json
{
  "object": {"id": "O001", "type": "Order", "...": "..."},
  "incoming": [
    {"relationship": "PLACED_ORDER", "source": {"id": "C001", "type": "Customer"}}
  ],
  "outgoing": [
    {"relationship": "ORDER_CONTAINS_PRODUCT", "target": {"id": "P001", "type": "Product"}, "properties": {"quantity": 10}}
  ],
  "documents": [],
  "available_actions": []
}
```

### 18.3 편집보다 검증이 먼저다

온톨로지는 한번 깨지면 AI 질의, 검색, 워크플로우, 권한이 모두 흔들린다.

따라서 편집 UI보다 먼저 필요한 것은 다음이다.

- schema validation
- impact preview
- publish/rollback
- audit trail

## 19. 완료 판정

다음이 가능해지면 팔란티어식 유연한 온톨로지의 1차 버전으로 볼 수 있다.

- Admin이 화면에서 객체 타입을 추가할 수 있다.
- Admin이 화면에서 관계 타입을 추가할 수 있다.
- Admin이 화면에서 객체 간 관계 인스턴스를 추가할 수 있다.
- 객체 탐색 화면이 새 타입/관계를 자동 표시한다.
- AI 질의가 새 관계를 컨텍스트로 사용할 수 있다.
- 워크플로우 그래프 팔레트가 Action Type을 자동 반영한다.
- 모든 변경은 검증 후 publish된다.
- 변경 이력과 감사 로그가 남는다.

## 20. 클로드 코드에 전달할 짧은 지시문

```text
현재 워크플로우 그래프는 유연하지만 온톨로지는 Customer/Product/Order와 관계가 코드에 하드코딩되어 있다.
팔란티어 Foundry의 Ontology Manager처럼 객체 타입, 속성, 관계 타입, 관계 인스턴스, 액션 타입을 화면에서 관리할 수 있는 구조로 확장해줘.

우선 Phase 1부터 진행해줘.
1. backend/config/ontology.default.json 생성
2. OntologyService가 JSON 설정으로 ObjectType/RelationshipDefinition을 등록하도록 변경
3. GET /api/ontology/schema, GET /api/ontology/relationship-types 추가
4. 프론트에 온톨로지 관리 메뉴와 읽기형 OntologyManager 화면 추가
5. 기존 59개 pytest, eval.scenarios, evaluate.py, Playwright E2E가 깨지지 않게 유지

그 다음 Phase 2로 관계 인스턴스 조회/추가 API와 관계 데이터 관리 화면을 구현해줘.
```

