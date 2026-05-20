# 04. API 명세서 (Detailed API Specification)

## 1. 공통 규격 (Standard Spec)
- **Base URL**: `/api/v1`
- **Auth**: `Authorization: Bearer <JWT>`
- **Pagination**: `?page=1&size=20` (List API 공통)

---

## 2. 테넌트 및 권한 API (Tenant & Permissions)

### 2.1 내 정보 및 권한 조회
- **GET `/tenant/me`**: 현재 토큰의 사용자, 회사, 프로젝트 정보 및 상세 권한 플래그 반환.
- **GET `/tenant/projects`**: 사용자가 접근 가능한 프로젝트 목록.

---

## 3. 온톨로지 관리 API (Ontology)

### 3.1 엔티티(Entity) 관리
- **GET `/ontology/entities`**: 테넌트 내 엔티티 목록 (필터: `type`, `project_id`, `q`).
- **POST `/ontology/entities`**: 신규 엔티티 생성.
- **GET `/ontology/entities/{id}`**: 상세 조회 (1-hop 관계 포함).
- **PUT `/ontology/entities/{id}`**: 속성 수정.
- **DELETE `/ontology/entities/{id}`**: 삭제 (Status를 `deleted`로 변경).

### 3.2 관계(Relationship) 관리
- **POST `/ontology/relationships`**: 엔티티 간 관계 생성.
- **DELETE `/ontology/relationships/{id}`**: 관계 삭제.

---

## 4. 문서 및 지식 추출 API (Documents)

### 4.1 문서 관리
- **GET `/documents`**: 업로드된 문서 목록 및 상태.
- **POST `/documents/upload`**: PDF 업로드 (Multipart).
- **DELETE `/documents/{id}`**: 문서 및 관련 벡터 데이터 삭제.

### 4.2 추출 후보 관리
- **GET `/ingestion/candidates`**: AI가 추출한 온톨로지 후보 목록.
- **POST `/ingestion/confirm`**: 후보 승인 및 실제 온톨로지 반영.

---

## 5. 하이브리드 질의 API (Hybrid Query)

### 5.1 질의 실행 계획 및 응답
- **POST `/query/plan`**: 질문에 대한 실행 계획(Plan)만 미리 확인.
- **POST `/query/ask`**: 실행 계획 수립 및 엔진 실행 후 답변 생성 (Streaming).

---

## 6. 감사 및 관측 API (Audit & Ops)

### 6.1 감사 로그
- **GET `/audit/logs`**: 시스템 변경 이력 조회.
- **GET `/audit/logs/{id}`**: 변경 전/후(Before/After) 상세 Diff 확인.

---

## 7. 상세 응답 예시 (Error Examples)

| 상태 코드 | 에러 코드 | 메시지 |
| :--- | :--- | :--- |
| **401** | `TOKEN_EXPIRED` | "인증 세션이 만료되었습니다. 다시 로그인해주세요." |
| **403** | `INSUFFICIENT_PERMISSION` | "요청하신 작업을 수행할 권한이 없습니다." |
| **422** | `SCHEMA_VALIDATION_FAILED` | "입력 데이터가 온톨로지 스키마 정의와 일치하지 않습니다." |
