# CLICK_TEST_CHECKLIST 중심 온톨로지 구현 평가

작성자: Codex  
작성일: 2026-05-12  
평가 대상: `E:\ontology_edu\claud_통합`  
중심 문서: `docs/CLICK_TEST_CHECKLIST.md`  
주요 코드 근거: `backend/app/ontology.py`, `backend/app/workflow_graph_engine.py`, `frontend/src/components/WorkflowGraph.tsx`

## 0. 재점검 결과

재점검일: 2026-05-12  
검증 결과:

- Backend: `67 passed in 2.38s`
- Scenario: `5/5 passed`
- Evaluate: `10/10 passed`
- Frontend: `next build` 성공

Claude Code가 지적된 온톨로지 문제를 상당 부분 보완했다. 특히 초기 평가에서 지적했던 "온톨로지 스키마가 Python 코드에 고정되어 있다", "범용 관계 탐색이 없다", "관계 추가 API가 없다", "온톨로지 그래프 화면이 없다"는 문제는 대부분 1차적으로 해결되었다.

반영된 개선:

- `backend/app/config/ontology.default.json`으로 객체 타입, 관계 타입, 액션 타입 정의를 외부화했다.
- `OntologyService.object_context()`와 `OntologyRegistry.find_relationships()`로 범용 incoming/outgoing 관계 탐색을 추가했다.
- `POST /api/ontology/relationships`, `DELETE /api/ontology/relationships/{rel_id}`를 추가했다.
- `GET /api/ontology/graph`와 `frontend/src/components/OntologyExplorerCanvas.tsx`로 온톨로지 그래프 캔버스를 추가했다.
- `policy.default.json`과 스키마의 `sensitive: true`를 결합해 민감 속성 마스킹을 외부 설정화했다.

다만 "팔란티어식 유연 온톨로지" 관점에서는 아직 남은 차이가 있다.

| 항목 | 재점검 평가 |
| --- | --- |
| 스키마 외부화 | 상당 부분 완료 |
| 범용 관계 탐색 | 백엔드 서비스 내부는 완료, 별도 객체 컨텍스트 API는 아직 부족 |
| 관계 인스턴스 CRUD | API/UI 있음. 단, 자동 생성된 기본 관계 삭제의 영속성은 주의 필요 |
| 새 객체 타입 추가 | 타입 등록은 가능. 하지만 인스턴스 로딩은 아직 `customers/products/orders` 중심 |
| 액션 타입 외부화 | 백엔드 권한 정책은 스키마 연동. 프론트 팔레트와 실행 핸들러는 아직 일부 하드코딩 |
| 문서 정합성 | `PROGRESS/NEXT_STEPS/CHANGELOG`는 최신. `README/FINAL_REPORT/DEMO_SCENARIO/CLICK_TEST_CHECKLIST` 일부 숫자와 설명은 구버전 흔적 있음 |

즉 현재 상태는 이 문서의 최초 평가보다 훨씬 진전되었다. 이제 평가는 **"하드코딩된 온톨로지 데모"에서 "설정 기반 온톨로지 관리 MVP"로 상승**했다고 보는 것이 맞다. 다만 새 도메인 타입과 새 액션을 운영자가 자유롭게 추가해 전체 화면/AI/워크플로우가 자동 확장되는 수준은 아직 후속 과제다.

## 1. 결론

`claud_통합`의 온톨로지는 현재 데모와 교육 목적에서는 충분히 작동한다. `Customer`, `Order`, `Product` 객체를 만들고, `PLACED_ORDER`, `ORDER_CONTAINS_PRODUCT` 관계를 통해 주문 중심 컨텍스트를 구성한다. 워크플로우의 `ApproveOrder`, `RiskAssess` 노드도 이 온톨로지 데이터를 사용하므로, 단순 화면 목업이 아니라 실제 정책 판단과 AI 질의의 기반 데이터로 연결되어 있다.

