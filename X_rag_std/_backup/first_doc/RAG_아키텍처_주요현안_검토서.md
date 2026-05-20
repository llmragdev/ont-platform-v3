# RAG 아키텍처 주요 현안 및 검토서

본 문서는 RAG 표준 설계 시 당면한 핵심 현안에 대한 분석 및 해결 방향을 정리한 참고 자료입니다.
* **기준 참조 자료**: `HNIX AI 백엔드 아키텍처 설계서- v1.0.docx` (`E:\ontology_edu\X_rag_std\first_doc\원본목록액셀\` 내 위치)
* **비교 대상 코드**: 부트캠프 코드 (`pre-work\std_boot_src_2026\ai_std_dev_llmragdev`) 및 클로드 코드 기반 RAG (`ont_platform`)

---

## 1. LLM과 VectorDB의 물리적 분리 구조 검토
### [이슈 개요]
일반적으로 LangChain과 같은 RAG 프레임워크를 사용하면, LLM 모델 체인과 Vector DB 검색(Retriever) 객체가 강하게 결합(Tightly Coupled)되는 경향이 있습니다. 엔터프라이즈 환경에서는 보안, 망 분리, 혹은 인프라 구성(GPU 서버 vs DB 서버)의 이유로 LLM 환경과 VectorDB 환경이 물리적으로 분리되어야 하는 경우가 많습니다. 기존 부트캠프 코드나 클로드 기반 RAG 코드가 이러한 분리 환경을 유연하게 지원하는지 검토해야 합니다.

### [설계 및 해결 방향 (기초 설계 반영)]
* **느슨한 결합(Loosely Coupled) 구조 도입**: LangChain 내장 컴포넌트를 그대로 쓰기보다는, VectorDB 조회 부분을 독립적인 API(Microservice)로 추상화합니다.
* **Remote Retriever 패턴**: LLM 파이프라인에서는 VectorDB에 직접 DB 커넥션을 맺는 대신, 내부 REST/gRPC API를 호출하여 Context만 전달받는 '원격 검색기' 구조를 채택합니다.
* **검토 포인트**: 기존 코드(`ai_std_dev_llmragdev`, 클로드 RAG)가 DB 의존성을 어떻게 주입하고 있는지 분석하고, 인터페이스 기반으로 리팩토링할 수 있는 구조를 표준 아키텍처에 반영합니다.

---

## 2. 파이썬 코딩 표준 (PEP 8 - Snake Case) 적용
### [이슈 개요]
이전 부트캠프 소스 코드에서는 자바/자바스크립트 등에서 흔히 쓰이는 카멜 표기법(CamelCase)을 사용하여 코드를 작성했습니다. 하지만, 파이썬 생태계의 표준 개발자들은 PEP 8 규약에 따라 스네이크 표기법(snake_case)을 사용하는 것에 익숙합니다. 범용성과 유지보수성을 위해 파이썬 표준을 준수해야 합니다.

### [설계 및 해결 방향 (기초 설계 반영)]
* **표준 명명 규칙(Naming Convention) 확립**:
  * **함수명 / 변수명**: `snake_case` (예: `searchVectorDb()` -> `search_vector_db()`)
  * **클래스명**: `PascalCase` (예: `DocumentManager`, `VectorDbClient`)
  * **상수명**: `UPPER_SNAKE_CASE` (예: `MAX_CHUNK_SIZE`)
* 이번 RAG 표준화 설계 및 향후 진행될 개발(다음 주 예정)부터는 위 파이썬 코드 표준을 전면적으로 채택하여 설계 명세 및 코드를 작성합니다.
