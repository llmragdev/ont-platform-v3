# RAG 표준 통합 문서와 Claude 하이브리드 질의 Spec 비교 보고서

## 1. 검토 개요
본 보고서는 `AI_Agent_Standard_Architecture_Combined.md`와 Claude 계열 문서에 기술된 RAG 및 하이브리드 질의 스펙을 비교한 결과입니다.

### 1.1 비교 대상
* `X_rag_std/std-combination/AI_Agent_Standard_Architecture_Combined.md`
* `claud_v1_legacy/docs/hybrid_query_requirements.md`
* `claud_v1_legacy/docs/hybrid_query_design.md`
* `claud_v1_legacy/docs/hybrid_query_analysis_report.md`

### 1.2 비교 관점
* RAG 파이프라인 구조
* 하이브리드 검색 방식
* API 및 응답 모델
* 데이터 저장 모델
* 온톨로지 결합 여부
* 운영, 평가, 확장성

## 2. 총평
두 문서는 경쟁 관계라기보다 서로 다른 레이어의 설계입니다.

* `AI_Agent_Standard_Architecture_Combined.md`는 엔터프라이즈 RAG 시스템의 표준 아키텍처, API, DB, 운영 기준을 정의한 문서입니다.
* Claude 문서는 순수 벡터 RAG가 취약한 필터링, 비교, 계산, 관계 질의를 온톨로지로 보완하는 제품형 하이브리드 질의 설계에 가깝습니다.

따라서 통합 문서를 상위 표준으로 유지하고, Claude 문서의 온톨로지 기반 하이브리드 질의 스펙을 확장 장으로 흡수하는 방향이 가장 적절합니다.

## 3. 핵심 차이 요약
| 항목 | 통합 문서 | Claude 문서 |
| :--- | :--- | :--- |
| 중심 목표 | 표준 RAG 아키텍처, API, DB, 운영 기준 | 온톨로지 + 벡터 RAG 결합형 질의 |
| 검색 방식 | Vector + BM25 + RRF + Reranking | 질문 유형 분류 후 Vector/Ontology/Hybrid 라우팅 |
| 주요 API | `/api/v1/query/hybrid`, `/api/v1/ingest/upload` | `/api/hybrid/ask`, `/api/documents/extract-ontology`, `/api/ontology/*` |
| 근거 구조 | `source_documents` 중심 | `vector_evidence`, `ontology_nodes` 분리 |
| 데이터 저장 | RDBMS 테이블 + Vector DB 매핑 | JSON 기반 `ontology_db/{doc_id}_ontology.json` |
| 구조형 질의 | 제한적 | filter, compare, calculate, category 지원 |
| 운영 기준 | 피드백, 평가 지표, 모니터링 포함 | 제품 기능 중심, 운영 표준은 약함 |
| 테넌트 격리 | `TENANT_ID` 기반 명시 | 문서 기준 설계에는 약함 |

## 4. 통합 문서의 강점

### 4.1 표준 API와 응답 모델
통합 문서는 `/api/v1`를 기본 경로로 정의하고, 질의 응답의 근거 문서 필드를 `source_documents`로 통일합니다. 이는 구현자와 클라이언트가 일관된 계약을 유지하기에 유리합니다.

### 4.2 RDBMS 기반 추적성
`TB_DOC_MASTER`, `TB_DOC_CHUNK`, `TB_EMB_MODEL`, `TB_VECTOR_MAPPING`을 통해 문서, 청크, 임베딩 모델, 벡터 저장소 매핑을 추적할 수 있습니다. Vector DB 검색 결과를 RDBMS 메타데이터와 연결하는 표준 구조가 명확합니다.

### 4.3 운영 및 품질 관리
피드백 루프, `TB_QA_FEEDBACK`, Faithfulness, Answer Relevance, Context Precision, Citation Coverage, latency 지표 등이 포함되어 운영 환경에 적합합니다.

