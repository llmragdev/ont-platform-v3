# ont_platform v3.0 — 통합 테스트 자동화

> 온톨로지 + RAG 보완·통합 관계를 자동으로 검증하는 프로젝트 기반 테스트 시스템

작성일: 2026-05-14  
작업 지시서: `E:\ontology_edu\AI_TASK_CONTROL\claude\20260514_1500_통합테스트_자동화_개발.md`

---

## 이 문서의 목적

같은 문서(AI바우처 PDF)에 대해 다음 세 가지를 자동으로 검증한다.

```
어떤 질문은 온톨로지가 답한다   →  구조화된 수치·기관명·날짜
어떤 질문은 RAG가 답한다        →  절차·규정·서술형 텍스트
어떤 질문은 둘이 협력한다       →  엔티티 + 맥락 결합
```

프로젝트명만 입력하면 자동 실행되고, 결과를 화면에서 조회할 수 있다.

---

## 폴더 구조

```
docs/integration_test/
  README.md                  ← 이 문서 (메인)
  01_design_document.md      ← QA 데이터셋 전문 + 판정 로직 상세
  02_execution_plan.md       ← API 명세 + 화면 구성 + 체크리스트

ont_platform/v3/
  test_data/
    ai-voucher-2025/
      qa_dataset.json        ← 테스트 케이스 25개 (구현 시 생성)

  src/backend/app/api/
    integration_test.py      ← 테스트 러너 API (구현 시 생성)

  src/frontend/src/components/
    IntegrationTestRunner.tsx ← 결과 조회 화면 (구현 시 생성)

  storage/demo-co/proj-01/
    test_runs/               ← 실행 결과 JSON (실행 시 자동 생성)
```

---

## 대상 문서

| 항목 | 내용 |
|------|------|
| 파일명 | 2025년 AI바우처 사업설명회 발표자료.pdf |
| 위치 | `ont_platform/docs/ref_data/01_raw/` |
| 주관 | 과학기술정보통신부 / NIPA |
| 핵심 데이터 | 예산 276억원, 130개 과제, 4개 분과, 22개 구조화 가능 엔티티 |
| 선택 이유 | LLM 학습 데이터 아님 → 환각 여부 판별 명확 |

---

## 테스트 케이스 설계 (25개)

### 소스 분류 기준

| 소스 | 판정 조건 | 의미 |
|------|-----------|------|
| `ontology` | ontology_hits > 0, vector_hits = 0 | 구조화 데이터로 답변 |
| `vector` | ontology_hits = 0, vector_hits > 0 | 문서 청크로 답변 |
| `hybrid` | ontology_hits > 0, vector_hits > 0 | 둘 다 사용 |
| `llm_only` | 둘 다 0 | 폴백 — 환각 위험 |

### A. 온톨로지 전용 (7개) — 구조적 사실

| ID | 질문 | 핵심 키워드 |
|----|------|------------|
| Q001 | 2025년 AI바우처 총 예산은 얼마야? | 276억 |
| Q002 | 2025년 총 과제수는 몇 개야? | 130개 |
| Q003 | 글로벌 분과의 2025년 과제수는? | 30개 |
| Q004 | AI반도체 분과 CSP 컨소시엄 구성 기업을 모두 나열해줘 | 리벨리온, 퓨리오사AI, KT클라우드 |
| Q005 | 이 사업의 주관 기관은 어디야? | NIPA, 과학기술정보통신부 |
| Q006 | 공급기업이 연간 신청할 수 있는 최대 과제수는? | 2개, 분과별 1개 |
| Q007 | 과제 수행 기간은 언제부터 언제까지야? | 5월, 11월, 2025 |

### B. 벡터 전용 (9개) — 절차·정책 텍스트

| ID | 질문 | 핵심 키워드 |
|----|------|------------|
| Q008 | 공급기업 Pool 신규 등록 절차를 설명해줘 | 신청서, 제출서류, AI솔루션 |
| Q009 | 데이터 관련 비용은 사업비로 쓸 수 있어? | 불가, 무상제공, 자체비용 |
| Q010 | 글로벌 분과에서 제출해야 하는 서류는? | K-SURE, 국제거래문서, NDA |
| Q011 | 민간매칭에서 현금과 현물의 차이는 뭐야? | 현금, 현물, 인건비 |
| Q012 | 타기관 사업과 중복 지원이 안 되는 경우는? | KOICA, KOTRA, 수출바우처 |
| Q013 | 의료 분과에서 병원이 신청할 때 제한 사항은? | 병원당, 1개, 진료과 |
| Q014 | 가점을 받을 수 있는 항목들은 뭐야? | 청년기업, 지역기업, 클라우드 |
| Q015 | 공급기업 변경 등록 대상은 누구야? | 기등록, 변경등록, 우정사항 |
| Q016 | 소상공인 분과에서 하드웨어 지원이 가능해? | 하드웨어, 소상공인 |

