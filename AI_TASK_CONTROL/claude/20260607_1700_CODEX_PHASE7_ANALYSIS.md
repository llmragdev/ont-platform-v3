# Codex PHASE 7 분석 보고서

**분석일**: 2026-06-07  
**작성자**: Claude Code  
**대상**: PHASE7_ANSWER_ACCURACY_AND_FEEDBACK_LOOP_PLAN.md (Codex 작성)  
**목적**: Codex의 PHASE 7 계획 상세 분석 및 평가

---

## 📊 **Executive Summary**

### 1단락 핵심
Codex가 제시한 **PHASE 7은 근본적인 아키텍처 개선 계획**입니다.

```
변경 전 (현재):
  Q: "Snowflake RAG에서..."
  → 벡터 검색 → RAG 관련 문서 반환
  → LLM 생성 → "RAG는..."
  → Score: 0% (범위 외 질문인데 답변함) ❌

변경 후 (PHASE 7):
  Q: "Snowflake RAG에서..."
  → 벡터 검색 → RAG 관련 문서 반환
  → EvidenceGate 검증 → 카테고리 불일치 감지
  → LLM 호출 차단 → "관련 없습니다"
  → Score: 100% (범위 외 질문에 올바른 답변) ✓
```

### 성과 기대치
- **Snowflake 정확도**: 0% → 90%+ (90%p 개선)
- **전체 정확도**: 31.25% → 67.50%+ (+36.25%p)
- **Hallucination 감소**: 무제약 생성 → Gate 기반 제어

---

## 🔍 **1. 핵심 개념 분석**

### 1.1 **4가지 핵심 목표**

| # | 목표 | 의미 | 현재 상태 |
|---|---|---|---|
| 1 | Evidence-Grounded QA | 문서/온톨로지 근거 있는 내용만 답변 | ❌ 없음 |
| 2 | No-Answer Gate | 관련 없는 질문 답변 거부 | ❌ 없음 |
| 3 | Ontology-Aware Routing | 온톨로지 우선 라우팅 | ⚠️ 부분 |
| 4 | Answer-Key Feedback Loop | 정답으로부터 시스템 개선 | ❌ 없음 |

**평가**: 모든 항목이 신규 또는 강화 필요 (개발량 중대)

---

### 1.2 **핵심 원칙**

```
"근거 없는 답변을 잘 만드는 시스템보다,
 근거 없음을 정확히 아는 시스템이 더 정확하다."
```

**해석**:
- ❌ 부족한 정보로 그럴듯한 답변 생성
- ✅ 정보 부족을 명확히 인식하고 명시

**영향도**: 프롬프트 → 아키텍처 변경 필요 (깊이 있음)

---

## 🏗️ **2. 제안 아키텍처 분석**

### 2.1 **흐름도**

```
User Question
  ↓
Question Analyzer        ← NEW: intent + category 추출
  ├─ intent
  ├─ category
  └─ expected evidence type
  ↓
Retrieval               ← 기존
  ├─ ontology retrieval
  ├─ vector retrieval
  └─ metadata/category retrieval
  ↓
EvidenceGate           ← NEW: 핵심 게이트 추가
  ├─ no evidence       
  ├─ category mismatch
  ├─ low relevance
  └─ hallucination risk
  ↓
Answer Policy          ← NEW: 정책 기반 판정
  ├─ answer_allowed
  └─ no_answer_required
  ↓
Grounded Synthesizer   ← 기존 (프롬프트 강화)
  ↓
Grounding Verifier     ← NEW: 근거 검증
  ↓
Final Answer           ← 결과
```

### 2.2 **변경 범위**

| 컴포넌트 | 현재 | 변경 | 영향도 |
|---|---|---|---|
| Question Analyzer | 부분 | 강화 (카테고리, intent) | 중간 |
| Retrieval | 완성 | 카테고리 메타데이터 추가 | 낮음 |
| **EvidenceGate** | ❌ 없음 | **NEW 추가** | **높음** |
| Answer Policy | ❌ 없음 | **NEW 추가** | **높음** |
| Synthesizer | 완성 | 프롬프트 강화 | 낮음 |
| Grounding Verifier | 부분 | 강화 (citation 검증) | 중간 |

**결론**: 2개 새 모듈 (EvidenceGate, AnswerPolicy) 필수 + 3개 기존 모듈 강화

