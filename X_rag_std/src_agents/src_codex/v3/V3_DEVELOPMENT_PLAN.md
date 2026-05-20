# src_codex v3 개발 계획

작성일: 2026-05-15

## 1. 목표

`src_codex` v3는 `RAG_표준_설계_v1.3.md`를 기준으로 기존 v2 구현을 업그레이드하는 버전이다. v2에서 이미 확보한 Gemini Gateway 연동, Chroma embedding 일관성, 문서/검색/대화 API를 유지하면서, v1.3의 `tenant_id`/`org_id` 격리 표준과 cross-code 평가에서 지적된 v2 결함을 v3에서 함께 수정한다.

v3의 기준 구현은 `src_agents/src_codex`이다. `src_claud/v2`의 API 범위와 테스트 구조 장점은 참고하되, v2 구현체를 그대로 병합하지 않는다.

## 2. 입력 기준

- 표준 문서: `RAG_표준_설계_v1.3.md`
- 평가 보고서: `src_agents/cross-코드-평가`
- 기존 기준 구현: `src_agents/src_codex`
- 비교 참고 구현: `src_agents/src_claud/v2`, `src_agents/src_antigravity/v2`

## 3. v3 핵심 변경 요약

| 영역 | v2 상태 | v3 목표 |
|------|---------|---------|
| 테넌트 키 | `company_id`, `X-Company-ID`, default fallback 존재 | `tenant_id`, `X-Tenant-ID` 필수, 누락 시 400 |
| 조직 범위 | 없음 또는 미정의 | `X-Org-ID`, `org_id`, `dept_code`, 전사 공유 포함 정책 구현 |
| RDBMS 조직 PK | `org_id` 단독 PK 성격 | `(tenant_id, org_id)` 복합키 또는 동등한 전역 안전 구조 |
| Vector metadata | `company_id`, `tags` 포함 | `tenant_id`, `org_id`, `dept_code`; `tags`는 Vector DB metadata 제외 |
| 검색 필터 | `company_id` 강제 | `tenant_id` 강제 + org scope 정책 적용 |
| PDF page_no | 일부 chunk index 기반 | 실제 PDF 페이지 번호 보존 |
| DB migration | ad-hoc column migration | Alembic 기반 정식 migration |
| 비동기/스레드 | 일부 blocking 가능성 | DB Session thread-safe 처리, 장기 작업 분리 |
| 라우팅 | routing JSON 수동 관리 | category/project 변경 시 routing 반영 정책 명확화 |
| 테스트 | v2 기능 중심 | v1.3 격리/metadata/오류 계약 테스트 추가 |

## 4. v2 버그 수정 항목

### 4.1. Critical

1. `X-Company-ID`/`company_id`를 `X-Tenant-ID`/`tenant_id`로 전면 교체한다.
2. `X-Tenant-ID` 누락 시 `"default"` fallback을 금지하고 400 오류를 반환한다.
3. RAG 검색, 문서 목록, 문서 삭제, 문서 수정, 대화 이력 저장 경로에 `tenant_id` 격리를 강제한다.
4. Gemini Gateway embed/generate/stream 호출 body에 실제 `tenant_id`를 전달한다.
5. Vector DB 검색 필터에 `tenant_id`를 항상 주입한다.

### 4.2. High

1. `org_id`/`dept_code` 기반 조직 범위 검색을 구현한다.
2. 팀 검색은 `tenant_id == T AND (org_id == X OR org_id IS NULL)` 정책을 적용한다.
3. 부서 검색은 `tenant_id == T AND (dept_code == D OR org_id IS NULL)` 정책을 적용한다.
4. `X-Org-ID`가 없는 일반 사용자는 인증된 사용자 소속 `org_id`로 자동 보정하거나 403 처리한다.
5. 관리자/시스템 토큰만 `tenant_id` 단독 전사 검색을 허용한다.
6. SQLAlchemy 모델의 FK와 조직 복합키를 보강한다.
7. `datetime.utcnow()` 계열을 timezone-aware UTC로 교체한다.

### 4.3. Medium

1. PDF 파서가 실제 페이지 번호를 chunk metadata의 `page_no`에 보존하도록 수정한다.
2. 문서 pipeline에서 DB Session을 thread 간 공유하지 않도록 구조를 정리한다.
3. Alembic migration을 도입하고 기존 ad-hoc schema patch를 제거한다.
4. category/project API 변경 시 routing registry와 불일치하지 않도록 갱신 정책을 추가한다.
5. 표준 오류 응답을 `status`, `error_code`, `message` 구조로 통일한다.

## 5. v1.3 표준 반영 항목

### 5.1. 헤더 계약

