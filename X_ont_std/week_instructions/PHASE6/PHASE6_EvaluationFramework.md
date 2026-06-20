# PHASE 6: 평가 및 정답 보정 프레임워크

**목표**: ont_platform 정확도 향상을 위한 평가 시스템 개발 및 자동 보정 메커니즘 구축  
**기간**: 2026-07-01 ~ 2026-08-31 (2개월, 8주)  
**담당**: Claude (평가 담당자)  
**상태**: 설계 단계

---

## 📌 Executive Summary

### PHASE 6의 필요성

| 이슈 | 원인 | 영향 |
|---|---|---|
| **Snowflake 평가 실패** | 범위 명시 부재 | Team4 순위 2위→3위 |
| **정답 검증 부재** | 사후 검증 프로세스 없음 | 오류 누적 |
| **수정 불가능** | 원본 파일 변경 금지 | 개선 루프 없음 |
| **LLM 범위 침범** | "문서 내용만" 제약 없음 | 일반 지식으로 답변 |

### PHASE 6의 솔루션

```
┌─────────────────────────────────────────────────────────────┐
│ 평가 전 (Stage 1)                                           │
│ - Q&A 검증: 예상답변이 문서 기반인가?                       │
│ - 범위 정의: 카테고리별 필수 개념 명시                      │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│ 평가 중 (Stage 2)                                           │
│ - 검증 체크포인트: 3개 지점에서 자동 검증                  │
│ - 제약 적용: 온톨로지 기반 범위 제약 자동 적용             │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│ 평가 후 (Stage 3)                                           │
│ - 정답 입력: 대화형 CLI로 정답 수집                         │
│ - 시스템 반영: 온톨로지/RAG 자동 업데이트                  │
│ - 재평가: 보정된 시스템으로 자동 재평가                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ PHASE 6 아키텍처

### 1. 독립적 평가 프레임워크

```
현재 구조:
  E:\ontology_edu\X_ont_std\
  ├─ ont_platform\v3\          (원본 시스템)
  └─ validation\                (기본 평가)

PHASE 6 추가:
  E:\ontology_edu\X_ont_std\
  ├─ ont_platform\v3\          (원본 시스템) [변경 금지]
  ├─ evaluation_framework\      [PHASE 6 신규] ← 독립적 평가 시스템
  │  ├─ config/                카테고리 정의, 검증 규칙
  │  ├─ stages/
  │  │  ├─ stage1_prevalidation/   평가 전 검증
  │  │  ├─ stage2_evaluation/      평가 실행
  │  │  └─ stage3_correction/      정답 보정
  │  ├─ tools/
  │  │  ├─ cli.py                  대화형 CLI
  │  │  ├─ updater.py              시스템 업데이트
  │  │  └─ revalidator.py           재평가 엔진
  │  └─ reports/                평가 보고서
  └─ validation\                (기본 평가) [그대로 유지]
```

### 2. 데이터 흐름

```
평가 기준 (Q&A)
    ↓
Stage 1: 사전 검증
  · Q&A 일관성 검증
  · 범위 명시성 검증
  · 문서 기반 가능성 검증
    ↓ [검증 통과]
  
원본 평가 (ont_platform v3)
    ↓
Stage 2: 평가 중 검증
  · 체크포인트 1: 답변 생성 직후
  · 체크포인트 2: 채점 전
  · 체크포인트 3: 결과 검증
    ↓ [평가 완료]

평가 결과
    ↓
Stage 3: 정답 보정
  · 정답 입력 (대화형 CLI)
  · 영향도 분석
  · 시스템 업데이트
  · 재평가
    ↓ [보정 완료]

