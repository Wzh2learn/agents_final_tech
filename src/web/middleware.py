"""Production middleware: Bearer token auth + request logging."""
from __future__ import annotations

import logging
import os
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger("m1.middleware")

# Paths exempt from auth
_AUTH_EXEMPT_PREFIXES = (
    "/health",
    "/api/health/full",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/static/",
    "/m1",
    "/favicon.ico",
)


def _is_exempt(path: str) -> bool:
    for prefix in _AUTH_EXEMPT_PREFIXES:
        if path == prefix or path.startswith(prefix + "/") or path.startswith(prefix + "?"):
            return True
    # Exact match for /m1 page
    if path == "/m1":
        return True
    return False


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Check Authorization: Bearer <token> on non-exempt paths.

    Token is read from env M1_API_TOKEN at startup. If not set, auth is
    skipped entirely (with a warning logged once).
    """

    def __init__(self, app, token: str | None = None):
        super().__init__(app)
        self.token = token or os.environ.get("M1_API_TOKEN")
        if not self.token:
            logger.warning("M1_API_TOKEN not set, API endpoints unprotected")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.token:
            return await call_next(request)

        path = request.url.path
        if _is_exempt(path):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer ") and auth_header[7:] == self.token:
            return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={"error": {"code": "Unauthorized", "message": "Invalid or missing token"}},
        )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log each request: method, path, status, latency_ms, request_id."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info(
            f"{request.method} {request.url.path} {response.status_code} "
            f"latency_ms={latency_ms} request_id={request_id}"
        )
        response.headers["X-Request-ID"] = request_id
        return response
