"""Middleware for generating and propagating unique Request IDs and calculating response latency."""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.middleware.request_id")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract existing X-Request-ID (e.g. from AWS ALB) or generate a new UUID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Inject request ID into response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        # Structured request logging
        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(getattr(request.state, "current_user", None), "id", "anonymous")

        logger.info(
            "%s %s %d - %.2fms (req_id: %s, user: %s, ip: %s)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
            user_id,
            client_ip,
            extra={
                "request_id": request_id,
                "extra_fields": {
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "user_id": user_id,
                    "client_ip": client_ip,
                },
            },
        )

        return response
