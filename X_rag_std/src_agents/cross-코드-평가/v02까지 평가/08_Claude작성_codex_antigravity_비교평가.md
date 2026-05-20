# RAG 구현체 아키텍처 검토 보고서

검토일: 2026-05-14  
검토 대상: `src_codex`, `src_antigravity/v2`  
기준 문서: `RAG_표준_설계_v1.0.md`, `details/01~04`

---

## 1. 검토 요약

세 구현체 중 `src_codex`가 표준 설계 준수율이 가장 높습니다. `src_antigravity/v2`는 아키텍처 골격은 올바르나 핵심 파이프라인에 Mock 잔재가 있고 멀티테넌트 격리가 불완전합니다. `src_claud/v2`는 이전 검토(`src_claud_v2_gemini_gateway_rag_review.md`)에서 지적된 company_id 격리·Chroma 임베딩 일관성 이슈가 미해결 상태입니다.

---

## 2. 설계 표준 준수율 비교표

| 요건 항목 | 출처 | src_codex | src_antigravity/v2 | src_claud/v2 |
|-----------|------|-----------|-------------------|--------------|
| 파이프라인 상태 전이 (pending→processing→completed/error) | 표준 2.1 | ✅ | ✅ | ✅ |
| raw/processed 디렉터리 분리 | 표준 2.1 | ✅ | ❌ (raw만 저장) | ✅ |
| 증분 업데이트 (PUT endpoint) | 표준 2.1 | ✅ | ❌ (미구현) | ✅ |
| 벡터DB 카테고리별 분리 (routing registry) | 표준 2.2 | ✅ | ⚠️ (동적 명명만) | ✅ |
| 엔진 이원화 (local_json + chroma) | 표준 2.2 | ✅ | ❌ (local_json만) | ✅ |
| 임베딩 모델별 컬렉션 분리 | 표준 2.2 | ⚠️ (구조는 있으나 치수 무관) | ❌ | ⚠️ |
| ChunkMetadata에 vector_db_id 포함 | 표준 2.3/2.4 | ✅ | ⚠️ (일부) | ❌ |
| ChunkMetadata에 doc_id 포함 | 표준 2.4 | ✅ | ❌ | ✅ |
| ChunkMetadata에 page_no 포함 | 표준 2.4 | ⚠️ (chunk index) | ⚠️ (chunk index) | ⚠️ (chunk index) |
| ChunkMetadata에 chunk_type, tags 포함 | 표준 2.4 | ✅ | ❌ | ✅ |
| company_id 벡터 메타데이터 저장 | 표준 2.4 | ✅ | ❌ | ❌ |
| 검색 시 company_id 필터 강제 주입 | 표준 2.7 | ✅ | ❌ | ❌ |
| Chroma add_documents에 embeddings= 전달 | 표준 2.2 | ✅ | N/A | ❌ |
| debug_mode: candidate_chunks vs used_chunks 분리 | 표준 2.7 | ✅ | ✅ | ✅ |
| 표준 오류 클래스 (document_parsing_error 등) | 표준 2.6 | ✅ | ❌ | ✅ |
| wc_project CRUD API | detail 04 | ✅ | ❌ | ✅ |
| wc_category CRUD API | detail 04 | ✅ | ❌ | ✅ |
| wc_category.vector_db_id 컬럼 | detail 04 | ✅ | ❌ | ✅ |
| DB 모델 ForeignKey 참조 무결성 | detail 04 | ❌ | ❌ | ✅ |
| DialogHistory company_id 컬럼 | detail 04 | ✅ | ❌ | ✅ |
| 문서 version 관리 | detail 01 | ✅ | ❌ | ✅ |
| PDF 실제 파싱 (pypdf 등) | detail 01 | ✅ | ❌ (Mock) | ✅ |
| chunk_size 표준 범위 (500~800) | detail 01 | ✅ (700) | ❌ (100자 하드코딩) | ✅ |
| chunk_overlap 표준 범위 (50~100) | detail 01 | ✅ (80) | ❌ (없음) | ✅ |

---

## 3. src_codex 상세 이슈

### ✅ 잘된 점

- **company_id 검색 격리 완전 구현**: 메타데이터 저장 + 검색 필터 강제 주입 둘 다 적용. 세 구현체 중 유일.
- **Chroma embedding 일관성**: `ChromaVectorDbAdapter.add_documents()`가 `embeddings=` 파라미터를 명시적으로 전달 — 문서/질의 벡터 공간 일치.
- **표준 메타데이터 완전 준수**: `doc_id`, `company_id`, `source_name`, `source_url`, `vector_db_id`, `category_mid`, `chunk_type`, `tags` 전부 chunk metadata에 포함.
- **오류 클래스 표준화**: `DocumentParsingError`, `VectorDbConnectionError` 등 표준 명명 준수.
- **프로젝트/카테고리 API 완비**: CRUD + 프로젝트 삭제 시 문서 cascade.
- **Chroma 포트 8001**: RAG(8000), Gateway(8010)과 포트 충돌 없음.

