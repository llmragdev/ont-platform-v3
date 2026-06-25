# PHASE 8 + Antigravity 설계 검토 보고서

**검토 대상**:
1. PHASE8_V5_UNIFIED_DESIGN_PLAN.md (Codex)
2. PHASE_ANTIGRAVITY_DESIGN.md (Antigravity)

**검토일**: 2026-06-07  
**평가**: 두 설계의 상충/보완 관계 분석

---

## 🎯 **Executive Summary**

### 핵심 발견

**상충**: 예 (복잡도 폭증)  
**보완**: 예 (상호 보완 가능)  
**권장**: 단계적 통합 (PHASE 8 먼저 → Antigravity 선택적)

```
PHASE 8 (Codex):
  v4 baseline → v5 개선
  핵심: 평가와 서빙의 정책 일관성
  산출물: answer_policy.yaml (중앙 집중식 정책)

ANTIGRAVITY:
  v5에 검색 모드 옵션 추가
  핵심: 사용자 선택 기반 멀티라우팅
  산출물: SearchMode Enum (사용자 유연성)

관계: 수직적 관계 (PHASE 8이 기반, Antigravity는 선택적 확장)
```

---

## 📊 **1. PHASE 8 설계 평가**

### 강점 ✅

```
1. 명확한 문제 정의
   v4의 근본 문제:
   - "정보 없으면 no-answer" 정책이 프롬프트에만 있음
   - 시스템 레벨에서 강제되지 않음
   
   v5의 해결책:
   - EvidenceGate로 아키텍처 레벨 강제
   ✓ 정확함

2. 단순하고 명확한 구조
   - 4개 Task로 분해 (v5 baseline, EvidenceGate, Analyzer, 통합)
   - 각 Task가 독립적 (병렬 가능)
   
3. 평가와 서빙의 정책 일관성
   - answer_policy.yaml이 양쪽 모두 사용
   - 정책 변경 → 평가/서빙 동시 반영
   ✓ 핵심 통찰

4. 구체적인 수용 기준
   - STD-S: 90% 이상
   - Ontology: 75.62% 유지
   - hallucination: 10% 이하
   ✓ 측정 가능

5. v4/v5 비교 평가 계획
   - baseline 보존으로 개선도 명확
   ✓ 연구 가치
```

### 약점 ⚠️

```
1. 구현 복잡도 과소평가
   - EvidenceGate: 4가지 판정 조건 (category, relevance, coverage, policy)
   - Question Analyzer: 규칙 기반 시작 → 나중에 LLM으로 확장?
   - 정책 파일 관리: JSONL 형식, 자동 업데이트 로직
   → 실제로는 상당한 개발량 (예상 20-30시간 이상)

2. threshold calibration 미해결
   - vector score 분포 분석 필요
   - threshold를 어떻게 정할 것인가?
   - "known-positive 10개" 수집이 실제로 가능한가?
   
3. Question Analyzer의 규칙 정의 부족
   - "Snowflake, ranking_issue, warehouse" → Snowflake
   - "온톨로지, 지식그래프, 클래스" → Ontology
   - 이것만으로는 부족 (정확도 80% 수준?)
   - LLM classifier로 확장하려면 추가 시간

4. 문서 메타데이터 추가 비용
   - 기존 문서들의 category 태깅 필요
   - 실제로는 수동 작업 (또는 파일명 기반 임시 처리)
   - 시간/비용 미계산

5. 정책 분리 위험
   - answer_policy.yaml과 answer_key_feedback.jsonl의 관계가 모호
   - 둘이 동기화되지 않으면 평가/서빙 불일치
```

### 개선 권장