다만 구조적 완성도는 **"온톨로지 플랫폼"이라기보다 "하드코딩된 업무 온톨로지 데모"**에 가깝다. 객체 타입, 속성, 관계 타입, 주문 컨텍스트 조립 방식이 대부분 코드에 고정되어 있어, 사용자가 화면이나 설정 파일로 새 업무 객체와 관계를 추가하는 형태는 아직 아니다.

따라서 평가를 나누면 다음과 같다.

| 항목 | 평가 |
| --- | --- |
| 교육/시연용 온톨로지 완성도 | 높음 |
| 워크플로우와 온톨로지 결합도 | 높음 |
| 관계 기반 컨텍스트 구성 | 중간 |
| 선언형 스키마 관리 | 낮음 |
| 사용자 주도 관계 추가/수정 | 낮음 |
| 팔란티어식 유연한 온톨로지 플랫폼화 | 초기 단계 |

핵심은 이렇다. **워크플로우는 유연해졌지만, 온톨로지는 아직 유연하지 않다.**

## 2. 현재 구현된 온톨로지의 장점

### 2.1 객체 타입과 관계 타입의 기본 뼈대가 있다

`backend/app/ontology.py`에는 `OntologyRegistry`, `ObjectType`, `RelationshipDefinition`, `RelationshipInstance` 구조가 있다. 즉 온톨로지를 단순 딕셔너리로만 다루지 않고, 객체 타입과 관계 타입을 구분하는 기본 모델은 이미 잡혀 있다.

현재 등록되는 객체 타입:

- `Customer`
- `Product`
- `Order`

현재 등록되는 관계 타입:

- `PLACED_ORDER`: `Customer -> Order`
- `ORDER_CONTAINS_PRODUCT`: `Order -> Product`

이 구조 덕분에 주문을 조회할 때 고객과 상품을 함께 묶어 AI 컨텍스트로 제공할 수 있다.

### 2.2 정책/워크플로우와 연결되어 있다

워크플로우 그래프의 도메인 노드인 `ApproveOrder`, `RiskAssess`는 단순 문자열 출력 노드가 아니다. 주문, 고객, 리스크 등급, 권한을 참조해 실행 결과를 만든다.

이 점은 중요하다. 온톨로지가 화면의 장식이 아니라, 다음 기능의 기반으로 사용된다.

- 승인 가능 여부 판단
- 리스크 평가
- AI 질의 컨텍스트 구성
- 역할별 마스킹
- 감사 로그와 실행 결과 설명

따라서 `CLICK_TEST_CHECKLIST.md` 기준으로 보면, 온톨로지는 워크플로우 검증 시나리오를 뒷받침하는 실제 도메인 계층으로 작동한다.

### 2.3 데모 데이터의 의미 연결은 명확하다

현재 데이터는 고객, 주문, 상품의 관계가 명확하다. 예를 들어 주문 `O001`을 기준으로 고객과 상품을 찾아가고, 고객의 `risk_tier`와 주문 금액을 정책 판단에 사용할 수 있다.

교육용 시연에서는 이 정도 구조가 오히려 장점이다. 관계가 단순하고 설명이 쉬워서, "온톨로지 데이터가 AI 답변과 워크플로우 판단에 들어간다"는 메시지를 빠르게 전달할 수 있다.

## 3. 핵심 한계

### 3.1 온톨로지 스키마가 코드에 하드코딩되어 있다

가장 큰 한계는 `OntologyService._build_registry()` 안에서 객체 타입과 속성이 직접 정의된다는 점이다.

현재 방식:

- `Customer` 속성: `name`, `segment`, `region`, `risk_tier`, `contract_terms`, `owner`
- `Product` 속성: `name`, `category`, `unit_price`
- `Order` 속성: `customer_id`, `order_date`, `status`, `amount`, `product_ids`
- 관계 타입: `PLACED_ORDER`, `ORDER_CONTAINS_PRODUCT`

이 구조에서는 새 객체 타입을 추가하려면 코드를 수정해야 한다. 예를 들어 `Warehouse`, `Invoice`, `SalesRep`, `Contract`, `Delivery` 같은 객체를 추가하려면 `ontology.py`를 바꿔야 한다.