### ⚠️ 이슈

#### 이슈 1 — DB 모델 ForeignKey 없음 (중요도: 중)

`ca_org_mgnt.company_id`, `ca_user.company_id`, `wc_project_rag_doc.project_code` 등에 `ForeignKey()` 선언이 없음. SQLAlchemy가 참조 무결성을 강제하지 않아 고아 레코드 발생 가능.

```python
# 현재 (src_codex/app/models/db_models.py)
company_id: Mapped[str] = mapped_column(String(64), nullable=False)

# 권장
company_id: Mapped[str] = mapped_column(String(64), ForeignKey("ca_company.company_id"), nullable=False)
```

#### 이슈 2 — page_no가 실제 PDF 페이지 번호가 아닌 chunk 인덱스 (중요도: 중)

`_run_pipeline()`에서 `page_no = index + 1` (chunk 순번). 표준 2.3은 "원본 파일 내의 페이지 번호"를 요구.  
pypdf를 이미 사용하므로 페이지별 텍스트 추출 시 실제 페이지 번호 부착이 가능.

```python
# 권장: PDF는 페이지별로 청킹하여 page_no 보존
reader = PdfReader(str(path))
for page_num, page in enumerate(reader.pages, start=1):
    page_text = page.extract_text() or ""
    for chunk_idx, chunk in enumerate(chunker.split_text(page_text)):
        metadata["page_no"] = page_num  # 실제 페이지 번호
```

#### 이슈 3 — wc_category ↔ routing.json 자동 연동 없음 (중요도: 하)

카테고리를 API로 등록해도 `vector_routing.json`이 자동 갱신되지 않음. routing.json을 수동으로 편집해야 라우팅 적용. 향후 v3 과제로 분류.

#### 이슈 4 — asyncio.to_thread와 SQLAlchemy Session 공유 (중요도: 중)

`src_claud/v2` 이슈 #3과 동일. `_run_pipeline()`을 `asyncio.to_thread()`로 실행하면서 request 스레드의 Session을 공유. SQLAlchemy Session은 스레드 비안전.

---

## 4. src_antigravity/v2 상세 이슈

### ✅ 잘된 점

- 계층형 아키텍처(API → Service → Repository → DB)가 명확히 분리됨.
- `asyncio.to_thread()` 적용으로 FastAPI 이벤트 루프 블로킹 방지.
- LLM Gateway 연동 구조(`gateway_client.py`) 설계 방향은 올바름.
- 라우팅 우선순위(vector_db_id > category_mid > default)가 명세와 일치.

### ❌ 심각한 이슈

#### 이슈 1 — PDF 파싱이 Mock (중요도: 상)

```python
# src_antigravity/v2/services/pipeline.py
text_content = content.decode('utf-8', errors='ignore')
if not text_content.strip():
    text_content = "실제 PDF나 바이너리 텍스트 추출 결과입니다. (Mock)"
```

`pypdf`, `python-docx` 등 실제 파서가 미통합. PDF 업로드 시 Mock 텍스트가 임베딩됨. 운영 불가 수준.

#### 이슈 2 — 청킹이 100자 하드코딩 + 10개 제한 (중요도: 상)

```python
chunks = [text_content[i:i+100] for i in range(0, len(text_content), 100)]
chunks = chunks[:10]  # 테스트/부하 방지
```

표준은 `chunk_size=500~800`, `chunk_overlap=50~100`. 현재 구현은 단어/문장 경계 무시, overlap 없음, 최대 1,000자만 처리. 5페이지 이상 문서는 내용이 잘림.

#### 이슈 3 — 임베딩 오류 시 `[0.1, 0.2]` fallback 반환 (중요도: 상)

```python
except Exception as e:
    return [0.1, 0.2]  # Fallback
```

Gateway 호출 실패 시 2차원 벡터를 반환. 실제 임베딩 차원(768 등)과 달라 벡터DB 삽입 시 차원 불일치 오류 또는 무의미한 검색 결과 발생. 예외를 전파하거나 `EmbeddingError`를 발생시켜야 함.

#### 이슈 4 — company_id 멀티테넌트 격리 없음 (중요도: 상)

API에서 `X-Company-ID` 헤더 수신 자체가 없음. chunk metadata에 `company_id`를 저장하지 않고, 검색 시에도 필터 주입 없음. 모든 테넌트의 문서가 같은 검색 풀에서 노출됨.

#### 이슈 5 — wc_category 모델에 vector_db_id 없음 (중요도: 상)

```python
class Category(Base):
    __tablename__ = "wc_category"
    category_id: ...
    category_mid: ...
    category_low: ...
    # vector_db_id 없음! ← 설계 명세 위반
```

