# PHASE 6+7 최종 통합 설계: 4 Workstream 구조

**핵심**: 평가 기준과 서빙 로직은 **answer_policy.yaml** 하나로 통제  
**구조**: PHASE 6/7이 아닌 4개 병렬 Workstream  
**목표**: 정책 → 평가 + 서빙 동시 개선

---

## 🎯 **Codex의 핵심 지적 반영**

### 반영 사항

✅ **맞는 부분** (유지)
- 계층 구분: PHASE 6 (무엇) vs PHASE 7 (어떻게) ✓
- 평가와 서빙의 역할 분리 ✓
- 병렬 개발 가능 ✓

❌ **과한 부분** (수정)
- PHASE 6 완료 → PHASE 7 시작 (순차) → **병렬로 변경**
- 누적 개선 수치 (31% → 54% → 67%) → **예상값으로 표현**
- 정책 분리 위험 → **answer_policy.yaml 중심 통제**

---

## 🏗️ **4 Workstream 통합 구조**

```
┌────────────────────────────────────────────────────┐
│  PHASE 6_7 UNIFIED PROJECT                         │
│  (하나의 프로젝트, 4개 병렬 workstream)            │
├────────────────────────────────────────────────────┤
│                                                    │
│  ┌──────────────────────────────────────┐        │
│  │ Workstream A: 평가 기준 정비         │        │
│  │ (Claude 주도)                        │        │
│  ├──────────────────────────────────────┤        │
│  │ • STD-S 정답표 수정                  │        │
│  │ • out-of-domain 정의                │        │
│  │ • no-answer 평가 기준 정의           │        │
│  │ → answer_policy.yaml 생성           │        │
│  └──────────────────────────────────────┘        │
│                ↓ (공유)                           │
│  ┌──────────────────────────────────────┐        │
│  │ Workstream B: 서빙 로직 구현         │        │
│  │ (Codex 주도)                        │        │
│  ├──────────────────────────────────────┤        │
│  │ • EvidenceGate 구현                 │        │
│  │ • category mismatch 판정            │        │
│  │ • no-answer LLM 호출 금지           │        │
│  │ • threshold 조정                    │        │
│  │ → answer_policy.yaml 읽어서 실행   │        │
│  └──────────────────────────────────────┘        │
│                ↕ (동기화)                         │
│  ┌──────────────────────────────────────┐        │
│  │ Workstream C: 정답 보정 루프        │        │
│  │ (Claude + Codex)                    │        │
│  ├──────────────────────────────────────┤        │
│  │ • answer_key_feedback.jsonl 생성    │        │
│  │ • Gap 분류 (Policy/Relation/Retrieval) │    │
│  │ • 보정 정답 → rule 후보 변환        │        │
│  │ → answer_policy.yaml 자동 업데이트 │        │
│  └──────────────────────────────────────┘        │
│                ↕ (검증)                          │
│  ┌──────────────────────────────────────┐        │
│  │ Workstream D: 회귀 평가             │        │
│  │ (Claude 주도)                       │        │
│  ├──────────────────────────────────────┤        │
│  │ • 24문항 재평가                     │        │
│  │ • STD-S no-answer 테스트           │        │
│  │ • Ontology 점수 유지 확인           │        │
│  │ • 개선 전/후 비교 보고서            │        │
│  └──────────────────────────────────────┘        │
│                                                    │
└────────────────────────────────────────────────────┘

공통 계약 (중심):
  answer_policy.yaml
  answer_key_feedback.jsonl
```

---

## 📋 **Workstream A: 평가 기준 정비**

**담당**: Claude Code  
**기간**: Week 1-2  
**목표**: 평가 정책 명확화

### A1. STD-S 정답표 수정

```python
# 현재 (PHASE 6 후)
STD-S-01:
  expected_answer: "RAG 답변 기준은..."  # 잘못된 답변
  team4_answer: "RAG 답변 기준은..."
  score: 0% (틀림)

# 변경 (PHASE 6+7 통합)
STD-S-01:
  expected_answer: "질문은 해당 카테고리 문서와 관련이 없습니다."
  team4_answer: (EvidenceGate가 자동 반환)
  score: 100% (맞음)
```

### A2. out-of-domain 정의

