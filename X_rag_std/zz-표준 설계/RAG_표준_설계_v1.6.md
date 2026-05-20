# 엔터프라이즈 RAG 표준 기본설계서 (v1.6)

> **버전 이력**
>
> | 버전 | 일자 | 주요 변경 |
> |------|------|---------|
> | v1.0 | 2026-05-14 | 초안 작성 |
> | v1.1 | 2026-05-14 | `company_id` 메타데이터 필수화 · X-Company-ID 헤더 표준 신설 · 임베딩 Fallback 금지 |
> | v1.2 | 2026-05-14 | `company_id` → `tenant_id` 전면 교체 · `org_id` 계층 코드 신설 · Index Swap 운영 패턴 추가 |
> | v1.3 | 2026-05-15 | X-Tenant-ID 필수화 · OR 조건 검색 정책 · RDBMS 복합키 설계 |
> | v1.4 | 2026-05-15 | API 레이아웃 전면 추가 · `category_large` 대분류 추가 · 이중 축 독립 원칙 신설 |
> | v1.5 | 2026-05-15 | **섹션 구조 재편** — RAG 기반 검색을 §2 첫 번째 기능 섹션으로 배치 · 9개 중분류 기준으로 통합 재구성 · Agent/Orchestration 섹션 신설(보류) |
> | v1.6 | 2026-05-19 | **포지셔닝 변경** — v1.1.docx를 기본 개발 가이드로 positioning · 본 문서는 다음 단계 상세 설계 및 참고용 · 테스트 데이터 정의 추가 예정 |

---

## 1. 개요 및 설계 원칙

본 문서는 엔터프라이즈 환경에서 안정적이고 유연하게 동작할 수 있는 RAG(Retrieval-Augmented Generation) 시스템의 표준 설계 기준을 정의합니다.

### 1.1 핵심 아키텍처 원칙

* **물리적 분리 (MSA 기반)**: LLM 추론 서버와 Vector DB 영역은 물리적으로 분리될 수 있어야 합니다. REST API 또는 gRPC를 통한 `Remote Retriever` 패턴을 활용하여 느슨한 결합(Loosely Coupled) 구조를 지향합니다.
* **멀티테넌트 격리 (Strict Isolation)**: 모든 데이터 저장·검색 경로에서 `tenant_id`를 기준으로 회사 단위 격리를 강제합니다. 헤더 누락 시 `"default"` 처리를 **금지**하고 명시적 오류(400)를 반환합니다.
* **계층적 지식 공유 (Hierarchical Knowledge)**: `org_id`를 통해 부서/팀 단위 미세 권한 제어 및 전사 공유 지식 조회를 지원합니다.
* **이중 축 독립 원칙 (Dual-Axis Independence)**: 문서 분류와 접근 통제는 **서로 독립된 두 개의 축**으로 설계합니다.
  * **WHAT 축 (지식 분류)**: `category_large → category_mid → category_low` — 벡터 DB 라우팅 기준
  * **WHO 축 (접근 통제)**: `tenant_id → org_id → dept_code` — 검색 필터 기준
  * 두 축은 독립적으로 결합됩니다. 예: "01팀이 볼 수 있는 인사/채용 문서" = WHO 필터 + WHAT 필터 동시 적용
* **표준 코딩 컨벤션**: 파이썬 PEP 8 규약(snake_case 함수/변수, PascalCase 클래스)을 준수합니다.

---

## 2. RAG 기반 검색

사용자 질의를 벡터 유사도로 검색하고 LLM이 답변을 생성하는 핵심 인터페이스를 정의합니다.

### 2.1 과업 목록

| # | 과업 | Endpoint |
|---|------|----------|
| 1 | 일반 RAG 검색 (동기) | `POST /api/v1/rag/search` |
| 2 | SSE 스트리밍 검색 | `POST /api/v1/rag/search/stream` |
| 3 | 검색 이력 목록 조회 | `GET  /api/v1/rag/history` |
| 4 | 검색 이력 상세 조회 | `GET  /api/v1/rag/history/{history_id}` |

