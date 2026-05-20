# src_anti 프로그램 평가

## 1. 평가 대상

평가 대상은 `src_anti` 폴더의 온톨로지 AI 업무 화면 구현입니다.

구성 파일:

- `src_anti/index.html`
- `src_anti/style.css`
- `src_anti/app.js`
- `src_anti/backend/main.py`
- `src_anti/backend/test_main.py`
- `src_anti/README.md`

`src_anti`는 Vanilla HTML/CSS/JavaScript 프론트엔드와 FastAPI 백엔드를 연결한 교육용 온톨로지 업무 화면입니다. 주요 기능은 주문 객체 조회, 고객/제품 컨텍스트 표시, AI 질의, 워크플로우 액션 실행입니다.

## 2. 전체 평가 요약

`src_anti`는 `06_온톨로지_AI_업무화면_기획.md`의 MVP 화면 방향은 어느 정도 구현했습니다. 좌측 메뉴, 중앙 작업 영역, 우측 컨텍스트 패널, AI 질의, 승인 워크플로우가 있어 사용자가 온톨로지 업무 앱의 형태를 빠르게 이해할 수 있습니다.

다만 `10_운영형_아키텍처_확장.md` 기준으로 보면 아직 운영형 아키텍처라기보다는 목 데이터 기반 FastAPI 데모에 가깝습니다. Auth, Policy Engine, BM25/RAG, Audit, 평가/모니터링, 오류 표준화, 권한 필터링, 상태 전이 검증이 대부분 단순화되어 있습니다.

평가 등급:

| 항목 | 평가 |
| --- | --- |
| 화면 MVP | 양호 |
| 백엔드 API 분리 | 보통 |
| 온톨로지 모델링 | 기초 수준 |
| 워크플로우 검증 | 미흡 |
| RAG/BM25 구현 | 미흡 |
| 권한/거버넌스 | 미흡 |
| 감사 로그 | 없음 |
| 자동 테스트 | 존재하지만 실행 환경 관리 미흡 |
| 운영형 확장성 | 낮음 |

## 3. 잘 구현된 부분

### 3.1 업무형 화면 구조

화면은 업무 애플리케이션 구조를 잘 따릅니다.

- 좌측 메뉴
- 중앙 업무 영역
- 우측 컨텍스트 패널
- 대시보드, 객체 탐색, AI 질의, 워크플로우 메뉴

이는 `06_온톨로지_AI_업무화면_기획.md`의 기본 레이아웃과 잘 맞습니다.

### 3.2 프론트엔드와 백엔드 분리

프론트엔드는 `fetch`를 통해 FastAPI 백엔드와 통신합니다.

구현된 API:

- `GET /api/objects/customers`
- `GET /api/objects/orders`
- `GET /api/objects/orders/{order_id}`
- `POST /api/ask`
- `POST /api/workflow/execute`

초기 목 데이터 화면에서 서버 API 분리 단계로 넘어간 점은 긍정적입니다.

### 3.3 객체 컨텍스트 표시

주문을 선택하면 우측 패널에 다음 정보가 갱신됩니다.

- 주문 ID
- 주문 상태
- 주문 금액
- 고객 이름
- 고객 리스크 등급
- 관련 제품 목록

객체 중심 업무 화면이라는 목표와 잘 맞습니다.

### 3.4 기본 자동 테스트 존재

`backend/test_main.py`에 FastAPI `TestClient` 기반 테스트가 있습니다.

테스트 대상:

- 고객 목록 조회
- 주문 목록 조회
- 주문 컨텍스트 조회
- 주문 없음 오류
- AI 질의 답변
- 워크플로우 실행

테스트 파일이 있는 점은 좋습니다.

## 4. 주요 문제점

### 4.1 실행 환경이 재현 가능하지 않음

README는 다음 설치를 안내합니다.

```bash
pip install fastapi uvicorn pydantic
pip install pytest httpx
```

