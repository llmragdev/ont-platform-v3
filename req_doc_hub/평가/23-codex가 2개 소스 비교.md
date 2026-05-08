# codex가 2개 소스 비교

## 1. 비교 목적

이 문서는 `22-codex가 2개 소스와 아키텍처, 기획 비교 기준.md`를 기준으로 `src_anti`와 `src_codex`를 비교한 결과입니다.

비교 대상:
- `src_anti`
- `src_codex`

기준 문서:
- `06_온톨로지_AI_업무화면_기획.md`
- `10_운영형_아키텍처_확장.md`
- `22-codex가 2개 소스와 아키텍처, 기획 비교 기준.md`

비교 원칙:
- 테스트 통과 여부보다 실제 소스 구조와 구현 내용을 중심으로 판단합니다.
- “더 좋은 코드” 하나를 뽑기보다, 용도별 적합성을 나눠 봅니다.
- 문서나 주석의 주장보다 실제 코드에 구현된 수준을 우선합니다.

## 2. 전체 요약

### 2.1 한 줄 결론

`src_anti`는 **업무 화면 MVP와 빠른 데모**에 강하고, `src_codex`는 **운영형 백엔드 아키텍처와 서비스 경계 설명**에 강합니다.

두 소스의 가장 좋은 결합 방향은 다음입니다.

> `src_anti`의 직관적인 화면 구조와 `src_codex`의 운영형 백엔드 구조를 결합한다.

### 2.2 종합 비교

| 비교 축 | src_anti | src_codex | 우세 |
| --- | --- | --- | --- |
| 업무 화면 기획 충족도 | 충족 | 부분 충족 | `src_anti` |
| 온톨로지 모델링 | 부분 충족 | 충족 | `src_codex` |
| RAG와 검색 | 부분 충족 | 충족 | `src_codex` |
| 워크플로우 | 부분 충족 | 충족 | `src_codex` |
| 권한과 거버넌스 | 부분 충족 | 충족 | `src_codex` |
| 감사 로그와 운영 관측성 | 부분 충족 | 충족 | `src_codex` |
| API와 오류 처리 | 부분 충족 | 충족 | `src_codex` |
| 데이터 저장과 확장성 | 미충족에 가까운 부분 충족 | 부분 충족 | `src_codex` |
| 테스트와 평가 | 부분 충족 | 충족 | `src_codex` |
| 교육용 이해도 | 충족 | 충족 | 용도 다름 |

## 3. 업무 화면 기획 충족도

기준 문서:
- `06_온톨로지_AI_업무화면_기획.md`

비교 항목:
- 대시보드
- 객체 탐색
- AI 질의
- 문서 근거
- 승인 워크플로우
- 우측 컨텍스트 패널
- 실행 이력 또는 감사 로그
- 선택 객체의 화면 전반 반영

### 3.1 `src_anti`

판단:
- **충족**

근거:
- `index.html`, `app.js`, `style.css`에 대시보드, 객체 탐색, AI 질의, 워크플로우, 감사 로그 화면이 구현되어 있습니다.
- 우측 컨텍스트 패널이 있고, 선택된 주문의 고객, 상태, 금액, 제품 정보가 갱신됩니다.
- AI 질의 결과에 답변, trace, evidence, 추천 액션이 표시됩니다.
- 워크플로우 액션 후 주문 목록과 컨텍스트를 다시 갱신합니다.
- 반응형 CSS도 일부 적용되어 있습니다.

한계:
- 문서 검색 전용 화면과 온톨로지 관리 화면은 별도 메뉴로 충분히 구현되어 있지 않습니다.
- `updateContext()`는 일부 직접 `fetch()`를 사용해 공통 오류 처리와 완전히 통일되어 있지는 않습니다.

### 3.2 `src_codex`

판단:
- **부분 충족**

근거:
- `index.html`, `app.js`, `style.css`가 있어 업무 UI는 존재합니다.
- 주문 컨텍스트, 질의, 워크플로우, 감사 로그 API를 사용할 수 있습니다.
- 백엔드 API가 화면에 필요한 데이터를 풍부하게 제공합니다.

한계:
- `src_codex`의 강점은 화면보다 백엔드 서비스 구조에 있습니다.
- `06` 문서가 기대하는 업무형 화면 완성도와 직관성은 `src_anti`가 더 강합니다.

### 3.3 판단