**헤더**: `X-Tenant-ID` (필수, 누락 시 400), `X-Org-ID` (선택)

### 2.2 검색 요청 / 응답

**검색 요청** (`POST /api/v1/rag/search`)

```json
{
  "query": "2026년 인사 규정 알려줘",
  "top_k": 5,
  "debug_mode": true,
  "filters": {
    "category_large": "인사",
    "category_mid": "채용",
    "vector_db_id": "vdb_hr_recruit_01"
  }
}
```

**검색 응답**

```json
{
  "status": "success",
  "data": {
    "query": "2026년 인사 규정 알려줘",
    "answer": "2026년 인사 규정에 따르면...",
    "used_chunks": [
      {
        "chunk_id": "doc_a1b2c3d4#chunk4",
        "content": "LLM이 정답 생성에 채택한 텍스트...",
        "metadata": {
          "source_name": "2026_인사규정.pdf",
          "source_url": "https://storage.example.com/docs/2026_인사규정.pdf",
          "page_no": 12,
          "category_large": "인사",
          "category_mid": "채용",
          "vector_db_id": "vdb_hr_recruit_01",
          "tenant_id": "company_abc",
          "org_id": "0102",
          "dept_code": "01"
        },
        "similarity_score": 0.89
      }
    ],
    "debug_info": {
      "execution_time_ms": 145,
      "candidate_chunks": ["// debug_mode: true 시에만 노출 — 미채택 청크 포함"]
    }
  },
  "error": null
}
```

### 2.3 SSE 스트리밍 검색

* **Endpoint**: `POST /api/v1/rag/search/stream`
* **Response**: `Content-Type: text/event-stream`

```
data: {"token": "2026년"}
data: {"token": " 인사"}
data: {"token": " 규정에"}
...
data: {"done": true, "used_chunks": [...]}
```

### 2.4 검색 이력 조회

**이력 목록** (`GET /api/v1/rag/history?page=1&size=20`)

```json
{
  "status": "success",
  "data": {
    "total": 142,
    "items": [
      {
        "history_id": 87,
        "query": "2026년 인사 규정 알려줘",
        "answer_preview": "2026년 인사 규정에 따르면...",
        "org_id": "0102",
        "created_at": "2026-05-15T09:12:33+00:00"
      }
    ]
  },
  "error": null
}
```

**이력 상세** (`GET /api/v1/rag/history/{history_id}`)

```json
{
  "status": "success",
  "data": {
    "history_id": 87,
    "query": "2026년 인사 규정 알려줘",
    "answer": "2026년 인사 규정에 따르면...",
    "used_chunks": ["// §2.2 응답 레이아웃과 동일 구조"],
    "created_at": "2026-05-15T09:12:33+00:00"
  },
  "error": null
}
```

---

## 3. 임베딩 대상 문서 관리

원천 데이터가 임베딩되어 Vector DB에 저장되기까지의 생명 주기를 체계적으로 관리합니다.

### 3.1 처리 원칙

* **데이터 보관소 분리**: 원본 문서(Raw Document)와 파싱/청킹된 중간 텍스트(Processed Data)의 물리적 보관소를 분리합니다.
* **상태 전이**:
  ```
  01(업로드) → 02(처리중) → 03(완료)
                          ↘ 04(오류)
  ```
* **증분 업데이트**: 원본 문서가 갱신될 경우 `doc_id` 기준 기존 청크를 전부 삭제하고 새 청크를 재적재합니다.
* **비동기 처리**: 업로드 API는 `asyncio.create_task(asyncio.to_thread(...))` 패턴으로 파이프라인을 백그라운드 실행하고 즉시 `"01"` 반환합니다.

### 3.2 Pipeline Status 코드

