# src_claud v2 RAG 표준 설계 준수 평가

검토일: 2026-05-14

검토 대상:

- `E:\ontology_edu\X_rag_std\RAG_표준_설계_v1.0.md`
- `E:\ontology_edu\X_rag_std\details\01_Document_Embedding_Pipeline.md`
- `E:\ontology_edu\X_rag_std\details\02_VectorDB_Management_Routing.md`
- `E:\ontology_edu\X_rag_std\details\03_RAG_Search_API.md`
- `E:\ontology_edu\X_rag_std\details\04_RDBMS_Schema_Design.md`
- `E:\ontology_edu\X_rag_std\src_agents\src_claud\v2`

## 총평

`src_claud/v2`는 `src_claud` v1보다 구조가 안정되었고, `src_codex`의 기준 구현을 확장해 운영형 API 표면을 넓힌 구현이다. FastAPI, Pydantic, SQLAlchemy, 라우터/어댑터 패턴, 문서 파이프라인, RAG 검색 API, 프로젝트/카테고리 API, LLM Gateway 연동 구조까지 포함되어 있어 전체적인 방향은 표준 설계와 잘 맞는다.

테스트도 현재 통과한다.

```text
pytest -q tests
14 passed
```

다만 표준 설계 문서 기준으로 보면 운영 후보로 인정하기 전에 반드시 고쳐야 할 미준수 항목이 남아 있다. 가장 중요한 것은 다음 네 가지다.

1. Chroma 운영 모드에서 문서 embedding과 query embedding이 서로 다른 공간이 될 수 있음
2. Vector chunk metadata에 표준 필수값인 `vector_db_id`, `created_at`이 빠짐
3. `X-Company-ID`를 받지만 vector search에 `company_id` 격리가 강제되지 않음
4. 문서 파이프라인이 `asyncio.to_thread()`에서 동일 SQLAlchemy Session을 사용함

## 표준 설계 준수 매트릭스

| 기준 | 평가 | 근거 |
|---|---:|---|
| PEP 8, snake_case/PascalCase | 양호 | 전반적으로 Python naming convention 준수 |
| FastAPI/Pydantic API | 양호 | `app/api`, `app/models/schemas.py` 구조 사용 |
| Raw/Processed 저장소 분리 | 양호 | `raw_documents_dir`, `processed_dir` 사용 |
| 문서 상태 전이 | 부분 준수 | `pending`, `processing`, `completed`, `error` 구현. 다만 응답은 동기 완료 후 `completed` 반환 |
| 비동기/스레드풀 파이프라인 | 부분 준수 | `asyncio.to_thread()` 사용. 단, Session thread safety 문제 있음 |
| 증분 업데이트 | 부분 준수 | 기존 청크 삭제 후 재삽입 및 version 증가. 실제 변경 chunk 식별은 아님 |
| VectorDB 물리/논리 분리 | 양호 | `vector_db_id`, routing config, local_json/chroma 선택 구조 |
| 라우터/어댑터 패턴 | 양호 | `VectorDbRouter`, `VectorDbAdapter`, LocalJson/Chroma adapter |
| Chroma 운영 연동 | 부분 준수 | Chroma adapter 있음. 단, embedding 명시 저장 누락 |
| Remote Retriever | 양호 | LangChain 결합 없이 adapter search 후 LLM Gateway 호출 |
| Gemini LLM Gateway 키 분리 | 양호 | RAG 서버는 `LLM_GATEWAY_URL`만 사용 |
| RAG Search API 레이아웃 | 부분 준수 | `used_chunks`, `debug_info.candidate_chunks` 구조 있음. metadata 필수값 일부 누락 |
| debug mode 후보 청크 노출 | 양호 | `debug_mode=True`일 때만 `debug_info` 생성 |
| RDBMS 주요 테이블 | 양호 | `ca_company`, `ca_org_mgnt`, `ca_user`, `wc_project`, `wc_category`, `wc_intent`, `wc_project_rag_doc`, `wc_dialog_history` 구현 |
| 표준 오류 응답 | 부분 준수 | custom error/http_error 있음. 일반 예외 처리 범위는 제한적 |
| 접근 권한/RBAC | 보류/미대상 | 기본 설계에서도 보류 항목 |

## 주요 Findings

### 1. High: Chroma 운영 모드에서 문서 embedding과 query embedding이 불일치할 수 있음

표준 설계 2.2는 임베딩 모델별 컬렉션 분리를 요구한다. 또한 Chroma/Qdrant 같은 VectorDB에서는 같은 embedding model로 생성된 문서 벡터와 query 벡터가 같은 컬렉션에 있어야 한다.

현재 `ChromaAdapter.add_documents()`는 Chroma에 `documents`와 `metadatas`만 전달한다.