업무 화면 기획 기준으로는 `src_anti`가 더 충실합니다.

다만 `src_anti`는 화면과 데모 흐름이 강한 대신, 백엔드 운영 구조는 아직 얇습니다. `src_codex`는 화면 완성도보다 운영형 백엔드 구조를 보여주는 데 초점이 있습니다.

## 4. 온톨로지 모델링

기준 문서:
- `03_객체기반_온톨로지_직접_구현.md`
- `06_온톨로지_AI_업무화면_기획.md`
- `10_운영형_아키텍처_확장.md`

비교 항목:
- 객체 타입 정의
- 객체 인스턴스 관리
- 속성 정의
- 관계 타입 정의
- 관계 인스턴스 관리
- 객체 컨텍스트 조회
- 질문 속 객체 ID 추출
- 고객-주문 관계 검증

### 4.1 `src_anti`

판단:
- **부분 충족**

근거:
- `models.py`에 `Customer`, `Order`, `Product`, `Document` 같은 Pydantic 모델이 있습니다.
- `ontology.py`에 `detect_objects()`, `verify_relationship()`, `get_order_context()`가 있습니다.
- 질문에서 `C001`, `O001` 같은 ID를 추출하고 고객-주문 관계를 검증합니다.

한계:
- 객체 타입, 속성, 관계 타입, 관계 인스턴스를 명시적으로 등록하는 구조는 아닙니다.
- 관계는 `order["customerId"]`, `order["productIds"]`를 직접 따라가는 방식입니다.
- 온톨로지 엔진이라기보다는 “객체 컨텍스트 조립 서비스”에 가깝습니다.

### 4.2 `src_codex`

판단:
- **충족**

근거:
- `models.py`에 `ObjectType`, `PropertyDefinition`, `ObjectInstance`, `RelationshipDefinition`, `RelationshipInstance`, `ActionDefinition`, `WorkflowTransition` 등이 있습니다.
- `ontology.py`에서 객체 타입과 관계 타입을 등록하고, 객체 인스턴스를 생성하며, 관계를 link로 연결합니다.
- `get_order_context()`에서 주문, 고객, 제품 관계를 조회합니다.
- 고객-주문 관계가 맞지 않으면 `RELATION_MISMATCH` 오류를 발생시킵니다.

한계:
- 데이터 규모와 관계 탐색은 교육용 샘플 수준입니다.
- 그래프 DB나 외부 온톨로지 저장소를 쓰는 수준은 아닙니다.

### 4.3 판단

온톨로지 모델링은 `src_codex`가 명확히 우세합니다.

`src_anti`는 Pydantic DTO와 간단한 관계 검증이 있고, `src_codex`는 온톨로지 개념 자체가 코드 구조로 드러납니다.

## 5. RAG와 검색

기준 문서:
- `05_BM25_RAG_온톨로지_융합_구현.md`
- `06_온톨로지_AI_업무화면_기획.md`
- `10_운영형_아키텍처_확장.md`

비교 항목:
- 검색 서비스 분리
- 토크나이저 구현
- BM25 또는 검색 점수 계산
- 온톨로지 컨텍스트 기반 검색 질의 강화
- 문서 권한 필터링
- 검색 결과 score 반환
- RAG 프롬프트 생성
- 답변에 근거 문서 연결
- 실제 LLM 또는 LLM Gateway 분리

### 5.1 `src_anti`

판단:
- **부분 충족**

근거:
- `search.py`에 토큰화와 문서 점수 계산이 있습니다.
- `rag.py`가 객체 탐지, 컨텍스트 조회, 관계 검증, 문서 검색, 답변 생성을 순서대로 수행합니다.
- 응답에 `evidence`, `available_actions`, `trace`가 포함됩니다.

한계:
- `get_bm25_scores()`라는 이름을 쓰지만 실제 BM25는 아닙니다.
- IDF, 문서 길이 보정, `k1`, `b` 파라미터가 없습니다.
- 검색 질의 강화가 거의 없고, 질문 원문 중심 검색입니다.
- RAG 프롬프트 생성이나 LLM Gateway 분리는 없습니다.
- 답변 생성은 규칙 기반 휴리스틱입니다.

과장 표현 주의:
- `src_anti`를 “BM25 기반 RAG 구현”이라고 표현하면 과합니다.
- 더 정확히는 “토큰 매칭 검색 + 근거 문서 반환 + 규칙 기반 답변”입니다.

