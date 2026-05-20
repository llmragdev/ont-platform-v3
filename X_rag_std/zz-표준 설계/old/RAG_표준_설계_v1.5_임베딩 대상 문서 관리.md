# RAG 표준설계 - 임베딩 대상 문서 관리 (v1.5)

> **버전 이력**
>
> | 버전 | 일자 | 주요 변경 |
> |------|------|---------|
> | v1.5 | 2026-05-19 | 신규 작성 — 문서 업로드/관리 API 표준 정의 |

---

## 1. 개요

본 문서는 RAG 시스템에 임베딩할 원본 문서(PDF, DOCX, TXT)의 업로드 및 생명주기 관리를 위한 API 표준을 정의합니다.

임베딩 파이프라인의 흐름:
```
문서 업로드 (01) → 파싱/청킹 (02) → 벡터화 (03) → 저장 완료 (04)
```

각 상태 코드 정의:
- **01**: 업로드 완료 — 시스템 수신함
- **02**: 처리 중 — 파싱/청킹 진행
- **03**: 벡터화 중 — 임베딩 진행
- **04**: 저장 완료 — 검색 가능

---

## 2. 문서 메타데이터 표준

### 2.1 필수 메타데이터

모든 문서는 다음 메타데이터를 포함하여 업로드됩니다.

| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| `doc_id` | String | 필수 | 시스템 내 문서 고유 ID (자동 생성) | `doc_20260519_001` |
| `file_name` | String | 필수 | 원본 파일명 | `2026_인사규정.pdf` |
| `tenant_id` | String | 필수 | 테넌트(회사) 고유 ID | `company_abc` |
| `org_id` | String | 필수 | 조직 계층 코드 (YYMM 형식) | `0102` |
| `dept_code` | String | 필수 | 부서 코드 (org_id 앞 2자리) | `01` |
| `category_large` | String | 필수 | 대분류 카테고리 | `인사`, `규정`, `기술` |
| `category_mid` | String | 필수 | 중분류 카테고리 — 벡터 DB 라우팅 기준 | `채용`, `복리`, `교육` |
| `category_low` | String | 선택 | 소분류 카테고리 | `신입채용`, `경력채용` |
| `vector_db_id` | String | 필수 | 라우팅된 벡터 DB 식별자 | `vdb_hr_recruit_01` |
| `version` | Integer | 자동 | 문서 버전 (초판: 1, 갱신: +1) | `1`, `2` |
| `pipeline_status` | String | 필수 | 파이프라인 상태 코드 | `01`, `02`, `03`, `04` |
| `created_at` | DateTime | 자동 | 생성일시 (ISO 8601) | `2026-05-19T10:30:00Z` |
| `updated_at` | DateTime | 자동 | 최종 수정일시 (ISO 8601) | `2026-05-19T10:35:00Z` |
| `created_by` | String | 필수 | 생성자 사용자 ID | `user_abc123` |
| `updated_by` | String | 자동 | 최종 수정자 사용자 ID | `user_def456` |

### 2.2 메타데이터 설계 원칙

- **이중 축 독립**: WHAT 축(category_large → mid → low)과 WHO 축(tenant_id → org_id → dept_code)은 독립적으로 결합됩니다.
- **Vector DB 라우팅**: `category_mid` 를 기준으로 어느 벡터 DB에 저장할지 결정합니다.
  - 예: `category_mid: "채용"` → `vector_db_id: "vdb_hr_recruit_01"` (자동 매핑)
- **접근 제어**: 검색 시 `tenant_id`, `org_id`, `dept_code` 조합으로 문서 조회 권한을 제어합니다.

---

## 3. API 레이아웃

### 3.1 공통 헤더

모든 API 요청에 다음 헤더를 포함해야 합니다.

| 헤더명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `X-Tenant-ID` | String | 필수 | 테넌트(회사) 식별자 — 누락 시 400 반환 |
| `X-Org-ID` | String | 선택 | 조직 계층 코드 — 생략 시 전사 공유 문서로 간주 |
| `X-Auth-Token` | String | 필수 | 인증 토큰 — Bearer {token} 형식 |
| `Content-Type` | String | 조건 | 파일 업로드 시 `multipart/form-data` |

### 3.2 API 내역

| # | Method | Endpoint | 설명 |
|---|--------|----------|------|
| 1 | POST | `/api/v1/documents/upload` | 새 문서 업로드 |
| 2 | GET | `/api/v1/documents` | 문서 목록 조회 (페이지네이션) |
| 3 | GET | `/api/v1/documents/{doc_id}` | 문서 상태 조회 |
| 4 | PUT | `/api/v1/documents/{doc_id}` | 문서 재업로드 (버전 업데이트) |
| 5 | DELETE | `/api/v1/documents/{doc_id}` | 문서 삭제 |