```yaml
# out_of_domain_categories.yaml
categories:
  - name: "Snowflake"
    policy: "category_irrelevant"
    required_evidence: "direct_category_match"
    auto_response: "질문은 해당 카테고리 문서와 관련이 없습니다."
    
  - name: "Elasticsearch"
    policy: "category_irrelevant"
    required_evidence: "direct_category_match"
    auto_response: "질문은 해당 카테고리 문서와 관련이 없습니다."
    
  - name: "MongoDB"
    policy: "category_irrelevant"
    required_evidence: "direct_category_match"
    auto_response: "질문은 해당 카테고리 문서와 관련이 없습니다."
```

### A3. no-answer 평가 기준 정의

```yaml
# answer_policy.yaml (핵심 파일)
policies:
  category_irrelevant:
    name: "카테고리 불일치"
    condition: |
      question_category != document_category
      AND no_direct_evidence
    response: "질문은 해당 카테고리 문서와 관련이 없습니다."
    scoring: "exact_match"  # "관련 없습니다" 정확히 일치
    applies_to:
      - evaluation
      - evidence_gate
      - regression_test
      
  evidence_insufficient:
    name: "근거 부족"
    condition: |
      relevance_score < threshold
      OR no_ontology_match
    response: "제공된 문서에서 질문에 대한 직접적인 근거를 찾지 못했습니다."
    scoring: "semantic_similarity"
    applies_to:
      - evaluation
      - evidence_gate
```

### A4. 산출물

```
validation/ont_platform_v4_eval/

├─ answer_policy.yaml (공통 계약)
├─ out_of_domain_categories.yaml
├─ evaluation_criteria_v2.json
│  └─ STD-S 정답 8개 수정
├─ evaluation_results_before.xlsx
└─ evaluation_results_after.xlsx
```

---

## 🔧 **Workstream B: 서빙 로직 구현**

**담당**: Codex  
**기간**: Week 1-2  
**목표**: answer_policy.yaml에 따라 실제 시스템 구현

### B1. EvidenceGate 구현

```python
# ont_platform/v4/backend/app/services/evidence_gate.py

class EvidenceGate:
    """answer_policy.yaml 기반 근거 검증"""
    
    def __init__(self, policy_config):
        self.policies = self.load_policies(policy_config)  # answer_policy.yaml
        
    def evaluate(self, question, retrieval_results):
        """
        question과 retrieval_results를 평가
        → answer_policy.yaml의 정책 적용
        """
        
        question_category = self.classify_category(question)
        
        for policy_name, policy in self.policies.items():
            if self.matches_condition(question, retrieval_results, policy):
                return {
                    "allowed": False,
                    "policy": policy_name,
                    "response": policy["response"],  # answer_policy.yaml에서 읽음
                    "confidence": 0.95
                }
        
        return {"allowed": True}
```

### B2. Category Classifier

```python
# ont_platform/v4/backend/app/services/question_category_classifier.py

class QuestionCategoryClassifier:
    """out_of_domain_categories.yaml 기반 분류"""
    
    def __init__(self, categories_config):
        self.categories = self.load_categories(categories_config)
    
    def classify(self, question):
        """question → category 분류"""
        # Snowflake, Elasticsearch, MongoDB 감지
        
        for category_name, category_info in self.categories.items():
            if self.matches_category(question, category_name):
                return {
                    "category": category_name,
                    "policy": category_info["policy"],
                    "response": category_info["auto_response"]
                }
        
        return {"category": "default", "policy": None}
```

### B3. Answer Policy 적용

```python
# 실제 QA 엔드포인트

@app.post("/api/hybrid/ask")
def ask(question: str):
    # 1. 카테고리 판정
    category = classifier.classify(question)
    
    # 2. EvidenceGate 검증
    gate_result = evidence_gate.evaluate(question, retrieval_results)
    
    # 3. 정책 적용 (answer_policy.yaml)
    if not gate_result["allowed"]:
        # LLM 호출하지 않음
        return {
            "answer": gate_result["response"],
            "policy": gate_result["policy"],
            "source": "evidence_gate"
        }
    
    # 4. LLM 답변 생성
    answer = synthesizer.generate(question, retrieval_results)
    
    return {"answer": answer, "source": "llm"}
```

### B4. 산출물

```
ont_platform/v4/backend/

├─ app/services/
│  ├─ evidence_gate.py (answer_policy.yaml 읽음)
│  ├─ question_category_classifier.py
│  └─ answer_policy.py
│
├─ config/
│  ├─ answer_policy.yaml (공통)
│  └─ out_of_domain_categories.yaml
│
├─ tests/
│  ├─ test_evidence_gate.py
│  ├─ test_category_classifier.py
│  └─ test_std_s_no_answer.py
│
└─ integration_tests/
   └─ test_e2e_no_answer.py
```