하지만 `requirements.txt`, `pyproject.toml`, `environment.yml` 같은 의존성 파일이 없습니다. 실제 테스트 실행 결과 현재 환경에서는 `fastapi`가 없어 테스트 수집 단계에서 실패했습니다.

실행 결과:

```text
ModuleNotFoundError: No module named 'fastapi'
```

보완:

- `src_anti/backend/requirements.txt` 추가
- 설치 후 테스트 실행을 README에 명확히 작성
- 가능하면 `python -m venv .venv` 기준 절차 제공

### 4.2 온톨로지 모델이 명시적이지 않음

현재 백엔드는 `customers`, `orders`, `products`, `documents` 리스트를 직접 다룹니다. 객체 타입, 속성 정의, 관계 정의, 관계 인스턴스, 액션 정의가 별도 모델로 분리되어 있지 않습니다.

문제:

- `Customer -> Order`
- `Order -> Product`
- `Order` 위의 `ApproveOrder`

이런 개념이 코드 구조로 드러나지 않습니다.

보완:

- `ObjectType`, `ObjectInstance`, `RelationshipDefinition`, `ActionDefinition` 모델 추가
- `OntologyService` 계층 생성
- 주문 컨텍스트 조회를 단순 조합이 아니라 관계 탐색으로 구현

### 4.3 질문 속 객체 관계 검증이 없음

`POST /api/ask`는 질문에서 `C001`, `O001` 같은 객체 ID를 추출하지 않습니다. 대신 `selectedOrderId` 또는 기본값 `O001`을 사용합니다.

문제 예:

```text
C001 고객과 O002 주문은 연결되어 있어?
```

실제 데이터에서 `O002.customerId`가 `C002`여도, 현재 구현은 관계 불일치를 명확히 반환하지 못합니다.

보완:

- 질문에서 `C\d{3}`, `O\d{3}` 패턴 추출
- 고객 ID와 주문 ID 관계 검증
- 불일치 시 `RELATION_MISMATCH` 오류 반환

### 4.4 BM25/RAG가 실제로 구현되어 있지 않음

현재 AI 질의는 규칙 기반 분기입니다.

- 승인 질문이면 `documents[0]`, `documents[2]`를 고정 반환
- 그 외 질문이면 `documents[1]`을 반환

BM25 점수 계산, 검색 질의 강화, 문서 권한 필터링, RAG 프롬프트 생성이 없습니다.

보완:

- 토크나이저 구현
- BM25 검색기 추가
- 온톨로지 컨텍스트로 검색 질의 강화
- 검색 결과에 `score` 포함
- RAG 프롬프트를 생성해 화면에 표시

### 4.5 워크플로우 상태 전이 검증이 약함

`POST /api/workflow/execute`는 현재 상태와 액션 가능 여부를 검증하지 않습니다.

문제:

- 이미 `Approved`인 주문에도 `ApproveOrder`를 다시 실행할 수 있음
- 알 수 없는 액션이 와도 명확한 오류가 없음
- `HoldOrder`가 `Submitted`로 되돌아가는데, 보류 상태를 표현하는 `Review` 또는 `OnHold`가 없음

보완:

- 상태 전이 테이블 추가
- `Submitted -> ApproveOrder -> Approved`
- `Submitted -> RejectOrder -> Rejected`
- `Submitted -> HoldOrder -> Review`
- 현재 상태에서 허용되지 않는 액션이면 409 오류 반환

### 4.6 권한과 거버넌스가 없음

운영형 아키텍처에서는 모든 API에서 인증과 권한을 확인해야 합니다. 현재 구현에는 사용자, 역할, 객체 권한, 문서 권한, 액션 권한이 없습니다.

문제:

- 모든 사용자가 모든 주문과 고객을 볼 수 있음
- 고액 주문 승인 권한 구분 없음
- 위험 고객 정보와 계약 정보 마스킹 없음
- 문서 접근 권한 필터 없음

보완:

- `GET /api/me` 추가
- 역할 모델 추가: `Viewer`, `Analyst`, `AccountManager`, `FinanceManager`, `Admin`
- 객체 조회 전 권한 확인
- 문서 검색 시 권한 필터 적용
- 민감 속성 마스킹
- 액션 실행 전 권한 재검증

### 4.7 감사 로그가 없음

`10_운영형_아키텍처_확장.md`는 감사 로그를 핵심 서비스로 둡니다. 현재는 워크플로우 이벤트나 질의 로그가 저장되지 않습니다.

보완:

- `audit_events` 저장소 추가
- 다음 이벤트 기록:
  - 객체 조회
  - AI 질의
  - 문서 검색
  - 권한 거부
  - 액션 실행
- `GET /api/audit/events` API 추가
- 화면에 감사 로그 메뉴 추가

### 4.8 API 오류 처리가 사용자에게 충분히 전달되지 않음

프론트엔드는 `fetch` 후 `response.ok`를 확인하지 않고 바로 JSON을 읽습니다. 백엔드 오류가 와도 사용자에게 구체적인 메시지를 보여주기 어렵습니다.

보완:

- 공통 API 호출 함수 작성
- `response.ok` 확인
- 오류 코드와 사용자 메시지 표시
- 빈 상태, 로딩 상태, 재시도 버튼 제공

### 4.9 프론트엔드가 특정 백엔드 주소에 고정됨

`app.js`에는 다음 값이 하드코딩되어 있습니다.

```javascript
const API_BASE = "http://localhost:8000/api";
```

문제:

- 포트 변경 시 수정 필요
- 배포 환경에서 동작 어려움
- 같은 서버에서 정적 파일을 서빙하는 경우 상대 경로가 더 적합함

보완:

```javascript
const API_BASE = `${window.location.origin}/api`;
```

또는 설정 파일을 분리합니다.

### 4.10 테스트가 상태 오염에 취약함

`test_workflow_execution`은 실제 전역 `orders` 리스트의 `O001` 상태를 `Approved`로 변경합니다. 이후 테스트가 추가되면 순서에 따라 실패할 수 있습니다.

보완:

- 테스트마다 데이터 초기화
- FastAPI dependency로 repository 주입
- `pytest.fixture(autouse=True)`로 목 데이터 리셋
- 전역 mutable 상태 최소화

### 4.11 프론트엔드 자동 테스트가 없음

백엔드 API 테스트는 있지만 화면 테스트는 없습니다.

보완:

- Playwright 또는 Selenium 기반 테스트 추가
- 메뉴 전환
- 주문 선택 시 컨텍스트 갱신
- AI 질의 실행 후 답변/근거 표시
- 워크플로우 액션 후 주문 상태 갱신

### 4.12 반응형 UI가 부족함

CSS는 3열 고정 레이아웃입니다.

```css
#app {
  display: grid;
  grid-template-columns: 260px 1fr 340px;
  height: 100vh;
}
```

모바일 또는 좁은 화면 대응을 위한 media query가 없습니다. `body { overflow: hidden; }` 때문에 작은 화면에서 콘텐츠 접근성이 나빠질 수 있습니다.

보완:

- `@media` 쿼리 추가
- 작은 화면에서는 우측 컨텍스트를 아래로 이동
- 메뉴를 상단 또는 접이식으로 전환
- `overflow: hidden` 제거 또는 영역별 스크롤 개선

## 5. 문서 요구사항 대비 충족도

| 요구 흐름 | 현재 충족도 | 평가 |
| --- | --- | --- |
| 객체 기반 온톨로지 | 낮음 | 리스트 기반 데이터 조합 수준 |
| 객체 관계 검증 | 낮음 | 주문 상세 조회는 가능하지만 질문 속 관계 검증 없음 |
| BM25 검색 | 없음 | 고정 문서 반환 |
| RAG 프롬프트 | 없음 | 답변 생성 컨텍스트가 명시적으로 없음 |
| 워크플로우 | 보통 이하 | 상태 변경은 가능하지만 전이 검증 없음 |
| 업무 화면 | 보통 | MVP 화면 구성은 잘 되어 있음 |
| 권한/거버넌스 | 없음 | 사용자/역할/문서 권한 없음 |
| 감사 로그 | 없음 | 이벤트 저장 없음 |
| 운영 오류 처리 | 낮음 | 오류 코드 표준화 없음 |
| 자동 테스트 | 보통 이하 | 테스트는 있으나 의존성/상태 초기화 보완 필요 |

