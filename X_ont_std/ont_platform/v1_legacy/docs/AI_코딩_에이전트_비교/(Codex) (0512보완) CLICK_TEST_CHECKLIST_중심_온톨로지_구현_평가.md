# (Codex) 0512 보완 — CLICK_TEST_CHECKLIST 중심 온톨로지 구현 평가

작성자: Codex  
작성일: 2026-05-12  
평가 대상: `E:\ontology_edu\claud_통합`  
중심 문서: `docs/CLICK_TEST_CHECKLIST.md`  
비교 기준: 기존 Codex 온톨로지 평가에서 지적한 하드코딩, 관계 탐색, 관계 CRUD, 온톨로지 UI 보완 여부

## 1. 결론

Claude Code가 기존에 지적된 온톨로지 문제를 상당히 보완했다. 최초 평가 당시에는 `Customer`, `Order`, `Product`, `PLACED_ORDER`, `ORDER_CONTAINS_PRODUCT`가 `backend/app/ontology.py`에 강하게 고정된 구조였고, 화면에서 관계를 추가하거나 온톨로지 그래프를 직접 탐색하는 기능도 없었다.

0512 보완 이후에는 다음 수준까지 올라왔다.

- 온톨로지 스키마 JSON 외부화
- 범용 incoming/outgoing 관계 탐색
- 관계 인스턴스 추가/삭제 API
- 온톨로지 그래프 캔버스 UI
- 액션 타입 일부 스키마화
- 민감 속성 자동 마스킹 설정화

따라서 현재 평가는 **"하드코딩된 온톨로지 데모"에서 "설정 기반 온톨로지 관리 MVP"로 상승**했다고 보는 것이 적절하다.

다만 팔란티어식 유연 온톨로지 플랫폼으로 보려면 아직 남은 과제가 있다. 새 객체 타입의 인스턴스 로딩, 워크플로우 노드 팔레트의 완전 동적화, 관계 삭제의 영속성 모델, 문서 정합성 최신화가 다음 보완 지점이다.

## 2. 검증 결과

재검증 명령은 `claud_be`, `claud_fe` conda 환경을 직접 사용했다.

| 항목 | 결과 |
| --- | --- |
| Backend pytest | `67 passed in 2.38s` |
| Scenario 검증 | `5/5 passed` |
| RAG evaluate | `10/10 passed` |
| Frontend build | `next build` 성공 |

프론트 빌드는 `claud_fe` 환경의 `node` 경로를 PATH에 포함해 실행했을 때 성공했다.

## 3. 기존 지적사항별 보완 판정

| 기존 지적 | 보완 상태 | 근거 | 판정 |
| --- | --- | --- | --- |
| 온톨로지 스키마가 코드에 하드코딩 | `ontology.default.json`으로 객체/관계/액션 타입 외부화 | `backend/app/config/ontology.default.json` | 해결 |
| `get_order_context` 중심의 고정 관계 탐색 | `object_context`, `find_relationships` 추가 | `backend/app/ontology.py` | 상당 부분 해결 |
| 관계 인스턴스 추가/삭제 불가 | `POST/DELETE /api/ontology/relationships` 추가 | `backend/app/main.py` | 해결 |
| 온톨로지 그래프 화면 없음 | React Flow 기반 온톨로지 그래프 캔버스 추가 | `frontend/src/components/OntologyExplorerCanvas.tsx` | 해결 |
| 민감 속성 마스킹이 코드 로직 중심 | 스키마 `sensitive` + `policy.default.json` 조합으로 전환 | `backend/app/policy.py` | 해결 |
| 액션이 온톨로지와 분리 | `action_types`를 스키마에 추가하고 백엔드 권한 정책에 반영 | `workflow_graph_engine.py` | 부분 해결 |
| AI 질의가 주문 중심 | Order 외 객체도 `object_context` 경로 사용 | `backend/app/app_context.py` | 부분 해결 |

## 4. 좋아진 점

### 4.1 스키마 외부화

`backend/app/config/ontology.default.json`에 객체 타입, 관계 타입, 액션 타입이 정의된다. 이제 최소한 타입 정의는 Python 코드 밖으로 나왔다.

현재 스키마에는 다음이 포함된다.

- `object_types`: `Customer`, `Product`, `Order`
- `relationship_types`: `PLACED_ORDER`, `ORDER_CONTAINS_PRODUCT`
- `action_types`: `ApproveOrder`, `RejectOrder`, `HoldOrder`, `RiskAssess`

특히 `id_prefix`, `display_name`, `icon`, `sensitive`, `searchable`, `enum_values` 같은 메타데이터가 들어간 점은 좋다. 단순한 타입 목록이 아니라 UI, 검색, 보안에 활용할 수 있는 구조가 되었다.

