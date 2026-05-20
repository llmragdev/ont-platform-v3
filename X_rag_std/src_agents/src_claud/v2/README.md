# src_claud v2

## 환경 설치

```bash
cd E:\ontology_edu\X_rag_std\src_agents\src_claud\v2
conda create --prefix ./env python=3.11 -y
conda activate ./env
pip install -r requirements.txt
```

## 기동 순서

### 1. ChromaDB 서버 (운영 시)

```bash
pip install chromadb
chroma run --host localhost --port 8001
```

### 2. LLM Gateway

```bash
cd E:\ontology_edu\X_rag_std\src_agents\llm_gateway
uvicorn app.main:app --port 8010 --reload
```

### 3. RAG 서버

```bash
cd E:\ontology_edu\X_rag_std\src_agents\src_claud\v2
set EMBEDDING_PROVIDER=gemini_http
set LLM_PROVIDER=gemini_http
set LLM_GATEWAY_URL=http://localhost:8010
set VECTOR_DB_ENGINE=chroma
set CHROMA_HOST=localhost
set CHROMA_PORT=8001
uvicorn app.main:app --port 8000 --reload
```

API 문서: http://localhost:8000/docs

## 벡터DB 엔진 선택

| 환경변수 | 값 | 동작 |
|----------|-----|------|
| `VECTOR_DB_ENGINE` | `local_json` (기본) | JSON 파일 저장 — ChromaDB 불필요 |
| `VECTOR_DB_ENGINE` | `chroma` | ChromaDB HTTP 연결 — 프로젝트 생성 시 컬렉션 자동 생성 |
| `CHROMA_HOST` | `localhost` (기본) | ChromaDB 호스트 |
| `CHROMA_PORT` | `8001` (기본) | ChromaDB 포트 |

## 테스트

서버 기동 불필요 — TestClient + 인메모리 DB + hash/mock 프로바이더로 독립 실행.

```bash
cd E:\ontology_edu\X_rag_std\src_agents\src_claud\v2
pytest tests/ -v
```

실서버 통합 테스트 (서버 기동 후):

```bash
cd E:\ontology_edu\X_rag_std\src_agents\src_claud
pytest test_api.py -v -s
```