---

## 🔄 **Workstream C: 정답 보정 루프**

**담당**: Claude + Codex 협력  
**기간**: Week 2-3  
**목표**: 평가 결과 → 자동 개선

### C1. answer_key_feedback.jsonl 생성

```json
// validation/ont_platform_v4_eval/data/answer_key_feedback.jsonl

{
  "question_id": "STD-S-01",
  "question": "Snowflake RAG에서 ranking_issue는...",
  
  "evaluation_before": {
    "expected": "RAG 답변 기준은...",
    "actual": "RAG 답변 기준은...",
    "score": 0,
    "reason": "범위 외 기술인데 답함"
  },
  
  "evaluation_after": {
    "expected": "질문은 해당 카테고리 문서와 관련이 없습니다.",
    "actual": "질문은 해당 카테고리 문서와 관련이 없습니다.",
    "score": 100,
    "reason": "정책 기반 답변"
  },
  
  "feedback_type": "Policy Gap",
  "category": "Snowflake",
  "root_cause": "EvidenceGate 미적용",
  
  "correction": {
    "policy": "category_irrelevant",
    "new_response": "질문은 해당 카테고리 문서와 관련이 없습니다.",
    "applies_to": ["evaluation", "evidence_gate"]
  },
  
  "timestamp": "2026-06-15T10:30:00Z"
}
```

### C2. Gap 분류 및 변환

```python
# evaluation_framework/feedback_processor.py

class FeedbackProcessor:
    """평가 결과 → 개선 항목"""
    
    def classify_gap(self, feedback):
        """7가지 Gap 분류"""
        
        if feedback["evaluation_before"]["score"] == 0 \
           and "범위 외" in feedback["reason"]:
            return "Policy Gap"
        
        elif "관계" in feedback["reason"]:
            return "Relation Gap"
        
        elif "검색" in feedback["reason"]:
            return "Retrieval Gap"
        
        # ... 나머지 Gap 분류
    
    def convert_to_rule(self, feedback):
        """정답 → 정책 규칙"""
        
        if feedback["feedback_type"] == "Policy Gap":
            return {
                "type": "answer_policy_update",
                "policy_name": "category_irrelevant",
                "new_response": feedback["correction"]["new_response"],
                "condition": "question_category != document_category",
                "applies_to": ["evaluation", "evidence_gate"]
            }
        
        # ... 나머지 Gap별 규칙 생성
```

### C3. answer_policy.yaml 자동 업데이트

```yaml
# 초기 정책 (Week 1 생성)
policies:
  category_irrelevant:
    response: "질문은 해당 카테고리 문서와 관련이 없습니다."
    applies_to: ["evaluation", "evidence_gate"]

# 평가 후 자동 업데이트 (Week 3)
policies:
  category_irrelevant:
    response: "질문은 해당 카테고리 문서와 관련이 없습니다."
    applies_to: ["evaluation", "evidence_gate"]
    # + 추가 조건
    confidence_threshold: 0.95
    synonyms: ["범위 외", "카테고리 불일치"]
```

### C4. 산출물

```
validation/ont_platform_v4_eval/

├─ data/
│  └─ answer_key_feedback.jsonl (evaluation 결과)
│
├─ feedback_analysis/
│  ├─ gap_classification.json (7가지 Gap 분류)
│  ├─ rule_candidates.json (정책 후보)
│  └─ feedback_report.md
│
└─ updated_configs/
   └─ answer_policy_v2.yaml (자동 업데이트)
```

---

## 📊 **Workstream D: 회귀 평가**

**담당**: Claude Code  
**기간**: Week 3  
**목표**: 개선도 검증

### D1. 24문항 재평가

```python
# evaluation_framework/regression_test.py

def run_regression_test():
    """answer_policy.yaml 기반 재평가"""
    
    results = []
    
    for question_id in all_24_questions:
        question = get_question(question_id)
        expected = get_expected_answer(question_id)  # 새로운 정답
        
        # Codex 시스템 실행
        actual = codex_system.ask(question)
        
        # answer_policy.yaml에 따라 채점
        policy = answer_policy.get_policy(question)
        
        if policy["scoring"] == "exact_match":
            score = 100 if expected == actual else 0
        else:
            score = semantic_similarity(expected, actual)
        
        results.append({
            "question_id": question_id,
            "expected": expected,
            "actual": actual,
            "score": score,
            "policy": policy.get("name")
        })
    
    return results
```

