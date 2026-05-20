# RAG 표준 v1.3 코드 평가 보고서 — 작성: Codex

작성일: 2026-05-15  
작성자: Codex (`src_agents/src_codex/v3`)  
평가 기준: `RAG_표준_설계_v1.3.md`  
참조 양식: `src_agents/cross-코드-평가/v03-2 평가 v1.2/00_평가_가이드_타에이전트용.md`, `src_agents/cross-코드-평가/v03-2 평가 v1.2/Claude_04_표준평가보고서_샘플.md`

---

## Part 1. 자기 코드 평가

### 1-A. v1.3 항목별 준수 현황

| v1.3 항목 | 준수 | 근거 파일:라인 | 비고 |
|-----------|:----:|--------------|------|
| §3.1 X-Tenant-ID 필수 (누락 시 400) | ✅ | `app/api/dependencies.py:17` | 누락 시 `tenant_header_required` 400 |
| §3.1 X-Org-ID 선택 수신 | ✅ | `app/api/dependencies.py:21` | 없으면 `org_id=None` 컨텍스트 |
| §3.2 OR 조건 검색 (팀+공유, 부서+공유) | ✅ | `app/services/rag_service.py:105` | `__org_or_null__` 정책 생성 |
| §2.3 org_id/dept_code 메타데이터 저장 | ✅ | `app/services/document_pipeline.py:124` | `tenant_id`, `org_id`, `dept_code` 저장 |
| §2.3 전사 공유 `org_id=""` sentinel | ⚠️ | `app/services/vector_adapters.py:147` | Chroma는 `None→""`, Local JSON은 `None` 유지 |
| §4 ca_org_mgnt 복합 PK (tenant_id, org_id) | ✅ | `app/models/db_models.py:26` | `tenant_id`, `org_id` 모두 primary key |
| §2.3 tags → vector metadata 제외 | ⚠️ | `app/services/document_pipeline.py:134` | pipeline metadata에는 `tags`가 남고 Chroma 저장 시 제외 |
| §2.2 embeddings= 명시 전달 | ⚠️ | `app/services/vector_adapters.py:157` | Chroma `embeddings=`는 명시하나 adapter 내부에서 생성 |
| §2.1 asyncio.to_thread 비동기 파이프라인 | ❌ | `app/api/documents.py:32` | 업로드 요청이 pipeline 완료까지 대기 |
| §2.1 pipeline_status "pending" 즉시 반환 | ❌ | `tests/test_tenant_rag.py:48` | 테스트 기대값이 `completed` |
| §1.1 Gateway 호출에 tenant_id 전달 | ✅ | `app/services/gemini_http_embedding.py:23` | embed 요청 body에 `tenant_id` 포함 |
| §2.3 page_no 실제 PDF 페이지 번호 | ✅ | `app/services/document_pipeline.py:161` | `enumerate(reader.pages)` 기반 |
| §2.1 chunk_size 700, overlap 80 | ✅ | `app/services/chunking.py:5` | 기본값 700/80 |
| §5 임베딩 Fallback 금지 | ✅ | `app/services/gemini_http_embedding.py:26` | `raise_for_status()` 후 예외 전파 |
| §5 Index Swap Pattern | ❌ | `V3_ARCHITECTURE_DESIGN.md:315` | 설계만 있고 실행 API/서비스 없음 |
| SSE 스트리밍 검색 | ✅ | `app/api/rag.py:30` | `StreamingResponse` 사용 |
| debug_mode candidate_chunks 분리 | ✅ | `app/services/rag_service.py:62` | debug mode일 때만 candidate 반환 |
| 감사 로그 (AuditLog) | ❌ | `app/repositories/dialog_repository.py:21` | 대화 이력은 있으나 감사 로그 테이블 없음 |
| datetime timezone-aware | ✅ | `app/models/db_models.py:11` | `datetime.now(UTC)` 사용 |
| 테스트 외부 의존 없음 | ✅ | `tests/conftest.py:24` | in-memory DB + hash/mock provider |

**자기 준수율: 14.5 / 20 항목 = 7.25 / 10**

검증 결과:

```text
src_codex/v3
python -m pytest -q
17 passed
```

---

### 1-B. 미준수 항목 개선 계획

#### §2.3 전사 공유 `org_id=""` sentinel

**현재 코드 (`app/services/document_pipeline.py:125`, `app/services/vector_adapters.py:104`):**

```python
metadata_payloads.append({
    "org_id": record.org_id,
})

if metadata.get("org_id") is None:
    return True
```

