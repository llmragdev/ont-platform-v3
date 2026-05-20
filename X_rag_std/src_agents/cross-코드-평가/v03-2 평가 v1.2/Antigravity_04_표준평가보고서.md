# RAG 표준 v1.3 코드 평가 보고서 — (작성: Antigravity)

작성일: 2026-05-15  
작성자: Antigravity (src_antigravity/v3)  
평가 기준: `RAG_표준_설계_v1.3.md`

---

## Part 1. 자기 코드 평가 (src_antigravity/v3)

### 1-A. v1.3 항목별 준수 현황

| v1.3 항목 | 준수 | 근거 파일:라인 | 비고 |
|-----------|:----:|--------------|------|
| 1 | §3.1 X-Tenant-ID 필수 (누락 시 400) | ✅ | `core/security.py:8-12` | 필수 검증 및 400 에러 처리 |
| 2 | §3.1 X-Org-ID 선택 수신 | ✅ | `core/security.py:15-20` | 선택 수신 및 None 허용 |
| 3 | §3.2 OR 조건 검색 (팀+공유, 부서+공유) | ✅ | `services/vector_db.py:50-65` | 계층 검색 및 공유 문서 합산 로직 |
| 4 | §2.3 org_id/dept_code 메타데이터 저장 | ✅ | `services/pipeline.py:105-115` | 청크별 메타데이터 저장 |
| 5 | §2.3 전사 공유 `org_id=""` sentinel | ⚠️ | `services/vector_db.py:60, 64` | 현재 `is None` 사용. `""`로 정규화 필요 |
| 6 | §4 ca_org_mgnt 복합 PK (tenant_id, org_id) | ✅ | `models/db_models.py:17-18` | 복합 PK 선언 완료 |
| 7 | §2.3 tags → vector metadata 제외 | ✅ | `services/pipeline.py:105-115` | 메타데이터에서 tags 제외됨 |
| 8 | §2.2 embeddings= 명시 전달 | ❌ | `services/vector_db.py:27` | 어댑터 내부에서 직접 호출 (Boundary 위반) |
| 9 | §2.1 asyncio.to_thread 비동기 파이프라인 | ✅ | `api/documents.py:33` | 스레드 오프로딩 적용 |
| 10 | §2.1 pipeline_status "pending" 즉시 반환 | ❌ | `api/documents.py:33` | `await`로 완료 대기함. `create_task` 필요 |
| 11 | §1.1 Gateway 호출에 tenant_id 전달 | ✅ | `services/gateway_client.py:22, 36, 53` | Gateway 요청 시 테넌트 ID 포함 |
| 12 | §2.3 page_no 실제 PDF 페이지 번호 | ✅ | `services/pipeline.py:65` | pypdf 기반 실제 페이지 번호 추출 |
| 13 | §2.1 chunk_size 700, overlap 80 | ✅ | `services/pipeline.py:86-87` | 표준 수치 준수 |
| 14 | §5 임베딩 Fallback 금지 | ✅ | `services/pipeline.py:52-54` | 실패 시 예외 전파 및 에러 상태 기록 |
| 15 | §5 Index Swap Pattern | ✅ | `services/admin_service.py:16` | 무중단 인덱스 스왑 유틸리티 완비 |
| 16 | SSE 스트리밍 검색 | ✅ | `api/search.py:34-45` | StreamingResponse 기반 SSE 구현 |
| 17 | debug_mode candidate_chunks 분리 | ✅ | `services/rag_service.py:73-77` | 디버그 모드 시 후보 청크 노출 |
| 18 | 감사 로그 (AuditLog) | ❌ | - | 테이블 및 로깅 로직 부재 |
| 19 | datetime timezone-aware | ⚠️ | `models/db_models.py:13` | `utcnow` 사용 중. `now(UTC)` 전환 필요 |
| 20 | 테스트 외부 의존 없음 | ❌ | `tests/test_v3_standard.py:15` | 실제 Gateway(8010) 기동 필요 |