### 5.2 `src_codex`

판단:
- **충족**

근거:
- `search.py`에 실제 BM25 구성요소가 있습니다. IDF, 문서 길이, `k1`, `b` 기반 점수 계산을 합니다.
- `SearchService`는 사용자 역할에 따라 볼 수 있는 문서만 검색합니다.
- `RAGService.build_search_query()`가 질문에 고객 segment, risk tier, 주문 상태, 금액, 제품명 등을 결합해 검색 질의를 강화합니다.
- `RAGService.build_prompt()`가 온톨로지 컨텍스트와 문서 컨텍스트를 결합한 프롬프트를 생성합니다.
- `LLMGateway`가 별도 클래스로 분리되어 있습니다.

한계:
- 실제 외부 LLM API 호출은 없습니다.
- `LLMGateway`는 여전히 규칙 기반 답변을 생성합니다.
- 벡터 검색이나 하이브리드 검색은 없습니다.

### 5.3 판단

RAG와 검색 기준으로는 `src_codex`가 더 충실합니다.

`src_anti`는 화면에서 이해하기 쉬운 RAG 유사 흐름을 보여주고, `src_codex`는 운영형 RAG 구성요소를 더 정확하게 분리합니다.

## 6. 워크플로우

기준 문서:
- `04_워크플로우_핸즈온.md`
- `06_온톨로지_AI_업무화면_기획.md`
- `10_운영형_아키텍처_확장.md`

비교 항목:
- 액션 정의
- 상태 전이 정의
- 현재 상태 기반 액션 가능 여부 계산
- 액션 실행 전 권한 검증
- 허용되지 않는 액션 거부
- 상태 변경 저장
- 워크플로우 이벤트 기록
- 화면에서 액션 버튼 또는 큐 표시

### 6.1 `src_anti`

판단:
- **부분 충족**

근거:
- `workflow.py`에 상태 전이 테이블 `TRANSITIONS`가 있습니다.
- `Submitted`, `Review` 상태에서 승인, 반려, 보류 전이를 처리합니다.
- 허용되지 않는 전이는 실패 메시지를 반환합니다.
- UI에서 워크플로우 액션을 실행할 수 있습니다.

한계:
- 액션 자체가 별도 모델로 정의되어 있지는 않습니다.
- 권한 검증은 `main.py`에서 단순 문자열 권한으로 처리합니다.
- 워크플로우 이벤트 객체나 상세 실행 이력 모델은 약합니다.
- 상태 변경은 전역 메모리 repo에 반영됩니다.

### 6.2 `src_codex`

판단:
- **충족**

근거:
- `WorkflowEngine`과 `WorkflowService`가 분리되어 있습니다.
- `ActionDefinition`, `WorkflowTransition`, `WorkflowEvent` 모델이 있습니다.
- 상태 전이와 액션 실행 핸들러가 등록됩니다.
- 실행 전 `PolicyEngine`으로 액션 권한을 다시 검증합니다.
- 허용되지 않는 액션은 `ACTION_NOT_ALLOWED` 오류로 거부됩니다.
- 실행 결과는 감사 로그에 남고, 주문 상태 변경은 Repository 저장 콜백까지 연결됩니다.

한계:
- 이벤트 저장은 아직 메모리 중심입니다.
- 실제 워크플로우 엔진이나 장기 실행 프로세스 관리는 아닙니다.

### 6.3 판단

워크플로우는 `src_codex`가 더 운영형 구조에 가깝습니다.

`src_anti`도 상태 전이 테이블이 있어 MVP 수준에서는 충분하지만, 권한, 이벤트, 액션 모델까지 포함한 구조는 `src_codex`가 더 낫습니다.

## 7. 권한과 거버넌스

기준 문서:
- `08_온톨로지_권한_거버넌스_설계.md`
- `10_운영형_아키텍처_확장.md`

비교 항목:
- 사용자 모델
- 역할 모델
- 객체 조회 권한
- 문서 조회 권한
- 액션 실행 권한
- 속성 마스킹
- 권한 거부 오류
- 서버 측 권한 적용

### 7.1 `src_anti`

판단:
- **부분 충족**

근거:
- `policy.py`에 역할과 권한 목록이 있습니다.
- `main.py`에서 워크플로우 실행 전 `PolicyService.check_permission()`을 호출합니다.
- 고객 목록 조회에서 `riskTier` 마스킹 조건이 있습니다.