```python
self._collection.add(ids=ids, documents=documents, metadatas=metadata)
```

반면 검색은 외부 embedding service가 만든 `query_vector`를 `query_embeddings`로 넘긴다.

```python
results = self._collection.query(query_embeddings=[query_vector], ...)
```

위 구조에서는 Chroma가 문서 저장 시 자체 기본 embedding function을 사용할 수 있고, 검색 시에는 Gemini Gateway embedding을 사용할 수 있다. 그 결과 차원 또는 벡터 공간이 달라져 운영 검색 품질이 깨질 수 있다.

관련 파일:

- `app/services/vector_db/chroma.py`
- `app/services/router.py`
- `app/services/embedding/gemini_http_embedding.py`

수정 권장:

- `ChromaAdapter`에 `EmbeddingService`를 주입
- `add_documents()`에서 각 chunk에 대해 동일 provider embedding 생성
- Chroma `add()` 호출 시 `embeddings=` 명시
- collection name에 embedding model/dimension 식별자를 포함

### 2. High: 표준 metadata 필수값 `vector_db_id`, `created_at`이 chunk metadata에 없음

기본 설계 2.4의 표준 metadata는 다음을 필수로 둔다.

- `doc_id`
- `source_url`
- `created_at`
- `vector_db_id`
- `category_mid`

현재 `document_service.py`에서 vector metadata를 만들 때 다음만 넣는다.

```python
{
    "source_name": safe_name,
    "source_url": str(raw_path),
    "doc_id": doc_id,
    "category_mid": category_mid,
    "category_low": category_low,
    "chunk_type": "text",
    "tags": [],
}
```

`vector_db_id`, `created_at`, `company_id`, `page_no`가 없다. `ChunkMetadata` Pydantic 모델에도 `vector_db_id`와 `created_at`이 없다.

이 문제는 RAG 역매핑 품질과 디버그 모드의 운영 분석력을 떨어뜨린다. 특히 설계서의 응답 예시는 `vector_db_id`를 명시적으로 요구한다.

관련 파일:

- `app/services/document_service.py`
- `app/models/schemas.py`
- `app/services/vector_db/local_json.py`
- `app/services/vector_db/chroma.py`

수정 권장:

- `ChunkMetadata`에 `vector_db_id`, `created_at`, `company_id` 추가
- `DocumentPipelineService._run_pipeline()`의 `meta_payloads`에 `assigned_vdb`, 현재 시각, 회사 ID 추가
- PDF는 가능하면 실제 page 단위 chunk metadata에 `page_no` 보존

### 3. High: `X-Company-ID` 기반 멀티테넌트 검색 격리가 불완전함

API 계층은 `X-Company-ID`를 읽고, 문서 목록도 회사별 조회를 한다. 하지만 vector metadata에는 `company_id`가 저장되지 않고, RAG 검색 필터에도 `company_id`가 강제 주입되지 않는다.

현재 검색 필터 구성:

```python
values = filters.model_dump(exclude_none=True)
values.pop("vector_db_id", None)
return values
```

즉 회사 A가 올린 문서와 회사 B가 올린 문서가 같은 `vector_db_id`에 있으면 검색 결과가 섞일 수 있다.

관련 파일:

- `app/api/documents.py`
- `app/api/search.py`
- `app/services/document_service.py`
- `app/services/rag_service.py`
- `app/services/vector_db/local_json.py`
- `app/services/vector_db/chroma.py`

수정 권장:

- vector metadata에 `company_id` 저장
- `RagSearchService._adapter_filters()`에 `company_id` 강제 주입
- `GeminiHttpEmbeddingService.embed_text()`에도 실제 `company_id` 전달
- update/delete도 record의 `company_id`와 요청 company를 비교 후 처리
- tenant 격리 pytest 추가

### 4. High: `asyncio.to_thread()`에서 동일 SQLAlchemy Session을 사용함

문서 업로드/수정 시 `_run_pipeline()`을 `asyncio.to_thread()`로 실행한다. 그런데 `_run_pipeline()` 내부에서 `self._doc_repo.set_status()`를 호출하고, 이 repository는 요청 thread에서 만들어진 같은 SQLAlchemy Session을 들고 있다.

SQLAlchemy Session은 thread-safe하지 않다. 테스트에서는 빨리 통과하지만 운영에서는 간헐적인 DB 오류, 세션 상태 꼬임, 커밋 실패가 날 수 있다.

관련 파일:

- `app/services/document_service.py`
- `app/repositories/document_repo.py`
- `app/db/session.py`

수정 권장:

- thread 내부에서 새 DB Session을 생성
- 또는 DB 상태 업데이트는 request thread에서 하고, 파일 추출/임베딩/VectorDB 적재만 thread로 분리
- 장기적으로는 background task queue 또는 worker 도입

### 5. Medium: 상세설계 01의 “pending 응답 후 비동기 처리” 의도와 현재 동작이 다름

상세설계 01의 업로드 응답 예시는 `pipeline_status: "pending"`이다. 설계 의도는 업로드 후 파이프라인을 비동기로 트리거하고 즉시 pending을 반환하는 흐름에 가깝다.

현재 구현은 `await asyncio.to_thread(...)`로 파이프라인 완료까지 기다린 뒤 `completed` 상태를 반환한다.

장점은 테스트와 로컬 사용이 단순하다는 점이다. 하지만 대용량 문서에서는 API 요청 시간이 길어지고, 상세설계의 “대용량 파일 임베딩 중 시스템 지연 방지” 목적에는 덜 맞는다.

수정 권장:

- 운영 모드에서는 upload 응답을 `pending`으로 즉시 반환
- background worker가 `processing -> completed/error` 처리
- 테스트/로컬 모드는 synchronous option을 둘 수 있음

### 6. Medium: 증분 업데이트가 “문서 단위 재삽입” 수준임

상세설계 01은 변경된 문서나 페이지 chunk만 식별하여 갱신하는 증분 업데이트를 지향한다. 현재 구현은 해당 `doc_id`의 기존 chunk를 모두 삭제하고 새 문서를 전부 재삽입한다.

이는 설계서 내 4.2의 구체 단계와는 어느 정도 맞지만, 기본설계 2.1의 “변경된 문서나 페이지만 식별” 수준까지는 아니다.

관련 파일:

- `app/services/document_service.py`
- `app/services/vector_db/local_json.py`
- `app/services/vector_db/chroma.py`

수정 권장:

- page/chunk hash 저장
- 변경 chunk만 delete/insert
- `version`과 chunk lineage 관리

### 7. Medium: Gemini Gateway 호출에 실제 `company_id`가 전달되지 않음

`GeminiHttpEmbeddingService`는 gateway에 `company_id: "default"`를 하드코딩한다.

```python
json={"text": text, "company_id": "default"}
```

`GeminiHttpLlmClient`도 generate 요청에 `company_id`를 전달하지 않는다.

Gateway가 tenant별 캐시, 감사 로그, quota, model policy를 관리하려면 실제 `X-Company-ID`가 전달되어야 한다.

관련 파일:

- `app/services/embedding/gemini_http_embedding.py`
- `app/services/llm/gemini_http_llm.py`
- `app/services/rag_service.py`
- `app/services/document_service.py`

수정 권장:

- `embed_text(text, company_id="default")` signature 도입
- `generate_answer(query, chunks, company_id="default")` signature 도입
- document embedding 및 query embedding 모두 실제 company_id 전달

### 8. Medium: 테스트가 표준 준수 리스크를 충분히 검증하지 않음

현재 테스트는 14개 모두 통과한다. 하지만 다음 핵심 표준 리스크는 테스트하지 않는다.

- `debug_mode=false`일 때 `debug_info`가 반드시 `None`인지
- `candidate_chunks`가 `debug_mode=true`에서만 노출되는지
- chunk metadata에 `vector_db_id`, `created_at`, `company_id`가 있는지
- 회사 A/B의 vector search 결과가 격리되는지
- Chroma adapter가 문서 embedding을 명시 저장하는지
- Gemini Gateway에 실제 company_id가 전달되는지
- upload 응답/상태 전이가 설계 의도와 맞는지

수정 권장:

- 표준 설계 compliance test suite 추가
- local_json과 chroma adapter contract test 분리
- gateway mock test 추가

### 9. Low: 오류 응답 스키마 이름이 표준과 약간 다름

기본 설계는 오류 응답에서 `error_code`와 `message` 형태를 원칙으로 한다. 현재 `ErrorDetail`은 `code`, `message`를 사용한다.

관련 파일:

- `app/models/schemas.py`
- `app/core/errors.py`

수정 권장:

- 외부 응답은 `error_code`로 통일
- 내부 exception class는 유지해도 됨

### 10. Low: Claude/Voyage provider가 Gemini Gateway 운영 방향과 혼재됨

현재 provider factory에는 `claude` 경로와 `ANTHROPIC_API_KEY`가 남아 있다. 사용자가 정한 운영 방향이 “Gemini LLM 추론 서버가 키를 관리한다”라면 Claude/Voyage 경로는 legacy/experimental로 명확히 분리하는 편이 좋다.

관련 파일:

- `app/core/config.py`
- `app/services/providers.py`
- `app/services/embedding/claude_embedding.py`
- `app/services/llm/claude_llm.py`
- `v2_Development_Plan.md`

