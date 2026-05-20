# Codex-통합 최종 요건 정의서

작성일: 2026-05-13  
대상: `E:\ontology_edu\Codex-통합`  
목표: 현재 프로토타입을 수준 높은 온톨로지/RAG 업무 AI 프로그램으로 고도화하기 위한 최종 요건 정의

---

## 1. 제품 목표

`Codex-통합`은 단순 온톨로지 데모가 아니라, 업무 문서와 구조화된 업무 객체를 함께 이해하는 **온톨로지 기반 RAG 워크벤치**가 되어야 한다.

최종 제품은 다음 사용 흐름을 제공한다.

1. 관리자가 업무 객체 타입, 관계 타입, 액션 타입을 정의한다.
2. 사용자가 문서를 업로드하면 문서 근거는 벡터 검색 대상으로 저장되고, 주요 엔티티/관계는 온톨로지 후보로 추출된다.
3. 사용자는 추출된 온톨로지 데이터를 검토하고 수정한다.
4. 사용자는 자연어로 질문한다.
5. 시스템은 질문을 실행 가능한 질의 계획으로 변환한다.
6. 필터, 비교, 계산, 관계 탐색은 코드가 결정적으로 수행한다.
7. 설명형 근거는 RAG 검색으로 보강한다.
8. 최종 답변은 구조형 결과, 문서 근거, 온톨로지 경로, 실행 trace를 함께 제공한다.
9. 멀티테넌트/멀티프로젝트 환경에서 사용자는 자신에게 허용된 데이터만 조회하고 수정한다.

---

## 2. 핵심 원칙

| 원칙 | 설명 |
| --- | --- |
| 설정 기반 | 객체/관계/액션 타입은 코드 수정 없이 설정으로 확장한다. |
| 결정적 실행 | 필터, 비교, 계산은 LLM이 아니라 코드가 수행한다. |
| 근거 우선 | 모든 답변은 문서 근거 또는 온톨로지 노드/관계 근거를 포함한다. |
| 사람 검토 가능 | LLM 추출 결과는 사용자가 보정할 수 있어야 한다. |
| 권한 내장 | 화면 숨김이 아니라 API 레벨에서 권한을 강제한다. |
| 테스트 가능 | 주요 흐름은 자동 테스트와 통합 리포트로 검증 가능해야 한다. |
| 교육 가능 | 내부 trace와 실행 계획을 노출해 학습자가 시스템 동작을 이해할 수 있어야 한다. |

### 2.1 인증/권한 통합 원칙

`claud_통합` Sprint 06에서 드러난 핵심 위험은 "기존 업무 사용자"와 "테넌트 사용자"가 분리될 때 권한 판단과 실제 API 호출 주체가 달라질 수 있다는 점이다. `Codex-통합`은 이 문제를 설계 단계에서 금지한다.

| ID | 원칙 |
| --- | --- |
| SEC-01 | 사용자 모델은 하나만 둔다. 데모 사용자, JWT 사용자, 테넌트 사용자를 별도 체계로 나누지 않는다. |
| SEC-02 | JWT payload에는 최소 `user_id`, `company_id`, `project_ids`, `default_project_id`, `role`을 포함한다. |
| SEC-03 | 모든 API는 서버에서 `TenantContext`를 생성하고, 클라이언트가 전달한 `company_id`를 신뢰하지 않는다. |
| SEC-04 | 개발 편의를 위한 `?user=`는 MVP 로컬 모드에서만 허용하며, 운영 모드에서는 비활성화한다. |
| SEC-05 | 프론트의 현재 사용자와 API 호출 사용자는 반드시 동일해야 한다. |
| SEC-06 | `PermissionGate`는 UX 보조 장치이며, 보안은 백엔드 dependency에서 강제한다. |
| SEC-07 | 문서, 벡터 검색, 온톨로지, 감사 로그는 모두 같은 `TenantContext`를 사용한다. |

---

## 3. 사용자 역할

| 역할 | 설명 | 권한 |
| --- | --- | --- |
| Admin | 전체 관리자 | 스키마 관리, 사용자/프로젝트 관리, 모든 편집 가능 |
| Editor | 업무 편집자 | 허용 프로젝트의 객체/관계/문서 편집 가능 |
| Viewer | 조회 사용자 | 허용 프로젝트의 조회와 질의만 가능 |
| Auditor | 감사/검토 사용자 | 실행 이력, 근거, 권한 로그 조회 가능 |

역할은 기본값이며, 사용자별 permission override를 지원한다.

---

## 4. 멀티테넌트/멀티프로젝트 요건

### 4.1 필수 데이터 속성

