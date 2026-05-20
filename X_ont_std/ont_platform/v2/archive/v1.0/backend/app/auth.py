"""JWT 기반 인증 (#7).

설계 원칙:
1. 기존 ``?user=analyst`` 쿼리 호환을 유지한다 — 교육 시나리오·E2E·evaluate가 깨지지 않음.
2. Authorization 헤더의 Bearer 토큰이 있으면 그쪽을 우선 사용한다.
3. 비밀번호는 PBKDF2-HMAC-SHA256(반복 200K) 해시로만 비교한다 (표준 라이브러리만 사용).
4. 토큰은 HS256, 환경변수 ``JWT_SECRET`` 또는 기본 비밀로 서명. 기본 비밀은 교육용이며 운영 전 반드시 교체.

레이어 분리:
- ``hash_password`` / ``verify_password`` — 비밀번호 다이제스트
- ``issue_token`` / ``decode_token`` — JWT 발급/검증
- ``current_user_key`` — FastAPI dependency (헤더 → 쿼리 → 기본값 ``analyst`` 순)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Optional

from fastapi import Depends, Header, HTTPException, Query

JWT_SECRET = os.environ.get("JWT_SECRET", "claud-tonghap-education-only")
JWT_ALG = "HS256"
JWT_TTL_SECONDS = int(os.environ.get("JWT_TTL_SECONDS", "3600"))
PBKDF2_ITER = 200_000


# --- 비밀번호 --------------------------------------------------------------

def hash_password(password: str, *, salt: bytes | None = None) -> str:
    """`pbkdf2_sha256$ITER$SALT$HASH` 포맷의 인코딩된 다이제스트."""
    if salt is None:
        salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITER)
    return f"pbkdf2_sha256${PBKDF2_ITER}${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iter_str, salt_b64, hash_b64 = encoded.split("$")
    except ValueError:
        return False
    if scheme != "pbkdf2_sha256":
        return False
    iterations = int(iter_str)
    salt = base64.urlsafe_b64decode(salt_b64.encode())
    expected = base64.urlsafe_b64decode(hash_b64.encode())
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(candidate, expected)


# --- JWT (표준 라이브러리만 사용) --------------------------------------------

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + pad).encode("ascii"))


def issue_token(user_key: str, *, ttl: int | None = None, now: int | None = None) -> str:
    header = {"alg": JWT_ALG, "typ": "JWT"}
    issued = int(now if now is not None else time.time())
    payload = {
        "sub": user_key,
        "iat": issued,
        "exp": issued + (ttl if ttl is not None else JWT_TTL_SECONDS),
    }
    head_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    body_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{head_b64}.{body_b64}".encode()
    signature = hmac.new(JWT_SECRET.encode(), signing_input, hashlib.sha256).digest()
    return f"{head_b64}.{body_b64}.{_b64url_encode(signature)}"


def decode_token(token: str) -> dict:
    try:
        head_b64, body_b64, sig_b64 = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=401, detail={"error": {"code": "INVALID_TOKEN", "message": "토큰 형식이 잘못되었습니다."}}) from exc

    signing_input = f"{head_b64}.{body_b64}".encode()
    expected = hmac.new(JWT_SECRET.encode(), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _b64url_decode(sig_b64)):
        raise HTTPException(status_code=401, detail={"error": {"code": "INVALID_TOKEN", "message": "서명이 일치하지 않습니다."}})

    payload = json.loads(_b64url_decode(body_b64))
    if payload.get("exp", 0) < int(time.time()):
        raise HTTPException(status_code=401, detail={"error": {"code": "TOKEN_EXPIRED", "message": "토큰이 만료되었습니다."}})
    return payload


# --- FastAPI dependency ----------------------------------------------------

def current_user_key(
    authorization: Optional[str] = Header(default=None),
    user: str = Query(default="analyst"),
) -> str:
    """헤더의 Bearer 토큰이 있으면 토큰의 ``sub``을 반환, 없으면 쿼리 ``?user=`` 폴백.

    하위호환을 유지하기 위해 쿼리 폴백을 살려두지만, 운영 전 ``?user=`` 분기를 제거할 것.
    """
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        payload = decode_token(token)
        sub = payload.get("sub")
        if not isinstance(sub, str):
            raise HTTPException(status_code=401, detail={"error": {"code": "INVALID_TOKEN", "message": "토큰 본문이 잘못되었습니다."}})
        return sub
    return user
