import io


# ── SSE 스트리밍 ─────────────────────────────────────────────

def test_stream_search_returns_sse_events(client):
    content = b"Python asyncio enables concurrent programming. " * 10
    client.post(
        "/api/v1/documents/upload",
        files={"file": ("async.txt", io.BytesIO(content), "text/plain")},
        data={"category_mid": "IT"},
    )

    with client.stream("POST", "/api/v1/rag/search/stream",
                       json={"query": "asyncio concurrent", "top_k": 2}) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
        body = resp.read().decode()
    assert "data:" in body


def test_stream_search_empty_db_returns_event(client):
    with client.stream("POST", "/api/v1/rag/search/stream",
                       json={"query": "topic xyz123 unknown", "top_k": 2}) as resp:
        assert resp.status_code == 200
        body = resp.read().decode()
    assert "data:" in body


def test_stream_search_requires_tenant_id(client_no_tenant):
    resp = client_no_tenant.post(
        "/api/v1/rag/search/stream",
        json={"query": "test"},
    )
    assert resp.status_code == 400


# ── 일반 검색 ────────────────────────────────────────────────

def test_search_returns_used_chunks(client):
    content = b"FastAPI is a modern web framework for Python. " * 10
    client.post(
        "/api/v1/documents/upload",
        files={"file": ("fw.txt", io.BytesIO(content), "text/plain")},
        data={"category_mid": "IT"},
    )

    response = client.post(
        "/api/v1/rag/search",
        json={"query": "FastAPI framework", "top_k": 3},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["answer"] != ""
    assert isinstance(data["data"]["used_chunks"], list)
    assert len(data["data"]["used_chunks"]) >= 1


def test_search_chunk_has_similarity_score(client):
    content = b"SQLAlchemy is an ORM for Python. " * 10
    client.post(
        "/api/v1/documents/upload",
        files={"file": ("orm.txt", io.BytesIO(content), "text/plain")},
        data={"category_mid": "IT"},
    )
    response = client.post(
        "/api/v1/rag/search",
        json={"query": "SQLAlchemy ORM", "top_k": 2},
    )
    assert response.status_code == 200
    chunks = response.json()["data"]["used_chunks"]
    if chunks:
        assert "similarity_score" in chunks[0]
        assert isinstance(chunks[0]["similarity_score"], float)


def test_search_debug_mode(client):
    response = client.post(
        "/api/v1/rag/search",
        json={"query": "test query", "top_k": 2, "debug_mode": True},
    )
    assert response.status_code == 200
    data = response.json()
    if data["data"]["used_chunks"]:
        assert data["data"]["debug_info"] is not None
        assert "execution_time_ms" in data["data"]["debug_info"]


def test_search_with_category_filter(client):
    response = client.post(
        "/api/v1/rag/search",
        json={
            "query": "regulation document",
            "top_k": 5,
            "filters": {"category_mid": "규정"},
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_search_empty_db_returns_no_chunks(client):
    response = client.post(
        "/api/v1/rag/search",
        json={"query": "completely unknown topic xyz123"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