팔란티어식 온톨로지를 목표로 한다면 이 부분은 가장 먼저 바뀌어야 한다. 객체 타입, 속성, 관계 타입은 코드가 아니라 JSON/YAML 또는 DB 저장소에서 로드되어야 한다.

### 3.2 관계 탐색이 주문 중심으로 고정되어 있다

현재 온톨로지 서비스에는 범용 그래프 탐색 API가 없다. 핵심 컨텍스트 함수는 `get_order_context(order_id, customer_id)`에 가깝다.

즉 현재의 질문 구조는 다음에 강하다.

- 이 주문의 고객은 누구인가?
- 이 주문에 포함된 상품은 무엇인가?
- 이 주문을 승인할 수 있는가?

하지만 다음 질문에는 약하다.

- 이 고객과 연결된 모든 주문, 상품, 문서, 정책, 담당자를 보여줘.
- 특정 상품 장애가 영향을 주는 고객과 주문을 추적해줘.
- 서울 지역 Enterprise 고객 중 고위험 주문과 담당자를 연결해줘.
- 관계를 2단계 이상 따라가며 영향도를 분석해줘.

현재는 "정해진 관계 경로"는 잘 처리하지만, "사용자가 정의한 임의 관계 그래프"를 탐색하는 단계는 아니다.

### 3.3 관계 인스턴스를 화면에서 추가하는 구조가 없다

현재 관계는 원천 데이터에서 자동으로 조립된다.

- 주문의 `customer_id`를 보고 `PLACED_ORDER` 생성
- `order_items`를 보고 `ORDER_CONTAINS_PRODUCT` 생성

이 방식은 데모에는 좋지만, 온톨로지 관리 화면 관점에서는 부족하다. 사용자가 화면에서 다음을 할 수 있어야 온톨로지 플랫폼에 가까워진다.

- 관계 타입 생성
- 관계 타입의 source/target 지정
- 관계 속성 정의
- 객체 간 관계 인스턴스 추가
- 관계 삭제 또는 비활성화
- 관계 변경 이력 확인

현재 `claud_통합`에는 이런 온톨로지 관리 UI/API가 없다.

### 3.4 액션이 온톨로지의 일부로 모델링되지 않았다

`ApproveOrder`, `RiskAssess`는 워크플로우 노드로는 잘 구현되어 있다. 그러나 온톨로지 관점에서는 액션 타입이 객체/관계와 같은 수준의 메타데이터로 관리되지 않는다.

이상적인 구조에서는 액션도 온톨로지에 연결되어야 한다.

- 어떤 객체 타입에 적용 가능한 액션인가?
- 실행 전 필요한 관계는 무엇인가?
- 실행 후 어떤 객체나 관계가 변경되는가?
- 어떤 역할이 실행할 수 있는가?
- 실행 결과가 어떤 감사 이벤트로 남는가?

현재는 도메인 노드가 온톨로지를 사용하지만, 액션 자체가 온톨로지 스키마에서 선언되는 구조는 아니다.

### 3.5 문서와 온톨로지 객체의 연결이 느슨하다

RAG 답변은 온톨로지 컨텍스트와 문서 검색 결과를 함께 사용한다. 이 방향은 좋다. 다만 문서 안의 엔티티가 온톨로지 객체 ID와 구조적으로 연결되어 있지는 않다.

향후에는 다음 구조가 필요하다.

- 문서 조항과 객체 타입 연결
- 문서 조항과 특정 객체 인스턴스 연결
- 정책 문서와 액션 타입 연결
- 근거 문장과 온톨로지 관계 경로 연결

그래야 AI 답변이 "검색 문서 + 객체 데이터"를 넘어 "근거가 연결된 지식 그래프"에 가까워진다.

## 4. CLICK_TEST_CHECKLIST 기준 평가

### 4.1 정상 승인 시나리오

평가: 통과

주문, 고객, 리스크, 권한을 조합해 승인 가능 여부를 판단한다. 데모 목적에서는 충분하다.

보완점:

