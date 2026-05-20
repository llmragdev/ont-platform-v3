# 통합 테스트 설계 문서
## ont_platform v3.0 — Ontology + RAG 보완/통합 검증

작성일: 2026-05-14  
대상 문서: 2025년 AI바우처 사업설명회 발표자료.pdf  
테스트 목적: 동일 질문을 온톨로지/벡터/하이브리드 경로로 각각 처리하는 것을 자동 검증

---

## 1. 테스트의 핵심 질문

> "같은 문서에서 어떤 질문은 온톨로지가 답하고,  
>  어떤 질문은 RAG가 답하고,  
>  어떤 질문은 둘이 협력해야 하는가?"

이 질문에 대한 **근거 있는 답변**을 자동으로 생성하고 검증하는 것이 이 테스트의 목표다.

---

## 2. 문서 분석 요약

### 2.1 문서 기본 정보

| 항목 | 내용 |
|------|------|
| 문서명 | 2025년 AI바우처 사업설명회 발표자료 |
| 주관 | 과학기술정보통신부 / 정보통신산업진흥원(NIPA) |
| 발표일 | 2025.2.20(목) 13:30, 코엑스 아센블름홀 |
| 총예산 | 276억원 (2024년 425억원 대비 35% 축소) |
| 총과제수 | 130개 (2024년 201개) |
| 분과 | 일반(의료포함), AI반도체, 소상공인, 글로벌 |

### 2.2 온톨로지로 구조화할 데이터 (구조적 사실)

이 데이터는 **변하지 않는 사실**로, 정확한 수치·기관명·분류가 중요하다.  
→ **온톨로지 엔티티로 저장해야 올바른 답변 가능**

```
METRIC 엔티티
  - 2025년 총예산: 276억원
  - 2024년 총예산: 425억원
  - 예산 감소율: 35%
  - 과제당 최대 지원비: 2억원
  - 2025년 총과제수: 130개
  - 공급기업 연간 신청 가능 과제수: 총 2개, 분과별 1개

CATEGORY 엔티티 (분과)
  - 일반(의료포함): 60개 과제
  - AI반도체: 20개 과제
  - 소상공인: 20개 과제
  - 글로벌: 30개 과제

ORGANIZATION 엔티티
  - 과학기술정보통신부 (주관기관)
  - 정보통신산업진흥원 NIPA (운영기관)
  - 리벨리온(주) (AI반도체 공급사)
  - 퓨리오사AI (AI반도체 공급사)
  - KT클라우드 (CSP 파트너)
  - NHN클라우드 (CSP 파트너)
  - 엘리스그룹 (CSP 파트너)
  - KOICA, KOTRA (중복 불가 기관)

EVENT 엔티티
  - 공급기업Pool등록마감_일반: 2025-03-13
  - 공급기업Pool등록마감_AI반도체: 2025-03-24
  - 과제접수마감_일반: 2025-03-13 15:00
  - 과제수행기간: 2025-05 ~ 2025-11
```

### 2.3 RAG로 검색할 데이터 (절차·정책 텍스트)

이 데이터는 **서술형 규정**으로, 원문 맥락이 중요하다.  
→ **벡터 검색으로 관련 청크를 찾아야 정확한 답변 가능**

```
- 공급기업 Pool 신규 등록 절차 (제출서류 목록 포함)
- 데이터 관련 비용 처리 원칙 (불인정 항목 상세)
- 민간매칭 계산 방식 (현금/현물 구분)
- 글로벌 분과 제출서류 목록
- 타기관 사업 중복 방지 규정
- 가점 항목별 세부 기준
- 의료 분과 병원 신청 제한 규정
```

### 2.4 하이브리드가 필요한 질문 유형

```
- 특정 기관(온톨로지)에 대한 역할/절차(RAG) 질문
  예: "리벨리온은 어떤 서비스를 제공해?"
  → 온톨로지: ORGANIZATION.리벨리온 찾기
  → RAG: NPU 기반 서비스 설명 청크 검색

- 비교 질문 (수치 + 맥락)
  예: "2024년 대비 2025년에 뭐가 바뀌었어?"
  → 온톨로지: METRIC 비교 (130 vs 201, 276억 vs 425억)
  → RAG: 변경 이유·배경 설명 청크 검색

- 자격 충족 여부 질문
  예: "소상공인이 일반 분과에 신청할 수 있어?"
  → 온톨로지: CATEGORY.소상공인 수요자격 조회
  → RAG: 자격 조건 세부 텍스트 확인
```

