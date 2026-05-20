# 01_Codex_통합 평가

작성일: 2026-05-16  
수행 에이전트: Codex  
분석 방식: 테스트 미수행, `E:\ontology_edu\X_ont_std` 내부 소스 정적 분석

---

## 1. 확인 결과

요청 기준은 **`X_ont_std` 폴더 안에 모아둔 소스들을 비교하고, 그 기록을 `X_ont_std\cross-source-comparison`에 남기는 것**이다.

현재 `E:\ontology_edu\X_ont_std`에는 다음 소스가 있다.

| 소스 | 경로 | 확인된 성격 |
|---|---|---|
| Antigravity | `E:\ontology_edu\X_ont_std\antigravity_platform` | FastAPI + Next.js 기반, 하이브리드 질의 콘솔과 UX 중심 플랫폼 |
| Claude 계열 | `E:\ontology_edu\X_ont_std\ont_platform` | v2/v3 구조, LLM 기반 질의 분류, provenance, workflow run, metric API 포함 |
| Codex 계열 | `E:\ontology_edu\X_ont_std\Codex-통합` | v1/v2/v3 통합 저장소, v3에 Palantir 실무 원칙 반영 중 |

따라서 이전처럼 루트의 `src_codex`, `claud_v1_legacy`, `Codex-통합`을 비교 기준으로 삼으면 안 된다. 이 문서는 위 3개 **`X_ont_std` 내부 소스**를 기준으로 다시 정리한다.

---

## 2. 기록 폴더 상태

기록 위치:

```text
E:\ontology_edu\X_ont_std\cross-source-comparison
```

현재 확인된 평가 문서:

| 파일 | 상태 |
|---|---|
| `01_Antigravity_통합 평가.md` | 존재 |
| `01_Claude_플랫폼통합평가.md` | 존재 |
| `01_Codex_통합 평가.md` | 존재, 경로 기준 수정 완료 |

참고: Claude 평가 문서의 표준 파일명은 `01_Claude_플랫폼통합평가.md`이다.

---

## 3. Antigravity Source 평가

경로:

```text
E:\ontology_edu\X_ont_std\antigravity_platform
```

### 확인한 구조

- `backend/app/api`
- `backend/app/core`
- `backend/app/models`
- `backend/app/repositories`
- `backend/app/services`
- `project/src/backend`
- `project/src/frontend`
- `storage/default/proj-default`
- `docs/01_REQUIREMENTS.md`부터 `09_UX_AND_OPERATIONS.md`

### 강점

- 제품형 UI/UX 구성이 가장 강하다.
- `LAUNCH_GUIDE.md` 기준으로 하이브리드 질의 콘솔, 온톨로지 설정, Q&A 문서 업로드 흐름을 명확히 지향한다.
- `backend/app` 아래에 API, core, models, repositories, services 경계가 있어 백엔드 계층 분리가 비교적 분명하다.
- `project/src/backend`, `project/src/frontend`, `storage` 구조가 운영형 프로젝트 배치에 가깝다.
- UX/운영 문서가 `docs`에 순차적으로 정리되어 있어 요구사항 추적에 유리하다.

### 한계

- 실행 가이드의 경로는 현재 표준 위치인 `E:\ontology_edu\X_ont_std\antigravity_platform` 기준으로 정리되었다.
- `LAUNCH_GUIDE.md`에 “Multi-Tenant Ready 준비 중”이라고 되어 있어, 테넌트 격리 구현은 v3 Codex나 ont_platform보다 확정도가 낮아 보인다.
- 13번 팔란티어 원칙의 Materialize, Write-back, Action-driven Modeling이 명시적으로 전면화되어 있지는 않다.

### 통합 활용 판단

Antigravity 소스는 **프론트 UX, 하이브리드 질의 콘솔, 사용성 중심 화면 설계**를 통합 기준에 반영할 때 가치가 높다. 다만 최종 표준 백엔드 기준으로 삼기보다는 UI/UX와 문서 구조 참고 소스로 쓰는 편이 안정적이다.

---

## 4. ont_platform Source 평가

경로:

```text
E:\ontology_edu\X_ont_std\ont_platform
```

