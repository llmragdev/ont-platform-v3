# src_antigravity/v3 개선 제안

작성일: 2026-05-15  
작성: Claude Code  
비교 기준: `src_claud/v3` (테스트 17/17 통과, v1.3 표준 준수)

---

## 개선 우선순위 요약

| 순위 | 항목 | 영향도 | 난이도 |
|------|------|--------|--------|
| 1 | 테스트 격리 (pydantic_settings + Gateway mock) | 🔴 치명 | 중 |
| 2 | Vector adapter embedding boundary 위반 수정 | 🔴 치명 | 중 |
| 3 | `org_id=None` → `org_id=""` sentinel 통일 | 🟠 높음 | 낮음 |
| 4 | Chroma 어댑터 추가 | 🟠 높음 | 높음 |
| 5 | `pipeline_status="pending"` 즉시 반환 | 🟡 중간 | 중 |
| 6 | `datetime.utcnow()` → timezone-aware | 🟡 중간 | 낮음 |
| 7 | FastAPI `on_event` → `lifespan` | 🟡 중간 | 낮음 |
| 8 | 감사 로그(AuditLog) 추가 | 🟢 낮음 | 중 |

---

## 1. 테스트 격리 (최우선)

### 현재 문제

`test_v3_standard.py`는 두 가지 이유로 실행 불가:

**문제 1: `pydantic_settings` 패키지 미설치**

```python
# core/config.py
from pydantic_settings import BaseSettings  # ImportError 발생
```

**문제 2: Gateway 실서버 의존**

```python
# test_v3_standard.py:88
response_search = client.post("/api/v1/rag/search", ...)
# Gateway가 없으면 500 반환 — 테스트가 스스로 500을 허용하도록 작성됨
if response_search.status_code == 500:
    assert "Gateway" in response_search.json()["detail"]  # 의미 없는 검증
```

**문제 3: 모듈 스코프 공유 DB**

```python
@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # 모든 테스트가 동일 DB 상태 공유 → 테스트 간 오염
```

### 개선 방법

**Step 1. requirements.txt에 추가**

```
pydantic-settings>=2.0.0
pytest>=7.0.0
pytest-asyncio>=0.23.0
httpx>=0.26.0
```

**Step 2. `conftest.py` 신설 — 인메모리 DB + Gateway mock**

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock

from main import app
from db.session import get_db
from models.db_models import Base


