# 엔터프라이즈 RAG 개발 가이드 (v1.5)


## 1. 개요 및 설계 원칙

본 문서는 엔터프라이즈 환경에서 안정적이고 유연하게 동작할 수 있는 RAG(Retrieval-Augmented Generation) 시스템을 개발하기 위한 설계 원칙과 구현 지침을 정의합니다.

**본 가이드의 적용 범위**

| 영역 | 포함 여부 | 비고 |
|------|:--------:|------|
| RAG 기반 검색 | ✅ | 벡터 유사도 검색 및 LLM 답변 생성 API |
| 임베딩 대상 문서 관리 | ✅ | 문서 업로드·상태 관리·청킹 표준 |
| 벡터 DB 관리 | ✅ | 엔진 선택·카테고리 매핑·관리자 API |
| 벡터DB 임베딩별 문서 매칭 관리 | ✅ | 청크 연결 규칙·출처 추적(Grounding) |
| 메타데이터 관리 | ✅ | 표준 메타데이터 속성·프로젝트·카테고리 API |
| 접근 권한 관리 | 🔲 보류 | 기본 격리 원칙만 정의, RBAC·RLS 설계 제외 |
| 오류/예외 결과 | ✅ | 표준 에러 코드 체계·응답 포맷 |
| Agent/Orchestration 요청 | 🔲 보류 | Multi-Agent RAG·Tool-calling 설계 제외 |

### 1.1 핵심 아키텍처 원칙

* **물리적 분리 (MSA 기반)**: LLM 추론 서버와 Vector DB 영역은 물리적으로 분리될 수 있어야 합니다. REST API 또는 gRPC를 통한 `Remote Retriever` 패턴을 활용하여 느슨한 결합(Loosely Coupled) 구조를 지향합니다.
* **멀티테넌트 격리 (Strict Isolation)**: 모든 데이터 저장·검색 경로에서 `tenant_id`를 기준으로 격리를 강제합니다. 물리적·논리적 격리 모두 접근 제어가 가능하나, 요구사항에 따라 완전한 물리적 단절이 필요한 경우(계열사·사업부 분리 등) 별도 `tenant_id`로 구성합니다. 헤더 누락 시 `"default"` 처리를 **금지**하고 명시적 오류(400)를 반환합니다.
* **계층적 지식 공유 (Hierarchical Knowledge)**: `org_id`를 통해 부서/팀 단위 미세 권한 제어 및 전사 공유 지식 조회를 지원합니다.
* **이중 축 독립 원칙 (Dual-Axis Independence)**: 문서 분류와 접근 통제는 **서로 독립된 두 개의 축**으로 설계합니다.
  * **WHAT 축 (지식 분류)**: `category_large → category_mid → category_low` — 벡터 DB 라우팅 기준
  * **WHO 축 (접근 통제)**: `tenant_id → org_id → dept_code` — 검색 필터 기준
  * 두 축은 독립적으로 결합됩니다. 예: "01팀이 볼 수 있는 인사/채용 문서" = WHO 필터 + WHAT 필터 동시 적용