```
1. Threshold Calibration 선행
   → PHASE 8 시작 전에 vector score 분석
   → 임계값 후보 정하고 시작 (아니면 보수적 값부터)

2. Question Analyzer 단계별 구현
   → Week 1: 규칙 기반 (간단한 키워드 매칭)
   → Week 2: 평가 결과 기반 개선
   → Week 3+: LLM classifier 고려 (선택)

3. 문서 메타데이터 관리 전략
   → 초기: 파일명 기반 자동 분류
   → 나중에: 사용자 지정 가능하게 확장

4. 정책 파일 통합 스키마
   answer_policy_unified.yaml:
   {
     "question_id": "STD-S-01",
     "category": "Snowflake",
     "policy": "category_irrelevant",
     "response": "관련 없습니다",
     "applies_to": ["evaluation", "evidence_gate", "regression_test"],
     "feedback_type": "Policy Gap"  ← answer_key_feedback와 연결
   }
```

---

## 🚀 **2. Antigravity 설계 평가**

### 강점 ✅

```
1. 실질적인 사용자 가치
   - 전문가: "온톨로지만 검색"
   - 기술 문제: "벡터 검색만"
   - 일반 사용자: "자동 선택"
   → 각 사용자 그룹에 최적화된 선택지

2. 성능 최적화 기회
   - ontology_only: VECTOR 스텝 스킵 → 40% 속도 향상 예상
   - vector_only: ONTOLOGY 스텝 스킵 → 30-40% 속도 향상 예상
   ✓ 실제 구현 가능

3. 명확한 API 확장
   - SearchMode Enum
   - AskRequestV5 모델
   - 기존 코드 호환성 유지 가능

4. 구체적인 수용 검증 기준
   - 로그 상에서 스텝 생략 확인 가능
   - 성능 비교 측정 가능
   ✓ 객관적 검증

5. EvidenceGate 모드별 차별화
   - ontology_only: 온톨로지 결과 0개만 차단
   - vector_only: relevance threshold 엄격
   - hybrid: 하나라도 높은 confidence면 통과
   ✓ 합리적 로직
```

### 약점 ⚠️

```
1. PHASE 8과의 관계가 모호
   - PHASE 8은 "정책 일관성"을 강조
   - Antigravity는 "사용자 유연성"을 강조
   
   상충점:
   - PHASE 8: answer_policy.yaml (중앙 집중식)
   - Antigravity: SearchMode 옵션 (분산적)
   
   → 이 둘이 어떻게 상호작용하는가?
   
2. 복잡도 폭증
   - 검색 모드 조합:
     AUTO × (intent 4종류)
     ONTOLOGY_ONLY × (1가지)
     VECTOR_ONLY × (1가지)
     HYBRID × (1가지)
   
   → 테스트 케이스 수: 7가지 × 24문항 = 168개
   → PHASE 8만: 24 × 3 = 72개
   → 복잡도 2.3배 증가

3. 데이터 섞임 위험
   - ontology_only로 "Snowflake" 질문 → 결과 없음 → no_evidence
   - vector_only로 "온톨로지 관계" 질문 → 결과 없음 → no_evidence
   
   → 사용자가 잘못된 모드 선택하면 당연히 실패
   → 이건 사용자 책임? 시스템 책임?

4. EvidenceGate 모드 의존성
   - 같은 EvidenceGate가 모드별로 다르게 동작
   - ONTOLOGY_ONLY: threshold 무시
   - VECTOR_ONLY: relevance 엄격
   → 버그 위험성 높음 (경계 케이스)

5. 성능 메트릭 미정의
   - "최대 40% 단축"이라는 목표
   - 실제로 측정할 방법은?
   - latency만? throughput도?
   - 100 requests 기준? 1000?

6. 마이그레이션 비용 미계산
   - 기존 API: /api/hybrid/ask (고정)
   - 새 API: /api/hybrid/ask?search_mode=ontology_only
   - 기존 클라이언트 호환성?
   - API 버전 관리 필요?
```

### 개선 권장