@pytest.fixture
def test_db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db_engine):
    TestSession = sessionmaker(bind=test_db_engine, autocommit=False, autoflush=False)
    session = TestSession()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def mock_gateway():
    """LlmGatewayClient를 완전 mock — 외부 의존 없는 격리 실행."""
    with patch("services.gateway_client.LlmGatewayClient") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.embed_text.return_value = [0.1] * 128
        mock_instance.generate_answer.return_value = "mock answer"
        mock_instance.cosine_similarity.return_value = 0.85
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def client(db_session, mock_gateway):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app, headers={"X-Tenant-ID": "test_tenant"}) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def client_no_tenant(db_session, mock_gateway):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
```

**Step 3. 각 테스트 파일 분리 — 함수 스코프 격리**

```python
# tests/test_upload.py
def test_upload_without_tenant_header(client_no_tenant):
    resp = client_no_tenant.post(
        "/api/v1/documents/upload",
        data={"category_mid": "test"},
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code == 400
    assert "X-Tenant-ID" in resp.json()["detail"]
```

---

## 2. Vector Adapter Embedding Boundary 위반 수정

### 현재 문제

```python
# services/vector_db.py:27 — adapter가 embedding 직접 생성
def add_documents(self, texts, metadatas):
    for text, meta in zip(texts, metadatas):
        embedding = self.gateway.embed_text(text, tenant_id=meta.get("tenant_id", "default"))
        # ↑ adapter가 Gateway를 직접 호출 → 벡터 공간 불일치 위험
```

RAG 표준 v1.3 §3.2: **embedding 생성은 pipeline에서, adapter는 저장만 담당한다.**

adapter가 embedding을 직접 생성하면:
- pipeline에서 사용하는 embedding 모델과 adapter의 모델이 달라질 수 있음
- 검색 시 query vector와 저장 vector의 공간이 불일치 → similarity 오류
- adapter를 교체할 때마다 embedding 로직도 함께 수정 필요

### 개선 방법

**BaseVectorDbAdapter에 `embeddings=` 명시 인터페이스 추가**

```python
# services/vector_db.py — 수정안
class BaseVectorDbAdapter:
    def add_documents(
        self,
        texts: list[str],
        metadatas: list[dict],
        embeddings: list[list[float]],  # pipeline에서 생성한 벡터 수신
    ):
        raise NotImplementedError

    def search(self, query_vector: list[float], tenant_id: str, org_id: str = None, top_k: int = 5):
        raise NotImplementedError


class LocalJsonVectorDbAdapter(BaseVectorDbAdapter):
    def __init__(self, vector_db_id: str):
        self.vector_db_id = vector_db_id
        self.storage_path = f"storage/{vector_db_id}.json"
        os.makedirs("storage", exist_ok=True)
        # gateway 의존 제거

    def add_documents(self, texts, metadatas, embeddings):
        data = self._load_data()
        for text, meta, emb in zip(texts, metadatas, embeddings):
            data.append({"content": text, "metadata": meta, "embedding": emb})
        self._save_data(data)
```

**pipeline에서 embedding 생성 후 전달**

```python
# services/pipeline.py — 수정안
from services.gateway_client import LlmGatewayClient

class DocumentPipelineService:
    def __init__(self, db):
        self.doc_repo = DocRepository(db)
        self.gateway = LlmGatewayClient()  # pipeline이 소유

    def process_upload(self, tenant_id, project_code, file, org_id=None):
        # ... 파싱, 청킹 ...
        
        # embedding 생성 — pipeline 책임
        embeddings = [
            self.gateway.embed_text(chunk, tenant_id=tenant_id)
            for chunk in chunks
        ]
        
        adapter = VectorDbRouter.get_adapter(vector_db_id=doc_record.assigned_vector_db)
        adapter.add_documents(chunks, metadata_list, embeddings=embeddings)
```

---

## 3. `org_id=None` → `org_id=""` Sentinel 통일

### 현재 문제

```python
# services/vector_db.py:60,64 — None으로 전사 공유 문서 판별
if meta.get("dept_code") == dept_code or meta.get("org_id") is None:
    match = True
# ...
if meta.get("org_id") == org_id or meta.get("org_id") is None:
    match = True
```

JSON 파일 저장 시 Python `None` → `null`로 직렬화된다. 재로드 시 `None`으로 복원되므로 현재는 동작하지만, **Chroma로 전환 시 `None` metadata는 저장 불가**하여 동작이 깨진다.

### 개선 방법

```python
# services/pipeline.py — _create_standard_chunks 수정
meta = {
    "doc_id": doc_record.doc_id,
    "tenant_id": doc_record.tenant_id,
    "org_id": doc_record.org_id or "",      # None → "" sentinel
    "dept_code": doc_record.dept_code or "", # None → ""
    # ...
}
```

```python
# services/vector_db.py — OR 조건 수정
if not org_id:
    match = True
elif org_id.endswith("00"):
    if meta.get("dept_code") == dept_code or meta.get("org_id") == "":
        match = True
else:
    if meta.get("org_id") == org_id or meta.get("org_id") == "":
        match = True
```

---

## 4. Chroma 어댑터 추가

현재 `LocalJsonVectorDbAdapter`만 존재 — 운영 규모(수십만 벡터) 한계.

### 개선 방법

```python
# services/vector_db.py — ChromaVectorDbAdapter 추가
import chromadb

class ChromaVectorDbAdapter(BaseVectorDbAdapter):
    def __init__(self, vector_db_id: str, host: str = "localhost", port: int = 8001):
        self.client = chromadb.HttpClient(host=host, port=port)
        self.collection = self.client.get_or_create_collection(
            name=vector_db_id,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, texts, metadatas, embeddings):
        ids = [f"{m['doc_id']}#chunk{i}" for i, m in enumerate(metadatas)]
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def search(self, query_vector, tenant_id, org_id=None, top_k=5):
        where = self._build_where(tenant_id, org_id)
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where,
        )
        return [
            {"content": doc, "metadata": meta, "score": 1 - dist}
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]

    def _build_where(self, tenant_id, org_id):
        if not org_id:
            return {"tenant_id": {"$eq": tenant_id}}
        dept_code = org_id[:2] if len(org_id) >= 2 else org_id
        if org_id.endswith("00"):
            return {
                "$and": [
                    {"tenant_id": {"$eq": tenant_id}},
                    {"$or": [{"dept_code": {"$eq": dept_code}}, {"org_id": {"$eq": ""}}]},
                ]
            }
        return {
            "$and": [
                {"tenant_id": {"$eq": tenant_id}},
                {"$or": [{"org_id": {"$eq": org_id}}, {"org_id": {"$eq": ""}}]},
            ]
        }