- 필수: `X-Tenant-ID`
- 선택: `X-Org-ID`
- 호환: v3 초기에는 `X-Company-ID`를 읽지 않는다. 필요 시 별도 legacy compatibility flag에서만 허용한다.

### 5.2. Metadata 계약

Vector DB metadata 필수/권장 필드는 다음으로 제한한다.

- `doc_id`
- `tenant_id`
- `org_id`
- `dept_code`
- `source_url`
- `source_name`
- `created_at`
- `vector_db_id`
- `category_mid`
- `category_low`
- `page_no`
- `chunk_type`

`tags`는 RDBMS/API 응답 전용으로 유지하고 Vector DB metadata에는 저장하지 않는다.

### 5.3. 조직 코드 정책

- `0100`: 01부서 공통 소유 문서 코드
- `0101`, `0102`: 팀 소유 문서 코드
- 부서 전체 검색: `dept_code == "01"` 조건 사용
- `org_id IS NULL`: 전사 공유 문서

## 6. 구현 단계

### Phase 0. v3 작업 공간 준비

- `src_agents/src_codex/v3`에 계획/설계 문서 유지
- 기존 v2 테스트를 기준선으로 보존
- v3 변경 전 `pytest -q`와 `python test_endpoints.py` 결과 기록

### Phase 1. 도메인 용어 전환

- schema, model, repository, service, API에서 `company_id`를 `tenant_id`로 변경
- `X-Company-ID`를 `X-Tenant-ID`로 변경
- default fallback 제거
- 관련 README/RUN_GUIDE 갱신

### Phase 2. RDBMS 및 migration 정리

- Alembic 도입
- `ca_company.tenant_id` 기준 테이블 재정의
- `ca_org_mgnt` 복합키 또는 전역 안전키 적용
- `wc_project_rag_doc`, `wc_dialog_history`, `ca_user`에 `tenant_id`, `org_id` FK 보강
- 기존 SQLite ad-hoc migration 제거

### Phase 3. 조직 범위 검색 구현

- request context resolver 도입
- `resolve_org_scope()` 구현
- vector adapter filter builder가 OR 조건을 표현할 수 있도록 확장
- Local JSON/Chroma adapter 모두 v1.3 scope 정책을 동일하게 적용

### Phase 4. 문서 pipeline 개선

- PDF page 단위 chunking 보강
- `dept_code` 자동 파생
- `tags` Vector metadata 제외
- pipeline DB Session thread safety 수정
- embedding failure fallback 금지 테스트 추가

### Phase 5. Gateway 및 VectorDB 계약 강화

- Gemini Gateway 요청 payload의 `company_id`를 `tenant_id`로 변경
- Chroma `add()` 호출 시 `embeddings=` 명시 유지
- Chroma/Qdrant 호환을 고려해 scalar metadata만 저장
- routing registry index swap 설계 반영

### Phase 6. 테스트 및 문서화

- v1.3 compliance 테스트 추가
- tenant/org isolation 테스트 추가
- Chroma embedding contract 테스트 유지/확장
- Gateway payload 테스트 갱신
- README, RUN_GUIDE, upgrade note 작성

## 7. 테스트 계획

필수 테스트는 다음을 포함한다.

1. `X-Tenant-ID` 누락 시 400
2. 일반 사용자 `X-Org-ID` 누락 시 사용자 조직으로 자동 보정 또는 403
3. 관리자 `X-Org-ID` 누락 시 전사 검색 허용
4. 팀 검색 시 팀 문서와 전사 공유 문서만 반환
5. 부서 검색 시 해당 부서 문서와 전사 공유 문서만 반환
6. 타 tenant 문서가 어떤 검색에서도 반환되지 않음
7. Vector metadata에 `tenant_id`, `org_id`, `dept_code`, `vector_db_id`, `created_at` 포함
8. Vector metadata에 `tags`가 저장되지 않음
9. Gateway embed/generate/stream 요청에 실제 `tenant_id` 전달
10. Chroma document embedding 저장 시 `embeddings=` 명시
11. PDF chunk metadata의 `page_no`가 실제 PDF 페이지 번호
12. embedding 실패 시 fallback vector 없이 표준 오류 반환
13. update/delete가 `tenant_id` ownership을 검증
14. Alembic migration으로 빈 DB 생성 및 기존 v2 DB migration 성공

## 8. 완료 기준

- v1.3 표준 필수 항목이 테스트로 고정되어야 한다.
- 기존 v2 테스트가 v3 용어 전환 후 모두 통과해야 한다.
- cross-code 평가에서 지적된 `src_codex` 보완점인 FK, page_no, Session safety, migration 문제가 해결되어야 한다.
- `company_id`와 `X-Company-ID`는 운영 기본 경로에서 제거되어야 한다.
- README/RUN_GUIDE가 v1.3 기준으로 갱신되어야 한다.

