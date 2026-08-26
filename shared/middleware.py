"""HTTP middleware used by the app shell."""

from __future__ import annotations

from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from shared.logger import bind_request_context


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        tenant_id = request.headers.get("X-Tenant-ID", "default")
        bind_request_context(correlation_id=correlation_id, tenant_id=tenant_id)
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


class IdempotencyStore:
    """In-memory idempotency key store for write-triggering agent actions."""

    def __init__(self) -> None:
        self._keys: dict[str, dict] = {}

    def get(self, key: str) -> dict | None:
        return self._keys.get(key)

    def set(self, key: str, response: dict) -> None:
        self._keys[key] = response
