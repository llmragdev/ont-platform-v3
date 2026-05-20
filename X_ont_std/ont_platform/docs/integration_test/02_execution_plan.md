# 통합 테스트 실행 계획
## ont_platform v3.0 — AI바우처 프로젝트 기반 자동 검증

작성일: 2026-05-14

---

## 전체 일정 (예상 총 8시간)

```
Phase 1  데이터 준비          2h   ──► PDF 업로드, 온톨로지 구축, QA 데이터셋
Phase 2  Backend 구현          3h   ──► 테스트 러너 API, 결과 스토리지
Phase 3  Frontend 구현         2h   ──► 실행 UI, 결과 조회 화면
Phase 4  실행 및 검증          1h   ──► 실제 테스트, 실패 분석, 보완
```

---

## Phase 1 — 데이터 준비

### 1-1. PDF 업로드 + RAG 인덱싱

```
작업: ont_platform 프론트엔드에서 PDF 업로드
      POST /api/documents/upload
확인: GET /api/documents → 목록에 있는지
     벡터 청크 수 확인 (storage/demo-co/proj-01/vector_db/)
```

### 1-2. 온톨로지 스키마 확장

기존 스키마에 2개 타입 추가:

```
PROGRAM  : 사업/프로그램 단위 (budget, year, quota 속성)
DIVISION : 사업 분과 단위 (quota_2025, quota_2024, target 속성)
```

추가 방법: 스키마 정의 화면 또는 API 직접 호출

### 1-3. 온톨로지 엔티티 등록

`ai-voucher-2025` 네임스페이스에 22개 엔티티 등록.
구체적인 엔티티 목록은 설계 문서 4.2절 참조.

등록 방법:
- 인스턴스 편집 화면에서 수동 등록
- 또는 시드 스크립트로 일괄 등록 (권장)

### 1-4. QA 데이터셋 파일 배치

```
위치: test_data/ai-voucher-2025/qa_dataset.json
내용: 25개 케이스 (설계 문서 10절 참조)
```

---

## Phase 2 — Backend 구현

### 신규 파일 목록

```
app/api/integration_test.py      ← 테스트 러너 라우터
test_data/
  └─ ai-voucher-2025/
       └─ qa_dataset.json
```

### API 명세

#### POST /api/integration-test/run
```json
Request:
{
  "project": "ai-voucher-2025",
  "company_id": "demo-co",
  "project_id": "proj-01"
}

Response (즉시):
{
  "run_id": "run-20260514-1030",
  "status": "running",
  "total_cases": 25
}
```

실제 실행은 백그라운드 또는 동기 처리.  
케이스 25개 × 평균 1~2초 = 약 30~50초 예상.

#### GET /api/integration-test/projects
```json
Response:
[
  {
    "project": "ai-voucher-2025",
    "run_count": 3,
    "last_run": "2026-05-14T10:30:00Z",
    "last_pass_rate": 0.88
  }
]
```

#### GET /api/integration-test/{project}/runs
```json
Response:
{
  "project": "ai-voucher-2025",
  "runs": [
    {
      "run_id": "run-20260514-1030",
      "timestamp": "2026-05-14T10:30:00Z",
      "total": 25,
      "passed": 22,
      "pass_rate": 0.88,
      "duration_sec": 18.4
    }
  ]
}
```

#### GET /api/integration-test/{project}/runs/{run_id}
```json
Response:
{
  "run_id": "...",
  "summary": { ... },
  "cases": [ ... ]  // 25개 케이스 상세
}
```

### 핵심 구현: 평가 로직

```python
# 소스 판정
def detect_source(quality_metrics):
    ont = quality_metrics.get("ontology_hits", 0)
    vec = quality_metrics.get("vector_hits", 0)
    if ont > 0 and vec == 0:   return "ontology"
    if ont == 0 and vec > 0:   return "vector"
    if ont > 0 and vec > 0:    return "hybrid"
    return "llm_only"

# 키워드 판정
def check_keywords(answer, keywords, forbidden=None):
    lower = answer.lower()
    if forbidden:
        return not any(kw.lower() in lower for kw in forbidden)
    if not keywords:
        return True  # 키워드 없으면 통과
    return any(kw.lower() in lower for kw in keywords)

# 최종 pass/fail
passed = source_matched and keyword_matched
```

---

## Phase 3 — Frontend 구현

### 신규 파일

```
src/components/IntegrationTestRunner.tsx
```

### 화면 구성

