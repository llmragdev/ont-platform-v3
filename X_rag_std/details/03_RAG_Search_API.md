# 상세설계 03: RAG 검색 및 역매핑 API (v1.3)

## 1. 개요
본 문서는 Agent/Orchestrator가 RAG 백엔드에 쿼리를 전송하고, Vector DB의 후보군과 최종 출처/페이지가 명시된 결과를 반환받는 "Remote Retriever" 패턴의 상세 API 명세 및 파이썬 코드 구조를 정의합니다.

---

## 2. API 상세 인터페이스 (FastAPI & Pydantic)

### 2.1. Request Model
```python
from pydantic import BaseModel
from typing import Optional

class RagSearchFilter(BaseModel):
    category_mid: Optional[str] = None
    vector_db_id: Optional[str] = None

class RagSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    debug_mode: bool = False
    filters: Optional[RagSearchFilter] = None
```

### 2.2. Response Model
```python
from pydantic import BaseModel
from typing import List, Optional

class ChunkMetadata(BaseModel):
    source_name: str
    source_url: str
    page_no: Optional[int] = None        # 실제 PDF 페이지 번호 (chunk 순번 아님)
    category_mid: str
    vector_db_id: str
    tenant_id: str                       # 회사 단위 테넌트 구분자 (필수)
    org_id: Optional[str] = None         # 조직 코드 ex: "0102" (선택)
    dept_code: Optional[str] = None      # org_id 앞 2자리 파생값 (org_id 존재 시 필수)
    created_at: Optional[str] = None     # ISO 8601 timezone-aware

class RetrievedChunk(BaseModel):
    chunk_id: str
    content: str
    metadata: ChunkMetadata
    similarity_score: float

class DebugInfo(BaseModel):
    execution_time_ms: int
    candidate_chunks: List[RetrievedChunk]

class RagSearchData(BaseModel):
    query: str
    answer: str
    used_chunks: List[RetrievedChunk]
    debug_info: Optional[DebugInfo] = None

class RagSearchResponse(BaseModel):
    status: str
    data: RagSearchData
    error: Optional[str] = None
```

---

## 3. Remote Retriever 패턴 작동 방식

1. **Controller 계층**: `RagSearchRequest` 수신 + `X-Tenant-ID` 헤더에서 `tenant_id` 추출 (누락 시 400 반환), `X-Org-ID` 헤더에서 `org_id` 추출 (없으면 기본설계 2.5항 정책 적용).
2. **Service 계층 (DB 라우팅)**: `filters.category_mid`를 확인하여 02번 상세설계에서 정의된 라우터 객체를 통해 대상 Vector DB의 Adapter 획득.
3. **Retrieval**: Adapter의 `search()` 호출 시 검색 필터에 tenant_id·org_id 강제 주입. 팀·부서 검색 시 전사 공유 문서(`org_id IS NULL`)를 포함합니다:
   ```python
   # 팀 단위 검색 (X-Org-ID: 0102)
   # → 해당 팀 문서 + 전사 공유 문서(org_id IS NULL) 포함
   filters["tenant_id"] = tenant_id
   filters["$or"] = [{"org_id": org_id}, {"org_id": None}]

   # 부서 단위 검색 (X-Org-ID: 0100 — 부서 공통 소유 코드)
   # → 해당 부서 문서 + 전사 공유 문서(org_id IS NULL) 포함
   filters["tenant_id"] = tenant_id
   filters["$or"] = [{"dept_code": dept_code}, {"org_id": None}]

   # 전사 검색 (관리자/시스템 전용, X-Org-ID 없음)
   filters["tenant_id"] = tenant_id    # tenant_id만 (org_id IS NULL 포함 불필요)
   ```
4. **LLM Generation**: 후보 청크의 `content`를 모아 Prompt Context를 구성한 뒤, 중앙화된 **LLM Gateway** API를 호출하여 응답 생성. 요청 body에 `tenant_id` 포함 (4항 참조).
5. **Reverse Mapping 및 조립**: LLM이 채택한 청크만 `used_chunks`로 필터링. `debug_mode=True`일 경우 전체 `candidate_chunks`를 `debug_info`에 조립.
6. 프론트엔드로 최종 `RagSearchResponse` JSON 반환.

---

## 4. LLM Gateway API 연동 명세
RAG 백엔드가 LLM Gateway를 호출하는 두 가지 인터페이스입니다. API 키 관리는 Gateway 서버가 전담하며, RAG 백엔드는 `LLM_GATEWAY_URL` 환경변수만 보유합니다.

### 4.1. 임베딩 요청

* **Endpoint:** `POST /v1/embed`
* **Request:**
```json
{
  "text": "임베딩할 텍스트",
  "tenant_id": "company_abc"
}
```
* **Response:**
```json
{
  "embedding": [0.023, -0.145, "..."],
  "model": "text-embedding-004",
  "dimension": 768
}
```

### 4.2. 답변 생성 요청

* **Endpoint:** `POST /v1/generate`
* **Request:**
```json
{
  "query": "사용자 질의",
  "context_chunks": [
    {"content": "...", "source_name": "2026_AI_가이드.pdf", "page_no": 12}
  ],
  "tenant_id": "company_abc",
  "stream": false
}
```
* **Response (`stream: false`):**
```json
{
  "answer": "생성된 답변 텍스트",
  "model": "gemini-2.0-flash",
  "usage": {"input_tokens": 512, "output_tokens": 128}
}
```
* **Response (`stream: true`):** `text/event-stream` SSE 포맷 (5항 참조)

### 4.3. 공통 규칙
* `tenant_id`는 모든 요청에 필수 포함 — Gateway 테넌트별 감사 로그·쿼타 관리에 사용
* 타임아웃 기본값: `embed` 10초, `generate` 60초
* 실패 시 `embedding_api_timeout` 또는 `llm_generation_error` 예외 전파. **더미 벡터 반환(fallback) 금지**

---

## 5. 스트리밍 검색 API (SSE)

* **Endpoint:** `POST /api/v1/rag/search/stream`
* **Headers:** `X-Tenant-ID: {tenant_id}` (필수), `X-Org-ID: {org_id}` (선택)
* **Response Content-Type:** `text/event-stream`

### 5.1. SSE 이벤트 포맷

```
data: {"type": "chunk", "text": "2026년 인사 규정에"}

data: {"type": "chunk", "text": " 따르면..."}

data: {"type": "done", "used_chunks": [...], "execution_time_ms": 420}

data: {"type": "error", "error_code": "llm_generation_error", "message": "..."}
```

### 5.2. FastAPI 구현 패턴

```python
from fastapi.responses import StreamingResponse
import json

@router.post("/rag/search/stream")
async def stream_search(
    request: RagSearchRequest,
    tenant_id: str = Depends(get_tenant_id),
    org_id: str | None = Depends(get_org_id)
):
    async def event_generator():
        try:
            async for token in llm_client.stream_answer(request.query, chunks, tenant_id):
                yield f"data: {json.dumps({'type': 'chunk', 'text': token})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'used_chunks': [...]})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error_code': 'llm_generation_error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```
