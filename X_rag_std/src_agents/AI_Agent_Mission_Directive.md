# AI Agent 개발 임무 지시서 (Mission Directive)

## 1. 임무 개요
본 지시서는 이 프로젝트에 투입된 모든 AI Agent (Codex, Antigravity 등)가 공통으로 수행해야 할 RAG 백엔드 개발 미션을 정의합니다. 당신의 목표는 제공된 설계서를 완벽하게 해석하여 동작하는 FastAPI 백엔드 애플리케이션 코드를 작성하는 것입니다.

## 2. 작업 공간 (Workspace)
* 당신은 반드시 `src_agents/{자신의_이름}/` 폴더 내부에서만 작업해야 합니다.
  * 예: `src_agents/src_codex/` 또는 `src_agents/src_antigravity/`
* 작업 폴더 내부에 `requirements.txt`, `main.py` 등을 생성하여 독립적인 애플리케이션을 구축하십시오.

## 3. 필독 설계 문서 (Context)
개발을 시작하기 전에 다음 문서들을 **반드시 읽고(View)** 그 스펙을 100% 준수해야 합니다.
1. **기본 설계**: `E:\ontology_edu\X_rag_std\RAG_표준_설계_v1.0.md`
2. **상세 설계**: `E:\ontology_edu\X_rag_std\details\` 폴더 하위의 4개 파일 전체
   * `01_Document_Embedding_Pipeline.md`
   * `02_VectorDB_Management_Routing.md`
   * `03_RAG_Search_API.md`
   * `04_RDBMS_Schema_Design.md`

## 4. 개발 핵심 규칙 (Core Rules)
1. **코딩 표준 준수**: Python PEP 8을 엄격히 따릅니다. 변수 및 함수는 `snake_case`, 클래스는 `PascalCase`를 적용하십시오. 과거의 카멜 표기법은 절대 사용하지 않습니다.
2. **프레임워크**: FastAPI와 Pydantic을 활용하여 API 인터페이스를 구축하십시오.
3. **물리적 분리 구현 (Remote Retriever)**: LangChain의 내장 검색기에 의존하지 말고, `02번 상세설계`에 정의된 라우터(Router)와 어댑터(Adapter) 패턴을 직접 구현하여 Vector DB 검색과 LLM 호출을 분리하십시오.
4. **디버그 모드 지원**: RAG 검색 API(`POST /api/v1/rag/search`) 구현 시, `debug_mode`가 True일 경우에만 `candidate_chunks` 전체를 반환하도록 로직을 작성하십시오. (`03번 상세설계` 참조)

## 5. 최종 산출물
* **실행 가능한 FastAPI 프로젝트 소스코드 일체** (라우팅 모듈, RDBMS 모델 클래스, API 엔드포인트 포함)
* 개발 완료 후, 당신이 작성한 코드가 어떻게 설계서의 요구사항을 충족했는지 README.md로 요약하여 자신의 폴더 안에 남겨주십시오.