**개선 코드:**

```python
metadata_payloads.append({
    "org_id": record.org_id or "",
})

if metadata.get("org_id", "") == "":
    return True
```

**구현 우선순위:** 중간

#### §2.3 tags → vector metadata 제외

**현재 코드 (`app/services/document_pipeline.py:134`):**

```python
metadata_payloads.append({
    "chunk_type": "text",
    "tags": [],
})
```

**개선 코드:**

```python
metadata_payloads.append({
    "chunk_type": "text",
    # tags는 RDBMS/JSON document metadata에만 저장하고 vector metadata에서는 제외한다.
})
```

**구현 우선순위:** 중간

#### §2.2 embeddings= 명시 전달

**현재 코드 (`app/services/vector_adapters.py:138`):**

```python
def add_documents(self, chunks: list[dict], metadata: list[dict]) -> bool:
    embeddings = [
        self._embed_document(chunk["content"], meta)
        for chunk, meta in zip(chunks, metadata, strict=True)
    ]
    self.collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
```

**개선 코드:**

```python
def add_documents(self, chunks: list[dict], metadata: list[dict], embeddings: list[list[float]]) -> bool:
    self.collection.add(
        ids=[chunk["chunk_id"] for chunk in chunks],
        documents=[chunk["content"] for chunk in chunks],
        metadatas=metadata,
        embeddings=embeddings,
    )
```

**구현 우선순위:** 높음

#### §2.1 asyncio.to_thread 비동기 파이프라인

**현재 코드 (`app/api/documents.py:32`):**

```python
record = await service.upload_document(
    file=file,
    category_mid=category_mid,
    tenant_id=context.tenant_id,
    org_id=context.org_id,
)
```

**개선 코드:**

```python
record = service.create_pending_document(
    file=file,
    category_mid=category_mid,
    tenant_id=context.tenant_id,
    org_id=context.org_id,
)
asyncio.create_task(asyncio.to_thread(service.run_pipeline_isolated, record.doc_id))
```

**구현 우선순위:** 높음

#### §2.1 pipeline_status "pending" 즉시 반환

**현재 코드 (`tests/test_tenant_rag.py:48`):**

```python
assert upload.json()["data"]["pipeline_status"] == "completed"
```

**개선 코드:**

```python
assert upload.json()["data"]["pipeline_status"] == "pending"
eventually_assert_document_status(client, doc_id, "completed")
```

**구현 우선순위:** 높음

#### §5 Index Swap Pattern

**현재 코드 (`V3_ARCHITECTURE_DESIGN.md:315`):**

```python
# 설계 문서에 Index Swap 개념만 존재하고 실행 가능한 AdminService/API는 없음
```

**개선 코드:**

```python
class AdminService:
    def perform_index_swap(self, tenant_id: str, project_code: str) -> dict:
        new_vector_db_id = self.reindex_to_shadow_collection(tenant_id, project_code)
        self.router.swap(project_code=project_code, vector_db_id=new_vector_db_id)
        return {"project_code": project_code, "active_vector_db_id": new_vector_db_id}
```

**구현 우선순위:** 중간

#### 감사 로그 (AuditLog)

**현재 코드 (`app/repositories/dialog_repository.py:21`):**

```python
record = DialogHistory(
    tenant_id=tenant_id,
    org_id=org_id,
    query=query,
    answer=answer,
)
```

**개선 코드:**

```python
audit = AuditLog(
    tenant_id=tenant_id,
    action="rag.search",
    resource=query[:100],
    org_id=org_id,
)
self.db.add(audit)
```

**구현 우선순위:** 중간

---

## Part 2. 타 에이전트 코드 평가

### 2-A. src_claud/v3 개선 제안

| 우선순위 | v1.3 항목 | 파일:라인 | 현재 코드 | 개선 코드 |
|---------|-----------|---------|----------|----------|
| 🔴 1 | §2.3 page_no 실제 PDF 페이지 번호 | `app/services/pipeline/extractor.py:31` | `reader.pages`를 텍스트 하나로 병합 | `(page_no, text)` 목록 반환 후 chunk metadata에 page_no 저장 |
| 🟠 2 | §5 Index Swap Pattern | `app/services/` | AdminService 없음 | `AdminService.perform_index_swap()` 추가 |
| 🟠 3 | §4 운영 migration | `v3/` | Alembic migration 없음 | `migrations/versions/0001_initial.py` 추가 |
| 🟡 4 | §2.3 tags → vector metadata 제외 | `app/services/vector_db/local_json.py:44` | 주석상 local_json metadata에 tags 유지 가능 | 모든 vector metadata에서 tags 제외 |
| 🟡 5 | §3.1 공통 dependency | `app/api/search.py:12` | API별 `_get_tenant_id` 반복 | `app/api/deps.py` 공통 Depends로 통합 |