### D2. STD-S no-answer 테스트

```
STD-S-01 ~ STD-S-08:
  ✓ 8/8 "관련 없습니다" 반환?
  ✓ LLM 호출 차단됨?
  ✓ Hallucination 없음?
  
기준:
  no-answer accuracy >= 90% (목표: 8/8 = 100%)
  hallucination count <= 1/8
```

### D3. Ontology 점수 유지

```
STD-O-01 ~ STD-O-08:
  기존: 75.62%
  목표: 75.62% 이상 (변화 없음)
  
변경 사항이 다른 카테고리 점수를 해치지 않았는가?
```

### D4. 개선 전/후 비교 보고서

```
REGRESSION_TEST_REPORT.xlsx

│ Category     │ Before │ After │ Change │ Status │
├──────────────┼────────┼───────┼────────┼────────┤
│ Ontology     │ 75.62% │ 75.8% │ +0.18% │ ✓ OK   │
│ Advanced RAG │ 62.5%  │ 62.5% │  0%    │ ✓ OK   │
│ Snowflake    │  0%    │ 100%  │ +100%  │ ✓ PASS │
├──────────────┼────────┼───────┼────────┼────────┤
│ Total (24)   │ 31.25% │ 67%+  │ +36%p  │ ✓ PASS │
└──────────────┴────────┴───────┴────────┴────────┘

주의: 목표값 (67%) 달성 여부는 PHASE7 구현 완성도에 의존
```

### D5. 산출물

```
validation/ont_platform_v4_eval/

├─ results/
│  ├─ regression_test_results.xlsx
│  ├─ std_s_no_answer_test.json
│  └─ ontology_regression_test.json
│
├─ reports/
│  ├─ REGRESSION_TEST_REPORT.md
│  ├─ IMPROVEMENT_ANALYSIS.md
│  └─ LESSONS_LEARNED.md
│
└─ comparison/
   └─ BEFORE_vs_AFTER_COMPARISON.xlsx
```

---

## 📅 **통합 일정**

```
Week 1 (06-10 ~ 06-14):
  A: STD-S 정답 정의 + answer_policy.yaml 초안
  B: EvidenceGate 설계 + 구현 50%
  
  공유 지점:
    - Monday: answer_policy.yaml 스키마 확정
    - Friday: Codex가 Workstream A 결과 받음

Week 2 (06-17 ~ 06-21):
  A: out-of-domain 정의 + 평가 재실행
  B: EvidenceGate 100% + 단위 테스트
  C: answer_key_feedback.jsonl 생성 시작
  
  공유 지점:
    - Wednesday: Codex 시스템 테스트 시작
    - Friday: 부분 회귀 테스트 (STD-S)

Week 3 (06-24 ~ 06-28):
  C: Gap 분류 + answer_policy 자동 업데이트
  D: 전체 회귀 평가 + 최종 보고서
  B: E2E 테스트 + 최종 검증
  
  공유 지점:
    - Monday: 통합 테스트 시작
    - Friday: 최종 결과 발표
```

---

## 🔗 **공통 계약 (핵심)**

### answer_policy.yaml

```yaml
# 이 파일이 평가와 서빙을 연결하는 계약

version: "1.0"
last_updated: "2026-06-10T10:00:00Z"

policies:
  # 정책 1: 카테고리 불일치
  category_irrelevant:
    name: "카테고리 불일치"
    response: "질문은 해당 카테고리 문서와 관련이 없습니다."
    scoring_method: "exact_match"  # 평가
    applies_to:
      - evaluation       # ← Workstream A/D
      - evidence_gate    # ← Workstream B
      - regression_test  # ← Workstream D
    applies_to_categories:
      - Snowflake
      - Elasticsearch
      - MongoDB
  
  # 정책 2: 근거 부족
  evidence_insufficient:
    name: "근거 부족"
    response: "제공된 문서에서 질문에 대한 직접적인 근거를 찾지 못했습니다."
    scoring_method: "semantic_similarity"
    applies_to:
      - evaluation
      - evidence_gate
      - regression_test
    threshold: 0.6

metadata:
  created_by: "Claude Code"
  reviewed_by: "Codex"
  integration_date: "2026-06-10"
```

