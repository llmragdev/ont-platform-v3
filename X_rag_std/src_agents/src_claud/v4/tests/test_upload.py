import io


def test_upload_txt_completes(client):
    content = b"This is a test document.\n\nSecond paragraph for semantic chunking."
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", io.BytesIO(content), "text/plain")},
        data={"category_mid": "IT"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["pipeline_status"] == "pending"
    assert data["data"]["doc_id"].startswith("doc_")
    assert data["data"]["version"] == 1


def test_upload_respects_explicit_vector_db_id(client):
    content = b"Policy document content."
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("policy.txt", io.BytesIO(content), "text/plain")},
        data={"category_mid": "규정", "vector_db_id": "vdb_policy_01"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["assigned_vector_db"] == "vdb_policy_01"


def test_list_documents_returns_uploaded(client):
    client.post(
        "/api/v1/documents/upload",
        files={"file": ("a.txt", io.BytesIO(b"doc a"), "text/plain")},
        data={"category_mid": "IT"},
    )
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1


def test_delete_document(client):
    upload = client.post(
        "/api/v1/documents/upload",
        files={"file": ("del.txt", io.BytesIO(b"to be deleted"), "text/plain")},
        data={"category_mid": "IT"},
    )
    doc_id = upload.json()["data"]["doc_id"]

    response = client.delete(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True
