# PHASE 6+7 통합 계획: Snowflake 정확도 개선 및 근거 기반 답변 구축

**목표**: 평가 시스템 + 서빙 시스템을 동시에 개선하여 정확도 31.25% → 67% 달성  
**기간**: 3주 (2026-06-10 ~ 06-28)  
**참여**: Claude Code (평가) + Codex (서빙) 병렬 진행  
**상태**: 🔴 READY TO START

---

## 📊 **통합 개요**

### 기존 계획 (순차)
```
PHASE 6 (완료)    PHASE 7 (예정)
  정답 보정   →   시스템 구현
  1주              3주
  = 총 4주
```

### 통합 계획 (병렬)
```
         Week 1           Week 2           Week 3
┌──────────────────┬──────────────────┬──────────────────┐
│ 평가 시스템      │ 평가 시스템      │ 평가 시스템      │
│ (Claude)         │ (Claude)         │ (Claude)         │
│ ✓ 정답 정의      │ ✓ 평가 재실행    │ ✓ 최종 검증      │
├──────────────────┼──────────────────┼──────────────────┤
│ 서빙 시스템      │ 서빙 시스템      │ 서빙 시스템      │
│ (Codex)          │ (Codex)          │ (Codex)          │
│ ✓ EvidenceGate   │ ✓ 구현 + 테스트  │ ✓ 통합 테스트    │
└──────────────────┴──────────────────┴──────────────────┘
     = 총 3주 (병렬)
```

---

## 🎯 **작업 분담 (중복 제거)**

### Claude Code의 작업 (평가 시스템)

**Week 1: 정답 보정 (PHASE 6 완료)**
```
✓ Stage 3 실행 (STD-S-01~08 정답 입력)
  → 대화형 CLI로 "관련 없습니다" 정답 정의
  
✓ 산출물:
  - corrections_YYYYMMDD_HHMMSS.json (8개 항목)
  - impact_analysis_report.md (변경점)
```

**Week 2: 평가 재실행**
```
✓ Stage 2 재실행 (보정된 정답으로)
✓ 정확도 개선 검증
  - 예상: 31.25% → 54% (+23%p)
  
✓ 산출물:
  - evaluation_results_v2.xlsx
  - regression_test_report.md
```

**Week 3: 최종 검증**
```
✓ Codex 시스템과 일관성 검증
✓ 회귀 테스트 (Ontology, Advanced RAG)
✓ 최종 보고서 작성

✓ 산출물:
  - final_evaluation_report.md
```

---

### Codex의 작업 (서빙 시스템)

**Week 1: EvidenceGate 구현 (PHASE 7 P0)**
```
✓ EvidenceGate 모듈 추가
  - 카테고리 검증
  - 관련성 threshold
  - LLM 호출 제어
  
✓ Category Classifier 강화
  - Question → Category 분류
  
✓ 정답 정책 추가
  - Snowflake: "관련 없습니다"
  - 기본: "근거를 찾지 못했습니다"
```

**Week 2: 구현 + 단위 테스트**
```
✓ 온톨로지 메타데이터 추가
  - Document category 지정
  - Chunk category 추가
  
✓ 벡터 Score Threshold 검증
  - Positive samples 10개 수집
  - Negative samples 10개 수집
  - Threshold 보정
  
✓ STD-S 8개 항목 테스트
  - 자동으로 "관련 없습니다" 반환하는가?
  - Hallucination 없는가?
```

**Week 3: 통합 + E2E 테스트**
```
✓ Claude 정답과 Codex 구현 연계
  - expected (Claude) = actual (Codex)?
  
✓ 회귀 테스트 (Ontology, Advanced RAG)
  - 기존 성능 유지?
  
✓ 성능 평가
  - STD-S: 90%+ 달성?
  - 전체: 67%+ 달성?
```

---

## 🔄 **병렬 협력 인터페이스**

### 공유 산출물 (Claude → Codex)

**Week 1 말 (Claude → Codex)**
```
파일: corrections_YYYYMMDD_HHMMSS.json
내용:
{
  "question_id": "STD-S-01",
  "original_answer": "RAG 답변은...",
  "corrected_answer": "관련 없습니다",
  "category": "Snowflake",
  "reason": "범위 외 기술"
}

활용: Codex가 이 정답을 EvidenceGate 정책으로 변환
     Snowflake → "관련 없습니다" (자동)
```

**Week 2 말 (Codex → Claude)**
```
파일: evidence_gate_policy.json
내용:
{
  "category": "Snowflake",
  "rule": "category_mismatch",
  "auto_response": "관련 없습니다",
  "confidence": 0.95
}

검증: Claude가 평가할 때
      expected = Codex auto_response인가?
```

---

## 📅 **주간 체크포인트**

### Week 1 (2026-06-10 ~ 06-14)

**Monday 06-10**:
- [ ] Claude: Stage 3 실행 시작
- [ ] Codex: EvidenceGate 설계 시작
- [ ] 일일 회의: 15:00 (30분)