최종 평가 결과
```

---

## 🗂️ PHASE 6 폴더 구조

```
E:\ontology_edu\X_ont_std\evaluation_framework\
├─ README.md                           (PHASE 6 개요)
├─ ARCHITECTURE.md                     (아키텍처 상세)
├─ ROADMAP.md                          (진행 계획)
│
├─ config/
│  ├─ category_definitions.py          카테고리 범위 정의
│  ├─ validation_rules.py              검증 규칙
│  └─ default_config.yaml              기본 설정
│
├─ stages/
│  ├─ stage1_prevalidation/
│  │  ├─ __init__.py
│  │  ├─ qa_validator.py               Q&A 쌍 검증
│  │  ├─ scope_analyzer.py             범위 분석
│  │  ├─ document_reference_checker.py  문서 기반 가능성 검증
│  │  └─ reports/
│  │     └─ qa_validation_report.md
│  │
│  ├─ stage2_evaluation/
│  │  ├─ __init__.py
│  │  ├─ constraint_enforcer.py        온톨로지 제약 적용
│  │  ├─ checkpoints.py                3개 검증 지점
│  │  ├─ metrics.py                    평가 메트릭
│  │  └─ reports/
│  │     └─ evaluation_checkpoint_report.md
│  │
│  └─ stage3_correction/
│     ├─ __init__.py
│     ├─ cli.py                        정답 입력 CLI
│     ├─ impact_analyzer.py            영향도 분석
│     ├─ ontology_updater.py           온톨로지 업데이트
│     ├─ rag_updater.py                RAG DB 업데이트
│     ├─ revalidation_engine.py        재평가 엔진
│     └─ reports/
│        ├─ corrections_input.json     정답 입력 데이터
│        ├─ impact_analysis.md         영향도 분석 보고서
│        └─ revalidation_report.md     재평가 보고서
│
├─ tools/
│  ├─ __init__.py
│  ├─ logger.py                        로깅 유틸리티
│  ├─ validators.py                    검증 유틸리티
│  └─ formatters.py                    포맷팅 유틸리티
│
├─ tests/
│  ├─ test_qa_validator.py
│  ├─ test_constraint_enforcer.py
│  ├─ test_correction_cli.py
│  └─ test_integration.py
│
├─ docs/
│  ├─ USER_GUIDE.md                    사용자 가이드
│  ├─ API_REFERENCE.md                 API 레퍼런스
│  └─ BEST_PRACTICES.md                베스트 프랙티스
│
└─ data/
   ├─ qa_pairs/
   │  ├─ validated_qa_set_v1.xlsx      검증된 Q&A 셋
   │  └─ qa_validation_log.json
   │
   ├─ corrections/
   │  ├─ corrections_20260607.json     정답 보정 데이터
   │  └─ correction_history.json       보정 이력
   │
   └─ ontology_snapshots/
      ├─ ontology_before_correction.rdf
      └─ ontology_after_correction.rdf
```

---

## 📅 PHASE 6 타임라인 (8주)

### Week 1-2: 설계 및 환경 구성

**목표**: 평가 프레임워크의 설계 확정 및 개발 환경 구성

| 날짜 | 작업 | 담당 | 산출물 |
|---|---|---|---|
| 07-01~02 | 기존 평가 분석 | Claude | analysis_report.md |
| 07-03~04 | 검증 규칙 설계 | Claude | validation_rules.py |
| 07-05~07 | 폴더 구조 및 기본 인프라 | Claude | 프레임워크 스켈레톤 |
| 07-08~11 | 문서 작성 (README, API) | Claude | 개발자 가이드 |

### Week 3-4: Stage 1 구현 (평가 전 검증)

**목표**: Q&A 쌍 검증 및 범위 명시화 완료

| 날짜 | 작업 | 담당 | 산출물 |
|---|---|---|---|
| 07-12~14 | Q&A 검증 로직 구현 | Claude | qa_validator.py |
| 07-15~16 | 범위 분석 및 카테고리 정의 | Claude | category_definitions.py |
| 07-17~18 | 문서 기반 가능성 검증 | Claude | document_reference_checker.py |
| 07-19~21 | Stage 1 테스트 및 보고서 | Claude | qa_validation_report.md |
| 07-22 | 기존 Q&A 검증 실행 | Claude | validated_qa_set_v1.xlsx |

### Week 5-6: Stage 2 구현 (평가 중 검증)

**목표**: 평가 중 자동 검증 및 제약 적용 완료

| 날짜 | 작업 | 담당 | 산출물 |
|---|---|---|---|
| 07-23~25 | 제약 적용 엔진 구현 | Claude | constraint_enforcer.py |
| 07-26~28 | 3개 체크포인트 구현 | Claude | checkpoints.py |
| 07-29~31 | 메트릭 및 평가 로직 | Claude | metrics.py |
| 08-01~04 | Stage 2 통합 테스트 | Claude | evaluation_checkpoint_report.md |

### Week 7-8: Stage 3 구현 (정답 보정)

**목표**: 정답 보정 및 시스템 자동 반영 완료

| 날짜 | 작업 | 담당 | 산출물 |
|---|---|---|---|
| 08-05~07 | 정답 입력 CLI 개발 | Claude | cli.py |
| 08-08~09 | 영향도 분석 엔진 | Claude | impact_analyzer.py |
| 08-10~12 | 온톨로지/RAG 업데이터 | Claude | ontology_updater.py, rag_updater.py |
| 08-13~15 | 재평가 엔진 구현 | Claude | revalidation_engine.py |
| 08-16~18 | 전체 통합 테스트 | Claude | integration_test_report.md |
| 08-19~22 | 최종 문서화 및 배포 | Claude | PHASE6_completion_report.md |

---

## 📊 PHASE 6 산출물

### 1. 코드 (evaluation_framework/)

```
Stage 1: 사전 검증
├─ qa_validator.py         (300줄) Q&A 쌍 검증 로직
├─ scope_analyzer.py       (200줄) 범위 분석
└─ document_reference_checker.py (250줄)

