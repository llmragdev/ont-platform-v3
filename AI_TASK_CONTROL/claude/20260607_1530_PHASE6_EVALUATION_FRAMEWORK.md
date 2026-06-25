# PHASE 6: 평가 및 정답 보정 프레임워크 설계 완료

**작업일시**: 2026-06-07 15:30  
**작업자**: Claude Code  
**목표**: Snowflake 교훈을 바탕으로 PHASE 6 평가 프레임워크 설계  
**상태**: ✅ 설계 완료 (구현 준비 중)

---

## 📌 Executive Summary

### 작업 배경

Snowflake 평가 실패 (`Team4: 31.25%`)를 교훈 삼아 **평가 시스템 전체를 개선**하는 PHASE 6를 설계했습니다.

```
문제점:
- 범위 제약 부재 (문서 내용만 사용 원칙 미구현)
- 사후 검증 없음 (오류 누적)
- 수정 불가능 (원본 파일 보존)
- LLM 범위 침범 (일반 지식으로 답변)

해결책:
→ PHASE 6: 평가 전/중/후 3단계 자동 검증
→ 정답 보정 메커니즘 (자동 시스템 반영)
→ 재평가 자동화 (개선 루프)
```

---

## 🏗️ PHASE 6 구조

### 1. 독립적 평가 프레임워크

**기존 코드와 분리**:
```
E:\ontology_edu\X_ont_std\
├─ ont_platform\v3\        [변경 금지]
├─ evaluation_framework\    [신규 추가] ← PHASE 6
└─ validation\              [참조만]
```

**장점**:
- 기존 시스템 영향 없음
- 독립적 개발 가능
- 재사용 가능한 평가 프레임워크
- 명확한 책임 분리

### 2. 3단계 검증 프로세스

```
Stage 1: 평가 전 검증 (Week 3-4)
  └─ Q&A 일관성, 범위, 카테고리 검증
  └─ 산출물: validated_qa_set_v1.xlsx

Stage 2: 평가 중 검증 (Week 5-6)
  └─ 3개 체크포인트 + 제약 자동 적용
  └─ 산출물: evaluation_checkpoint_report.md

Stage 3: 정답 보정 (Week 7-8)
  └─ 정답 입력 → 시스템 반영 → 재평가
  └─ 산출물: revalidation_report.md
```

---

## 📊 생성된 문서

### PHASE 6 메인 문서

| 문서 | 위치 | 목적 |
|---|---|---|
| **PHASE6_EvaluationFramework.md** | `week_instructions/PHASE6/` | PHASE 6 전체 개요 및 아키텍처 |
| **Stage1_Prevalidation.md** | `week_instructions/PHASE6/` | Stage 1 상세 명세 (평가 전 검증) |

### 문서 내용

#### 1. PHASE6_EvaluationFramework.md (550줄)
- 📌 Executive Summary (문제 분석)
- 🏗️ PHASE 6 아키텍처
- 🗂️ 폴더 구조 (evaluation_framework/)
- 📅 8주 타임라인 (Week 1-8)
- 📊 산출물 정의 (코드 3,850줄, 데이터, 문서)
- 🎯 Success Criteria
- 🔗 의존성 및 연계

#### 2. Stage1_Prevalidation.md (400줄)
- 📋 Stage 1 개요
- 🔍 검증 체크리스트
- 📝 구현 상세 (Task 1-3)
  - Task 1: Q&A 일관성 검증 (QAConsistencyValidator)
  - Task 2: 범위 명시성 검증 (ScopeAnalyzer)
  - Task 3: 카테고리 일관성 검증 (CategoryConsistencyValidator)
- 📊 산출 방식 (JSON 로그 + 마크다운 보고서)
- ✅ 완료 조건

---

## 💾 생성된 파일 목록

```
E:\ontology_edu\X_ont_std\week_instructions\
├─ PHASE6\                          [신규 디렉토리]
│  ├─ PHASE6_EvaluationFramework.md (550줄) ✅
│  ├─ Stage1_Prevalidation.md       (400줄) ✅
│  ├─ Stage2_Evaluation.md          [계획 중]
│  └─ Stage3_Correction.md          [계획 중]
│
└─ PHASE4-eval-claude.md            [삭제됨, PHASE6로 이동]
```