### 확인한 구조

- `v2`
- `v3`
- `docs`
- `v3/src/backend/app/api`
- `v3/src/backend/app/middleware`
- `v3/src/backend/app/models`
- `v3/src/backend/app/prompts`
- `v3/src/backend/app/repositories`
- `v3/src/backend/app/services`
- `v3/src/frontend`

### 강점

- `v3/README.md` 기준으로 개발 완료 상태와 v2 대비 개선점이 명확하다.
- LLM 기반 질의 분류와 fallback을 명시한다.
- `OntologyProvenance` 모델, Repository 패턴, HMAC-SHA256 인증, WorkflowRun 이력, `/api/metrics/query`를 포함한다.
- `api`, `middleware`, `models`, `prompts`, `repositories`, `services`로 백엔드 모듈 경계가 가장 정돈되어 있다.
- `POST /api/hybrid/ask`, `POST /api/rag/ask`, `GET /api/ontology`, `GET /api/workflow-graphs`, `GET /api/metrics/query` 등 하이브리드 질의와 운영 메트릭에 필요한 API가 명확하다.
- 프론트엔드도 `AIQuery`, `HybridQuery`, `RAGQuery`, `WorkflowGraph`, `LlmAnswerPanel`, `OntologyEvidenceList`, `VectorSourceList`, `ProvenanceBadge`, `WorkflowRunHistory` 등 역할별 컴포넌트가 잘 나뉘어 있다.

### 한계

- README의 실행 경로는 현재 표준 위치인 `E:\ontology_edu\X_ont_std\ont_platform` 기준으로 정리되었다.
- Palantir 실무 설계 관점에서 Materialize와 Write-back은 Codex v3보다 덜 직접적으로 드러난다.
- Action-driven Modeling보다는 하이브리드 질의/RAG/워크플로우/메트릭 쪽 완성도가 더 강한 소스다.

### 통합 활용 판단

ont_platform은 **하이브리드 질의, LLM 분류, provenance, repository 패턴, workflow run 이력, metric API**의 표준 후보로 가장 강하다. 최종 통합에서 질의 엔진과 운영 관측성 계층은 ont_platform v3를 많이 참고하는 것이 좋다.

---

## 5. Codex-통합 Source 평가

경로:

```text
E:\ontology_edu\X_ont_std\Codex-통합
```

### 확인한 구조

- `v1`
- `v2`
- `v3`
- `docs`
- `backup_old`
- `v3/src/backend/app/action_service.py`
- `v3/src/backend/app/materialize_service.py`
- `v3/src/backend/app/writeback_service.py`
- `v3/src/backend/app/provenance_service.py`
- `v3/src/backend/app/governance_service.py`
- `v3/src/backend/app/repositories.py`
- `v3/src/backend/app/tenant.py`
- `v3/src/backend/app/storage_config.py`

### 강점

- v1/v2/v3를 한 저장소에서 관리하므로 발전 이력이 가장 분명하다.
- v3가 13번 팔란티어 실무 설계원칙을 직접 목표로 삼고 있다.
- `materialize_service.py`가 논리 온톨로지 객체를 물리 JSON dataset으로 materialize한다.
- `writeback_service.py`가 Action 결과를 write-back 요청으로 기록하고 외부 ERP 어댑터를 파일로 시뮬레이션한다.
- `provenance_service.py`가 출처, 신뢰도, 생성자, 생성 시각을 표준화한다.
- `governance_service.py`가 `[도메인]_[주제]_v[버전]` 네이밍 규칙을 검증한다.
- `tenant.py`, `storage_config.py`가 company/project 기반 저장소 격리를 제공한다.
- repository가 직접 write-back을 하지 않고, action/writeback/materialize 서비스가 분리되어 있어 Palantir식 경계가 가장 선명하다.

### 한계

- README의 실행 경로는 현재 표준 위치인 `E:\ontology_edu\X_ont_std\Codex-통합` 기준으로 정리되었다.
- 하이브리드 질의, LLM 분류, 프론트 컴포넌트 완성도는 ont_platform보다 약하다.
- 제조/조선 도메인의 `Ship`, `Block`, `Material`, `Worker`, `Sensor` 스키마가 아직 본격 반영되지 않았다.
- Materialize/Write-back은 현재 구조 원칙과 시뮬레이션 단계이며, 운영 어댑터/재시도/승인/실패 보상은 추가 설계가 필요하다.

