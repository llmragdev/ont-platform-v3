# src_claud v2 Gemini Gateway RAG 구현 검토

## 검토 요약

`src_claud/v2`는 `src_codex`보다 구조적으로 확장된 구현입니다. 특히 Gemini API 키를 RAG 서버가 직접 보관하지 않고 `llm_gateway`가 중앙 관리하도록 분리한 방향은 적절합니다.

테스트 결과도 개선되었습니다.

```text
pytest -q tests
14 passed
```

다만 운영 후보로 보기 전에 아래 항목은 수정이 필요합니다.

## 주요 이슈

### 1. Chroma 운영 모드에서 문서 임베딩과 질의 임베딩이 불일치할 수 있음

`ChromaAdapter.add_documents()`는 Chroma에 `documents`와 `metadatas`만 전달하고, Gemini gateway에서 생성한 embedding을 함께 저장하지 않습니다. 반면 검색 시에는 Gemini gateway에서 만든 `query_embeddings`를 사용합니다.

이 경우 Chroma가 내부 기본 embedding function으로 문서 벡터를 만들고, 검색 질의는 Gemini embedding을 쓰게 되어 벡터 공간이나 차원이 달라질 수 있습니다.

수정 권장:

- `ChromaAdapter`에 `EmbeddingService`를 주입
- `add_documents()`에서 각 chunk의 embedding을 생성
- Chroma `add()` 호출 시 `embeddings=`도 함께 전달

### 2. 멀티테넌트 검색 격리가 아직 불완전함

API는 `X-Company-ID`를 받고 문서 목록은 회사별로 필터링하지만, 벡터DB에 저장되는 chunk metadata에는 `company_id`가 없습니다. 검색 시에도 `company_id`가 adapter filter에 강제 포함되지 않습니다.

결과적으로 회사 A가 업로드한 청크가 회사 B의 RAG 검색 결과에 섞일 수 있습니다.

수정 권장:

- chunk metadata에 `company_id` 저장
- `RagSearchService.search()`와 `stream_search()`에서 필터에 `company_id` 강제 주입
- delete/update도 `doc_id`뿐 아니라 `company_id` 확인 후 처리

### 3. `asyncio.to_thread()`에서 같은 SQLAlchemy Session을 다른 스레드로 사용함

문서 업로드/수정 파이프라인에서 `_run_pipeline()`을 `asyncio.to_thread()`로 실행하지만, 그 내부에서 같은 repository와 SQLAlchemy Session으로 상태 업데이트를 수행합니다.

SQLAlchemy Session은 스레드 세이프하지 않으므로 운영 환경에서 간헐적인 DB 오류가 날 수 있습니다.

수정 권장:

- worker thread 내부에서 새 Session을 생성
- 또는 DB 상태 업데이트는 request thread에서 처리하고, 파일 추출/임베딩/벡터 적재만 별도 thread로 분리

### 4. 검색 응답 metadata에 `vector_db_id`가 빠짐

표준 RAG 응답과 디버그 모드에서는 어떤 물리 VectorDB에서 검색된 chunk인지 추적할 수 있어야 합니다. 현재 `ChunkMetadata`에는 `vector_db_id`가 없고, 저장 metadata에도 포함되지 않습니다.

수정 권장:

- `ChunkMetadata`에 `vector_db_id` 추가
- `document_service.py`의 chunk metadata 생성 시 `assigned_vdb` 저장
- 가능하면 `page_no`도 추출 가능한 문서에서는 보존

### 5. Gemini 전용 운영 방향과 Claude/Voyage 레거시 설정이 혼재됨

현재 RAG 서버에는 `claude` provider, `ANTHROPIC_API_KEY`, `claude_embedding.py`, `claude_llm.py`가 남아 있습니다. Gemini gateway만 정식 경로라면 운영 문서에서는 Claude/Voyage 경로를 legacy 또는 비권장으로 표시하는 편이 좋습니다.

수정 권장:

- README에는 Gemini gateway 경로를 primary로 명시
- Claude/Voyage provider는 호환용 legacy로 분리 설명
- 실제 운영 env 예시에서는 `ANTHROPIC_API_KEY` 제거

### 6. README의 실서버 통합 테스트 안내 경로 확인 필요

`README.md`에는 `pytest test_api.py -v -s` 안내가 있지만 현재 `src_claud/v2` 파일 목록 기준으로는 해당 파일이 확인되지 않았습니다.

수정 권장:

- 실제 존재하는 통합 테스트 파일명으로 수정
- 또는 `test_api.py`를 추가

## 좋은 점

- Gemini API 키 관리가 `llm_gateway`로 분리되어 RAG 서버가 키를 직접 보유하지 않음
- embedding/LLM/chunker provider factory가 `providers.py`로 중앙화됨
- 테스트용 in-memory SQLite 문제가 `StaticPool` 적용으로 해결됨
- 문서 업로드, 검색, 삭제, 프로젝트, 카테고리 API까지 범위가 확장됨
- `debug_mode`일 때만 `candidate_chunks`를 반환하는 구조가 유지됨

## 결론

`src_codex`는 안정적인 기준 구현이고, `src_claud/v2`는 더 운영형에 가까운 확장 구현입니다.

현재 `src_claud/v2`는 테스트 기준으로는 통과하지만, 운영 후보가 되려면 다음 두 가지를 우선 수정해야 합니다.

1. Chroma + Gemini embedding 일관성 보장
2. `company_id` 기반 벡터 검색 격리

이 두 항목이 해결되면 `src_claud/v2`가 `src_codex`보다 상위 구현으로 보는 것이 타당합니다.