| 코드 | 상태명 | 설명 |
|------|--------|------|
| `01` | 업로드 완료 | 파일 저장 완료, 처리 미시작 |
| `02` | 처리중 | 파싱 → 청킹 → 임베딩 → 저장 진행 중 |
| `03` | 완료 | 벡터 DB 저장 완료, 검색 가능 |
| `04` | 오류 | 처리 중 오류 발생 (상세는 error_code 참조) |

> **상세 상태 분류** (파싱중/청킹중/임베딩중/저장중)는 **상세설계_2.0**에서 정의합니다.

### 3.3 API 레이아웃

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/api/v1/documents/upload` | 문서 업로드 및 파이프라인 시작 |
| `GET` | `/api/v1/documents` | 문서 목록 조회 |
| `GET` | `/api/v1/documents/{doc_id}` | 문서 상태 조회 (pipeline_status 폴링) |
| `PUT` | `/api/v1/documents/{doc_id}` | 문서 재업로드 (버전 갱신) |
| `DELETE` | `/api/v1/documents/{doc_id}` | 문서 삭제 (벡터 포함) |

**헤더**: `X-Tenant-ID` (필수, 누락 시 400 반환), `X-Org-ID` (선택)

**업로드 요청** (`POST /api/v1/documents/upload`, `multipart/form-data`)

```
file            : 업로드 파일 (PDF, DOCX, TXT)
category_large  : 대분류 카테고리 (필수) — 예: 인사, 규정, 기술
category_mid    : 중분류 카테고리 (필수) — 벡터 DB 라우팅 기준
category_low    : 소분류 카테고리 (선택)
project_code    : 프로젝트 코드 (선택, 기본값 "000001")
```

**업로드 응답**

```json
{
  "status": "success",
  "data": {
    "doc_id": "doc_a1b2c3d4",
    "file_name": "2026_인사규정.pdf",
    "pipeline_status": "01",
    "assigned_vector_db": "vdb_hr_recruit_01"
  },
  "error": null
}
```

**상태 조회 응답** (`GET /api/v1/documents/{doc_id}`)

```json
{
  "status": "success",
  "data": {
    "doc_id": "doc_a1b2c3d4",
    "file_name": "2026_인사규정.pdf",
    "pipeline_status": "03",
    "org_id": "0102",
    "dept_code": "01",
    "version": 1,
    "created_at": "2026-05-15T09:00:00+00:00",
    "updated_at": "2026-05-15T09:00:45+00:00"
  },
  "error": null
}
```

### 3.3 청킹 표준

| 항목 | 값 |
|------|-----|
| chunk_size | 700자 |
| chunk_overlap | 80자 |
| 분리 방식 | 슬라이딩 윈도우 (RecursiveCharacterTextSplitter 유사) |
| page_no | 실제 PDF 페이지 번호 (chunk 인덱스 사용 금지) |

---

## 4. 벡터 DB 관리

### 4.1 물리적 분리 원칙

* 단일 거대 벡터 DB 운영을 지양하고 업무(카테고리) 또는 테넌트 단위로 독립된 `vector_db_id`를 발급하여 라우팅합니다.
* **임베딩 모델별 컬렉션 분리**: 모델(OpenAI, Gemini, Solar 등)마다 벡터 차원이 다르므로 단일 컬렉션에 혼재하지 않습니다.
* **임베딩 일관성 원칙**: 저장 시와 쿼리 시 반드시 동일한 임베딩 서비스를 사용합니다. 저장 단계에서 임베딩을 생성하여 `embeddings=` 파라미터로 명시 전달합니다 (adapter 내부 호출 금지).

### 4.2 엔진 이원화

| 엔진 | 사용 시점 |
|------|---------|
| **ChromaDB / Qdrant** | 영구 지식 베이스, 풍부한 메타데이터 필터링 |
| **FAISS** | 세션 기반 휘발성 컨텍스트, 초고속 단순 유사도 검색 |

### 4.3 Routing Registry

라우팅 기준은 `category_mid`(중분류)이며, `category_large`(대분류)는 벡터 DB를 논리적으로 그룹핑하는 상위 단위입니다.

```json
[
  { "category_large": "인사", "category_mid": "채용",    "vector_db_id": "vdb_hr_recruit_01" },
  { "category_large": "인사", "category_mid": "급여",    "vector_db_id": "vdb_hr_payroll_01" },
  { "category_large": "규정", "category_mid": "취업규칙", "vector_db_id": "vdb_policy_01"    },
  { "category_large": "기술", "category_mid": "ontology", "vector_db_id": "vdb_ontology_01" }
]
```

### 4.4 Admin API

| Method | Endpoint | 설명 |
|--------|----------|------|
| `GET`  | `/api/v1/admin/vector-dbs` | 등록된 벡터 DB 목록 조회 |
| `POST` | `/api/v1/admin/index-swap` | Index Swap 실행 요청 |
| `GET`  | `/api/v1/admin/index-swap/{job_id}` | 스왑 진행 상태 조회 |

**벡터 DB 목록 응답**

```json
{
  "status": "success",
  "data": [
    {
      "vector_db_id": "vdb_policy_01",
      "engine": "chroma",
      "collection_name": "policy_v2",
      "category_large": "규정",
      "category_mid": "취업규칙",
      "doc_count": 1240
    }
  ],
  "error": null
}
```

**Index Swap 요청 / 상태 응답**

```json
// 요청 (POST /api/v1/admin/index-swap)
{ "vector_db_id": "vdb_policy_01", "new_collection_name": "policy_v3" }