### C. 하이브리드 (6개) — 엔티티 + 맥락 결합

| ID | 질문 | 온톨로지 역할 | RAG 역할 |
|----|------|--------------|---------|
| Q017 | 2024년과 2025년을 비교하면 예산과 과제수가 어떻게 달라졌어? | METRIC 수치 비교 | 변경 배경 설명 |
| Q018 | 리벨리온이 제공하는 서비스는 뭐야? | ORGANIZATION 엔티티 | NPU 서비스 설명 |
| Q019 | 일반 분과와 소상공인 분과의 민간매칭 방식이 어떻게 달라? | CATEGORY 분과 | 매칭 세부 규정 |
| Q020 | NIPA가 이 사업에서 하는 역할은 뭐야? | ORGANIZATION.NIPA | 운영 역할 설명 |
| Q021 | AI반도체 분과 신청 마감일은 언제고 신청 방법은? | EVENT 날짜 | 신청 절차 설명 |
| Q022 | 소상공인이 글로벌 분과에 신청할 수 있어? | CATEGORY 자격 | 자격 조건 텍스트 |

### D. 경계 케이스 (3개) — 어려운 질문 / 환각 방지

| ID | 질문 | 목적 |
|----|------|------|
| Q023 | 이 사업에 반도체 기업이 수요기업으로 참여할 수 있어? | 암묵적 추론 검증 |
| Q024 | 과제 선정 시 평가 배점 기준표는? | 문서 범위 밖 — 폴백 동작 확인 |
| Q025 | 2026년 AI바우처 예산은 얼마야? | **환각 방지 필수 통과** |

---

## 온톨로지 사전 구축 (22개 엔티티)

테스트 실행 전 `ai-voucher-2025` 네임스페이스에 등록해야 함.

| 타입 | 이름 | 핵심 속성 |
|------|------|-----------|
| PROGRAM | AI바우처 2025 | budget:276억, year:2025, quota:130 |
| PROGRAM | AI바우처 2024 | budget:425억, year:2024, quota:201 |
| ORGANIZATION | 과학기술정보통신부 | role:주관기관 |
| ORGANIZATION | NIPA | role:운영기관 |
| ORGANIZATION | 리벨리온 | type:AI반도체, role:NPU공급사 |
| ORGANIZATION | 퓨리오사AI | type:AI반도체, role:NPU공급사 |
| ORGANIZATION | KT클라우드 | type:CSP |
| ORGANIZATION | NHN클라우드 | type:CSP |
| ORGANIZATION | 엘리스그룹 | type:CSP |
| ORGANIZATION | KOICA | role:중복금지대상 |
| ORGANIZATION | KOTRA | role:중복금지대상 |
| CATEGORY | 일반분과 | quota_2025:60, quota_2024:100 |
| CATEGORY | AI반도체분과 | quota_2025:20, quota_2024:30 |
| CATEGORY | 소상공인분과 | quota_2025:20, quota_2024:21 |
| CATEGORY | 글로벌분과 | quota_2025:30, quota_2024:50 |
| METRIC | 2025총예산 | value:276, unit:억원 |
| METRIC | 2024총예산 | value:425, unit:억원 |
| METRIC | 과제당최대지원비 | value:2, unit:억원 |
| METRIC | 공급기업연간최대과제수 | value:2, unit:개 |
| EVENT | 일반과제접수마감 | date:2025-03-13, time:15:00 |
| EVENT | AI반도체과제접수마감 | date:2025-03-24, time:15:00 |
| EVENT | 과제수행기간 | start:2025-05-01, end:2025-11-30 |

스키마 추가 필요:
- `PROGRAM` 타입 (budget, year, quota 속성)
- `DIVISION` 타입 (quota_2025, quota_2024, target 속성)

---

## 시스템 구조

```
[브라우저]
  IntegrationTestRunner.tsx
    ├─ 프로젝트 선택 (드롭다운)
    ├─ [▶ 테스트 실행] 버튼
    ├─ 실행 이력 목록 (pass율, 소요시간)
    └─ 케이스 상세 (소스 배지 / 답변 / 증거 / pass·fail)

         ↕ API 호출

[FastAPI Backend]
  POST /api/integration-test/run
    → QA 25개 순회
    → hybridAsk 호출 (기존 /api/hybrid/ask 재사용)
    → 소스 판정 + 키워드 매칭
    → 결과 JSON 저장

  GET  /api/integration-test/projects
  GET  /api/integration-test/{project}/runs
  GET  /api/integration-test/{project}/runs/{run_id}

         ↕ 저장

[Storage]
  storage/demo-co/proj-01/test_runs/{run_id}.json
```

---

## pass/fail 판정 로직