한계:
- `CURRENT_USER`, `CURRENT_ROLE`이 `main.py`에 하드코딩되어 있습니다.
- 현재 역할은 항상 `Admin`이므로 실제 사용자별 권한 차이가 거의 드러나지 않습니다.
- 객체 조회 권한, 문서 조회 권한, 속성 마스킹이 일관되게 서버 전체에 적용되지는 않습니다.
- 문서 검색에 권한 필터가 없습니다.

과장 표현 주의:
- `src_anti`를 “RBAC 구현 완료”라고 표현하면 과합니다.
- “역할/권한 골격 추가”가 더 정확합니다.

### 7.2 `src_codex`

판단:
- **충족**

근거:
- `data.py`에 사용자와 역할 데이터가 있습니다.
- `AppContext.user()`가 요청의 사용자 키를 해석합니다.
- `PolicyEngine`이 객체 조회 권한, 문서 조회 권한, 속성 마스킹, 액션 권한을 담당합니다.
- 객체 접근 권한이 없으면 `FORBIDDEN` 오류를 발생시키고 감사 로그를 남깁니다.
- RAG 검색 전 문서 권한 필터가 적용됩니다.
- 워크플로우 실행 전 액션 권한을 재검증합니다.

한계:
- 실제 로그인, 세션, 토큰 인증은 없습니다.
- 역할과 권한 모델은 코드 내 샘플 데이터입니다.

### 7.3 판단

권한과 거버넌스는 `src_codex`가 더 충실합니다.

`src_anti`는 권한 규칙을 보여주는 수준이고, `src_codex`는 서버 로직 여러 경로에서 권한을 실제로 적용합니다.

## 8. 감사 로그와 운영 관측성

기준 문서:
- `09_RAG_평가와_운영_설계.md`
- `10_운영형_아키텍처_확장.md`

비교 항목:
- 객체 조회 로그
- AI 질의 로그
- 검색 로그
- 권한 거부 로그
- 워크플로우 실행 로그
- 실패 이벤트 로그
- 감사 로그 조회 API
- 화면에서 감사 로그 확인 가능 여부
- latency, retrieved documents, detected objects 같은 운영 메타데이터

### 8.1 `src_anti`

판단:
- **부분 충족**

근거:
- `audit.py`에 `AuditService.log_event()`가 있습니다.
- `main.py`에서 데이터 조회, AI 질의, 워크플로우 실행, 실패, 시스템 리셋을 기록합니다.
- `/api/audit/events` API와 화면의 감사 로그 메뉴가 있습니다.

한계:
- 로그가 문자열 description 중심입니다.
- 검색 단계, 관계 검증 실패, 검색 결과 문서, latency 같은 운영 메타데이터는 구조적으로 충분히 남지 않습니다.
- `RAGService` 내부 단계별 로그는 감사 로그가 아니라 응답 trace에 가깝습니다.

### 8.2 `src_codex`

판단:
- **충족**

근거:
- `AuditService`가 이벤트 타입, actor, object type, object id, detail, occurred_at을 구조화해 기록합니다.
- 객체 컨텍스트 조회, 문서 검색, 질의 완료, 질의 실패, 접근 거부, 액션 거부, 액션 실행 등이 기록됩니다.
- `ASK_COMPLETED`에는 질문, detected objects, search query, retrieved documents, answer status, latency가 들어갑니다.
- `ASK_FAILED`도 별도로 기록됩니다.
- `/api/audit/events` API가 있습니다.

한계:
- 외부 로그 저장소나 모니터링 대시보드는 없습니다.
- 장기 보존, 검색, SIEM 연동은 아직 없습니다.

### 8.3 판단

운영 관측성은 `src_codex`가 더 충실합니다.

`src_anti`는 화면에서 감사 로그를 볼 수 있다는 장점이 있고, `src_codex`는 로그 구조와 기록 범위가 더 운영형에 가깝습니다.

## 9. API와 오류 처리

기준 문서:
- `10_운영형_아키텍처_확장.md`

비교 항목:
- `/api/me`
- `/api/ontology/object-types`
- `/api/objects/customers`
- `/api/objects/orders`
- `/api/objects/orders/:id/context`
- `/api/search`
- `/api/ask`
- `/api/workflow/queue`
- `/api/workflow/execute`
- `/api/audit/events`
- 표준 오류 코드
- 프론트엔드 오류 표시