모든 주요 데이터에는 다음 속성이 있어야 한다.

| 속성 | 대상 | 설명 |
| --- | --- | --- |
| `company_id` | 문서, 객체, 관계, 사용자, 프로젝트 | 테넌트 격리 기준 |
| `project_id` | 문서, 객체, 관계 | 프로젝트 범위 필터 |
| `created_by` | 문서, 객체, 관계 | 생성자 추적 |
| `updated_at` | 문서, 객체, 관계 | 변경 시점 |

### 4.2 권한 요구사항

| ID | 요구사항 |
| --- | --- |
| MT-01 | 사용자는 자신이 속한 회사의 데이터만 볼 수 있다. |
| MT-02 | 사용자는 허용된 프로젝트만 선택할 수 있다. |
| MT-03 | Viewer는 객체/관계/문서/스키마 편집 API 호출 시 403을 받아야 한다. |
| MT-04 | Editor는 자신에게 허용된 프로젝트 안에서만 편집할 수 있다. |
| MT-05 | Admin은 같은 회사 안의 모든 프로젝트를 관리할 수 있다. |
| MT-06 | 다른 회사 데이터에 대한 직접 ID 접근은 404 또는 403으로 차단한다. |
| MT-07 | 프론트의 버튼 숨김과 백엔드 권한 검사는 모두 구현한다. |

---

## 5. 온톨로지 요건

### 5.1 스키마 관리

| ID | 요구사항 |
| --- | --- |
| ONT-01 | 객체 타입은 JSON 또는 DB 설정으로 관리한다. |
| ONT-02 | 관계 타입은 source/target 타입과 cardinality를 가진다. |
| ONT-03 | 액션 타입은 target_type, input_schema, permission, exposed_as_graph_node를 가진다. |
| ONT-04 | 새 객체 타입 추가 시 목록, 상세, 컨텍스트, 질의 엔진이 자동 대응한다. |
| ONT-05 | 속성에는 type, required, enum, searchable, sensitive, display_name을 둘 수 있다. |

### 5.2 인스턴스 관리

| ID | 요구사항 |
| --- | --- |
| ONT-10 | 객체 인스턴스는 특정 업무 타입에 하드코딩하지 않고 `ontology_objects` 구조로 저장한다. |
| ONT-11 | 관계 인스턴스는 `ontology_relationships` 구조로 저장한다. |
| ONT-12 | 관계는 system-derived, user-created, disabled 상태를 구분한다. |
| ONT-13 | 객체 삭제 시 연결 관계 처리 정책을 명시한다. |
| ONT-14 | 객체 컨텍스트 API는 incoming, outgoing, documents, actions를 반환한다. |

### 5.3 온톨로지 추출

| ID | 요구사항 |
| --- | --- |
| ONT-20 | PDF/문서 업로드 시 온톨로지 추출을 선택적으로 실행할 수 있다. |
| ONT-21 | 긴 문서는 청크별로 엔티티/관계를 추출하고 병합한다. |
| ONT-22 | 추출 결과는 source_doc_id, source_page, source_chunk_id, source_text, confidence를 포함한다. |
| ONT-23 | LLM 추출 결과는 승인 전 후보 상태로 저장한다. |
| ONT-24 | 사용자는 후보 엔티티/관계를 승인, 수정, 폐기할 수 있다. |

---

## 6. RAG 요건

| ID | 요구사항 |
| --- | --- |
| RAG-01 | 문서 업로드, 목록, 삭제를 지원한다. |
| RAG-02 | 문서는 BM25와 Vector 검색 대상이 된다. |
| RAG-03 | 벡터 검색은 company_id, project_id, doc_ids 필터를 지원한다. |
| RAG-04 | 검색 결과는 chunk_id, page, score, source_text를 포함한다. |
| RAG-05 | 답변에는 사용한 문서 근거가 명시되어야 한다. |
| RAG-06 | 임베딩 실패 시 사용자에게 명확한 오류와 재시도 경로를 제공한다. |

---

## 7. 하이브리드 질의 요건

### 7.1 질문 유형

시스템은 다음 유형을 지원해야 한다.

| 유형 | 예 | 처리 |
| --- | --- | --- |
| descriptive | "Snowflake 아키텍처를 설명해줘" | RAG 중심 |
| filter | "Serverless 과금 기능만 보여줘" | 온톨로지 필터 |
| compare | "A와 B 제품을 비교해줘" | 온톨로지 비교 + RAG 보강 |
| calculate | "고위험 고객 주문 금액 합계는?" | 온톨로지 계산 |
| relation | "이 고객과 연결된 주문은?" | 관계 탐색 |
| hybrid | "조건에 맞는 기능과 근거 설명을 함께 보여줘" | 온톨로지 + RAG |