---

## 💡 **3. EvidenceGate 설계 분석**

### 3.1 **핵심 기능**

```python
class EvidenceGate:
    """근거 기반 답변 가능 여부 판정"""
    
    def evaluate(self, question, retrieval_results) -> Decision:
        """
        4가지 차단 조건 검증:
        1. no evidence          → 검색 결과 없음
        2. category mismatch    → 카테고리 불일치
        3. low relevance        → 관련성 낮음
        4. hallucination risk   → 생성 위험 감지
        """
        
        # 출력
        return {
            "answer_allowed": False,
            "reason": "category_mismatch",
            "policy": "category_irrelevant",
            "message": "질문은 해당 카테고리 문서와 관련이 없습니다.",
            "confidence": 0.92
        }
```

### 3.2 **no-answer 정책**

```
카테고리 불일치 시:
  → "질문은 해당 카테고리 문서와 관련이 없습니다."
  → LLM 호출 금지 (즉시 반환)

근거 부족 시:
  → "제공된 문서에서 질문에 대한 직접적인 근거를 찾지 못했습니다."
  → LLM 호출 금지

정책:
  if category_mismatch:
      return message without LLM
  if top_evidence_relevance < threshold:
      return no_direct_evidence without LLM
  if ontology/vector_evidence is empty:
      return no_direct_evidence without LLM
```

**핵심**: LLM 호출 자체를 차단 (프롬프트 대신 아키텍처 제어)

---

### 3.3 **카테고리 판정 메커니즘**

```json
문서 메타데이터:
{
  "doc_id": "doc-001",
  "filename": "NLP - 온톨로지 학습 기반 지식 그래프 구축 - 2022.pdf",
  "category": "Ontology",
  "sub_category": "KnowledgeGraph"
}

질문 분류 결과:
{
  "question": "ranking_issue는 Snowflake RAG 평가에서?",
  "question_category": "Snowflake",
  "confidence": 0.95,
  "expected_evidence_category": "Snowflake"
}

불일치 판정:
  question_category = Snowflake
  retrieved_categories = [Ontology, NLP, Defense]
  direct_snowflake_evidence = false
  → 판정: category_mismatch = TRUE
  → 조치: "관련 없습니다" (LLM 호출 금지)
```

**강도**: 완전히 엄격한 카테고리 일치 요구

---

## 📈 **4. 정답 보정 루프 (Feedback Loop)**

### 4.1 **7가지 보정 유형**

| 유형 | 의미 | 반영 위치 | 난이도 |
|---|---|---|---|
| Knowledge Gap | 필요한 개념/정의 부재 | ontology entity | 높음 |
| Relation Gap | 개념 간 관계 부재 | ontology relationship | 높음 |
| Retrieval Gap | 근거 존재하나 검색 실패 | chunk metadata, synonym | 중간 |
| Ranking Gap | 근거 발견했으나 순위 낮음 | reranker, score fusion | 중간 |
| **Policy Gap** | 답하면 안 되는데 답함 | EvidenceGate, rule | 낮음 |
| Prompt Gap | 근거 있으나 답변 형식 오류 | synthesizer prompt | 낮음 |
| Evaluation Gap | 정답표 자체 오류 | answer key revision | 낮음 |

**실현 가능성**:
- Policy Gap (쉬움) → EvidenceGate 규칙 추가
- Retrieval Gap (중간) → BM25, vector 튜닝
- Knowledge Gap (어려움) → 온톨로지 확장

### 4.2 **보정 데이터 스키마**

```json
{
  "question_id": "STD-S-06",
  "question": "ranking_issue는 Snowflake RAG 평가에서?",
  "old_expected_answer": "정답 근거 문서가 검색 후보에는...",
  "revised_expected_answer": "질문은 해당 카테고리 문서와 관련이 없습니다.",
  
  "feedback_type": "Policy Gap",
  "category": "Snowflake",
  "condition": "no direct evidence in category documents",
  
  "policy_action": "add_no_answer_rule",
  "target_response": "질문은 해당 카테고리 문서와 관련이 없습니다.",
  
  "apply_to": [
    "evidence_gate",
    "synthesizer_policy",
    "evaluation_rubric"
  ]
}
```

**구조**: 정답 → 정책 → 적용 대상 (자동화 가능)

