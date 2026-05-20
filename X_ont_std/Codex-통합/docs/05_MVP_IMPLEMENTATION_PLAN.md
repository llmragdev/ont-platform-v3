# 05. MVP 구현 계획

작성일: 2026-05-13  
목표: `FINAL_REQUIREMENTS.md`, `FINAL_DESIGN.md`, `03_FINAL_API_SPEC.md`, `04_FINAL_DATA_SCHEMA.md`를 실제 개발 스프린트로 분해

---

## 1. 범위 원칙

MVP는 "작동하는 닫힌 경로"를 우선한다. 사용자는 로그인하고, 허용된 프로젝트 범위에서 문서를 올리고, 온톨로지를 관리하고, 하이브리드 질의 결과와 근거를 확인할 수 있어야 한다.

포함:

- JWT/dev user 기반 인증
- TenantContext와 프로젝트 격리
- JSON Repository
- Generic Ontology CRUD
- 문서 registry, chunk, vector mapping
- BM25 검색 + vector 검색 adapter 구조
- Query Planner + Ontology Executor
- Hybrid Answer API
- 권한/격리/audit 자동 테스트
- 기본 운영 로그와 query run 기록

제외:

- PostgreSQL 운영 전환
- 완전한 비동기 작업 큐
- SSO/OAuth
- 물리적 테넌트 DB 분리
- 대규모 관리자 콘솔
- 고급 reranker 모델 운영

---

## 2. Sprint 01 - Auth, TenantContext, Repository

목표:

- 기존 단일 사용자 흐름을 tenant-aware user 모델로 정리한다.
- 모든 API dependency에서 동일한 `TenantContext`를 사용하게 한다.
- JSON 저장소 접근을 Repository 계층으로 모은다.

구현 파일:

- `backend/app/auth.py`
- `backend/app/tenant.py`
- `backend/app/repositories.py`
- `backend/app/storage_config.py`
- `backend/data/companies.json`
- `backend/data/users.json`
- `backend/data/projects.json`
- `backend/data/role_defaults.json`

주요 API:

- `POST /api/v1/auth/login`
- `GET /api/v1/tenant/me`
- `GET /api/v1/tenant/projects`

핵심 작업:

- password hash 검증과 JWT 발급 구현
- `ALLOW_DEV_USER=true`일 때만 dev user query 허용
- role default와 permission override 병합
- Repository read/write 시 JSON 원자적 저장 적용
- 쓰기 작업 공통 audit helper 준비

테스트:

- JWT login 성공/실패
- disabled user login 실패
- `?user_id=` dev mode on/off
- 다른 project 접근 403
- permission override merge
- JSON 파일이 없거나 비어 있을 때 기본값 처리

완료 기준:

- 모든 보호 API가 `TenantContext`를 받을 수 있다.
- 클라이언트가 보낸 `company_id`, `project_id`를 서버 권한 결정에 사용하지 않는다.

---

## 3. Sprint 02 - Generic Ontology CRUD

목표:

- Customer/Order/Product 하드코딩에서 벗어나 generic object/relationship 구조로 전환한다.
- schema-driven validation을 구현한다.

구현 파일:

- `backend/app/ontology.py`
- `backend/app/validators.py`
- `backend/app/models.py`
- `backend/data/ontology_schema.json`
- `backend/data/ontology_objects.json`
- `backend/data/ontology_relationships.json`
- `frontend/src/components/OntologySchemaManager.tsx`
- `frontend/src/components/OntologyInstanceManager.tsx`

주요 API:

- `GET /api/v1/ontology/schema`
- `PUT /api/v1/ontology/schema`
- `POST /api/v1/ontology/schema/object-types`
- `GET /api/v1/ontology/objects`
- `POST /api/v1/ontology/objects`
- `GET /api/v1/ontology/objects/{id}/context`
- `GET /api/v1/ontology/relationships`
- `POST /api/v1/ontology/relationships`
- `DELETE /api/v1/ontology/relationships/{id}`

핵심 작업:

- property type 검증 구현
- required, enum, object_ref 검증 구현
- relationship source/target type 검증
- object context 응답에 incoming/outgoing/documents/actions 포함
- relationship 삭제는 `status=disabled` tombstone 처리
- schema version 증가와 audit 기록

테스트:

- 새 타입 추가 후 객체 생성
- required property 누락 422
- enum 범위 밖 값 422
- 관계 source/target 타입 불일치 422
- viewer 쓰기 403
- 다른 company object 직접 조회 403 또는 404

완료 기준:

- 새 객체 타입을 추가하면 API와 UI에서 생성/조회할 수 있다.
- 관계 삭제 후 기본 조회에는 노출되지 않는다.

---

## 4. Sprint 03 - Documents, Chunk, Search

목표:

- 문서 업로드, registry, chunk, 검색 근거 구조를 만든다.
- Vector DB가 없어도 adapter를 통해 BM25 기반 MVP가 동작하도록 한다.

구현 파일:

- `backend/app/document_service.py`
- `backend/app/search_service.py`
- `backend/app/chunking.py`
- `backend/data/documents_registry.json`
- `backend/data/document_chunks.json`
- `backend/data/vector_mapping.json`
- `frontend/src/components/DocumentManager.tsx`

주요 API:

- `GET /api/v1/documents`
- `POST /api/v1/documents/upload`
- `DELETE /api/v1/documents/{doc_id}`

핵심 작업:

- 업로드 파일을 `uploads/{company_id}/{project_id}`에 저장
- registry에 상태, 파일 크기, page/chunk count 기록
- 텍스트 추출 실패 시 `index_failed`와 `error_message` 기록
- chunk size 500~800 tokens, overlap 10~15% 기준 적용
- BM25 검색 결과를 `document_evidence` 형식으로 반환
- vector adapter interface를 두어 FAISS/Chroma 교체 가능하게 설계

