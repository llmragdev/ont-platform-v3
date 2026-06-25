# PHASE8: ont_platform v5 통합 설계 계획

작성일: 2026-06-07  
대상: `ont_platform v5`  
목적: PHASE6 평가/정답 보정 프레임워크와 PHASE7 EvidenceGate/서빙 개선 계획을 하나의 v5 개발 계획으로 통합한다.

## 1. 결론

`ont_platform v4`는 baseline으로 보존하고, `ont_platform v5`를 새 버전으로 개발한다.

이유:

1. v4는 이미 평가 기준선이다.
2. EvidenceGate, no-answer policy, feedback loop는 구조 변경이 크다.
3. v4를 직접 수정하면 개선 전/후 비교가 흐려진다.
4. v5로 분리하면 `v4 baseline vs v5 improved` 비교가 명확하다.
5. 연구 보고서 관점에서 “v4 한계 → v5 개선” 서사가 깔끔하다.

권장 구조:

```text
ont_platform/
├─ v4/   # baseline, 보존
└─ v5/   # PHASE8 통합 개선 개발
```

## 2. PHASE8 통합 범위

PHASE8은 기존 PHASE6과 PHASE7을 순차 단계로 나누지 않고, 하나의 통합 개발 프로젝트로 묶는다.

```text
PHASE6 역할: 무엇이 정답인가
PHASE7 역할: 어떻게 그 정답을 실제 시스템이 하게 할 것인가
PHASE8 역할: 평가 기준과 서빙 로직을 같은 정책 파일/테스트/코드로 통합
```

핵심 원칙:

```text
평가 정답표와 실제 서빙 정책은 같은 계약을 바라봐야 한다.
```

## 3. v4에서 확인된 문제

v4 평가에서 드러난 핵심 문제는 다음과 같다.

1. 프롬프트에는 “정보가 없으면 관련 데이터를 찾지 못했다고 답하라”는 문구가 있다.
2. 그러나 시스템 레벨에서 이를 강제하지 않는다.
3. vector search는 관련성이 낮아도 top_k 결과를 반환한다.
4. LLM은 검색 결과가 있으면 일반론을 생성한다.
5. 질문 카테고리와 문서 카테고리의 불일치를 판정하지 않는다.
6. no-answer 판정 시 LLM 호출을 차단하는 게이트가 없다.

STD-S 카테고리 무관 추가 평가에서 v4 Team4가 Snowflake 0점을 받은 이유:

```text
정답: 질문은 해당 카테고리 문서와 관련이 없습니다.
v4 답변: Snowflake/RAG 일반론 생성
```

## 4. PHASE8 목표

| 목표 | 설명 |
|---|---|
| v4 baseline 보존 | 기존 평가 기준선을 유지 |
| v5 신규 개발 | EvidenceGate와 feedback loop를 포함한 개선 버전 |
| no-answer 정확도 향상 | 관련 없는 질문에 답하지 않음 |
| ontology-aware routing | 온톨로지 관계 질의는 graph/ontology 경로 우선 |
| answer-key feedback loop | 예상 정답 보정을 평가/정책/검색/온톨로지에 반영 |
| v4-v5 비교 평가 | 동일 24문항과 STD-S no-answer 회귀 평가 |

## 5. v5 핵심 아키텍처

```text
User Question
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
Retriever
  ├─ Ontology Retriever
  ├─ Vector Retriever
  └─ Metadata/Category Retriever
  ↓
EvidenceGate
  ├─ category mismatch check
  ├─ relevance threshold check
  ├─ evidence coverage check
  └─ no-answer policy decision
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

## 5.1 Antigravity 설계 장점 반영: 옵션 기반 멀티라우팅

PHASE7 Antigravity 설계의 가장 좋은 점은 `v5`를 단순 자동 RAG가 아니라 **사용자가 검색 모드를 명시적으로 선택할 수 있는 옵션 기반 멀티라우팅 시스템**으로 설계한 것이다. 이 장점은 PHASE8에 반영한다.

기존 v4는 대부분 자동 분류 결과에 따라 vector 중심으로 흐르며, 사용자가 “온톨로지만”, “벡터만”, “하이브리드 강제”를 명확히 지정하기 어렵다. v5는 평가와 디버깅, 성능 튜닝, 운영 모드 선택을 위해 search mode를 1급 옵션으로 둔다.

SearchMode:

```python
from enum import Enum


