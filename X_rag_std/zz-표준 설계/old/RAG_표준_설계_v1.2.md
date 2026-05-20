# 엔터프라이즈 RAG 표준 기본설계서 (v1.2)

> **버전 이력**
>
> | 버전 | 일자 | 주요 변경 |
> |------|------|---------|
> | v1.0 | 2026-05-14 | 초안 작성 |
> | v1.1 | 2026-05-14 | `company_id` 메타데이터 필수화 · X-Company-ID 헤더 표준 신설 · 용어 통일 · chunk_size 단위 명확화 · 임베딩 fallback 금지 |
> | v1.2 | 2026-05-14 | `company_id` → `tenant_id` 전면 교체 · `org_id` 계층 코드 신설 · `dept_code` 파생 필드 추가 · X-Tenant-ID/X-Org-ID 헤더 표준 · Index Swap 운영 패턴(2.8) 추가 |

---

## 1. 개요 및 설계 원칙
본 문서는 `HNIX AI 백엔드 아키텍처 설계서`를 기반으로, 엔터프라이즈 환경에서 안정적이고 유연하게 동작할 수 있는 RAG(Retrieval-Augmented Generation) 시스템의 표준 설계 기준을 정의합니다.

### 1.1 핵심 아키텍처 원칙 (Core Principles)
* **물리적 분리 (MSA 기반)**: 보안 및 인프라 운영상의 이유로 LLM 추론 서버와 Vector DB 영역은 물리적으로 분리될 수 있어야 합니다. 프레임워크(예: LangChain)에 종속된 강한 결합을 피하고, REST API 또는 gRPC를 통한 `Remote Retriever` 패턴을 활용하여 느슨한 결합(Loosely Coupled) 구조를 지향합니다.
* **멀티테넌트 격리 (Tenant Isolation)**: 모든 데이터 저장·검색 경로에서 `tenant_id`를 기준으로 회사 단위 격리를 보장합니다. 추가로 `org_id`를 통해 조직(부서·팀) 단위 범위 제어가 가능합니다. 격리 구현 방법은 2.5항을 따릅니다.
* **표준 코딩 컨벤션**: 모든 구현체는 파이썬 PEP 8 규약(snake_case 함수/변수, PascalCase 클래스)을 준수하여 가독성과 협업 효율성을 극대화합니다.

---

## 2. RAG 핵심 컴포넌트 설계 표준

### 2.1. 임베딩 대상 문서 관리
원천 데이터가 임베딩되어 Vector DB에 저장되기까지의 생명 주기를 체계적으로 관리합니다.
* **데이터 보관소 분리**: 원본 문서(Raw Document)와 파싱/청킹된 중간 텍스트(Processed Data)의 물리적 보관소를 분리합니다. (예: S3/MinIO 버킷 분리)
* **상태 전이 관리**: 각 문서는 `pending` -> `processing` -> `completed` / `error` 의 상태값을 가집니다.
* **증분 업데이트(Incremental Update)**: 원본 문서가 갱신될 경우, 기존 청크를 전부 삭제하고 다시 적재하는 대신 변경된 문서나 페이지(Chunk)만 식별하여 갱신합니다.

### 2.2. 벡터 DB 관리 및 물리적 분리 구조
RDBMS에 비해 벡터 DB는 대규모 데이터 적재 시 안정성이 떨어질 수 있으며 덩치가 기하급수적으로 커집니다. 따라서 다음과 같이 벡터 DB를 물리적/논리적으로 분리하는 아키텍처를 채택합니다.
* **벡터 DB의 물리적 분리**:
  * 단일 거대 벡터 DB를 운영하기보다 업무(예: 카테고리) 혹은 테넌트 단위로 분리된 인스턴스를 운영하거나 독립된 `vector_db_id`를 발급하여 라우팅합니다.
  * 문서 업로드 시 중분류/소분류(`category_mid`, `category_low`)를 지정하고, 이에 매칭되는 물리적 벡터 DB(`vector_db_id`)에 분산 저장하여 안정성과 검색 속도를 확보합니다.
* **엔진 이원화 활용**:
  * **ChromaDB / Qdrant 등**: 풍부한 메타데이터 필터링 및 영구적인 지식 베이스(Knowledge Base)가 필요할 때 사용합니다.
  * **FAISS**: 세션 기반의 휘발성 컨텍스트 관리나 초고속 단순 유사도 검색이 필요할 때 활용합니다.
* **컬렉션(Collection) 분리 방침**:
  * **임베딩 모델별 분리**: 모델(OpenAI, Solar 등)마다 벡터의 차원(Dimension) 크기가 다르므로 단일 컬렉션에 혼재되지 않도록 철저히 분리합니다.
  * **임베딩 일관성 원칙**: 문서 저장 시와 쿼리 검색 시 **반드시 동일한 임베딩 서비스**를 사용해야 합니다. ChromaDB 등 외부 벡터 DB 저장 단계에서 임베딩을 직접 생성하여 `embeddings=` 파라미터로 명시 전달합니다.