테스트:

- viewer upload 403
- editor upload 201
- 업로드 후 registry와 chunk 생성
- `doc_ids` 필터 검색
- 다른 company 문서 미노출
- 삭제 문서는 검색 제외

완료 기준:

- 문서 목록과 검색이 TenantContext로 필터링된다.
- 검색 결과에서 `doc_id`, filename, page, chunk_id, score를 복원할 수 있다.

---

## 5. Sprint 04 - Query Planner + Ontology Executor

목표:

- 자연어 질문을 실행 가능한 Query Plan으로 변환한다.
- 온톨로지 계산은 LLM이 아니라 코드로 실행한다.

구현 파일:

- `backend/app/query_planner.py`
- `backend/app/query_plan_schema.py`
- `backend/app/ontology_query_engine.py`
- `backend/data/query_runs.jsonl`

주요 API:

- `POST /api/v1/hybrid/plan`

Query Plan 최소 구조:

```json
{
  "intent": "filter",
  "target_type": "Customer",
  "filters": [
    {
      "field": "risk_tier",
      "op": "eq",
      "value": "High"
    }
  ],
  "relationships": [],
  "aggregation": null,
  "needs_vector": false,
  "fallback_used": false
}
```

지원 intent:

- `filter`: 조건 검색
- `compare`: 객체 비교
- `calculate`: 합계/평균/개수 계산
- `relation`: 연결 객체 탐색
- `hybrid`: 온톨로지와 문서 근거를 함께 사용
- `unknown`: 안전한 fallback

핵심 작업:

- LLM planner 응답을 JSON schema로 검증
- 실패 시 rule-based fallback planner 사용
- schema에 없는 타입/필드 참조는 warning 또는 422로 처리
- executor는 현재 project의 active object/relationship만 사용
- 실행 trace에 planner, filter, executor 단계를 기록

테스트:

- filter plan 검증
- compare plan 검증
- calculate plan 검증
- relation traversal 검증
- 잘못된 property 제거 또는 422
- LLM JSON 실패 시 fallback planner

완료 기준:

- 주요 5개 질문 유형이 실행 가능한 plan으로 변환된다.
- LLM이 실패해도 임의 답변이 아니라 fallback/warning을 반환한다.

---

## 6. Sprint 05 - Hybrid Answer + UI

목표:

- 온톨로지 실행 결과와 문서 근거를 결합해 사용자에게 답변한다.
- 답변은 항상 plan, structured data, evidence, trace를 함께 반환한다.

구현 파일:

- `backend/app/hybrid_answer.py`
- `frontend/src/components/HybridQuery.tsx`
- `frontend/src/components/QueryPlanViewer.tsx`
- `frontend/src/components/EvidencePanel.tsx`
- `frontend/src/components/TracePanel.tsx`

주요 API:

- `POST /api/v1/hybrid/ask`

응답 필수 필드:

- `question`
- `query_plan`
- `answer`
- `structured_data`
- `ontology_evidence`
- `document_evidence`
- `trace`
- `warnings`

핵심 작업:

- 온톨로지 executor 결과를 테이블로 반환
- BM25/vector 검색 결과를 document evidence로 반환
- LLM은 최종 설명 생성에만 사용
- 근거 부족 시 `warnings`에 명시하고 단정 답변 금지
- `query_runs.jsonl`에 latency, fallback 여부, evidence count 기록

테스트:

- filter + evidence
- compare + evidence
- calculate no hallucination
- hybrid answer includes plan, structured_data, evidence, trace
- 근거 없는 질문 warning
- 권한 없는 doc_ids 제외 또는 403

완료 기준:

- LLM 없이도 구조형 결과가 반환된다.
- LLM 답변에는 근거 문서 또는 온톨로지 evidence가 연결된다.

---

## 7. Sprint 06 - Acceptance Tests + Reporting

목표:

- 권한, 테넌트 격리, 하이브리드 질의, UI 흐름을 자동 테스트로 고정한다.

구현 파일:

- `backend/integration_tests/scenarios.py`
- `backend/integration_tests/runner.py`
- `backend/integration_tests/reporter.py`
- `frontend/e2e/tenant.spec.ts`
- `frontend/e2e/hybrid-query.spec.ts`

테스트:

- [06_ACCEPTANCE_TEST_PLAN.md](06_ACCEPTANCE_TEST_PLAN.md)의 필수 케이스 구현
- backend unit test
- API integration test
- integration runner
- Playwright E2E

리포트 산출물:

- `reports/integration-{run_id}.json`
- `reports/integration-{run_id}.html`
- 실패 요청/응답 payload
- trace와 warning

완료 기준:

- backend unit + API integration + integration scenarios + frontend E2E 통과
- HTML/JSON 리포트 생성
- 실패 시 어떤 권한/격리/근거 조건이 깨졌는지 즉시 확인 가능

---

## 8. 최종 릴리스 체크리스트

- [ ] `pytest` 전체 통과
- [ ] integration runner 통과
- [ ] Playwright E2E 통과
- [ ] API 문서와 실제 route 일치
- [ ] 데이터 스키마 샘플로 서버 부팅 가능
- [ ] viewer/editor/admin/auditor 권한 차이 확인
- [ ] 다른 company/project 데이터 접근 차단
- [ ] Hybrid Query가 plan/structured/evidence/trace를 반환
- [ ] 문서 검색 결과가 registry/chunk/vector mapping으로 복원 가능
- [ ] audit log에 권한 거부와 주요 쓰기 이벤트 기록
- [ ] query run log에 latency와 fallback 사용률 기록
