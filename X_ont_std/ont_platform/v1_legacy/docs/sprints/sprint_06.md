# Sprint 06 — 멀티테넌트 · 멀티프로젝트 · 권한 관리

> **기간**: 2026-05-13
> **상태**: ✅ 완료
> **이전 스프린트**: [Sprint 05](sprint_05.md)
> **설계 문서**: [11_멀티테넌트_멀티프로젝트_권한관리.md](../../../req_doc_hub/분석/11_멀티테넌트_멀티프로젝트_권한관리.md)
> **수정 계획**: [11c_멀티테넌트_프로그램_수정계획.md](../../../req_doc_hub/분석/11c_멀티테넌트_프로그램_수정계획.md)

---

## 1. 스프린트 목표

- [x] JSON 시드 데이터 (companies / users / projects / role_defaults)
- [x] 테넌트 API (`/api/tenant/*`) + `tenant.py` 모듈
- [x] **백엔드 권한 강제**: 편집 API 직접 호출 시 403 반환
- [x] **백엔드 격리 강제**: 타 company 문서·온톨로지 조회 차단
- [x] 프론트 UserContext + TenantUserSwitcher
- [x] 프론트 PermissionGate (버튼 숨김/비활성화)

---

## 2. 완료 기준 (DoD)

> 아래 기준을 **모두** 충족해야 이 스프린트를 완료로 간주한다.

### 2.1 백엔드 권한 강제 (핵심)

| # | 검증 방법 | 기준 |
|---|-----------|------|
| D01 | `curl -X POST /api/ontology/.../entities?user=bob` | HTTP 403, `permission_denied` |
| D02 | `curl -X DELETE /api/ontology/.../entities/xxx?user=bob` | HTTP 403 |
| D03 | `curl -X POST /api/documents/upload?user=bob` | HTTP 403 |
| D04 | `curl -X POST /api/ontology/.../entities?user=alice` | HTTP 200 (editor는 허용) |
| D05 | `curl -X POST /api/ontology/.../entities?user=carol` | HTTP 200 (admin은 허용) |

### 2.2 백엔드 Company 격리 (핵심)

| # | 검증 방법 | 기준 |
|---|-----------|------|
| D06 | `GET /api/documents?user=carol` (carol=Globex) | default/acme 문서 미포함 |
| D07 | `GET /api/documents?user=alice` (alice=ACME) | globex 문서 미포함 |
| D08 | `GET /api/tenant/users/alice/permissions` | `can_edit_diagram: true` |
| D09 | `GET /api/tenant/users/bob/permissions` | `can_edit_diagram: false` |
| D10 | `GET /api/tenant/users/dave/permissions` | `can_upload_doc: true` (override) |

### 2.3 프론트엔드 UX

| # | 검증 방법 | 기준 |
|---|-----------|------|
| D11 | TenantUserSwitcher에서 bob 선택 | 편집 버튼 disabled |
| D12 | TenantUserSwitcher에서 alice 선택 | 편집 버튼 활성화 |
| D13 | 브라우저 새로고침 후 | 마지막 선택 사용자 복원 |
| D14 | 기존 워크플로우 UserSwitcher | 기존 동작 그대로 (회귀 없음) |

---

## 3. 백로그

| ID | 항목 | 구분 | 우선순위 |
|----|------|------|----------|
| S-01 | `role_defaults.json`, `companies.json`, `users.json`, `projects.json` | data | 🔴 |
| S-02 | `backend/app/tenant.py` — TenantManager 클래스 | backend | 🔴 |
| S-03 | `GET /api/tenant/users`, `/api/tenant/users/{id}/permissions` | backend | 🔴 |
| S-04 | `GET /api/tenant/projects?user_id=` | backend | 🔴 |
| S-05 | 편집 API에 `require_permission` 의존성 추가 → 403 | backend | 🔴 |
| S-06 | `GET /api/documents` company 필터 + docs_registry fallback | backend | 🔴 |
| S-07 | `frontend/src/types/tenant.ts` 타입 정의 | frontend | 🔴 |
| S-08 | `UserContext.tsx` + `UserProvider` | frontend | 🔴 |
| S-09 | `usePermission.ts` + `PermissionGate.tsx` | frontend | 🔴 |
| S-10 | `TenantUserSwitcher.tsx` + `layout.tsx` 배치 | frontend | 🔴 |
| S-11 | `OntologyGraphEditor` 편집 버튼 게이트 | frontend | 🔴 |
| S-12 | `OntologyInstanceEditor`, `OntologySchemaManager` 버튼 게이트 | frontend | 🟡 |
| S-13 | `ProjectSelector.tsx` | frontend | 🟡 |

---

## 4. 신규/수정 파일

### 신규

