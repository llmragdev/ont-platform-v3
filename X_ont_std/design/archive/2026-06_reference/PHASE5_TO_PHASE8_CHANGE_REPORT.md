# PHASE5 → PHASE8 변화 보고서

작성일: 2026-06-07  
대상: `ont_platform` v4 평가 결과, PHASE6/7 설계, PHASE8 v5 통합 설계  
목적: PHASE5 이후 설계가 왜 PHASE8/v5로 이동했는지, 어떤 교훈과 변경점이 있었는지 정리한다.

## 1. 요약

PHASE5까지의 흐름은 주로 RAG/온톨로지 기능을 구현하고 평가하는 데 초점이 있었다. 이후 PHASE6/7 과정에서 중요한 문제가 드러났다.

```text
시스템은 문서에 있는 내용을 답하는 능력뿐 아니라,
문서에 없는 내용에 답하지 않는 능력도 가져야 한다.
```

이 교훈을 바탕으로 PHASE8은 v4를 직접 수정하지 않고 `ont_platform/v5`를 새 버전으로 설계한다.

핵심 변화:

```text
PHASE5: 기능 구현 중심
PHASE6: 평가/정답 보정 프레임워크
PHASE7: EvidenceGate와 서빙 개선 계획
PHASE8: 평가 기준 + 서빙 정책 + v5 버전업 통합
```

## 2. 확정 사실

### 2.1 v4 baseline 평가

동일 24문항 기준 `Team4 (ont_platform v4)`는 전체 2위였다.

| 팀 | 정확도 |
|---|---:|
| Team1 | 71.77% |
| Team4 (ont_platform v4) | 67.50% |
| Team2 | 65.21% |
| Team0 | 60.42% |

Ontology 영역에서는 Team1과 거의 동률이었다.

| 팀 | Ontology |
|---|---:|
| Team1 | 75.94% |
| Team4 (ont_platform v4) | 75.62% |
| Team2 | 74.38% |
| Team0 | 61.25% |

### 2.2 STD-S 카테고리 무관 추가 평가

사용자 판단에 따라 STD-S/Snowflake 문항의 정답 기준을 다음으로 수정했다.

```text
질문은 해당 카테고리 문서와 관련이 없습니다.
```

이 기준으로 추가 평가했을 때 Team4는 STD-S 문항에서 모두 답을 생성했고, Snowflake 카테고리 점수는 0점이었다.

| 팀 | STD-S/Snowflake |
|---|---:|
| Team1 | 40.00% |
| Team0 | 37.50% |
| Team2 | 16.88% |
| Team4 (ont_platform v4) | 0.00% |

### 2.3 v4 코드 확인 결과

v4 프롬프트에는 “정보가 없으면 관련 데이터를 찾지 못했다고 답하라”는 문구가 있었다.

하지만 실제 구현에서는 다음이 부족했다.

```text
EvidenceGate 없음
질문 카테고리와 문서 카테고리 불일치 판정 없음
검색 관련성 threshold에 따른 차단 없음
no-answer 판정 시 LLM 호출 금지 없음
```

따라서 v4는 관련 없는 질문에도 vector 검색 결과를 바탕으로 LLM이 일반론을 생성할 수 있었다.

### 2.4 PHASE6 분석 결과

PHASE6 평가 프레임워크는 실제 파일과 모듈이 존재한다.

역할:

```text
Stage1: 평가 전 검증
Stage2: 평가 중 제약 검증
Stage3: 정답 보정 및 영향도 분석
```

다만 Stage3의 시스템 업데이트와 재평가는 실제 backend 적용이 아니라 시뮬레이션이었다.

따라서 다음 표현은 확정 사실이 아니라 목표 또는 시뮬레이션 결과로 봐야 한다.

```text
Snowflake 평가 실패 완전 해결
시스템 자동 업데이트 완료
Team4 정확도 개선 확정
```

## 3. PHASE5에서 PHASE8로의 설계 변화

### 3.1 기능 중심에서 정책 중심으로

