from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

TENANT_EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class TenantMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        if request.url.path in TENANT_EXEMPT_PATHS:
            return await call_next(request)

        tenant_id = request.headers.get("X-Tenant-Id")

        if not tenant_id and request.url.path == "/search":
            tenant_id = request.query_params.get("tenant")

        if not tenant_id:
            return JSONResponse(
                status_code=400,
                content={"message": "Tenant is required via X-Tenant-Id header or tenant query param"},
            )

        request.state.tenant_id = tenant_id
        return await call_next(request)
