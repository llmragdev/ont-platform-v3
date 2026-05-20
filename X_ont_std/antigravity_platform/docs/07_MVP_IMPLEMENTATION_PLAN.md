# 07. MVP 구현 계획서 (MVP Implementation Plan)

## 1. 개요
본 문서는 `Antigravity-통합` 프로젝트의 추상적 설계를 구체적인 구현 단계로 나누어, 리스크를 최소화하고 작동하는 시스템을 빠르게 구축하기 위한 로드맵을 정의합니다.

---

## 2. 단계별 구현 상세 (Phased Roadmap)

### Phase 1: 통합 인증 및 테넌트 컨텍스트 (Foundation & Identity)
- **목표**: 기존 사용자 체계를 폐기하고, JWT 기반의 단일 테넌트 사용자 모델(`Unified Identity`) 구축.
- **핵심 구현 항목**:
    - `backend/app/core/identity.py`: `User + Tenant + Role` 통합 모델 정의.
    - `backend/app/api/middleware.py`: JWT 해석 및 `IdentityContext` 주입.
- **자동화 테스트 목록**:
    - [ ] **TC-SEC-01**: 토큰 없음 → 401
    - [ ] **TC-SEC-02**: 만료 토큰 → 401
    - [ ] **TC-SEC-03**: 타 프로젝트 접근 → 403
    - [ ] **TC-SEC-06**: `request.state.identity` 존재 확인
- **완료 기준**: JWT 토큰 정보와 API 처리 테넌트 정보가 100% 일치함이 자동 테스트로 증명됨.

### Phase 2: 테넌트 보안 강화 및 범용 데이터 (Security Lockdown)
- **목표**: 모든 CRUD API에 권한 필터를 적용하고 데이터 레벨 격리 완료.
- **핵심 구현 항목**:
    - `backend/app/repositories/base.py`: 모든 쿼리에 `company_id` 필터 강제.
    - `backend/app/api/v1/ontology.py`: 수정/삭제 API 포함 전수 권한 적용.
- **자동화 테스트 목록**:
    - [ ] **TC-SEC-04**: `viewer`가 엔티티 생성 시도 → 403
    - [ ] **TC-SEC-05**: `editor`가 엔티티 생성 → 201
    - [ ] **TC-ONT-03**: 엔티티 삭제 시 관계 상태 변경 확인
- **완료 기준**: `DELETE` API 포함 모든 엔드포인트에 권한/테넌트 위반 케이스 403 반환 확인.

### Phase 3: 문서 처리 및 벡터 엔진 (RAG Base)
- **목표**: PDF 업로드부터 벡터 검색까지의 격리된 파이프라인.
- **핵심 구현 항목**:
    - `backend/app/services/ingestion.py`: PDF 파싱 및 청킹.
    - `backend/app/services/vector.py`: 테넌트별 벡터 인덱스 관리.
- **완료 기준**: 업로드한 문서가 본인 테넌트 검색 결과에서만 노출됨.

### Phase 4: 하이브리드 질의 엔진 (Intelligence)
- **목표**: Query Planner와 Executor의 연동.
- **핵심 구현 항목**:
    - `backend/app/services/planner.py`: LLM 기반 구조형 계획 생성 (Strict JSON).
    - `backend/app/services/executor.py`: 계획 파싱 및 온톨로지/벡터 엔진 실행.
- **완료 기준**: "에러 장비 목록을 찾아줘"라는 질문에 대해 온톨로지 필터 쿼리가 실행됨.

---

## 3. 구현 원칙 (Implementation Principles)

1.  **No Isolation Leak**: 모든 API는 반드시 `TenantContext`를 의존성으로 받으며, 데이터 접근 시 이를 생략할 수 없음.
2.  **Schema First**: 백엔드 모델 변경 시 항상 `05_DATABASE_AND_DATA_SCHEMA.md`를 선행 업데이트.
3.  **Automated Verification**: 각 Phase 종료 시 `pytest`로 권한 위반 시나리오(Cross-tenant access) 테스트 수행 필수.

---

## 4. Phase 1 상세 할당 (Next Step)

| Task ID | 작업 내용 | 담당 | 완료 기준 |
| :--- | :--- | :--- | :--- |
| T1-01 | JWT 기반 Tenant Middleware 구현 | Antigravity | 모든 API 요청에서 `request.state.tenant` 접근 가능 |
| T1-02 | RBAC 권한 체크 데코레이터 구현 | Antigravity | `@require_permission("ontology:edit")` 적용 시 권한 미달 사용자 403 반환 |
| T1-03 | 테넌트 격리형 Base Repository 구현 | Antigravity | 물리적 경로(`storage/{tid}/`) 기반 파일 접근 추상화 |
