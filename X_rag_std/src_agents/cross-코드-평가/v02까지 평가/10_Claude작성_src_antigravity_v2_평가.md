# src_antigravity v2 RAG 구현 검토

검토일: 2026-05-14  
검토 대상: `src_antigravity/v2`  
기준 문서: `RAG_표준_설계_v1.0.md`, `details/01~04`

---

## 검토 요약

`src_antigravity/v2`는 계층형 아키텍처 설계와 LLM Gateway 연동 방향은 올바르나, PDF 파싱 Mock 잔재·청킹 미표준화·멀티테넌트 격리 부재 등 핵심 파이프라인 이슈가 다수 남아 있어 현 상태로는 운영 불가입니다.

---

## 잘된 점

- 계층형 아키텍처(API → Service → Repository → DB)가 명확히 분리됨.
- `asyncio.to_thread()` 적용으로 FastAPI 이벤트 루프 블로킹 방지.
- LLM Gateway 연동 구조(`gateway_client.py`) 설계 방향은 올바름.
- 라우팅 우선순위(vector_db_id > category_mid > default)가 명세와 일치.
- `debug_mode` 시 `candidate_chunks` vs `used_chunks` 분리 구조 준수.

---

## 이슈

### 이슈 1 — PDF 파싱이 Mock (중요도: 상)

```python
# src_antigravity/v2/services/pipeline.py
text_content = content.decode('utf-8', errors='ignore')
if not text_content.strip():
    text_content = "실제 PDF나 바이너리 텍스트 추출 결과입니다. (Mock)"
```

`pypdf`, `python-docx` 등 실제 파서 미통합. PDF 업로드 시 Mock 텍스트가 임베딩됨. 운영 불가 수준.

**권장**: `requirements.txt`에 `pypdf>=4.0.0`, `python-docx>=1.1.0` 추가 후 파서 통합.

### 이슈 2 — 청킹이 100자 하드코딩 + 10개 제한 (중요도: 상)

```python
chunks = [text_content[i:i+100] for i in range(0, len(text_content), 100)]
chunks = chunks[:10]  # 최대 10개
```

표준은 `chunk_size=500~800`, `chunk_overlap=50~100`. 현재 구현은 단어/문장 경계 무시, overlap 없음, 최대 1,000자만 처리. 5페이지 이상 문서는 내용이 잘림.

### 이슈 3 — 임베딩 오류 시 `[0.1, 0.2]` fallback 반환 (중요도: 상)

```python
except Exception as e:
    return [0.1, 0.2]  # Fallback
```

Gateway 호출 실패 시 2차원 벡터 반환. 실제 임베딩 차원(768 등)과 달라 벡터DB 삽입 시 차원 불일치 오류 또는 무의미한 검색 결과 발생. 예외를 전파하거나 `EmbeddingError`를 발생시켜야 함.

### 이슈 4 — company_id 멀티테넌트 격리 없음 (중요도: 상)

`X-Company-ID` 헤더 수신 자체가 없음. chunk metadata에 `company_id` 저장 안 함, 검색 시 필터 주입도 없음. 모든 테넌트의 문서가 동일 검색 풀에서 노출됨.

**권장**:
```python
# API 헤더 수신
def _company_id(request: Request) -> str:
    return request.headers.get("X-Company-ID", "default")

# chunk metadata에 저장
metadata["company_id"] = company_id

# 검색 시 강제 주입
filters["company_id"] = company_id
```

### 이슈 5 — wc_category 모델에 vector_db_id 없음 (중요도: 상)

```python
class Category(Base):
    __tablename__ = "wc_category"
    category_id: ...
    category_mid: ...
    category_low: ...
    # vector_db_id 누락 ← details/04 명세 위반
```

`details/04_RDBMS_Schema_Design.md` 및 표준 2.4에서 `vector_db_id`는 필수 컬럼.

### 이슈 6 — 프로젝트/카테고리 관리 API 없음 (중요도: 상)

`/api/v1/projects`, `/api/v1/categories` 엔드포인트 미구현. `details/04`에서 명시적으로 요구하는 항목.

### 이슈 7 — DialogHistory에 company_id 없음 (중요도: 중)

```python
class DialogHistory(Base):
    dialog_id: ...
    query: ...
    answer: ...
    used_chunks_meta: ...
    created_at: ...
    # company_id 없음 ← 멀티테넌트 이력 조회 불가
```

### 이슈 8 — ChunkMetadata에 doc_id, company_id 없음 (중요도: 중)

```python
metadata_list = [{
    "source_name": file.filename,
    "category_mid": category_mid,
    "vector_db_id": doc_record.assigned_vector_db,
    "page_no": i + 1
    # doc_id 없음 → delete_by_doc_id() 필터 동작 안 함
    # company_id 없음 → 멀티테넌트 검색 격리 불가
}]
```

doc_id 없으면 문서 삭제 시 모든 청크가 삭제되거나 삭제가 아예 안 됨.

### 이슈 9 — DB 모델 ForeignKey 없음 (중요도: 중)

참조 무결성 미보장. `wc_project_rag_doc.project_code` 등에 `ForeignKey()` 선언 필요.

### 이슈 10 — 문서 삭제/업데이트 endpoint 없음 (중요도: 중)

`DELETE /api/v1/documents/{doc_id}`, `PUT /api/v1/documents/{doc_id}` 미구현. 표준 2.1의 증분 업데이트 요건 미충족.

---

## 우선순위별 수정 권고

| 순위 | 항목 | 난이도 |
|------|------|--------|
| 1 | PDF 파싱 구현 (pypdf 통합) | 하 |
| 2 | 청킹 표준화 (chunk_size=700, overlap=80) | 하 |
| 3 | 임베딩 오류 시 fallback 제거 → EmbeddingError 전파 | 하 |
| 4 | company_id 격리 (X-Company-ID 헤더 + 메타데이터 + 필터) | 중 |
| 5 | chunk metadata에 doc_id, company_id 추가 | 하 |
| 6 | wc_category.vector_db_id 컬럼 추가 | 하 |
| 7 | DialogHistory.company_id 컬럼 추가 | 하 |
| 8 | 프로젝트/카테고리 CRUD API 추가 | 중 |
| 9 | 문서 삭제/업데이트 endpoint 추가 | 중 |
| 10 | DB 모델 ForeignKey 추가 | 하 |

---

## 결론

골격 설계는 좋으나 운영 전 필수 수정 항목이 10가지입니다. 1~5번(파싱·청킹·임베딩 안전성·멀티테넌트)을 먼저 수정하면 기본 운영 수준에 도달 가능합니다.
