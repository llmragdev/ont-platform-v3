# PHASE7: 답변 정확도 향상 및 정답 보정 루프 구축 계획

작성일: 2026-06-07  
대상: `ont_platform v4` 질의응답 정확도 개선  
목적: PHASE4 평가에서 확인된 실패를 제품 개선 과제로 전환한다. 특히 관련 없는 질문에 답하지 않는 능력, 문서/온톨로지 근거 기반 답변, 테스트 후 예상 정답 보정 루프를 구현한다.

## 1. PHASE7 핵심 목표

PHASE7의 목표는 단순한 RAG 평균 점수 상승이 아니다. 시스템이 다음 네 가지를 안정적으로 수행하도록 만드는 것이다.

| 목표 | 설명 |
|---|---|
| Evidence-Grounded QA | 문서/온톨로지 근거가 있는 내용만 답변 |
| No-Answer Gate | 관련 없는 질문은 답변하지 않고 정해진 문구로 거절 |
| Ontology-Aware Routing | 온톨로지 관계/개념 질문은 graph/ontology 경로를 우선 사용 |
| Answer-Key Feedback Loop | 테스트 후 예상 정답을 정책, 관계, 검색 조건 개선으로 반영 |

핵심 원칙:

```text
근거 없는 답변을 잘 만드는 시스템보다,
근거 없음을 정확히 아는 시스템이 더 정확하다.
```

## 2. 배경: PHASE4 평가 교훈

동일 24문항 평가에서 `ont_platform v4`는 Ontology 영역에서는 Team1과 거의 동률이었다.

```text
Ontology:
Team1 75.94%
Team4 ont_platform v4 75.62%
```

하지만 STD-S 문항을 “카테고리 무관 질문”으로 재평가했을 때 Team4는 Snowflake 카테고리에서 0점을 받았다.

```text
STD-S 카테고리 무관 추가 평가:
Team4 Snowflake 0.00%
```

원인:

```text
정답: 질문은 해당 카테고리 문서와 관련이 없습니다.
실제 Team4: Snowflake/RAG 일반론을 생성
```

현재 프롬프트에는 “정보가 없으면 관련 데이터를 찾지 못했다고 답하라”는 문구가 있으나, 시스템 레벨에서 강제되지 않는다.

## 3. 구현 범위

PHASE7은 다음 범위를 포함한다.

1. `EvidenceGate` 모듈 추가
2. 카테고리 불일치 판정
3. 관련성 threshold 기반 no-answer 판정
4. no-answer 시 LLM 생성 금지
5. synthesizer 프롬프트 강화
6. 온톨로지 우선 라우팅 개선
7. 테스트 후 정답 보정 데이터 구조 추가
8. 보정 정답을 정책/관계/검색 조건으로 변환하는 초안 구현
9. STD-S 회귀 테스트 추가
10. 평가 리포트 자동 생성

## 4. 권장 아키텍처

```text
User Question
  ↓
Question Analyzer
  ├─ intent
  ├─ category
  └─ expected evidence type
  ↓
Retrieval
  ├─ ontology retrieval
  ├─ vector retrieval
  └─ metadata/category retrieval
  ↓
EvidenceGate
  ├─ no evidence
  ├─ category mismatch
  ├─ low relevance
  └─ hallucination risk
  ↓
Answer Policy
  ├─ answer_allowed
  └─ no_answer_required
  ↓
Grounded Synthesizer
  ↓
Grounding Verifier
  ↓
Final Answer
```

## 5. EvidenceGate 설계

### 5.1 입력

`EvidenceGate`는 다음 입력을 받는다.

```text
question
intent
question_category
ontology_results
vector_results
document_metadata
retrieval_scores
```

### 5.2 출력

```json
{
  "answer_allowed": false,
  "reason": "category_mismatch",
  "policy": "category_irrelevant",
  "message": "질문은 해당 카테고리 문서와 관련이 없습니다.",
  "confidence": 0.92
}
```

### 5.3 no-answer 정책

필수 응답 문구:

```text
질문은 해당 카테고리 문서와 관련이 없습니다.
```

일반 근거 부족 문구:

```text
제공된 문서에서 질문에 대한 직접적인 근거를 찾지 못했습니다.
```

정책:

```text
if category_mismatch:
    return category_irrelevant message without LLM generation

if top evidence relevance is below threshold:
    return no_direct_evidence message without LLM generation

if ontology/vector evidence is empty:
    return no_direct_evidence message without LLM generation
```

## 6. 카테고리 판정 및 문서 메타데이터

### 6.1 문서 카테고리

각 문서와 chunk에 category metadata를 부여한다.

예:

```json
{
  "doc_id": "doc-001",
  "filename": "NLP - 온톨로지 학습 기반 지식 그래프 구축 - 2022.pdf",
  "category": "Ontology",
  "sub_category": "KnowledgeGraph",
  "source_type": "pdf"
}
```

### 6.2 질문 카테고리

질문 분류 결과:

```json
{
  "question": "ranking_issue는 Snowflake RAG 평가에서 어떤 경우로 기록해야 하는가?",
  "question_category": "Snowflake",
  "confidence": 0.95,
  "expected_evidence_category": "Snowflake"
}
```

### 6.3 카테고리 불일치 판정

```text
question_category = Snowflake
retrieved_categories = Ontology, NLP, Defense
direct_snowflake_evidence = false
→ category_mismatch
```

## 7. 검색 관련성 threshold

현재 vector score가 distance인지 similarity인지 먼저 검증한다.

작업:

1. known-positive 문항 10개 score 수집
2. known-negative 문항 10개 score 수집
3. score 분포 비교
4. threshold 후보 산출
5. 회귀 테스트로 no-answer precision/recall 확인

권장 산출물:

```text
validation/ont_platform_v4_eval/results/phase7_score_calibration/
```

## 8. 프롬프트 강화

현재 프롬프트는 권고 수준이다. PHASE7에서는 정책을 더 명시한다.

추가 문구:

```text
검색 결과는 후보일 뿐입니다.
후보 문서가 질문에 직접 답하지 않으면 일반 지식으로 보완하지 마세요.

질문이 해당 카테고리 문서와 관련 없으면 정확히 다음 문장으로만 답하세요:
"질문은 해당 카테고리 문서와 관련이 없습니다."

문서나 온톨로지 근거에 없는 내용을 추론하거나 생성하지 마세요.
```

주의: 프롬프트는 보조 수단이다. 핵심은 `EvidenceGate`에서 LLM 호출 자체를 막는 것이다.

## 9. 온톨로지 우선 라우팅

질문 유형별 라우팅:

| 질문 유형 | 우선 경로 |
|---|---|
| 개념 정의 | ontology + vector |
| 관계/상하위/매핑 | ontology graph |
| DB schema 변환 | ontology + vector |
| 동의어/이질성 | ontology relation + vector |
| 카테고리 무관 질문 | no-answer |
| 운영 평가 지표 | category evidence 확인 후 answer/no-answer |

필요 변경:

```text
IntentType에 no_answer_candidate 또는 category_mismatch 추가 검토
QueryPlan에 evidence_policy 추가
HybridSynthesizer 호출 전 EvidenceGate 삽입
```

## 10. 테스트 후 정답 보정 루프

사용자가 예상 정답을 제공하면 이를 그대로 암기시키지 않는다. 정답을 분석해 시스템 개선 항목으로 변환한다.

### 10.1 정답 보정 유형

| 유형 | 의미 | 반영 위치 |
|---|---|---|
| Knowledge Gap | 필요한 개념/정의가 없음 | ontology entity, document metadata |
| Relation Gap | 개념 간 관계가 없음 | ontology relationship |
| Retrieval Gap | 근거는 있는데 검색 실패 | chunk metadata, synonym, BM25/vector |
| Ranking Gap | 근거는 찾았지만 순위가 낮음 | reranker, score fusion |
| Policy Gap | 답하면 안 되는 질문에 답함 | EvidenceGate, no-answer rule |
| Prompt Gap | 근거는 있으나 답변 형식이 틀림 | synthesizer prompt |
| Evaluation Gap | 정답표 자체 오류 | answer key revision |

### 10.2 보정 데이터 파일

경로:

```text
validation/ont_platform_v4_eval/data/answer_key_feedback.jsonl
```

스키마:

```json
{
  "question_id": "STD-S-06",
  "question": "ranking_issue는 Snowflake RAG 평가에서 어떤 경우로 기록해야 하는가?",
  "old_expected_answer": "정답 근거 문서가 검색 후보에는 포함됐지만...",
  "revised_expected_answer": "질문은 해당 카테고리 문서와 관련이 없습니다.",
  "feedback_type": "Policy Gap",
  "category": "Snowflake",
  "condition": "no direct evidence in category documents",
  "policy_action": "add_no_answer_rule",
  "target_response": "질문은 해당 카테고리 문서와 관련이 없습니다.",
  "apply_to": ["evidence_gate", "synthesizer_policy", "evaluation_rubric"]
}
```

### 10.3 RAG/온톨로지 반영 방식

예상 정답에서 다음 구조를 추출한다.

```text
subject
predicate
object
condition
answer_policy
evidence_requirement
```