---

## 3. QA 데이터셋 설계 (25개 케이스)

### 3.1 소스 분류 기준

| 소스 | 판정 기준 | API 지표 |
|------|-----------|----------|
| `ontology` | ontology_hits > 0, vector_hits == 0 | `quality_metrics.ontology_hits` |
| `vector` | ontology_hits == 0, vector_hits > 0 | `quality_metrics.vector_hits` |
| `hybrid` | ontology_hits > 0, vector_hits > 0 | 둘 다 > 0 |
| `llm_only` | 둘 다 0, llm_used == true | 폴백 케이스 |

### 3.2 QA 케이스 목록

#### A. 온톨로지 전용 (7개) — 구조적 사실 조회

| ID | 질문 | 기대 소스 | 기대 엔티티 타입 | 핵심 키워드 |
|----|------|-----------|------------------|-------------|
| Q001 | 2025년 AI바우처 총 예산은 얼마야? | ontology | METRIC | 276억, 276,000,000 |
| Q002 | 2025년 총 과제수는 몇 개야? | ontology | METRIC | 130개 |
| Q003 | 글로벌 분과의 과제수는? | ontology | METRIC | 30개 |
| Q004 | AI반도체 분과 CSP 컨소시엄 구성 기업을 모두 나열해줘 | ontology | ORGANIZATION | 리벨리온, 퓨리오사AI, KT클라우드 |
| Q005 | 이 사업의 주관 기관은 어디야? | ontology | ORGANIZATION | 과학기술정보통신부, NIPA |
| Q006 | 공급기업이 연간 신청할 수 있는 최대 과제수는? | ontology | METRIC | 2개, 분과별 1개 |
| Q007 | 과제 수행 기간은 언제부터 언제까지야? | ontology | EVENT | 5월, 11월, 2025 |

#### B. 벡터 전용 (9개) — 절차·정책 텍스트

| ID | 질문 | 기대 소스 | 핵심 키워드 |
|----|------|-----------|-------------|
| Q008 | 공급기업 Pool 신규 등록 절차를 설명해줘 | vector | 신청서, 제출서류, AI솔루션 증빙 |
| Q009 | 데이터 관련 비용은 사업비로 쓸 수 있어? | vector | 불가, 무상제공, 자체비용 |
| Q010 | 글로벌 분과에서 제출해야 하는 서류는? | vector | K-SURE, 국제거래문서, NDA |
| Q011 | 민간매칭에서 현금과 현물의 차이는 뭐야? | vector | 현금, 현물, 인건비, 부담금 |
| Q012 | 타기관 사업과 중복 지원이 안 되는 경우는? | vector | KOICA, KOTRA, NIPA, 고성장클럽 |
| Q013 | 의료 분과에서 병원이 신청할 때 제한 사항은? | vector | 병원당 최대 1개, 진료과, 센터 |
| Q014 | 가점을 받을 수 있는 항목들은 뭐야? | vector | 청년기업, 지역기업, 클라우드 |
| Q015 | 공급기업 변경 등록 대상은 누구야? | vector | 기등록, 24~25년, 우정사항 |
| Q016 | 소상공인 분과에서 하드웨어 지원이 가능해? | vector | 하드웨어, 확산형, 소상공인 |

#### C. 하이브리드 (6개) — 엔티티 + 맥락 결합

