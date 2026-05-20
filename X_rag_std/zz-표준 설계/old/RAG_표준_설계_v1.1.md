# 엔터프라이즈 RAG 표준 기본설계서 (v1.1)

> **버전 이력**
>
> | 버전 | 일자 | 주요 변경 |
> |------|------|---------|
> | v1.0 | 2026-05-14 | 초안 작성 |
> | v1.1 | 2026-05-14 | `company_id` 메타데이터 필수화 · X-Company-ID 헤더 표준 신설(2.5) · `retrieved_chunks`→`used_chunks` 용어 통일(2.3) · `chunk_size` 단위 명확화 · 임베딩 fallback 금지 조항 추가(2.6) · 멀티테넌트 격리를 핵심 원칙으로 격상(1.1) |

---

## 1. 개요 및 설계 원칙
본 문서는 `HNIX AI 백엔드 아키텍처 설계서`를 기반으로, 엔터프라이즈 환경에서 안정적이고 유연하게 동작할 수 있는 RAG(Retrieval-Augmented Generation) 시스템의 표준 설계 기준을 정의합니다.

### 1.1 핵심 아키텍처 원칙 (Core Principles)
* **물리적 분리 (MSA 기반)**: 보안 및 인프라 운영상의 이유로 LLM 추론 서버와 Vector DB 영역은 물리적으로 분리될 수 있어야 합니다. 프레임워크(예: LangChain)에 종속된 강한 결합을 피하고, REST API 또는 gRPC를 통한 `Remote Retriever` 패턴을 활용하여 느슨한 결합(Loosely Coupled) 구조를 지향합니다.
* **멀티테넌트 격리 (Tenant Isolation)**: 모든 데이터 저장·검색 경로에서 `company_id`를 기준으로 테넌트를 격리합니다. RDBMS 레코드, Vector DB chunk metadata, LLM Gateway 호출 모두 `company_id`를 포함해야 합니다. 격리 구현 방법은 2.5항을 따릅니다.
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
  * **임베딩 일관성 원칙**: 문서 저장 시와 쿼리 검색 시 **반드시 동일한 임베딩 서비스**를 사용해야 합니다. ChromaDB 등 외부 벡터 DB 저장 단계에서 임베딩을 직접 생성하여 `embeddings=` 파라미터로 명시 전달합니다. 구현 세부는 상세설계 02 5항을 참조합니다.

### 2.3. 벡터DB의 임베딩별 문서 매칭 관리 (API 응답 레이아웃)
답변의 신뢰성(Grounding)을 확보하기 위해 검색된 벡터가 어느 원문의 몇 페이지에서 왔는지 명확히 추적하고 프론트엔드에 전달해야 합니다.
* **역매핑 (Reverse Mapping) API 표준 레이아웃**: RAG 엔진이 반환하는 JSON 응답 포맷은 아래와 같이 문서 출처(`source`), 페이지 번호(`page_no`), 유사도 점수(`score`), 테넌트(`company_id`)를 명시적으로 포함해야 합니다.

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
          "company_id": "company_abc"
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
| `company_id` | String | 필수 | 테넌트 구분자 — `X-Company-ID` 헤더에서 주입. 검색 필터에 반드시 강제 적용 |
| `source_url` | String | 필수 | 원본 파일 다운로드 또는 열람 경로 |
| `created_at` | DateTime | 필수 | 인덱싱(임베딩)된 시각 (timezone-aware ISO 8601) |
| `vector_db_id` | String | 필수 | 문서가 저장된 물리적 벡터 DB의 식별자 |
| `category_mid` | String | 필수 | 문서의 중분류 카테고리 (라우팅 기준) |
| `category_low` | String | 선택 | 문서의 소분류 카테고리 |
| `page_no` | Integer | 선택(권장) | 원본 파일 내의 **실제 페이지 번호** (chunk 순번 아님) |
| `chunk_type` | String | 선택 | 청크 속성 (`text`, `table`, `image_desc` 등) |
| `tags` | Array[String] | 선택 | 비즈니스 로직에 따른 검색 필터링용 태그 |

### 2.5. 멀티테넌트 격리 표준 (X-Company-ID)
엔터프라이즈 환경에서 여러 회사/조직의 데이터를 동일 인프라에서 운영할 경우 반드시 적용합니다.

