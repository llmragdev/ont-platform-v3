from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_tenant_me_loads_tenant_and_project_settings() -> None:
    response = client.get("/api/v1/tenant/me?user_id=alice")
    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["id"] == "alice"
    assert payload["user"]["company_id"] == "acme"
    assert payload["user"]["project_id"] == "proj-001"
    assert payload["user"]["permissions"]["can_edit_object"] is True
    assert payload["tenant_settings"]["display_name"] == "ACME Corp"
    assert payload["project_settings"]["display_name"] == "ACME Sales"
    assert "paths" not in payload
    assert "JWT_SECRET" not in str(payload)


def test_tenant_me_can_include_debug_paths() -> None:
    response = client.get("/api/v1/tenant/me?user_id=alice&include_paths=true")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert paths["raw"].endswith("storage\\acme\\proj-001\\raw") or paths["raw"].endswith("storage/acme/proj-001/raw")
    assert "Codex-통합" in paths["raw"]


def test_permission_override_is_resolved() -> None:
    response = client.get("/api/v1/tenant/me?user_id=dave")
    assert response.status_code == 200
    permissions = response.json()["user"]["permissions"]
    assert response.json()["user"]["role"] == "viewer"
    assert permissions["can_edit_object"] is False
    assert permissions["can_upload_doc"] is True


def test_project_forbidden_for_other_company_project() -> None:
    response = client.get("/api/v1/tenant/me?user_id=alice&project_id=proj-002")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PROJECT_FORBIDDEN"


def test_path_traversal_user_id_is_rejected() -> None:
    response = client.get("/api/v1/tenant/me?user_id=../alice")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_STORAGE_ID"


def test_path_traversal_project_id_is_rejected() -> None:
    response = client.get("/api/v1/tenant/me?user_id=alice&project_id=..\\proj-001")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_STORAGE_ID"


def test_missing_settings_files_fall_back_to_safe_defaults(tmp_path, monkeypatch) -> None:
    project_root = tmp_path / "storage" / "acme" / "proj-001"
    for leaf in ("raw", "vector_db", "ontology", "uploads"):
        (project_root / leaf).mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path / "storage"))

    response = client.get("/api/v1/tenant/me?user_id=alice")
    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_settings"]["display_name"] == "Default Tenant"
    assert payload["project_settings"]["display_name"] == "Default Project"


def test_dev_user_mode_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setenv("ALLOW_DEV_USER", "false")
    response = client.get("/api/v1/tenant/me?user_id=alice")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"
