# -*- coding: utf-8 -*-
"""v4 RAG 보조 엔드포인트 E2E 테스트."""

import io


def _upload_text(client, file_name: str, text: str, category_mid: str = "ontology") -> str:
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": (file_name, io.BytesIO(text.encode("utf-8")), "text/plain")},
        data={"category_large": "기술", "category_mid": category_mid},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["doc_id"]


def test_expand_query_returns_weighted_variants(client):
    response = client.post(
        "/api/v1/rag/expand-query",
        json={"query": "정책"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["original_query"] == "정책"
    queries = [item["query"] for item in payload["expanded_queries"]]
    assert "정책" in queries
    assert "규정" in queries
    assert all(0 < item["weight"] <= 1.0 for item in payload["expanded_queries"])


def test_batch_search_returns_result_for_each_query(client):
    _upload_text(
        client,
        "ontology_batch.txt",
        "온톨로지 knowledge graph semantic web RDF " * 20,
    )

    response = client.post(
        "/api/v1/rag/batch-search",
        json={
            "queries": [
                {"query": "온톨로지", "top_k": 2},
                {"query": "knowledge graph", "top_k": 2},
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert len(payload["results"]) == 2
    assert all("chunks" in result for result in payload["results"])
    assert isinstance(payload["processing_time_ms"], int)


def test_rerank_orders_chunks_by_query_term_overlap(client):
    search = client.post(
        "/api/v1/rag/search",
        json={"query": "placeholder", "top_k": 1},
    )
    assert search.status_code == 200
    template = search.json()["data"]["used_chunks"]
    if template:
        base = template[0]
    else:
        _upload_text(client, "rerank_seed.txt", "온톨로지 RDF " * 20)
        base = client.post(
            "/api/v1/rag/search",
            json={"query": "온톨로지", "top_k": 1},
        ).json()["chunks"][0]

    first = {**base, "chunk_id": "low", "content": "일반 문서", "similarity_score": 0.1}
    second = {**base, "chunk_id": "high", "content": "온톨로지 RDF 핵심 문서", "similarity_score": 0.1}

    response = client.post(
        "/api/v1/rag/rerank",
        json={"query": "온톨로지 RDF", "chunks": [first, second]},
    )

    assert response.status_code == 200
    assert response.json()["chunks"][0]["chunk_id"] == "high"


def test_advanced_endpoints_require_tenant_id(client_no_tenant):
    endpoints = [
        ("/api/v1/rag/expand-query", {"query": "정책"}),
        ("/api/v1/rag/batch-search", {"queries": [{"query": "정책"}]}),
        ("/api/v1/rag/rerank", {"query": "정책", "chunks": []}),
    ]

    for path, payload in endpoints:
        response = client_no_tenant.post(path, json=payload)
        assert response.status_code == 400
