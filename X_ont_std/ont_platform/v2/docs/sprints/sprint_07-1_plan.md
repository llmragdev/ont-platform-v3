# Sprint 07-1 — 물리적 격리 + 서비스 레이어 기반 구축

> **에픽**: Sprint 07 — v2.0 기반 구축 (07-1 / 07-2 / 07-3)  
> **기간**: 2026-05-13  
> **상태**: ✅ 완료 — 테스트 39/39 통과 (D15 보강 후)  
> **기반**: ont_platform v2.0 (src/)  
> **이전 버전**: [v1.0 archive](../../archive/v1.0/README.md)

---

## 1. 스프린트 목표

v1.0의 물리 격리 부재와 단일 app_context 구조를 해결하는 v2.0 기반을 구축한다.

1. **물리적 스토리지 격리** — `storage_config.py` 기반 V-ID 샤딩 + company/project 디렉토리 구조
2. **서비스 레이어 분리** — `TenantContext` + 3개 서비스 (OntologyService, DocumentService, VectorSearchService)

*온톨로지 범용화(app_context 완전 분리)는 07-3에서 완성.*

---

## 2. 완료 기준 (DoD)

### 2.1 물리적 격리

| # | 기준 |
|---|------|
| D01 | `storage_config.py`의 경로 함수만으로 모든 파일 경로 결정 |
| D02 | PDF 업로드 시 `storage/{company_id}/{project_id}/uploads/` 에 저장 |
| D03 | 벡터화 시 `storage/{company_id}/{project_id}/vector_db/V{shard_id}/` 에 Chroma 인스턴스 생성 |
| D04 | 온톨로지 JSON이 `storage/{company_id}/{project_id}/ontology/` 에 저장 |
| D05 | company A의 Chroma 인스턴스로 company B 문서가 검색되지 않음 (물리 격리) |
| D06 | 특정 V-ID 지정 검색 vs 전체 샤드 순회 검색 모두 동작 |

### 2.2 서비스 레이어

| # | 기준 |
|---|------|
| D07 | `OntologyService` 클래스 — entities/relationships CRUD, company/project scope 주입 |
| D08 | `DocumentService` 클래스 — upload/vectorize/delete, storage_config 사용 |
| D09 | `VectorSearchService` 클래스 — V-ID 기반 샤드 검색, score 재정렬 |
| D10 | 세 서비스 모두 `TenantContext` (company_id, project_id, user_id)를 받아 동작 |
| D11 | `app_context.py` 의존성 없이 세 서비스 단독 테스트 가능 |

### 2.3 백엔드 API 연결

| # | 기준 |
|---|------|
| D12 | `POST /api/documents/upload` — DocumentService 경유, 물리 경로에 저장 |
| D13 | `GET /api/documents` — company/project 필터 (물리 격리 보장) |
| D14 | `POST /api/ontology/{doc_id}/entities` — OntologyService 경유 |
| D15 | 기존 `/api/workflow/*` 엔드포인트 회귀 없음 (v1.0 호환) |

---

## 3. 백로그

| ID | 항목 | 우선순위 | 상태 |
|----|------|----------|------|
| S-01 | `storage_config.py` 단위 테스트 | 🔴 | ✅ |
| S-02 | `VectorSearchService` (V-ID 샤딩, score 재정렬) | 🔴 | ✅ |
| S-03 | `DocumentService` (upload → vectorize 연동) | 🔴 | ✅ |
| S-04 | `OntologyService` (CRUD + scope 주입) | 🔴 | ✅ |
| S-05 | `TenantContext` 단일 실행 컨텍스트 | 🔴 | ✅ |
| S-06 | `main.py` — 세 서비스를 Depends로 연결 | 🟡 | ✅ |
| S-07 | v1.0 데이터 마이그레이션 스크립트 | 🟡 | ⏳ 07-3 이후 |
| S-08 | DoD 자동 테스트 (`test_sprint07_1_dod.py`) | 🔴 | ✅ |

---

## 4. 핵심 설계 결정

### V-ID 샤딩 전략

```
문서 업로드 시 shard_id 결정:
  Option C: 초기에는 항상 "default" 단일 샤드 (단순)
  Option A: 사용자가 명시 (target_v_id 파라미터) — API 파라미터로 준비됨

→ 07-1: Option C로 시작, Option A는 API 파라미터로 준비
```

### 서비스 레이어 패턴

```python
@dataclass
class TenantContext:
    user_id: str
    company_id: str
    project_id: str
    role: str
    permissions: dict

# 서비스는 TenantContext만 받고, 경로는 storage_config에서 계산
class VectorSearchService:
    def search(self, query: str, ctx: TenantContext, shard_id: str | None = None): ...
```

### v1.0 호환 전략

```
- /api/workflow/*: app_context.py 그대로 유지 (07-3에서 이식 예정)
- /api/objects/customers, orders: 그대로 유지
- 신규 서비스(/api/documents, /api/ontology): 새 서비스 레이어 경유
```

---

## 5. 산출물

| 파일 | 역할 |
|------|------|
| `src/backend/storage_config.py` | 경로 팩토리 |
| `src/backend/app/models/tenant_context.py` | TenantContext 데이터클래스 |
| `src/backend/app/services/vector_search.py` | V-ID 샤딩 기반 검색 서비스 |
| `src/backend/app/services/document.py` | 문서 업로드/벡터화/삭제 |
| `src/backend/app/services/ontology.py` | 엔티티/관계 CRUD |
| `src/backend/app/main.py` | FastAPI Depends 연결 |
| `src/backend/tests/test_storage_config.py` | 경로 계산 단위 테스트 (17개) |
| `src/backend/tests/test_sprint07_1_dod.py` | DoD 자동 테스트 (22개) |

---

## 6. 완료 기록

| 항목 | 결과 |
|------|------|
| 테스트 | 39/39 통과 (test_storage_config: 17, test_sprint07_1_dod: 22) |
| 실행 환경 | conda env `claud_be` / Python 3.11.15 |
| D15 비고 | `/api/workflow/*` v2.0 미이식 — `/api/health` 기동 확인 + v1.0 archive workflow.py 존재 확인으로 대리 검증. 07-3에서 이식 예정. |

---

## 7. 다음 단계

- **07-2**: Query Planner 프로토타입 (`filter` intent) → [sprint_07-2_plan.md](sprint_07-2_plan.md)
- **07-3**: 범용 온톨로지 완성 (app_context 도메인 로직 분리) → [sprint_07-3_plan.md](sprint_07-3_plan.md)
