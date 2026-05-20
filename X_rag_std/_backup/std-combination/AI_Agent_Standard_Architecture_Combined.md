# AI 에이전트 표준 아키텍처 통합 설계서 (v1.0)

## 1. 개요 및 출처
본 문서는 `AI Agent 표준 아키텍처 설계-실전.md`와 `std-work/details` 하위 상세 문서를 통합한 구현 기준 문서입니다. 상위 가이드의 방향성은 유지하되, 상세 문서 간 불일치가 있던 API 경로, 응답 필드명, DB 테이블 및 인용 규칙을 하나의 기준으로 정리합니다.

### 1.1 참조 문서
* `AI Agent 표준 아키텍처 설계-실전.md`
* `std-work/details/01_DB_Schema_Detail.md`
* `std-work/details/02_API_Interface_Spec.md`
* `std-work/details/03_RAG_Pipeline_Advanced.md`
* `가이드 자료 배포 - 20240401`
* `ragChatbot_설치_가이드_v0.2 (20240401)`

### 1.2 통합 기준
* API 기본 경로는 `/api/v1`로 통일합니다.
* 하이브리드 질의 응답의 근거 문서 필드는 `source_documents`로 통일합니다.
* 문서 인덱싱 API는 `/api/v1/ingest/upload`를 기준으로 합니다.
* 인용은 답변 본문에 `[1]`, `[2]` 형태로 표시하고, 상세 근거는 `source_documents`에서 제공합니다.
* RDBMS는 문서 메타데이터와 추적성을 담당하고, Vector DB는 임베딩 검색을 담당합니다.

## 2. 전체 아키텍처
AI 에이전트 표준 아키텍처는 문서 수집, 전처리, 임베딩, 저장, 검색, 리랭킹, 답변 생성, 근거 제시, 피드백 수집의 흐름으로 구성됩니다.

```text
문서 업로드
  -> 텍스트 추출
  -> 동적 청킹
  -> 임베딩 생성
  -> Vector DB 저장
  -> RDBMS 메타데이터 저장
  -> 하이브리드 검색
  -> 리랭킹
  -> LLM 답변 생성
  -> 인용 및 근거 문서 반환
  -> 사용자 피드백 수집
```

## 3. 데이터베이스 상세 설계
RDBMS는 문서, 청크, 임베딩 모델, 벡터 저장소 매핑, 피드백 정보를 관리합니다. Vector DB 검색 결과는 `VECTOR_ID`를 통해 RDBMS의 청크 및 문서 메타데이터와 연결됩니다.

### 3.1 TB_DOC_MASTER
원천 문서의 업로드 상태 및 기본 메타데이터를 관리합니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `DOC_ID` | VARCHAR(36) | PK | 문서 고유 식별자(UUID) |
| `FILE_NAME` | VARCHAR(255) | NOT NULL | 파일 원본 명칭 |
| `FILE_PATH` | VARCHAR(512) | NOT NULL | 스토리지 내 저장 경로 |
| `FILE_TYPE` | VARCHAR(20) | - | PDF, DOCX, TXT 등 파일 유형 |
| `FILE_SIZE` | BIGINT | - | 파일 크기(Bytes) |
| `TENANT_ID` | VARCHAR(50) | NOT NULL, INDEX | 테넌트 또는 그룹 식별자 |
| `CATEGORY` | VARCHAR(100) | INDEX | 문서 분류 |
| `STATUS` | VARCHAR(20) | - | PENDING, PROCESSING, COMPLETED, FAILED |
| `REG_DT` | DATETIME | DEFAULT NOW() | 등록 일시 |
| `UPD_DT` | DATETIME | - | 수정 일시 |

### 3.2 TB_DOC_CHUNK
문서를 임베딩 단위로 분할한 텍스트 조각과 벡터 매핑 정보를 관리합니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `CHUNK_ID` | VARCHAR(36) | PK | 청크 고유 식별자 |
| `DOC_ID` | VARCHAR(36) | FK, INDEX | `TB_DOC_MASTER.DOC_ID` 참조 |
| `CONTENT` | TEXT | NOT NULL | 청크된 실제 텍스트 내용 |
| `PAGE_NO` | INT | - | 원본 문서 내 페이지 번호 |
| `CHUNK_SEQ` | INT | - | 문서 내 청크 순서 |
| `VECTOR_ID` | VARCHAR(128) | UNIQUE, INDEX | Vector DB 내 식별자 |
| `TOKEN_COUNT` | INT | - | 해당 청크의 토큰 수 |
| `REG_DT` | DATETIME | DEFAULT NOW() | 등록 일시 |