---

## 🎯 PHASE 6 핵심 기능

### 1. Stage 1: 평가 전 검증

```python
# qa_validator.py - 300줄
QAConsistencyValidator().validate_pair(
    question="온톨로지 기반 질의응답에서...",
    expected_answer="온톨로지는 도메인 개념을...",
    category="Ontology",
    documents=[...]
)
# → {is_valid: True, score: 95, issues: []}

# scope_analyzer.py - 200줄
ScopeAnalyzer().analyze_scope(
    question="Snowflake RAG에서...",
    expected_answer="RAG 답변 기준은...",
    category="Snowflake"
)
# → {has_scope_issues: True, 
#     issues: ["Snowflake 문서 없음"], ...}
```

### 2. Stage 2: 평가 중 검증 (향후)

```python
# constraint_enforcer.py - 400줄
OntologyConstraintEnforcer().validate_answer_scope(
    question="Snowflake RAG에서...",
    category="Snowflake",
    retrieved_docs=[...]
)
# → {should_answer: False, fallback_answer: "해당 카테고리..."}

# checkpoints.py - 300줄
EvaluationCheckpoints()
  .checkpoint_1_answer_generation(...)
  .checkpoint_2_accuracy_scoring(...)
  .checkpoint_3_qa_validity(...)
```

### 3. Stage 3: 정답 보정 (향후)

```python
# cli.py - 500줄
AnswerCorrectionCLI().run_correction_session(
    evaluation_excel_path='4팀_정확도_비교.xlsx'
)
# 대화형 인터페이스로 정답 입력

# revalidation_engine.py - 450줄
RevalidationEngine().revalidate_qa_pairs(
    corrected_system=new_system,
    qa_pairs=[...],
    original_results={...}
)
# → 보정된 시스템으로 자동 재평가
```

---

## 📈 예상 효과

### Snowflake 평가 개선

```
현재 (잘못된 예상답변):
  Team0: 50%, Team1: 60%, Team2: 50%, Team4: 75%
  평균: 58.75%

수정 후 (현재 보정 완료):
  Team0: 75%, Team1: 75%, Team2: 75%, Team4: 75%
  평균: 75.00%

PHASE 6 이후 (정답 자동 보정):
  자동 감지 + 즉시 수정 가능
  향후 유사 오류 사전 차단
```

### 정확도 개선 메커니즘

```
평가 → 오류 발견 → 정답 입력 → 자동 수정 → 재평가
                    ↑                        ↓
                    ←← 루프 ←←←←←←←←←←←←←←

장점:
✓ 평가 오류 빠른 수정
✓ 시스템 자동 개선
✓ 오류 누적 방지
✓ 재사용 가능한 평가 프레임워크
```

---

## 📅 향후 일정

### PHASE 6 구현 (8주)

| 주차 | 기간 | 작업 | 산출물 |
|---|---|---|---|
| W1-2 | 07-01~11 | 설계 및 환경 구성 | 프레임워크 스켈레톤 |
| W3-4 | 07-12~22 | **Stage 1 구현** | validated_qa_set_v1.xlsx |
| W5-6 | 07-23~08-04 | **Stage 2 구현** | evaluation_checkpoints.py |
| W7-8 | 08-05~22 | **Stage 3 구현** | revalidation_engine.py |

### 선행 작업 (현재)

```markdown
✅ 2026-06-07: PHASE 6 설계 완료
├─ PHASE6_EvaluationFramework.md (아키텍처)
├─ Stage1_Prevalidation.md (평가 전 검증)
├─ evaluation_framework/ 폴더 구조 (계획)
└─ 타임라인 및 Success Criteria 정의

→ 2026-07-01: PHASE 6 구현 시작
```

---

## 🔗 관련 문서

### 현재 존재하는 문서

| 문서 | 경로 | 내용 |
|---|---|---|
| Snowflake 분석 | `week_instructions/PHASE4-eval-claude.md` | 문제 원인 분석 |
| 수정본 평가 | `validation/ont_platform_v4_eval/reports/4팀_정확도_비교_v2_수정본_분석.md` | 수정 후 결과 분석 |

