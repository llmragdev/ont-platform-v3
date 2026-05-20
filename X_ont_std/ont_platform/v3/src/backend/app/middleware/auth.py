"""HMAC Authentication Middleware v3.0.

Verifies x-signature = HMAC-SHA256(HMAC_SECRET, f"{user_id}:{timestamp}")
Only active when HMAC_SECRET env var is set.
If not set: middleware is a no-op (backward compatible with v2.0).

Headers required when active:
  x-user-id:   alice
  x-timestamp: 1716000000  (Unix epoch, within 5 min of server time)
  x-signature: <hex digest>
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

SKIP_AUTH_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc"}

_TIMESTAMP_TOLERANCE_SECONDS = 300  # 5 minutes


class HmacAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret: str | None = None) -> None:
        super().__init__(app)
        self._secret = (secret or os.getenv("HMAC_SECRET") or "").encode("utf-8")
        self._active = bool(self._secret)
        if self._active:
            logger.info("[AUTH] HMAC middleware active")
        else:
            logger.info("[AUTH] HMAC_SECRET not set — auth middleware inactive (v2 compatible mode)")

    async def dispatch(self, request: Request, call_next):
        if not self._active:
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(skip) for skip in SKIP_AUTH_PATHS):
            return await call_next(request)

        user_id = request.headers.get("x-user-id", "")
        timestamp_str = request.headers.get("x-timestamp", "")
        signature = request.headers.get("x-signature", "")

        if not (user_id and timestamp_str and signature):
            return JSONResponse({"detail": "Missing auth headers"}, status_code=401)

        try:
            ts = int(timestamp_str)
        except ValueError:
            return JSONResponse({"detail": "Invalid timestamp"}, status_code=401)

        if abs(time.time() - ts) > _TIMESTAMP_TOLERANCE_SECONDS:
            return JSONResponse({"detail": "Timestamp expired"}, status_code=401)

        expected = hmac.new(
            self._secret,
            f"{user_id}:{timestamp_str}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, signature.lower()):
            logger.warning("[AUTH] signature mismatch user=%s", user_id)
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)

        return await call_next(request)
