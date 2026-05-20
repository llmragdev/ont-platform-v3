# 01_Antigravity_통합 평가

작성자: Antigravity  
정리/검증 보정: Codex  
작성일: 2026-05-16  
분석 범위: `E:\ontology_edu\X_ont_std` 산하 3개 플랫폼 소스  
분석 방식: 테스트 미수행, 소스/문서 정적 분석

---

## 1. 평가 대상

이 문서는 `X_ont_std` 내부에 모아둔 3개 온톨로지 통합 프로그램 소스를 같은 기준으로 비교한다.

| 플랫폼 | 경로 | 핵심 성격 |
|---|---|---|
| Antigravity | `E:\ontology_edu\X_ont_std\antigravity_platform` | 모듈형 FastAPI 백엔드, 테넌트 격리, 하이브리드 질의 API 지향 |
| ont_platform | `E:\ontology_edu\X_ont_std\ont_platform` | v3 하이브리드 질의/LLM 분류/워크플로우 실행 이력 중심 |
| Codex-통합 | `E:\ontology_edu\X_ont_std\Codex-통합` | v1/v2/v3 통합 저장소, Palantir 실무 원칙(Materialize/Write-back/Governance) 중심 |

---

## 2. Antigravity Source 분석

### 2.1 확인된 구조

Antigravity의 실제 구현 중심 경로는 다음이다.

```text
E:\ontology_edu\X_ont_std\antigravity_platform\project\src\backend
```

주요 구조:

```text
app/
├── api/
│   ├── deps.py
│   ├── middleware.py
│   └── v1/
│       ├── documents.py
│       ├── hybrid.py
│       └── ontology.py
├── core/
│   ├── prompts.py
│   └── security.py
├── models/
│   ├── identity.py
│   └── query_plan.py
├── repositories/
│   ├── audit.py
│   ├── base.py
│   ├── documents.py
│   └── ontology.py
└── services/
    ├── audit.py
    ├── documents.py
    ├── hybrid_synthesizer.py
    ├── ontology.py
    ├── ontology_engine.py
    ├── ontology_schema.py
    ├── query_planner.py
    └── search.py
```

### 2.2 강점

- FastAPI 라우터가 `ontology`, `documents`, `hybrid`로 분리되어 있어 API 표면이 명확하다.
- `QueryPlanner`, `OntologyQueryEngine`, `HybridSynthesizer`, `SearchService`가 분리되어 하이브리드 질의 구조를 이해하기 쉽다.
- `StorageConfig`가 `company_id/project_id` 기반 storage 경로를 만든다. 테넌트/프로젝트 분리 방향은 분명하다.
- `IdentityMiddleware`, `UserIdentity`, `PermissionSet`, `PermissionChecker`가 있어 인증/권한 모델을 붙이려는 구조가 있다.
- `OntologyRepository`, `DocumentRepository`, `AuditRepository`처럼 저장소 계층이 분리되어 있다.
- `docs/01_REQUIREMENTS.md`부터 `09_UX_AND_OPERATIONS.md`까지 문서가 순차 구성되어 있어 개발 의사결정 추적에 유리하다.

### 2.3 한계 및 보정 사항

- 기존 평가에는 “운영급 모듈화 완료”, “Write-back Service 내장”, “완전한 Multi-tenant 격리”처럼 강하게 표현되어 있었으나, 소스 정적 확인 기준으로는 과장이다.
- 현재 확인된 Antigravity 백엔드에는 Codex v3처럼 명시적인 `materialize_service.py`, `writeback_service.py`, `provenance_service.py`, `governance_service.py`가 보이지 않는다.
- `LAUNCH_GUIDE.md`는 “Multi-Tenant Ready 준비 중”이라고 표현한다. 따라서 테넌트 격리는 구조 방향은 있으나 완료로 단정하면 안 된다.
- `project/src/frontend/src` 경로는 현재 존재하지 않았다. 프론트 UX는 문서/가이드상 지향점으로 보는 것이 맞고, 실제 컴포넌트 구현 기준 평가는 추가 확인이 필요하다.
- 실행 가이드의 경로는 현재 표준 위치인 `E:\ontology_edu\X_ont_std\antigravity_platform` 기준으로 정리되었다.

### 2.4 Antigravity 판단

Antigravity는 **하이브리드 질의 API와 모듈형 백엔드 구조 참고 소스**로 적합하다. 다만 Palantir 실무 원칙의 Materialize/Write-back/Governance 기준 소스로 삼기에는 아직 직접 구현이 약하다.

---

## 3. ont_platform Source 분석

경로:

```text
E:\ontology_edu\X_ont_std\ont_platform
```

### 강점

- `v3/README.md` 기준으로 LLM 기반 질의 분류, Gemini API 합성, fallback, provenance, repository 패턴, HMAC 인증, workflow run 이력, metric API를 명시한다.
- 백엔드 구조가 `api`, `middleware`, `models`, `prompts`, `repositories`, `services`로 나뉘어 있다.
- `POST /api/hybrid/ask`, `POST /api/rag/ask`, `GET /api/workflow-graphs`, `GET /api/metrics/query`처럼 하이브리드 질의와 운영 관측성 API가 뚜렷하다.
- 프론트엔드 구성도 `HybridQuery`, `RAGQuery`, `WorkflowGraph`, `LlmAnswerPanel`, `OntologyEvidenceList`, `ProvenanceBadge`, `WorkflowRunHistory` 등 역할별 컴포넌트가 풍부하다.

