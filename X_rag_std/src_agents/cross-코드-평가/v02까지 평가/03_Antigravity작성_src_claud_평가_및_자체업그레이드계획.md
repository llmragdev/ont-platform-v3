# `src_claud/v2` 소스 평가 및 `src_antigravity/v2` 개선 계획

## 1. `src_claud/v2` 소스코드 평가

`src_claud/v2`는 프로덕션 환경에 적합한 수준의 우수한 아키텍처를 보여줍니다. 주요 장점은 다음과 같습니다.

* **동기/비동기 블로킹 제어**: FastAPI의 라우터는 `async def`로 선언되는데, 내부적으로 동기(Synchronous) 작업(예: HTTPx 동기 호출, SQLAlchemy 등)이 실행될 때 `asyncio.to_thread()`를 활용하여 이벤트 루프(Event Loop)가 블로킹되는 현상을 방지했습니다. 이는 동시 접속 처리에 매우 중요합니다.
* **디자인 패턴(Factory & DI)의 적극 활용**: `providers.py`를 통해 임베딩(Embedding), LLM, 청커(Chunker) 등의 구현체를 동적으로 주입합니다. 이를 통해 실제 환경(`gemini_http`, `claude`)과 로컬 환경(`mock`)의 전환을 유연하게 처리합니다.
* **추상화된 스토리지 라우팅**: VectorDB를 `ChromaDB`와 `Local JSON` 중 환경 변수(`VECTOR_DB_ENGINE`)에 따라 선택 가능하게 구성하여, 인프라 종속성을 분리해 냈습니다.
* **풍부한 API 모듈 분리**: Project, Category, Document, Search 등 명확한 도메인별 라우터 분리와 서비스 계층 분리가 돋보입니다.

---

## 2. `src_antigravity/v2` 개선(업그레이드) 계획

앞선 평가를 바탕으로, 현재 `src_antigravity/v2`에서 아쉽게 구현된 부분들을 보완하는 다음의 업그레이드 계획을 수립합니다.

### A. FastAPI 이벤트 루프 블로킹 해소 (가장 치명적인 문제)
* **문제점**: 현재 `api/documents.py`와 `api/search.py`에서 `async def` 라우터 내부에 동기 코드로 짜인 `pipeline_service.process_upload`와 `search_service.process_search`를 바로 호출하고 있습니다. 이는 FastAPI의 비동기 성능을 저하시킵니다.
* **해결책**: `asyncio.to_thread()`를 사용하여 I/O 바운드 작업(RDBMS 질의, 임베딩 외부 API 호출, 파일 쓰기 등)을 스레드 풀(Thread Pool)로 넘겨서 백그라운드로 처리하고 `await` 하도록 변경합니다.

### B. Gateway Client의 의존성 주입화 및 구조 개선
* **문제점**: 현재 `rag_service.py`와 `vector_db.py`의 메서드 내부에서 `LlmGatewayClient()`를 직접 인스턴스화하여 사용하고 있어, 테스트와 확장에 불리합니다.
* **해결책**: 생성자를 통한 주입 또는 전역 인스턴스를 통해 의존성을 관리합니다.

### C. 설정 중앙화 (Config)
* **문제점**: `LLM_GATEWAY_URL` 등을 여러 파일(`gateway_client.py`)에서 `os.environ.get()`으로 흩어져서 관리하고 있습니다.
* **해결책**: `core/config.py`를 신설하여 설정을 중앙에서 통제합니다.

---

## 3. 개발 수행 내역

위 계획에 따라 다음 작업을 수행합니다.
1. `core/config.py` 생성 및 `gateway_client.py` 반영
2. `api/documents.py` 라우터 비동기 개선 (`asyncio.to_thread`)
3. `api/search.py` 라우터 비동기 개선 (`asyncio.to_thread`)
