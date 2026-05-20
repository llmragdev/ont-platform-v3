# 09 RAG 평가와 운영 설계 추적도

## 1. 원문 문서

- `req_doc_hub/분석/09_RAG_평가와_운영_설계.md`

## 2. 핵심 요구/설계

- 테스트 질문 세트
- 객체 식별 평가
- 관계 검증 평가
- 검색 평가
- 답변 평가
- 운영 로그
- 실패 유형
- 모니터링 지표
- 배포 전 체크리스트

## 3. 구현 추적

### 3.1 평가 스크립트

`src_codex`:
- `src_codex/evaluate.py`
- RAG/온톨로지 평가 시나리오

`src_anti`:
- 별도 평가 스크립트 없음
- `src_anti/backend/test_main.py`에 일부 API 테스트 존재

판단:
- `src_codex`: 구현됨
- `src_anti`: 부분 구현

### 3.2 객체 식별과 관계 검증 평가

`src_codex`:
- `extract_object_ids()`
- `OntologyService.get_order_context()`
- `evaluate.py`
- `tests/test_services.py`

`src_anti`:
- `OntologyService.detect_objects()`
- `OntologyService.verify_relationship()`
- `test_main.py`

판단:
- `src_codex`: 구현됨
- `src_anti`: 부분 구현

### 3.3 검색과 답변 평가

`src_codex`:
- `SearchService.search()`
- `RAGService.build_search_query()`
- `LLMGateway.generate_rule_based_answer()`
- `evaluate.py`

`src_anti`:
- `SearchService.search()`
- `RAGService.generate_answer()`
- 전용 평가 스크립트 없음

판단:
- `src_codex`: 구현됨
- `src_anti`: 부분 구현

### 3.4 운영 로그

`src_codex`:
- `AuditService.record()`
- `ASK_COMPLETED`
- `ASK_FAILED`
- `latency_ms`
- `retrieved_documents`
- `detected_objects`

`src_anti`:
- `AuditService.log_event()`
- `AI_QUERY`
- `WORKFLOW_EXECUTE`
- `WORKFLOW_ERROR`

판단:
- `src_codex`: 구현됨
- `src_anti`: 부분 구현

### 3.5 실패 유형과 모니터링

`src_codex`:
- `AppError`
- `OBJECT_NOT_FOUND`
- `RELATION_MISMATCH`
- `FORBIDDEN`
- `DOCUMENT_NOT_FOUND`
- `ACTION_NOT_ALLOWED`

`src_anti`:
- FastAPI `HTTPException`
- 일부 실패는 정상 응답 메시지로 처리

판단:
- `src_codex`: 구현됨
- `src_anti`: 부분 구현

## 4. 요약

`09` 문서의 RAG 평가와 운영 설계는 `src_codex`가 더 잘 반영합니다. `src_anti`는 API 테스트와 감사 로그는 있지만, 별도 평가 스크립트와 구조화된 운영 메타데이터는 부족합니다.