### 4.2 범용 관계 탐색

`OntologyRegistry.find_relationships(source_id?, target_id?, relationship_name?)`가 추가되었다. 이로써 특정 관계 함수만 호출하는 방식에서 벗어나, source/target/type 조건으로 관계를 찾을 수 있다.

`OntologyService.object_context(object_id)`도 추가되어 특정 객체 기준의 outgoing/incoming 관계를 반환한다. 이 부분은 온톨로지 플랫폼화에 중요한 진전이다.

### 4.3 관계 CRUD

관계 생성과 삭제 API가 생겼다.

```text
POST   /api/ontology/relationships
DELETE /api/ontology/relationships/{rel_id}
```

관계 생성 시 다음 검증도 수행한다.

- 관계 타입 존재 여부
- source 객체 존재 여부
- target 객체 존재 여부
- source/target 객체 타입 일치 여부

이는 이전 평가에서 요구한 "관계를 넣을 수 있는 구조"에 대한 직접적인 보완이다.

### 4.4 온톨로지 그래프 캔버스

`OntologyExplorerCanvas.tsx`가 추가되어 객체와 관계를 React Flow 캔버스로 볼 수 있다.

화면에서 가능한 일:

- 객체 노드 시각화
- 관계 edge 시각화
- 노드 클릭 시 속성 확인
- incoming/outgoing 관계 확인
- 관계 추가 모달
- 관계 삭제 버튼

이제 온톨로지가 백엔드 내부 모델에만 머물지 않고, 사용자가 직접 확인할 수 있는 화면 기능으로 올라왔다.

### 4.5 민감 속성 마스킹 설정화

`policy.default.json`과 온톨로지 스키마의 `sensitive: true`가 결합되었다. 이전처럼 특정 필드를 코드에서 직접 분기하는 방식보다 확장성이 좋아졌다.

새 객체 타입에 민감 속성을 추가하고 정책 파일에 규칙을 넣으면 같은 방식으로 마스킹할 수 있는 구조다.

## 5. 남은 한계

### 5.1 새 객체 타입의 인스턴스 로딩은 아직 범용이 아니다

스키마에 새 객체 타입을 추가하면 타입 등록은 된다. 하지만 실제 인스턴스 로딩은 아직 아래 데이터 구조에 고정되어 있다.

- `raw["customers"]`
- `raw["products"]`
- `raw["orders"]`
- `raw["order_items"]`

따라서 `Contract`, `Warehouse`, `Invoice` 같은 타입을 JSON에 추가해도, 해당 인스턴스를 범용 저장소에서 자동 로딩하는 구조는 아직 아니다.

필요한 다음 단계:

```json
{
  "ontology_objects": [
    {"id": "CT001", "type": "Contract", "values": {"title": "Enterprise Contract"}}
  ]
}
```

또는 DB 테이블을 `object_instances`, `relationship_instances` 형태로 일반화해야 한다.

### 5.2 객체 컨텍스트 API가 아직 공개 엔드포인트로 충분하지 않다

서비스 내부에는 `object_context(object_id)`가 있지만, REST API는 아직 주문 전용 경로가 더 강하다.

현재 강한 경로:

```text
GET /api/objects/orders/{order_id}/context
```

필요한 범용 경로:

```text
GET /api/ontology/objects/{object_id}/context
GET /api/ontology/objects?type=Customer
```

백엔드 내부 구현은 이미 일부 준비되어 있으므로 API만 추가하면 완성도가 올라간다.

### 5.3 액션 타입은 백엔드 일부만 동적화되었다

`ontology.default.json`의 `action_types`가 `WorkflowGraphEngine` 권한 정책에 반영되는 것은 좋다. 하지만 프론트의 워크플로우 노드 팔레트는 아직 `WorkflowGraph.tsx` 안의 `PALETTE` 상수에 고정되어 있다.

즉 JSON에 새 액션 타입을 추가하더라도, 화면 팔레트와 실행 핸들러가 완전히 자동 확장되는 것은 아니다.

필요한 다음 단계:

- 프론트 팔레트를 `/api/ontology/schema.action_types`에서 생성
- `exposed_as_graph_node=true`만 노드로 표시
- 노드별 입력 필드를 action schema에서 생성
- 백엔드 실행 핸들러도 generic action executor로 확장

### 5.4 기본 자동 관계 삭제의 의미가 애매하다

현재 관계 삭제 API는 `rel_id` 기준으로 in-memory 관계를 제거하고, `raw["ontology_relationships"]`에서 같은 ID를 제거한다.

문제는 기본 관계는 `orders`, `order_items`에서 매번 자동 생성된다는 점이다. 따라서 사용자가 기본 관계를 삭제해도 재시작 또는 reset 이후 다시 생성될 수 있다.