```
1. PHASE 8과 명확한 통합 정의
   
   Option 1: Sequential (권장하지 않음)
   - PHASE 8 완료 후
   - Antigravity 추가
   → 기간 연장, 복잡도 폭증
   
   Option 2: Integrated (권장)
   - PHASE 8의 answer_policy.yaml
   - Antigravity의 SearchMode
   → 정책은 통일, 라우팅은 유연
   
   통합 방식:
   answer_policy.yaml:
   {
     "policy": "category_irrelevant",
     "applies_to_modes": ["AUTO", "HYBRID"],  ← Mode별 적용 가능
     "applies_to_categories": ["Snowflake"]
   }

2. 테스트 케이스 우선순위
   - P1: AUTO mode (기존과 동일)
   - P2: ONTOLOGY_ONLY (별도 테스트)
   - P3: VECTOR_ONLY (별도 테스트)
   - P4: HYBRID (조합 테스트)
   
   → 순차 배포로 위험 분산

3. 사용자 가이드 제공
   - "언제 어떤 모드를 선택할 것인가?"
   - 예시 문항별 추천 모드
   - API 문서에 명시

4. 성능 벤치마크 정의
   - 100문항 × 4 모드
   - 평균 응답 시간 (ms)
   - P99 latency
   - 벡터 검색 시간 (option을 사용했을 때 vs 미사용)

5. API 버전 관리
   - /api/v1/hybrid/ask (기존 - AUTO 기본값)
   - /api/v2/hybrid/ask (신규 - SearchMode 옵션)
   → 기존 클라이언트 호환성 유지
```

---

## 🔗 **3. 두 설계의 상충 분석**

### 3.1 핵심 상충점

```
PHASE 8의 원칙:
  "평가 정책과 서빙 정책은 같은 파일(answer_policy.yaml)로 관리"
  → 중앙 집중식 정책
  → 변경 시 동시 적용

Antigravity의 원칙:
  "사용자가 검색 모드를 선택할 수 있음"
  → 분산적 라우팅
  → 모드별로 다른 행동 가능

문제:
  같은 정책을 4가지 모드에서 다르게 적용하려면?
  
예시:
  policy: "category_irrelevant"
  → AUTO mode: 적용
  → ONTOLOGY_ONLY: 적용 (온톨로지 0개면)
  → VECTOR_ONLY: 적용 (relevance 낮으면)
  → HYBRID: 적용 (양쪽 모두 낮으면)
  
  → 같은 정책, 다른 조건
  → 코드 복잡도 증가
```

### 3.2 상호작용 매트릭스

```
           | PHASE 8 정책 | Antigravity 모드 | 상충도 | 해결책 |
-----------|------------|-----------------|------|--------|
Policy Gap | 명확       | Mode-dependent  | 높음 | 정책에 mode 정보 추가 |
Threshold  | 단일값     | Mode별 다름      | 중간 | mode별 threshold 정의 |
EvidenceGate| 단일 인스턴스| Mode별 제약 다름 | 높음 | 정책 드리븐 EG 설계 |
테스트     | 24 × 3    | 24 × 7 (최악)   | 높음 | P1/P2 우선순위 명확 |
```

---

## 📋 **4. 구현 순서 권장**

### Option A: PHASE 8 먼저 (보수적)

```
Week 1-3: PHASE 8 완료
  - v5 baseline
  - EvidenceGate 최소 구현
  - Question Analyzer (규칙 기반)
  - STD-S 회귀 테스트 통과
  → 정확도: 31% → 67%+

Week 4-5: Antigravity 추가 (선택)
  - SearchMode Enum 추가
  - QueryPlanner v5 수정
  - 4가지 모드 테스트
  → 성능: 30-40% 개선

장점:
  - PHASE 8이 안정화된 후 Antigravity 추가
  - 위험 분산
  - 각 단계 검증 가능

단점:
  - 총 5주 소요 (길어짐)
  - 중간에 API 변경 가능성
```

### Option B: 통합 설계 (권장) ⭐