### 2.3. 벡터DB의 임베딩별 문서 매칭 관리 (API 응답 레이아웃)
답변의 신뢰성(Grounding)을 확보하기 위해 검색된 벡터가 어느 원문의 몇 페이지에서 왔는지 명확히 추적하고 프론트엔드에 전달해야 합니다.

```json
{
  "status": "success",
  "data": {
    "query": "검색된 사용자의 질의",
    "used_chunks": [
      {
        "chunk_id": "doc123#chunk4",
        "content": "이 부분은 문서에서 추출된 실제 텍스트 내용입니다...",
        "metadata": {
          "source_name": "2026_AI_가이드.pdf",
          "source_url": "https://storage.../2026_AI_가이드.pdf",
          "page_no": 12,
          "category_mid": "규정",
          "vector_db_id": "vdb_policy_01",
          "tenant_id": "company_abc",
          "org_id": "0102",
          "dept_code": "01"
        },
        "similarity_score": 0.89
      }
    ]
  }
}
```

### 2.4. 표준 메타데이터 관리
Vector DB 검색 정확도 향상 및 분리된 DB 환경 지원을 위한 기준 스키마입니다.

| 속성명 (snake_case) | 데이터 타입 | 필수 여부 | 설명 |
| :--- | :--- | :--- | :--- |
| `doc_id` | String | 필수 | 시스템 내 원본 문서 고유 ID |
| `tenant_id` | String | 필수 | 회사 단위 테넌트 구분자 — `X-Tenant-ID` 헤더에서 주입. 검색 필터에 반드시 강제 적용 |
| `org_id` | String | 선택 | 조직 계층 코드 — `{DD}{TT}` 형식 (DD: 부서 2자리, TT: 팀 2자리). 없으면 전사 공유 문서로 처리 |
| `dept_code` | String | 조건부 필수 | `org_id` 존재 시 필수. `org_id` 앞 2자리 파생값. 부서 단위 검색 필터용 |
| `source_url` | String | 필수 | 원본 파일 다운로드 또는 열람 경로 |
| `created_at` | DateTime | 필수 | 인덱싱(임베딩)된 시각 (timezone-aware ISO 8601) |
| `vector_db_id` | String | 필수 | 문서가 저장된 물리적 벡터 DB의 식별자 |
| `category_mid` | String | 필수 | 문서의 중분류 카테고리 (라우팅 기준) |
| `category_low` | String | 선택 | 문서의 소분류 카테고리 |
| `page_no` | Integer | 선택(권장) | 원본 파일 내의 실제 페이지 번호 (chunk 순번 아님) |
| `chunk_type` | String | 선택 | 청크 속성 (`text`, `table`, `image_desc` 등) |
| `tags` | Array[String] | 선택 | 비즈니스 로직에 따른 검색 필터링용 태그 |

### 2.5. 멀티테넌트 격리 표준 (X-Tenant-ID / X-Org-ID)
엔터프라이즈 환경에서 회사·조직 단위 데이터 격리를 보장합니다.

#### 헤더 수신 규칙
```python
def get_tenant_id(request: Request) -> str:
    return request.headers.get("X-Tenant-ID", "default")

def get_org_id(request: Request) -> str | None:
    return request.headers.get("X-Org-ID", None)   # None = 전사 범위
```

#### org_id 계층 코드 체계
```
형식: {DD}{TT}  — DD: 부서(2자리), TT: 팀(2자리)
예시:
  0100  → 01부서 전체 (팀 미지정)
  0102  → 01부서 02팀
  0200  → 02부서 전체

확장:
  {DD}{TT}{PP}  — PP: 파트(2자리) 추가 시 6자리로 확장
  제약: zero-padding 필수 (01 O, 1 X), 최대 8자리 이하

메타데이터 저장 시 파생값 생성:
  org_id = "0102"  →  dept_code = "01"  (앞 2자리 슬라이싱)
```

#### 격리 적용 레벨

| 레벨 | 헤더 | 벡터 DB 필터 | 범위 |
|------|------|-------------|------|
| 전사 격리 | `X-Tenant-ID` | `tenant_id == "abc"` | 회사 전체 |
| 부서 격리 | `X-Tenant-ID` + `X-Org-ID: 0100` | `tenant_id == "abc"` AND `dept_code == "01"` | 01부서 전체 |
| 팀 격리 | `X-Tenant-ID` + `X-Org-ID: 0102` | `tenant_id == "abc"` AND `org_id == "0102"` | 01부서 02팀 |

