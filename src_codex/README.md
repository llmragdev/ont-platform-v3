# Operational Ontology Console

`01`부터 `10_운영형_아키텍처_확장.md`까지의 흐름을 하나로 묶은 교육용 운영 데모입니다. 정적 목 화면이 아니라 Python 백엔드가 온톨로지, 권한, BM25/RAG, 워크플로우, 감사 로그를 실행하고, 화면은 `/api/...`를 호출합니다.

## 실행

```bash
cd src_codex
python server.py
```

브라우저에서 다음 주소를 엽니다.

```text
http://127.0.0.1:8000
```

별도 실습 프로그램도 실행할 수 있습니다.

```bash
python cli_demo.py
python evaluate.py
python run_tests.py
```

## 구현된 API

- `GET /api/me`
- `GET /api/ontology/object-types`
- `GET /api/objects/customers`
- `GET /api/objects/orders`
- `GET /api/objects/orders/:id`
- `GET /api/objects/orders/:id/context`
- `POST /api/search`
- `POST /api/ask`
- `GET /api/workflow/queue`
- `POST /api/workflow/execute`
- `GET /api/audit/events`

## Python 구조

- `backend/models.py`: 객체 타입, 객체 인스턴스, 관계, 액션, 워크플로우 이벤트 모델
- `backend/ontology.py`: 온톨로지 레지스트리와 객체/관계 컨텍스트 조회
- `backend/search.py`: 외부 라이브러리 없는 BM25 검색기
- `backend/rag.py`: 객체 식별, 검색 질의 강화, RAG 프롬프트, 규칙 기반 LLM Gateway
- `backend/policy.py`: 객체/속성/문서/액션 권한과 마스킹
- `backend/workflow.py`: 상태 전이, 액션 실행, 실행 이력
- `backend/audit.py`: 감사 로그
- `backend/app_context.py`: 서비스 조립과 `/api/ask` 처리 흐름
- `server.py`: 표준 라이브러리 HTTP API 서버와 정적 화면 서빙
- `cli_demo.py`: 문서의 질문 처리 흐름을 콘솔에서 실행
- `evaluate.py`: RAG/온톨로지 운영 평가 질문 세트
- `run_tests.py`: 서비스/API 자동 테스트 실행기
- `tests/`: `unittest` 기반 자동 테스트

## 화면 기능

- AI 질의: 객체 식별, 관계 검증, BM25 검색, 프롬프트, 답변, 액션 표시
- 워크플로우: 승인 큐와 상태 전이 실행
- 객체/관계: 주문, 고객, 제품 컨텍스트 조회
- 감사 로그: 객체 조회, 문서 검색, 질의, 액션 이벤트 확인
- 서비스 경계: 운영형 아키텍처 구성요소 확인

## 자동 테스트

```bash
cd src_codex
python run_tests.py
```

테스트 범위:

- `/api/me`, `/api/ask`, `/api/workflow/execute` API 응답
- 객체 없음, 관계 불일치 오류 처리
- 문서 권한 필터링
- 고객 민감 속성 마스킹
- 워크플로우 상태 전이와 감사 로그
- 고위험 고객 주문의 승인 액션 차단
