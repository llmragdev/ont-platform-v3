# 07. UX 및 운영 품질 기준

작성일: 2026-05-13  
목표: 기능 구현을 넘어 사용성과 운영 신뢰성을 확보

---

## 1. UX 원칙

| 원칙 | 설명 |
| --- | --- |
| Scope visibility | 현재 사용자, 회사, 프로젝트를 항상 볼 수 있어야 한다. |
| Evidence first | AI 답변보다 근거와 구조형 결과가 먼저 검증 가능해야 한다. |
| No silent deny | 권한 때문에 막힌 기능은 가능한 경우 이유를 표시한다. |
| Stable layout | 테이블, 그래프, 패널은 데이터 변화로 과도하게 흔들리지 않아야 한다. |
| Explainable AI | Query Plan과 trace를 사용자가 열어볼 수 있어야 한다. |
| Tenant safety | 화면, API, 로그 어디에서도 다른 회사/프로젝트 데이터가 섞여 보이면 안 된다. |

---

## 2. 공통 레이아웃

상단 바:

- 현재 사용자
- 회사
- 프로젝트
- 역할
- 권한 요약
- 로그인/로그아웃

좌측 메뉴:

- Dashboard
- Documents
- Ontology Schema
- Ontology Instances
- Ontology Graph
- Hybrid Query
- Audit
- Admin

우측 또는 하단 보조 패널:

- 선택 객체 context
- Query Plan
- Evidence
- Trace

---

## 3. 권한 UX

권한 없는 기능 처리:

| 상황 | UX |
| --- | --- |
| 조회 권한 없음 | 화면 진입 차단 + 403 설명 |
| 편집 권한 없음 | 버튼 disabled + tooltip |
| 삭제 권한 없음 | 삭제 버튼 숨김 또는 disabled |
| API에서 403 | toast/error banner에 필요한 권한 표시 |

문구 예:

```text
이 작업에는 can_edit_relationship 권한이 필요합니다.
현재 역할 viewer는 관계를 수정할 수 없습니다.
```

`PermissionGate`는 다음 모드를 지원한다.

- `hide`: 렌더링하지 않음
- `disable`: disabled 상태로 표시
- `readonly`: 읽기 전용 UI로 대체

---

## 4. Hybrid Query UX

화면 구성:

1. 질문 입력
2. 범위 선택: 현재 프로젝트, 문서 선택, top_k
3. 실행 버튼
4. 구조형 결과 테이블
5. 답변 요약
6. 문서 근거 패널
7. 온톨로지 근거 패널
8. Query Plan Viewer
9. Trace Panel
10. Warnings Panel

Query Plan Viewer:

- 기본 접힘
- JSON pretty print
- intent, filters, needs_vector를 badge로 요약
- fallback plan이면 노란 warning 표시

Evidence Panel:

- 문서명
- 페이지
- chunk score
- 인용 텍스트
- 연결된 ontology node

Warnings:

- 근거 부족
- 일부 필터 실패
- LLM planner fallback
- doc_ids 중 권한 없는 문서 제외
- 삭제되었거나 indexing 실패한 문서 제외

결과 표시 순서:

1. 구조형 결과 테이블
2. 답변 요약
3. 문서 근거
4. 온톨로지 근거
5. Query Plan
6. Trace
7. Warnings

구조형 결과가 있으면 답변 요약보다 먼저 보여준다. 사용자는 LLM 문장보다 계산/필터 결과를 먼저 검증할 수 있어야 한다.

---

## 5. Ontology UX

Schema Manager:

- 객체 타입 목록
- 관계 타입 목록
- 액션 타입 목록
- property editor
- required/searchable/sensitive 토글

Instance Manager:

- 타입 필터
- 검색
- status 필터: active/candidate/disabled
- candidate 승인/수정/거절
- 객체 상세 패널

Graph:

- 노드 타입별 색상
- 관계 타입별 edge label
- 선택 노드의 incoming/outgoing 목록
- 권한 없으면 편집 핸들 숨김

---

## 6. Dashboard KPI

표시할 지표:

- 문서 수
- 온톨로지 객체 수
- 관계 수
- candidate 수
- 최근 질의 수
- 권한 거부 이벤트 수
- 평균 hybrid query latency
- fallback planner 사용률

---

## 7. Audit 운영

Audit 화면 필터:

- 시간 범위
- 사용자
- action
- resource_type
- result: success/denied/error

필수 이벤트:

- LOGIN_SUCCESS
- LOGIN_FAILED
- PERMISSION_DENIED
- CREATE_OBJECT
- UPDATE_OBJECT
- DISABLE_RELATIONSHIP
- UPLOAD_DOCUMENT
- DELETE_DOCUMENT
- EXTRACT_ONTOLOGY
- HYBRID_QUERY
- PLANNER_FALLBACK

권한 거부 이벤트는 반드시 남긴다.

Audit 상세 화면에는 다음 값을 노출한다.

- 사용자, 회사, 프로젝트
- action, resource_type, resource_id
- result, error_code
- 요청 시각과 latency
- before/after diff
- trace 또는 query run link

---

## 8. 운영 지표

| 지표 | 목표 |
| --- | --- |
| 권한 위반 차단율 | 100% |
| 구조형 질의 성공률 | 95% 이상 |
| 하이브리드 질의 평균 응답 | MVP 기준 5초 이하 |
| fallback planner 사용률 | 20% 이하 |
| evidence 포함률 | 100% |
| E2E 통과율 | 100% |
| audit 누락률 | 0% |
| 다른 project 데이터 노출 | 0건 |