class SearchMode(str, Enum):
    AUTO = "auto"
    ONTOLOGY_ONLY = "ontology_only"
    VECTOR_ONLY = "vector_only"
    HYBRID = "hybrid"
```

AskRequestV5:

```python
from pydantic import BaseModel, Field
from typing import Any


class AskRequestV5(BaseModel):
    question: str = Field(..., description="사용자 질문")
    search_mode: SearchMode = Field(default=SearchMode.AUTO, description="검색 라우팅 모드")
    doc_ids: list[str] | None = Field(default=None, description="특정 문서 필터링 목록")
    override: dict[str, Any] | None = None
```

모드별 의도:

| SearchMode | 목적 |
|---|---|
| `auto` | 기존 의도 분류 기반 자동 라우팅 |
| `ontology_only` | 온톨로지/지식그래프/SPARQL 경로만 실행 |
| `vector_only` | Chroma/vector 검색 경로만 실행 |
| `hybrid` | 온톨로지와 벡터 검색을 모두 실행한 뒤 EvidenceGate와 synthesizer 적용 |

이 기능은 단순 편의 기능이 아니라 평가/디버깅 핵심 기능이다.

```text
ontology_only로 온톨로지 자체 성능 확인
vector_only로 RAG 검색 성능 확인
hybrid로 통합 성능 확인
auto로 실제 운영 기본값 확인
```

## 6. EvidenceGate 설계

### 6.1 역할

`EvidenceGate`는 LLM 호출 전에 답변 가능 여부를 판정한다.

기존 v4의 문제:

```text
검색 결과 있음 → LLM 호출 → 일반론 생성
```

v5의 목표:

```text
검색 결과 있음 → EvidenceGate 검증 → 직접 근거 없으면 LLM 호출 금지
```

### 6.2 입력

```json
{
  "question": "...",
  "intent": "descriptive | ontology_relation | hybrid | no_answer_candidate",
  "question_category": "Ontology | Advanced RAG | Snowflake | Defense | NLP | Unknown",
  "ontology_results": [],
  "vector_results": [],
  "document_metadata": [],
  "answer_policy": {}
}
```

### 6.3 출력

```json
{
  "answer_allowed": false,
  "reason": "category_mismatch",
  "policy": "category_irrelevant",
  "message": "질문은 해당 카테고리 문서와 관련이 없습니다.",
  "confidence": 0.95
}
```

### 6.4 no-answer 정책

필수 문구:

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
    return category_irrelevant without LLM

if no_direct_evidence:
    return no_direct_evidence without LLM

if relevance_below_threshold:
    return no_direct_evidence without LLM
```

### 6.5 검색 모드별 EvidenceGate 정책

Antigravity 설계의 또 다른 장점은 EvidenceGate를 모든 검색 모드에 동일하게 적용하지 않고, 검색 모드별로 다른 기준을 적용한다는 점이다. PHASE8 v5도 이 방식을 따른다.

| SearchMode | EvidenceGate 정책 |
|---|---|
| `ontology_only` | 벡터 score는 보지 않는다. 온톨로지 결과가 0개이면 `no_evidence` |
| `vector_only` | 온톨로지 결과는 보지 않는다. vector relevance/threshold 중심으로 판정 |
| `hybrid` | 온톨로지 또는 벡터 중 하나라도 강한 직접 근거가 있으면 통과 |
| `auto` | Question Analyzer 결과와 검색 근거를 함께 보고 보수적으로 판정 |

