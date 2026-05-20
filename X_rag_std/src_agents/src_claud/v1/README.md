# src_claud v1 — 안정 버전 (개발/테스트)

버그 수정 완료된 안정 버전. 외부 API 없이 로컬에서 바로 실행 가능.

---

## 1. 환경 설치

```bash
cd E:\ontology_edu\X_rag_std\src_agents\src_claud\v1
conda create --prefix ./env python=3.11 -y
conda activate ./env
pip install -r requirements.txt
```

---

## 2. 실행

```bash
uvicorn app.main:app --reload --port 8000
```

브라우저에서 API 문서 확인: http://localhost:8000/docs

---

## 3. 환경변수 (모두 선택 — 기본값으로 동작)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `EMBEDDING_PROVIDER` | `hash` | `hash` 고정 (v1은 외부 임베딩 없음) |
| `LLM_PROVIDER` | `mock` | `mock` 고정 (v1은 외부 LLM 없음) |
| `CHUNKER_TYPE` | `semantic` | `semantic` (문단 우선) / `fixed` (700자) |
| `DATABASE_URL` | SQLite 로컬 | PostgreSQL 등으로 교체 가능 |

> v1은 `ANTHROPIC_API_KEY` 불필요. `claude` 프로바이더 선택 시 `NotImplementedError` 발생.

---

## 4. 테스트

```bash
cd E:\ontology_edu\X_rag_std\src_agents\src_claud\v1
pytest tests/ -v
```

예상 결과: **14/14 passed**

---

## 5. 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/v1/documents/upload` | 문서 업로드 + 파이프라인 (추출→청킹→임베딩→벡터 저장) |
| PUT | `/api/v1/documents/{doc_id}` | 문서 업데이트 (버전 증가 + 벡터 재삽입) |
| GET | `/api/v1/documents` | 문서 목록 조회 |
| DELETE | `/api/v1/documents/{doc_id}` | 문서 삭제 (벡터 + DB 동시 삭제) |
| POST | `/api/v1/rag/search` | RAG 검색 (질의 → 벡터 검색 → Mock LLM 답변) |
| POST | `/api/v1/rag/search/stream` | RAG 검색 SSE 스트리밍 |
| GET | `/api/v1/health` | DB · 벡터스토어 · LLM 상태 확인 |

---

## 6. 멀티테넌트

모든 요청에 `X-Company-ID` 헤더 추가:

```
X-Company-ID: company_001
```

헤더 없으면 `default` 테넌트로 처리.

---

## 7. 빠른 동작 확인 (curl)

```bash
# 문서 업로드
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "X-Company-ID: company_001" \
  -F "file=@sample.txt" \
  -F "category_mid=정책"

# RAG 검색
curl -X POST http://localhost:8000/api/v1/rag/search \
  -H "Content-Type: application/json" \
  -H "X-Company-ID: company_001" \
  -d '{"query": "휴가 정책은?", "top_k": 3}'

# 헬스체크
curl http://localhost:8000/api/v1/health
```

---

## 8. 스토리지 경로

```
v1/storage/
├── raw_documents/   ← 업로드된 원본 파일
├── processed/       ← 청킹 결과 텍스트
├── vector_store/    ← LocalJSON 벡터 DB
└── metadata.db      ← SQLite (문서 메타, 대화 이력, 감사 로그)
```
