# AI 에이전트 표준 아키텍처 설계 - 실전 가이드 (v1.0)

## 1. 개요 및 출처 (Overview & Sources)
본 문서는 `가이드 자료 배포 - 20240401`에 포함된 **WC_DB설계서** 및 **WC_인터페이스명세서**를 기반으로, 실제 상용 수준의 RAG(Retrieval-Augmented Generation) 시스템을 구축하기 위한 실전 설계 지침을 정의합니다. 기존의 정형 데이터 중심 설계를 AI 기반 비정형 데이터 처리 아키텍처로 확장하였습니다.

*   **참조 자료**: 
    *   가이드 자료 배포 - 20240401 (WC_DB설계서_v1.0, WC_인터페이스명세서_v1.0)
    *   ragChatbot_설치_가이드_v0.2 (20240401)

## 2. 실전 데이터베이스 설계 (Practical DB Design)
벡터 DB와 RDBMS를 상호 보완적으로 활용하여 데이터의 무결성과 검색 성능을 동시에 확보합니다.

### 2.1 주요 테이블 구조
*   **TB_DOC_MASTER (문서 마스터)**: 업로드된 원천 문서의 메타 정보 관리
    *   `DOC_ID` (PK), `FILE_NAME`, `FILE_PATH`, `FILE_TYPE`, `TENANT_ID`, `REG_DT`
*   **TB_DOC_CHUNK (문서 청크)**: 임베딩 단위로 분할된 텍스트 및 벡터 매핑 정보
    *   `CHUNK_ID` (PK), `DOC_ID` (FK), `CONTENT`, `PAGE_NO`, `VECTOR_ID` (벡터 DB 식별자)
*   **TB_EMB_MODEL (임베딩 모델 관리)**: 사용된 모델 정보 및 버전 관리
    *   `MODEL_ID` (PK), `MODEL_NAME`, `DIMENSION`, `PROVIDER` (OpenAI, Local 등)

### 2.2 관계 설계 (Relationship)
*   **1:N 관계**: 하나의 문서는 여러 개의 청크로 분할됨.
*   **역방향 추적**: 벡터 DB의 검색 결과(`VECTOR_ID`)를 통해 `TB_DOC_CHUNK`와 `TB_DOC_MASTER`를 즉시 조인하여 근거 문서를 식별함.

## 3. 핵심 인터페이스 명세 (Interface Specification)
에이전트 서비스와 외부 시스템 간의 표준 통신 규격을 정의합니다.

### 3.1 문서 인덱싱 API (`POST /api/v1/ingest`)
*   **Request**: `file` (Multipart), `metadata` (JSON)
*   **Process**: 텍스트 추출 → 청킹 → 임베딩 → 벡터 DB 저장 → RDBMS 메타데이터 기록
*   **Response**: `task_id`, `status`

### 3.2 하이브리드 질의 API (`POST /api/v1/query/hybrid`)
*   **Request**: `question` (String), `top_k` (Int), `filters` (JSON)
*   **Process**: 질문 분석 → 벡터 검색 + 키워드 검색(BM25) → 결과 합성(Reciprocal Rank Fusion) → LLM 답변 생성
*   **Response**: `answer`, `sources` (근거 문서 리스트), `confidence_score`

## 4. 실전 RAG 파이프라인 전략 (Advanced RAG Pipeline)
검색 정확도 향상을 위한 고도화된 기술적 접근 방식입니다.

*   **하이브리드 검색 (Hybrid Search)**: 의미 기반 벡터 검색의 한계를 보완하기 위해 고유 명사나 특정 키워드에 강한 어휘 검색을 결합합니다.
*   **리랭킹 (Reranking)**: 초기 검색된 10~20개의 후보군을 Cross-Encoder 모델을 통해 재정렬하여 가장 관련성 높은 컨텍스트를 LLM에 전달합니다.
*   **동적 청킹 (Dynamic Chunking)**: 문서의 구조(제목, 문단 등)를 분석하여 의미적으로 끊어지지 않도록 가변 길이 청킹을 수행합니다.

## 5. 운영 및 모니터링 (UX & Operations)
*   **근거 제시 (Citations)**: 답변 내에 `[1]`, `[2]` 형태의 인덱스를 부여하고, 하단에 해당 원문 스니펫과 페이지 번호를 노출하여 신뢰성을 확보합니다.
*   **피드백 루프**: 사용자의 추천/비추천 피드백을 수집하여 향후 리랭킹 모델 학습 또는 프롬프트 개선에 활용합니다.
