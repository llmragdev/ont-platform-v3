from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.auth import decode_token, hash_password, issue_token, verify_password
from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# --- 비밀번호 ---

def test_hash_password_format():
    encoded = hash_password("hello")
    assert encoded.startswith("pbkdf2_sha256$200000$")
    assert encoded.count("$") == 3


def test_verify_password_roundtrip():
    encoded = hash_password("hunter2")
    assert verify_password("hunter2", encoded) is True
    assert verify_password("wrong", encoded) is False


def test_verify_password_malformed():
    assert verify_password("x", "garbage") is False


# --- JWT ---

def test_jwt_roundtrip():
    token = issue_token("analyst")
    payload = decode_token(token)
    assert payload["sub"] == "analyst"
    assert payload["exp"] > payload["iat"]


def test_jwt_expired_token():
    token = issue_token("analyst", ttl=-10)
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as excinfo:
        decode_token(token)
    assert excinfo.value.status_code == 401


def test_jwt_tampered_signature():
    token = issue_token("analyst")
    head, body, _ = token.split(".")
    tampered = f"{head}.{body}.AAAA"
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        decode_token(tampered)


# --- 로그인 라우트 ---

def test_login_success(client: TestClient):
    response = client.post("/api/auth/login", json={"email": "kim.ops@example.com", "password": "analyst"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "Bearer"
    assert "access_token" in body
    assert body["user"]["role"] == "AccountManager"
    assert "password_hash" not in body["user"]


def test_login_failure(client: TestClient):
    response = client.post("/api/auth/login", json={"email": "kim.ops@example.com", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_auth_header_overrides_query(client: TestClient):
    # query는 analyst인데 헤더 토큰은 finance → 헤더가 이긴다
    token = issue_token("finance")
    response = client.get(
        "/api/me",
        params={"user": "analyst"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "FinanceManager"


def test_query_fallback_still_works(client: TestClient):
    response = client.get("/api/me", params={"user": "viewer"})
    assert response.status_code == 200
    assert response.json()["role"] == "Viewer"


def test_invalid_bearer_token_returns_401(client: TestClient):
    response = client.get("/api/me", headers={"Authorization": "Bearer not-a-token"})
    assert response.status_code == 401