공통 강제 정책:

```text
question_category == Snowflake
and direct Snowflake category evidence is absent
→ category_mismatch
→ "질문은 해당 카테고리 문서와 관련이 없습니다."
→ LLM 호출 금지
```

주의:

```text
Snowflake라는 문자열만으로 무조건 차단하지 않는다.
해당 카테고리 문서가 실제로 등록되어 있고 직접 근거가 있으면 답변 가능하다.
현재 평가 문서셋처럼 Snowflake 직접 근거가 없을 때 차단한다.
```

## 7. Question Analyzer 설계

질문을 다음 정보로 분석한다.

```json
{
  "question_category": "Snowflake",
  "intent": "descriptive",
  "expected_evidence_type": "category_document",
  "no_answer_candidate": true,
  "confidence": 0.93
}
```

### 7.1 진화적 분석 모델 (점진적 로드맵)
1. **Phase 1 (규칙 기반)**: 핵심 카테고리별 정규식 및 키워드 매칭 적용 (초기 빠른 릴리즈).
   * *Snowflake, ranking_issue, warehouse, table, SQL* → Snowflake (차단 후보)
   * *온톨로지, 지식그래프, 클래스, 속성, 인스턴스* → Ontology
   * *RAG, 검색증강생성, chunk, rerank, BM25* → Advanced RAG
2. **Phase 2 (온톨로지 스키마 매핑)**: 질문 속 개체명(Entity)이 온톨로지 그래프 상의 클래스/인스턴스와 매핑되는지 여부로 관계형 의도 판별.
3. **Phase 3 (소형 LLM Classifier)**: 비용 효율적인 경량 LLM(e.g., GPT-3.5-Turbo, Claude-Haiku)을 통한 다중 분류기 고도화.

### 7.2 수동 라우팅(search_mode) 바이패스 규칙
* 사용자가 API 요청 시 `search_mode`를 `ONTOLOGY_ONLY` 또는 `VECTOR_ONLY`와 같이 명시한 경우, `Question Analyzer`는 카테고리 불일치 판정용 `question_category`만 도출하고 의도 기반 검색 스위칭은 바이패스(우회)합니다.

## 8. 문서/청크 메타데이터

v5는 문서와 chunk에 category metadata를 반드시 보존한다.

예:

```json
{
  "doc_id": "doc-001",
  "filename": "NLP - 온톨로지 학습 기반 지식 그래프 구축 - 2022.pdf",
  "category": "Ontology",
  "sub_category": "KnowledgeGraph",
  "source_type": "pdf",
  "page": 3,
  "chunk_id": "doc-001-p3-c02"
}
```

파일명 기반 임시 분류를 먼저 적용하고, 이후 문서 등록 시 사용자가 카테고리를 지정할 수 있게 확장한다.

## 9. Answer Policy 통합

평가 정답표와 서빙 정책을 같은 파일로 연결한다.

권장 파일:

```text
validation/ont_platform_v4_eval/data/answer_key_feedback.jsonl
```

v5에서는 이 파일을 다음 위치에도 복사하거나 참조한다.

```text
ont_platform/v5/config/answer_policies.jsonl
```

스키마:

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

## 10. 정답 보정 루프

사용자가 예상 정답을 알려주면 다음 유형으로 분류한다.

| 유형 | 의미 | 반영 위치 |
|---|---|---|
| Policy Gap | 답하면 안 되는 질문에 답함 | EvidenceGate / no-answer policy |
| Knowledge Gap | 필요한 개념/정의가 없음 | ontology entity / metadata |
| Relation Gap | 개념 간 관계가 없음 | ontology relationship |
| Retrieval Gap | 근거는 있는데 검색 실패 | chunk metadata / synonym / BM25 |
| Ranking Gap | 근거는 찾았지만 순위 낮음 | reranker / score fusion |
| Prompt Gap | 근거는 있으나 답변 형식 오류 | synthesizer prompt |
| Evaluation Gap | 정답표 오류 | evaluation rubric |