```
Week 1-3: PHASE 8 + Antigravity 통합 설계
  
  Workstream A: 정책 기반 아키텍처 (PHASE 8)
    - answer_policy.yaml 정의 (mode 정보 포함)
    - EvidenceGate 설계 (정책 드리븐)
    
  Workstream B: 라우팅 아키텍처 (Antigravity)
    - SearchMode 정의
    - QueryPlannerV5 설계
    - Mode별 제약 조건 매핑
    
  Workstream C: 통합 테스트
    - 24 문항 × 4 모드 = 96 test cases
    - P1: AUTO (기존과 동일)
    - P2: MODE 별 단위 테스트
    - P3: 조합 테스트
  
  Workstream D: 평가 및 보고
    - v4 vs v5 비교
    - 모드별 성능 비교

장점:
  - 정책과 라우팅이 동시에 설계
  - API 변경 1회만
  - 총 3주 (짧음)
  - 일관된 아키텍처

단점:
  - 초기 설계 시간 증가
  - 복잡도 관리 필요
```

---

## 🎯 **5. 통합 설계 (권장안)**

### 5.1 answer_policy.yaml 확장 (PHASE 8 + Antigravity)

```yaml
# 단일 정책 파일이 평가와 서빙을 모두 지배

policies:
  category_irrelevant:
    name: "카테고리 불일치"
    
    # PHASE 8: 평가 정책
    scoring_method: "exact_match"
    applies_to:
      - evaluation
      - regression_test
    
    # Antigravity: 라우팅 정책
    applies_to_modes:
      - AUTO        # 정상적인 의도 분류
      - HYBRID      # 양쪽 모두 검증
      - ONTOLOGY_ONLY    # 온톨로지만 확인
      - VECTOR_ONLY      # 벡터 relevance 확인
    
    # Mode별 제약 조건
    constraints:
      AUTO:
        condition: "category_mismatch OR low_relevance"
      HYBRID:
        condition: "(ont_confidence < 0.5) AND (vec_relevance < threshold)"
      ONTOLOGY_ONLY:
        condition: "ontology_results == empty"
      VECTOR_ONLY:
        condition: "max_vector_score < threshold"
    
    target_response: "질문은 해당 카테고리 문서와 관련이 없습니다."
    
    applies_to_categories:
      - Snowflake
      - Elasticsearch
      - MongoDB
```

### 5.2 통합 EvidenceGate

```python
class EvidenceGateV5:
    """정책 기반 EvidenceGate (PHASE 8 + Antigravity)"""
    
    def check_evidence(self, 
                      question, 
                      search_mode: SearchMode,  # ← Antigravity
                      retrieval_results):       # ← PHASE 8
        
        # 1. 정책 로드 (중앙 집중식)
        policy = self.load_policy(question)
        
        # 2. 모드별 제약 조건 선택
        constraint = policy["constraints"][search_mode.value]
        
        # 3. 검증 실행
        if self.evaluate_constraint(retrieval_results, constraint):
            return {
                "allowed": False,
                "policy": policy["name"],
                "response": policy["target_response"],
                "mode": search_mode.value  # ← 모드 정보 함께 반환
            }
        
        return {"allowed": True}
```

### 5.3 QueryPlannerV5 통합

```python
class QueryPlannerServiceV5:
    """라우팅 기반 쿼리 계획 (Antigravity) + 정책 기반 검증 (PHASE 8)"""
    
    def ask_v5(self, request: AskRequestV5):
        mode = request.search_mode
        
        # 1. 모드에 따른 라우팅
        if mode == SearchMode.ONTOLOGY_ONLY:
            results = self.ontology_engine.execute(...)
        elif mode == SearchMode.VECTOR_ONLY:
            results = self.vector_svc.search(...)
        elif mode == SearchMode.HYBRID:
            results = self.both_engines(...)
        else:  # AUTO
            results = self.classify_intent_and_execute(...)
        
        # 2. 정책 기반 검증 (PHASE 8)
        gate_result = self.evidence_gate.check_evidence(
            question=request.question,
            search_mode=mode,  # ← 모드 정보 전달
            retrieval_results=results
        )
        
        # 3. 응답
        if not gate_result["allowed"]:
            return self.build_response(gate_result)
        
        return self.synthesizer.synthesize(results)
```

---

## ✅ **6. 최종 평가**

### PHASE 8 설계

