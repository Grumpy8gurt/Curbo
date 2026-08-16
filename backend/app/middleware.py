from __future__ import annotations

import json
import logging
import time
from collections import defaultdict, deque
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger("curbo.requests")


class ProductionSafetyMiddleware(BaseHTTPMiddleware):
    """Apply body/rate limits, request IDs, security headers, and access logs."""

    def __init__(self, app, *, max_body_bytes: int, mutations_per_minute: int):
        super().__init__(app)
        self.max_body_bytes = max_body_bytes
        self.mutations_per_minute = mutations_per_minute
        self._mutation_windows: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid4().hex
        started = time.monotonic()

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_bytes:
                    return self._json_error(413, "Request body is too large", request_id)
            except ValueError:
                return self._json_error(400, "Content-Length must be an integer", request_id)

        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            client_host = request.client.host if request.client else "unknown"
            now = time.monotonic()
            window = self._mutation_windows[client_host]
            while window and window[0] <= now - 60:
                window.popleft()
            if len(window) >= self.mutations_per_minute:
                response = self._json_error(429, "Mutation rate limit exceeded", request_id)
                response.headers["Retry-After"] = "60"
                return response
            window.append(now)

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                json.dumps(
                    {
                        "event": "request_failed",
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                    }
                )
            )
            raise

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        if request.url.path.startswith("/api/") and not request.url.path.startswith(
            ("/api/v1/", "/api/health", "/api/live", "/api/ready")
        ):
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = "Sat, 15 Nov 2026 00:00:00 GMT"
            response.headers["Link"] = '</api/v1>; rel="successor-version"'
        logger.info(
            json.dumps(
                {
                    "event": "request_complete",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "actor": getattr(
                        getattr(request.state, "principal", None),
                        "subject",
                        "anonymous",
                    ),
                    "duration_ms": round((time.monotonic() - started) * 1000, 2),
                }
            )
        )
        return response

    @staticmethod
    def _json_error(status_code: int, detail: str, request_id: str) -> JSONResponse:
        response = JSONResponse(status_code=status_code, content={"detail": detail})
        response.headers["X-Request-ID"] = request_id
        return response