### 3.3 TB_EMB_MODEL
임베딩 모델의 버전과 차원 정보를 관리합니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `MODEL_ID` | VARCHAR(50) | PK | 임베딩 모델 식별자 |
| `MODEL_NAME` | VARCHAR(100) | NOT NULL | 모델명 |
| `PROVIDER` | VARCHAR(50) | - | OpenAI, Local, HuggingFace 등 |
| `DIMENSION` | INT | NOT NULL | 임베딩 벡터 차원 |
| `VERSION` | VARCHAR(50) | - | 모델 버전 |
| `IS_ACTIVE` | BOOLEAN | DEFAULT TRUE | 활성 여부 |
| `REG_DT` | DATETIME | DEFAULT NOW() | 등록 일시 |

### 3.4 TB_VECTOR_MAPPING
Vector DB 엔진 및 컬렉션 정보를 관리합니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `VECTOR_ID` | VARCHAR(128) | PK | Vector DB 내 고유 ID |
| `CHUNK_ID` | VARCHAR(36) | FK, INDEX | `TB_DOC_CHUNK.CHUNK_ID` 참조 |
| `ENGINE_TYPE` | VARCHAR(20) | - | CHROMA, FAISS, ELASTIC 등 |
| `COLLECTION_NAME` | VARCHAR(100) | - | Vector DB 내 컬렉션 또는 인덱스 명 |
| `MODEL_ID` | VARCHAR(50) | FK | `TB_EMB_MODEL.MODEL_ID` 참조 |
| `REG_DT` | DATETIME | DEFAULT NOW() | 등록 일시 |

### 3.5 TB_QA_FEEDBACK
답변 품질 개선을 위한 사용자 피드백을 저장합니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `FEEDBACK_ID` | VARCHAR(36) | PK | 피드백 고유 식별자 |
| `QUERY_ID` | VARCHAR(36) | INDEX | 질의 추적 식별자 |
| `USER_ID` | VARCHAR(100) | - | 사용자 식별자 |
| `TENANT_ID` | VARCHAR(50) | INDEX | 테넌트 식별자 |
| `RATING` | VARCHAR(20) | - | LIKE, DISLIKE 등 |
| `COMMENT` | TEXT | - | 사용자 의견 |
| `REG_DT` | DATETIME | DEFAULT NOW() | 등록 일시 |

### 3.6 데이터 격리 정책
* 모든 문서 조회, 검색, 피드백 쿼리는 `TENANT_ID`를 기본 필터로 사용합니다.
* Vector DB 검색 시에도 테넌트 필터 또는 컬렉션 분리 정책을 적용합니다.
* Vector DB에서 반환된 `VECTOR_ID`는 `TB_DOC_CHUNK` 및 `TB_DOC_MASTER`와 조인하여 원문과 메타데이터를 복원합니다.

## 4. API 인터페이스 명세

### 4.1 공통 스펙
| 항목 | 기준 |
| :--- | :--- |
| Protocol | HTTPS RESTful API |
| Data Format | JSON UTF-8 |
| Base Path | `/api/v1` |
| Authentication | Bearer Token(JWT) |

### 4.2 문서 업로드 및 인덱싱
`POST /api/v1/ingest/upload`

새로운 문서를 시스템에 등록하고 백그라운드 인덱싱 작업을 시작합니다.

**Request Parameters**

| 필드 | 타입 | 필수 | 설명 |
| :--- | :--- | :--- | :--- |
| `file` | Multipart file | Y | PDF, DOCX, TXT 등 |
| `metadata` | JSON string | N | 작성자, 카테고리, 테넌트 등 |

**Response Body**

```json
{
  "task_id": "ingest_789",
  "status": "processing",
  "message": "문서 업로드 완료. 백그라운드 인덱싱이 시작되었습니다."
}
```

### 4.3 인덱싱 상태 조회
`GET /api/v1/ingest/status/{task_id}`

비동기로 진행되는 문서 인덱싱 작업의 진행률과 결과를 조회합니다.

**Response Body**