- `ApproveOrder`가 실제 상태 변경인지, 승인 가능성 평가인지 문서와 UI에서 명확히 구분해야 한다.
- 실제 승인 실행이라면 주문 상태 변경, 감사 이벤트, 후속 관계 업데이트가 필요하다.

### 4.2 고위험 고객 거부 시나리오

평가: 통과

고객의 `risk_tier`를 정책 판단에 사용하는 점은 온톨로지 활용 사례로 좋다.

보완점:

- `risk_tier`가 단순 속성값으로만 존재한다.
- 리스크 등급이 어떤 관계와 규칙으로 계산되었는지는 온톨로지 안에 없다.
- 향후에는 리스크 판단 근거를 객체/관계/문서 조항으로 추적할 수 있어야 한다.

### 4.3 금액 임계값 분기

평가: 부분 통과

금액 기반 정책 판단은 잘 작동한다. 다만 금액 임계값은 온톨로지라기보다 정책 엔진의 규칙에 가깝다.

보완점:

- 정책 규칙을 코드 밖으로 분리해야 한다.
- 정책이 어떤 객체 타입과 속성을 참조하는지 선언적으로 드러나야 한다.

### 4.4 속성 마스킹

평가: 통과

역할에 따라 민감 속성을 제한하는 흐름은 좋다.

보완점:

- 현재는 데이터 가공 또는 응답 제어에 가깝다.
- 객체 타입, 속성, 관계 타입 단위의 RBAC 정책으로 확장해야 한다.
- "이 역할은 특정 관계 자체를 볼 수 없다"는 스키마 레벨 보안이 필요하다.

### 4.5 AI 질의

평가: 부분 통과

주문 중심 질문에는 비교적 강하다. 하지만 범용 온톨로지 질의라고 보기에는 아직 부족하다.

보완점:

- `Order`에 고정되지 않은 객체 질의가 필요하다.
- AI 응답에 관계 경로를 표시해야 한다.
- "왜 이 답이 나왔는가"를 객체, 관계, 문서 근거로 분리해 보여줘야 한다.

## 5. 이상적인 목표 구조

`claud_통합`을 온톨로지 중심으로 더 발전시킨다면 목표는 다음과 같다.

### 5.1 선언형 온톨로지 스키마

객체 타입 예시:

```json
{
  "name": "Customer",
  "label": "고객",
  "properties": [
    {"name": "name", "type": "string", "required": true},
    {"name": "risk_tier", "type": "string", "required": true}
  ]
}
```

관계 타입 예시:

```json
{
  "name": "PLACED_ORDER",
  "label": "주문함",
  "source_type": "Customer",
  "target_type": "Order",
  "properties": [
    {"name": "created_at", "type": "datetime", "required": false}
  ]
}
```

이렇게 바뀌면 `Warehouse`, `Invoice`, `SalesRep` 같은 새 타입을 코드 수정 없이 추가할 수 있다.

### 5.2 범용 객체 컨텍스트 API

필요 API:

```text
GET /api/ontology/schema
GET /api/ontology/object-types
GET /api/ontology/relationship-types
GET /api/ontology/objects?type=Customer
GET /api/ontology/objects/{object_id}
GET /api/ontology/objects/{object_id}/context?depth=2
POST /api/ontology/relationships
DELETE /api/ontology/relationships/{relationship_id}
```

핵심은 `get_order_context`를 범용화하는 것이다. `Order`뿐 아니라 어떤 객체든 incoming/outgoing 관계를 따라 컨텍스트를 만들 수 있어야 한다.

### 5.3 온톨로지 관리 화면

필요 화면:

- 객체 타입 목록
- 객체 타입 상세와 속성 목록
- 관계 타입 목록
- 관계 타입 source/target 표시
- 객체 인스턴스 목록
- 객체 상세의 incoming/outgoing 관계
- 관계 인스턴스 추가/삭제
- AI 질의에서 사용된 관계 경로 표시

현재 워크플로우 그래프 화면이 강해졌으므로, 다음 보강은 온톨로지 관리 화면이 되어야 한다.

### 5.4 액션 타입과 워크플로우 노드의 온톨로지화