Stage 2: 평가 중 검증
├─ constraint_enforcer.py  (400줄) 제약 적용 엔진
├─ checkpoints.py          (300줄) 3개 체크포인트
└─ metrics.py              (200줄) 평가 메트릭

Stage 3: 정답 보정
├─ cli.py                  (500줄) 대화형 CLI
├─ impact_analyzer.py      (400줄) 영향도 분석
├─ ontology_updater.py     (350줄) 온톨로지 업데이트
├─ rag_updater.py          (300줄) RAG DB 업데이트
└─ revalidation_engine.py  (450줄) 재평가 엔진

총 약 3,850줄의 프로덕션 코드
```

### 2. 데이터

```
QA 검증:
  ├─ qa_validation_report.md     (기존 평가 Q&A 검증 결과)
  └─ validated_qa_set_v1.xlsx    (검증된 Q&A 셋)

평가 결과:
  ├─ evaluation_checkpoint_report.md  (체크포인트 기록)
  └─ evaluation_metrics.json          (평가 메트릭)

정답 보정:
  ├─ corrections_20260607.json   (정답 보정 데이터)
  ├─ impact_analysis.md          (영향도 분석)
  └─ revalidation_report.md      (재평가 결과)
```

### 3. 문서

```
개발자 문서:
  ├─ README.md                   (PHASE 6 개요)
  ├─ ARCHITECTURE.md             (아키텍처 상세)
  ├─ API_REFERENCE.md            (API 문서)
  └─ BEST_PRACTICES.md           (베스트 프랙티스)

사용자 문서:
  ├─ USER_GUIDE.md               (사용 방법)
  └─ EXAMPLES.md                 (사용 예제)

최종 보고서:
  └─ PHASE6_completion_report.md (완료 보고서)
```

---

## 🎯 PHASE 6 Success Criteria

### Code Quality
- ✅ 모든 코드 PEP 8 준수
- ✅ 클래스별 단위 테스트 ≥ 90% 커버리지
- ✅ 통합 테스트 ≥ 5개
- ✅ 타입 힌팅 100%

### Functionality
- ✅ Stage 1: 모든 Q&A 쌍 검증 완료
- ✅ Stage 2: 평가 중 3개 체크포인트 자동 작동
- ✅ Stage 3: 정답 입력→시스템 반영→재평가 자동화

### Documentation
- ✅ API 문서 100% 커버리지
- ✅ 사용자 가이드 (예제 포함)
- ✅ 아키텍처 설명서

### Results
- ✅ ont_platform v4 정확도 개선 측정
- ✅ 정답 보정 후 회귀(Regression) 없음
- ✅ 재사용 가능한 평가 프레임워크 완성

---

## 🔗 PHASE 6 의존성 및 연계

### 선행 요구사항
- PHASE 4: 온톨로지 확장성 (Week 1-8) ✓
- 기존 평가 결과: validation/ont_platform_v4_eval/ ✓

### 후행 연계
- PHASE 7: 자동화 및 CI/CD 통합
- PHASE 8: 프로덕션 배포 및 모니터링

### 기존 시스템 영향
- **ont_platform v3 (원본)**: 영향 없음 [읽기만]
- **validation/ (기본 평가)**: 영향 없음 [참조만]
- **evaluation_framework/ (신규)**: 독립적 시스템 [신규 추가]

---

## 💡 PHASE 6 주요 특징

### 1. 독립성
```
기존 시스템을 변경하지 않고
평가 프레임워크만 추가하는 구조
→ 기존 데이터 보호 + 새로운 기능 추가
```

### 2. 자동화
```
Stage 1, 2, 3 모두 자동화
→ 수동 개입 최소화 (정답 입력만 필요)
```

### 3. 트레이서빌리티
```
모든 변경사항 로깅
→ 정답 보정의 이력 추적 가능
```

### 4. 재사용성
```
평가 프레임워크를 다른 시스템에도 적용 가능
→ 향후 평가 자동화에 재사용
```

---

## 📝 PHASE 6 관련 문서

| 문서 | 경로 | 목적 |
|---|---|---|
| 상세 계획 | `week_instructions/PHASE6/PHASE6_DetailedPlan.md` | 주차별 상세 계획 |
| Stage 1 명세 | `week_instructions/PHASE6/Stage1_Prevalidation.md` | Stage 1 상세 명세 |
| Stage 2 명세 | `week_instructions/PHASE6/Stage2_Evaluation.md` | Stage 2 상세 명세 |
| Stage 3 명세 | `week_instructions/PHASE6/Stage3_Correction.md` | Stage 3 상세 명세 |
| API 문서 | `evaluation_framework/docs/API_REFERENCE.md` | API 레퍼런스 |
| 사용 가이드 | `evaluation_framework/docs/USER_GUIDE.md` | 사용 방법 |

---

**문서 버전**: 1.0  
**작성일**: 2026-06-07  
**상태**: 설계 완료, 구현 준비 중