```json
{
  "task_id": "ingest_789",
  "progress": 75,
  "status": "COMPLETED",
  "result": {
    "doc_id": "doc_002",
    "chunk_count": 42
  }
}
```

### 4.4 하이브리드 질의
`POST /api/v1/query/hybrid`

Vector 검색과 BM25 키워드 검색을 결합하고, 리랭킹을 거쳐 근거 기반 답변을 생성합니다.

**Request Body**

```json
{
  "question": "주문 취소 정책에 대해 알려줘",
  "user_id": "user123",
  "top_k": 5,
  "filters": {
    "tenant_id": "HNI_01",
    "category": "policy"
  }
}
```

**Response Body**

```json
{
  "query_id": "query_456",
  "answer": "주문 취소는 결제 후 24시간 이내에 가능합니다. [1]",
  "status": "success",
  "source_documents": [
    {
      "source_no": 1,
      "doc_id": "doc_001",
      "file_name": "운영규정.pdf",
      "page_no": 12,
      "snippet": "주문 취소는 결제 후 24시간 이내에만 가능합니다.",
      "score": 0.89
    }
  ],
  "confidence_score": 0.89
}
```

### 4.5 피드백 등록
`POST /api/v1/feedback`

사용자의 추천, 비추천, 의견을 수집하여 리랭킹 모델 학습 또는 프롬프트 개선에 활용합니다.

**Request Body**

```json
{
  "query_id": "query_456",
  "user_id": "user123",
  "tenant_id": "HNI_01",
  "rating": "LIKE",
  "comment": "근거가 명확합니다."
}
```

**Response Body**

```json
{
  "feedback_id": "feedback_001",
  "status": "success"
}
```

### 4.6 Pydantic 데이터 모델

```python
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class QaRequest(BaseModel):
    question: str
    user_id: str = "guest"
    top_k: int = 3
    filters: Optional[Dict[str, Any]] = None


class SourceDocument(BaseModel):
    source_no: int
    doc_id: str
    file_name: str
    page_no: Optional[int] = None
    snippet: str
    score: Optional[float] = None


class QaResponse(BaseModel):
    query_id: str
    answer: str
    source_documents: List[SourceDocument]
    status: str = "success"
    confidence_score: float
```

### 4.7 오류 코드
| 코드 | 메시지 | 설명 |
| :--- | :--- | :--- |
| `E001` | `AUTH_FAILED` | 인증 토큰이 누락되거나 만료됨 |
| `E101` | `DOC_PARSE_ERR` | 문서 파일 형식 오류 또는 텍스트 추출 불가 |
| `E102` | `DOC_INDEX_ERR` | 문서 청킹, 임베딩, 저장 중 오류 |
| `E201` | `LLM_TIMEOUT` | LLM 모델 서버 응답 지연 |
| `E202` | `NO_CONTEXT` | 답변 생성을 위한 유효 컨텍스트 없음 |
| `E301` | `TENANT_FORBIDDEN` | 테넌트 접근 권한 없음 |

## 5. RAG 파이프라인 설계

### 5.1 인제스션 전략
문서 인제스션은 텍스트 추출, 동적 청킹, 임베딩, Vector DB 저장, RDBMS 메타데이터 저장 순서로 수행합니다. 각 단계의 실패 상태는 `TB_DOC_MASTER.STATUS`와 인덱싱 상태 API를 통해 추적합니다.

### 5.2 동적 청킹
문서의 의미적 단위를 유지하기 위해 고정 길이 대신 구조 기반 청킹을 적용합니다.

| 항목 | 기준 |
| :--- | :--- |
| Strategy | `RecursiveCharacterTextSplitter` |
| Separators | `["\n\n", "\n", ".", " ", ""]` |
| Chunk Size | 500~800 tokens |
| Overlap | 10~15% |

### 5.3 임베딩 모델 전략
* 한국어와 다국어 문서가 섞이는 환경에서는 BGE-M3, KoSimCSE 등 한국어 또는 다국어 지원 모델을 우선 검토합니다.
* 차원 수는 768 또는 1024를 기본 후보로 두고, 성능과 저장 공간의 균형을 기준으로 선택합니다.
* 사용한 모델은 `TB_EMB_MODEL`에 등록하고, 각 벡터는 `TB_VECTOR_MAPPING.MODEL_ID`로 추적합니다.

