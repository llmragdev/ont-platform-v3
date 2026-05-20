import io


def upload_text(client, tenant_id: str, content: str, category_mid: str = "policy"):
    return client.post(
        "/api/v1/documents/upload",
        headers={"X-Tenant-ID": tenant_id},
        files={"file": ("doc.txt", io.BytesIO(content.encode("utf-8")), "text/plain")},
        data={"category_mid": category_mid},
    )


def upload_text_for_org(
    client,
    tenant_id: str,
    org_id: str | None,
    content: str,
    category_mid: str = "policy",
):
    headers = {"X-Tenant-ID": tenant_id}
    if org_id is not None:
        headers["X-Org-ID"] = org_id
    return client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("doc.txt", io.BytesIO(content.encode("utf-8")), "text/plain")},
        data={"category_mid": category_mid},
    )


def test_upload_without_tenant_header_returns_400(client):
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("doc.txt", io.BytesIO(b"hello"), "text/plain")},
        data={"category_mid": "policy"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"]["error_code"] == "tenant_header_required"


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
        headers={"X-Tenant-ID": "company_a"},
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
        headers={"X-Tenant-ID": "company_a"},
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
    assert debug_info["candidate_chunks"][0]["metadata"]["tenant_id"] == "company_a"


def test_tenant_id_isolation(client):
    upload_text(client, "company_a", "alpha contract renewal policy")
    upload_text(client, "company_b", "beta payroll security policy")

    response = client.post(
        "/api/v1/rag/search",
        headers={"X-Tenant-ID": "company_a"},
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
    assert {chunk["metadata"]["tenant_id"] for chunk in chunks} == {"company_a"}


def test_document_list_is_company_scoped(client):
    upload_text(client, "company_a", "company a handbook")
    upload_text(client, "company_b", "company b handbook")

    response = client.get("/api/v1/documents", headers={"X-Tenant-ID": "company_a"})
    assert response.status_code == 200
    records = response.json()["data"]
    assert len(records) == 1
    assert records[0]["tenant_id"] == "company_a"


def test_team_search_includes_public_and_team_only(client):
    upload_text_for_org(client, "company_a", "0102", "team only vacation policy")
    upload_text_for_org(client, "company_a", None, "public shared handbook")
    upload_text_for_org(client, "company_a", "0103", "other team confidential guide")

    response = client.post(
        "/api/v1/rag/search",
        headers={"X-Tenant-ID": "company_a", "X-Org-ID": "0102"},
        json={
            "query": "policy handbook guide",
            "top_k": 10,
            "debug_mode": True,
            "filters": {"category_mid": "policy"},
        },
    )
    assert response.status_code == 200
    chunks = response.json()["data"]["debug_info"]["candidate_chunks"]
    org_ids = {chunk["metadata"]["org_id"] for chunk in chunks}
    assert org_ids <= {"0102", None}
    assert "0103" not in org_ids


def test_department_search_includes_public_and_department(client):
    upload_text_for_org(client, "company_a", "0102", "department one team two policy")
    upload_text_for_org(client, "company_a", "0201", "department two policy")
    upload_text_for_org(client, "company_a", None, "public company policy")

    response = client.post(
        "/api/v1/rag/search",
        headers={"X-Tenant-ID": "company_a", "X-Org-ID": "0100"},
        json={
            "query": "department policy",
            "top_k": 10,
            "debug_mode": True,
            "filters": {"category_mid": "policy"},
        },
    )
    assert response.status_code == 200
    chunks = response.json()["data"]["debug_info"]["candidate_chunks"]
    org_ids = {chunk["metadata"]["org_id"] for chunk in chunks}
    assert org_ids <= {"0102", None}
    assert "0201" not in org_ids

