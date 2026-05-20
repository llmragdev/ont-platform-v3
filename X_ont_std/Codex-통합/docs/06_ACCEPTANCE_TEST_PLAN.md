# 06. 인수 테스트 계획

작성일: 2026-05-13  
목표: MVP 완료 여부를 자동 테스트로 판정

---

## 1. 테스트 원칙

- 수동 확인은 완료 기준이 아니다.
- 모든 권한/격리 요구사항은 API 테스트로 검증한다.
- 프론트 권한 UI는 Playwright로 검증한다.
- 하이브리드 질의는 정답 문자열보다 구조형 결과와 근거 포함 여부를 우선 검증한다.

---

## 2. 테스트 데이터

기본 사용자:

| user | company | role | project | 특징 |
| --- | --- | --- | --- | --- |
| `alice` | acme | editor | proj-acme-sales | 편집 가능 |
| `bob` | acme | viewer | proj-acme-sales | 조회만 |
| `carol` | globex | admin | proj-globex-ops | 전체 편집 가능 |
| `dave` | globex | viewer | proj-globex-ops | `can_upload_doc=true` override |
| `auditor` | acme | auditor | proj-acme-sales | audit 조회 |

기본 객체:

- ACME: `C001`, `O001`, `P001`
- Globex: `G001`, `GO001`, `GP001`

기본 문서:

| doc_id | company | project | status | 특징 |
| --- | --- | --- | --- | --- |
| `doc-acme-001` | acme | proj-acme-sales | indexed | Serverless 과금 설명 포함 |
| `doc-acme-deleted` | acme | proj-acme-sales | deleted | 검색 제외 확인 |
| `doc-globex-001` | globex | proj-globex-ops | indexed | ACME 사용자에게 미노출 |

필수 fixture 파일:

- `companies.json`
- `projects.json`
- `users.json`
- `role_defaults.json`
- `ontology_schema.json`
- `ontology_objects.json`
- `ontology_relationships.json`
- `documents_registry.json`
- `document_chunks.json`
- `vector_mapping.json`

---

## 3. 권한/격리 API 테스트

| ID | 요청 | 기대 |
| --- | --- | --- |
| PERM-01 | bob `POST /ontology/objects` | 403 `PERMISSION_DENIED` |
| PERM-02 | bob `POST /ontology/relationships` | 403 |
| PERM-03 | bob `DELETE /ontology/relationships/REL001` | 403 |
| PERM-04 | bob `POST /documents/upload` | 403 |
| PERM-05 | alice `POST /ontology/objects` | 201 |
| PERM-06 | alice `POST /ontology/relationships` | 201 |
| PERM-07 | alice `DELETE /documents/doc-acme-001` | 403 |
| PERM-08 | carol `PUT /ontology/schema` | 200 |
| PERM-09 | dave `POST /documents/upload` | 201 |
| PERM-10 | auditor `GET /audit/events` | 200 |
| PERM-11 | bob `GET /audit/events` | 403 |
| ISO-01 | alice `GET /documents` | Globex 문서 없음 |
| ISO-02 | carol `GET /documents` | ACME 문서 없음 |
| ISO-03 | alice `GET /ontology/objects/G001` | 403 또는 404 |
| ISO-04 | carol `GET /ontology/objects/C001` | 403 또는 404 |
| ISO-05 | alice project를 `proj-globex-ops`로 요청 | 403 `PROJECT_FORBIDDEN` |

---

## 4. 온톨로지 CRUD 테스트

| ID | 시나리오 | 기대 |
| --- | --- | --- |
| ONT-01 | `Contract` 타입 추가 | schema version 증가 |
| ONT-02 | `Contract` 객체 생성 | ID prefix `CT` 적용 |
| ONT-03 | required property 누락 | 422 |
| ONT-04 | enum 범위 밖 값 | 422 |
| ONT-05 | 관계 source/target 타입 일치 | 201 |
| ONT-06 | 관계 source/target 타입 불일치 | 422 |
| ONT-07 | 객체 context 조회 | incoming/outgoing/documents/actions 포함 |
| ONT-08 | 관계 삭제 | `status=disabled` |
| ONT-09 | disabled 관계는 기본 목록에서 제외 | 제외됨 |
| ONT-10 | `include_disabled=true` | disabled 포함 |

---

## 5. 문서/RAG 테스트

| ID | 시나리오 | 기대 |
| --- | --- | --- |
| DOC-01 | editor PDF 업로드 | registry 생성 |
| DOC-02 | upload 후 검색 | document_evidence 반환 |
| DOC-03 | doc_ids 필터 검색 | 지정 문서만 검색 |
| DOC-04 | 다른 company doc_id 검색 | 결과 없음 또는 403 |
| DOC-05 | 문서 삭제 | registry status `deleted` |
| DOC-06 | 삭제 문서 검색 | 결과 없음 |
| DOC-07 | chunk 생성 확인 | `document_chunks`에 `chunk_id`, `doc_id`, `page`, `vector_id` 저장 |
| DOC-08 | vector 검색 결과 복원 | `vector_mapping` -> `document_chunks` -> `documents_registry` 연결 |
| DOC-09 | indexing 실패 파일 업로드 | registry status `index_failed`, `error_message` 저장 |
| DOC-10 | 검색 evidence 필드 검증 | `doc_id`, `filename`, `page`, `chunk_id`, `score`, `snippet` 포함 |