### 9.1 `src_anti`

판단:
- **부분 충족**

근거:
- 고객, 주문, 주문 컨텍스트, AI 질의, 워크플로우 실행, 감사 로그 API가 있습니다.
- FastAPI의 `HTTPException`을 사용합니다.
- 프론트엔드에 `apiCall()` 공통 래퍼와 오류 메시지 표시가 있습니다.

한계:
- `/api/me`, `/api/search`, `/api/workflow/queue`, `/api/ontology/object-types`는 없습니다.
- 오류 코드가 표준 도메인 코드로 분리되어 있지 않고, FastAPI 기본 `detail` 메시지 중심입니다.
- 관계 불일치가 HTTP 오류가 아니라 정상 응답의 답변 문장으로 표현됩니다.

### 9.2 `src_codex`

판단:
- **충족**

근거:
- `/api/me`, `/api/ontology/object-types`, `/api/objects/customers`, `/api/objects/orders`, `/api/objects/orders/:id/context`, `/api/search`, `/api/ask`, `/api/workflow/queue`, `/api/workflow/execute`, `/api/audit/events`가 있습니다.
- `AppError`로 `OBJECT_NOT_FOUND`, `RELATION_MISMATCH`, `FORBIDDEN`, `ACTION_NOT_ALLOWED`, `DOCUMENT_NOT_FOUND` 등 도메인 오류를 표현합니다.
- 서버가 JSON 오류 응답을 통일해서 반환합니다.

한계:
- FastAPI가 아니라 Python 표준 `http.server` 기반이라, 실제 운영 API 서버로는 보완이 필요합니다.
- OpenAPI 문서 자동 생성 같은 편의는 없습니다.

### 9.3 판단

API 범위와 도메인 오류 처리 기준으로는 `src_codex`가 더 충실합니다.

다만 웹 프레임워크 기반 개발 경험은 FastAPI를 쓰는 `src_anti`가 더 친숙할 수 있습니다.

## 10. 데이터 저장과 확장성

기준 문서:
- `10_운영형_아키텍처_확장.md`

비교 항목:
- 메모리 데이터 구조
- Repository 분리 여부
- JSON 또는 DB 영속성
- 저장소 교체 가능성
- 상태 변경의 저장
- 서버 재시작 후 데이터 유지 가능성

### 10.1 `src_anti`

판단:
- **미충족에 가까운 부분 충족**

근거:
- `data.py`에 `Repository` 클래스가 있고, 전역 `repo` 인스턴스를 통해 데이터를 관리합니다.
- `/api/system/reset`으로 테스트/데모 상태를 초기화할 수 있습니다.
- 워크플로우 실행 시 전역 repo의 주문 상태가 변경됩니다.

한계:
- 파일이나 DB 영속성은 없습니다.
- Repository 인터페이스나 저장소 교체 구조는 약합니다.
- 전역 mutable 상태에 의존합니다.
- 서버 재시작 후 상태가 유지되지 않습니다.

주의:
- 기존 `23-anti` 문서에는 `src_anti`가 JSON 파일 기반 Repository를 지원한다고 적혀 있지만, 실제 소스 기준으로는 맞지 않습니다.

### 10.2 `src_codex`

판단:
- **부분 충족**

근거:
- `repository.py`에 `DataRepository`, `InMemoryDataRepository`, `JsonFileDataRepository`가 있습니다.
- `AppContext`가 Repository를 주입받을 수 있습니다.
- `ONTOLOGY_DATA_PATH` 환경변수가 있으면 JSON 파일 기반 저장소를 사용합니다.
- 워크플로우로 변경된 주문 상태가 Repository 저장 콜백으로 이어집니다.

한계:
- 실제 PostgreSQL, Snowflake 같은 DB 저장소는 없습니다.
- JSON 저장은 교육용 영속성에 가깝습니다.

### 10.3 판단

데이터 저장과 확장성은 `src_codex`가 우세합니다.

`src_anti`는 전역 메모리 Repository이고, `src_codex`는 최소한 저장소 교체와 JSON 영속성의 길을 열어두었습니다.

## 11. 테스트와 평가

기준 문서:
- `09_RAG_평가와_운영_설계.md`
- `10_운영형_아키텍처_확장.md`