---

### 3.2.1 문서 업로드

**Endpoint**: `POST /api/v1/documents/upload`  
**Content-Type**: `multipart/form-data`

#### 요청 필드

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `file` | File | 필수 | 업로드 파일 (PDF, DOCX, TXT) — 최대 50MB |
| `category_large` | String | 필수 | 대분류 카테고리 (예: `인사`, `규정`, `기술`) |
| `category_mid` | String | 필수 | 중분류 카테고리 — 벡터 DB 라우팅 기준 (예: `채용`, `복리`) |
| `category_low` | String | 선택 | 소분류 카테고리 (예: `신입채용`, `경력채용`) |
| `project_code` | String | 선택 | 프로젝트 코드 (기본값: `"000001"`) |

#### 응답 필드

| 필드명 | 타입 | 설명 |
|--------|------|------|
| `status` | String | `"success"` 또는 `"error"` |
| `data.doc_id` | String | 시스템 내 문서 고유 ID |
| `data.file_name` | String | 업로드된 파일명 |
| `data.pipeline_status` | String | 초기 상태 `"01"` (업로드 완료) |
| `data.assigned_vector_db` | String | 라우팅된 벡터 DB 식별자 |
| `data.created_at` | DateTime | 생성일시 (ISO 8601) |
| `error` | Object\|null | 오류 시 `{code, message}` |

#### 요청 예시

```bash
curl -X POST \
  -H "X-Tenant-ID: company_abc" \
  -H "X-Auth-Token: Bearer {token}" \
  -F "file=@2026_인사규정.pdf" \
  -F "category_large=인사" \
  -F "category_mid=채용" \
  -F "category_low=신입채용" \
  https://api.example.com/api/v1/documents/upload
```

#### 응답 예시

```json
{
  "status": "success",
  "data": {
    "doc_id": "doc_20260519_001",
    "file_name": "2026_인사규정.pdf",
    "pipeline_status": "01",
    "assigned_vector_db": "vdb_hr_recruit_01",
    "created_at": "2026-05-19T10:30:00Z"
  },
  "error": null
}
```

---

### 3.2.2 문서 목록 조회

**Endpoint**: `GET /api/v1/documents`  
**설명**: 조건에 맞는 문서 목록을 페이지네이션 형식으로 반환합니다.

#### 요청 필드 (Query Parameter)

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `page` | Integer | 선택 | 페이지 번호 (기본값: `1`) |
| `size` | Integer | 선택 | 페이지당 건수 (기본값: `20`, 최대: `100`) |
| `pipeline_status` | String | 선택 | 상태 필터 (`01` \| `02` \| `03` \| `04`) |
| `category_large` | String | 선택 | 대분류 필터 |
| `category_mid` | String | 선택 | 중분류 필터 |
| `sort` | String | 선택 | 정렬 기준 (기본: `created_at:desc`) |

#### 응답 필드

| 필드명 | 타입 | 설명 |
|--------|------|------|
| `status` | String | `"success"` 또는 `"error"` |
| `data.total` | Integer | 조건에 맞는 전체 문서 수 |
| `data.page` | Integer | 현재 페이지 번호 |
| `data.size` | Integer | 이 페이지의 건수 |
| `data.items[]` | Array | 문서 목록 배열 |
| `data.items[].doc_id` | String | 문서 고유 ID |
| `data.items[].file_name` | String | 파일명 |
| `data.items[].pipeline_status` | String | 파이프라인 상태 코드 |
| `data.items[].category_large` | String | 대분류 |
| `data.items[].category_mid` | String | 중분류 |
| `data.items[].version` | Integer | 문서 버전 |
| `data.items[].created_at` | DateTime | 생성일시 (ISO 8601) |
| `error` | Object\|null | 오류 시 `{code, message}` |

#### 요청 예시

```
GET /api/v1/documents?page=1&size=10&pipeline_status=04&category_large=인사
```

#### 응답 예시

```json
{
  "status": "success",
  "data": {
    "total": 25,
    "page": 1,
    "size": 10,
    "items": [
      {
        "doc_id": "doc_20260519_001",
        "file_name": "2026_인사규정.pdf",
        "pipeline_status": "04",
        "category_large": "인사",
        "category_mid": "채용",
        "version": 1,
        "created_at": "2026-05-19T10:30:00Z"
      }
    ]
  },
  "error": null
}
```

---

### 3.2.3 문서 상태 조회

**Endpoint**: `GET /api/v1/documents/{doc_id}`  
**설명**: 특정 문서의 상태와 메타데이터를 조회합니다.

#### 요청 필드 (Path Parameter)

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `doc_id` | String | 필수 | 문서 고유 ID |