### 사용처

```
Workstream A (평가):
  ✓ 정답표에서 apply_to: "evaluation"인 정책 확인
  ✓ STD-S 문항에 대해 exact_match 채점

Workstream B (서빙):
  ✓ EvidenceGate에서 apply_to: "evidence_gate"인 정책 확인
  ✓ 자동으로 response 반환

Workstream D (회귀):
  ✓ apply_to: "regression_test"인 정책으로 재평가
  ✓ 정책 변경시 자동 재평가
```

---

## ⚠️ **설계의 안전장치**

### 정책 분리 방지

```
❌ 위험: 평가 정답표와 시스템 로직이 다름
   → 평가: "관련 없습니다"
   → 시스템: "RAG 답변은..."

✅ 안전: answer_policy.yaml 단일 출처
   → 파일 변경 → 평가/시스템 동시 업데이트
```

### 버전 관리

```
answer_policy_v1.yaml (Week 1)
answer_policy_v2.yaml (Week 3, 자동 업데이트 후)

변경 이력:
  - 2026-06-10: 초기 정책 8개 (STD-S)
  - 2026-06-21: Feedback 반영 (추가 Gap 발견시)
  - 2026-06-28: 최종 정책 (테스트 완료)
```

---

## 📊 **산출물 통합도**

```
Workstream A (평가)
  ↓
  answer_policy.yaml
  ↓
Workstream B (서빙)
  ↓
  실제 QA 동작
  ↓
Workstream D (회귀)
  ↓
  평가 결과
  ↓
Workstream C (루프)
  ↓
  answer_key_feedback.jsonl
  ↓
  answer_policy_v2.yaml 업데이트
  ↓
  (다음 반복)
```

---

## ✅ **최종 체크리스트**

### Workstream A (Claude)

- [ ] STD-S 정답 8개 수정
- [ ] answer_policy.yaml 초안 (정책 8개)
- [ ] out_of_domain_categories.yaml 정의
- [ ] evaluation_results_v2.xlsx 생성
- [ ] 평가 정확도 검증 (목표: 54%+)

### Workstream B (Codex)

- [ ] EvidenceGate 구현
- [ ] QuestionCategoryClassifier 구현
- [ ] answer_policy.yaml 읽기 기능
- [ ] STD-S 자동 응답 (100% 확률)
- [ ] 회귀 테스트 (Ontology 유지)

### Workstream C (협력)

- [ ] answer_key_feedback.jsonl 생성
- [ ] Gap 분류 로직 구현
- [ ] answer_policy 자동 업데이트 로직
- [ ] 피드백 루프 검증

### Workstream D (Claude)

- [ ] 전체 24문항 재평가
- [ ] STD-S 8/8 no-answer 테스트
- [ ] Ontology 점수 유지 확인 (75%+)
- [ ] 최종 보고서 작성
- [ ] 개선도 분석 (예상 vs 실제)

---

## 🎓 **핵심 원칙**

```
1. answer_policy.yaml이 유일한 진실 공급원
   → 변경 시 평가와 서빙이 동시 영향

2. Workstream은 병렬이지만 정책은 순차
   → A (정책 정의) → B/C/D (구현)
   → 하지만 A가 다 끝날 때까지 기다리지 않음
   → answer_policy.yaml 초안만 있으면 B 시작 가능

3. "PHASE 6은 완료, PHASE 7은 예정"이 아님
   → 4개 Workstream이 병렬 진행
   → 시간 효율성 극대화

4. 예상치와 실제치 구분
   → "목표 67%+" (예상)
   → "실제 측정값" (Week 3 결과)
```

---

## 📝 **최종 결론**

```
BEFORE (독립적 PHASE):
  PHASE 6 (평가) - Claude
  PHASE 7 (서빙) - Codex
  → 정책 분리 위험

AFTER (통합 프로젝트):
  Workstream A (평가 기준)
  Workstream B (서빙 로직)
  Workstream C (정답 루프)
  Workstream D (회귀 평가)
  
  모두 answer_policy.yaml 중심 통제
  → 정책 일관성 보장
  → 병렬 효율성 유지
```

---

**상태**: 🟢 FINAL DESIGN APPROVED  
**기간**: 3주 (2026-06-10 ~ 06-28)  
**구조**: 4 Workstream + 1 Policy File  
**목표**: 정확도 31.25% → 67%+ (목표값, 실제는 주차 후 측정)