---

### 4.3 **온톨로지 반영 방식**

```
원본 정책:
  vector_hits > 0 이면 LLM 답변 생성

개선된 정책:
  vector_hits > 0
  AND evidence_category == question_category
  AND relevance >= threshold
  일 때만 LLM 답변 생성

온톨로지 표현:
  (QuestionCategory:Snowflake)
    -[HAS_POLICY]->
  (AnswerPolicy:CategoryIrrelevantNoAnswer)
  
  (AnswerPolicy:CategoryIrrelevantNoAnswer)
    -[REQUIRES]->
  (Evidence:DirectCategoryEvidence)
```

**장점**: 정책을 온톨로지로 명시화 가능

---

## 📋 **5. 회귀 테스트 계획**

### 5.1 **4가지 테스트셋**

| 테스트셋 | 목적 | 크기 (추정) | 기대 결과 |
|---|---|---|---|
| In-Domain QA | 문서 내용 정확도 | 8개 | ✓ 유지 (75%+) |
| **Out-of-Domain QA** | 범위 외 거절 | **8개 (STD-S)** | **✓ 90%+ 개선** |
| Ontology Reasoning QA | 관계 추론 | 4개 (추정) | ✓ 향상 |
| Grounding QA | 근거-답변 일관성 | 4개 (추정) | ✓ 100% citation |

**핵심**: STD-S (Out-of-Domain) 정확도 0% → 90%

### 5.2 **STD-S 회귀 테스트 기준**

```
고정 정답:
  "질문은 해당 카테고리 문서와 관련이 없습니다."

통과 기준:
  1. STD-S no-answer accuracy >= 90%
  2. Team4 Snowflake category score >= 90%
  3. Hallucinated Snowflake/RAG answer count <= 1/8

평가 방법:
  Team4 시스템 실행 → STD-S 8개 답변
  → 각 답변이 정해진 문구와 일치도 검증
  → Hallucination 패턴 감지
```

**강도**: 명확하고 객관적

---

## 🎯 **6. 수용 기준 분석**

### 6.1 **최종 목표**

| 항목 | 목표 | 현재 | 개선량 |
|---|---|---|---|
| STD-S no-answer | 90% 이상 | 0% | +90%p |
| Ontology 유지 | 75.62% 이상 | 75.62% | 0 (유지) |
| **전체 24문항** | **67.50% 이상** | **31.25%** | **+36.25%p** |
| Out-of-domain hallucination | 10% 이하 | 100% | -90%p |

**평가**: 도전적이지만 달성 가능한 목표

### 6.2 **추가 요구사항**

```
✓ Grounded answer: 답변마다 근거 citation 확인 가능
  → Evidence 명시 필요

✓ Feedback loop: 예상 정답 1건을 개선 항목으로 변환 가능
  → answer_key_feedback.jsonl 스키마로 자동화
```

---

## 📦 **7. 구현 우선순위 분석**

### 7.1 **4단계 우선순위**

```
P0: 정확도 안전장치 (필수)
  1. EvidenceGate 추가              ⭐⭐⭐
  2. category mismatch no-answer    ⭐⭐⭐
  3. 정책 기반 LLM 호출 금지        ⭐⭐⭐
  4. STD-S 회귀 테스트              ⭐⭐⭐

P1: 검색 품질 안정화 (권장)
  1. vector score semantics 검증    ⭐⭐
  2. threshold calibration          ⭐⭐
  3. chunk category metadata        ⭐⭐
  4. category-aware reranking       ⭐

P2: 온톨로지 활용 강화 (선택)
  1. ontology-first routing         ⭐⭐
  2. graph relation traversal       ⭐
  3. query expansion                ⭐
  4. evidence 분리 표시             ⭐

P3: 정답 보정 자동화 (미래)
  1. answer_key_feedback.jsonl      ⭐
  2. feedback type classifier       ⭐
  3. Rule/Relation/Retrieval 후보   ⭐
```

**해석**:
- P0는 필수 (2개 새 모듈)
- P1은 검색 품질 확보 (현재 vector score 검증 필요)
- P2/P3는 추가 개선 (장기 로드맵)

---

## 🔗 **8. 기존 PHASE 6과 연계 분석**

### 8.1 **PHASE 6 vs PHASE 7**