**Wednesday 06-12**:
- [ ] Claude: Stage 3 완료 (정답 8개 입력)
- [ ] Codex: EvidenceGate 구현 50%
- [ ] 검토: 일관성 확인

**Friday 06-14**:
- [ ] Claude: 산출물 정리 (corrections.json)
- [ ] Codex: EvidenceGate 구현 완료
- [ ] 인수인계: 정책 파일 공유
- [ ] 주간 리뷰 (16:00, 1시간)

**산출물**:
```
corrections_20260610_HHMMSS.json
evidence_gate_v1.py
category_classifier.py
```

---

### Week 2 (2026-06-17 ~ 06-21)

**Monday 06-17**:
- [ ] Claude: Stage 2 재실행 (보정된 정답으로)
- [ ] Codex: 온톨로지 메타데이터 추가
- [ ] 일일 회의: 15:00

**Wednesday 06-19**:
- [ ] Claude: 정확도 검증 (54% 예상)
- [ ] Codex: Vector threshold calibration
- [ ] STD-S 8개 테스트 시작

**Friday 06-21**:
- [ ] Claude: 회귀 테스트 (Ontology, Advanced RAG)
- [ ] Codex: STD-S 8개 단위 테스트 완료
- [ ] 주간 리뷰

**산출물**:
```
evaluation_results_v2.xlsx
threshold_calibration_report.md
std_s_unit_test_results.json
```

---

### Week 3 (2026-06-24 ~ 06-28)

**Monday 06-24**:
- [ ] Claude: 최종 검증 데이터 정리
- [ ] Codex: 통합 테스트 시작
- [ ] 일일 회의

**Wednesday 06-26**:
- [ ] E2E 테스트 (Claude expected = Codex actual)
- [ ] 성능 검증
  - STD-S: 90%+?
  - Ontology: 75%+ 유지?
  - 전체: 67%+?

**Friday 06-28**:
- [ ] 최종 리포트 작성
- [ ] 성공 기준 달성 검증
- [ ] 최종 회의

**산출물**:
```
final_evaluation_report.md
e2e_test_results.xlsx
unified_completion_report.md
```

---

## 🎯 **작업 범위 (통합)**

### Claude의 작업 상세

| Week | Task | 산출물 | 시간 |
|---|---|---|---|
| 1 | Stage 3 실행 (대화형) | corrections.json | 2h |
| 1 | 영향도 분석 | impact_report.md | 1h |
| 2 | Stage 2 재실행 | evaluation_v2.xlsx | 1h |
| 2 | 회귀 테스트 | regression_report.md | 2h |
| 3 | 최종 검증 | final_report.md | 2h |
| **Total** | | | **8h** |

### Codex의 작업 상세

| Week | Task | 산출물 | 시간 |
|---|---|---|---|
| 1 | EvidenceGate 설계 | design_doc.md | 2h |
| 1 | 구현 (Category, Policy) | evidence_gate.py | 4h |
| 2 | 메타데이터 추가 | metadata.json | 2h |
| 2 | Threshold calibration | calibration.md | 3h |
| 2 | STD-S 단위 테스트 | test_results.json | 2h |
| 3 | E2E 테스트 | e2e_results.xlsx | 3h |
| 3 | 통합 검증 | integration_report.md | 2h |
| **Total** | | | **18h** |

**총 투입**: Claude 8h + Codex 18h = 26h (3명 × 1주일 정도)

---

## 💡 **통합의 장점**

### 1. 시간 절감
```
순차: 4주 (PHASE 6 → PHASE 7)
병렬: 3주 (PHASE 6+7 동시)
절감: 1주 (25% 단축)
```

### 2. 일관성 보장
```
정답 정의와 구현이 동시에 진행
→ 정책 불일치 위험 낮음
→ 의도한 대로 작동할 확률 높음
```

### 3. 빠른 피드백
```
Claude 결과 → Codex 구현 → Claude 검증
→ 1주 단위로 피드백 루프 완성
→ 문제 조기 발견 및 수정
```

### 4. 효율적 테스트
```
정답 보정과 시스템 구현을 동시에 테스트
→ 둘이 일관성 있는지 검증
→ 최종 성능 예측 정확
```

---

## ⚠️ **통합 시 주의사항**

### 의존성 관리

```
Week 1:
  Claude: 정답 정의 (8개 항목)
  Codex: 동시에 정책 구현
  → 중간에 조정 가능하도록 의사소통

Week 2:
  Claude: 정확도 검증
  Codex: 임계값 조정
  → 반복적 개선
  
Week 3:
  최종 통합 테스트
  → 둘이 일치하는가?
```

### 리스크 관리

```
❌ 위험: 정답과 구현 불일치
✅ 해결: 주 2회 검토 회의

❌ 위험: 의존성 충돌
✅ 해결: 공유 인터페이스 정의 (corrections.json)

❌ 위험: 시간 지연
✅ 해결: 병렬 진행으로 한쪽 지연이 다른 쪽에 영향 최소화
```

---

## 📊 **성공 기준 (통합)**

### 기술적 기준