| ID | 질문 | 기대 소스 | 온톨로지 역할 | RAG 역할 |
|----|------|-----------|--------------|---------|
| Q017 | 2024년과 2025년을 비교하면 예산과 과제수가 어떻게 달라졌어? | hybrid | METRIC 수치 비교 | 변경 배경 설명 |
| Q018 | 리벨리온이 제공하는 서비스는 뭐야? | hybrid | ORGANIZATION 엔티티 | NPU 서비스 설명 |
| Q019 | 일반 분과와 소상공인 분과의 민간매칭 방식이 어떻게 달라? | hybrid | CATEGORY 분과 엔티티 | 매칭 방식 세부 규정 |
| Q020 | NIPA가 이 사업에서 하는 역할은 뭐야? | hybrid | ORGANIZATION.NIPA | 운영 역할 설명 |
| Q021 | AI반도체 분과 신청 마감일은 언제고 신청 방법은? | hybrid | EVENT 날짜 | 신청 절차 설명 |
| Q022 | 소상공인이 글로벌 분과에 신청할 수 있어? | hybrid | CATEGORY 자격 조회 | 자격 조건 텍스트 |

#### D. 경계 케이스 (3개) — 어려운 질문 / 정보 없는 질문

| ID | 질문 | 기대 소스 | 기대 결과 | 목적 |
|----|------|-----------|-----------|------|
| Q023 | 이 사업에 반도체 기업이 수요기업으로 참여할 수 있어? | hybrid | 조건부 가능 설명 | 암묵적 추론 필요 |
| Q024 | 과제 선정 시 평가 배점 기준표는? | vector | 문서에 없음(폴백) | 문서 범위 밖 검증 |
| Q025 | 2026년 AI바우처 예산은 얼마야? | llm_only | 알 수 없음 | 미래 정보 환각 방지 |

---

## 4. 온톨로지 사전 구축 계획

테스트 실행 전 `ai-voucher-2025` 문서 네임스페이스에 아래 엔티티를 등록해야 한다.

### 4.1 스키마 추가 (domain_schema.json)

```json
entity_types:
  - PROGRAM     : 사업/프로그램 (name, budget, year)
  - DIVISION    : 분과 (quota, target)

relation_types:
  - MANAGES     : ORGANIZATION → PROGRAM
  - HAS_DIVISION: PROGRAM → DIVISION
  - PARTNERS_WITH: ORGANIZATION → ORGANIZATION
  - RESTRICTS   : PROGRAM → ORGANIZATION (중복금지)
```

### 4.2 사전 등록 엔티티 목록

| 타입 | 이름 | 핵심 속성 |
|------|------|-----------|
| PROGRAM | AI바우처 2025 | budget:276억, year:2025, quota:130 |
| PROGRAM | AI바우처 2024 | budget:425억, year:2024, quota:201 |
| ORGANIZATION | 과학기술정보통신부 | role:주관기관 |
| ORGANIZATION | NIPA | role:운영기관, full_name:정보통신산업진흥원 |
| ORGANIZATION | 리벨리온 | type:AI반도체, role:NPU공급사 |
| ORGANIZATION | 퓨리오사AI | type:AI반도체, role:NPU공급사 |
| ORGANIZATION | KT클라우드 | type:CSP, role:클라우드파트너 |
| ORGANIZATION | NHN클라우드 | type:CSP, role:클라우드파트너 |
| ORGANIZATION | 엘리스그룹 | type:CSP, role:클라우드파트너 |
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
| EVENT | 과제수행기간시작 | date:2025-05-01 |
| EVENT | 과제수행기간종료 | date:2025-11-30 |

---

## 5. 시스템 아키텍처

```
[통합 테스트 시스템]

Frontend
  └─ IntegrationTestRunner.tsx
       ├─ 프로젝트 선택 드롭다운
       ├─ [테스트 실행] 버튼
       ├─ 실행 이력 목록 (pass율, 시간)
       └─ 실행 상세 뷰
            ├─ 케이스별 카드 (pass/fail/skip)
            ├─ 예상 소스 vs 실제 소스
            ├─ 답변 텍스트 + 증거
            └─ 온톨로지 히트 목록

Backend
  ├─ POST /api/integration-test/run
  │    ├─ QA 데이터셋 로드 (project_name 기반)
  │    ├─ 각 케이스 → hybridAsk 호출
  │    ├─ 소스 판정 (ontology_hits / vector_hits)
  │    ├─ 키워드 매칭 (pass/fail 판정)
  │    └─ 결과 저장 → test_runs/{run_id}.json
  │
  ├─ GET /api/integration-test/projects
  ├─ GET /api/integration-test/{project}/runs
  └─ GET /api/integration-test/{project}/runs/{run_id}

Storage
  └─ storage/{company}/{project}/test_runs/
       ├─ {run_id}.json  (전체 결과)
       └─ qa_dataset.json (QA 케이스 정의)

Test Data
  └─ test_data/
       └─ ai-voucher-2025/
            ├─ qa_dataset.json
            └─ expected_ontology.json
```