### 4.4 테넌트 격리 기준
모든 조회와 검색에 `TENANT_ID`를 기본 필터로 사용하는 정책이 명시되어 있어 멀티테넌트 환경에서 안정적입니다.

## 5. Claude 문서의 강점

### 5.1 RAG 한계 인식이 명확함
Claude 문서는 벡터 RAG가 서술형 설명에는 강하지만, 필터링, 비교, 수치 계산, 다중 조건 교차 질의에는 취약하다는 점을 명확히 구분합니다.

### 5.2 질문 유형 분류 기반 라우팅
질문을 `descriptive`, `filter`, `compare`, `calculate`, `hybrid`로 분류하고, 유형에 따라 벡터 검색, 온톨로지 질의, 병합 검색으로 라우팅합니다. 이는 실제 업무 질의 처리에 유용합니다.

### 5.3 온톨로지 추출 및 관리 UI
PDF 업로드 후 LLM 기반으로 엔티티와 관계를 추출하고, 사용자가 스키마, 인스턴스, 관계 그래프를 수정할 수 있는 UI 설계를 포함합니다. Human-in-the-loop 보정 흐름이 있는 점이 강점입니다.

### 5.4 구조형 결과 지원
필터, 비교, 계산 결과를 표나 목록으로 반환하는 구조형 응답을 고려합니다. 이는 단순 RAG 답변보다 업무 분석형 질의에 적합합니다.

### 5.5 고도화 제안
대용량 문서 처리를 위한 Map-Reduce 추출, Text-to-GraphQuery, Virtual Merged Graph, Context-Aware Synthesis 같은 확장 아이디어가 포함되어 있습니다.

## 6. 주요 불일치 및 리스크

### 6.1 API 경로 체계 불일치
통합 문서는 `/api/v1/query/hybrid`를 표준으로 사용하지만, Claude 문서는 `/api/hybrid/ask`를 사용합니다.

권장 기준:
```text
POST /api/v1/query/hybrid
POST /api/v1/ontology/extract
GET  /api/v1/ontology/{doc_id}/graph
POST /api/v1/ontology/schema/entity-types
POST /api/v1/ontology/schema/relation-types
```

### 6.2 근거 응답 모델 불일치
통합 문서는 `source_documents`를 사용하고, Claude 문서는 `vector_evidence`, `ontology_nodes`를 사용합니다.

권장 응답:
```json
{
  "query_id": "query_456",
  "query_type": "hybrid",
  "answer": "답변 본문 [1]",
  "structured_data": {
    "headers": [],
    "rows": []
  },
  "source_documents": [],
  "ontology_evidence": [],
  "confidence_score": 0.89
}
```

### 6.3 저장 모델 차이
통합 문서는 RDBMS 중심이고, Claude 문서는 JSON 파일 기반입니다. 운영 표준 관점에서는 JSON 파일은 MVP에는 적합하지만, 권한, 검색, 감사, 마이그레이션 측면에서는 RDBMS 스키마로 승격 가능한 모델이 필요합니다.

### 6.4 온톨로지 품질 관리 리스크
Claude 문서의 온톨로지 추출은 LLM 기반이므로 누락, 중복, 잘못된 관계 생성 가능성이 있습니다. 따라서 추출 결과 검증, 중복 병합, 사용자 승인, 변경 이력 관리가 필요합니다.

### 6.5 대용량 문서 처리 리스크
Claude 분석 보고서에서 지적한 것처럼 전체 텍스트를 제한된 길이로 잘라 추출하면 대용량 문서에서 정보 누락이 발생할 수 있습니다. 청크별 추출 후 병합하는 Map-Reduce 방식이 필요합니다.

## 7. 통합 권장안

### 7.1 통합 문서는 상위 표준으로 유지
현재 통합 문서의 DB, API, 운영, 평가 기준은 유지합니다. 이 문서는 구현 표준과 운영 기준의 기준점 역할을 해야 합니다.

### 7.2 Claude 스펙은 확장 장으로 흡수
통합 문서에 아래 장을 추가하는 것을 권장합니다.