| 항목 | 평가 | 근거 |
|---|---|---|
| **타당성** | ⭐⭐⭐⭐⭐ | 근본 문제를 정확히 파악 |
| **완전성** | ⭐⭐⭐⭐ | Task 분해 명확, 수용 기준 구체적 |
| **실현성** | ⭐⭐⭐ | 구현 복잡도 과소평가, threshold 미해결 |
| **위험도** | ⭐⭐ | v4 보존, v5 분리로 안전장치 있음 |
| **확장성** | ⭐⭐⭐ | Antigravity 통합 가능하지만 복잡도 증가 |

**종합**: 💪 **강력하고 실행 가능한 설계** (선행 작업 필요)

### Antigravity 설계

| 항목 | 평가 | 근거 |
|---|---|---|
| **타당성** | ⭐⭐⭐⭐ | 사용자 가치 명확, 성능 이점 있음 |
| **완전성** | ⭐⭐⭐ | API 설계 좋으나, PHASE 8과의 관계 모호 |
| **실현성** | ⭐⭐⭐ | 구현 가능하나 테스트 폭증 |
| **위험도** | ⭐⭐ | 모드 의존성, 경계 케이스 많음 |
| **확장성** | ⭐⭐⭐⭐ | 향후 더 많은 모드 추가 가능 |

**종합**: 🚀 **매력적이나 PHASE 8과 통합 필수** (독립 구현 권장하지 않음)

---

## 🎓 **7. 권장 실행 전략**

### Phase A: PHASE 8 우선 (2-3주)

```
목표: 평가와 서빙의 정책 일관성 확립

✓ answer_policy.yaml 설계 (Antigravity 고려)
✓ EvidenceGate 구현 (정책 드리븐)
✓ STD-S no-answer 테스트 통과 (90%+)
✓ v4 vs v5 비교 평가 완료

산출물:
  - PHASE8 완료 보고서 (정확도 67%+ 달성 여부)
```

### Phase B: Antigravity 통합 (선택, 1-2주)

```
전제: PHASE 8 완료 + answer_policy.yaml 안정화

옵션 1: 통합 설계 (권장) ⭐
  - SearchMode Enum 추가
  - QueryPlannerV5 수정
  - Mode별 제약 매핑
  → 추가 개발: 10-15시간

옵션 2: Phase A만 완료 (최소)
  - PHASE 8의 정책 일관성 달성
  - Antigravity는 향후 과제
  → 추가 개발: 0시간

권장: Option 1 (총 3-4주)
```

---

## 📄 **최종 결론**

### 상태

```
✅ PHASE 8: 실행 준비 완료 (선행 작업 필요)
⚠️ Antigravity: PHASE 8과 통합하여 실행 권장 (독립 불가)
```

### 명확히 해야 할 점

```
1. SearchMode 옵션은 "나중에 추가 가능"인가, "필수"인가?
   → 지금 결정하면 PHASE 8 설계 변경 필요

2. v4 → v5 마이그레이션 전략은?
   → 기존 클라이언트 호환성 유지?
   → API 버전 관리?

3. 테스트 범위 확정은?
   → PHASE 8만: 24 문항 × 3 기준 = 72 테스트
   → + Antigravity: 96-168 테스트
   → 일정/비용에 영향
```

### 다음 단계

```
1. 이 두 설계를 "통합" 하겠는가?
   → YES: 5.1 통합 설계 적용
   → NO: PHASE 8만 먼저 (Antigravity는 나중에)

2. PHASE 8 선행 작업 (2-3일)
   → Vector score distribution 분석
   → Threshold 후보 정하기
   → Question Analyzer 규칙 정의

3. 일정 확정
   → Option A (순차): 5주 + 안정화
   → Option B (통합): 3주 + 복잡도 관리
```

---

**평가 완료**  
**핵심**: PHASE 8은 강력하고 실행 가능. Antigravity는 매력적이지만 PHASE 8과 통합되어야 함.  
**권장**: Option B 통합 설계 (3-4주, 복잡도 관리 필요)