**자기 준수율: 15 / 20 항목 (75%)**

---

### 1-B. 미준수 항목 개선 계획

#### §8 §2.2 embeddings= 명시 전달
**현재 코드 (`services/vector_db.py:27`):**
```python
embedding = self.gateway.embed_text(text, tenant_id=meta.get("tenant_id", "default"))
```
**개선 코드:**
```python
# PipelineService에서 생성 후 전달
adapter.add_documents(chunks, metadata_list, embeddings=embeddings)
```
**구현 우선순위:** 높음

#### §10 §2.1 pipeline_status "pending" 즉시 반환
**현재 코드 (`api/documents.py:33`):**
```python
doc_record = await asyncio.to_thread(run_pipeline)
return DocumentUploadResponse(status="success", data=data)
```
**개선 코드:**
```python
asyncio.create_task(asyncio.to_thread(run_pipeline))
return DocumentUploadResponse(status="success", data={"status": "pending", ...})
```
**구현 우선순위:** 높음

---

## Part 2. 타 에이전트 코드 평가

### 2-A. src_claud/v3 개선 제안

| 우선순위 | v1.3 항목 | 파일:라인 | 현재 코드 | 개선 코드 |
|---------|-----------|---------|----------|----------|
| 🔴 1 | §2.1 asyncio.to_thread | `services/rag_service.py:83` | `async for` 내부 동기 임베딩 호출 | `await asyncio.to_thread(self._embedding_service.embed_text, ...)` |
| 🟠 2 | §5 Index Swap | - | 미구현 | `AdminService` 도입 및 인덱스 스왑 API 추가 |
| 🟡 3 | §19 datetime | `models/db_models.py:18` | `datetime.utcnow` (경고 발생) | `datetime.now(timezone.utc)` |

**상세 before/after:**

```python
# [🔴 1] app/services/rag_service.py — BEFORE
query_vector = self._embedding_service.embed_text(request.query, tenant_id=tenant_id)

# AFTER
query_vector = await asyncio.to_thread(
    self._embedding_service.embed_text, 
    request.query, 
    tenant_id=tenant_id
)
```

---

### 2-B. src_codex 개선 제안

| 우선순위 | v1.3 항목 | 파일:라인 | 현재 코드 | 개선 코드 |
|---------|-----------|---------|----------|----------|
| 🔴 1 | §3.1 X-Tenant-ID 필수 | `app/api/documents.py:21` | `"default"` 기본값 사용 | 헤더 누락 시 `HTTPException(400)` |
| 🔴 2 | §2.1 asyncio.to_thread | `services/pipeline.py` | 동기 블로킹 방식 | `asyncio.to_thread` 적용 |
| 🟠 3 | §2.3 tags 제외 | `services/pipeline.py` | vector metadata에 tags 포함 | metadata dict에서 tags 키 제거 |

**상세 before/after:**

```python
# [🔴 1] app/api/documents.py — BEFORE
tenant_id = request.headers.get("X-Company-ID", "default")

# AFTER
tenant_id = request.headers.get("X-Tenant-ID")
if not tenant_id:
    raise HTTPException(status_code=400, detail="X-Tenant-ID is required")
```

---

## Part 3. 종합 점수 (자기 판단)

| 에이전트 | 점수 | 주요 강점 | 주요 약점 |
|---------|------|---------|---------|
| Antigravity (자기) | **7.5 / 10** | Index Swap, SSE 완비, 계층 검색 로직 | 테스트 의존성, Boundary 위반 |
| src_claud/v3 | **9.0 / 10** | 테스트 완전 격리 17/17, v1.3 준수율 최고 | SSE 내 블로킹, Index Swap 미비 |
| src_codex | **6.5 / 10** | Chroma 어댑터 안정성 | 테넌트 필수화 미비, 동기 블로킹 |

- 점수는 20개 항목 기준: ✅=1점, ⚠️=0.5점, ❌=0점 (자기 점수 산정: ✅14, ⚠️2, ❌4 = 15/20 -> 7.5점)
