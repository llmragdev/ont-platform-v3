# AI Agent 표준 아키텍처 및 RAG 표준 설계 프로젝트

## 프로젝트 개요
본 프로젝트는 AI Agent 표준 아키텍처를 기반으로 엔터프라이즈 환경에 적합한 RAG(Retrieval-Augmented Generation) 표준 설계 및 예시를 개발하는 것을 목표로 합니다.
현재는 **설계 단계**에 있으며, 체계적인 문서화 및 표준화를 통해 향후 개발 및 확장성을 보장합니다.

## 일정 계획
* **이번 주**: 기초 설계 (Basic Design) - 구조, 파이프라인 뼈대 및 표준화 기준 정의
* **다음 주**: 상세 설계 및 개발 진행 (Detailed Design & Development) - 프로토타입 개발 및 상세 로직 구현

## 디렉토리 구조 및 참조 자료
본 프로젝트는 다음의 구조로 관리됩니다. 과거의 자료들은 혼동을 피하기 위해 `_backup` 폴더로 분리되었습니다.

* **`RAG_표준_설계_v1.0.md`**: 엑셀 핵심 목록과 현안을 모두 통합한 **RAG 기본설계서**
* **`details/`**: 다음 주 개발과 연계될 분야별 **상세 설계서** 모음 (파이프라인, DB 라우팅, 검색 API, 레거시 기반 RDBMS 스키마 등)
* **`src_agents/`**: 각 AI 에이전트들의 코드 초안 작업 공간
  * **`src_codex/`**: Codex 전용 RAG 백엔드 작업 공간
  * **`src_antigravity/`**: Antigravity 전용 RAG 백엔드 작업 공간
* **`src_final/`**: 클로드 코드(Claude Code)를 통해 최종 통합 및 정리될 제출용(Clean) 소스코드 폴더
* **`_backup/`**: 2024~2026년 진행된 선행 연구(`pre-work`), 기존 표준화 작업물(`std-work`), 기초 설계 예시(`first_doc`) 등 과거 이력 보존용 폴더
* **기타 참고 사항**: `E:\ontology_edu\ont_platform\docs` (클로드 코드 기반의 RAG 참고 자료)

## 주요 설계 항목 (핵심 목록)
기초가 되는 원본 목록은 다음 링크 및 로컬 경로에서 확인할 수 있습니다.
* **원본 링크**: [Excel 링크](https://hninc365-my.sharepoint.com/:x:/g/personal/js_chae1187_hnix_co_kr/IQD6xgACyNr8Rbm-7SV3kHxjAW6Nakmw2fw7NoMOOTtpewY?e=G5cex6)
* **로컬 파일 경로**: `E:\ontology_edu\X_rag_std\first_doc\원본목록액셀`
* **아키텍처 기준 문서**: `E:\ontology_edu\X_rag_std\first_doc\원본목록액셀\HNIX AI 백엔드 아키텍처 설계서- v1.0.docx` (부트캠프 기반 코드 `pre-work\std_boot_src_2026\ai_std_dev_llmragdev`의 근간)

핵심 설계 목록은 다음과 같습니다:
1. 임베딩 대상 문서 관리
2. 벡터 DB 관리
3. 벡터DB의 임베딩별 문서 매칭관리
4. 메타데이터 관리
5. 접근 권한 관리 (보류)
6. 오류/예외 결과
7. Agent/Orchestration 요청 (보류)

## 주요 현안 및 고려사항 (진행 중)
현재 다음 2가지의 핵심 현안을 최우선으로 검토하여 **기초 설계**에 반영합니다. (자세한 내용은 [RAG_아키텍처_주요현안_검토서.md](./first_doc/RAG_아키텍처_주요현안_검토서.md) 참고)
1. **LLM과 Vector DB의 물리적 분리**: LangChain 등에서 발생하는 강한 결합(Tightly Coupled)을 해소하고, 물리적으로 인프라가 분리된 환경에서도 연동 가능한 유연한 추상화/API 분리 구조 설계 (기존 부트캠프 코드 및 클로드 RAG와 비교 분석)
2. **파이썬 코딩 표준(PEP 8) 도입**: 기존 부트캠프 코드의 카멜 표기법(CamelCase)에서 벗어나, 파이썬 표준 개발 환경에 맞춘 스네이크 표기법(snake_case) 전면 적용

## 다음 단계 (Next Steps)
README가 작성됨에 따라 다음 단계 진행을 위한 상의가 필요합니다.
1. `first_doc`에 정의된 기초 설계의 고도화 및 확정 (위 현안 2가지 내용 반영)
2. 선행 연구(pre-work)와 참조 폴더(ont_platform) 내용을 분석하여 설계안에 병합
3. 다음 주 상세 설계를 위한 컴포넌트별 명세서 작성 방향 논의
