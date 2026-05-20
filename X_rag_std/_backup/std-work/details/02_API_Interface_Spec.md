# AI 에이전트 표준 인터페이스 상세 명세서 (v1.0)

## 1. 개요
본 문서는 AI 에이전트 시스템의 API 규격 및 데이터 교환 모델을 정의합니다. 기존 `ai_solution_development_standard.md`의 개발 표준과 `가이드 자료 배포 - 20240401`의 `WC_인터페이스명세서`를 통합하여 설계되었습니다.

## 2. 공통 스펙
*   **Protocol**: HTTPS (RESTful API)
*   **Data Format**: JSON (UTF-8)
*   **Base Path**: `/api/v1`
*   **Authentication**: Bearer Token (JWT)

## 3. 핵심 API 명세

### 3.1 하이브리드 질의 (`POST /query/hybrid`)
의미적 검색(Vector)과 키워드 검색(BM25)을 결합하여 최적의 답변을 생성합니다.

**Request Body:**
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

**Response Body:**
```json
{
  "answer": "HNiX의 주문 취소 정책에 따르면...",
  "status": "success",
  "source_documents": [
    {
      "doc_id": "doc_001",
      "file_name": "운영규정.pdf",
      "page_no": 12,
      "snippet": "...주문 취소는 결제 후 24시간 이내에만 가능합니다..."
    }
  ],
  "confidence_score": 0.89
}
```

### 3.2 문서 업로드 및 인덱싱 (`POST /ingest/upload`)
새로운 문서를 시스템에 등록하고 벡터 인덱싱을 수행합니다.

**Request Parameters:**
*   `file`: Multipart/form-data (PDF, DOCX)
*   `metadata`: JSON string (작성자, 카테고리 등)

**Response Body:**
```json
{
  "task_id": "ingest_789",
  "status": "processing",
  "message": "문서 업로드 완료. 백그라운드 인덱싱이 시작되었습니다."
}
```

### 3.3 작업 상태 조회 (`GET /ingest/status/{task_id}`)
비동기로 진행되는 인덱싱 작업의 진행률을 조회합니다.

**Response Body:**
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

## 4. 데이터 모델 (Pydantic)
기존 개발 표준을 준수하는 공통 모델 정의입니다.

```python
class QaRequest(BaseModel):
    question: str
    user_id: str = "guest"
    top_k: int = 3
    filters: Optional[Dict[str, Any]] = None

class SourceDoc(BaseModel):
    doc_id: str
    file_name: str
    page_no: Optional[int]
    snippet: str

class QaResponse(BaseModel):
    answer: str
    source_documents: List[SourceDoc]
    status: str = "success"
    confidence_score: float
```

## 5. 오류 코드 규격
| 코드 | 메시지 | 설명 |
| :--- | :--- | :--- |
| `E001` | `AUTH_FAILED` | 인증 토큰이 누락되거나 만료됨 |
| `E101` | `DOC_PARSE_ERR` | 문서 파일 형식 오류 또는 텍스트 추출 불가 |
| `E201` | `LLM_TIMEOUT` | LLM 모델 서버의 응답 지연 |