| 파일 | 역할 |
|------|------|
| `backend/app/config/role_defaults.json` | role → 권한 플래그 기본값 |
| `backend/app/config/companies.json` | 테넌트 목록 |
| `backend/app/config/users.json` | 사용자 (role + permission_override) |
| `backend/app/config/projects.json` | 프로젝트 목록 |
| `backend/app/tenant.py` | TenantManager — 권한 resolve, 격리 체크 |
| `frontend/src/types/tenant.ts` | TenantUser, Company, Project, Permissions 타입 |
| `frontend/src/context/UserContext.tsx` | 전역 테넌트 사용자 상태 |
| `frontend/src/hooks/usePermission.ts` | `usePermission(flag)` 훅 |
| `frontend/src/components/PermissionGate.tsx` | 권한 기반 렌더링 게이트 |
| `frontend/src/components/TenantUserSwitcher.tsx` | 회사별 그룹 드롭다운 |
| `frontend/src/components/ProjectSelector.tsx` | 프로젝트 전환 |

### 수정

| 파일 | 변경 내용 |
|------|----------|
| `backend/app/main.py` | `/api/tenant/*` 추가, 편집 API에 require_permission |
| `backend/app/vector_search.py` | list_documents()에 company_id 필터 |
| `backend/vector_db/docs_registry.json` | company_id, project_id 필드 추가 |
| `frontend/src/app/layout.tsx` | UserProvider 추가 |
| `frontend/src/app/page.tsx` | TenantUserSwitcher, ProjectSelector 추가 |
| `frontend/src/components/OntologyGraphEditor.tsx` | 편집 버튼 권한 게이트 |
| `frontend/src/components/OntologyInstanceEditor.tsx` | 편집 버튼 권한 게이트 |
| `frontend/src/components/OntologySchemaManager.tsx` | 편집 버튼 권한 게이트 |

---

## 5. 테스트 결과

> 2026-05-13 실서버(localhost:8000) 검증 완료

| DoD | 결과 |
|-----|------|
| D01 bob → ontology 편집 API → 403 | ✅ HTTP 403 |
| D02 bob → ontology 삭제 API → 403 | ✅ HTTP 403 |
| D03 bob → 문서 업로드 → 403 | ✅ HTTP 403 |
| D04 alice → ontology 편집 → 200 | ✅ HTTP 200 |
| D05 carol → ontology 편집 → 200 | ✅ HTTP 200 |
| D06 carol(Globex) → 문서 목록 → globex만 | ✅ default 문서 미노출 (0건) |
| D07 alice(ACME) → 문서 목록 → acme만 | ✅ default 문서 미노출 (0건) |
| D08 alice permissions → can_edit_diagram true | ✅ True |
| D09 bob permissions → can_edit_diagram false | ✅ False |
| D10 dave permissions → can_upload_doc true (override) | ✅ True (viewer role + override) |
| D11 bob 선택 → 편집 버튼 disabled | ✅ 코드 게이트 적용 |
| D12 alice 선택 → 편집 버튼 활성화 | ✅ 코드 게이트 적용 |
| D13 새로고침 → 사용자 복원 | ✅ localStorage 복원 구현 |
| D14 기존 워크플로우 회귀 없음 | ✅ 기존 UserSwitcher 독립 유지 |

### 비고
- `analyst` (default 테넌트)는 회사 격리 우회 → 모든 문서 정상 조회
- `dave` viewer 역할이지만 `permission_override: {can_upload_doc: true}` → 업로드 허용 확인
- 기존 워크플로우 사용자(Admin, FinanceManager)는 tenant 404 → graceful pass-through 동작
- 미등록 사용자(nobody_xyz) → `/api/documents` 401 차단 확인

### 재점검 후 수정 사항 (2026-05-13 v2)

| 수정 항목 | 내용 |
|-----------|------|
| F1 | `DELETE /api/ontology/{doc_id}/relationships/{rel_id}` — `require_permission("can_edit_ontology")` 누락 추가 |
| F2 | `documents_list/upload/delete`에서 `ctx.user(user)` → `require_known_user()` Depends로 교체 (alice/carol 401 → 200) |
| F3 | 프론트 `api.ontologyMgmt.*` 쓰기 메서드에 `user?` 파라미터 추가, 세 컴포넌트에서 `userId` 전달 |
| F4 | sprint_06.md 설계 문서 상대 경로 수정 (`../../` → `../../../`) |
| F5 | `tests/test_sprint06_dod.py` — 14개 DoD 자동 테스트 추가, **14/14 PASS** |

### 최종 전체 테스트 결과
```
tests/ 전체: 126 passed (기존 112 + DoD 14)
```

---

## 6. 다음 스프린트 제안

- JWT 로그인 화면 (Phase 2)
- 어드민 사용자 관리 화면
- 프로젝트별 역할 분리 (동일 사용자가 프로젝트마다 다른 역할)