---

## 6. 테스트 결과 데이터 구조

```json
{
  "run_id": "run-20260514-1030",
  "project": "ai-voucher-2025",
  "timestamp": "2026-05-14T10:30:00Z",
  "doc_uploaded": "2025년_AI바우처_사업설명회.pdf",
  "summary": {
    "total": 25,
    "passed": 22,
    "failed": 3,
    "pass_rate": 0.88,
    "duration_sec": 18.4,
    "by_source": {
      "ontology": { "total": 7, "passed": 6 },
      "vector":   { "total": 9, "passed": 8 },
      "hybrid":   { "total": 6, "passed": 5 },
      "edge":     { "total": 3, "passed": 3 }
    }
  },
  "cases": [
    {
      "id": "Q001",
      "question": "2025년 AI바우처 총 예산은 얼마야?",
      "expected_source": "ontology",
      "expected_keywords": ["276억", "276,000,000"],
      "actual_source": "ontology",
      "actual_answer": "2025년 AI바우처 총 예산은 276억원입니다.",
      "ontology_hits": 2,
      "vector_hits": 0,
      "llm_used": true,
      "keyword_matched": true,
      "source_matched": true,
      "passed": true,
      "evidence": [
        { "type": "ontology", "entity": "2025총예산", "value": "276억원" }
      ],
      "duration_ms": 620
    }
  ]
}
```

---

## 7. pass/fail 판정 기준

```python
def evaluate_case(case, response):
    # 1. 소스 판정
    ont_hits = response["quality_metrics"]["ontology_hits"]
    vec_hits  = response["quality_metrics"]["vector_hits"]

    if ont_hits > 0 and vec_hits == 0:
        actual_source = "ontology"
    elif ont_hits == 0 and vec_hits > 0:
        actual_source = "vector"
    elif ont_hits > 0 and vec_hits > 0:
        actual_source = "hybrid"
    else:
        actual_source = "llm_only"

    source_matched = (actual_source == case["expected_source"])

    # 2. 키워드 매칭
    answer = response["answer"].lower()
    keyword_matched = any(
        kw.lower() in answer
        for kw in case.get("expected_keywords", [])
    )

    # 3. 경계 케이스 특수 처리
    if case.get("expect_no_answer"):
        keyword_matched = not any(
            kw.lower() in answer
            for kw in case.get("forbidden_keywords", [])
        )

    passed = source_matched and keyword_matched
    return passed, actual_source, source_matched, keyword_matched
```

---

## 8. 구현 단계별 계획

### Phase 1 — 데이터 준비 (예상 2시간)

```
1-1. PDF 업로드 → RAG 인덱싱 확인
1-2. 온톨로지 스키마 추가 (PROGRAM, DIVISION)
1-3. 엔티티 22개 사전 등록 (ai-voucher-2025 네임스페이스)
1-4. qa_dataset.json 작성 (25개 케이스)
```

### Phase 2 — Backend 구현 (예상 3시간)

```
2-1. test_data/ 디렉토리 구조 + qa_dataset.json 로드
2-2. POST /api/integration-test/run 구현
     - QA 순회, hybridAsk 호출, 결과 평가, 저장
2-3. GET /api/integration-test/{project}/runs 구현
2-4. GET /api/integration-test/{project}/runs/{run_id} 구현
2-5. test_runs/ 스토리지 연동
```

### Phase 3 — Frontend 구현 (예상 2시간)

```
3-1. 사이드바에 "통합 테스트" 메뉴 추가
3-2. IntegrationTestRunner.tsx 컴포넌트 구현
     - 프로젝트 선택, 실행 버튼, 진행 상태
     - 실행 이력 목록
     - 케이스별 상세 뷰
3-3. api.ts에 통합 테스트 API 추가
```

