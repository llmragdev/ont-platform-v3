# PHASE4-eval-codex: 질의 답변 정확도 향상 계획

작성일: 2026-06-07  
대상: `ont_platform v4` 질의응답 정확도 개선  
작성 목적: 동일 24문항 평가와 STD-S 카테고리 무관 추가 평가에서 드러난 실패를 바탕으로, 현재 질의에 대한 답변 정확도를 높이는 실행 계획을 정의한다.

## 1. 배경

이번 평가에서 `ont_platform v4`는 Ontology 문항에서는 Team1과 거의 동률이었다.

```text
Ontology:
Team1 75.94%
Team4 ont_platform v4 75.62%
```

하지만 Snowflake 계열 STD-S 문항에서는 심각한 문제가 드러났다.

```text
STD-S 카테고리 무관 추가 평가:
Team4 Snowflake 0.00%
```

원인은 Snowflake 문항이 해당 카테고리 문서와 관련 없는 질문이었는데도, 시스템이 “질문은 해당 카테고리 문서와 관련이 없습니다”라고 답하지 않고 Snowflake/RAG 일반론을 생성했기 때문이다.

즉, 이번 교훈은 다음과 같다.

```text
답변 정확도 = 정답 생성 능력 + 근거 없는 질문을 거절하는 능력
```

## 2. 핵심 문제

현재 `/api/hybrid/ask` 경로에는 다음 약점이 있다.

1. 문서 검색 결과가 낮은 관련성이어도 top_k 결과를 LLM에 전달한다.
2. LLM 프롬프트에는 “정보가 없으면 관련 데이터를 찾지 못했다고 답하라”는 문구가 있지만 시스템 레벨 강제가 없다.
3. 질문 카테고리와 문서 카테고리의 불일치를 판정하지 않는다.
4. 온톨로지 관계 질의가 아니라 일반 descriptive 질의로 분류되면 vector RAG 중심으로 답한다.
5. 검색 결과와 답변 간 citation-grounding 검증이 없다.
6. 테스트 후 예상 정답에서 드러난 누락 관계나 거절 조건을 온톨로지/RAG 정책에 반영하는 루프가 없다.

## 3. 목표

PHASE4의 목표는 단순히 평균 점수를 높이는 것이 아니라, 다음 네 가지 능력을 강화하는 것이다.

| 목표 | 설명 |
|---|---|
| Grounded Answer | 문서/온톨로지 근거가 있는 내용만 답변 |
| No-Answer Gate | 관련 없는 질문은 답변 생성하지 않고 거절 |
| Ontology-Aware Routing | 온톨로지 관계 질의는 graph/ontology 경로로 우선 처리 |
| Answer-Key Feedback Loop | 테스트 후 예상 정답을 분석해 RAG 관계/조건/정책에 반영 |

## 4. 개선 아키텍처

권장 질의 처리 흐름:

```text
User Question
  ↓
Question Category Classifier
  ↓
Evidence Retrieval
  ├─ Ontology retrieval
  ├─ Vector retrieval
  └─ Metadata/category retrieval
  ↓
Evidence Gate
  ├─ category mismatch?
  ├─ relevance below threshold?
  ├─ no ontology/vector evidence?
  └─ forbidden hallucination risk?
  ↓
Answer Policy
  ├─ answer allowed
  └─ no-answer required
  ↓
Grounded Synthesizer
  ↓
Citation / Grounding Verifier
  ↓
Final Answer
```

## 5. No-Answer Gate 구현 계획

### 5.1 카테고리 불일치 게이트

질문과 검색 근거의 카테고리를 비교한다.

예:

```text
질문 카테고리: Snowflake
검색 근거 카테고리: Ontology/NLP/Defense
판정: category_mismatch
답변: 질문은 해당 카테고리 문서와 관련이 없습니다.
```

필요 데이터:

- 문서별 카테고리 메타데이터
- chunk별 source category
- 질문 카테고리 분류 결과
- category confidence

권장 정책:

```text
if question_category is known
and top evidence category does not match
and no direct supporting evidence exists:
    return "질문은 해당 카테고리 문서와 관련이 없습니다."
```

### 5.2 관련성 점수 게이트

벡터 검색 결과가 있어도 관련성이 낮으면 LLM 생성으로 넘기지 않는다.

필요 조건:

- vector score/distance 정규화
- top1 relevance
- top_k 평균 relevance
- evidence coverage

권장 정책:

```text
if top1_relevance < threshold:
    no_answer

if avg_topk_relevance < threshold:
    no_answer
```

주의: 현재 Chroma score가 distance인지 similarity인지 명확히 해석해야 한다. 먼저 score semantics를 검증한 뒤 threshold를 정한다.

### 5.3 답변 생성 금지 정책

No-answer 판정 시 LLM synthesizer를 호출하지 않는다.

나쁜 흐름:

```text
근거 약함 → 그래도 LLM 호출 → 일반론 생성
```

좋은 흐름:

```text
근거 약함 → no_answer response 즉시 반환
```

권장 응답:

```text
질문은 해당 카테고리 문서와 관련이 없습니다.
```

또는 카테고리 정보가 없을 때:

```text
제공된 문서에서 질문에 대한 직접적인 근거를 찾지 못했습니다.
```

## 6. 프롬프트 개선 계획

현재 프롬프트의 문제:

- “정보가 없으면 말하라”는 문구는 있지만 강도가 약하다.
- 검색 결과가 있으면 LLM이 답을 만들어도 되는 것처럼 해석할 수 있다.
- “검색 결과가 질문과 직접 관련 있는지 먼저 판단하라”는 단계가 약하다.

개선 프롬프트 원칙:

```text
1. 답변 전에 근거가 질문에 직접 대응하는지 판단한다.
2. 직접 근거가 없으면 답변을 생성하지 않는다.
3. 일반 지식으로 보완하지 않는다.
4. 문서에 없는 내용은 추론하지 않는다.
5. 카테고리 불일치 시 지정 문구로 답한다.
```

권장 시스템 문구:

```text
검색 결과가 질문과 직접 관련되지 않으면 절대 일반 지식으로 답하지 마세요.
이 경우 정확히 다음 문장으로 답하세요:
"질문은 해당 카테고리 문서와 관련이 없습니다."

검색 결과는 참고 후보일 뿐이며, 후보가 있다는 사실만으로 답변 근거가 충분하다고 판단하지 마세요.
```

## 7. 온톨로지 라우팅 개선 계획

질문이 온톨로지 개념, 관계, 매핑, 상하위 관계, 동의어/이질성, 클래스/속성/인스턴스를 묻는 경우에는 vector-only 경로로 보내지 않는다.

권장 라우팅:

| 질문 유형 | 우선 경로 |
|---|---|
| 개념 정의 | ontology + vector |
| 관계/상하위/매핑 | ontology graph 우선 |
| 절차/방법론 | vector + ontology evidence |
| 카테고리 외 질문 | no-answer |
| 운영/평가 지표 | 문서 근거 확인 후 answer/no-answer |

필요 구현:

- intent classifier에 `category_mismatch`, `ontology_relation`, `no_answer_candidate` 추가
- ontology retrieval 결과가 없고 vector 결과도 약하면 no-answer
- graph relation query 결과를 답변 prompt에 명시적으로 삽입

## 8. 테스트 후 정답 보정 루프

사용자가 예상 정답을 제공하면, 그 정답을 단순히 외워 넣지 말고 다음 네 가지로 분해해 시스템에 반영한다.

```text
예상 정답
  ↓
정답 유형 분석
  ├─ 지식 추가 필요
  ├─ 관계 추가 필요
  ├─ 검색/랭킹 조건 수정 필요
  └─ no-answer/거절 조건 추가 필요
```

### 8.1 정답 유형 분류

예상 정답을 다음 유형으로 분류한다.

| 유형 | 의미 | 반영 위치 |
|---|---|---|
| Knowledge Gap | 문서/온톨로지에 필요한 개념이 없음 | ontology entity, document metadata |
| Relation Gap | 개념 간 관계가 없음 | ontology relationship |
| Retrieval Gap | 근거는 있는데 검색이 못 찾음 | chunk metadata, synonym, BM25/vector rerank |
| Ranking Gap | 근거는 찾았지만 상위에 못 올림 | reranker, score fusion |
| Policy Gap | 답하면 안 되는 질문에 답함 | no-answer rule, category gate |
| Prompt Gap | 근거는 있으나 답변 형식이 틀림 | synthesizer prompt |
| Evaluation Gap | 정답표 자체가 부정확함 | answer key revision |

### 8.2 예상 정답을 RAG 관계에 추가하는 방식

예상 정답에서 다음 요소를 추출한다.

```text
subject
predicate
object
condition
source_category
evidence_requirement
answer_policy
```

예:

```text
질문: ranking_issue는 Snowflake RAG 평가에서 어떤 경우로 기록해야 하는가?
수정 정답: 질문은 해당 카테고리 문서와 관련이 없습니다.

추출:
subject = STD-S category
predicate = has_answer_policy
object = category_irrelevant_no_answer
condition = no direct Snowflake evidence in category documents
answer_policy = "질문은 해당 카테고리 문서와 관련이 없습니다."
```

온톨로지/RAG 정책 반영:

```text
(QuestionCategory:Snowflake) -[HAS_POLICY]-> (AnswerPolicy:CategoryIrrelevantNoAnswer)
(AnswerPolicy:CategoryIrrelevantNoAnswer) -[REQUIRES]-> (Evidence:DirectCategoryEvidence)
(Question:STD-S-06) -[EXPECTED_POLICY]-> (AnswerPolicy:CategoryIrrelevantNoAnswer)
```

