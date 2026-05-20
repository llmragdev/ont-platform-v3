# RAG 표준 v1.3 코드 평가 보고서 — 샘플 (작성: Claude)

작성일: 2026-05-15  
작성자: Claude Code (src_claud/v3)  
평가 기준: `RAG_표준_설계_v1.3.md`

> **이 문서는 양식 샘플이다.**  
> Codex, Antigravity는 이 구조와 표기 방식 그대로 자신의 보고서를 작성한다.  
> 양식 가이드: `00_평가_가이드_타에이전트용.md`

---

## Part 1. 자기 코드 평가 (src_claud/v3)

### 1-A. v1.3 항목별 준수 현황

| v1.3 항목 | 준수 | 근거 파일:라인 | 비고 |
|-----------|:----:|--------------|------|
| §3.1 X-Tenant-ID 필수 (누락 시 400) | ✅ | `app/api/deps.py:12` | `get_tenant_id` Depends |
| §3.1 X-Org-ID 선택 수신 | ✅ | `app/api/deps.py:20` | `Header(default=None)` |
| §3.2 OR 조건 검색 (팀+공유, 부서+공유) | ✅ | `app/services/search_service.py:58` | `_build_where_clause()` |
| §2.3 org_id/dept_code 메타데이터 저장 | ✅ | `app/services/document_service.py:112` | pipeline 메타 생성 |
| §2.3 전사 공유 org_id="" sentinel | ✅ | `app/services/document_service.py:108` | `org_id or ""` |
| §4 ca_org_mgnt 복합 PK (tenant_id, org_id) | ✅ | `app/models/db_models.py:22` | `mapped_column(primary_key=True)` x2 |
| §2.3 tags → vector metadata 제외 | ✅ | `app/services/document_service.py:115` | metadata dict에 tags 키 없음 |
| §2.2 embeddings= 명시 전달 | ✅ | `app/services/vector_adapters.py:34` | pipeline → adapter 전달 |
| §2.1 asyncio.to_thread 비동기 파이프라인 | ✅ | `app/services/document_service.py:88` | `asyncio.create_task(asyncio.to_thread(...))` |
| §2.1 pipeline_status "pending" 즉시 반환 | ✅ | `app/services/document_service.py:94` | create_task 후 즉시 return |
| §1.1 Gateway 호출에 tenant_id 전달 | ✅ | `app/services/llm/claude_llm.py:28` | `tenant_id=tenant_id` 파라미터 |
| §2.3 page_no 실제 PDF 페이지 번호 | ✅ | `app/services/document_service.py:65` | pypdf `enumerate(reader.pages)` |
| §2.1 chunk_size 700, overlap 80 | ✅ | `app/services/chunking.py:8` | 상수 선언 |
| §5 임베딩 Fallback 금지 | ✅ | `app/services/embedding/claude_embedding.py:22` | 예외 그대로 raise |
| §5 Index Swap Pattern | ❌ | 미구현 | v3 설계에 없음 |
| SSE 스트리밍 검색 | ✅ | `app/api/search.py:45` | `StreamingResponse` + async generator |
| debug_mode candidate_chunks 분리 | ✅ | `app/services/search_service.py:90` | debug_mode 조건부 반환 |
| 감사 로그 (AuditLog) | ✅ | `app/models/db_models.py:95` | `wc_audit_log` 테이블 |
| datetime timezone-aware | ✅ | `app/models/db_models.py:18` | `lambda: datetime.now(timezone.utc)` |
| 테스트 외부 의존 없음 | ✅ | `tests/conftest.py:49` | in-memory DB + mock provider |

**자기 준수율: 19 / 20 항목 (95%)**

---

### 1-B. 미준수 항목 개선 계획

#### §5 Index Swap Pattern

**현재 상태:** 미구현. 재색인 시 기존 컬렉션에 직접 덮어쓰므로 검색 서비스가 일시 중단될 수 있다.

**개선 코드 (src_antigravity/v3 `AdminService` 참조):**

```python
# app/services/admin_service.py (신규)
class AdminService:
    def perform_index_swap(self, tenant_id: str, vector_db_id: str, new_collection_name: str):
        """
        1. 새 컬렉션에 재색인 완료
        2. routing.json의 vector_db_id 매핑을 atomic하게 교체
        3. 구 컬렉션 삭제
        """
        router = VectorDbRouter()
        router.swap_collection(vector_db_id, new_collection_name)
```

**구현 우선순위:** 중 (운영 전 필수, 개발 환경에서는 무관)

---

## Part 2. 타 에이전트 코드 평가

### 2-A. src_antigravity/v3 개선 제안