### 7.2 Query Planner

| ID | 요구사항 |
| --- | --- |
| HQ-01 | LLM은 질문을 실행 가능한 JSON Query Plan으로 변환한다. |
| HQ-02 | Query Plan은 intent, filters, sort, metrics, entity_refs, relation_path, doc_ids를 포함할 수 있다. |
| HQ-03 | Query Plan은 Pydantic 또는 JSON Schema로 검증한다. |
| HQ-04 | 검증 실패 시 규칙 기반 fallback planner를 사용한다. |
| HQ-05 | 실제 필터/비교/계산은 코드가 결정적으로 실행한다. |

### 7.3 응답 형식

하이브리드 질의 응답은 다음을 포함해야 한다.

```json
{
  "question": "...",
  "query_plan": {},
  "answer": "...",
  "structured_data": {
    "headers": [],
    "rows": []
  },
  "ontology_evidence": [],
  "document_evidence": [],
  "trace": [],
  "warnings": []
}
```

---

## 8. 프론트엔드 요건

| 화면 | 필수 기능 |
| --- | --- |
| Dashboard | 문서, 객체, 관계, 프로젝트, 최근 질의 요약 |
| Ontology Schema | 객체/관계/액션 타입 관리 |
| Ontology Instances | 객체/관계 인스턴스 CRUD, 후보 승인 |
| Ontology Graph | 관계 그래프 탐색/편집 |
| Documents | 업로드, 삭제, 추출 상태, 근거 확인 |
| Hybrid Query | 질문 입력, Query Plan, 구조형 결과, 근거 표시 |
| Users/Projects | 사용자 전환, 프로젝트 선택, 권한 확인 |
| Audit | 질의/편집/권한 거부 로그 조회 |

권한이 없는 기능은 UI에서 비활성화하거나 숨기되, API 권한 검사를 대체해서는 안 된다.

---

## 9. 감사와 관측성

| ID | 요구사항 |
| --- | --- |
| OBS-01 | 질의 실행 trace를 저장한다. |
| OBS-02 | 권한 거부 이벤트를 감사 로그에 남긴다. |
| OBS-03 | LLM 호출, 검색, 온톨로지 질의, 합성 단계를 span 또는 trace로 구분한다. |
| OBS-04 | latency_ms, retrieved_documents, ontology_node_count, llm_provider를 기록한다. |

---

## 10. 테스트와 완료 기준

### 10.1 자동 테스트

| 테스트 | 기준 |
| --- | --- |
| Backend unit | 스키마 검증, 권한, 질의 엔진 |
| API integration | 주요 API 2xx/4xx 검증 |
| Hybrid scenarios | filter/compare/calculate/relation/hybrid 최소 20개 |
| Permission scenarios | viewer/editor/admin/company 격리 최소 15개 |
| Frontend E2E | 주요 화면 진입, 질의 실행, 권한 버튼 상태 |

### 10.2 Definition of Done

기능은 다음을 만족해야 완료로 본다.

- API 구현 완료
- 프론트에서 사용 가능
- 권한 검사 적용
- 오류 코드 정의
- 최소 단위 테스트 추가
- 관련 통합 시나리오 추가
- 문서 업데이트
- 회귀 테스트 통과

상세 API, 데이터, 구현 계획, 인수 테스트 기준은 다음 문서를 따른다.

- [03_FINAL_API_SPEC.md](03_FINAL_API_SPEC.md)
- [04_FINAL_DATA_SCHEMA.md](04_FINAL_DATA_SCHEMA.md)
- [05_MVP_IMPLEMENTATION_PLAN.md](05_MVP_IMPLEMENTATION_PLAN.md)
- [06_ACCEPTANCE_TEST_PLAN.md](06_ACCEPTANCE_TEST_PLAN.md)
- [07_UX_AND_OPERATIONS.md](07_UX_AND_OPERATIONS.md)

---

## 11. MVP 범위

1차 MVP는 다음까지만 포함한다.

- JSON 기반 저장소
- 회사/프로젝트/사용자 시드 데이터
- 온톨로지 스키마/인스턴스 CRUD
- 문서 업로드 및 검색
- Query Planner + 결정적 온톨로지 질의
- 하이브리드 질의 화면
- 권한 게이트와 API 403
- 자동 테스트와 HTML 리포트

2차 이후 과제:

- PostgreSQL 전환
- 실시간 협업 편집
- 고급 그래프 알고리즘
- BPMN/워크플로우 엔진 통합
- SSO/OAuth
- 운영용 관리자 콘솔