---

## 6. 하이브리드 질의 테스트

| ID | 질문 | 기대 |
| --- | --- | --- |
| HQ-01 | "ACME의 고위험 고객만 보여줘" | `intent=filter`, Customer rows |
| HQ-02 | "C001과 C002를 비교해줘" | `intent=compare`, 비교 테이블 |
| HQ-03 | "ACME 주문 금액 합계는?" | `intent=calculate`, numeric result |
| HQ-04 | "C001과 연결된 주문은?" | `intent=relation`, relationship evidence |
| HQ-05 | "Serverless 과금 기능과 근거를 알려줘" | structured + document evidence |
| HQ-06 | 존재하지 않는 타입 질문 | warning 포함, 임의 답변 금지 |
| HQ-07 | LLM planner JSON 실패 | fallback plan 사용 |
| HQ-08 | 다른 project doc_ids 포함 | 403 또는 doc 제외 |
| HQ-09 | 답변에 source doc 누락 | 테스트 실패 |
| HQ-10 | 답변에 ontology node 누락 | 구조형 질의면 테스트 실패 |
| HQ-11 | "C001과 연결된 주문 합계는?" | relation + calculate plan, LLM 없이 structured result |
| HQ-12 | 삭제된 문서만 doc_ids 지정 | warning 포함, document_evidence 비어 있음 |
| HQ-13 | fallback planner 사용 | `query_plan.fallback_used=true`, audit/query run 기록 |
| HQ-14 | 근거 부족 질문 | 단정 답변 금지, warnings 포함 |

응답 필수 필드:

- `query_plan`
- `structured_data`
- `ontology_evidence`
- `document_evidence`
- `trace`
- `warnings`

Query run 검증:

- `query_runs.jsonl`에 `run_id`, `latency_ms`, `fallback_used`, `document_evidence_count`, `ontology_evidence_count`가 저장된다.
- 권한 없는 문서가 제외되면 `warnings` 또는 403 응답으로 드러난다.
- 구조형 질의 결과는 LLM 사용 여부와 무관하게 재현 가능해야 한다.

---

## 7. 프론트 E2E 테스트

| ID | 시나리오 | 기대 |
| --- | --- | --- |
| E2E-01 | alice 로그인 | 프로젝트/회사 배지 표시 |
| E2E-02 | bob 전환 | 편집 버튼 disabled 또는 hidden |
| E2E-03 | alice 전환 | 편집 버튼 enabled |
| E2E-04 | 새로고침 | 마지막 사용자/프로젝트 복원 |
| E2E-05 | 문서 업로드 | 문서 목록 갱신 |
| E2E-06 | Hybrid Query 실행 | Plan/Result/Evidence 패널 표시 |
| E2E-07 | 권한 없는 API 실패 | 사용자 친화 오류 표시 |
| E2E-08 | fallback plan 응답 | Query Plan Viewer에 warning badge 표시 |
| E2E-09 | 삭제 문서 포함 질의 | Warnings Panel에 제외 사유 표시 |
| E2E-10 | Audit 화면 필터 | `PERMISSION_DENIED`, `HYBRID_QUERY` 이벤트 검색 가능 |

---

## 8. 감사/운영 로그 테스트

| ID | 시나리오 | 기대 |
| --- | --- | --- |
| AUD-01 | 로그인 성공 | `LOGIN_SUCCESS` event 저장 |
| AUD-02 | 로그인 실패 | `LOGIN_FAILED` event 저장 |
| AUD-03 | 권한 없는 쓰기 요청 | `PERMISSION_DENIED` event 저장 |
| AUD-04 | 객체 생성 | `CREATE_OBJECT` event에 before null, after object |
| AUD-05 | 관계 삭제 | `DISABLE_RELATIONSHIP` event 저장 |
| AUD-06 | 문서 업로드 | `UPLOAD_DOCUMENT` event 저장 |
| AUD-07 | Hybrid Query 실행 | `HYBRID_QUERY` event와 query run 저장 |
| AUD-08 | planner fallback | `PLANNER_FALLBACK` event 저장 |

감사 로그 필수 필드:

- `event_id`
- `timestamp`
- `user_id`
- `company_id`
- `project_id`
- `action`
- `resource_type`
- `resource_id`
- `result`
- `error_code`
- `latency_ms`

---

## 9. 리포트 형식

통합 테스트 runner는 다음 JSON을 저장한다.

```json
{
  "run_id": "run-20260513-001",
  "started_at": "2026-05-13T00:00:00Z",
  "summary": {
    "total": 68,
    "passed": 68,
    "failed": 0
  },
  "cases": [
    {
      "id": "PERM-01",
      "status": "passed",
      "latency_ms": 12
    }
  ]
}
```

HTML 리포트는 실패 케이스, 요청/응답, trace를 접이식으로 보여준다.