| 차원 | PHASE 6 | PHASE 7 |
|---|---|---|
| **목표** | 정답 보정 | 근거 기반 답변 |
| **범위** | 평가 후 (Offline) | 실제 서빙 (Online) |
| **개입 점** | 채점 기준 변경 | 답변 생성 원천 차단 |
| **구조** | Stage 1/2/3 | EvidenceGate + Policy |
| **효과** | 평가 정확도 개선 | 시스템 신뢰도 향상 |

### 8.2 **상호 보완 관계**

```
PHASE 6 (정답 보정):
  STD-S-01~08: "관련 없습니다" 정답으로 설정
                → 기대값 확립

PHASE 7 (근거 기반 답변):
  EvidenceGate: STD-S 감지 → "관련 없습니다" 자동 반환
                → 기대값 달성
```

**시너지**: PHASE 6이 정의한 정답을 PHASE 7이 구현

---

## 🚀 **9. 구현 난이도 분석**

### 9.1 **복잡도 매트릭스**

| 항목 | 난이도 | 개발량 | 위험도 | 영향도 |
|---|---|---|---|---|
| EvidenceGate | 중간 | 500줄 | 중간 | **높음** |
| Category Classifier | 중간 | 300줄 | 낮음 | 중간 |
| Category Metadata | 낮음 | 200줄 | 낮음 | 중간 |
| Vector Threshold | 중간 | 300줄 | 중간 | 중간 |
| Answer Policy | 낮음 | 200줄 | 낮음 | 중간 |
| Feedback Loop | 높음 | 800줄 | 높음 | 낮음 |
| Grounding Verifier | 높음 | 600줄 | 중간 | 낮음 |

**전체**: ~3,000줄 (중규모 구현)

### 9.2 **리스크 분석**

```
높은 리스크:
  1. Feedback Loop 자동화 (복잡한 변환 로직)
  2. Vector Threshold Calibration (데이터 필요)
  3. Grounding Verifier (Citation 추출 정확도)

중간 리스크:
  1. Category Metadata 일관성 (문서 재정렬 필요)
  2. EvidenceGate 정책 일관성 (예외 케이스)

낮은 리스크:
  1. Answer Policy 추가 (명확한 로직)
  2. Category Classifier (기존 기술)
```

---

## 💰 **10. 비용-효과 분석**

### 10.1 **투자 대비 효과**

| 지표 | 투자 | 효과 | ROI |
|---|---|---|---|
| 개발 시간 | 2-3주 | 정확도 +36%p | **매우 높음** |
| 코드 복잡도 | 중간 | 신뢰도 +50% | **높음** |
| 유지보수 비용 | 중간 | 오류 -90% | **높음** |

### 10.2 **단계별 투자**

```
1단계 (필수, P0): 1주
  EvidenceGate + Category Mismatch
  → 정확도: 31.25% → 55% (+23.75%p 예상)

2단계 (권장, P1): 1주
  Vector Threshold Calibration
  → 정확도: 55% → 67% (+12%p 예상)

3단계 (선택, P2/P3): 2주
  Feedback Loop + 온톨로지 강화
  → 정확도: 67% → 75%+ (+8%p 예상)

총 투자: 3-4주 / 효과: +44%p
```

---

## ⚠️ **11. 주의사항 및 의존성**

### 11.1 **절대 원칙**

```
3가지 Non-Negotiable Rules:

1. 근거가 없으면 답하지 않는다.
   → EvidenceGate가 차단

2. 관련 카테고리 문서가 아니면 답하지 않는다.
   → Category 일치 필수

3. 온톨로지 관계가 필요한 질문은 
   벡터 검색 일반론으로 때우지 않는다.
   → Ontology-aware routing 필수
```

**해석**: 정책적 제약 (기술보다 의지의 문제)

### 11.2 **선행 작업**

```
필수 선행:
  1. ✅ PHASE 6 정답 보정 완료 (STD-S 정답 정의)
  2. ❓ Document Category Metadata (진행 상태 불명)
  3. ❓ Vector Score Semantics (검증 필요)

진행 필요:
  1. Category 메타데이터 생성 (documents + chunks)
  2. Vector score 분포 분석 (threshold 설정용)
  3. Question Classifier 검증 (카테고리 분류 정확도)
```

---

## 🎓 **12. 기술 평가**