### 한계

- README의 실행 경로는 `E:\ontology_edu\X_ont_std\ont_platform` 기준으로 정리되었다.
- Materialize와 Write-back은 Codex v3만큼 직접적인 서비스 계층으로 보이지 않는다.
- Palantir 13번 문서 기준으로는 하이브리드 질의/운영 추적은 강하지만, Action-driven write-back 쪽은 추가 결합이 필요하다.

### 판단

ont_platform은 **LLM 기반 Hybrid Query, Workflow Run, Metric, Provenance UI/응답 설계의 핵심 참조 소스**다.

---

## 4. Codex-통합 Source 분석

경로:

```text
E:\ontology_edu\X_ont_std\Codex-통합
```

### 강점

- `v1`, `v2`, `v3` 발전 구조가 명확하다.
- `v3`에 Palantir Practical Edition 방향이 명시되어 있다.
- `v3/src/backend/app` 아래에 다음 실무 원칙 모듈이 확인된다.
  - `action_service.py`
  - `materialize_service.py`
  - `writeback_service.py`
  - `provenance_service.py`
  - `governance_service.py`
  - `tenant.py`
  - `storage_config.py`
- repository가 외부 write-back을 직접 수행하지 않고, Action과 Write-back 서비스가 분리되어 있다.
- `[도메인]_[주제]_v[버전]` 네이밍 검증 등 governance 기준이 코드에 들어가기 시작했다.

### 한계

- 하이브리드 질의/LLM 분류/프론트 컴포넌트 완성도는 ont_platform보다 약하다.
- 제조/조선 도메인 스키마(`Ship`, `Block`, `Material`, `Worker`, `Sensor`)는 아직 본격 반영 전이다.
- Materialize와 Write-back은 구조와 시뮬레이션 단계이며, 운영 어댑터/재시도/승인/실패 보상은 추가 설계가 필요하다.
- README 실행 경로는 `E:\ontology_edu\X_ont_std\Codex-통합` 기준으로 정리되었다.

### 판단

Codex-통합 v3는 **Palantir 실무 원칙의 기준 골격**으로 적합하다.

---

## 5. 비교 매트릭스

| 항목 | Antigravity | ont_platform | Codex-통합 |
|---|---:|---:|---:|
| `X_ont_std` 내부 소스 여부 | 확인 | 확인 | 확인 |
| FastAPI 백엔드 구조 | 높음 | 높음 | 높음 |
| Next.js 프론트 확인 가능성 | 추가 확인 필요 | 높음 | 중간 |
| 하이브리드 질의 구조 | 중간~높음 | 높음 | 중간 |
| LLM 질의 분류/합성 | 중간 | 높음 | 중간 |
| 테넌트/프로젝트 격리 | 중간 | 중간~높음 | 높음 |
| Repository 계층 | 중간~높음 | 높음 | 중간~높음 |
| Provenance | 낮음~중간 | 높음 | 높음 |
| Workflow Run 이력 | 낮음~중간 | 높음 | 중간 |
| Materialize | 낮음 | 낮음~중간 | 높음 |
| Write-back | 낮음 | 낮음~중간 | 높음 |
| Governance Naming | 낮음~중간 | 중간 | 높음 |
| Palantir 13번 원칙 직접성 | 중간 | 중간~높음 | 높음 |
| 가장 적합한 활용 | 백엔드 모듈/질의 API 참고 | Hybrid/LLM/Metric 참고 | 최종 Palantir 골격 |

---

## 6. 통합 권고

최종 통합 방향은 다음이 적절하다.

```text
기준 골격:
  E:\ontology_edu\X_ont_std\Codex-통합\v3

하이브리드 질의/LLM/메트릭 참조:
  E:\ontology_edu\X_ont_std\ont_platform\v3

모듈형 API/문서 업로드/질의 API 참고:
  E:\ontology_edu\X_ont_std\antigravity_platform
```

Antigravity를 주축으로 삼기보다는, **Antigravity의 모듈형 API 구조를 참고하고 Codex-통합 v3의 Palantir 실무 골격에 ont_platform의 하이브리드 질의 계층을 결합**하는 방식이 더 안전하다.

---

## 7. 조치 필요 사항

1. Antigravity `LAUNCH_GUIDE.md`의 실행 경로는 `E:\ontology_edu\X_ont_std\antigravity_platform` 기준으로 유지한다.
2. ont_platform `v3/README.md`의 실행 경로는 `E:\ontology_edu\X_ont_std\ont_platform` 기준으로 유지한다.
3. Codex-통합 `README.md`와 `v3/README.md`의 실행 경로는 `E:\ontology_edu\X_ont_std\Codex-통합` 기준으로 유지한다.
4. 세 평가 문서의 파일명 규칙은 현재 표준을 유지한다.
5. 추후 테스트가 허용되면 각 플랫폼의 API 기동/스모크 테스트를 별도 문서로 남긴다.

---

## 8. 결론

`X_ont_std` 기준으로 다시 보면 Antigravity는 운영 완료 플랫폼이라기보다 **모듈형 백엔드와 하이브리드 질의 API 참고 소스**에 가깝다. 최종 통합은 Codex-통합 v3를 기준 골격으로 삼고, ont_platform의 LLM/Hybrid/Metric 계층과 Antigravity의 API 구조를 선별 흡수하는 편이 가장 타당하다.