### 5.4 하이브리드 검색
하이브리드 검색은 의미 기반 Vector 검색과 키워드 기반 BM25 검색을 결합합니다.

* 고유 명사, 코드, 정책명, 상품명처럼 정확한 어휘 일치가 중요한 질의는 BM25가 보완합니다.
* 유사 표현, 문맥 기반 질문, 자연어 질의는 Vector 검색이 보완합니다.
* 두 검색 결과는 Reciprocal Rank Fusion(RRF)으로 통합합니다.

```text
Score = 1 / (Vector_Rank + k) + 1 / (BM25_Rank + k)
k = 60
```

### 5.5 리랭킹
1차 검색된 후보군은 Cross-Encoder 계열 모델을 사용하여 재정렬합니다.

| 항목 | 기준 |
| :--- | :--- |
| 후보 수 | 기본 N=20 |
| 모델 | BGE-Reranker 등 Cross-Encoder 계열 |
| 입력 | `(Query, Chunk)` 쌍 |
| 출력 | 0~1 범위의 관련성 점수 |

### 5.6 답변 생성 정책
LLM은 리랭킹된 컨텍스트만 근거로 답변을 생성합니다.

* 제시된 컨텍스트에 근거가 없으면 "모릅니다"라고 답변합니다.
* 답변 본문에는 반드시 `[1]`, `[2]` 형태의 근거 번호를 포함합니다.
* 전문 용어는 필요한 경우 한글과 영문을 병기합니다.
* 답변과 근거 문서의 연결은 `source_documents.source_no`로 관리합니다.

### 5.7 인용 및 근거 제시
* 답변 본문에는 `[1]`, `[2]` 형태의 간결한 인용 번호를 표시합니다.
* API 응답의 `source_documents`에는 문서명, 페이지 번호, 스니펫, 점수를 포함합니다.
* UI에서는 인용 번호 클릭 시 해당 원문 청크를 하이라이트 표시합니다.

## 6. 운영 및 모니터링

### 6.1 피드백 루프
사용자의 추천, 비추천, 의견은 `TB_QA_FEEDBACK`에 저장합니다. 누적된 피드백은 다음 개선 작업에 활용합니다.

* 리랭킹 모델 학습 데이터 후보 선정
* 프롬프트 개선
* 문서 품질 개선 대상 식별
* 자주 실패하는 질의 유형 분석

### 6.2 평가 지표
| 지표 | 설명 |
| :--- | :--- |
| Faithfulness | 답변이 실제 컨텍스트에 기반하는지 |
| Answer Relevance | 질문에 직접 답하고 있는지 |
| Context Precision | 검색 결과 중 실제 유용한 정보의 비율 |
| Citation Coverage | 답변 문장 중 근거가 연결된 비율 |
| No-answer Rate | "모릅니다" 응답 비율 |
| Feedback Score | 사용자 추천/비추천 기반 품질 점수 |

### 6.3 시스템 모니터링 항목
| 항목 | 설명 |
| :--- | :--- |
| Ingestion Latency | 문서 업로드부터 인덱싱 완료까지 걸린 시간 |
| Retrieval Latency | Vector/BM25 검색 소요 시간 |
| Rerank Latency | 리랭킹 소요 시간 |
| Generation Latency | LLM 답변 생성 소요 시간 |
| Error Rate | API 및 파이프라인 단계별 오류율 |
| Token Usage | 질의별 입력/출력 토큰 사용량 |

## 7. 구현 정합성 체크리스트
* `POST /api/v1/query/hybrid` 응답 필드는 `source_documents`를 사용한다.
* `POST /api/v1/ingest/upload`와 `GET /api/v1/ingest/status/{task_id}`를 문서 인덱싱 표준 API로 사용한다.
* `TB_DOC_MASTER`에는 `FILE_TYPE`, `FILE_SIZE`, `STATUS`, `TENANT_ID`를 포함한다.
* `TB_EMB_MODEL`과 `TB_VECTOR_MAPPING`을 통해 임베딩 모델과 Vector DB 매핑을 추적한다.
* 모든 검색 및 조회에는 `TENANT_ID` 기반 데이터 격리를 적용한다.
* 답변 본문 인용은 `[1]`, `[2]` 형식으로 통일한다.
* 상세 근거는 `source_documents` 배열에서 제공한다.
* 피드백 API와 `TB_QA_FEEDBACK`을 운영 개선 루프에 포함한다.