class VectorDbRouter:
    @staticmethod
    def get_adapter(vector_db_id: str = None) -> BaseVectorDbAdapter:
        db_id = vector_db_id or "vdb_default_01"
        engine = os.environ.get("VECTOR_DB_ENGINE", "local_json")
        if engine == "chroma":
            host = os.environ.get("CHROMA_HOST", "localhost")
            port = int(os.environ.get("CHROMA_PORT", "8001"))
            return ChromaVectorDbAdapter(db_id, host, port)
        return LocalJsonVectorDbAdapter(db_id)
```

---

## 5. `pipeline_status="pending"` 즉시 반환

### 현재 문제

```python
# services/pipeline.py:28 — 동기 처리, API가 완료까지 블로킹
self.doc_repo.update_status(doc_id, "processing")
# ... embedding + 벡터 저장 동기 실행 ...
self.doc_repo.update_status(doc_id, "completed")
return doc_record  # 완료 후 반환 → 느린 응답
```

### 개선 방법

```python
# api/documents.py — FastAPI endpoint를 async로 변경
@router.post("/api/v1/documents/upload")
async def upload_document(
    file: UploadFile,
    ...
    background_tasks: BackgroundTasks,
):
    # RDBMS에 pending 등록 후 즉시 반환
    doc_record = await service.create_pending(tenant_id, project_code, file, org_id)
    background_tasks.add_task(service.run_pipeline_background, doc_record)
    return {"doc_id": doc_record.doc_id, "pipeline_status": "pending"}
```

또는 `asyncio.to_thread` + 독립 Session 패턴 (src_claud/v3 방식):

```python
# services/pipeline.py
import asyncio

def _run_pipeline_isolated(doc_id, tenant_id, file_content, filename, vector_store_dir):
    """별도 스레드 + 독립 Session으로 실행."""
    from db.session import SessionLocal
    db = SessionLocal()
    try:
        # ... pipeline 로직 ...
    finally:
        db.close()

async def process_upload_async(self, ...):
    doc_record = self.doc_repo.create_doc(...)
    # pending 즉시 반환 — background에서 처리
    asyncio.create_task(
        asyncio.to_thread(_run_pipeline_isolated, doc_record.doc_id, ...)
    )
    return doc_record
```

---

## 6. `datetime.utcnow()` → timezone-aware

### 현재 문제

```python
# models/db_models.py:13
created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
# Python 3.12+ DeprecationWarning, 3.14에서 제거 예정
```

### 개선 방법

```python
# models/db_models.py
from datetime import datetime, timezone

class Tenant(Base):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

class ProjectRagDoc(Base):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
```

---

## 7. FastAPI `on_event` → `lifespan`

### 현재 문제

```python
# main.py:8
@app.on_event("startup")  # FastAPI 0.93+ deprecated
def startup_event():
    init_db()
```

### 개선 방법

```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Antigravity RAG API v3", lifespan=lifespan)
```

---

## 8. 감사 로그(AuditLog) 추가

### 현재 상태

검색 이력 및 접근 로그 없음 — 엔터프라이즈 요건(컴플라이언스, 이상 접근 감지) 미충족.

### 개선 방법

**모델 추가 (src_claud/v3의 `AuditLog` 참조)**

```python
# models/db_models.py
class AuditLog(Base):
    __tablename__ = "wc_audit_log"
    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    org_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)   # SEARCH, UPLOAD, DELETE
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        ForeignKeyConstraint(["tenant_id"], ["ca_tenant.tenant_id"]),
    )
```

**RAG 서비스에서 기록**

```python
# services/rag_service.py
def search(self, query, tenant_id, org_id=None, ...):
    results = self._do_search(query, tenant_id, org_id, ...)
    self.audit_repo.log(
        tenant_id=tenant_id,
        org_id=org_id,
        action="SEARCH",
        detail=f"query={query[:50]}, results={len(results)}",
    )
    return results
```

---

## 개선 후 예상 점수

| 항목 | 현재 | 개선 후 |
|------|------|---------|
| 테스트 신뢰성 | ❌ 실행 불가 | ✅ 격리 실행 |
| Embedding boundary | ❌ adapter가 직접 호출 | ✅ pipeline 위임 |
| org_id sentinel | ⚠️ None 혼용 | ✅ "" 통일 |
| Chroma 지원 | ❌ 없음 | ✅ HTTP 어댑터 |
| pending 즉시 반환 | ❌ 동기 블로킹 | ✅ background |
| datetime UTC | ❌ utcnow | ✅ timezone-aware |
| lifespan | ⚠️ deprecated | ✅ contextmanager |
| AuditLog | ❌ 없음 | ✅ 구현 |
| **종합 점수** | **7.0 / 10** | **9.5 / 10** |

> 위 개선 완료 시 Index Swap 구현 우위를 살리면서 src_claud/v3의 테스트·표준 준수도 격차도 해소된다.