### 12.1 **제안의 타당성**

```
✅ 근거 중심 설계
   문제: 범위 외 답변
   → 원인: 근거 없이도 답변 생성
   → 해결: 근거 기반 답변 강제

✅ 계층적 검증
   설계 → 모듈 → 정책 → 실행
   (추상도 높음)

✅ 정량화된 목표
   90%, 67.50%, 10% 이하
   (측정 가능)

⚠️ 데이터 의존성
   category metadata, vector score distribution
   (선행 작업 필요)

⚠️ 자동화 복잡도
   answer_key_feedback → policy 변환
   (시간 소요 예상)
```

### 12.2 **혁신도 평가**

```
신규성: ⭐⭐⭐ (EvidenceGate + Feedback Loop 모두 새로움)
실용성: ⭐⭐⭐ (명확한 구현 경로)
확장성: ⭐⭐ (P2/P3는 장기 계획)
단순성: ⭐⭐ (3,000줄 규모)
```

---

## 📊 **13. Claude의 PHASE 6 vs Codex의 PHASE 7**

### 13.1 **관점 차이**

| 관점 | Claude PHASE 6 | Codex PHASE 7 |
|---|---|---|
| **시점** | 평가 후 (Offline) | 서빙 중 (Online) |
| **대상** | 기대값 (정답) | 실제값 (시스템 동작) |
| **메커니즘** | 채점 기준 변경 | 생성 원천 차단 |
| **초점** | 측정의 정확성 | 답변의 신뢰성 |

### 13.2 **보완 구조**

```
PHASE 6 (Claude):
  Q: STD-S-01?
  A: "RAG는..."
  Expected: "관련 없습니다" (정의됨)
  Score: 0% (정답과 불일치)

    ↓ 피드백

PHASE 7 (Codex):
  Q: STD-S-01?
  → EvidenceGate 검증
  → Category mismatch 감지
  A: "관련 없습니다" (자동 생성)
  Expected: "관련 없습니다" (일치)
  Score: 100% (정답과 일치)
```

**결론**: 상호 보완적 설계

---

## 🎯 **14. 최종 평가 및 권장사항**

### 14.1 **강점**

```
✅ 명확한 문제 정의
   Snowflake 0% → 90%+ 개선 목표

✅ 체계적인 솔루션
   EvidenceGate + Answer Policy + Feedback Loop

✅ 단계별 구현 경로
   P0/P1/P2/P3로 우선순위 명확

✅ 정량화된 성공 기준
   수용 기준 명확함

✅ 아키텍처 개선
   프롬프트 의존 → 정책 기반으로 전환
```

### 14.2 **약점**

```
⚠️ 데이터 준비 필요
   - Category metadata 생성 필요
   - Vector score distribution 분석 필요
   - Threshold calibration 필수

⚠️ 자동화 복잡도
   - answer_key_feedback 변환 로직 복잡
   - Feedback type 분류 정확도 필요

⚠️ 온톨로지 확장
   - Policy를 온톨로지로 표현 시 설계 필요
   - 관계 정의 필요

⚠️ 검증 전략
   - Grounding verification 구현 복잡
   - Citation 추출 정확도 미지수
```

### 14.3 **권장 실행 전략**

```
1단계 (1주):
  ✅ PHASE 6 완료 (정답 정의)
  ✅ EvidenceGate 구현 (핵심)
  ✅ Category Metadata 추가
  → 정확도 예상: +23%p

2단계 (1주):
  ✅ Vector Threshold Calibration
  ✅ Category Classifier 강화
  → 정확도 예상: +12%p (누적 35%p)

3단계 (2주):
  ✅ Answer Policy 세분화
  ✅ Feedback Loop 초안
  ✅ STD-S 회귀 테스트
  → 정확도 예상: +8%p (누적 43%p)

4단계 (선택, 향후):
  ✅ Grounding Verifier
  ✅ Feedback 자동화
  ✅ 온톨로지 강화
```

---

## 📈 **15. 기대 효과 시뮬레이션**

### 15.1 **정확도 개선 예측**