```python
# 1. 소스 판정
ont_hits = response["quality_metrics"]["ontology_hits"]
vec_hits  = response["quality_metrics"]["vector_hits"]

actual_source = (
    "ontology" if ont_hits > 0 and vec_hits == 0 else
    "vector"   if ont_hits == 0 and vec_hits > 0 else
    "hybrid"   if ont_hits > 0 and vec_hits > 0 else
    "llm_only"
)
source_matched = (actual_source == case["expected_source"])

# 2. 키워드 매칭
answer_lower = response["answer"].lower()
if case.get("expect_no_answer"):          # Q025 환각 방지
    keyword_matched = not any(kw.lower() in answer_lower
                              for kw in case.get("forbidden_keywords", []))
elif not case.get("expected_keywords"):   # 키워드 없으면 통과
    keyword_matched = True
else:
    keyword_matched = any(kw.lower() in answer_lower
                          for kw in case["expected_keywords"])

# 3. 최종
passed = source_matched and keyword_matched
```

---

## 예상 화면

```
┌─────────────────────────────────────────────────────────────┐
│ 통합 테스트                                                    │
│                                                              │
│ 프로젝트  [ai-voucher-2025 ▼]         [▶ 테스트 실행]        │
│                                                              │
│ ── 실행 이력 ────────────────────────────────────────────── │
│  2026-05-14 15:30   22/25 통과 (88%)   18.4초   [상세보기]  │
│                                                              │
│ ── 케이스 상세 ─────────────────────────────────────────── │
│                                                              │
│  [전체▼]  [소스: 전체▼]  [상태: 전체▼]                       │
│                                                              │
│  Q001  ✅  [온톨로지]  2025년 AI바우처 총 예산은 얼마야?      │
│   소스: ontology (기대: ontology)                            │
│   답변: "2025년 AI바우처 총 예산은 276억원입니다."            │
│   근거: METRIC:2025총예산 = 276억원                          │
│                                                              │
│  Q008  ✅  [벡터]  공급기업 Pool 신규 등록 절차를 설명해줘   │
│   소스: vector (기대: vector)                               │
│   답변: "공급기업 Pool 신규 등록은 신청서와..."               │
│   근거: AI바우처PDF p.4  score=0.91                         │
│                                                              │
│  Q017  ✅  [하이브리드]  2024년 vs 2025년 비교              │
│   소스: hybrid (기대: hybrid)   온톨로지 2건 + 벡터 3건     │
│                                                              │
│  Q025  ✅  [경계]  2026년 AI바우처 예산은?                  │
│   소스: llm_only (기대: llm_only)  환각 감지 없음 ✓         │
└─────────────────────────────────────────────────────────────┘
```

---

## 구현 계획 및 예상 소요 시간

| Phase | 작업 | 예상 시간 |
|-------|------|----------|
| Phase 1 | PDF 업로드·벡터 확인, 스키마 추가, 엔티티 22개 시드, qa_dataset.json | 25분 |
| Phase 2 | `integration_test.py` 러너 + 4개 엔드포인트 + main.py 등록 | 30분 |
| Phase 3 | `IntegrationTestRunner.tsx` + api.ts + 사이드바 메뉴 | 30분 |
| Phase 4 | 첫 실행 + 실패 분석 + 보완 | 20분 |
| **합계** | | **1시간 45분** |

낙관: 1시간 30분 / 보수: 2시간

---

## 성공 기준

| 항목 | 목표 |
|------|------|
| 전체 pass율 | 80% 이상 |
| 온톨로지 케이스 pass율 | 85% 이상 |
| 벡터 케이스 pass율 | 75% 이상 |
| 하이브리드 케이스 pass율 | 70% 이상 |
| Q025 환각 방지 | **100% 필수** |

---

## 완료 기준 (DoD)

```
☐ PDF 업로드 완료 + 벡터 청크 1개 이상 확인
☐ ai-voucher-2025 네임스페이스 엔티티 22개 등록
☐ POST /api/integration-test/run → run_id 반환
☐ 25개 케이스 에러 없이 실행 완료
☐ 브라우저에서 통합 테스트 화면 접근 가능
☐ 케이스별 소스 배지 표시 (온톨로지/벡터/하이브리드)
☐ 전체 pass율 수치 표시
☐ Q025 환각 방지 케이스 결과 확인
```

---

## 관련 문서

| 문서 | 내용 |
|------|------|
| [01_design_document.md](01_design_document.md) | QA 데이터셋 JSON 전문, 엔티티 상세, 판정 로직 코드 |
| [02_execution_plan.md](02_execution_plan.md) | API 명세 상세, 화면 구성 상세, 체크리스트 |
| [AI_TASK_CONTROL/.../20260514_1500_통합테스트_자동화_개발.md](../../../AI_TASK_CONTROL/claude/20260514_1500_통합테스트_자동화_개발.md) | 작업 지시서 (단계별 체크리스트) |