```markdown
## 8. 온톨로지 기반 하이브리드 질의 확장
### 8.1 질문 유형 분류
### 8.2 온톨로지 추출 파이프라인
### 8.3 온톨로지 저장 모델
### 8.4 Query Planner
### 8.5 Hybrid Answer 응답 모델
### 8.6 벡터 근거와 온톨로지 근거 통합
### 8.7 온톨로지 관리 UI
```

### 7.3 표준 질의 응답 모델 확장
기존 `QaResponse`를 유지하되, 하이브리드 질의용 확장 필드를 추가합니다.

```python
class StructuredData(BaseModel):
    headers: list[str] = []
    rows: list[list[str]] = []


class OntologyEvidence(BaseModel):
    evidence_no: int
    node_id: str
    node_type: str
    label: str
    path: list[str] = []
    confidence: float | None = None


class HybridQaResponse(QaResponse):
    query_type: str
    structured_data: StructuredData | None = None
    ontology_evidence: list[OntologyEvidence] = []
    trace: list[str] = []
```

### 7.4 온톨로지 저장 모델 추가
RDBMS 표준에 아래 테이블 또는 파일 대응 모델을 추가하는 것을 권장합니다.

| 논리 모델 | 설명 |
| :--- | :--- |
| `TB_ONT_ENTITY` | 문서에서 추출된 엔티티 |
| `TB_ONT_RELATION` | 엔티티 간 관계 |
| `TB_ONT_SCHEMA` | 엔티티/관계 유형 정의 |
| `TB_ONT_EXTRACT_TASK` | 온톨로지 추출 작업 상태 |

MVP에서는 JSON 파일로 시작하되, 표준 문서에는 RDBMS 승격 가능한 논리 모델을 함께 제시하는 편이 좋습니다.

### 7.5 질의 라우팅 정책 추가
질의 유형별 기본 라우팅은 다음과 같이 정의할 수 있습니다.

| Query Type | 기본 처리 경로 | 설명 |
| :--- | :--- | :--- |
| `descriptive` | Vector + BM25 + Rerank | 설명형 문서 질의 |
| `filter` | Ontology | 조건 필터링 |
| `compare` | Ontology + optional RAG | 엔티티 비교 |
| `calculate` | Ontology | 수치 계산, 집계 |
| `hybrid` | Ontology + RAG | 구조형 결과와 문서 근거 결합 |

## 8. 우선순위별 반영 과제

### 8.1 1순위
* 통합 문서에 질문 유형 분류와 라우팅 정책 추가
* `HybridQaResponse` 확장 응답 모델 추가
* `ontology_evidence` 필드 표준화
* API 경로를 `/api/v1` 기준으로 통일

### 8.2 2순위
* 온톨로지 추출 API 추가
* 온톨로지 엔티티/관계 논리 모델 추가
* 구조형 결과 `structured_data` 표준 추가
* 온톨로지 근거와 문서 근거의 우선순위 정책 정의

### 8.3 3순위
* Map-Reduce 기반 대용량 문서 추출 전략 추가
* Text-to-GraphQuery 또는 Query Plan 검증 계층 추가
* 온톨로지 관리 UI 표준 추가
* Virtual Merged Graph 기반 다중 문서 비교 전략 추가

## 9. 결론
통합 문서는 표준 RAG 시스템의 골격으로 적합하고, Claude 문서는 온톨로지 기반 하이브리드 질의를 제품 기능으로 확장하는 데 강점이 있습니다.

최종 방향은 다음과 같습니다.

```text
통합 문서 = 표준 RAG 운영/구현 기준
Claude 스펙 = 온톨로지 하이브리드 질의 확장 모듈
```

따라서 현재 통합 문서에 Claude 스펙을 그대로 병합하기보다는, API 경로와 응답 모델을 통합 문서 기준으로 정규화한 뒤 `온톨로지 기반 하이브리드 질의 확장` 장으로 흡수하는 것이 바람직합니다.