// 상태 응답 (GET /api/v1/admin/index-swap/{job_id})
{
  "status": "success",
  "data": {
    "job_id": "swap_20260515_001",
    "vector_db_id": "vdb_policy_01",
    "swap_status": "in_progress",
    "progress_pct": 67,
    "started_at": "2026-05-15T02:00:00+00:00",
    "estimated_done_at": "2026-05-15T02:30:00+00:00"
  },
  "error": null
}
```

### 4.5 Index Swap 패턴

조직 개편 시 벡터 메타데이터를 건별 수정하는 대신 **원자적 컬렉션 교체** 패턴을 사용합니다.

```
1. 신규 컬렉션 백그라운드 재색인 (구 컬렉션 서비스 유지)
2. 재색인 완료 후 routing.json의 collection_name만 교체
3. 구 컬렉션 삭제 (롤백 기간 경과 후)
```

| 방식 | 특징 |
|------|------|
| 건별 metadata update | 부분 실패 위험, 서비스 중 불일치 상태 존재 |
| **Index Swap (권장)** | 원자적 전환, 무중단, 롤백 용이 |

---

## 5. 벡터DB의 임베딩별 문서 매칭관리

문서↔벡터 청크 간 연결 유지 규칙을 정의합니다. 세부 구현은 각 참조 섹션에서 정의합니다.

### 5.1 핵심 매칭 규칙

| 규칙 | 내용 |
|------|------|
| **chunk_id 명명** | `{doc_id}#chunk{순번}` 자동 생성 (예: `doc_a1b2c3d4#chunk0`) |
| **라우팅** | `category_mid` → `vector_db_id` 매핑으로 저장 벡터DB 결정 (§4.3 Routing Registry) |
| **연쇄 삭제** | 문서 삭제 시 `doc_id`의 모든 청크를 벡터DB에서 함께 삭제 |
| **임베딩 경계** | 임베딩 생성은 파이프라인 책임, adapter는 `embeddings=` 파라미터로 수신만 함 |
| **org_id OR 검색** | 검색 시 `org_id == "{org_id}" OR org_id == ""` (전사 공유 문서 자동 포함) |

#### OR 조건 검색 정책

