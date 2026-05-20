import io


def upload_text(client, company_id: str, content: str, category_mid: str = "policy"):
    return client.post(
        "/api/v1/documents/upload",
        headers={"X-Company-ID": company_id},
        files={"file": ("doc.txt", io.BytesIO(content.encode("utf-8")), "text/plain")},
        data={"category_mid": category_mid},
    )


def test_upload_search_and_debug_mode(client):
    upload = upload_text(
        client,
        "company_a",
        "휴가 규정은 연 15일입니다. 재택근무는 부서장 승인 후 가능합니다.",
    )
    assert upload.status_code == 200
    assert upload.json()["data"]["pipeline_status"] == "completed"

    normal = client.post(
        "/api/v1/rag/search",
        headers={"X-Company-ID": "company_a"},
        json={
            "query": "휴가 규정",
            "top_k": 3,
            "debug_mode": False,
            "filters": {"category_mid": "policy"},
        },
    )
    assert normal.status_code == 200
    normal_body = normal.json()
    assert normal_body["data"]["used_chunks"]
    assert normal_body["data"]["debug_info"] is None

    debug = client.post(
        "/api/v1/rag/search",
        headers={"X-Company-ID": "company_a"},
        json={
            "query": "휴가 규정",
            "top_k": 3,
            "debug_mode": True,
            "filters": {"category_mid": "policy"},
        },
    )
    assert debug.status_code == 200
    debug_info = debug.json()["data"]["debug_info"]
    assert debug_info is not None
    assert debug_info["candidate_chunks"]
    assert debug_info["candidate_chunks"][0]["metadata"]["company_id"] == "company_a"


def test_company_id_isolation(client):
    upload_text(client, "company_a", "alpha contract renewal policy")
    upload_text(client, "company_b", "beta payroll security policy")

    response = client.post(
        "/api/v1/rag/search",
        headers={"X-Company-ID": "company_a"},
        json={
            "query": "payroll security",
            "top_k": 5,
            "debug_mode": True,
            "filters": {"category_mid": "policy"},
        },
    )
    assert response.status_code == 200
    chunks = response.json()["data"]["debug_info"]["candidate_chunks"]
    assert chunks
    assert {chunk["metadata"]["company_id"] for chunk in chunks} == {"company_a"}


def test_document_list_is_company_scoped(client):
    upload_text(client, "company_a", "company a handbook")
    upload_text(client, "company_b", "company b handbook")

    response = client.get("/api/v1/documents", headers={"X-Company-ID": "company_a"})
    assert response.status_code == 200
    records = response.json()["data"]
    assert len(records) == 1
    assert records[0]["company_id"] == "company_a"