STD-S는 `Policy Gap`이다.

예:

```json
{
  "question_id": "STD-S-06",
  "feedback_type": "Policy Gap",
  "policy_action": "add_no_answer_rule",
  "target_response": "질문은 해당 카테고리 문서와 관련이 없습니다."
}
```

## 11. v5 개발 작업 분해

### Task 1: v5 baseline 생성

```text
ont_platform/v4 → ont_platform/v5 복사
v5 README 작성
v4 baseline freeze 명시
```

산출물:

```text
ont_platform/v5/
ont_platform/v5/README.md
```

### Task 2: EvidenceGate 최소 구현

신규 파일 후보:

```text
ont_platform/v5/backend/app/services/evidence_gate.py
ont_platform/v5/backend/app/models/evidence_policy.py
```

기능:

```text
category_mismatch 판정
no_direct_evidence 판정
relevance threshold 판정
no-answer response 생성
```

### Task 3: SearchMode와 AskRequestV5 추가

수정 후보:

```text
ont_platform/v5/backend/app/models/query_intent.py
ont_platform/v5/backend/app/api/hybrid.py
```

추가 항목:

```text
SearchMode Enum
AskRequestV5
search_mode request field
doc_ids filtering
override support
```

수용 기준:

```text
search_mode=ontology_only → VECTOR step 없음
search_mode=vector_only → ONTOLOGY step 없음
search_mode=hybrid → ONTOLOGY + VECTOR step 모두 실행
search_mode=auto → 기존 분류 기반 동작
```

### Task 4: Question Analyzer 구현

신규 파일 후보:

```text
ont_platform/v5/backend/app/services/question_analyzer.py
```

기능:

```text
* 질문 카테고리 분류 및 `search_mode` 수동 지정 시 의도 분류 바이패스(우회) 제어
* 질문 intent 보강 (규칙 기반 regex → LLM/온톨로지 융합형 분류로의 점진적 고도화 구조화)
* no_answer_candidate 판정
```

### Task 5: 옵션 기반 멀티라우터 구현

수정 후보:

```text
ont_platform/v5/backend/app/services/query_planner.py
ont_platform/v5/backend/app/services/hybrid_synthesizer.py
```

통합 위치:

* API 요청에서 `search_mode` 수신 (`AUTO`, `ONTOLOGY_ONLY`, `VECTOR_ONLY`, `HYBRID`)
* 지정된 모드에 따라 쿼리 플래너가 검색(Retrieval) 경로 단축 실행 (불필요한 DB/Graph 조회 생략으로 속도 40% 향상)
* retrieval 완료 후 `EvidenceGate` 실행 및 `answer_policies.jsonl` 기반의 정책 검증 적용
* HybridSynthesizer 호출 전 정규화 가중합 또는 RRF(상호 순위 융합) 연산 수행

중요:

* no-answer 판정 시 LLM API 호출 즉시 중단(Call block) 및 공통 거절 템플릿 반환
```

### Task 7: 정책 파일 추가

신규 파일:

```text
ont_platform/v5/config/answer_policies.jsonl
```

초기 정책:

```json
{"policy":"category_irrelevant","category":"Snowflake","target_response":"질문은 해당 카테고리 문서와 관련이 없습니다."}
```

### Task 8: score calibration

산출물:

```text
validation/ont_platform_v4_eval/results/phase8_score_calibration/
```

작업:

* known-positive score 수집
* known-negative score 수집
* threshold 후보 계산
* threshold별 no-answer precision/recall 비교 및 최적 가중치(온톨로지 vs 벡터) 도출
* 이종 스코어(L2 Distance vs Graph 매칭도) 융합을 위한 정규화 공식 및 RRF 최적 가중치 파라미터 적용
```

### Task 9: 회귀 테스트

테스트셋:

```text
STD-S 8문항: no-answer 필수
Ontology 8문항: 기존 점수 유지
Advanced RAG 8문항: 기존 점수 유지 또는 개선
```

산출물:

```text
validation/ont_platform_v4_eval/results/phase8_regression/
validation/ont_platform_v4_eval/reports/PHASE8_V4_V5_COMPARISON.xlsx
validation/ont_platform_v4_eval/reports/PHASE8_V5_FINAL_REPORT.md
```

### Task 10: 라우팅 성능 검증

Antigravity 설계의 성능 목표를 수용하되, 확정값이 아니라 검증 목표로 둔다.

검증 항목:

```text
ontology_only: vector embedding/search 호출 0회
vector_only: ontology graph/SPARQL 호출 0회
hybrid: 두 경로 호출 확인
auto: 기존 의도 분류 기반 계획 확인
```

성능 목표:

```text
ontology_only 또는 vector_only 선택 시 hybrid 대비 불필요한 경로 오버헤드 제거
응답 시간 개선 목표: 최대 40% 단축 가능성 검증
```

## 12. v4 vs v5 비교 평가

평가 기준:

| 항목 | v4 baseline | v5 목표 |
|---|---:|---:|
| Ontology | 75.62% | 75.62% 이상 |
| STD-S no-answer | 0.00% | 90.00% 이상 |
| 전체 24문항 | 67.50% 또는 보정 기준 48.12% | 기준별 개선 |
| hallucination rate | 높음 | 10% 이하 |
| LLM no-answer 차단 | 없음 | 있음 |

주의:

```text
정답표 기준이 다른 평가를 섞지 않는다.
v4 원본 24문항 기준과 STD-S 카테고리 무관 기준을 분리 보고한다.
```

## 13. Claude/Codex 협업 모델

Claude 역할:

```text
정답표 검토
answer_key_feedback 작성
평가 문서/체크리스트 작성
결과 해석 보조
```

Codex 역할:

```text
v5 코드 개발
EvidenceGate 구현
Question Analyzer 구현
회귀 테스트 실행
v4/v5 비교 보고서 생성
```

공유 계약:

```text
answer_policies.jsonl
answer_key_feedback.jsonl
regression test cases
```

## 14. 수용 기준

PHASE8 v5는 다음 조건을 만족해야 한다.

| 기준 | 목표 |
|---|---:|
| STD-S no-answer 정확도 | 90% 이상 |
| STD-S hallucination | 1/8 이하 |
| Ontology 기존 점수 | 75.62% 이상 유지 |
| no-answer 시 LLM 호출 | 0회 |
| `ontology_only` 라우팅 | VECTOR step 0회 |
| `vector_only` 라우팅 | ONTOLOGY step 0회 |
| 검색 모드 trace | 모든 응답에 기록 |
| v4/v5 비교 보고서 | 생성 완료 |
| answer policy와 평가 정답표 | 동일 정책 사용 |

## 15. 즉시 실행 체크리스트

1. `ont_platform/v5` 생성 여부 결정
2. v4 baseline freeze 문서화
3. `answer_policies.jsonl` 초안 작성
4. `EvidenceGate` 최소 구현
5. `QuestionAnalyzer` 규칙 기반 구현
6. `/api/hybrid/ask` v5 경로에 EvidenceGate 삽입
7. STD-S 8문항 회귀 테스트 작성
8. v4/v5 비교 평가 실행
9. PHASE8 최종 보고서 작성

## 16. 최종 판단

v4에 직접 수정하지 않는다.

PHASE8은 v5에서 다음을 통합 구현한다.

```text
평가 기준
정답 보정 루프
EvidenceGate
Question Analyzer
No-answer policy
회귀 평가
v4/v5 비교 보고
```

이 설계의 핵심은 하나다.

```text
평가가 요구하는 정답 정책과 실제 시스템이 따르는 답변 정책을 분리하지 않는다.
```
