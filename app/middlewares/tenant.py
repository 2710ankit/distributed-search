from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse


class TenantMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        if request.url.path == "/health":
            return await call_next(request)
        tenant_id = request.headers.get("X-Tenant-Id")

        if not tenant_id:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "X-Tenant-Id header is required"
                }
            )

        request.state.tenant_id = tenant_id

        response = await call_next(request)

        return response