| 레벨 | 헤더 | 벡터 DB 필터 |
|------|------|------------|
| 전사 검색 | `X-Tenant-ID` | `tenant_id == "abc"` |
| 부서 검색 | `X-Tenant-ID` + `X-Org-ID: 0100` | `tenant_id == "abc"` AND (`dept_code == "01"` OR `org_id == ""`) |
| 팀 검색 | `X-Tenant-ID` + `X-Org-ID: 0102` | `tenant_id == "abc"` AND (`org_id == "0102"` OR `org_id == ""`) |

> ChromaDB는 `None` 메타데이터를 지원하지 않으므로 전사 공유 문서는 `org_id = ""`(빈 문자열 sentinel)로 저장합니다.

```python
def build_chunk_metadata(tenant_id: str, org_id: str | None, ...) -> dict:
    return {
        "tenant_id": tenant_id,
        "org_id": org_id or "",          # None → "" sentinel
        "dept_code": org_id[:2] if org_id else "",  # 자동 파생
        # ...
    }
```

### 5.2 청크 출처 추적 (Grounding)

답변의 신뢰성(Grounding)을 확보하기 위해 검색된 벡터가 어느 원문의 몇 페이지에서 왔는지 추적합니다.  
응답 레이아웃은 §2.2 `used_chunks` 항목 구조를 따릅니다.

**참조 섹션**

- 검색 API 및 used_chunks 응답 → §2 RAG 기반 검색
- 라우팅 규칙 (category_mid → vector_db_id) → §4.3 Routing Registry
- 구현 소스 → `src_claud/v3/app/services/vector_db/`, `src_claud/v3/app/services/document_service.py`

---

## 6. 메타데이터 관리

### 6.1 이중 축 원칙

> - **WHO 축 (접근 통제)**: `tenant_id`, `org_id`, `dept_code`
> - **WHAT 축 (지식 분류)**: `category_large`, `category_mid`, `category_low`

### 6.2 표준 메타데이터 매트릭스

| 속성명 | 축 | 타입 | 필수 | 설명 |
| :--- | :---: | :--- | :--- | :--- |
| `doc_id` | — | String | 필수 | 시스템 내 원본 문서 고유 ID |
| `tenant_id` | WHO | String | 필수 | 회사 단위 테넌트 구분자 — 검색 필터 강제 적용 |
| `org_id` | WHO | String | 선택 | 조직 계층 코드 (`{DD}{TT}`). 빈값(`""`) = 전사 공유 |
| `dept_code` | WHO | String | 조건부 | `org_id` 존재 시 필수. `org_id` 앞 2자리 파생값 |
| `category_large` | WHAT | String | 필수 | 대분류 (예: 인사, 규정, 기술). 벡터 DB 그룹핑 단위 |
| `category_mid` | WHAT | String | 필수 | 중분류. **벡터 DB 라우팅 기준** |
| `category_low` | WHAT | String | 선택 | 소분류 (예: 공고, 계약) |
| `source_url` | — | String | 필수 | 원본 파일 다운로드 또는 열람 경로 |
| `vector_db_id` | — | String | 필수 | 문서가 저장된 물리적 벡터 DB 식별자 |
| `page_no` | — | Integer | 권장 | 실제 PDF 페이지 번호 (chunk 순번 아님) |
| `chunk_type` | — | String | 선택 | `text`, `table`, `image_desc` |
| `created_at` | — | DateTime | 필수 | timezone-aware ISO 8601 |
| `tags` | — | Array[String] | 선택 | RDBMS/JSON 전용. **Vector DB metadata 저장 금지** |

#### org_id 코드 체계

```
형식: {DD}{TT}  — DD: 부서(2자리), TT: 팀(2자리)
예:  0100 → 01부서 전체  /  0102 → 01부서 02팀  /  0200 → 02부서 전체
확장: {DD}{TT}{PP} — 파트 2자리 추가 시 6자리, 최대 8자리
규칙: zero-padding 필수 (01 O, 1 X)
저장: org_id = "0102"  →  dept_code = "01" (앞 2자리 자동 파생, 수동 입력 금지)
```