## 상세 요건별 평가

### 01. Document Embedding Pipeline

준수한 점:

- `POST /api/v1/documents/upload` 구현
- `file`, `category_mid`, `category_low`, `vector_db_id` 입력 지원
- raw/processed 저장소 분리
- `pending -> processing -> completed/error` 상태 필드 구현
- PDF/DOCX/TXT 추출 지원
- semantic/fixed chunker 제공
- update 시 기존 chunk 삭제 후 version 증가 및 재삽입

미흡한 점:

- 응답이 즉시 `pending`이 아니라 동기 처리 후 `completed`에 가까움
- thread-safe하지 않은 Session 사용
- metadata에 `vector_db_id`, `created_at`, `company_id`, `page_no` 누락
- 변경 chunk만 식별하는 세밀한 증분 업데이트는 아님

평가: 7.0 / 10

### 02. VectorDB Management Routing

준수한 점:

- `VectorDbRouter` 구현
- routing config 기반 `vector_db_id` resolve
- `vector_db_id` 우선, `category_mid` fallback 구조
- `VectorDbAdapter` base interface
- local_json, Chroma adapter 구현
- `VECTOR_DB_ENGINE`, `CHROMA_HOST`, `CHROMA_PORT` 환경변수 지원

미흡한 점:

- Chroma 저장 시 embedding 명시 전달 없음
- Qdrant/FAISS는 설계 예시일 뿐 구현 없음
- `company_id` 기반 물리/논리 분리 미완성
- 라우팅 config parse 실패 시 조용히 빈 배열 반환하여 운영 장애를 숨길 수 있음

평가: 7.5 / 10

### 03. RAG Search API

준수한 점:

- `POST /api/v1/rag/search` 구현
- `query`, `top_k`, `debug_mode`, `filters` Pydantic 모델화
- `used_chunks`, `debug_info.candidate_chunks` 분리
- LangChain retriever에 결합하지 않음
- LLM Gateway 연동 provider 존재
- streaming endpoint 추가

미흡한 점:

- response metadata에서 `vector_db_id` 누락
- `company_id` 검색 격리 미완성
- LLM/Gemini 호출에 company_id 미전달
- `debug_mode=false` 보장 테스트가 약함

평가: 7.0 / 10

### 04. RDBMS Schema Design

준수한 점:

- `ca_company`, `ca_org_mgnt`, `ca_user` 구현
- `wc_project`, `wc_category`, `wc_intent` 구현
- `wc_project_rag_doc` 구현
- `wc_dialog_history` 구현
- `project_code` FK, category/vector_db_id 구조 반영
- `company_id`와 audit log 확장 구현

미흡한 점:

- migration 체계 없음
- `datetime.utcnow()` deprecation warning
- 일부 FK/tenant 관계는 운영 수준 제약이 약함
- vector metadata와 RDBMS metadata 간 필수 필드 정합성 부족

평가: 8.0 / 10

## 종합 점수

현재 구현 기준:

```text
src_claud/v2 표준 준수도: 7.3 / 10
```

테스트 통과와 API 범위는 좋지만, 표준 설계에서 중요한 “역매핑 metadata”, “임베딩 모델/컬렉션 일관성”, “tenant 격리”, “운영형 비동기 파이프라인”이 아직 완성되지 않았다.

위 High 항목 4개를 수정하면 8.5점 이상으로 볼 수 있다.

## 우선 수정 순서

1. `ChunkMetadata`와 vector metadata에 `vector_db_id`, `created_at`, `company_id` 추가
2. RAG 검색 필터에 `company_id` 강제 주입
3. Gemini embedding/LLM gateway 호출에 실제 `company_id` 전달
4. Chroma adapter가 document embedding을 같은 provider로 생성하여 `embeddings=` 전달
5. `asyncio.to_thread()` 내부 DB 작업을 별도 Session 또는 worker 구조로 변경
6. 표준 compliance pytest 추가
7. README에서 통합 테스트 경로와 Gemini-only 운영 방침 정리

## 결론

`src_claud/v2`는 설계 방향은 좋고 API 범위도 넓다. 특히 Gemini Gateway를 분리한 점, router/adapter 구조, project/category API, audit log는 `src_codex` 초기 구현보다 확장성이 좋다.

하지만 RAG 표준 설계 v1.0을 엄격히 기준으로 보면, 현재는 “테스트가 통과하는 확장 구현”이지 “표준 완전 준수 구현”은 아니다. 운영 후보로 올리려면 metadata 표준화, tenant 격리, Chroma embedding 일관성, thread-safe pipeline을 먼저 보완해야 한다.
