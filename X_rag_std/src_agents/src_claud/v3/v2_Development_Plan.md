# src_claud v2 개발 계획

## 개요

v1(버그 수정된 안정 버전)을 베이스로 프로덕션 수준 업그레이드를 적용한 버전.

---

## v1 → v2 변경 내역

### 완료된 업그레이드

| 항목 | v1 | v2 |
|------|----|----|
| 팩토리 함수 | `document_service.py`, `rag_service.py` 각자 보유 | `providers.py` 로 중앙화 (DRY) |
| 파이프라인 실행 | `self._run_pipeline()` 동기 블로킹 | `await asyncio.to_thread(self._run_pipeline, ...)` 비동기 |
| Voyage AI 임베딩 | `NotImplementedError` 스텁 | `voyageai.Client` 실제 구현 |
| Claude LLM | `NotImplementedError` 스텁 | `anthropic.Anthropic` 실제 구현 (스트리밍 포함) |
| LLM 기반 추상 타입 | `AsyncGenerator[str, None]` (abstract async def) | `AsyncIterator[str]` (abstract def, 구현체가 async gen) |
| DB 모델 FK | FK 없음 | `ca_org_mgnt`, `ca_user`, `wc_project_rag_doc` 에 ForeignKey 추가 |
| 테스트 격리 | `scope="session"` — 테스트 간 상태 누출 가능 | 함수 스코프 — 테스트마다 독립 인메모리 DB |
| 프로젝트 관리 API | 없음 | `POST/GET/DELETE /api/v1/projects` |
| 카테고리 관리 API | 없음 | `POST/GET/DELETE /api/v1/categories` |
| 벡터DB 엔진 선택 | local_json 고정 | `VECTOR_DB_ENGINE` 환경변수로 local_json / chroma 선택 |
| ChromaDB 연동 | 미구현 | `ChromaAdapter` + localhost:8001 HTTP 연결 |
| 프로젝트 생성 시 컬렉션 | 없음 | chroma 모드 시 프로젝트 생성 즉시 컬렉션 자동 생성 |
| 의존성 | `requirements.txt` 기본 | `voyageai>=0.2.0`, `chromadb>=0.5.0` 추가 |

---

## 파일 구조

```
v2/app/
├── api/
│   ├── projects.py       ← 프로젝트 CRUD (신규)
│   ├── categories.py     ← 카테고리 CRUD (신규)
│   ├── documents.py      ← project_code Form 파라미터 추가
│   ├── search.py
│   └── health.py
├── core/
│   ├── config.py         ← VECTOR_DB_ENGINE, CHROMA_HOST/PORT 추가
│   ├── errors.py         ← ProjectNotFoundError 추가
│   └── events.py         ← 서버 시작 시 기본 프로젝트 000001 시딩
├── repositories/
│   ├── project_repo.py   ← wc_project CRUD (신규)
│   └── category_repo.py  ← wc_category CRUD (신규)
├── services/
│   ├── project_service.py    ← 프로젝트 삭제 cascade + chroma 컬렉션 생성 (신규)
│   ├── providers.py          ← embedding/LLM/chunker 팩토리 중앙화
│   ├── router.py             ← VECTOR_DB_ENGINE 우선 적용
│   ├── document_service.py   ← asyncio.to_thread + project_code 전달
│   ├── rag_service.py        ← providers 사용
│   ├── embedding/
│   │   ├── claude_embedding.py    ← voyageai.Client 실제 구현
│   │   └── gemini_http_embedding.py ← LLM Gateway 경유
│   ├── llm/
│   │   ├── base.py           ← AsyncIterator[str] 시그니처
│   │   ├── claude_llm.py     ← anthropic.Anthropic 실제 구현
│   │   └── gemini_http_llm.py ← LLM Gateway 경유
│   └── vector_db/
│       ├── chroma.py         ← ChromaDB HttpClient (localhost:8001)
│       └── local_json.py     ← JSON 파일 기반 (개발/테스트)
```

---

## 환경변수 전체 목록

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `EMBEDDING_PROVIDER` | `hash` | hash / claude / gemini_http |
| `LLM_PROVIDER` | `mock` | mock / claude / gemini_http |
| `VECTOR_DB_ENGINE` | `local_json` | local_json / chroma |
| `CHROMA_HOST` | `localhost` | ChromaDB 호스트 |
| `CHROMA_PORT` | `8001` | ChromaDB 포트 |
| `LLM_GATEWAY_URL` | `` | http://localhost:8010 |
| `ANTHROPIC_API_KEY` | `` | Voyage/Claude 사용 시 필요 |
| `CHUNKER_TYPE` | `semantic` | semantic / fixed |
| `DATABASE_URL` | SQLite | PostgreSQL 등으로 교체 가능 |

---

## 운영 환경 전환 방법

```bash
# ChromaDB + Gemini Gateway 풀 스택
chroma run --host localhost --port 8001
cd llm_gateway && uvicorn app.main:app --port 8010

set VECTOR_DB_ENGINE=chroma
set EMBEDDING_PROVIDER=gemini_http
set LLM_PROVIDER=gemini_http
set LLM_GATEWAY_URL=http://localhost:8010
cd src_claud/v2 && uvicorn app.main:app --port 8000
```

---

## 향후 과제 (v3 후보)

| 과제 | 설명 |
|------|------|
| AsyncSession | SQLAlchemy `AsyncSession` + async repository 전면 전환 |
| 비동기 ChromaDB | `chromadb.AsyncHttpClient` 사용 |
| 벡터 DB 풀링 | 어댑터 인스턴스 재사용 (현재 요청마다 생성) |
| JWT 인증 | X-Company-ID 헤더 → Bearer 토큰 검증 |
| 마이그레이션 | Alembic 기반 DB 스키마 버전 관리 |
| 멀티프로세싱 | `_run_pipeline` → Celery/ARQ 비동기 작업 큐 |
| wc_category ↔ routing.json 자동 연동 | 카테고리 등록 시 routing.json 자동 갱신 |