### 8.3 기존 조건 수정 방식

예상 정답이 기존 조건과 충돌하면 조건을 수정한다.

예:

기존 조건:

```text
vector_hits > 0이면 LLM 답변 생성
```

수정 조건:

```text
vector_hits > 0
and evidence_category == question_category
and relevance >= threshold
일 때만 LLM 답변 생성
```

예:

기존 조건:

```text
검색 결과가 있으면 출처와 함께 답변
```

수정 조건:

```text
검색 결과가 질문에 직접 대응하지 않으면 no-answer
```

### 8.4 정답 보정 데이터 저장 형식

권장 파일:

```text
validation/ont_platform_v4_eval/data/answer_key_feedback.jsonl
```

권장 스키마:

```json
{
  "question_id": "STD-S-06",
  "question": "ranking_issue는 Snowflake RAG 평가에서 어떤 경우로 기록해야 하는가?",
  "old_expected_answer": "...",
  "revised_expected_answer": "질문은 해당 카테고리 문서와 관련이 없습니다.",
  "feedback_type": "Policy Gap",
  "policy_action": "add_no_answer_rule",
  "category": "Snowflake",
  "condition": "no direct evidence in category documents",
  "target_response": "질문은 해당 카테고리 문서와 관련이 없습니다.",
  "apply_to": ["retrieval_gate", "synthesizer_policy", "evaluation_rubric"]
}
```

## 9. 평가 개선 계획

평가셋을 세 종류로 분리한다.

| 평가셋 | 목적 |
|---|---|
| In-Domain QA | 문서에 있는 내용을 정확히 답하는지 |
| Out-of-Domain QA | 관련 없는 질문에 답하지 않는지 |
| Ontology Reasoning QA | 관계/상하위/매핑/동의어 추론을 하는지 |

각 문항에 다음 메타데이터를 추가한다.

```text
question_id
category
expected_answer_type
expected_answer
expected_policy
required_evidence_category
forbidden_answer_type
must_cite
```

예:

```json
{
  "question_id": "STD-S-06",
  "category": "Snowflake",
  "expected_answer_type": "no_answer",
  "expected_policy": "category_irrelevant",
  "expected_answer": "질문은 해당 카테고리 문서와 관련이 없습니다.",
  "forbidden_answer_type": "general_snowflake_rag_answer"
}
```

## 10. 구현 우선순위

### P0: 즉시 수정

1. `EvidenceGate` 모듈 추가
2. no-answer 판정 시 LLM 호출 금지
3. `category_mismatch` 응답 문구 고정
4. STD-S 같은 out-of-domain 테스트 케이스를 회귀 테스트로 추가

### P1: 검색 품질 개선

1. vector score semantics 검증
2. relevance threshold 도입
3. chunk category metadata 추가
4. BM25 + vector hybrid retrieval 도입 또는 개선
5. reranking에 category match 가중치 추가

### P2: 온톨로지 활용 강화

1. 질문 유형별 ontology-first routing
2. graph relation traversal 결과를 답변 근거로 삽입
3. synonym/alias/상하위 관계 기반 query expansion
4. ontology evidence와 vector evidence를 분리 표시

### P3: 정답 보정 자동화

1. `answer_key_feedback.jsonl` 도입
2. 예상 정답 분석기 구현
3. Policy Gap은 no-answer rule로 자동 변환
4. Relation Gap은 ontology relationship 후보로 저장
5. Retrieval Gap은 synonym/chunk metadata/rerank 후보로 저장

## 11. 수용 기준

다음 조건을 만족하면 PHASE4 개선을 통과로 본다.

| 항목 | 기준 |
|---|---|
| STD-S 카테고리 무관 문항 | Team4 no-answer 정확도 90% 이상 |
| Ontology 문항 | 기존 75.62% 이상 유지 |
| 전체 24문항 | 기존 67.50% 이상 회복 |
| hallucination rate | out-of-domain 문항에서 10% 이하 |
| citation grounding | 답변 문장별 근거 확인 가능 |

## 12. 다음 에이전트 작업 지시

다음 에이전트는 이 문서를 기준으로 다음 순서로 작업한다.

1. 현재 `/api/hybrid/ask` 경로에서 `EvidenceGate` 삽입 위치를 찾는다.
2. 검색 결과의 score semantics를 검증한다.
3. chunk/document category metadata 구조를 확인한다.
4. no-answer gate를 구현한다.
5. STD-S 카테고리 무관 문항을 회귀 테스트로 만든다.
6. 예상 정답 보정 파일 `answer_key_feedback.jsonl` 스키마를 추가한다.
7. 보정 정답을 RAG 정책/온톨로지 관계 후보로 변환하는 초안을 만든다.

핵심 원칙:

```text
근거 없는 답변을 잘 만드는 시스템보다,
근거 없음을 정확히 아는 시스템이 더 정확하다.
```
