# 하이브리드 질의 시스템 가이드 (Hybrid Query Guide)

본 문서는 `Antigravity-통합` 프로젝트에 구현된 온톨로지 기반 하이브리드 질의 시스템의 구조와 사용법을 설명합니다.

## 1. 아키텍처 개요

하이브리드 질의 시스템은 두 가지 데이터 소스를 결합하여 답변의 정확도와 풍부함을 동시에 확보합니다.

1.  **Ontology (Structural):** 스키마 기반의 정형 데이터. 필터링, 관계 추적, 수치 계산에 강점.
2.  **Vector DB (Unstructured):** PDF 등 문서의 텍스트 청크. 서술적 설명 및 세부 지식 검색에 강점.

### 질의 처리 흐름
1.  **유형 분류 (Classification):** 질문이 서술형(Descriptive), 구조형(Structural), 또는 혼합형(Hybrid)인지 LLM이 판별합니다.
2.  **병렬 검색:**
    *   서술형/혼합형인 경우: Chroma DB에서 관련 문서 청크를 검색합니다.
    *   구조형/혼합형인 경우: `OntologyEngine`에서 관련 객체와 관계 컨텍스트를 추출합니다.
3.  **답변 합성 (Synthesis):** 두 소스의 컨텍스트를 LLM에게 전달하여 최종 답변을 생성합니다. 정형 데이터가 비정형 텍스트보다 우선순위를 가집니다.

---

## 2. 주요 구성 요소

### 2-1. `VectorSearchService`
*   **역할:** PDF 업로드, 임베딩 생성, 벡터 검색.
*   **엔드포인트:** 
    *   `POST /api/documents/upload`: PDF 파일을 벡터화하여 저장.
    *   `GET /api/documents`: 업로드된 문서 목록 확인.

### 2-2. `OntologyExtractor`
*   **역할:** 문서 텍스트에서 엔티티와 관계를 자동으로 추출하여 `OntologyEngine`에 등록.
*   **엔드포인트:**
    *   `POST /api/documents/{filename}/extract`: 문서 내용 기반 지식 그래프 자동 구축.

### 2-3. `HybridQueryEngine`
*   **역할:** 질문 분류 및 최종 답변 합성.
*   **엔드포인트:**
    *   `POST /api/hybrid/ask`: 하이브리드 질의 실행.

---

## 3. 사용 방법 (API 예시)

### 3-1. 하이브리드 질의 실행
```bash
curl -X POST "http://localhost:8000/api/hybrid/ask" \
     -H "Content-Type: application/json" \
     -d '{
           "question": "Serverless 과금 방식인 컴퓨팅 계층의 기능들을 알려주고, 현재 등록된 고객 중 관련 있는 사례가 있는지 찾아줘.",
           "doc_ids": ["Snowflake_Guide.pdf"]
         }'
```

### 3-2. 온톨로지 자동 추출
```bash
curl -X POST "http://localhost:8000/api/documents/Snowflake_Guide.pdf/extract"
```

---

## 4. 고도화 포인트 (Next Steps)

*   **Query Planner:** 복잡한 구조형 질문 시 `OntologyEngine`에서 특정 속성값으로 필터링하는 로직을 LLM이 자동으로 생성하도록 개선 예정.
*   **Multi-hop Reasoning:** 관계를 여러 단계 거쳐야 하는 질문(예: "창립자의 이전 직장 동료가 소속된 다른 회사는?")에 대한 추론 능력 강화.
*   **Feedback Loop:** 사용자가 수정하거나 추가한 온톨로지 데이터를 기반으로 추출 프롬프트를 자가 학습하는 기능.