비교 항목:
- 단위 테스트
- API 통합 테스트
- RAG 평가 스크립트
- 관계 불일치 테스트
- 권한 테스트
- 워크플로우 상태 전이 테스트
- 테스트 상태 초기화
- 프론트엔드 E2E 테스트

### 11.1 `src_anti`

판단:
- **부분 충족**

근거:
- `backend/test_main.py`에 FastAPI `TestClient` 기반 API 테스트가 있습니다.
- 고객/주문 조회, 주문 컨텍스트, AI 질의, 관계 불일치, 워크플로우 유효/무효 전이, 감사 로그 테스트가 있습니다.
- `/api/system/reset`과 fixture로 테스트 상태 초기화를 시도합니다.

한계:
- 별도 RAG 평가 스크립트는 없습니다.
- 권한/문서 필터/마스킹 테스트는 제한적입니다.
- 프론트엔드 E2E 테스트는 없습니다.

### 11.2 `src_codex`

판단:
- **충족**

근거:
- `run_tests.py`가 단위 및 API 통합 테스트를 실행합니다.
- `tests/test_services.py`, `tests/test_api.py`가 서비스 흐름과 API 흐름을 검증합니다.
- 관계 불일치, 객체 없음, 문서 권한 필터, 속성 마스킹, 워크플로우 권한 재검증, JSON Repository 영속성을 확인합니다.
- `evaluate.py`가 RAG/온톨로지 시나리오 평가를 수행합니다.

한계:
- 프론트엔드 E2E 테스트는 없습니다.
- 실제 LLM 품질 평가는 아닙니다.

### 11.3 판단

테스트와 평가 기준으로는 `src_codex`가 더 충실합니다.

특히 `evaluate.py`가 있다는 점이 `src_anti`와의 큰 차이입니다.

## 12. 교육용 이해도

기준 문서:
- 전체 핸즈온 문서 흐름

비교 항목:
- 코드가 읽기 쉬운가
- 파일 구조가 학습 흐름과 맞는가
- 기능이 너무 숨겨져 있지 않은가
- 작은 예제로 핵심 개념이 보이는가
- `src_anti`와 `src_codex`의 역할 차이가 학습자에게 분명한가

### 12.1 `src_anti`

판단:
- **충족**

강점:
- FastAPI와 Vanilla JS 조합이라 웹 앱 구조를 이해하기 쉽습니다.
- 화면 메뉴와 사용자 흐름이 직관적입니다.
- 대시보드, 질의, 워크플로우, 감사 로그를 눈으로 확인하기 좋습니다.
- 처음 배우는 사람에게 “온톨로지 AI 업무 화면이 이런 모습이구나”를 보여주기 좋습니다.

주의:
- 소스 안의 “BM25”, “RBAC”, “Operational” 같은 표현은 실제 구현보다 강하게 느껴질 수 있습니다.
- 교육 시에는 “개념을 맛보는 구현”이라고 설명하는 것이 안전합니다.

### 12.2 `src_codex`

판단:
- **충족**

강점:
- 온톨로지, RAG, Policy, Workflow, Audit, Repository가 파일과 클래스로 분리되어 있어 운영형 구조를 설명하기 좋습니다.
- 질문 처리 흐름이 `AppContext.ask()` 안에서 단계별로 드러납니다.
- 권한, 관계 검증, 문서 필터, 감사 로그 같은 운영 요소가 코드로 비교적 명확합니다.

주의:
- 초보자에게는 `src_anti`보다 추상화가 많아 보일 수 있습니다.
- 화면 경험보다 백엔드 아키텍처 학습에 더 적합합니다.

### 12.3 판단

교육용 이해도는 승자를 하나로 정하기보다 역할을 나누는 것이 맞습니다.

- `src_anti`: 화면 중심 MVP 학습용
- `src_codex`: 운영형 백엔드 아키텍처 학습용

## 13. 기준 문서 대비 최종 평가

### 13.1 `06_온톨로지_AI_업무화면_기획.md` 기준

`src_anti`가 더 충실합니다.

이유:
- 실제 업무 화면 구조가 더 선명합니다.
- 대시보드, 객체 탐색, AI 질의, 워크플로우, 감사 로그 메뉴가 UI에 잘 드러납니다.
- 선택 객체를 중심으로 우측 컨텍스트 패널이 갱신됩니다.

단, `src_anti`도 문서 검색 전용 화면과 온톨로지 관리 화면은 부족합니다.