## 6. 보완 우선순위

### 1순위: 실행 가능성 보장

- `requirements.txt` 추가
- README 실행 절차 검증
- `pytest`가 클린 환경에서 통과하도록 수정

### 2순위: 백엔드 서비스 경계 분리

추천 구조:

```text
backend/
  main.py
  models.py
  data.py
  ontology.py
  policy.py
  search.py
  rag.py
  workflow.py
  audit.py
  tests/
```

`main.py`에 모든 로직이 모여 있으면 교육용 설명은 쉬워도 운영형 확장에는 불리합니다.

### 3순위: 온톨로지와 RAG 실제 구현

- 질문 객체 ID 추출
- 관계 검증
- BM25 검색
- 온톨로지 컨텍스트 + 문서 컨텍스트 결합
- 프롬프트 생성
- 근거 기반 답변 반환

### 4순위: 권한과 감사 로그 추가

- 사용자 역할
- 객체/문서/액션 권한
- 속성 마스킹
- 감사 로그 저장
- 권한 거부 이벤트 기록

### 5순위: 프론트엔드 안정화

- API 오류 공통 처리
- 로딩/빈 상태 표시
- 액션 버튼 활성/비활성 처리
- 하드코딩된 API 주소 제거
- 반응형 레이아웃 개선

## 7. 개선된 API 응답 예시

`POST /api/ask`는 현재 `answer`, `evidence`만 반환합니다. 운영형으로는 다음 형태가 더 좋습니다.

```json
{
  "answer": "승인 가능성이 높습니다.",
  "detected_objects": ["C001", "O001"],
  "ontology_context": {
    "customer_id": "C001",
    "order_id": "O001"
  },
  "evidence": [
    {
      "document_id": "D001",
      "title": "Order Approval Policy",
      "score": 3.82
    }
  ],
  "available_actions": ["ApproveOrder", "RejectOrder"],
  "trace": [
    "auth_checked",
    "objects_detected",
    "relation_verified",
    "documents_retrieved",
    "answer_generated",
    "audit_logged"
  ]
}
```

## 8. 자동 테스트 보완 제안

추가해야 할 테스트:

- 질문 `"C001 고객과 O002 주문은 연결되어 있어?"`가 관계 불일치 오류를 반환하는지
- `"O999 주문 상태"`가 객체 없음 오류를 반환하는지
- `Approved` 상태 주문에 `ApproveOrder`가 거부되는지
- 고액 주문은 `AccountManager`가 승인할 수 없는지
- 권한 없는 문서가 검색 결과에 포함되지 않는지
- AI 답변에 권한 없는 민감 속성이 포함되지 않는지
- 워크플로우 실행 후 감사 로그가 남는지
- 프론트엔드에서 API 오류를 사용자 메시지로 표시하는지

## 9. 결론

`src_anti`는 온톨로지 AI 업무 화면의 첫 MVP로는 의미가 있습니다. 화면 구성이 명확하고, FastAPI 백엔드를 붙여 프론트와 서버를 분리한 점도 좋습니다.

하지만 운영형 아키텍처 관점에서는 아직 핵심 서비스 경계가 코드로 충분히 분리되지 않았고, BM25/RAG, 권한, 감사 로그, 상태 전이 검증, 오류 표준화가 부족합니다. 다음 단계에서는 단순 데모를 넘어서 `OntologyService`, `PolicyEngine`, `WorkflowService`, `SearchService`, `RAGService`, `AuditService`를 명확히 나누고, 테스트가 그 경계를 검증하도록 보완하는 것이 좋습니다.
