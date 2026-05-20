# 05 BM25 RAG 온톨로지 융합 구현 추적도

## 1. 원문 문서

- `req_doc_hub/분석/05_BM25_RAG_온톨로지_융합_구현.md`

## 2. 핵심 요구/설계

- 문서 데이터
- 온톨로지 저장소
- BM25 검색기
- 질문에서 객체 식별
- 온톨로지 컨텍스트 구성
- 검색 질의 강화
- RAG 컨텍스트와 프롬프트 생성
- 규칙 기반 답변 생성
- LLM 연결 지점

## 3. 구현 추적

### 3.1 문서 데이터

`src_codex`:
- `src_codex/backend/data.py`
- `DOCUMENTS`
- 문서별 `visibility`, `related_objects`, `text`

`src_anti`:
- `src_anti/backend/data.py`
- `self.documents`

판단:
- `src_codex`: 구현됨
- `src_anti`: 부분 구현

### 3.2 BM25 검색

`src_codex`:
- `src_codex/backend/search.py`
- `tokenize()`
- `BM25Search`
- `_idf()`
- `_score_document()`
- `SearchService.search()`

`src_anti`:
- `src_anti/backend/search.py`
- `SearchService.tokenize()`
- `SearchService.get_bm25_scores()`
- `SearchService.search()`

판단:
- `src_codex`: 구현됨
- `src_anti`: 부분 구현

주의:
- `src_anti`는 함수명에 BM25가 있으나 실제 구현은 토큰 등장 횟수 기반입니다.

### 3.3 객체 식별과 관계 검증

`src_codex`:
- `src_codex/backend/rag.py`
- `extract_object_ids()`
- `OntologyService.get_order_context()`
- `RELATION_MISMATCH`

`src_anti`:
- `src_anti/backend/ontology.py`
- `detect_objects()`
- `verify_relationship()`

판단:
- `src_codex`: 구현됨
- `src_anti`: 부분 구현

### 3.4 검색 질의 강화

`src_codex`:
- `RAGService.build_search_query()`
- 질문, 고객 segment, risk tier, 주문 상태, 금액, 제품명, 정책 키워드 결합

`src_anti`:
- 질문 원문 중심 검색
- 별도 질의 강화 함수 없음

판단:
- `src_codex`: 구현됨
- `src_anti`: 미구현에 가까운 부분 구현

### 3.5 프롬프트와 답변 생성

`src_codex`:
- `RAGService.build_prompt()`
- `LLMGateway.generate_rule_based_answer()`

`src_anti`:
- `RAGService.generate_answer()`
- 프롬프트 생성 없음
- 휴리스틱 답변 생성

판단:
- `src_codex`: 구현됨
- `src_anti`: 부분 구현

## 4. 요약

`05` 문서의 BM25/RAG/온톨로지 융합 흐름은 `src_codex`가 더 충실합니다. `src_anti`는 화면 표시용 RAG 유사 흐름을 구현했지만, BM25와 프롬프트 생성은 단순화되어 있습니다.