### 13.2 `10_운영형_아키텍처_확장.md` 기준

`src_codex`가 더 충실합니다.

이유:
- 서비스 경계가 더 명확합니다.
- Ontology, RAG, Search, Policy, Workflow, Audit, Repository가 분리되어 있습니다.
- 질문 처리 흐름이 운영형 순서와 더 가깝습니다.
- 권한, 문서 필터, 속성 마스킹, 표준 오류, 감사 로그, 평가 스크립트가 더 체계적입니다.

단, `src_codex`도 실제 LLM, 실제 DB, 실제 인증, 배포 관측성까지 갖춘 상용 구현은 아닙니다.

## 14. 두 소스의 적합한 용도

### 14.1 `src_anti`가 적합한 경우

- 온톨로지 AI 업무 화면을 빠르게 시연하고 싶을 때
- 프론트엔드와 FastAPI 연결 구조를 보여주고 싶을 때
- 업무 담당자에게 화면 흐름을 설명하고 싶을 때
- MVP에서 어떤 메뉴와 패널이 필요한지 보여주고 싶을 때

### 14.2 `src_codex`가 적합한 경우

- 운영형 AI 애플리케이션의 백엔드 구조를 설명하고 싶을 때
- 온톨로지, RAG, 권한, 워크플로우, 감사 로그의 책임 분리를 보여주고 싶을 때
- `10_운영형_아키텍처_확장.md`의 구현 예시를 보여주고 싶을 때
- 향후 DB, LLM, 인증, 벡터 검색으로 확장할 골격을 만들고 싶을 때

## 15. 결합 방향

두 소스를 하나의 방향으로 합친다면 다음이 가장 좋습니다.

### 15.1 유지할 것

`src_anti`에서 유지할 것:
- 직관적인 업무 화면
- 대시보드, 객체 탐색, AI 질의, 워크플로우, 감사 로그 메뉴
- 우측 컨텍스트 패널
- FastAPI 기반 개발 편의성

`src_codex`에서 유지할 것:
- `AppContext` 중심 조립 구조
- `OntologyService`
- `RAGService`
- `SearchService`
- `PolicyEngine`
- `WorkflowService`
- `AuditService`
- `Repository` 계층
- `AppError` 기반 도메인 오류
- `evaluate.py` 기반 평가 흐름

### 15.2 권장 통합 구조

```text
frontend/
  src_anti의 화면 구조를 개선해 사용

backend/
  FastAPI 기반 서버
  src_codex의 서비스 구조 이식
  Repository 계층 유지
  AppError를 FastAPI exception handler로 변환
  /api/me
  /api/ontology/object-types
  /api/search
  /api/ask
  /api/workflow/queue
  /api/workflow/execute
  /api/audit/events
```

### 15.3 개선 우선순위

1. `src_anti` 프론트엔드를 유지하고 백엔드를 `src_codex` 구조로 교체
2. FastAPI에 `src_codex`의 `AppError`, `PolicyEngine`, `OntologyService`, `WorkflowService` 이식
3. 문서 검색 전용 화면 추가
4. `/api/me`와 사용자 선택 기능 추가
5. 실제 LLM Gateway 연동
6. PostgreSQL 또는 Snowflake Repository 추가
7. 벡터 검색 또는 하이브리드 검색 추가
8. 프론트엔드 E2E 테스트 추가

## 16. 최종 결론

`src_anti`와 `src_codex`는 경쟁 관계라기보다 역할이 다른 두 샘플입니다.

`src_anti`는 사용자가 보는 화면과 MVP 흐름을 잘 보여줍니다. 따라서 `06_온톨로지_AI_업무화면_기획.md`의 화면 기획을 설명하기 좋습니다.

`src_codex`는 운영형 백엔드 구조를 더 잘 보여줍니다. 따라서 `10_운영형_아키텍처_확장.md`의 서비스 경계와 운영 요구를 설명하기 좋습니다.

최종적으로는 다음 판단이 가장 적절합니다.

> 화면은 `src_anti`, 운영형 백엔드는 `src_codex`가 더 낫다.

따라서 다음 단계의 목표는 어느 하나를 버리는 것이 아니라, `src_anti`의 화면성과 `src_codex`의 운영형 구조를 합쳐 **업무 화면과 운영 아키텍처가 모두 살아 있는 통합 샘플**로 발전시키는 것입니다.
