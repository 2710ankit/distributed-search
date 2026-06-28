import os
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.db.redis import redis_client





class RateLimitMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        RATE_LIMIT = int(os.getenv("RATE_LIMIT"))
        WINDOW = int(os.getenv("RATE_LIMIT_WINDOW"))


        tenant_id = request.headers.get("X-Tenant-Id")
        print(WINDOW,"WINDOW")
        print(RATE_LIMIT,"RATE_LIMIT")
        if tenant_id:
            key = f"rate_limit:{tenant_id}"

            current = redis_client.get(key)

            if current is None:
                redis_client.setex(key, WINDOW, 1)

            else:
                current = redis_client.incr(key)

                if current > RATE_LIMIT:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "message": "Rate limit exceeded"
                        }
                    )

        response = await call_next(request)

        return response