### 통합 활용 판단

Codex-통합 v3는 **Palantir 실무 원칙 계층의 기준 소스**로 쓰는 것이 맞다. Materialize, Write-back, Action, Provenance, Governance는 Codex-통합 v3의 방향을 표준으로 삼고, 하이브리드 질의와 UI는 ont_platform/Antigravity의 강점을 흡수하는 방식이 적절하다.

---

## 6. 비교 매트릭스

| 평가 항목 | Antigravity | ont_platform | Codex-통합 |
|---|---:|---:|---:|
| 표준 위치가 `X_ont_std` 안에 있음 | 확인 | 확인 | 확인 |
| FastAPI + Next.js 구조 | 높음 | 높음 | 높음 |
| UI/UX 완성도 | 높음 | 중간~높음 | 중간 |
| 하이브리드 질의 구조 | 중간~높음 | 높음 | 중간 |
| LLM 기반 질의 분류 | 불명확/부분 | 높음 | 중간 |
| RAG/Vector 근거 결합 | 중간 | 높음 | 중간 |
| Repository 패턴 | 중간 | 높음 | 중간~높음 |
| 멀티테넌트/프로젝트 격리 | 준비 중 | 중간~높음 | 높음 |
| Provenance | 중간 | 높음 | 높음 |
| Workflow Run 이력 | 중간 | 높음 | 중간 |
| Materialize | 낮음 | 낮음~중간 | 높음 |
| Write-back | 낮음 | 낮음~중간 | 높음 |
| Governance Naming | 중간 | 중간 | 높음 |
| Palantir 13번 원칙 직접성 | 중간 | 중간~높음 | 높음 |
| 최종 통합 기준 적합도 | UI 기준 우수 | 질의/운영 기준 우수 | Palantir 구조 기준 우수 |

---

## 7. 최종 판단

`X_ont_std` 안의 3개 소스를 기준으로 보면, 역할 분담은 다음이 가장 적절하다.

```text
최종 통합 기준 골격:
  E:\ontology_edu\X_ont_std\Codex-통합\v3

하이브리드 질의/LLM/메트릭 참조:
  E:\ontology_edu\X_ont_std\ont_platform\v3

프론트 UX/콘솔 경험 참조:
  E:\ontology_edu\X_ont_std\antigravity_platform
```

즉, **Codex-통합 v3를 Palantir 실무 원칙의 기준 골격으로 삼고, ont_platform v3의 하이브리드 질의 계층과 Antigravity의 화면 경험을 선별 흡수**하는 방향이 좋다.

---

## 8. 조치 필요 사항

현재 기록 폴더와 비교 문서는 표준 위치 기준으로 정리되었다. 이후 유지할 기준은 다음과 같다.

1. 각 소스의 README/실행 가이드는 `E:\ontology_edu\X_ont_std\...` 기준을 유지한다.
2. Claude 평가 문서의 표준 파일명은 `01_Claude_플랫폼통합평가.md`로 유지한다.
3. Antigravity 평가는 `X_ont_std` 내부 소스 기준으로 보정된 내용을 유지한다.
4. 앞으로 비교 문서는 모두 `E:\ontology_edu\X_ont_std\cross-source-comparison`에 작성한다.

---

## 9. 결론

처음 작성된 Codex 평가 문서는 요청 의도와 달리 루트의 이전 소스들을 비교하고 있었다. 현재 본 문서에서 기준을 바로잡아 **`X_ont_std` 내부 소스 3개를 비교 대상으로 수정 완료**했다.

정리하면, 지금 기준은 다음과 같다.

```text
비교 대상:
  E:\ontology_edu\X_ont_std\antigravity_platform
  E:\ontology_edu\X_ont_std\ont_platform
  E:\ontology_edu\X_ont_std\Codex-통합

기록 위치:
  E:\ontology_edu\X_ont_std\cross-source-comparison
```