#### 응답 필드

| 필드명 | 타입 | 설명 |
|--------|------|------|
| `status` | String | `"success"` 또는 `"error"` |
| `data.doc_id` | String | 문서 고유 ID |
| `data.file_name` | String | 파일명 |
| `data.pipeline_status` | String | 파이프라인 상태 코드 (`01` \| `02` \| `03` \| `04`) |
| `data.category_large` | String | 대분류 |
| `data.category_mid` | String | 중분류 |
| `data.category_low` | String | 소분류 |
| `data.org_id` | String | 조직 계층 코드 |
| `data.dept_code` | String | 부서 코드 (org_id 앞 2자리) |
| `data.vector_db_id` | String | 라우팅된 벡터 DB ID |
| `data.version` | Integer | 문서 버전 |
| `data.created_at` | DateTime | 생성일시 (ISO 8601) |
| `data.updated_at` | DateTime | 최종 수정일시 (ISO 8601) |
| `data.created_by` | String | 생성자 사용자 ID |
| `data.updated_by` | String | 최종 수정자 사용자 ID |
| `error` | Object\|null | 오류 시 `{code, message}` |

#### 요청 예시

```
GET /api/v1/documents/doc_20260519_001
```

#### 응답 예시

```json
{
  "status": "success",
  "data": {
    "doc_id": "doc_20260519_001",
    "file_name": "2026_인사규정.pdf",
    "pipeline_status": "04",
    "category_large": "인사",
    "category_mid": "채용",
    "category_low": "신입채용",
    "org_id": "0102",
    "dept_code": "01",
    "vector_db_id": "vdb_hr_recruit_01",
    "version": 1,
    "created_at": "2026-05-19T10:30:00Z",
    "updated_at": "2026-05-19T10:35:00Z",
    "created_by": "user_abc123",
    "updated_by": "user_abc123"
  },
  "error": null
}
```

---

### 3.2.4 문서 재업로드

**Endpoint**: `PUT /api/v1/documents/{doc_id}`  
**Content-Type**: `multipart/form-data`  
**설명**: 기존 문서의 파일을 교체합니다. 기존 청크는 전부 삭제 후 새 청크를 재적재합니다 (doc_id 기준).

#### 요청 필드

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `doc_id` (path) | String | 필수 | 교체할 문서의 고유 ID |
| `file` | File | 필수 | 새 파일 (PDF, DOCX, TXT) — 최대 50MB |
| `category_large` | String | 선택 | 대분류 변경 시 지정 |
| `category_mid` | String | 선택 | 중분류 변경 시 지정 |
| `category_low` | String | 선택 | 소분류 변경 시 지정 |

#### 응답 필드

| 필드명 | 타입 | 설명 |
|--------|------|------|
| `status` | String | `"success"` 또는 `"error"` |
| `data.doc_id` | String | 문서 고유 ID (기존과 동일) |
| `data.file_name` | String | 새 파일명 |
| `data.pipeline_status` | String | 재처리 시작 상태 `"02"` |
| `data.version` | Integer | 갱신된 버전 번호 |
| `data.updated_at` | DateTime | 수정일시 (ISO 8601) |
| `error` | Object\|null | 오류 시 `{code, message}` |

#### 요청 예시

```bash
curl -X PUT \
  -H "X-Tenant-ID: company_abc" \
  -H "X-Auth-Token: Bearer {token}" \
  -F "file=@2026_인사규정_v2.pdf" \
  -F "category_mid=복리" \
  https://api.example.com/api/v1/documents/doc_20260519_001
```

#### 응답 예시

```json
{
  "status": "success",
  "data": {
    "doc_id": "doc_20260519_001",
    "file_name": "2026_인사규정_v2.pdf",
    "pipeline_status": "02",
    "version": 2,
    "updated_at": "2026-05-19T11:00:00Z"
  },
  "error": null
}
```

---

### 3.2.5 문서 삭제

**Endpoint**: `DELETE /api/v1/documents/{doc_id}`  
**설명**: 문서를 삭제합니다. 해당 doc_id의 모든 청크를 벡터 DB에서 연쇄 삭제합니다.

#### 요청 필드 (Path Parameter)

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `doc_id` | String | 필수 | 삭제할 문서의 고유 ID |

#### 응답 필드

| 필드명 | 타입 | 설명 |
|--------|------|------|
| `status` | String | `"success"` 또는 `"error"` |
| `data.doc_id` | String | 삭제된 문서 고유 ID |
| `data.deleted_chunks` | Integer | 벡터 DB에서 삭제된 청크 수 |
| `error` | Object\|null | 오류 시 `{code, message}` |

#### 요청 예시

