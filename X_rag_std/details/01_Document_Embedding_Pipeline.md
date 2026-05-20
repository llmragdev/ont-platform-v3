# 상세설계 01: 임베딩 대상 문서 관리 파이프라인 (v1.2)

## 1. 개요
본 문서는 RAG 기본 설계에 따라 문서가 시스템에 업로드되어 파싱, 청킹, 임베딩을 거쳐 벡터 DB에 물리적으로 격리·적재되기까지의 상세 처리 로직과 인터페이스를 정의합니다.
* **적용 표준**: 파이썬 PEP 8 (`snake_case`), FastAPI 및 Pydantic 기반 스키마

---

## 2. 인터페이스 명세 (Document API)

### 2.1. 문서 업로드 및 적재 요청 (`POST /api/v1/documents/upload`)
사용자 또는 연동 시스템이 문서를 업로드하고 파이프라인(비동기)을 트리거합니다.

* **Content-Type**: `multipart/form-data`
* **Header**: `X-Tenant-ID: {tenant_id}` (필수), `X-Org-ID: {org_id}` (선택 — 조직 단위 격리)
* **Request 파라미터**:
  * `file`: 바이너리 파일 객체 (PDF, DOCX 등)
  * `category_mid`: 중분류 카테고리 (필수 - 라우팅 목적)
  * `category_low`: 소분류 카테고리 (선택)
  * `vector_db_id`: 물리적으로 강제할 대상 Vector DB ID (선택 - 미입력 시 `category_mid` 기반 자동 할당)

* **Response (Pydantic Model: `DocumentUploadResponse`)**:
```json
{
  "status": "success",
  "data": {
    "doc_id": "doc_5f2b8a",
    "file_name": "2026_인사규정.pdf",
    "pipeline_status": "pending",
    "assigned_vector_db": "vdb_policy_01"
  },
  "error": null
}
```

---

## 3. 파이프라인 상태 전이 로직 (State Management)
대용량 파일 임베딩 중 시스템이 다운되거나 지연되는 상황을 방지하기 위해 문서는 다음과 같은 상태값을 가집니다. (RDBMS 또는 메타데이터 DB에 기록)

1. `pending`: 파일이 S3/로컬 등 물리적 스토리지에 업로드 완료됨. (대기열 진입)
2. `processing`: 파서(Parser)가 텍스트를 추출하고 청킹한 뒤, 중앙화된 **LLM Gateway** API를 호출하여 임베딩 중임. (비동기 스레드 풀 적용)
3. `completed`: 모든 청크가 벡터 DB에 성공적으로 적재됨.
4. `error`: 파싱 실패 또는 LLM Gateway 통신 타임아웃 발생. (`error_message`에 상세 사유 기록)

---

## 4. 청킹 및 임베딩 상세 전략 (Chunking Strategy)

### 4.1. 텍스트 분할 (Text Splitter) 설정
한국어 문서 특성을 반영하여 문맥이 끊기지 않도록 Recursive Character Text Splitter를 기본으로 사용합니다.
* `chunk_size`: 500 ~ 800 **문자(character)** — 한국어 1문자 ≈ 1~2토큰 기준 (LLM Context 윈도우 및 임베딩 모델 제한 고려)
* `chunk_overlap`: 50 ~ 100 **문자(character)** (문단 간 문맥 단절 방지)
* **메타데이터 부착**: 쪼개진 모든 청크 데이터에는 `{doc_id}#{chunk_index}` 형태의 ID와 `page_no`(실제 PDF 페이지 번호), `tenant_id`(필수), `org_id`(선택), `dept_code`(org_id 존재 시 필수)가 딕셔너리로 부착됩니다.

### 4.2. 증분 업데이트 (Incremental Update) 로직
기존에 적재된 문서의 수정본이 업로드될 경우(`PUT /api/v1/documents/{doc_id}`), 전체 벡터 DB를 밀어버리지 않고 해당 문서에 국한된 증분 업데이트를 수행합니다.
1. 메타데이터 필터(`doc_id == "기존ID"`)를 통해 대상 벡터 DB에서 기존 청크들을 일괄 삭제(Delete). → `BaseVectorDbAdapter.delete_by_doc_id()` 사용 (상세설계 02 참조)
2. 새로 업로드된 문서로 파이프라인을 재가동하여 새로운 청크를 인서트(Insert).
3. 버전을 `v1` -> `v2`로 갱신하고 상태를 `completed`로 변경.

---

## 5. 비동기 파이프라인 구현 패턴

### 5.1. asyncio.to_thread 적용 범위
FastAPI `async def` 라우터 내부에서 동기(blocking) I/O를 직접 호출하면 이벤트 루프가 블로킹되어 다른 요청을 처리하지 못합니다. 다음 작업은 반드시 `asyncio.to_thread()`로 스레드 풀에 위임합니다.

* 문서 파싱 (pypdf, python-docx 등 동기 라이브러리)
* 텍스트 청킹 및 전처리
* LLM Gateway HTTP 호출 (동기 httpx/requests 클라이언트 사용 시)
* Vector DB 삽입·검색 (동기 드라이버 사용 시)

```python
# 권장 패턴
result = await asyncio.to_thread(sync_pipeline_fn, file_bytes, category_mid)
```

### 5.2. SQLAlchemy Session 스레드 분리 원칙
SQLAlchemy 동기 `Session`은 **thread-safe하지 않습니다.** `asyncio.to_thread()`로 실행되는 worker 함수에 요청 스레드의 Session을 그대로 전달하면 운영 환경에서 간헐적인 DB 오류·세션 꼬임이 발생합니다.

```python
# 금지 — 요청 스레드 Session을 worker thread에 전달
await asyncio.to_thread(pipeline_fn, db_from_request)  # ❌

# 권장 A — worker thread 내부에서 새 Session 생성
def pipeline_fn(file_bytes: bytes):
    with SessionLocal() as db:          # worker 내에서 독립 세션
        doc_repo = DocumentRepository(db)
        ...
await asyncio.to_thread(pipeline_fn, file_bytes)  # ✅

# 권장 B — 순수 계산(파싱/임베딩)만 thread로 분리, DB 업데이트는 request thread에서 처리
chunks = await asyncio.to_thread(extract_and_chunk, file_bytes)  # ✅ DB 없음
doc_repo.set_status(doc_id, "completed")                          # ✅ request thread
```