### Phase 4 — 검증 (예상 1시간)

```
4-1. 테스트 실행 → 결과 확인
4-2. 실패 케이스 원인 분석
4-3. 온톨로지/RAG 보완 후 재실행
```

---

## 9. 성공 기준

| 항목 | 목표 |
|------|------|
| 전체 pass율 | 80% 이상 |
| 온톨로지 전용 케이스 pass율 | 85% 이상 |
| 벡터 전용 케이스 pass율 | 75% 이상 |
| 하이브리드 케이스 pass율 | 70% 이상 |
| 소스 판정 정확도 | 90% 이상 |
| 경계 케이스 환각 방지율 | 100% (Q025 필수 통과) |

---

## 10. 부록: QA 데이터셋 JSON 전문 (qa_dataset.json)

파일 위치: `test_data/ai-voucher-2025/qa_dataset.json`

```json
{
  "project": "ai-voucher-2025",
  "version": "1.0",
  "doc": "2025년 AI바우처 사업설명회 발표자료.pdf",
  "ontology_namespace": "ai-voucher-2025",
  "created": "2026-05-14",
  "cases": [
    {
      "id": "Q001", "tags": ["ontology", "budget"],
      "question": "2025년 AI바우처 총 예산은 얼마야?",
      "expected_source": "ontology",
      "expected_entity_type": "METRIC",
      "expected_keywords": ["276억", "276,000"]
    },
    {
      "id": "Q002", "tags": ["ontology", "quota"],
      "question": "2025년 총 과제수는 몇 개야?",
      "expected_source": "ontology",
      "expected_entity_type": "METRIC",
      "expected_keywords": ["130개", "130"]
    },
    {
      "id": "Q003", "tags": ["ontology", "division"],
      "question": "글로벌 분과의 2025년 과제수는?",
      "expected_source": "ontology",
      "expected_entity_type": "CATEGORY",
      "expected_keywords": ["30개", "30"]
    },
    {
      "id": "Q004", "tags": ["ontology", "organization"],
      "question": "AI반도체 분과 CSP 컨소시엄 구성 기업을 모두 나열해줘",
      "expected_source": "ontology",
      "expected_entity_type": "ORGANIZATION",
      "expected_keywords": ["리벨리온", "퓨리오사", "KT클라우드", "NHN"]
    },
    {
      "id": "Q005", "tags": ["ontology", "organization"],
      "question": "이 사업의 주관 기관은 어디야?",
      "expected_source": "ontology",
      "expected_entity_type": "ORGANIZATION",
      "expected_keywords": ["NIPA", "정보통신산업진흥원", "과학기술정보통신부"]
    },
    {
      "id": "Q006", "tags": ["ontology", "quota"],
      "question": "공급기업이 연간 신청할 수 있는 최대 과제수는?",
      "expected_source": "ontology",
      "expected_entity_type": "METRIC",
      "expected_keywords": ["2개", "분과별 1개"]
    },
    {
      "id": "Q007", "tags": ["ontology", "event"],
      "question": "과제 수행 기간은 언제부터 언제까지야?",
      "expected_source": "ontology",
      "expected_entity_type": "EVENT",
      "expected_keywords": ["5월", "11월", "2025"]
    },
    {
      "id": "Q008", "tags": ["vector", "procedure"],
      "question": "공급기업 Pool 신규 등록 절차를 설명해줘",
      "expected_source": "vector",
      "expected_keywords": ["신청서", "제출서류", "AI솔루션"]
    },
    {
      "id": "Q009", "tags": ["vector", "policy"],
      "question": "데이터 관련 비용은 사업비로 쓸 수 있어?",
      "expected_source": "vector",
      "expected_keywords": ["불가", "무상제공", "자체비용"]
    },
    {
      "id": "Q010", "tags": ["vector", "documents"],
      "question": "글로벌 분과에서 제출해야 하는 서류는?",
      "expected_source": "vector",
      "expected_keywords": ["K-SURE", "국제거래문서", "NDA"]
    },
    {
      "id": "Q011", "tags": ["vector", "matching"],
      "question": "민간매칭에서 현금과 현물의 차이는 뭐야?",
      "expected_source": "vector",
      "expected_keywords": ["현금", "현물", "인건비"]
    },
    {
      "id": "Q012", "tags": ["vector", "restriction"],
      "question": "타기관 사업과 중복 지원이 안 되는 경우는?",
      "expected_source": "vector",
      "expected_keywords": ["KOICA", "KOTRA", "수출바우처"]
    },
    {
      "id": "Q013", "tags": ["vector", "medical"],
      "question": "의료 분과에서 병원이 신청할 때 제한 사항은?",
      "expected_source": "vector",
      "expected_keywords": ["병원당", "1개", "진료과"]
    },
    {
      "id": "Q014", "tags": ["vector", "bonus"],
      "question": "가점을 받을 수 있는 항목들은 뭐야?",
      "expected_source": "vector",
      "expected_keywords": ["청년기업", "지역기업", "클라우드"]
    },
    {
      "id": "Q015", "tags": ["vector", "procedure"],
      "question": "공급기업 변경 등록 대상은 누구야?",
      "expected_source": "vector",
      "expected_keywords": ["기등록", "변경등록", "우정사항"]
    },
    {
      "id": "Q016", "tags": ["vector", "hardware"],
      "question": "소상공인 분과에서 하드웨어 지원이 가능해?",
      "expected_source": "vector",
      "expected_keywords": ["하드웨어", "소상공인"]
    },
    {
      "id": "Q017", "tags": ["hybrid", "comparison"],
      "question": "2024년과 2025년을 비교하면 예산과 과제수가 어떻게 달라졌어?",
      "expected_source": "hybrid",
      "expected_keywords": ["276억", "425억", "130개", "201개", "35%"]
    },
    {
      "id": "Q018", "tags": ["hybrid", "organization"],
      "question": "리벨리온이 제공하는 서비스는 뭐야?",
      "expected_source": "hybrid",
      "expected_keywords": ["NPU", "AI반도체", "컨소시엄"]
    },
    {
      "id": "Q019", "tags": ["hybrid", "matching"],
      "question": "일반 분과와 소상공인 분과의 민간매칭 방식이 어떻게 달라?",
      "expected_source": "hybrid",
      "expected_keywords": ["일반", "소상공인", "현금", "현물"]
    },
    {
      "id": "Q020", "tags": ["hybrid", "organization"],
      "question": "NIPA가 이 사업에서 하는 역할은 뭐야?",
      "expected_source": "hybrid",
      "expected_keywords": ["NIPA", "운영", "정보통신산업진흥원"]
    },
    {
      "id": "Q021", "tags": ["hybrid", "deadline"],
      "question": "AI반도체 분과 신청 마감일은 언제고 신청 방법은?",
      "expected_source": "hybrid",
      "expected_keywords": ["3월 24일", "3.24", "2025-03-24"]
    },
    {
      "id": "Q022", "tags": ["hybrid", "eligibility"],
      "question": "소상공인이 글로벌 분과에 신청할 수 있어?",
      "expected_source": "hybrid",
      "expected_keywords": ["해외", "글로벌", "수요처"]
    },
    {
      "id": "Q023", "tags": ["edge", "inference"],
      "question": "이 사업에 반도체 기업이 수요기업으로 참여할 수 있어?",
      "expected_source": "hybrid",
      "expected_keywords": ["중소기업", "중견기업", "자격"]
    },
    {
      "id": "Q024", "tags": ["edge", "out_of_scope"],
      "question": "과제 선정 시 평가 배점 기준표는?",
      "expected_source": "vector",
      "expected_keywords": [],
      "expect_low_confidence": true,
      "note": "문서에 없는 정보 — 폴백 동작 검증"
    },
    {
      "id": "Q025", "tags": ["edge", "hallucination"],
      "question": "2026년 AI바우처 예산은 얼마야?",
      "expected_source": "llm_only",
      "expected_keywords": [],
      "forbidden_keywords": ["300억", "400억", "500억"],
      "expect_no_answer": true,
      "note": "미래 정보 — 환각 방지 검증"
    }
  ]
}
```
