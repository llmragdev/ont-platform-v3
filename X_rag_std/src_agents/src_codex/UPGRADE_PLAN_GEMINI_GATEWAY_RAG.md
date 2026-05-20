# src_codex Gemini Gateway RAG 업그레이드 계획

## 목표

`src_codex`의 장점인 작은 범위, 실행 안정성, 명확한 RAG 루프를 유지하면서 `src_claud/v2`에서 확인된 운영형 구조를 선별 도입한다.

핵심 목표는 다음과 같다.

- Gemini API 키는 RAG 서버가 보유하지 않고 `llm_gateway`가 중앙 관리한다.
- `src_codex`는 Gemini LLM/embedding을 HTTP gateway client로만 호출한다.
- 문서/검색/대화 이력/벡터 metadata에 `company_id`를 포함해 멀티테넌트 검색 격리를 보장한다.
- `debug_mode=false`에서는 후보 청크가 노출되지 않고, `debug_mode=true`에서만 `candidate_chunks`가 반환된다.
- 기존 local hash/mock 동작은 테스트와 오프라인 실행을 위해 유지한다.

## 단계

### 1. Provider 구조 도입

환경변수로 런타임 provider를 선택한다.

```text
EMBEDDING_PROVIDER=hash | gemini_http
LLM_PROVIDER=mock | gemini_http
LLM_GATEWAY_URL=http://localhost:8010
```

추가 파일:

- `app/services/providers.py`
- `app/services/gemini_http_embedding.py`
- `app/services/gemini_http_llm.py`

### 2. Gemini Gateway 연동

RAG 서버는 Gemini API key를 읽지 않는다. `LLM_GATEWAY_URL`만 사용한다.

연동 endpoint:

- `POST /api/v1/embed`
- `POST /api/v1/generate`
- `POST /api/v1/generate/stream`은 다음 단계에서 도입

### 3. 멀티테넌트 격리

API 요청에서 `X-Company-ID` 헤더를 읽고 기본값은 `default`로 둔다.

적용 위치:

- `wc_project_rag_doc.company_id`
- `wc_dialog_history.company_id`
- vector chunk metadata `company_id`
- 검색 adapter filter에 `company_id` 강제 주입

### 4. Metadata 표준화

검색 응답과 debug 후보 청크에서 아래 metadata를 유지한다.

- `doc_id`
- `company_id`
- `source_name`
- `source_url`
- `page_no`
- `category_mid`
- `category_low`
- `vector_db_id`
- `chunk_type`
- `tags`

### 5. 테스트 정리

기존 script smoke test는 유지하되, pytest 기반 테스트를 추가한다.

필수 검증:

- 업로드 성공
- 검색 성공
- debug 모드 후보 청크 노출 조건
- company A/B 검색 격리
- Gemini gateway client 요청 contract

### 6. 다음 단계 후보

1차 구현 후 다음 항목을 순차 적용한다.

- `DELETE /api/v1/documents/{doc_id}`
- `POST /api/v1/rag/search/stream`
- Chroma adapter 추가
- Projects/Categories API 추가

## 완료 상태

아래 항목은 구현 및 검증 완료했다.

- provider factory 추가
- Gemini HTTP LLM/embedding client 추가
- `company_id` 기반 업로드/검색 격리
- metadata 표준화
- pytest 테스트 추가
- 문서 삭제 API
- streaming search API
- Chroma adapter
- Projects API
- Categories API
- README 최신화

검증 결과:

```text
pytest -q
14 passed

python test_endpoints.py
ALL TESTS PASSED
```

## 1차 구현 범위

이번 업그레이드의 1차 범위는 다음이다.

1. provider factory 추가
2. Gemini HTTP LLM/embedding client 추가
3. `company_id` 기반 업로드/검색 격리
4. metadata 표준화
5. pytest 테스트 추가 및 통과

## 2차 구현 범위

2차 후보였던 아래 항목도 완료했다.

1. `DELETE /api/v1/documents/{doc_id}`
2. `POST /api/v1/rag/search/stream`
3. `VECTOR_DB_ENGINE=chroma` adapter
4. `POST/GET/DELETE /api/v1/projects`
5. `POST/GET/DELETE /api/v1/categories`

Chroma adapter는 문서 저장 시에도 현재 embedding provider를 사용해
`embeddings=`를 명시적으로 전달한다. 따라서 Gemini gateway embedding으로 문서를
저장하면 검색 query embedding도 같은 gateway embedding 공간을 사용한다.

## 남은 개선 후보

- Alembic 기반 정식 migration 도입
- timezone-aware UTC timestamp 적용
- Chroma 서버가 실제로 떠 있는 실서버 통합 테스트 추가
- Gemini gateway 실서버 통합 테스트 추가