| 항목 | 기준 | 검증 방법 |
|---|---|---|
| STD-S 정답 | "관련 없습니다" × 8 | corrections.json |
| EvidenceGate | 8/8 올바르게 감지 | unit_tests |
| 자동 응답 | 8/8 일치 | e2e_tests |
| 회귀 테스트 | Ontology 75%+ 유지 | regression_tests |

### 정확도 기준

| 항목 | 목표 | 현재 | 개선량 |
|---|---|---|---|
| STD-S no-answer | 90%+ | 0% | +90%p |
| Ontology | 75%+ | 75.62% | 유지 |
| **전체** | **67%+** | **31.25%** | **+36%p** |

### 일정 기준

| 항목 | 기준 |
|---|---|
| 총 기간 | 3주 (2026-06-10 ~ 06-28) |
| 병렬 효율 | 순차 대비 1주 단축 |
| 마일스톤 | 주 1회 이상 검토 |

---

## 📁 **산출물 목록 (통합)**

### Claude의 산출물

```
validation/ont_platform_v4_eval/data/
├─ corrections_20260610_HHMMSS.json          ← Week 1 말
│  └─ STD-S 정답 (8개)

reports/
├─ impact_analysis_report.md                 ← Week 1 말
├─ evaluation_results_v2.xlsx                ← Week 2 말
├─ regression_test_report.md                 ← Week 2 말
└─ final_evaluation_report.md                ← Week 3 말
```

### Codex의 산출물

```
ont_platform/v4/backend/app/services/
├─ evidence_gate.py                          ← Week 1 말
├─ question_category_classifier.py           ← Week 1 말
└─ answer_policy.py                          ← Week 1 말

validation/ont_platform_v4_eval/results/
├─ threshold_calibration_report.md           ← Week 2 말
├─ std_s_unit_test_results.json              ← Week 2 말
└─ e2e_test_results.xlsx                     ← Week 3 말

metadata/
└─ document_category_metadata.json           ← Week 2 말
```

### 공유 산출물

```
reports/
├─ UNIFIED_COMPLETION_REPORT.md              ← Week 3 말
├─ PERFORMANCE_COMPARISON.xlsx               ← Week 3 말
└─ LESSONS_LEARNED.md                        ← Week 3 말
```

---

## 🚀 **실행 체크리스트**

### Week 1 준비

- [ ] Claude
  - [ ] Stage 3 환경 준비 (corrections/ 폴더)
  - [ ] Stage 2 체크포인트 로그 확인
  - [ ] 대화형 실행 준비

- [ ] Codex
  - [ ] EvidenceGate 모듈 구조 설계
  - [ ] Category Classifier 신규 생성 vs 기존 강화 결정
  - [ ] 정책 정의 (no-answer messages)

- [ ] 공동
  - [ ] 일일 회의 시간 정하기 (15:00)
  - [ ] 정답 파일 형식 정의 (corrections.json 스키마)
  - [ ] 정책 파일 형식 정의 (evidence_gate_policy.json 스키마)

### Week 2 준비

- [ ] Claude
  - [ ] Stage 2 재실행 환경 준비
  - [ ] 회귀 테스트 시나리오 준비

- [ ] Codex
  - [ ] 온톨로지 메타데이터 생성 방식 정의
  - [ ] Vector score 분석 샘플 준비 (positive 10, negative 10)

### Week 3 준비

- [ ] E2E 테스트 시나리오 정의
- [ ] 최종 보고서 템플릿 준비

---

## 📞 **커뮤니케이션 계획**

### 정기 회의

```
Monday:   15:00 (15분) - 주 계획 확인
Wednesday: 15:00 (15분) - 진행 상황 점검
Friday:    16:00 (60분) - 주간 리뷰 + 다음 주 계획
```

### 비정기 회의

```
필요 시: Slack/문서로 즉시 공유
이슈 발생: 24시간 이내 응답
```

### 문서화

```
모든 결정사항 → shared Google Doc
모든 산출물 → 지정된 폴더
모든 테스트 → JSON/Excel 기록
```

---

## 🎓 **최종 정리**

### 통합 방식

```
기존 (순차):     PHASE 6 (1주) → PHASE 7 (3주) = 4주
통합 (병렬):     PHASE 6+7 (3주) = 3주

효과:
  ✓ 1주 단축 (25% 효율성 증가)
  ✓ 정책 불일치 위험 감소 (동시 진행)
  ✓ 피드백 루프 단축 (주 1회)
  ✓ 최종 성능 향상 (일관성 증가)
```

### 역할 분담

```
Claude:
  평가 시스템 개선
  정답 정의 + 평가 재실행
  8시간 × 3주

Codex:
  서빙 시스템 개선
  EvidenceGate + 구현
  18시간 × 3주

최종: 둘이 일치하는 최종 시스템 구축
```

---

**상태**: 🔴 READY TO EXECUTE  
**기간**: 3주 (2026-06-10 ~ 06-28)  
**목표**: 정확도 31.25% → 67%+ 달성  
**참여**: Claude Code + Codex (병렬)