기존에는 “검색하고 답한다”가 중심이었다.

PHASE8에서는 다음 정책이 중심이 된다.

```text
근거가 없으면 답하지 않는다.
관련 카테고리 문서가 아니면 답하지 않는다.
온톨로지 관계 질문은 벡터 일반론으로 때우지 않는다.
```

### 3.2 평가와 서빙의 분리 문제 해소

PHASE6은 평가 기준을 다루고, PHASE7은 서빙 구현을 다룬다. 그러나 둘을 분리하면 다음 문제가 생긴다.

```text
평가 정답표는 "관련 없습니다"로 수정됨
실제 시스템은 여전히 Snowflake 일반론 생성
```

PHASE8은 평가 정답 정책과 실제 서빙 정책을 같은 계약으로 묶는다.

공유 계약 후보:

```text
answer_key_feedback.jsonl
answer_policies.jsonl
regression test cases
```

### 3.3 v4 직접 수정에서 v5 버전업으로

v4는 baseline으로 보존한다.

v5를 만드는 이유:

```text
v4 baseline과 v5 개선 결과 비교 가능
구조 변경의 위험 격리
연구 보고서에서 변화 서사 명확
실패 시 v4로 복귀 가능
```

권장 구조:

```text
ont_platform/
├─ v4/   # baseline 보존
└─ v5/   # PHASE8 통합 개선
```

## 4. PHASE8에서 새로 통합된 설계 요소

### 4.1 EvidenceGate

LLM 호출 전에 답변 가능 여부를 판정한다.

핵심:

```text
no-answer 판정 시 LLM 호출 금지
```

### 4.2 Question Analyzer

질문을 분석해 다음 정보를 만든다.

```text
intent
question_category
expected_evidence_type
no_answer_candidate
```

### 4.3 SearchMode 기반 멀티라우팅

Antigravity 설계의 장점을 반영해 v5는 검색 모드를 명시 선택할 수 있게 한다.

```text
auto
ontology_only
vector_only
hybrid
```

이 기능은 평가와 디버깅에 중요하다.

```text
ontology_only: 온톨로지 자체 성능 확인
vector_only: RAG 검색 성능 확인
hybrid: 통합 성능 확인
auto: 운영 기본값 확인
```

### 4.4 Answer Policy와 정답 보정 루프

예상 정답은 단순 암기가 아니라 시스템 개선 신호로 분류한다.

| 유형 | 의미 |
|---|---|
| Policy Gap | 답하면 안 되는 질문에 답함 |
| Knowledge Gap | 필요한 개념/정의가 없음 |
| Relation Gap | 개념 간 관계가 없음 |
| Retrieval Gap | 근거 검색 실패 |
| Ranking Gap | 근거 순위화 실패 |
| Prompt Gap | 답변 형식 오류 |
| Evaluation Gap | 정답표 오류 |

STD-S 문제는 `Policy Gap`이다.

## 5. 확정과 목표의 구분

### 확정된 것

```text
v4는 STD-S 카테고리 무관 평가에서 Team4 Snowflake 0.00%
v4에는 EvidenceGate가 없다.
PHASE6 Stage3의 업데이트/재평가는 시뮬레이션이다.
PHASE8은 v5로 분리 개발하는 방향이 타당하다.
```

### 목표 또는 예상

```text
v5 STD-S no-answer 정확도 90% 이상
Ontology 기존 점수 75.62% 이상 유지
out-of-domain hallucination 10% 이하
SearchMode 선택 시 불필요한 라우팅 오버헤드 감소
RRF/score fusion으로 ranking 개선 가능
```

## 6. 최종 변화 요약

PHASE8은 단순히 “RAG 개선”이 아니다.

PHASE8은 다음을 통합한다.

```text
평가 기준
정답 보정
서빙 정책
검색 라우팅
온톨로지 활용
근거 검증
회귀 테스트
v4/v5 비교 보고
```

최종 설계 방향:

```text
평가가 요구하는 정답 정책과 실제 시스템이 따르는 답변 정책을 분리하지 않는다.
```
