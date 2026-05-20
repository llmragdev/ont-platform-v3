# src_antigravity v2 RAG 표준 설계 준수 평가

검토일: 2026-05-14

검토 대상:

- `E:\ontology_edu\X_rag_std\RAG_표준_설계_v1.0.md`
- `E:\ontology_edu\X_rag_std\details\01_Document_Embedding_Pipeline.md`
- `E:\ontology_edu\X_rag_std\details\02_VectorDB_Management_Routing.md`
- `E:\ontology_edu\X_rag_std\details\03_RAG_Search_API.md`
- `E:\ontology_edu\X_rag_std\details\04_RDBMS_Schema_Design.md`
- `E:\ontology_edu\X_rag_std\src_agents\src_antigravity\v2`

## 총평

`src_antigravity/v2`는 v1의 mock 성격을 벗어나 계층 구조와 실제 Local JSON VectorDB, SQLAlchemy RDBMS 저장, Gemini LLM Gateway 호출을 도입했다. `api`, `models`, `repositories`, `services`로 분리되어 있고, 업로드 후 청킹/임베딩/검색/답변 생성까지 한 흐름으로 동작한다.

테스트도 현재 통과한다.

```text
pytest -q test_endpoints_v2.py
1 passed
```

하지만 RAG 표준 설계 v1.0과 상세 설계 기준으로 보면 아직 “프로토타입을 벗어난 개선판” 수준이며, 운영 후보로 보기에는 미흡하다. 특히 PDF 파싱이 mock fallback에 가깝고, 라우팅 레지스트리가 하드코딩이며, RDBMS 스키마가 상세설계 04보다 부족하고, tenant 격리/Chroma/metadata 표준화가 없다.

## 표준 설계 준수 매트릭스

| 기준 | 평가 | 근거 |
|---|---:|---|
| PEP 8, snake_case/PascalCase | 보통 | 대체로 준수하나 타입/라인 정리 등은 더 다듬을 수 있음 |
| FastAPI/Pydantic API | 보통 | upload/search API와 Pydantic 모델 구현 |
| Raw/Processed 저장소 분리 | 미흡 | 원본 파일 저장/processed 저장소 분리가 제대로 구현되지 않음 |
| 문서 상태 전이 | 부분 준수 | `pending -> processing -> completed/error` 상태 업데이트 있음 |
| 비동기/스레드풀 파이프라인 | 부분 준수 | API에서 `asyncio.to_thread()` 사용. 동일 Session thread 사용 리스크 있음 |
| 증분 업데이트 | 미준수 | `PUT /api/v1/documents/{doc_id}` 없음 |
| VectorDB 물리/논리 분리 | 부분 준수 | `vector_db_id`별 JSON 파일 분리는 있음. 라우팅 registry는 없음 |
| 라우터/어댑터 패턴 | 부분 준수 | `VectorDbRouter`, LocalJson adapter는 있으나 Base adapter/엔진 확장성은 약함 |
| Chroma/Qdrant/FAISS 엔진 구조 | 미준수 | local_json만 구현 |
| Remote Retriever | 부분 준수 | LangChain 비의존, adapter 검색 후 Gateway 호출. 다만 gateway fallback이 mock 벡터 |
| Gemini LLM Gateway 키 분리 | 부분 준수 | RAG 서버는 Gateway URL만 사용. company_id는 default 하드코딩 |
| RAG Search API 레이아웃 | 보통 | `used_chunks`, `debug_info.candidate_chunks` 구현 |
| debug mode 후보 청크 노출 | 양호 | `debug_mode=True`일 때만 debug_info 생성 |
| RDBMS 주요 테이블 | 미흡 | 일부 테이블만 구현. `ca_org_mgnt`, `wc_intent`, vector_db_id/category FK 등 부족 |
| 표준 오류 응답 | 미흡 | 일반 예외가 표준 error JSON으로 충분히 정규화되지 않음 |
| 테스트 범위 | 미흡 | 1개 통합 테스트만 존재. 표준 compliance 리스크 대부분 미검증 |

## 주요 Findings

### 1. High: 실제 PDF 파싱이 아니라 UTF-8 decode + mock fallback에 가깝다

상세설계 01은 PDF/DOCX 등 문서 파싱과 청킹을 요구한다. 현재 `pipeline.py`는 업로드 파일 bytes를 UTF-8 decode하고, 텍스트가 비어 있으면 mock 문자열을 사용한다.

```python
content = file.file.read()
text_content = content.decode('utf-8', errors='ignore')
if not text_content.strip():
    text_content = "실제 PDF나 바이너리 텍스트 추출 결과입니다. (Mock)"
```

PDF 테스트가 통과하더라도 실제 PDF 텍스트 품질을 검증하는 것이 아니라, 바이너리 decode 결과 또는 mock fallback을 청킹하는 구조다.

수정 권장:

- PDF는 `pypdf.PdfReader` 등으로 page별 텍스트 추출
- DOCX는 `python-docx` 지원
- page별 `page_no` metadata 보존
- 빈 추출 결과는 mock 대체가 아니라 `document_parsing_error` 처리

### 2. High: VectorDB 라우팅 registry가 없고 `vdb_{category_mid}_01` 하드코딩이다

상세설계 02는 JSON/YAML 또는 RDBMS 기반 routing registry를 요구한다. 현재 `VectorDbRouter.get_adapter()`는 다음 규칙으로만 동작한다.

```python
target_db_id = f"vdb_{category_mid}_01" if category_mid else "vdb_default_01"
```

이는 설계서의 물리 DB 라우팅 config, engine_type, host, port, collection_name 구조를 반영하지 못한다.

수정 권장:

- `storage/vector_routing.json` 또는 RDBMS 라우팅 테이블 도입
- `vector_db_id`, `target_category_mid`, `engine_type`, `connection` 구조 사용
- LocalJson/Chroma/Qdrant 등 adapter 선택을 registry 기반으로 수행

### 3. High: RDBMS 스키마가 상세설계 04에 크게 미달한다

상세설계 04는 다음 주요 테이블을 요구한다.

- `ca_company`
- `ca_org_mgnt`
- `ca_user`
- `wc_project`
- `wc_category`
- `wc_intent`
- `wc_project_rag_doc`
- `wc_dialog_history`

현재 구현은 `ca_company`, `ca_user`, `wc_project`, `wc_category`, `wc_project_rag_doc`, `wc_dialog_history` 정도만 있으며 `ca_org_mgnt`, `wc_intent`가 없다. 또한 `Company.company_id`, `User.user_id`가 integer autoincrement라 상세 설계의 legacy-compatible 문자열 ID 방향과도 다르다.

수정 권장:

- `ca_org_mgnt`, `wc_intent` 추가
- `wc_project.vector_db_id`, `wc_category.vector_db_id` 추가
- `wc_project_rag_doc`에 `category_mid`, `category_low`, `error_message`, `version`, `updated_at`, `company_id` 추가
- migration 전략 도입

### 4. High: 동일 SQLAlchemy Session을 `asyncio.to_thread()`로 넘긴다

API 계층은 `DocumentPipelineService(db)`를 만든 뒤 `pipeline_service.process_upload`을 `asyncio.to_thread()`로 실행한다. 이 서비스 내부 repository는 요청 thread에서 생성된 같은 SQLAlchemy Session을 들고 있다.

SQLAlchemy Session은 thread-safe하지 않다. 검색 API도 같은 방식으로 `RagSearchService(db)`를 thread에 넘긴다.

관련 파일:

- `api/documents.py`
- `api/search.py`
- `services/pipeline.py`
- `services/rag_service.py`

수정 권장:

- thread 내부에서 새 Session 생성
- 또는 DB 작업은 request thread에서 하고, 파일 추출/임베딩/Gateway 호출만 thread로 분리
- 장기적으로 background worker 구조 도입

### 5. Medium: LLM Gateway fallback이 조용히 mock 벡터 `[0.1, 0.2]`를 반환한다

`LlmGatewayClient.embed_text()`는 Gateway 호출 실패 시 예외를 숨기고 `[0.1, 0.2]`를 반환한다.

```python
except Exception as e:
    print(f"Error during embedding: {e}")
    return [0.1, 0.2]
```

이 구조는 장애를 테스트 통과로 위장할 수 있다. 표준 설계의 `embedding_api_timeout`, `vector_db_connection_error` 같은 오류 표준과도 맞지 않는다.

수정 권장:

- Gateway 실패 시 `embedding_api_timeout` 또는 명시적 custom exception
- 테스트용 mock provider와 운영 provider를 분리
- fallback은 테스트 fixture에서만 사용

### 6. Medium: 표준 metadata가 부족하다

현재 chunk metadata는 다음 정도다.

- `source_name`
- `category_mid`
- `vector_db_id`
- `page_no`

표준 2.4의 `doc_id`, `source_url`, `created_at`, `category_low`, `chunk_type`, `tags`가 빠져 있다. 특히 `doc_id`가 vector metadata에 없으므로 문서 단위 delete/update 필터링도 어렵다.

수정 권장:

- metadata에 `doc_id`, `source_url`, `created_at`, `category_low`, `chunk_type`, `tags`, `company_id` 추가
- `ChunkMetadata` Pydantic 모델과 LocalJson 저장 metadata 일치

### 7. Medium: 증분 업데이트 API가 없다

상세설계 01은 `PUT /api/v1/documents/{doc_id}`를 통한 기존 chunk 삭제 후 새 chunk 삽입, version 증가를 요구한다. Antigravity v2에는 upload만 있고 update API가 없다.

수정 권장:

- `PUT /api/v1/documents/{doc_id}` 추가
- `delete_by_doc_id()` 구현을 위해 vector metadata에 `doc_id` 저장
- `version`, `updated_at`, `error_message` 필드 추가

### 8. Medium: tenant 격리가 없다

현재 API는 `X-Company-ID`를 받지 않고, RDBMS와 vector metadata에도 `company_id` 흐름이 없다. 엔터프라이즈 RAG에서 tenant별 분리 요구가 생기면 검색 결과가 섞일 수 있다.

수정 권장:

- `X-Company-ID` header 지원
- RDBMS와 vector metadata에 `company_id` 저장
- 검색 필터에 `company_id` 강제 주입
- Gateway 요청에도 실제 company_id 전달

### 9. Low: README의 “Production-Ready” 표현은 과장이다

README는 `v2`를 Production-Ready로 설명하지만, 현재 구현은 다음 제약이 있다.

- 실제 PDF parser 부재
- 라우팅 registry 부재
- Chroma/Qdrant 부재
- update/delete 부재
- metadata 표준 미달
- tenant 격리 없음
- Gateway 장애 fallback이 mock

표현을 “improved prototype” 또는 “v2 integration prototype” 정도로 낮추는 것이 정확하다.

## 상세 요건별 평가

### 01. Document Embedding Pipeline

준수한 점:

- `POST /api/v1/documents/upload` 구현
- `category_mid`, `category_low` 일부 입력 지원
- `pending -> processing -> completed/error` 상태 업데이트
- Local JSON VectorDB 적재
- Gateway embedding 호출 시도

미흡한 점:

- 실제 PDF/DOCX 파싱 부재
- raw/processed 물리 저장소 분리 미흡
- chunk_size/overlap 전략 미흡
- metadata 표준 미달
- update API 없음
- thread-safe하지 않은 Session 사용

평가: 5.0 / 10

### 02. VectorDB Management Routing

준수한 점:

- `vector_db_id`별 Local JSON 파일 분리
- `vector_db_id` 우선, category 기반 fallback 구현
- adapter 비슷한 구조 존재

미흡한 점:

- routing registry 없음
- engine_type/connection 설정 없음
- Chroma/Qdrant/FAISS 없음
- Base adapter interface 부재
- tenant별 분리 없음

평가: 4.5 / 10

### 03. RAG Search API

준수한 점:

- `POST /api/v1/rag/search` 구현
- `query`, `top_k`, `debug_mode`, `filters` 모델화
- `used_chunks`와 `debug_info.candidate_chunks` 구조 구현
- Gateway LLM 생성 호출 시도
- LangChain 강결합 없음

미흡한 점:

- Gateway 실패 시 mock fallback
- metadata 필수값 부족
- tenant 격리 없음
- streaming 없음
- 오류 표준화 부족

평가: 6.0 / 10

### 04. RDBMS Schema Design

준수한 점:

- 일부 domain/RAG 테이블 구현
- 문서 상태와 대화 이력 저장

미흡한 점:

- `ca_org_mgnt`, `wc_intent` 없음
- `wc_project.vector_db_id`, `wc_category.vector_db_id` 없음
- `wc_project_rag_doc` 필드 부족
- migration 없음
- legacy-compatible 스키마와 차이 큼

평가: 4.5 / 10

## 종합 점수

```text
src_antigravity/v2 표준 준수도: 5.0 / 10
```

`src_antigravity/v2`는 v1보다 명확히 발전했지만, `src_codex`와 `src_claud/v2`에 비해 표준 설계 준수 깊이와 운영 준비도가 낮다. 특히 문서 파싱, 라우팅 registry, RDBMS schema, metadata, update/delete, tenant 격리가 핵심 격차다.

## 우선 수정 순서

1. 실제 PDF/DOCX parser 도입
2. 표준 metadata 전체 추가: `doc_id`, `source_url`, `created_at`, `vector_db_id`, `category_mid`, `category_low`, `page_no`, `chunk_type`, `tags`
3. routing config 기반 `VectorDbRouter` 재구성
4. RDBMS 스키마를 상세설계 04 기준으로 확장
5. `PUT /api/v1/documents/{doc_id}`와 `delete_by_doc_id()` 구현
6. Gateway 실패 시 mock fallback 제거 및 표준 error 응답 적용
7. thread-safe DB Session 구조로 변경
8. tenant 격리 추가
9. pytest를 독립 fixture 기반으로 확장

## 결론

Antigravity v2는 “동작하는 RAG API 흐름”을 보여주는 데는 성공했다. 하지만 표준 설계 v1.0의 요구를 엄격히 적용하면 아직 운영형 구현이라기보다 개선된 통합 프로토타입이다.

세 구현 중에서는 현재 가장 낮은 준수도를 보이며, 다음 단계에서는 `src_codex`의 안정적인 provider/metadata/tenant 구조와 `src_claud/v2`의 API 확장 구조를 참고해 보강하는 것이 좋다.