```python
# [🔴 1] app/services/pipeline/extractor.py — BEFORE
pages = [page.extract_text() or "" for page in reader.pages]
return "\n\n".join(p for p in pages if p.strip())
```

```python
# AFTER
return [
    (page_index + 1, page.extract_text() or "")
    for page_index, page in enumerate(reader.pages)
    if (page.extract_text() or "").strip()
]
```

```python
# [🟠 2] app/services/admin_service.py — AFTER
class AdminService:
    def perform_index_swap(self, tenant_id: str, project_code: str) -> dict:
        shadow_id = self.reindex_project_to_shadow(tenant_id, project_code)
        self.router.swap_project_vector_db(tenant_id, project_code, shadow_id)
        return {"project_code": project_code, "active_vector_db_id": shadow_id}
```

### 2-B. src_antigravity/v3 개선 제안

| 우선순위 | v1.3 항목 | 파일:라인 | 현재 코드 | 개선 코드 |
|---------|-----------|---------|----------|----------|
| 🔴 1 | §20 테스트 외부 의존 없음 | `services/vector_db.py:27` | 테스트 중 실제 Gateway embed 호출 | Gateway client fixture/mock 주입 |
| 🔴 2 | §2.2 embeddings= 명시 전달 | `services/vector_db.py:27` | adapter 내부에서 `self.gateway.embed_text()` 호출 | pipeline이 embeddings 생성 후 adapter에 전달 |
| 🟠 3 | §2.1 pending 즉시 반환 | `api/documents.py:33` | `await asyncio.to_thread(run_pipeline)`로 완료 대기 | pending record 반환 후 background task 실행 |
| 🟠 4 | §2.3 전사 공유 sentinel | `services/vector_db.py:60` | `meta.get("org_id") is None` | `meta.get("org_id", "") == ""` |
| 🟡 5 | datetime timezone-aware | `models/db_models.py:13` | `default=datetime.utcnow` | `datetime.now(timezone.utc)` |
| 🟡 6 | FastAPI lifespan | `main.py:8` | `@app.on_event("startup")` | `lifespan` context manager |

```python
# [🔴 2] services/vector_db.py — BEFORE
def add_documents(self, texts: List[str], metadatas: List[dict]):
    for text, meta in zip(texts, metadatas):
        embedding = self.gateway.embed_text(text, tenant_id=meta.get("tenant_id", "default"))
        data.append({"content": text, "metadata": meta, "embedding": embedding})
```

```python
# AFTER
def add_documents(self, texts: list[str], metadatas: list[dict], embeddings: list[list[float]]):
    for text, meta, embedding in zip(texts, metadatas, embeddings, strict=True):
        data.append({"content": text, "metadata": meta, "embedding": embedding})
```

```python
# [🟠 3] api/documents.py — BEFORE
doc_record = await asyncio.to_thread(run_pipeline)
return DocumentUploadResponse(status="success", data=data)
```

```python
# AFTER
doc_record = repo.create_pending_doc(...)
asyncio.create_task(asyncio.to_thread(run_pipeline, doc_record.doc_id))
return DocumentUploadResponse(status="success", data={"pipeline_status": "pending"})
```

---

## Part 3. 종합 점수 (자기 판단)

점수는 가이드 기준에 따라 20개 항목을 `✅=1`, `⚠️=0.5`, `❌=0`으로 환산했다.

| 에이전트 | 점수 | 주요 강점 | 주요 약점 |
|---------|------|---------|---------|
| src_codex/v3 (자기) | **7.25 / 10** | 테스트 17/17, tenant/org 검색, Chroma `embeddings=`, Alembic, SSE | pending 비동기 pipeline, Index Swap, AuditLog 미구현 |
| src_claud/v3 | **8.25 / 10** | 테스트 17/17, pending 즉시 반환, embedding boundary 우수, AuditLog 있음 | PDF page_no 보존, Index Swap, migration 부족 |
| src_antigravity/v3 | **7.0 / 10** | Index Swap API와 SSE 구현, tenant/org 기본 정책 반영 | 외부 Gateway 의존 테스트 실패, embedding boundary, pending 반환, timezone 경고 |

