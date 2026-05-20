# Sprint 07-3 — 범용 온톨로지 완성 (app_context 분리)

> **에픽**: Sprint 07 — v2.0 기반 구축 (07-1 / 07-2 / 07-3)  
> **기간**: 2026-05-13  
> **상태**: ✅ 완료 — 전체 76/76 테스트 통과  
> **선행**: [sprint_07-2_plan.md](sprint_07-2_plan.md)

---

## 1. 스프린트 목표

v1.0의 `app_context.py`에 하드코딩된 도메인 로직(Order/Customer/Product 워크플로우)을  
v2.0 서비스 레이어로 분리해, **어떤 도메인 온톨로지에도 동일 코드베이스를 적용**할 수 있게 한다.

### v1.0 app_context.py 현황

```
AppContext.__init__()
  ├── OntologyService(raw, save)    ← 인메모리 dict 기반, 도메인 고정
  ├── PolicyEngine(audit, schema)   ← ORDER_REGION_MAP 하드코딩
  ├── WorkflowService(ont, policy)  ← Order 5액션 7전환 하드코딩
  ├── WorkflowGraphService          ← SSE 스트리밍 실행기
  └── VectorSearchService()         ← 단일 Chroma, 경로 하드코딩
```

목표: 위 로직을 v2.0 `TenantContext` + `storage_config` 기반으로 이식.

---

## 2. 완료 기준 (DoD)

### 2.1 워크플로우 이식

| # | 기준 |
|---|------|
| D01 | `/api/workflow/queue` — TenantContext 기반 사용자 권한 내 주문 목록 |
| D02 | `/api/workflow/execute` — 주문 상태 전환, TenantContext 권한 확인 |
| D03 | `/api/workflow-graphs/*` — CRUD + SSE 실행 이식 |
| D04 | 기존 D15 대리 검증 제거 — 실제 `/api/workflow/*` smoke test로 교체 |

### 2.2 도메인 설정 외부화

| # | 기준 |
|---|------|
| D05 | 워크플로우 전환 정의(`from_status`, `action_name`, `to_status`)를 `config/workflow.json`으로 분리 |
| D06 | `policy.default.json`의 마스킹 규칙이 도메인 변경 없이 동작 |
| D07 | `app_context.py` 없이 `/api/workflow/*` 동작 |

### 2.3 범용성 검증

| # | 기준 |
|---|------|
| D08 | 주문 도메인 외 새로운 엔티티 타입을 `config/domain.json` 편집만으로 추가 가능 |
| D09 | Sprint 07-1 + 07-2 테스트 53개 계속 통과 |
| D10 | Sprint 07-3 전용 테스트 추가 및 통과 |

---

## 3. 백로그

| ID | 항목 | 우선순위 |
|----|------|----------|
| S-01 | v1.0 WorkflowService → v2.0 이식 | 🔴 |
| S-02 | v1.0 WorkflowGraphService + Engine → v2.0 이식 | 🔴 |
| S-03 | v1.0 PolicyEngine → 도메인 설정 외부화 | 🔴 |
| S-04 | `/api/workflow/*` 엔드포인트 v2.0 등록 | 🔴 |
| S-05 | D15 smoke test 실제 엔드포인트로 교체 | 🟡 |
| S-06 | `config/workflow.json` 도메인 설정 분리 | 🟡 |
| S-07 | v1.0 → v2.0 데이터 마이그레이션 스크립트 | 🟡 |
| S-08 | `test_sprint07_3_dod.py` DoD 자동 테스트 | 🔴 |

---

## 4. 핵심 설계 결정

### app_context.py 처리 전략

```
Option A: 완전 제거
  - app_context.py를 v2.0 서비스 조합으로 완전 대체
  - 장점: 의존성 완전 제거
  - 단점: WorkflowGraphEngine(SSE) 이식 비용 높음

Option B: Adapter 패턴 (권장)
  - app_context.py를 legacy wrapper로 유지
  - 새 엔드포인트는 새 서비스, 기존 엔드포인트는 wrapper 경유
  - 장점: 점진적 전환 가능
  - 단점: 과도기 코드 존재
```

→ 07-3: Option B로 착수, 안정화 후 Option A 전환 검토.

### 도메인 설정 구조 (config/workflow.json 예시)

```json
{
  "object_type": "Order",
  "actions": ["ApproveOrder", "RejectOrder", "HoldOrder", "FulfillOrder", "CloseOrder"],
  "transitions": [
    {"from": "Submitted", "action": "ApproveOrder", "to": "Approved"},
    {"from": "Submitted", "action": "HoldOrder",    "to": "Review"},
    {"from": "Submitted", "action": "RejectOrder",  "to": "Rejected"},
    {"from": "Review",    "action": "ApproveOrder", "to": "Approved"},
    {"from": "Review",    "action": "RejectOrder",  "to": "Rejected"},
    {"from": "Approved",  "action": "FulfillOrder", "to": "Fulfilled"},
    {"from": "Fulfilled", "action": "CloseOrder",   "to": "Closed"}
  ]
}
```

---

## 5. 예상 산출물

| 파일 | 역할 |
|------|------|
| `src/backend/app/services/workflow.py` | WorkflowService v2.0 이식 |
| `src/backend/app/api/workflow.py` | /api/workflow/* 라우터 |
| `src/backend/app/config/workflow.json` | 도메인 설정 외부화 |
| `src/backend/tests/test_sprint07_3_dod.py` | DoD 자동 테스트 |

**v1.0 참조**:
- `archive/v1.0/backend/app/workflow.py`
- `archive/v1.0/backend/app/workflow_graph.py`
- `archive/v1.0/backend/app/workflow_graph_engine.py`
- `archive/v1.0/backend/app/policy.py`
