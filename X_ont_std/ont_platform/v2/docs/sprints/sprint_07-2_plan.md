# Sprint 07-2 — Query Planner 프로토타입 (filter intent)

> **에픽**: Sprint 07 — v2.0 기반 구축 (07-1 / 07-2 / 07-3)  
> **기간**: 2026-05-13  
> **상태**: ✅ 완료 — 전체 53/53 테스트 통과  
> **선행**: [sprint_07-1_plan.md](sprint_07-1_plan.md)

---

## 1. 스프린트 목표

v1.0의 `query_classifier.py` + `ontology_query_engine.py`를 v2.0 서비스 레이어로 재구성한다.  
이번 Sprint의 DoD는 **filter intent**에 한정하며, compare / calculate / hybrid는 구조만 열어둔다.

---

## 2. 완료 기준 (DoD)

| # | 기준 |
|---|------|
| D01 | 질문을 descriptive / filter 중 최소 구분 가능 |
| D02 | filter 질문에서 entity_type, property_key, property_value 추출 또는 수동 입력 fallback |
| D03 | `OntologyService.filter_by_property(ctx, ...)` — tenant scope 내 JSON만 검색 |
| D04 | `POST /api/hybrid/ask` — filter 결과를 구조화 응답으로 반환 |
| D05 | 다른 company/project의 ontology JSON은 검색되지 않음 |
| D06 | Sprint 07-1 테스트 39개가 계속 통과 |
| D07 | Sprint 07-2 전용 테스트 추가 및 통과 |

---

## 3. 백로그

| ID | 항목 | 우선순위 | 상태 |
|----|------|----------|------|
| S-01 | `QueryPlannerService` 신규 작성 (v1.0 참고) | 🔴 | ✅ |
| S-02 | `OntologyService.filter_by_property` 추가 | 🔴 | ✅ |
| S-03 | `OntologyService.find_by_name` (fallback) 추가 | 🔴 | ✅ |
| S-04 | `POST /api/hybrid/ask` 엔드포인트 | 🔴 | ✅ |
| S-05 | `test_sprint07_2_dod.py` DoD 자동 테스트 | 🔴 | ✅ |

---

## 4. 핵심 설계 결정

### 분류 전략 (3단계 폴백)

```
1순위: LLM (Gemini API) — 정확한 구조화 분류
2순위: 키워드 휴리스틱 — API 키 없을 때 (테스트 환경)
3순위: descriptive 폴백 — 분류 실패 시
```

### filter 처리 흐름

```
POST /api/hybrid/ask
  ↓
QueryPlannerService.execute(question, ctx, doc_ids, override)
  ↓ type == "filter"
  ├─ property_key + property_value 있음 → filter_by_property(ctx, ...)
  └─ 없음 → find_by_name(ctx, question, ...) [fallback]
  ↓
{ query_type, classification, results, count }
```

### override 파라미터

테스트 및 디버깅용으로 분류 결과를 수동 지정 가능:
```json
{
  "question": "...",
  "override": {
    "type": "filter",
    "entity_type": "PRODUCT",
    "property_key": "category",
    "property_value": "hardware"
  }
}
```

### compare / calculate / hybrid

Sprint 07-2 범위 외. `_handle_unsupported()`로 안내 메시지 반환. 07-3 이후 구현.

---

## 5. 산출물

| 파일 | 역할 |
|------|------|
| `src/backend/app/services/query_planner.py` | QueryPlannerService (신규) |
| `src/backend/app/services/ontology.py` | filter_by_property, find_by_name 추가 |
| `src/backend/app/main.py` | POST /api/hybrid/ask 추가 |
| `src/backend/tests/test_sprint07_2_dod.py` | DoD 자동 테스트 (14개) |

**v1.0 참조**:
- `archive/v1.0/backend/app/query_classifier.py`
- `archive/v1.0/backend/app/ontology_query_engine.py`

---

## 6. 완료 기록

| 항목 | 결과 |
|------|------|
| Sprint 07-2 단독 | 14/14 통과 |
| 07-1 + 07-2 누적 | 53/53 통과 |
| 실행 환경 | conda env `claud_be` / Python 3.11.15 |

---

## 7. 다음 단계

- **07-3**: 범용 온톨로지 완성 (app_context 도메인 로직 분리) → [sprint_07-3_plan.md](sprint_07-3_plan.md)