STD-S 예:

```text
(QuestionCategory:Snowflake)
  -[HAS_POLICY]->
(AnswerPolicy:CategoryIrrelevantNoAnswer)

(AnswerPolicy:CategoryIrrelevantNoAnswer)
  -[REQUIRES]->
(Evidence:DirectCategoryEvidence)
```

조건 수정 예:

기존:

```text
vector_hits > 0이면 LLM 답변 생성
```

수정:

```text
vector_hits > 0
and evidence_category == question_category
and relevance >= threshold
일 때만 LLM 답변 생성
```

## 11. 회귀 테스트 계획

### 11.1 테스트셋 분리

| 테스트셋 | 목적 |
|---|---|
| In-Domain QA | 문서에 있는 내용을 정확히 답하는지 |
| Out-of-Domain QA | 관련 없는 질문에 답하지 않는지 |
| Ontology Reasoning QA | 관계/상하위/동의어/매핑 추론 |
| Grounding QA | 답변이 citation과 충돌하지 않는지 |

### 11.2 STD-S 회귀 테스트

STD-S 8문항은 다음 정답으로 고정한다.

```text
질문은 해당 카테고리 문서와 관련이 없습니다.
```

통과 기준:

```text
STD-S no-answer accuracy >= 90%
Team4 Snowflake category score >= 90%
Hallucinated Snowflake/RAG answer count <= 1 / 8
```

## 12. 산출물

PHASE7 완료 시 다음 파일을 생성한다.

```text
validation/ont_platform_v4_eval/data/answer_key_feedback.jsonl
validation/ont_platform_v4_eval/results/phase7_score_calibration/
validation/ont_platform_v4_eval/results/phase7_regression/
validation/ont_platform_v4_eval/reports/PHASE7_ANSWER_ACCURACY_REPORT.md
validation/ont_platform_v4_eval/reports/PHASE7_REGRESSION_RESULTS.xlsx
```

코드 산출물 후보:

```text
ont_platform/v4/backend/app/services/evidence_gate.py
ont_platform/v4/backend/app/models/evidence_policy.py
ont_platform/v4/backend/app/services/question_category_classifier.py
```

## 13. 구현 우선순위

### P0: 정확도 안전장치

1. `EvidenceGate` 추가
2. category mismatch no-answer 구현
3. no-answer 시 LLM 호출 금지
4. STD-S 회귀 테스트 추가

### P1: 검색 품질 안정화

1. vector score semantics 검증
2. threshold calibration
3. chunk category metadata 추가
4. category-aware reranking

### P2: 온톨로지 활용 강화

1. ontology-first routing
2. graph relation traversal 근거 삽입
3. synonym/alias/상하위 관계 기반 query expansion
4. ontology evidence와 vector evidence 분리 표시

### P3: 정답 보정 자동화

1. `answer_key_feedback.jsonl` 도입
2. feedback type classifier 구현
3. Policy Gap → EvidenceGate rule 후보 생성
4. Relation Gap → ontology relation 후보 생성
5. Retrieval/Ranking Gap → retriever/reranker 개선 후보 생성

## 14. 수용 기준

| 항목 | 기준 |
|---|---|
| STD-S no-answer | 90% 이상 |
| Ontology 기존 점수 | 75.62% 이상 유지 |
| 전체 24문항 | 67.50% 이상 회복 |
| Out-of-domain hallucination | 10% 이하 |
| Grounded answer | 답변마다 근거 citation 확인 가능 |
| Feedback loop | 예상 정답 1건을 policy/relation/retrieval 개선 후보로 변환 가능 |

## 15. 다음 에이전트 지시

다음 에이전트는 다음 순서로 진행한다.

1. `/api/hybrid/ask` 실행 경로에서 `HybridSynthesizer` 호출 직전 위치를 확인한다.
2. `EvidenceGate`를 설계하고 최소 구현한다.
3. STD-S 8문항을 no-answer 회귀 테스트로 추가한다.
4. category metadata가 없다면 임시 파일명 기반 분류부터 적용한다.
5. vector score threshold는 calibration 결과 전까지 보수적으로 적용한다.
6. `answer_key_feedback.jsonl` 스키마를 추가한다.
7. 예상 정답 보정 1건을 `Policy Gap`으로 변환하는 샘플을 만든다.
8. 개선 전/후를 `PHASE7_REGRESSION_RESULTS.xlsx`로 비교한다.

절대 원칙:

```text
근거가 없으면 답하지 않는다.
관련 카테고리 문서가 아니면 답하지 않는다.
온톨로지 관계가 필요한 질문은 벡터 검색 일반론으로 때우지 않는다.
```
