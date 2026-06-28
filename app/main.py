from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from app.db.postgres import Base, engine
from app.middlewares.rate_limiter import RateLimitMiddleware
from app.middlewares.tenant import TenantMiddleware
from app.routes.documents import router as document_router
from app.routes.health import router as health_router
from app.routes.search import router as search_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Distributed Document Search Service",
    description="Multi-tenant document search prototype with Elasticsearch, Redis caching, and async indexing.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(TenantMiddleware)
app.include_router(search_router)
app.include_router(document_router)