### 6.3 프로젝트·카테고리 관리 API

| # | 과업 | Endpoint |
|---|------|----------|
| 1 | 프로젝트 생성 | `POST   /api/v1/meta/projects` |
| 2 | 프로젝트 목록 조회 | `GET    /api/v1/meta/projects` |
| 3 | 프로젝트 상세 조회 | `GET    /api/v1/meta/projects/{project_code}` |
| 4 | 프로젝트 삭제 | `DELETE /api/v1/meta/projects/{project_code}` |
| 5 | 카테고리 생성 | `POST   /api/v1/meta/categories` |
| 6 | 카테고리 목록 조회 | `GET    /api/v1/meta/categories` |
| 7 | 카테고리 삭제 | `DELETE /api/v1/meta/categories/{category_id}` |

**헤더**: `X-Tenant-ID` (필수) — 전 과업 공통

**프로젝트 생성 요청/응답** (`POST /api/v1/meta/projects`)

```json
// 요청
{ "project_code": "PROJ01", "project_name": "2026 인사제도 지식베이스", "vector_db_id": "vdb_hr_01" }

// 응답
{
  "status": "success",
  "data": {
    "tenant_id": "company_abc",
    "project_code": "PROJ01",
    "project_name": "2026 인사제도 지식베이스",
    "vector_db_id": "vdb_hr_01",
    "created_at": "2026-05-15T09:00:00+00:00"
  },
  "error": null
}
```

**카테고리 생성 요청** (`POST /api/v1/meta/categories`)

```json
{ "category_large": "인사", "category_mid": "채용", "category_low": "공고", "vector_db_id": "vdb_hr_recruit_01" }
```

**카테고리 목록 응답** (`GET /api/v1/meta/categories`)

```json
{
  "status": "success",
  "data": [
    {
      "category_id": 1,
      "tenant_id": "company_abc",
      "category_large": "인사",
      "category_mid": "채용",
      "category_low": "공고",
      "vector_db_id": "vdb_hr_recruit_01"
    },
    {
      "category_id": 2,
      "tenant_id": "company_abc",
      "category_large": "규정",
      "category_mid": "취업규칙",
      "category_low": null,
      "vector_db_id": "vdb_policy_01"
    }
  ],
  "error": null
}
```

### 6.4 RDBMS 테이블 설계

**`wc_project`** — PK: `(tenant_id, project_code)`

**`wc_category`** — PK: `category_id` (SERIAL), UK: `(tenant_id, category_large, category_mid, category_low)`

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|:----:|------|
| `category_id` | SERIAL | PK | 자동 증가 식별자 |
| `tenant_id` | VARCHAR(50) | ✅ | 테넌트 구분자 |
| `category_large` | VARCHAR(50) | ✅ | 대분류 — Routing Registry 그룹핑 기준 |
| `category_mid` | VARCHAR(50) | ✅ | 중분류 — **벡터 DB 라우팅 기준** |
| `category_low` | VARCHAR(50) | — | 소분류 (선택) |
| `vector_db_id` | VARCHAR(50) | ✅ | 할당된 벡터 DB 식별자 |
| `created_at` | TIMESTAMPTZ | ✅ | `datetime.now(timezone.utc)` |

---

## 7. 접근 권한 관리 (보류)

> **상태**: 테넌트/조직 단위 격리는 §3·§5에서 구현 완료. 역할 기반 접근 제어(RBAC)·행 수준 보안(RLS) 등 세부 권한 정책은 **설계 보류**.

### 7.1 현재 구현 요약