```
DELETE /api/v1/documents/doc_20260519_001
```

#### 응답 예시

```json
{
  "status": "success",
  "data": {
    "doc_id": "doc_20260519_001",
    "deleted_chunks": 42
  },
  "error": null
}
```

---

## 4. 청킹 표준

### 4.1 청킹 정책

문서가 파이프라인 상태 `02` (처리 중)에서 청킹될 때 다음 규칙을 적용합니다.

| 정책 | 설명 |
|------|------|
| **청크 크기** | 문장 단위로 분할, 약 300~500 토큰/청크 (문서 유형에 따라 조정) |
| **겹침 (Overlap)** | 인접 청크 간 50~100 토큰 겹침으로 문맥 손실 방지 |
| **메타데이터 상속** | 모든 청크는 부모 문서의 메타데이터 (tenant_id, category_large, etc.) 상속 |
| **청크 ID** | `{doc_id}#chunk{sequence_number}` 형식 (예: `doc_20260519_001#chunk0042`) |

### 4.2 벡터 DB 라우팅

`category_mid` 값에 따라 자동으로 벡터 DB를 선택합니다.

| category_mid | vector_db_id | 설명 |
|--------------|--------------|------|
| `채용` | `vdb_hr_recruit_01` | HR/채용 벡터 DB |
| `복리` | `vdb_hr_welfare_01` | HR/복리후생 벡터 DB |
| `교육` | `vdb_hr_training_01` | HR/교육 벡터 DB |
| `규정` | `vdb_compliance_01` | 컴플라이언스 벡터 DB |
| `기술` | `vdb_tech_01` | 기술 문서 벡터 DB |
| (기타) | `vdb_general_01` | 기본 벡터 DB |

---

## 5. 상태별 워크플로우

### 5.1 문서 생명주기

```
[업로드 (01)] → [처리 중 (02)] → [벡터화 (03)] → [저장 완료 (04)]
     ↓
   오류 발생 시 재시도 또는 delete 가능
```

### 5.2 각 상태의 의미

| 상태 | 코드 | 설명 | 조회 가능 | 검색 가능 |
|------|------|------|----------|----------|
| 업로드 완료 | `01` | 파일을 시스템이 수신함 | ✓ | ✗ |
| 처리 중 | `02` | 파싱/청킹 작업 진행 중 | ✓ | ✗ |
| 벡터화 중 | `03` | 청크를 임베딩 중 | ✓ | ✗ |
| 저장 완료 | `04` | 벡터 DB 저장 완료 — 검색 가능 | ✓ | ✓ |

### 5.3 비정상 워크플로우

**재시도 정책**:
- 상태 `02` 또는 `03`에서 오류 발생 시, 자동으로 재시도 (최대 3회)
- 3회 연속 실패 시 상태 `04`로 진행하지 않고 중단

**사용자 개입**:
- 중단된 문서는 PUT (재업로드) 또는 DELETE로 처리 가능
- 재업로드 시 version 번호가 +1 증가

---

## 참고

### 참고 A. HTTP 상태 코드

| HTTP 상태 | 설명 |
|-----------|------|
| `200` | 성공 (업로드, 조회 등) |
| `201` | 생성됨 (문서 업로드 시) |
| `400` | 요청 오류 (필수 헤더 누락, 필드 오류) |
| `401` | 인증 실패 |
| `403` | 권한 없음 (다른 테넌트의 문서 접근 시도) |
| `404` | 문서를 찾을 수 없음 |
| `409` | 충돌 (doc_id 중복) |
| `500` | 서버 오류 (처리 실패) |

### 참고 B. 오류 응답 형식

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "필수 필드 'category_large'가 누락되었습니다."
  }
}
```

**오류 코드**:
- `INVALID_REQUEST`: 필수 필드 누락 또는 형식 오류
- `FILE_NOT_FOUND`: 업로드된 파일을 찾을 수 없음
- `FILE_TOO_LARGE`: 파일 크기 초과 (50MB)
- `UNSUPPORTED_FORMAT`: 지원하지 않는 파일 형식
- `INVALID_CATEGORY`: 카테고리 값이 유효하지 않음
- `DOC_NOT_FOUND`: 문서를 찾을 수 없음
- `PARSING_FAILED`: 파일 파싱 실패
- `EMBEDDING_FAILED`: 임베딩 실패
- `DATABASE_ERROR`: 데이터베이스 오류

### 참고 C. 관련 문서

- [RAG 표준 기본설계서 v1.5](RAG_표준_설계_v1.5.md)
- [RAG 개발 가이드 v1.1](RAG%20개발%20가이드_v1.1.docx)

---

**작성일**: 2026-05-19  
**최종 수정일**: 2026-05-19