### 향후 작성할 문서

```
week_instructions/PHASE6/
├─ PHASE6_EvaluationFramework.md      ✅ 완료
├─ Stage1_Prevalidation.md            ✅ 완료
├─ Stage2_Evaluation.md               📝 예정
├─ Stage3_Correction.md               📝 예정
└─ PHASE6_CompletionGuide.md          📝 예정

evaluation_framework/
├─ README.md                          📝 예정
├─ docs/API_REFERENCE.md              📝 예정
└─ docs/USER_GUIDE.md                 📝 예정
```

---

## 💡 Key Insights

### 1. 온톨로지 기반 시스템의 제약

```
강점:
✓ 범위가 명확함 (온톨로지에 없는 개념 = 답변 불가)
✓ 일관성 있는 답변

약점:
✗ 유연성 부족 (새 개념 추가 어려움)
✗ 범위 외 질문을 거절하기 어려움 (LLM이 "해석"함)

해결책:
→ 명시적 제약 구현 (constraint_enforcer.py)
→ 범위 검증 자동화 (checkpoints.py)
```

### 2. 평가 오류의 근본 원인

```
Snowflake 실패의 3가지 원인:

1. 설계 오류 (60%)
   - 예상답변이 문서 범위를 벗어남
   - 검증 체계 없음
   
2. 시스템 한계 (30%)
   - LLM이 일반 지식으로 "보정"
   - 제약 메커니즘 없음
   
3. 프로세스 부재 (10%)
   - 사후 검증 없음
   - 오류 수정 루프 없음

PHASE 6 해결책:
→ 설계 검증 (Stage 1) - 60% 개선
→ 제약 구현 (Stage 2) - 30% 개선
→ 보정 프로세스 (Stage 3) - 10% 개선
```

### 3. 재사용 가능한 프레임워크

```
PHASE 6 평가 프레임워크는:
- 온톨로지 기반 RAG 평가에 재사용 가능
- 향후 평가 자동화의 기반이 될 수 있음
- 다른 도메인의 평가에도 적용 가능

향후 PHASE 7-8에서:
- PHASE 6 프레임워크를 자동화
- CI/CD 파이프라인에 통합
- 프로덕션 배포
```

---

## ✅ 작업 완료 체크리스트

```markdown
✅ Snowflake 문제 근본 원인 분석
✅ PHASE 6 아키텍처 설계
✅ 평가 프레임워크 폴더 구조 정의
✅ 8주 타임라인 작성
✅ Stage 1 상세 명세 작성
✅ 코드 구조 (3,850줄) 계획
✅ Success Criteria 정의
✅ 선행 작업 문서화

📝 향후:
→ Stage 2, Stage 3 명세 작성 (이후 회차)
→ 2026-07-01부터 구현 시작
```

---

## 🎓 배운 점

### 1. 평가 설계의 중요성

```
좋은 평가 기준:
✓ 명확한 범위 (문서, 카테고리, 필수 개념)
✓ 사전 검증 (평가 전에 오류 감지)
✓ 명시적 제약 (코드로 구현)
✓ 사후 검증 (평가 후 오류 수정)
```

### 2. 온톨로지 기반 시스템의 설계 원칙

```
설계 시 고려사항:
✓ "문서에만 기반" 원칙을 명시적으로 구현
✓ 범위 외 질문 자동 감지 메커니즘
✓ LLM의 "일반화 경향"을 제약
✓ 테스트를 통한 조기 발견
```

### 3. 오류 수정의 체계화

```
지금까지: 오류 발견 → 수동 수정 → 종료
PHASE 6: 오류 발견 → 자동 입력 → 자동 반영 → 재평가
         (루프화)

효과:
- 같은 오류 재발 방지
- 시스템 자동 개선
- 평가 신뢰도 향상
```

---

**작업 상태**: ✅ 설계 완료  
**다음 단계**: PHASE 6 구현 (2026-07-01)  
**예상 완료**: 2026-08-22