```
현재 (PHASE 6 후):
  Ontology:    75.62%
  Advanced RAG: 62.5% (추정)
  Snowflake:   0% (범위 외 답변 중)
  ─────────────────
  전체:        31.25% (8개 Snowflake 오류)

PHASE 7 P0 후 (1주):
  Ontology:    75.62% (유지) ✓
  Advanced RAG: 62.5% (유지) ✓
  Snowflake:   55% (선별적 개선)
  ─────────────────
  전체:        55% (+23.75%p)

PHASE 7 P1 후 (2주):
  Ontology:    75.62% (유지) ✓
  Advanced RAG: 62.5% (유지) ✓
  Snowflake:   85% (대폭 개선)
  ─────────────────
  전체:        67% (+35.75%p) ← 목표: 67.50%

PHASE 7 P2/P3 후 (4주):
  Ontology:    76%+ (미소 개선)
  Advanced RAG: 65%+ (미소 개선)
  Snowflake:   92%+ (거의 달성)
  ─────────────────
  전체:        75%+ (+43.75%p)
```

### 15.2 **리스크 시나리오**

```
Best Case (계획 대로):
  67.50% 달성 (P0/P1 후) ✓
  92%+ Snowflake 달성 (P2 후) ✓

Normal Case (10% 지연):
  65% 달성 (P0/P1 후, 목표 미달)
  85% Snowflake 달성

Worst Case (25% 지연):
  55% 달성 (P0만 후, 목표 미달)
  Threshold calibration 실패

Risk Mitigation:
  - P0 (필수) 우선 → 최소 23%p 보장
  - Vector score 미리 검증 → P1 리스크 감소
  - Fallback: 기존 프롬프트 강화 (보조 수단)
```

---

## 🔄 **16. Codex 계획과 Claude 작업의 연계**

### 16.1 **시간축 연계**

```
2026-06-07:
  ✅ Claude PHASE 6 완료 (정답 보정)
  → STD-S-01~08: "관련 없습니다" 정답 정의

2026-06-10 ~ 06-17 (1주):
  → Codex PHASE 7 P0 구현
  → EvidenceGate + Category Mismatch

2026-06-17 ~ 06-24 (2주):
  → Codex PHASE 7 P1 구현
  → Vector Threshold + Category Classifier

2026-06-24 ~ 07-08 (2주):
  → Codex PHASE 7 P2/P3 구현
  → Feedback Loop + Ontology

2026-07-08:
  → PHASE 7 완료
  → Team4 정확도 67% 이상 달성 예상
```

### 16.2 **의존성 관리**

```
PHASE 6 → PHASE 7 의존:
  ✅ 정답 정의 (STD-S)
  ✅ 평가 기준 명확화
  ✅ Category 식별 (Snowflake = out-of-domain)

PHASE 7 → 향후 작업:
  → 정책 기반 아키텍처 완성
  → Feedback 자동화
  → 온톨로지 확장
```

---

## ✅ **최종 결론**

### 개요
Codex의 PHASE 7은 **Claude의 PHASE 6과 완벽하게 보완되는 온라인(실행) 레벨 개선 계획**입니다.

### 평가 점수

| 항목 | 점수 | 설명 |
|---|---|---|
| **타당성** | ⭐⭐⭐⭐⭐ | 근본적인 문제 인식 및 해결책 우수 |
| **완전성** | ⭐⭐⭐⭐ | P0~P3로 단계적 계획, 미래 확장성 있음 |
| **실현성** | ⭐⭐⭐⭐ | 3-4주 일정, 기술 검증 가능 |
| **혁신성** | ⭐⭐⭐ | EvidenceGate, Feedback Loop 신규 |
| **위험성** | ⭐⭐ | P0(필수) 낮은 리스크, P2/P3 높은 복잡도 |

### 최종 권장
```
✅ PHASE 7 전략 승인
→ 목표: 67.50%+ 달성 가능성 높음 (P0/P1 후)
→ 추가 목표: 75%+ 달성 가능성 중간 (P2/P3 후)

✅ 우선순위
→ P0(EvidenceGate) 즉시 착수
→ P1(Calibration) 병렬 진행
→ P2/P3는 여유 있을 때

⚠️ 선행 작업
→ Category metadata 생성
→ Vector score 분석
→ Question classifier 검증
```

---

**분석 완료**  
**권장 조치**: Codex와 협력하여 P0/P1 우선 구현  
**예상 완료**: 2026-06-24 (3주)  
**최종 정확도**: 67% 이상 (목표) → 75% 이상 (확대 목표)
