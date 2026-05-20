# AI 에이전트 RAG 파이프라인 고도화 설계서 (v1.0)

## 1. 개요
본 문서는 단순 검색을 넘어 엔터프라이즈 환경에서 요구되는 고정밀 답변 생성을 위한 RAG(Retrieval-Augmented Generation) 파이프라인의 고급 전략을 정의합니다.

## 2. 인제스션(Ingestion) 전략

### 2.1 동적 청킹 (Dynamic Chunking)
문서의 의미적 단위를 유지하기 위해 고정 길이 대신 구조 기반 청킹을 적용합니다.
*   **Strategy**: `RecursiveCharacterTextSplitter` 활용
*   **Separators**: `["\n\n", "\n", ".", " ", ""]` 순서로 계층적 분할
*   **Chunk Size**: 500 ~ 800 Tokens (모델의 Context Window 고려)
*   **Overlap**: 10~15% (문맥 연속성 유지)

### 2.2 임베딩 모델 최적화
*   **Model Selection**: 다국어 지원 및 한국어 특화 모델(예: KoSimCSE, BGE-M3) 우선 고려
*   **Dimension**: 768 또는 1024 차원 (성능과 저장 공간의 트레이드오프)

## 3. 검색(Retrieval) 전략

### 3.1 하이브리드 검색 (Hybrid Search)
의미 기반(Vector) 검색과 키워드 기반(BM25) 검색을 결합하여 고유 명사 및 전문 용어 검색의 정확도를 보완합니다.
*   **Algorithm**: `Reciprocal Rank Fusion (RRF)`
*   **Weighting**: 
    *   `Score = (Vector_Rank + k)^-1 + (BM25_Rank + k)^-1` (k=60)
*   **장점**: 서로 다른 스케일의 점수를 순위 기반으로 안전하게 통합 가능

### 3.2 리랭킹 (Reranking)
1차 검색된 후보군($N=20$)에 대해 정밀 모델을 사용하여 순위를 재정렬합니다.
*   **Model**: Cross-Encoder 계열 (예: BGE-Reranker)
*   **Process**: (Query, Chunk) 쌍을 입력으로 하여 0~1 사이의 유사도 점수 산출
*   **효과**: 검색 노이즈 제거 및 LLM에 가장 적합한 컨텍스트 제공

## 4. 답변 생성(Generation) 전략

### 4.1 프롬프트 엔지니어링 (System Prompt)
*   **Persona**: "당신은 신뢰할 수 있는 엔터프라이즈 지식 전문가입니다."
*   **Constraint**: 
    1. 제시된 컨텍스트에 근거가 없는 경우 "모릅니다"라고 답변할 것.
    2. 답변 끝에 반드시 근거 문서의 `[ID]`를 명시할 것.
    3. 한국어로 답변하되 전문 용어는 병기할 것.

### 4.2 인용 및 근거 제시 (Citations)
*   **Format**: `[문서명, p.XX]` 형태의 인용구 자동 삽입
*   **UI 연동**: 답변 내 인용구 클릭 시 해당 청크의 원문을 하이라이트 표시

## 5. 성능 평가 지표 (Evaluation)
*   **Faithfulness**: 답변이 실제 컨텍스트에 기반하고 있는가?
*   **Answer Relevance**: 질문에 대한 직접적인 해답인가?
*   **Context Precision**: 검색된 결과 중 실제 유용한 정보의 비율은?