```
┌─────────────────────────────────────────────────────┐
│ 통합 테스트                                           │
│                                                      │
│ 프로젝트  [ai-voucher-2025 ▼]   [▶ 테스트 실행]      │
│                                                      │
│ ── 실행 이력 ──────────────────────────────────────  │
│  2026-05-14 10:30  22/25 (88%)  18.4초  [상세보기]  │
│  2026-05-14 09:10  18/25 (72%)  22.1초  [상세보기]  │
│                                                      │
│ ── 케이스 상세 ─────────────────────────────────── │
│                                                      │
│  필터: [전체▼]  [소스: 전체▼]  [상태: 전체▼]        │
│                                                      │
│  Q001 ✅  온톨로지    2025년 AI바우처 총 예산은?      │
│       소스: ontology (기대: ontology)               │
│       답변: "2025년 AI바우처 총 예산은 276억원..."   │
│       근거: [METRIC:2025총예산 = 276억원]           │
│                                                      │
│  Q008 ✅  벡터검색    공급기업 Pool 신규 등록 절차?  │
│       소스: vector (기대: vector)                   │
│       답변: "공급기업 Pool 신규 등록은..."           │
│       근거: [Doc:AI바우처PDF p.4 score=0.91]       │
│                                                      │
│  Q017 ✅  하이브리드  2024년 vs 2025년 비교          │
│       소스: hybrid (기대: hybrid)                   │
│       온톨로지 2건 + 벡터 3건                       │
│                                                      │
│  Q025 ❌  경계케이스  2026년 AI바우처 예산은?        │
│       소스: llm_only (기대: llm_only)               │
│       키워드 실패: "300억" 포함됨 (환각 감지!)       │
└─────────────────────────────────────────────────────┘
```

### 사이드바 메뉴 추가 위치

```
운영 섹션 하단에 추가:
  - 감사 로그 (기존)
  - 통합 테스트  ← 신규
```

---

## Phase 4 — 실행 및 검증

### 4-1. 첫 실행 예상 결과

```
초기 상태 (온톨로지 엔티티 없음, RAG만 있음):
  - 온톨로지 케이스 Q001~Q007: 대부분 FAIL (소스가 vector로 잘못 판정)
  - 벡터 케이스 Q008~Q016: 대부분 PASS
  - 하이브리드 케이스: 절반 FAIL

온톨로지 엔티티 등록 후:
  - 온톨로지 케이스: 85% 이상 PASS 목표
  - 전체: 80% 이상 PASS 목표
```

### 4-2. 실패 케이스 분류

```
실패 유형 A: 소스 불일치
  → 원인: 온톨로지 엔티티 미등록 또는 질문 키워드 미매칭
  → 조치: 엔티티 추가 등록

실패 유형 B: 키워드 불일치
  → 원인: LLM이 숫자 표현 변환 (276억원 → 2,760,000만원)
  → 조치: QA 데이터셋 키워드 확장

실패 유형 C: 환각 감지
  → 원인: Q025 등에서 LLM이 없는 정보 생성
  → 조치: 환각 사례 기록, 프롬프트 개선 검토
```

---

## 산출물 체크리스트

```
데이터
  ☐ PDF 업로드 완료 + RAG 인덱싱 확인
  ☐ 스키마에 PROGRAM, DIVISION 추가
  ☐ ai-voucher-2025 네임스페이스 엔티티 22개 등록
  ☐ test_data/ai-voucher-2025/qa_dataset.json 배치

Backend
  ☐ POST /api/integration-test/run 구현
  ☐ GET /api/integration-test/projects 구현
  ☐ GET /api/integration-test/{project}/runs 구현
  ☐ GET /api/integration-test/{project}/runs/{run_id} 구현
  ☐ 평가 로직 (소스 판정 + 키워드 매칭) 구현
  ☐ test_runs/ 결과 저장 구현

Frontend
  ☐ IntegrationTestRunner.tsx 구현
  ☐ api.ts에 통합 테스트 API 추가
  ☐ 사이드바 메뉴 "통합 테스트" 추가
  ☐ 케이스별 소스 배지 (온톨로지/벡터/하이브리드)
  ☐ 증거 섹션 (온톨로지 히트 + 벡터 청크)
  ☐ 통과/실패 필터링

검증
  ☐ 25개 케이스 실행 완료
  ☐ 전체 pass율 80% 이상
  ☐ Q025 환각 방지 통과
  ☐ 실패 케이스 원인 분석 문서화
```
