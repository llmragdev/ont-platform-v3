# PHASE8 Master Technical Report

작성일: 2026-06-07  
대상: `ont_platform v5`  
목적: PHASE8의 최종 기술 설계 사상과 v5 개발 방향을 정리한다.

## 1. Master Principle

PHASE8의 핵심 설계 사상은 하나다.

```text
평가가 요구하는 정답 정책과 실제 시스템이 따르는 답변 정책을 분리하지 않는다.
```

v4의 문제는 단순한 검색 성능 문제가 아니었다. 시스템은 관련 없는 질문에도 검색 후보를 LLM에 넘겼고, LLM은 일반론을 생성했다.

v5는 이 문제를 구조적으로 막아야 한다.

```text
근거 없는 답변을 잘 만드는 시스템보다,
근거 없음을 정확히 아는 시스템이 더 정확하다.
```

## 2. v5 개발 원칙

### 2.1 v4 baseline 보존

v4는 수정하지 않는다.

```text
ont_platform/v4 = baseline
ont_platform/v5 = PHASE8 개선 버전
```

v4를 보존해야 전후 비교가 가능하다.

### 2.2 API 분리

v5 API는 v4와 분리한다.

권장 엔드포인트:

```text
POST /api/v5/hybrid/ask
```

이유:

```text
v4/v5 동시 테스트 가능
baseline 회귀 방지
로그와 메트릭 분리
```

### 2.3 정책 우선순위

v5의 답변 정책 우선순위:

```text
1. explicit answer policy
2. category mismatch
3. no direct evidence
4. search_mode-specific evidence rule
5. grounded synthesizer
```

중요:

```text
search_mode를 수동 지정해도 EvidenceGate는 우회할 수 없다.
```

## 3. v5 High-Level Architecture

```text
POST /api/v5/hybrid/ask
  ↓
AskRequestV5
  ├─ question
  ├─ search_mode
  ├─ doc_ids
  └─ override
  ↓
Question Analyzer
  ├─ intent
  ├─ question_category
  ├─ expected_evidence_type
  └─ no_answer_candidate
  ↓
Option-Based Multi Router
  ├─ auto
  ├─ ontology_only
  ├─ vector_only
  └─ hybrid
  ↓
Retrieval
  ├─ ontology retrieval
  ├─ vector retrieval
  └─ metadata/category retrieval
  ↓
EvidenceGate
  ├─ explicit policy check
  ├─ category mismatch check
  ├─ relevance threshold check
  └─ evidence coverage check
  ↓
Answer Policy Decision
  ├─ no-answer response
  └─ grounded synthesis
  ↓
Grounding Verifier
  ↓
Final Answer
```

## 4. AskRequestV5 and SearchMode

SearchMode:

```python
class SearchMode(str, Enum):
    AUTO = "auto"
    ONTOLOGY_ONLY = "ontology_only"
    VECTOR_ONLY = "vector_only"
    HYBRID = "hybrid"
```

AskRequestV5:

```python
class AskRequestV5(BaseModel):
    question: str
    search_mode: SearchMode = SearchMode.AUTO
    doc_ids: list[str] | None = None
    override: dict[str, Any] | None = None
```

모드별 의미:

| Mode | 실행 |
|---|---|
| `auto` | Question Analyzer와 intent classifier 기반 자동 라우팅 |
| `ontology_only` | 온톨로지/지식그래프 경로만 실행 |
| `vector_only` | vector search 경로만 실행 |
| `hybrid` | ontology + vector 모두 실행 |

수동 모드 규칙:

```text
사용자가 ontology_only/vector_only/hybrid를 명시하면 intent 기반 라우팅 결정은 생략한다.
하지만 category analysis와 EvidenceGate는 항상 수행한다.
```

## 5. Question Analyzer

역할:

```text
질문 카테고리 판정
질문 intent 보강
필요 근거 유형 판정
no-answer 후보 판정
```

점진적 진화:

```text
Stage A: regex/rule 기반
Stage B: ontology schema mapping
Stage C: lightweight LLM classifier
```

초기 규칙 예:

```text
Snowflake, ranking_issue, warehouse, table, SQL → Snowflake
온톨로지, 지식그래프, 클래스, 속성, 인스턴스 → Ontology
RAG, BM25, chunk, rerank → Advanced RAG
```

## 6. EvidenceGate

### 6.1 역할

EvidenceGate는 LLM 호출 전에 답변 가능 여부를 판정한다.

v4:

```text
검색 결과 있음 → LLM 호출 → 일반론 생성 가능
```

v5:

```text
검색 결과 있음 → EvidenceGate 검증 → 직접 근거 없으면 LLM 호출 금지
```

### 6.2 출력 예

```json
{
  "answer_allowed": false,
  "reason": "category_mismatch",
  "policy": "category_irrelevant",
  "message": "질문은 해당 카테고리 문서와 관련이 없습니다.",
  "confidence": 0.95
}
```

### 6.3 공통 no-answer 문구

카테고리 무관:

```text
질문은 해당 카테고리 문서와 관련이 없습니다.
```

일반 근거 부족:

```text
제공된 문서에서 질문에 대한 직접적인 근거를 찾지 못했습니다.
```

### 6.4 SearchMode별 EvidenceGate

| Mode | Gate 기준 |
|---|---|
| `ontology_only` | 온톨로지 결과가 없으면 no_evidence |
| `vector_only` | vector relevance threshold 기준 |
| `hybrid` | ontology 또는 vector 중 직접 근거가 있으면 통과 |
| `auto` | analyzer 결과와 검색 근거를 보수적으로 종합 |

