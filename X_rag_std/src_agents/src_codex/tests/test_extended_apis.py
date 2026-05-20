import io
import sys
import types

from app.core import config as config_module
from app.services.embeddings import HashEmbeddingService
from app.services.vector_adapters import ChromaVectorDbAdapter


def test_delete_document_removes_search_result(client):
    upload = client.post(
        "/api/v1/documents/upload",
        headers={"X-Company-ID": "company_a"},
        files={"file": ("delete.txt", io.BytesIO(b"delete marker text"), "text/plain")},
        data={"category_mid": "policy"},
    )
    doc_id = upload.json()["data"]["doc_id"]

    delete = client.delete(f"/api/v1/documents/{doc_id}", headers={"X-Company-ID": "company_a"})
    assert delete.status_code == 200
    assert delete.json()["data"]["deleted"] is True

    search = client.post(
        "/api/v1/rag/search",
        headers={"X-Company-ID": "company_a"},
        json={
            "query": "delete marker",
            "debug_mode": True,
            "filters": {"category_mid": "policy"},
        },
    )
    assert search.status_code == 200
    assert search.json()["data"]["debug_info"]["candidate_chunks"] == []


def test_stream_search_returns_sse(client):
    client.post(
        "/api/v1/documents/upload",
        headers={"X-Company-ID": "company_a"},
        files={"file": ("stream.txt", io.BytesIO(b"streaming response evidence"), "text/plain")},
        data={"category_mid": "policy"},
    )

    with client.stream(
        "POST",
        "/api/v1/rag/search/stream",
        headers={"X-Company-ID": "company_a"},
        json={"query": "streaming", "filters": {"category_mid": "policy"}},
    ) as response:
        assert response.status_code == 200
        text = "".join(response.iter_text())
    assert "data:" in text
    assert "[DONE]" in text


def test_project_and_category_apis(client):
    project = client.post(
        "/api/v1/projects",
        json={
            "project_code": "123456",
            "project_name": "테스트 프로젝트",
            "vector_db_id": "vdb_policy_01",
        },
    )
    assert project.status_code == 201
    assert project.json()["data"]["project_code"] == "123456"

    projects = client.get("/api/v1/projects")
    assert projects.status_code == 200
    assert any(item["project_code"] == "123456" for item in projects.json()["data"])

    category = client.post(
        "/api/v1/categories",
        json={
            "category_mid": "보안",
            "category_low": "접근통제",
            "vector_db_id": "vdb_policy_01",
        },
    )
    assert category.status_code == 201
    category_id = category.json()["data"]["category_id"]

    categories = client.get("/api/v1/categories")
    assert categories.status_code == 200
    assert any(item["category_id"] == category_id for item in categories.json()["data"])

    deleted = client.delete(f"/api/v1/categories/{category_id}")
    assert deleted.status_code == 200
    assert deleted.json()["data"]["deleted"] is True


def test_chroma_adapter_stores_provider_embeddings(monkeypatch):
    calls = {}

    class FakeCollection:
        def add(self, **kwargs):
            calls["add"] = kwargs

        def query(self, **kwargs):
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        def get(self, **kwargs):
            return {"ids": []}

    class FakeClient:
        def __init__(self, host, port):
            calls["client"] = {"host": host, "port": port}

        def get_or_create_collection(self, name):
            calls["collection_name"] = name
            return FakeCollection()

    fake_chromadb = types.SimpleNamespace(HttpClient=FakeClient)
    monkeypatch.setitem(sys.modules, "chromadb", fake_chromadb)
    monkeypatch.setattr(config_module.settings, "vector_db_engine", "local_json")

    adapter = ChromaVectorDbAdapter(
        vector_db_id="vdb_policy_01",
        host="localhost",
        port=8001,
        collection_name="policy",
        embedding_service=HashEmbeddingService(),
    )
    adapter.add_documents(
        [{"chunk_id": "doc_1#chunk0", "content": "policy text"}],
        [
            {
                "doc_id": "doc_1",
                "company_id": "company_a",
                "source_name": "doc.txt",
                "source_url": "/tmp/doc.txt",
                "page_no": 1,
                "category_mid": "policy",
                "vector_db_id": "vdb_policy_01",
            }
        ],
    )

    assert calls["client"] == {"host": "localhost", "port": 8001}
    assert calls["collection_name"] == "policy"
    assert "embeddings" in calls["add"]
    assert len(calls["add"]["embeddings"][0]) == 64