> **Note**: ChromaDB, Qdrant 등 벡터 DB는 LIKE/prefix 검색을 지원하지 않습니다. 부서 단위 검색을 위해 `dept_code`를 별도 메타데이터 필드로 반드시 저장해야 합니다.

#### 저장 시 자동 파생 처리 (구현 규칙)
```python
def build_chunk_metadata(tenant_id: str, org_id: str | None, ...) -> dict:
    meta = {"tenant_id": tenant_id, ...}
    if org_id:
        meta["org_id"] = org_id
        meta["dept_code"] = org_id[:2]   # 파생 — 절대 수동 입력하지 않음
    return meta
```

### 2.6. 오류 및 예외 결과 표준
모든 컴포넌트는 예외 발생 시 표준화된 응답 포맷을 반환하여 시스템 안정성을 유지합니다.
* **표준 예외 클래스 명명**:
  * `document_parsing_error`: 파일 로드 및 파싱 실패 시
  * `embedding_api_timeout`: 임베딩 모델 호출 시간 초과 시
  * `vector_db_connection_error`: 물리적으로 분리된 Vector DB와의 연결 실패 시
* 오류 발생 시 프론트엔드/에이전트에 `status: "error"`, `error_code: "..."`, `message: "..."` 형태의 JSON 포맷으로 반환합니다.
* **임베딩 실패 시 fallback 금지**: 임베딩 API 호출 실패 시 더미 벡터(`[0.1, 0.2]` 등)를 반환하거나 조용히 무시해서는 안 됩니다. 반드시 `embedding_api_timeout` 예외를 전파하여 파이프라인을 `error` 상태로 전환합니다.

### 2.7. RAG 쿼리 통합 인터페이스 표준 (API Layout)

#### [검색 요청 Request]
* **Endpoint:** `POST /api/v1/rag/search`
* **Headers:** `X-Tenant-ID: {tenant_id}` (필수), `X-Org-ID: {org_id}` (선택)

```json
{
  "query": "사용자의 질의어 (예: 2026년 인사 규정 알려줘)",
  "top_k": 5,
  "debug_mode": true,
  "filters": {
    "category_mid": "규정",
    "vector_db_id": "vdb_policy_01"
  }
}
```

#### [검색 응답 Response]

```json
{
  "status": "success",
  "data": {
    "query": "2026년 인사 규정 알려줘",
    "answer": "2026년 인사 규정에 따르면...",
    "used_chunks": [
      {
        "chunk_id": "doc123#chunk4",
        "content": "LLM이 정답 생성에 실제 채택한 텍스트...",
        "metadata": {
          "source_name": "2026_AI_가이드.pdf",
          "source_url": "https://storage.example.com/docs/2026_AI_가이드.pdf",
          "page_no": 12,
          "category_mid": "규정",
          "vector_db_id": "vdb_policy_01",
          "tenant_id": "company_abc",
          "org_id": "0102",
          "dept_code": "01"
        },
        "similarity_score": 0.89
      }
    ],
    "debug_info": {
      "execution_time_ms": 145,
      "candidate_chunks": ["// debug_mode: true 시에만 노출"]
    }
  },
  "error": null
}
```

### 2.8. 조직 개편 시 인덱스 교체 패턴 (Index Swap)
벡터 DB의 chunk metadata를 건별 수정하면 부분 실패 위험이 있고 서비스 중단이 필요합니다. 검색 엔진(Elasticsearch 등)에서 검증된 **인덱스 교체(alias swap)** 패턴을 사용합니다.

#### 교체 절차
```
1. 신규 컬렉션 생성 (새 org_id 기준으로 전체 재색인)
   vdb_abc_01_v1 (구) → 서비스 중 유지
   vdb_abc_01_v2 (신) → 백그라운드 재색인

2. 재색인 완료 및 검증 후 routing.json의 collection_name만 교체
   "collection_name": "abc_dept01_v1"  →  "collection_name": "abc_dept01_v2"

3. 구 컬렉션 삭제 (롤백 기간 경과 후)
```

#### 왜 이 방식인가

| 방식 | 특징 |
|------|------|
| 건별 metadata update | 부분 실패 위험, 서비스 중 불일치 상태 존재 |
| **Index Swap (권장)** | 원자적 전환, 무중단, 롤백 용이 |

#### 구현 포인트
* 애플리케이션 코드는 `vector_db_id`만 바라보기 때문에 routing.json의 `collection_name` 한 줄 변경으로 전환 완료
* 신규 컬렉션 재색인은 야간 배치로 수행 가능
* 전환 전 신·구 컬렉션 동시 서비스도 가능 (A/B 검색 품질 비교)