공통:

```text
명시적 answer policy 또는 category mismatch는 모든 모드보다 우선한다.
```

## 7. Answer Policy and Feedback Loop

정답 보정은 시스템 개선 신호다.

파일 후보:

```text
validation/ont_platform_v4_eval/data/answer_key_feedback.jsonl
ont_platform/v5/config/answer_policies.jsonl
```

정책 예:

```json
{
  "question_id": "STD-S-06",
  "question_pattern": "ranking_issue|Snowflake RAG",
  "category": "Snowflake",
  "policy": "category_irrelevant",
  "condition": "no direct evidence in category documents",
  "target_response": "질문은 해당 카테고리 문서와 관련이 없습니다.",
  "applies_to": ["evaluation", "evidence_gate", "regression_test"]
}
```

Feedback type:

| Type | Meaning | Target |
|---|---|---|
| Policy Gap | 답하면 안 되는 질문에 답함 | EvidenceGate |
| Knowledge Gap | 개념/정의 누락 | ontology entity |
| Relation Gap | 관계 누락 | ontology relationship |
| Retrieval Gap | 검색 실패 | retriever metadata/synonym |
| Ranking Gap | 순위화 실패 | reranker/RRF |
| Prompt Gap | 답변 형식 오류 | prompt |
| Evaluation Gap | 정답표 오류 | evaluation rubric |

## 8. Hybrid Fusion

v5 hybrid는 ontology 결과와 vector 결과를 단순 concat하지 않는다.

초기 MVP:

```text
각 경로의 상위 근거를 분리 보존
EvidenceGate에서 직접 근거 여부 판정
Synthesizer에는 검증된 근거만 전달
```

후속 개선:

```text
score normalization
weighted score fusion
RRF(Reciprocal Rank Fusion)
category-aware reranking
```

주의:

```text
RRF와 weight calibration은 v5 MVP 필수 구현이 아니라 P1/P2 개선 과제다.
```

## 9. Score Calibration

score calibration은 두 영역으로 나눈다.

### 9.1 Evidence threshold calibration

목적:

```text
no-answer gate의 relevance threshold 결정
```

작업:

```text
known-positive 질문 score 수집
known-negative 질문 score 수집
threshold별 precision/recall 계산
```

### 9.2 Fusion weight calibration

목적:

```text
ontology/vector hybrid ranking 최적화
```

작업:

```text
ontology confidence 정규화
vector distance/similarity 정규화
RRF weight 후보 평가
category-aware weight 평가
```

## 10. Regression Evaluation

평가 기준은 섞지 않는다.

산출물 후보:

```text
validation/ont_platform_v4_eval/reports/PHASE8_V4_V5_BASELINE_24Q.xlsx
validation/ont_platform_v4_eval/reports/PHASE8_V4_V5_CATEGORY_IRRELEVANT_STDS.xlsx
validation/ont_platform_v4_eval/reports/PHASE8_V5_REGRESSION_SUMMARY.md
```

테스트셋:

| 테스트셋 | 목적 |
|---|---|
| Baseline 24Q | 기존 동일 24문항 비교 |
| STD-S No-Answer | 카테고리 무관 질문 차단 |
| Ontology QA | 기존 온톨로지 성능 유지 |
| Routing Integrity | SearchMode별 라우팅 검증 |
| Grounding QA | 답변과 citation 충돌 확인 |

## 11. Acceptance Criteria

| 기준 | 목표 |
|---|---:|
| STD-S no-answer accuracy | 90% 이상 |
| STD-S hallucination | 1/8 이하 |
| Ontology score | v4 75.62% 이상 유지 |
| no-answer 시 LLM 호출 | 0회 |
| `/api/v5/hybrid/ask` | v4와 분리 동작 |
| `ontology_only` | VECTOR step 0회 |
| `vector_only` | ONTOLOGY step 0회 |
| SearchMode trace | 모든 응답에 기록 |
| v4/v5 comparison report | 생성 완료 |

## 12. Implementation Roadmap

### P0: v5 MVP

```text
v4 → v5 복사
/api/v5/hybrid/ask 추가
SearchMode / AskRequestV5 추가
Question Analyzer rule 기반 구현
EvidenceGate 최소 구현
no-answer 시 LLM 호출 차단
STD-S 회귀 테스트
```

### P1: 평가와 정책 통합

```text
answer_policies.jsonl
answer_key_feedback.jsonl
PHASE8 regression runner
v4/v5 비교 보고서
```

### P2: 검색/랭킹 개선

```text
score calibration
RRF
weighted fusion
category-aware reranking
```

### P3: 온톨로지 강화

```text
ontology-first routing
graph relation traversal
schema-aware query expansion
synonym/alias relation 활용
```

## 13. Final Technical Position

PHASE8/v5는 단순한 RAG 업그레이드가 아니다.

PHASE8/v5는 다음을 하나의 정책 체계로 통합한다.

```text
정답 기준
서빙 정책
검색 라우팅
온톨로지 근거
문서 근거
no-answer 판단
회귀 평가
```

최종 판단:

```text
v4는 baseline으로 보존한다.
v5는 EvidenceGate와 SearchMode를 중심으로 새로 개발한다.
평가 정답 정책과 실제 시스템 정책은 같은 answer policy를 공유한다.
```