지표 산출 기준:

- `query_runs.jsonl`: latency, fallback planner 사용률, evidence count
- `audit_log.jsonl`: 권한 거부, 쓰기 작업, 로그인, planner fallback
- integration report: 권한/격리/E2E 통과율
- frontend runtime log: 사용자에게 노출된 API error와 recovery 여부

---

## 9. 운영 모드 설정

환경 변수:

```text
ALLOW_DEV_USER=false
AUTH_REQUIRED=true
JWT_SECRET=...
DATA_DIR=backend/data
VECTOR_DB_DIR=backend/vector_db
LLM_PROVIDER=gemini
LLM_TIMEOUT_SEC=30
MAX_UPLOAD_MB=50
CHUNK_SIZE=700
CHUNK_OVERLAP_RATIO=0.12
OTEL_ENABLED=false
LOG_LEVEL=INFO
```

운영 모드에서는:

- `?user_id=` 금지
- JWT 필수
- CORS origin 제한
- audit log 활성
- permission denied log 활성
- upload 확장자와 파일 크기 제한
- 문서 저장 경로는 `company_id/project_id` 아래로 제한
- LLM timeout과 fallback planner 정책 활성
- 민감 필드 로그 마스킹

---

## 10. 배포/운영 표준

MVP 배포 단위:

| 구성요소 | 실행 방식 | 비고 |
| --- | --- | --- |
| Backend | FastAPI/Uvicorn | `/api/v1` |
| Frontend | Next.js | API base URL 환경 변수 사용 |
| Data | JSON files | `DATA_DIR`로 위치 지정 |
| Uploads | local filesystem | 운영 전환 시 object storage 가능 |
| Vector DB | local adapter | FAISS/Chroma 교체 가능 |

배포 전 점검:

- `AUTH_REQUIRED=true`
- `ALLOW_DEV_USER=false`
- `JWT_SECRET` 기본값 사용 금지
- CORS origin 명시
- `DATA_DIR`, `UPLOAD_DIR`, `VECTOR_DB_DIR` 쓰기 권한 확인
- seed data에 테스트 password가 남아 있지 않은지 확인
- `/docs` 또는 OpenAPI 노출 정책 결정

백업:

- JSON data와 uploads는 같은 시점의 snapshot으로 백업한다.
- vector index는 `vector_mapping.json`과 함께 백업한다.
- 백업 파일명에는 UTC timestamp와 environment를 포함한다.

복구:

- registry에 있는데 파일이 없으면 문서는 `index_failed` 또는 `deleted`로 격리한다.
- vector mapping에 있는데 chunk가 없으면 해당 vector 결과는 검색에서 제외한다.
- JSON parse 실패 시 마지막 정상 백업으로 복구하고 audit에 운영 이벤트를 남긴다.

---

## 11. 보안 기준

인증/인가:

- 모든 운영 API는 JWT를 요구한다.
- 권한은 서버에서만 판정한다.
- 클라이언트가 보낸 `company_id`, `project_id`, `created_by`는 신뢰하지 않는다.

데이터 보호:

- `sensitive=true` property는 로그와 evidence snippet에서 마스킹한다.
- password는 평문 저장 금지, hash만 저장한다.
- 파일 경로 traversal을 차단한다.
- 삭제 문서와 disabled relationship은 기본 검색에서 제외한다.

LLM 안전:

- LLM planner 결과는 schema 검증 전까지 실행하지 않는다.
- schema에 없는 타입/필드는 자동 실행하지 않는다.
- 근거 없는 답변은 warning과 함께 제한한다.
- 최종 답변 생성 LLM에는 현재 project evidence만 전달한다.

---

## 12. 장애 처리 기준

| 상황 | 처리 |
| --- | --- |
| JSON 저장 실패 | 500, audit error, 기존 파일 유지 |
| 문서 파싱 실패 | registry `index_failed`, 사용자에게 파일 처리 실패 표시 |
| Vector adapter 실패 | BM25 fallback, warning 표시 |
| LLM planner timeout | rule-based fallback planner |
| LLM answer timeout | structured result와 evidence만 반환 |
| 권한 없는 doc_id 포함 | 403 또는 제외 후 warning |
| 다른 project object 직접 조회 | 403 또는 404 |

사용자에게 보여줄 오류는 기술 stack trace가 아니라 action 가능한 문장이어야 한다.

---

## 13. 릴리스 전 UX 체크리스트

- [ ] 현재 사용자/회사/프로젝트가 상단에 보인다.
- [ ] viewer는 편집 버튼을 사용할 수 없다.
- [ ] 권한 없는 API 실패가 이해 가능한 메시지로 표시된다.
- [ ] Hybrid Query 결과에 plan/result/evidence/trace가 모두 보인다.
- [ ] 근거 없는 답변은 warning을 표시한다.
- [ ] 그래프와 테이블이 모바일/좁은 화면에서 깨지지 않는다.
- [ ] 새로고침 후 사용자와 프로젝트가 복원된다.
- [ ] audit 화면에서 권한 거부 이벤트를 찾을 수 있다.
- [ ] fallback planner가 사용되면 사용자가 확인할 수 있다.
- [ ] 삭제/실패 문서는 검색 근거에 나오지 않는다.
- [ ] evidence snippet에 민감 필드가 노출되지 않는다.