* **표준 코딩 컨벤션**: 파이썬 [PEP 8](https://peps.python.org/pep-0008/) 규약을 기본으로 권장합니다. PEP 8은 파이썬 공식 스타일 가이드로, 함수·변수는 단어를 밑줄(`_`)로 연결하는 `snake_case`, 클래스는 각 단어의 첫 글자를 대문자로 쓰는 `PascalCase`를 사용합니다. 자바(Java) 개발 사상에 익숙한 경우 함수·변수에 `camelCase`를 적용하기도 하나, 파이썬 프로젝트에서는 PEP 8 준수를 권장합니다.

  | 대상 | PEP 8 권장 | Java 사상(camelCase) | 예시 (PEP 8 기준) |
  |------|-----------|---------------------|------------------|
  | 함수·변수·모듈 | `snake_case` | `camelCase` | `build_chunk_metadata`, `tenant_id` |
  | 클래스 | `PascalCase` | `PascalCase` (동일) | `DocumentService`, `VectorDbAdapter` |
  | 상수 | `UPPER_SNAKE_CASE` | `UPPER_SNAKE_CASE` (동일) | `DEFAULT_CHUNK_SIZE` |
  | 내부(private) | `_underscore` 접두사 | `_underscore` 또는 `private` 키워드 | `_run_pipeline` |

### 1.2 핵심 개념 정의

본 가이드 전반에 걸쳐 사용되는 두 핵심 식별자입니다.

| 개념 | 구분 단위 | 역할 | 예시 |
|------|----------|------|------|
| `tenant_id` (테넌트 식별자) | 완전 격리가 필요한 단위 | 물리적 단절. 다른 테넌트 데이터 접근 절대 불가. 요구사항에 따라 회사·계열사·사업부 단위로 구성 가능 | `"company_abc"` |
| `org_id` (조직 코드) | 부서·팀 | 같은 회사 내 접근 범위 제어. 빈값(`""`)이면 전사 공유 | `"0102"` → 01부서 02팀 |

> `tenant_id`는 **하드 파티셔닝(Hard Partitioning)** — 데이터 격리의 최상위 경계로, 다른 테넌트 데이터에 접근 자체가 불가합니다. `org_id`는 **쿼리 타임 필터(Query-Time Filter)** — 동일 테넌트 내에서 검색 시 메타데이터 필터로 동적 적용되는 접근 범위 제어입니다.

### 1.3 프로젝트 구조 및 아키텍처 규약

#### 3계층 구조 (APP → BIZ → Repository)

자바의 MVC 패턴과 유사하게 3계층으로 분리합니다. 각 계층은 역할이 명확히 분리되어 있으며, 파일명 접미사로 계층을 식별합니다.

| 계층 | 역할 | MVC 대응 | 접미사 | 예시 |
|------|------|---------|--------|------|
| **APP** (라우터) | HTTP 요청 수신·응답 반환 | Controller (C) | `_router` | `document_router.py` |
| **BIZ** (서비스) | 비즈니스 로직 처리·조합 | Controller+Model (C+M) | `_service` | `document_service.py` |
| **Repository** (저장소) | DB·벡터DB 직접 접근 | Model (M) | `_repo` | `vector_db_repo.py` |

#### 데이터 객체 구분

서버 프레임워크는 FastAPI를 권장합니다. 데이터 처리 객체는 아래와 같이 역할에 따라 구분하며, 파일명 접미사로 식별합니다.

| 역할 | 접미사 | 설명 | 예시 |
|------|--------|------|------|
| API 요청·응답 스키마 | `_sch` | Pydantic 기반. 입출력 데이터 검증·직렬화 담당 | `document_sch.py` |
| 내부 데이터 모델 | `_mdl` | 내부 데이터 구조 표현 객체. SQLAlchemy ORM, dataclass, 일반 클래스 모두 포함 | `document_mdl.py` |

> `_sch`와 `_mdl`의 구분 기준: **외부(API 경계)와 통신하면** `_sch`, **내부 로직·DB에서 데이터를 다루면** `_mdl`

#### 도메인 카테고리 구조

| 프로젝트 규모 | 권장 구조 | 예시 |
|-------------|---------|------|
| 대형 | 도메인 2단계 계층 | `hr/recruit/`, `policy/rules/` |
| 소형 | 단일 계층 간소화 | `hr/`, `policy/` |

---

## 2. RAG 기반 검색

사용자 질의를 벡터 유사도로 검색하고 LLM이 답변을 생성하는 핵심 인터페이스를 정의합니다.

### 2.1 API 레이아웃

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/api/v1/rag/search` | 사용자 질의 벡터 검색 및 LLM 답변 생성 |

**헤더**: `X-Tenant-ID` (필수, 누락 시 400), `X-Org-ID` (선택)

### 2.2 검색 요청 / 응답


**검색 요청 필드** (`POST /api/v1/rag/search`)

| 필드 | 타입 | 필수 | 설명 |
|------|------|:----:|------|
| `query` | String | ✅ | 사용자 질의 문장 |
| `top_k` | Integer | — | 검색 결과 수 (기본값: 5) |
| `debug_mode` | Boolean | — | `true` 시 미채택 청크 포함 반환 |
| `filters.category_large` | String | — | 대분류 필터 |
| `filters.category_mid` | String | — | 중분류 필터 (벡터 DB 라우팅) |
| `filters.vector_db_id` | String | — | 특정 벡터 DB 직접 지정 |

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

**검색 응답 주요 필드**

| 필드 | 타입 | 설명 |
|------|------|------|
| `data.answer` | String | LLM 생성 답변 |
| `data.used_chunks[].chunk_id` | String | 청크 고유 ID (`{doc_id}#chunk{n}`) |
| `data.used_chunks[].content` | String | LLM이 채택한 원문 텍스트 |
| `data.used_chunks[].similarity_score` | Float | 벡터 유사도 점수 |
| `data.used_chunks[].metadata.source_url` | String | 원본 파일 경로 (출처 링크) |
| `data.used_chunks[].metadata.page_no` | Integer | PDF 페이지 번호 |
| `data.debug_info` | Object | `debug_mode: true` 시에만 반환 (미채택 청크 포함) |

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

---

## 3. 임베딩 대상 문서 관리

원천 데이터가 임베딩되어 Vector DB에 저장되기까지의 생명 주기를 체계적으로 관리합니다.

### 3.1 처리 원칙

* **데이터 보관소 분리**: 원본 문서(Raw Document)와 파싱/청킹된 중간 텍스트(Processed Data)의 물리적 보관소를 분리합니다.
* **상태 전이**:
  ```
  pending → processing → completed
                       ↘ error
  ```
* **증분 업데이트**: 원본 문서가 갱신될 경우 `doc_id` 기준 기존 청크를 전부 삭제하고 새 청크를 재적재합니다.
* **비동기 처리**: 업로드 API는 `asyncio.create_task(asyncio.to_thread(...))` 패턴으로 파이프라인을 백그라운드 실행하고 즉시 `"pending"` 반환합니다.

### 3.2 API 레이아웃

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/api/v1/documents/upload` | 문서 업로드 및 파이프라인 시작 |
| `GET` | `/api/v1/documents` | 문서 목록 조회 |
| `GET` | `/api/v1/documents/{doc_id}` | 문서 상태 조회 (pipeline_status 폴링) |
| `PUT` | `/api/v1/documents/{doc_id}` | 문서 재업로드 (버전 갱신) |
| `DELETE` | `/api/v1/documents/{doc_id}` | 문서 삭제 (벡터 포함) |

**헤더**: `X-Tenant-ID` (필수, 누락 시 400 반환), `X-Org-ID` (필수, 누락 시 400 반환 — 전사 공유 문서는 빈값 `""` 으로 명시)

**업로드 요청 필드** (`POST /api/v1/documents/upload`, `multipart/form-data`)

| 필드 | 타입 | 필수 | 설명 |
|------|------|:----:|------|
| `file` | File | ✅ | 업로드 파일 (PDF, DOCX, TXT) |
| `category_large` | String | ✅ | 대분류 카테고리 (예: 인사, 규정, 기술) |
| `category_mid` | String | ✅ | 중분류 카테고리 — 벡터 DB 라우팅 기준 |
| `category_low` | String | — | 소분류 카테고리 |
| `project_code` | String | — | 프로젝트 코드 (기본값: `"000001"`) |

**업로드 응답 필드**

| 필드 | 타입 | 설명 |
|------|------|------|
| `data.doc_id` | String | 시스템 발급 문서 고유 ID |
| `data.file_name` | String | 업로드된 파일명 |
| `data.pipeline_status` | String | 처리 상태 (`pending` 고정 반환) |
| `data.assigned_vector_db` | String | 라우팅 결정된 벡터 DB ID |

```json
{
  "status": "success",
  "data": {
    "doc_id": "doc_a1b2c3d4",
    "file_name": "2026_인사규정.pdf",
    "pipeline_status": "pending",
    "assigned_vector_db": "vdb_hr_recruit_01"
  },
  "error": null
}
```

**상태 조회 응답 필드** (`GET /api/v1/documents/{doc_id}`)

| 필드 | 타입 | 설명 |
|------|------|------|
| `data.pipeline_status` | String | `pending` → `processing` → `completed` / `error` |
| `data.org_id` | String | 조직 코드 (빈값 = 전사 공유) |
| `data.dept_code` | String | 부서 코드 (`org_id` 앞 2자리 자동 파생) |
| `data.version` | Integer | 재업로드 횟수 기반 버전 번호 |
| `data.created_at` | DateTime | 최초 등록 일시 (UTC) |
| `data.updated_at` | DateTime | 마지막 갱신 일시 (UTC) |

```json
{
  "status": "success",
  "data": {
    "doc_id": "doc_a1b2c3d4",
    "file_name": "2026_인사규정.pdf",
    "pipeline_status": "completed",
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

아래 값은 기본 설정(예시)이며, **문서의 성격과 프로젝트 요건에 따라 조정 가능**합니다.

| 항목 | 기본값 | 조정 가이드 |
|------|--------|-------------|
| `chunk_size` | 700자 | 짧은 단락형 문서는 축소, 장문 보고서는 확대 |
| `chunk_overlap` | 80자 | 문맥 연속성이 중요한 문서(법률·계약 등)는 확대 |
| 분리 방식 | 슬라이딩 윈도우 | 표·코드 중심 문서는 구조 인식 분리 방식 검토 |
| `page_no` | 실제 PDF 페이지 번호 | chunk 인덱스 사용 금지 (고정 규칙) |

---

## 4. 벡터 DB 관리

### 4.1 물리적 분리 원칙

* 단일 거대 벡터 DB 운영을 지양하고 업무(카테고리) 또는 테넌트 단위로 독립된 `vector_db_id`를 발급하여 라우팅합니다.
* **임베딩 모델별 컬렉션 분리**: 모델(OpenAI, Gemini, Solar 등)마다 벡터 차원이 다르므로 단일 컬렉션에 혼재하지 않습니다.
* **임베딩 일관성 원칙**: 저장 시와 쿼리 시 반드시 동일한 임베딩 서비스를 사용합니다. 저장 단계에서 임베딩을 생성하여 `embeddings=` 파라미터로 명시 전달합니다 (adapter 내부 호출 금지).

### 4.2 벡터 DB 엔진 선택

프로젝트 규모와 운영 환경에 따라 엔진을 선택합니다. **본 가이드의 예시 코드는 ChromaDB 기준으로 작성**되었습니다. 벡터 DB 변경 시 영향 범위를 최소화하기 위해 **APP → BIZ → Repository** 3계층으로 분리 설계합니다. 엔진 교체 시 Repository 계층의 수정은 불가피하나, BIZ·APP 계층은 변경 없이 유지됩니다.

| 엔진 | 특성 | 적합한 환경 |
|------|------|------------|
| **ChromaDB** | 로컬 파일 기반, 설치 간단, Python 친화적 | 개발·테스트, 소규모 단일 서버 구성 |
| **Qdrant** | 분산 아키텍처, REST/gRPC, 복합 메타데이터 필터 고성능 | 프로덕션, MSA·멀티테넌트 환경 |
| **FAISS** | 인메모리, 메타데이터 필터 없음 | 단순 유사도 실험·연구용 (운영 비권장) |

> **제약**: 멀티테넌트 격리(`tenant_id`, `org_id` 필터)가 필수이므로 메타데이터 필터를 지원하지 않는 엔진은 이 표준에 적합하지 않습니다.

### 4.3 카테고리-벡터DB 매핑

문서의 **중분류(`category_mid`)를 기준으로 어느 벡터 DB에 저장하고 검색할지**를 정의합니다. 대분류(`category_large`)는 벡터 DB를 묶어 보는 상위 그룹 역할만 합니다.

> **카테고리와 `org_id`의 관계**: 둘 다 계층 구조를 갖고 벡터 DB 필터에 활용된다는 점에서 설계 구조가 유사합니다. 그러나 개념적으로는 독립된 두 축입니다. 카테고리는 **"무엇에 관한 문서인가"(WHAT)** — 지식 분류·DB 라우팅 기준이고, `org_id`는 **"누가 볼 수 있는 문서인가"(WHO)** — 접근 통제 기준입니다. (§1.1 이중 축 원칙 참조)

> 아래는 논리적 구성 예시이며, 실제 카테고리 정보와 매핑은 프로젝트 요건에 따라 구성합니다.

| 대분류 | 중분류 | 매핑 벡터 DB |
|--------|--------|-------------|
| 인사 | 채용 | `vdb_hr_recruit_01` |
| 인사 | 급여 | `vdb_hr_payroll_01` |
| 규정 | 취업규칙 | `vdb_policy_01` |
| 기술 | ontology | `vdb_ontology_01` |

### 4.4 관리자 API

시스템에 등록된 벡터 DB 현황을 조회하는 관리자용 인터페이스입니다. 어떤 카테고리가 어느 벡터 DB에 연결되어 있는지, 현재 저장된 문서 수가 얼마인지 확인할 수 있습니다.

| Method | Endpoint | 설명 |
|--------|----------|------|
| `GET`  | `/api/v1/admin/vector-dbs` | 등록된 벡터 DB 목록 조회 |

**응답 필드**

| 필드 | 타입 | 설명 |
|------|------|------|
| `data[].vector_db_id` | String | 벡터 DB 식별자 |
| `data[].engine` | String | 사용 엔진 (`chroma`, `qdrant` 등) |
| `data[].collection_name` | String | 엔진 내 컬렉션(테이블) 이름 |
| `data[].category_large` | String | 연결된 대분류 |
| `data[].category_mid` | String | 연결된 중분류 |
| `data[].doc_count` | Integer | 현재 저장된 문서 수 |

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
 

## 5. 벡터DB의 임베딩별 문서 매칭관리

문서↔벡터 청크 간 연결 유지 규칙을 정의합니다. 세부 구현은 각 참조 섹션에서 정의합니다.

### 5.1 핵심 매칭 규칙

| 규칙 | 내용 |
|------|------|
| **chunk_id 명명** | `{doc_id}#chunk{순번}` 자동 생성 (예: `doc_a1b2c3d4#chunk0`) |
| **라우팅** | `category_mid` → `vector_db_id` 매핑으로 저장 벡터DB 결정 (§4.3 카테고리-벡터DB 매핑) |
| **연쇄 삭제** | 문서 삭제 시 `doc_id`의 모든 청크를 벡터DB에서 함께 삭제 |
| **임베딩 경계** | 임베딩 생성은 파이프라인 책임, adapter는 `embeddings=` 파라미터로 수신만 함 |
| **org_id OR 검색** | 검색 시 `org_id == "{org_id}" OR org_id == ""` (전사 공유 문서 자동 포함) |

#### OR 조건 검색 정책

| 레벨 | 헤더 | 벡터 DB 필터 |
|------|------|------------|
| 전사 검색 | `X-Tenant-ID` | `tenant_id == "abc"` |
| 부서 검색 | `X-Tenant-ID` + `X-Org-ID: 0100` | `tenant_id == "abc"` AND (`dept_code == "01"` OR `org_id == ""`) |
| 팀 검색 | `X-Tenant-ID` + `X-Org-ID: 0102` | `tenant_id == "abc"` AND (`org_id == "0102"` OR `org_id == ""`) |

> **저장 원칙**: 문서 업로드 시 `org_id`는 반드시 명시합니다. 전사 공유 문서는 `X-Org-ID: ""`(빈 문자열)로 명시적으로 지정해야 하며, 헤더 누락은 400 오류입니다. ChromaDB는 `None` 메타데이터를 지원하지 않으므로 전사 공유 sentinel은 `""`(빈 문자열)로 저장합니다.

> **⚠ 보안 주의**: `X-Org-ID` 생략 시 전사 범위 검색이 허용됩니다. 현재는 RBAC 미구현(§7) 상태이므로, 운영 환경에서는 서버가 인증 토큰의 사용자 소속 `org_id`로 자동 보정하거나 일반 사용자의 전사 검색을 제한하는 정책을 별도 적용할 것을 권장합니다.

```python
def build_chunk_metadata(tenant_id: str, org_id: str | None, ...) -> dict:
    return {
        "tenant_id": tenant_id,
        "org_id": org_id,                  # 업로드 시 반드시 명시 ("" = 전사 공유 명시적 지정)
        "dept_code": org_id[:2] if org_id else "",  # 자동 파생
        # ...
    }
```

### 5.2 청크 출처 추적 (Grounding)

답변의 신뢰성(Grounding)을 확보하기 위해 검색된 벡터가 어느 원문의 몇 페이지에서 왔는지 추적합니다.  
응답 레이아웃은 §2.2 `used_chunks` 항목 구조를 따릅니다.

**참조 섹션**

- 검색 API 및 used_chunks 응답 → §2 RAG 기반 검색
- 카테고리-벡터DB 매핑 기준 (category_mid → vector_db_id) → §4.3 카테고리-벡터DB 매핑
- 구현 소스 → `{구현체}/app/services/vector_db/`, `{구현체}/app/services/document_service.py` (예시 경로, 실제 구현체 경로로 대체)

---

## 6. 메타데이터 관리

RAG에서 메타데이터란 벡터 청크에 함께 저장되는 **부가 속성 정보**입니다. 벡터 DB는 유사도 검색 결과에 이 속성을 자동으로 함께 반환하며, 검색 시 필터 조건으로도 활용됩니다.

| 역할 | 설명 | 예시 속성 |
|------|------|---------|
| 접근 제어 (WHO) | 누가 볼 수 있는 문서인지 식별 | `tenant_id`, `org_id`, `dept_code` |
| 지식 분류 (WHAT) | 어떤 주제의 문서인지 분류 | `category_large`, `category_mid` |
| 출처 추적 | 답변 근거 문서와 페이지 확인 | `source_url`, `page_no`, `doc_id` |

메타데이터는 **문서 업로드 시 자동 생성**되어 벡터 DB에 저장됩니다. 별도 관리 작업 없이 검색·필터링에 즉시 활용됩니다.

> 속성 구조 상세 → §1.1 이중 축 원칙, 전체 속성 목록 → §3.2 업로드 요청 필드

---

## 7. 접근 권한 관리 (보류)

> **사상**: "**누가 볼 수 있는 문서인가(WHO)**"를 제어하는 것이 접근 권한 관리의 핵심입니다. 본 가이드에서는 회사 식별자(`tenant_id`)로 회사 간 절대 격리를, 조직 코드(`org_id`)로 같은 회사 내 부서·팀 단위 접근 범위를 제어하는 수준으로 구현합니다. 역할 기반 접근 제어(RBAC)·행 수준 보안(RLS) 등 세분화된 권한 정책은 **본 가이드에서 설계를 생략**합니다.
>
> **세밀한 문서 권한은 원본 시스템에 위임합니다.** RAG 시스템은 `org_id` 필터로 대략적인 조직 범위를 제한하고, 검색 결과와 함께 `source_url`을 반환합니다. 사용자가 실제 문서에 접근할 때는 SharePoint·DRM 등 원본 시스템의 권한이 재검증됩니다. RAG 내부에 문서별 세밀한 권한을 구현하는 것은 과설계(Over-engineering)입니다.

---

## 8. 오류/예외 결과

RAG 시스템은 임베딩 API, 벡터DB, LLM 등 여러 외부 컴포넌트를 연계하므로 오류 발생 지점이 다양합니다. 오류가 발생했을 때 **호출하는 측(애플리케이션·에이전트)과 RAG 시스템 간의 원활한 의사소통**을 위해 일관된 오류 응답 형식과 코드 체계를 정의합니다.

예외 처리의 주요 목적은 다음과 같습니다.

* **전파 차단**: 임베딩·벡터DB 등 하위 컴포넌트의 오류가 전체 시스템으로 확산되지 않도록 격리합니다.
* **명확한 원인 전달**: 오류 코드와 메시지로 어느 계층에서 무슨 문제가 발생했는지 즉시 파악할 수 있도록 합니다.
* **일관된 응답 포맷**: 호출 측이 성공·실패를 동일한 구조로 처리할 수 있도록 `status / data / error` 포맷을 전 API에 통일합니다.

### 8.1 표준 예외 코드

에러 코드는 `{도메인}-{번호}` 형식으로 관리합니다. 짧고 로그·응답에 포함하기 용이하며, 번호 추가만으로 확장됩니다. 구현체 내부 예외 식별자와의 매핑은 아래 표를 참조합니다.

| 코드 | 도메인 | HTTP | 발생 조건 | 구현 식별자 |
|------|--------|:----:|---------|-----------|
|------|--------|:----:|---------|
| `DOC-001` | 문서 | 422 | 파일 파싱 실패 | `document_parsing_error` |
| `DOC-002` | 문서 | 404 | 문서(`doc_id`) 없음 | `document_not_found` |
| `DOC-003` | 문서 | 409 | 동일 문서 중복 업로드 | `document_duplicate` |
| `EMB-001` | 임베딩 | 503 | 임베딩 API 호출 시간 초과 | `embedding_api_timeout` |
| `EMB-002` | 임베딩 | 502 | 임베딩 API 오류 응답 | `embedding_api_error` |
| `VDB-001` | 벡터DB | 503 | 벡터DB 연결 실패 | `vector_db_connection_error` |
| `VDB-002` | 벡터DB | 404 | 지정한 컬렉션·DB 없음 | `vector_db_not_found` |
| `AUTH-001` | 인증 | 400 | `X-Tenant-ID` 헤더 누락 | `tenant_id_missing` |

### 8.2 오류 응답 포맷

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "EMB-001",
    "message": "임베딩 API 호출이 시간 초과되었습니다."
  }
}
```

### 8.3 임베딩 오류 시 즉시 중단

임베딩 API 호출이 실패했을 때, 가짜 벡터(`[0.1, 0.2]` 등)를 만들어 넘기거나 오류를 무시한 채 처리를 계속하는 것을 **금지**합니다. 잘못된 벡터로 저장된 데이터는 검색 품질을 오염시키고, 오류가 발생했다는 사실 자체를 숨기게 됩니다.

오류가 발생하면 `EMB-001` 코드를 호출한 쪽으로 반환하고 파이프라인을 `error` 상태로 전환하여, 문제가 즉시 드러나도록 해야 합니다.

---

## 9. Agent/Orchestration 요청 (보류)

> 복수 에이전트가 RAG 파이프라인을 도구로 호출하는 Orchestration 인터페이스(Multi-Agent RAG, Tool-calling 등)는 **설계 보류**입니다. SSE 스트리밍은 일반 RAG 검색 범위에서는 별도 검토하며, 여기서의 보류는 **Agent 간 Orchestration 전용 스트리밍 표준**에 한합니다.