#### 헤더 수신 규칙
모든 API 엔드포인트는 `X-Company-ID` HTTP 헤더를 수신합니다. 헤더가 없을 경우 `"default"`를 사용합니다.

```python
def get_company_id(request: Request) -> str:
    return request.headers.get("X-Company-ID", "default")
```

#### 격리 적용 3단계 (전 경로 필수)

| 단계 | 대상 | 규칙 |
|------|------|------|
| 1. 저장 | Vector DB chunk metadata | `metadata["company_id"] = company_id` 반드시 포함 |
| 2. 검색 | Vector DB search filter | `filters["company_id"] = company_id` 반드시 강제 주입 |
| 3. Gateway | LLM/임베딩 요청 body | `"company_id": company_id` 포함 — 감사·쿼타 관리 지원 |

#### 위반 시 리스크
- 회사 A의 검색 결과에 회사 B의 문서가 노출되는 보안 사고 발생
- Gateway 테넌트별 사용량 추적 불가

### 2.6. 오류 및 예외 결과 표준
모든 컴포넌트는 예외 발생 시 표준화된 응답 포맷을 반환하여 시스템 안정성을 유지합니다.
* **표준 예외 클래스 명명**:
  * `document_parsing_error`: 파일 로드 및 파싱 실패 시
  * `embedding_api_timeout`: 임베딩 모델 호출 시간 초과 시
  * `vector_db_connection_error`: 물리적으로 분리된 Vector DB와의 연결 실패 시
* 오류 발생 시 프론트엔드/에이전트에 `status: "error"`, `error_code: "..."`, `message: "..."` 형태의 JSON 포맷으로 반환하는 것을 원칙으로 합니다.
* **임베딩 실패 시 fallback 금지**: 임베딩 API 호출 실패 시 더미 벡터(`[0.1, 0.2]` 등)를 반환하거나 조용히 무시해서는 안 됩니다. 반드시 `embedding_api_timeout` 예외를 전파하여 파이프라인을 `error` 상태로 전환합니다.

### 2.7. RAG 쿼리 통합 인터페이스 표준 (API Layout)
Agent/Orchestrator가 RAG 엔진에 질의를 던지고 결과를 취합하는 표준 인터페이스입니다. 본 API 레이아웃은 표준으로 확정되어 모든 연동 시스템(프론트엔드 및 외부 AI Agent)에 제공됩니다.

#### [검색 요청 Request]
* **Endpoint:** `POST /api/v1/rag/search`
* **Content-Type:** `application/json`
* **Header:** `X-Company-ID: {company_id}` (필수)

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
* 2.3항에서 정의된 역매핑 스키마를 포함하여, LLM이 정답 생성에 최종 사용한 핵심 청크(`used_chunks`)와, 디버그 모드일 경우 Vector DB가 1차로 검색해 온 전체 후보 청크(`debug_info.candidate_chunks`)를 명확히 구분하여 반환합니다.

```json
{
  "status": "success",
  "data": {
    "query": "2026년 인사 규정 알려줘",
    "answer": "2026년 인사 규정에 따르면...",
    "used_chunks": [
      {
        "chunk_id": "doc123#chunk4",
        "content": "이 부분은 LLM이 정답을 생성하는 데 실제 채택한 텍스트입니다...",
        "metadata": {
          "source_name": "2026_AI_가이드.pdf",
          "source_url": "https://storage.example.com/docs/2026_AI_가이드.pdf",
          "page_no": 12,
          "category_mid": "규정",
          "vector_db_id": "vdb_policy_01",
          "company_id": "company_abc"
        },
        "similarity_score": 0.89
      }
    ],
    "debug_info": {
      "execution_time_ms": 145,
      "candidate_chunks": [
        "// 디버그 모드(debug_mode: true) 요청 시에만 노출됩니다.",
        "// 정답 생성에 채택되지 않았더라도 Vector DB에서 1차로 검색된 Top-K (예: 10개) 후보 청크 전체의 원문과 유사도 점수를 리스트업하여",
        "// 임베딩 검색 품질을 모니터링하고 분석할 수 있도록 제공합니다."
      ]
    }
  },
  "error": null
}
```