| 항목 | 적용 위치 | 상태 |
|------|----------|:----:|
| X-Tenant-ID 필수 검증 (누락 시 400) | 전 API 엔드포인트 | ✅ |
| X-Org-ID 선택 수신 | 전 API 엔드포인트 | ✅ |
| org_id 기반 격리 + OR 검색 | §5.1 검색 필터 | ✅ |
| 역할 기반 접근 제어 (RBAC) | — | 🔲 보류 |
| 행 수준 보안 (RLS) | — | 🔲 보류 |
| API 키 / OAuth 토큰 관리 | — | 🔲 보류 |

### 7.2 헤더 검증 구현 규칙

```python
from fastapi import Header, HTTPException

def get_tenant_id(x_tenant_id: str | None = Header(default=None)) -> str:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is required")
    return x_tenant_id

def get_org_id(x_org_id: str | None = Header(default=None)) -> str | None:
    return x_org_id   # None = 전사 범위 검색
```

---

## 8. 오류/예외 결과

### 8.1 표준 예외 코드

| 예외 코드 | 발생 조건 |
|---------|---------|
| `document_parsing_error` | 파일 로드 및 파싱 실패 |
| `embedding_api_timeout` | 임베딩 모델 호출 시간 초과 |
| `vector_db_connection_error` | 물리적으로 분리된 Vector DB 연결 실패 |

### 8.2 오류 응답 포맷

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "embedding_api_timeout",
    "message": "임베딩 API 호출이 시간 초과되었습니다."
  }
}
```

### 8.3 임베딩 Fallback 금지

임베딩 API 호출 실패 시 더미 벡터(`[0.1, 0.2]` 등) 반환 또는 조용한 무시를 **금지**합니다.  
반드시 `embedding_api_timeout` 예외를 전파하여 파이프라인을 `error` 상태로 전환합니다.

---

## 9. Agent/Orchestration 요청 (보류)

> **상태**: 설계 보류. 하기 항목은 향후 확장 방향으로만 정의하며 구현 표준은 미확정입니다.

### 9.1 확장 방향

| 항목 | 설명 |
|------|------|
| Multi-Agent RAG | 복수 에이전트가 동일 벡터DB를 쿼리하는 Orchestration 표준 |
| Tool-calling 인터페이스 | LLM Tool Use / Function Calling 기반 검색 트리거 |
| RAG-as-Tool | 외부 에이전트가 RAG 검색 파이프라인을 도구로 호출하는 API 스펙 |
| 응답 스트리밍 표준화 | 에이전트 ↔ RAG 서버 간 SSE / WebSocket 프로토콜 표준 |
| 컨텍스트 누적 관리 | 멀티턴 대화에서 이전 used_chunks를 다음 쿼리에 전달하는 표준 |

### 9.2 예상 API 스켈레톤 (미확정)

```json
// POST /api/v1/agent/query  (스펙 미확정)
{
  "agent_id": "agent_001",
  "query": "2026년 인사 규정 검색",
  "context": {
    "session_id": "sess_abc",
    "turn": 3,
    "prior_chunks": ["// 이전 턴의 used_chunks — 선택적 전달"]
  },
  "rag_options": {
    "top_k": 5,
    "filters": { "category_large": "인사" }
  }
}
```

---

## 부록. RDBMS 공통 설계 지침

### A.1 복합 기본키 설계

| 테이블 | PK | 비고 |
|--------|-----|------|
| `ca_org_mgnt` | `(tenant_id, org_id)` | 조직 마스터 |
| `wc_project` | `(tenant_id, project_code)` | 프로젝트 마스터 |
| `wc_project_rag_doc` | `doc_id` (UUID) | FK → `(tenant_id, project_code)` |
| `wc_category` | `category_id` (SERIAL) | UK: `(tenant_id, category_large, category_mid, category_low)` |

### A.2 datetime 표준

모든 `created_at`, `updated_at` 컬럼은 **timezone-aware** datetime을 사용합니다.

```python
from datetime import datetime, timezone

# 올바른 방법
default=lambda: datetime.now(timezone.utc)

# 금지 (Python 3.12+ deprecated, 3.14 제거 예정)
default=datetime.utcnow
```