운영형 온톨로지에서는 관계를 다음처럼 구분해야 한다.

- system-derived relationship
- user-created relationship
- deleted/disabled relationship tombstone

삭제가 정말 삭제인지, 비활성화인지, 원천 데이터 재계산 대상인지를 명확히 해야 한다.

### 5.5 문서 정합성은 일부 남았다

최신 문서:

- `PROGRESS.md`
- `NEXT_STEPS.md`
- `CHANGELOG.md`

구버전 흔적이 남은 문서:

- `README.md`: `pytest 17 passed`, `pytest 36건` 흔적
- `FINAL_REPORT.md`: `59/59 PASS` 등 이전 수치
- `DEMO_SCENARIO.md`: `36 passed` 흔적
- `CLICK_TEST_CHECKLIST.md`: 회귀 검증 부분에 `59 passed` 흔적

문서 최신화는 기능 품질과 별개지만, 비교 보고서와 전달용 자료에서는 혼동을 만들 수 있으므로 정리하는 것이 좋다.

## 6. CLICK_TEST_CHECKLIST 관점 평가

현재 `CLICK_TEST_CHECKLIST.md`의 기존 5종 시나리오, AI 질의, 워크플로우 그래프 검증은 유지된다. 여기에 온톨로지 보완 검증 항목을 추가하면 더 좋다.

추가 권장 체크:

- [ ] `온톨로지 그래프` 메뉴 진입
- [ ] 객체 노드와 관계 edge가 표시됨
- [ ] `C001`, `O001`, `P001` 등 노드 클릭 시 상세 속성이 표시됨
- [ ] `O001` 노드에서 incoming `PLACED_ORDER`, outgoing `ORDER_CONTAINS_PRODUCT` 확인
- [ ] `AccountManager` 권한으로 관계 추가 성공
- [ ] 잘못된 source/target 타입으로 관계 추가 시 `TYPE_MISMATCH`
- [ ] `Viewer` 권한으로 관계 추가 시 `FORBIDDEN`
- [ ] `Admin` 권한으로 관계 삭제 성공
- [ ] `Customer` 또는 `Product` ID를 AI 질의에 넣었을 때 범용 객체 컨텍스트 사용

## 7. 다음 지시 사항

Claude Code에 추가로 지시한다면 우선순위는 다음과 같다.

1. 문서 수치 최신화
   - `README.md`, `FINAL_REPORT.md`, `DEMO_SCENARIO.md`, `CLICK_TEST_CHECKLIST.md`의 `17/36/59 passed` 흔적을 현재 `67 passed` 기준으로 정리한다.

2. 범용 객체 인스턴스 저장소 도입
   - `raw["customers"]`, `raw["products"]`, `raw["orders"]` 고정 로딩을 유지하되, 새 타입은 `raw["ontology_objects"]`에서 로딩하게 한다.

3. 범용 객체 컨텍스트 API 공개
   - `GET /api/ontology/objects/{object_id}/context`
   - `GET /api/ontology/objects?type=...`

4. 워크플로우 팔레트 동적화
   - `action_types`에서 노드 팔레트를 만들고, 하드코딩된 `PALETTE` 의존을 줄인다.

5. 관계 삭제 정책 명확화
   - 사용자 생성 관계와 원천 데이터 파생 관계를 구분한다.
   - 기본 관계 삭제는 비활성화 tombstone으로 관리할지 결정한다.

## 8. 최종 판정

이번 0512 보완은 실질적인 개선이다. 이전에 지적한 온톨로지 핵심 문제 중 절반 이상은 코드와 화면에 반영되었다. 특히 스키마 외부화, 관계 CRUD, 그래프 캔버스는 단순 문서 보완이 아니라 실제 프로그램 구조를 바꾼 변화다.

최종 평가는 다음과 같다.

| 구분 | 보완 전 | 0512 보완 후 |
| --- | --- | --- |
| 온톨로지 성격 | 하드코딩된 업무 데모 | 설정 기반 온톨로지 관리 MVP |
| 관계 관리 | 코드/원천 데이터에서 자동 조립 | API/UI로 사용자 추가 가능 |
| 그래프 탐색 | 주문 중심 | 객체 기준 incoming/outgoing 가능 |
| 화면 | 객체 탐색 중심 | 온톨로지 그래프 캔버스 추가 |
| 확장성 | 낮음 | 중간 |
| 운영형 플랫폼 완성도 | 초기 | MVP 이후 보강 단계 |

한 줄로 요약하면 다음과 같다.

**Claude Code의 0512 보완은 온톨로지 비평을 실제 코드 개선으로 상당히 흡수했다. 이제 남은 과제는 "스키마 외부화"가 아니라 "데이터와 액션까지 완전히 범용화"하는 것이다.**