| 우선순위 | v1.3 항목 | 파일:라인 | 현재 코드 | 개선 코드 |
|---------|-----------|---------|----------|----------|
| 🔴 1 | §테스트 격리 | `core/config.py:1` | `from pydantic_settings import BaseSettings` (미설치 → ImportError) | `requirements.txt`에 `pydantic-settings>=2.0` 추가 + Gateway mock |
| 🔴 2 | §2.2 embedding boundary | `services/vector_db.py:27` | `self.gateway.embed_text(text, ...)` adapter 내부 호출 | pipeline이 생성 후 `adapter.add_documents(..., embeddings=embs)` 전달 |
| 🟠 3 | §2.3 org_id sentinel | `services/vector_db.py:60` | `meta.get("org_id") is None` | `meta.get("org_id") == ""` |
| 🟡 4 | §2.1 pending 즉시 반환 | `api/documents.py:33` | `doc_record = await asyncio.to_thread(run_pipeline)` (완료 대기) | `asyncio.create_task(...)` fire-and-forget → "pending" 반환 |
| 🟡 5 | §datetime | `models/db_models.py:13` | `default=datetime.utcnow` | `default=lambda: datetime.now(timezone.utc)` |
| 🟡 6 | FastAPI lifespan | `main.py:8` | `@app.on_event("startup")` deprecated | `@asynccontextmanager async def lifespan(app)` |

**상세 before/after:**

```python
# [🔴 2] services/vector_db.py — BEFORE
def add_documents(self, texts, metadatas):
    for text, meta in zip(texts, metadatas):
        embedding = self.gateway.embed_text(text, tenant_id=meta.get("tenant_id"))
        # ↑ adapter가 Gateway 직접 호출 — boundary 위반

# AFTER
def add_documents(self, texts, metadatas, embeddings):  # embeddings 파라미터 추가
    for text, meta, emb in zip(texts, metadatas, embeddings):
        data.append({"content": text, "metadata": meta, "embedding": emb})
```

```python
# [🟠 3] services/vector_db.py — BEFORE
if meta.get("org_id") is None:   # None 판별
    match = True

# AFTER
if meta.get("org_id") == "":     # "" sentinel (Chroma 전환 대비)
    match = True
```

---

### 2-B. src_codex 개선 제안

| 우선순위 | v1.3 항목 | 파일:라인 | 현재 코드 | 개선 코드 |
|---------|-----------|---------|----------|----------|
| 🔴 1 | §3.1 X-Tenant-ID 필수 | `app/api/documents.py:21` | `request.headers.get("X-Company-ID", "default")` | `Depends(get_tenant_id)` — 누락 시 400 |
| 🔴 2 | §2.1 asyncio.to_thread | `app/services/document_pipeline.py:48` | `self._run_pipeline(record, raw_path)` 동기 블로킹 | `asyncio.create_task(asyncio.to_thread(_run_pipeline_isolated, ...))` |
| 🟠 3 | §3.2 OR 조건 검색 | `app/services/rag_service.py` | org_id 계층 없음, company_id 1차원 | `_build_where_clause(tenant_id, org_id)` OR 조건 |
| 🟠 4 | §2.3 tags 제외 | `app/services/document_pipeline.py:123` | `"tags": []` vector metadata에 포함 | metadata dict에서 tags 키 제거 |
| 🟡 5 | §2.3 page_no | `app/services/document_pipeline.py:118` | `"page_no": index + 1` chunk 인덱스 기반 | pypdf `enumerate(reader.pages)` → 실제 페이지 번호 |
| 🟡 6 | §4 FK 선언 | `app/models/db_models.py:63` | FK 없음 | `ForeignKey("wc_project.project_code")` 추가 |
| 🟡 7 | §datetime | `app/models/db_models.py:77` | `default=datetime.utcnow` | `default=lambda: datetime.now(timezone.utc)` |

**상세 before/after:**

```python
# [🔴 1] app/api/documents.py — BEFORE
def _company_id(request: Request) -> str:
    return request.headers.get("X-Company-ID", "default")  # 보안 결함

# AFTER
from fastapi import Header, HTTPException

def get_tenant_id(x_tenant_id: str | None = Header(default=None)) -> str:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is required")
    return x_tenant_id
```

```python
# [🟠 4] app/services/document_pipeline.py — BEFORE
metadata_payloads.append({
    ...
    "tags": [],  # vector metadata에 저장 금지

# AFTER
metadata_payloads.append({
    "doc_id": record.doc_id,
    "tenant_id": tenant_id,
    "source_name": record.file_name,
    "page_no": page_no,
    "category_mid": record.category_mid,
    # tags 없음
})
```

---

## Part 3. 종합 점수 (자기 판단)

| 에이전트 | 점수 | 주요 강점 | 주요 약점 |
|---------|------|---------|---------|
| src_claud/v3 (자기) | **9.0 / 10** | 테스트 완전 격리 17/17, v1.3 준수율 최고 | Index Swap 미구현 |
| src_antigravity/v3 | **7.0 / 10** | Index Swap 유일 구현, asyncio 정상 | 테스트 실행 불가, embedding boundary 위반 |
| src_codex | **6.8 / 10** | Chroma embeddings= 안정, SSE 구현 | X-Tenant-ID 선택, 동기 블로킹, org_id 계층 없음 |
