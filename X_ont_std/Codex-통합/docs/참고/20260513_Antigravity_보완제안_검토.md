# 20260513 Antigravity 보완 제안 검토

작성일: 2026-05-13  
대상 문서: `Codex-통합/docs` 최종 설계 문서 세트  
성격: 외부 제안 보관 및 검토 의견

---

## 1. 제안 요약

Antigravity는 `Codex-통합/docs` 문서 세트에 대해 다음 네 가지 보완을 제안했다.

| 번호 | 제안 | 요지 |
| --- | --- | --- |
| 1 | Plan Validator 추가 | LLM이 만든 Query Plan을 실행 전에 live schema와 권한 범위로 검증 |
| 2 | AI 품질 모니터링 구체화 | token cost, confidence, grounding, latency 등을 tenant별로 추적 |
| 3 | Reasoning Trace Graph 추가 | 답변 생성 경로를 React Flow로 시각화 가능한 graph JSON으로 반환 |
| 4 | 프리미엄 UX 가이드라인 | 다크 모드, 디자인 토큰, 마이크로 인터랙션 등 UI 품질 기준 강화 |

---

## 2. Codex 검토 의견

### 2.1 Plan Validator

반영 가치: 높음

현재 설계의 Query Planner -> Executor 구조는 좋지만, LLM이 존재하지 않는 타입, 속성, 관계, 연산자를 제안할 수 있다. 따라서 실행 전에 `PlanValidator` 계층이 필요하다.

검증 항목:

- 존재하는 entity type인지
- 존재하는 property인지
- 허용된 operator인지
- aggregate 대상 field가 number인지
- relation path가 schema상 가능한지
- 사용자가 접근 가능한 doc_ids인지
- company/project scope를 벗어나지 않는지

권장 pipeline:

```text
QueryPlanner
  -> PlanValidator
  -> OntologyQueryEngine / SearchService
  -> HybridAnswerService
```

### 2.2 AI 품질 모니터링

반영 가치: 높음

Audit Log가 행위 기록만 담으면 운영 중 답변 품질, 비용, 실패 패턴을 파악하기 어렵다. Hybrid Query 실행 이벤트에 AI 품질 지표를 추가하는 것이 좋다.

권장 필드:

- `prompt_tokens`
- `completion_tokens`
- `total_tokens`
- `estimated_cost`
- `llm_model`
- `planner_fallback_used`
- `plan_validation_errors`
- `llm_self_confidence`
- `grounding_score`
- `plan_validity_score`
- `evidence_count`
- `latency_ms`

주의: LLM의 자기 확신도는 신뢰 지표로 단독 사용하지 않는다. `grounding_score`, `plan_validity_score`처럼 시스템이 계산 가능한 지표와 분리한다.

### 2.3 Reasoning Trace Graph

반영 가치: 높음

현재 응답의 `structured_data`, `evidence`, `trace`는 기계적 검증에는 좋지만, 사용자가 답변 경로를 직관적으로 이해하기에는 부족하다. React Flow로 표시 가능한 graph path JSON을 추가하면 신뢰성이 높아진다.

예시:

```json
{
  "reasoning_trace_graph": {
    "nodes": [
      {"id": "q1", "type": "question", "label": "사용자 질문"},
      {"id": "plan1", "type": "query_plan", "label": "Product.billing_model contains Serverless"},
      {"id": "ent-P001", "type": "ontology_entity", "label": "Snowpipe"},
      {"id": "doc-001-p3", "type": "document_chunk", "label": "Snowflake 소개서 p.3"},
      {"id": "answer1", "type": "answer", "label": "최종 답변"}
    ],
    "edges": [
      {"source": "q1", "target": "plan1", "label": "planned_as"},
      {"source": "plan1", "target": "ent-P001", "label": "matched"},
      {"source": "ent-P001", "target": "doc-001-p3", "label": "grounded_by"},
      {"source": "doc-001-p3", "target": "answer1", "label": "supports"}
    ]
  }
}
```

### 2.4 프리미엄 UX 가이드라인

반영 가치: 중간

디자인 품질을 높이는 방향은 좋다. 다만 업무용 엔터프라이즈 도구에서 글래스모피즘이나 강한 시각 효과를 핵심 화면에 과도하게 적용하면 가독성과 신뢰성이 떨어질 수 있다.

권장 방향:

- 다크 모드는 선택 지원
- 디자인 토큰은 적극 도입
- 마이크로 인터랙션은 상태 변화, 로딩, 권한 차단에 제한적으로 사용
- 글래스모피즘은 로그인, 대시보드 보조 영역 등 제한된 곳에만 사용
- 핵심 업무 화면은 명료성, 대비, 정보 밀도, 스캔 가능성을 우선한다

---

## 3. 반영 우선순위

| 우선순위 | 항목 | 판단 |
| --- | --- | --- |
| 1 | Plan Validator | 필수급 |
| 2 | Reasoning Trace Graph | 필수급 |
| 3 | AI 품질 모니터링 | 권장 |
| 4 | 프리미엄 UX 가이드 | 절제해서 반영 |

---

## 4. 대상 문서 매핑

| 반영 항목 | 대상 문서 |
| --- | --- |
| Plan Validator | `FINAL_DESIGN.md`, `06_ACCEPTANCE_TEST_PLAN.md` |
| Reasoning Trace Graph | `FINAL_DESIGN.md`, `03_FINAL_API_SPEC.md`, `07_UX_AND_OPERATIONS.md` |
| AI 품질 모니터링 | `04_FINAL_DATA_SCHEMA.md`, `07_UX_AND_OPERATIONS.md` |
| 프리미엄 UX | `07_UX_AND_OPERATIONS.md` |

---

## 5. 결론

Antigravity 제안은 현재 `Codex-통합` 문서의 실행 가능성을 해치지 않으면서 신뢰성, 관측성, 설명 가능성, UX 품질을 높일 수 있는 보완이다.

다만 UI 효과 중심 제안은 업무형 제품의 명료성을 해치지 않는 범위에서 제한적으로 반영한다.