워크플로우 노드 팔레트도 코드 하드코딩이 아니라 온톨로지/액션 정의에서 만들어지는 것이 바람직하다.

예시:

```json
{
  "name": "ApproveOrder",
  "label": "주문 승인",
  "target_type": "Order",
  "required_roles": ["AccountManager"],
  "reads": ["Order.amount", "Customer.risk_tier"],
  "writes": ["Order.status"],
  "emits": ["ORDER_APPROVED"]
}
```

이 구조가 되면 `RiskAssess`, `ApproveOrder` 같은 도메인 노드를 코드에 박아두지 않고 설정으로 확장할 수 있다.

## 6. Claude Code에 추가 지시할 사항

다음 지시는 온톨로지 완성도를 높이기 위한 우선순위다.

### 6.1 1순위: 온톨로지 스키마 외부화

지시:

`backend/app/ontology.py`의 `_build_registry()`에 하드코딩된 `Customer`, `Product`, `Order`, `PLACED_ORDER`, `ORDER_CONTAINS_PRODUCT` 정의를 `backend/config/ontology.default.json`으로 분리하라.

완료 기준:

- 객체 타입이 JSON에서 로드된다.
- 관계 타입이 JSON에서 로드된다.
- 필수 속성 누락 시 검증 오류가 난다.
- source/target 타입이 맞지 않는 관계 생성은 실패한다.
- 기존 테스트와 클릭 시나리오는 깨지지 않는다.

### 6.2 2순위: 범용 객체 컨텍스트 API 추가

지시:

`get_order_context()`에 의존하지 않는 범용 컨텍스트 API를 추가하라.

완료 기준:

- `GET /api/ontology/objects/{object_id}/context` 제공
- incoming 관계 목록 반환
- outgoing 관계 목록 반환
- 관련 객체 요약 반환
- `Order`, `Customer`, `Product` 모두에서 동작

### 6.3 3순위: 관계 인스턴스 추가 API

지시:

사용자가 객체 간 관계를 추가할 수 있는 API를 구현하라.

완료 기준:

- `POST /api/ontology/relationships`
- 관계 타입 검증
- source/target 객체 타입 검증
- 관계 속성 검증
- 추가한 관계가 객체 컨텍스트와 AI 질의에 반영

### 6.4 4순위: 온톨로지 관리 화면

지시:

프론트엔드에 `온톨로지 관리` 메뉴를 추가하고, 객체 타입/관계 타입/관계 데이터를 조회할 수 있게 하라.

완료 기준:

- 객체 타입 카드 표시
- 관계 타입 카드 표시
- 객체 목록과 상세 표시
- incoming/outgoing 관계 표시
- 관계 추가 폼 제공

### 6.5 5순위: AI 답변에 관계 경로 표시

지시:

AI 질의 응답에 사용된 객체, 관계, 문서 근거를 분리해서 표시하라.

완료 기준:

- `ontology_context`에 객체와 관계가 분리되어 있다.
- `evidence`에 문서 근거가 분리되어 있다.
- `trace`에 어떤 관계 경로를 따라 컨텍스트를 만들었는지 표시한다.

## 7. 최종 평가

Claude Code가 만든 현재 구현은 "워크플로우가 온톨로지를 실제로 사용한다"는 점에서 좋은 성과다. 특히 `CLICK_TEST_CHECKLIST.md` 기준으로 사람이 클릭해서 확인할 수 있는 흐름까지 연결되어 있으므로, 단순 샘플보다 완성도가 높다.

그러나 온톨로지 자체만 놓고 보면 아직 팔란티어식 유연한 온톨로지와는 거리가 있다. 현재는 `Customer`, `Order`, `Product` 중심의 고정 업무 모델이고, 관계도 `PLACED_ORDER`, `ORDER_CONTAINS_PRODUCT`로 제한되어 있다.

따라서 다음 단계의 핵심 문장은 다음과 같다.

**워크플로우는 이미 유연한 그래프 실행 모델로 진입했다. 이제 온톨로지도 코드 하드코딩에서 벗어나, 설정 가능한 객체/관계/액션 모델로 전환해야 한다.**