`details/04_RDBMS_Schema_Design.md`와 표준 2.4에서 `vector_db_id`는 필수 컬럼.

#### 이슈 6 — 프로젝트/카테고리 관리 API 없음 (중요도: 상)

`/api/v1/projects`, `/api/v1/categories` 엔드포인트 미구현. `details/04`에서 명시적으로 요구하는 항목.

#### 이슈 7 — DialogHistory에 company_id 없음 (중요도: 중)

```python
class DialogHistory(Base):
    dialog_id: ...
    query: ...
    answer: ...
    used_chunks_meta: ...
    created_at: ...
    # company_id 없음
```

멀티테넌트 환경에서 회사별 대화 이력 조회 불가. 표준 명세 위반.

#### 이슈 8 — ChunkMetadata에 doc_id, company_id 없음 (중요도: 중)

```python
metadata_list = [{
    "source_name": file.filename,
    "category_mid": category_mid,
    "vector_db_id": doc_record.assigned_vector_db,
    "page_no": i + 1
    # doc_id 없음, company_id 없음
}]
```

doc_id 없으면 `delete_by_doc_id()` 필터가 동작 안 함 (검색 조건 없음). 문서 삭제가 작동하지 않거나 모든 문서를 삭제할 위험.

#### 이슈 9 — DB 모델 ForeignKey 없음 (중요도: 중)

src_codex와 동일. 참조 무결성 없음.

---

## 5. 구현체 등급 종합

| 평가 항목 | src_codex | src_antigravity/v2 | src_claud/v2 |
|-----------|-----------|-------------------|--------------|
| 표준 설계 준수율 | **A** | C | B |
| 멀티테넌트 격리 | **A** (완전) | D (없음) | C (DB만, 벡터 없음) |
| 운영 가능 수준 | **B+** | D (Mock 잔재) | B |
| 표준 메타데이터 | **A** | C | B |
| 코드 구조 | A | B | A |
| 테스트 커버리지 | A | B | A |
| Chroma 연동 | **A** | F (미구현) | C (임베딩 불일치) |

---

## 6. 우선순위별 수정 권고

### src_antigravity/v2 — 운영 전 필수 수정

| 순위 | 항목 | 난이도 |
|------|------|--------|
| 1 | PDF 파싱 구현 (pypdf 통합) | 하 |
| 2 | 청킹 표준화 (500-800, overlap 80) | 하 |
| 3 | 임베딩 오류 시 fallback 제거 → 예외 전파 | 하 |
| 4 | company_id 벡터 격리 (X-Company-ID 헤더 + 필터 강제) | 중 |
| 5 | wc_category.vector_db_id 컬럼 추가 | 하 |
| 6 | chunk metadata에 doc_id, company_id 추가 | 하 |
| 7 | 프로젝트/카테고리 CRUD API 추가 | 중 |
| 8 | DialogHistory.company_id 추가 | 하 |
| 9 | 문서 삭제/업데이트 endpoint 추가 | 중 |

### src_codex — 보완 권고

| 순위 | 항목 | 난이도 |
|------|------|--------|
| 1 | DB 모델 ForeignKey 추가 | 하 |
| 2 | PDF 파싱 시 실제 page_no 보존 | 중 |
| 3 | asyncio.to_thread 내 신규 Session 생성 | 중 |

### src_claud/v2 — 이전 검토 미해결 이슈

| 순위 | 항목 | 상태 |
|------|------|------|
| 1 | Chroma add_documents에 embeddings= 전달 | ❌ 미수정 |
| 2 | 검색 시 company_id 필터 강제 주입 | ❌ 미수정 |
| 3 | asyncio.to_thread 내 Session 공유 | ❌ 미수정 |
| 4 | ChunkMetadata에 vector_db_id 추가 | ❌ 미수정 |

---

## 7. 결론

**src_codex**가 현재 세 구현체 중 가장 운영 수준에 가깝습니다. company_id 멀티테넌트 격리와 Chroma embedding 일관성을 모두 올바르게 구현한 유일한 구현체입니다. FK 추가, page_no 정확도 개선, asyncio Session 이슈 3가지만 수정하면 운영 후보로 적합합니다.

**src_antigravity/v2**는 골격 설계는 좋으나 PDF Mock, 100자 청킹, company_id 격리 부재 등 핵심 파이프라인 이슈가 다수 남아 있어 현 상태로는 운영 불가입니다.

**src_claud/v2**는 이전 검토에서 지적된 4개 이슈 — Chroma embedding 불일치, company_id 벡터 격리, Session 스레드 안전, vector_db_id 메타데이터 — 가 미해결로 src_codex보다 낮은 완성도입니다. 프로젝트/카테고리 API 범위에서는 앞서지만 핵심 RAG 품질 이슈를 우선 수정해야 합니다.
