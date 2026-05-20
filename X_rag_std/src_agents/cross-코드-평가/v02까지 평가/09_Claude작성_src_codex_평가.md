# src_codex RAG 구현 검토

검토일: 2026-05-14  
검토 대상: `src_codex`  
기준 문서: `RAG_표준_설계_v1.0.md`, `details/01~04`

---

## 검토 요약

`src_codex`는 세 구현체(src_codex, src_antigravity/v2, src_claud/v2) 중 표준 설계 준수율이 가장 높습니다. company_id 멀티테넌트 격리와 Chroma embedding 일관성을 모두 올바르게 구현한 유일한 구현체로, FK 추가·page_no 정확도·asyncio Session 이슈 3가지만 수정하면 운영 후보로 적합합니다.

```
pytest -q tests
전체 테스트 통과 확인됨
```

---

## 잘된 점

- **company_id 검색 격리 완전 구현**: chunk metadata 저장 + 검색 필터 강제 주입(`_adapter_filters()`) 둘 다 적용. 세 구현체 중 유일.
- **Chroma embedding 일관성**: `ChromaVectorDbAdapter.add_documents()`가 `embeddings=` 파라미터를 명시적으로 전달 — 문서/질의 벡터 공간 일치.
- **표준 메타데이터 완전 준수**: `doc_id`, `company_id`, `source_name`, `source_url`, `vector_db_id`, `category_mid`, `chunk_type`, `tags` 전부 chunk metadata에 포함.
- **오류 클래스 표준화**: `DocumentParsingError`, `VectorDbConnectionError` 등 표준 명명 준수.
- **프로젝트/카테고리 API 완비**: CRUD + 프로젝트 삭제 시 문서 cascade.
- **Chroma 포트 8001**: RAG(8000), Gateway(8010)과 포트 충돌 없음.
- **chunk_size 700, overlap 80**: 표준 범위(500~800, 50~100) 준수.
- **증분 업데이트(PUT endpoint)**: 버전 관리 + 벡터 재적재 구현.

---

## 이슈

### 이슈 1 — DB 모델 ForeignKey 없음 (중요도: 중)

`ca_org_mgnt.company_id`, `ca_user.company_id`, `wc_project_rag_doc.project_code` 등에 `ForeignKey()` 선언이 없음. SQLAlchemy가 참조 무결성을 강제하지 않아 고아 레코드 발생 가능.

```python
# 현재
company_id: Mapped[str] = mapped_column(String(64), nullable=False)

# 권장
company_id: Mapped[str] = mapped_column(String(64), ForeignKey("ca_company.company_id"), nullable=False)
```

### 이슈 2 — page_no가 실제 PDF 페이지 번호가 아닌 chunk 인덱스 (중요도: 중)

`_run_pipeline()`에서 `page_no = index + 1` (chunk 순번). 표준 2.3은 "원본 파일 내의 페이지 번호"를 요구. pypdf를 이미 사용하므로 페이지별 추출 시 실제 번호 부착 가능.

```python
# 권장
reader = PdfReader(str(path))
for page_num, page in enumerate(reader.pages, start=1):
    page_text = page.extract_text() or ""
    for chunk in chunker.split_text(page_text):
        metadata["page_no"] = page_num  # 실제 페이지 번호
```

### 이슈 3 — asyncio.to_thread와 SQLAlchemy Session 공유 (중요도: 중)

`_run_pipeline()`을 `asyncio.to_thread()`로 실행하면서 request 스레드의 Session을 공유. SQLAlchemy Session은 스레드 비안전으로 운영 환경에서 간헐적 DB 오류 발생 가능.

**권장**: worker thread 내부에서 새 Session 생성하거나, DB 상태 업데이트는 request 스레드에서 처리하고 파일 추출/임베딩만 별도 thread로 분리.

### 이슈 4 — wc_category ↔ routing.json 자동 연동 없음 (중요도: 하)

카테고리 API로 등록해도 `vector_routing.json`이 자동 갱신되지 않음. 향후 v3 과제.

---

## 우선순위별 수정 권고

| 순위 | 항목 | 난이도 |
|------|------|--------|
| 1 | DB 모델 ForeignKey 추가 | 하 |
| 2 | PDF 파싱 시 실제 page_no 보존 | 중 |
| 3 | asyncio.to_thread 내 신규 Session 생성 | 중 |

---

## 결론

현재 세 구현체 중 운영 수준에 가장 가깝습니다. 위 3가지 수정 후 운영 후보로 적합합니다.
