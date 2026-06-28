import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.db.redis import redis_client

DEFAULT_RATE_LIMIT = 1000
DEFAULT_RATE_LIMIT_WINDOW = 60
EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class RateLimitMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        rate_limit = int(os.getenv("RATE_LIMIT", DEFAULT_RATE_LIMIT))
        window = int(os.getenv("RATE_LIMIT_WINDOW", DEFAULT_RATE_LIMIT_WINDOW))

        tenant_id = request.headers.get("X-Tenant-Id")
        if not tenant_id and request.url.path == "/search":
            tenant_id = request.query_params.get("tenant")

        if tenant_id:
            key = f"rate_limit:{tenant_id}"
            current = redis_client.incr(key)
            if current == 1:
                redis_client.expire(key, window)

            if current > rate_limit:
                return JSONResponse(
                    status_code=429,
                    content={"message": "Rate limit exceeded"},
                )

        return await call_next(request)
