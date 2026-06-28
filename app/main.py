from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()


from app.db.postgres import engine
from app.db.postgres import Base
from app.middlewares.rate_limiter import RateLimitMiddleware
from app.middlewares.tenant import TenantMiddleware
from app.models.documents import Document
from app.routes.documents import router as document_router
from app.routes.health import router as health_router

app = FastAPI()

Base.metadata.create_all(bind=engine)
app.include_router(health_router)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(TenantMiddleware)

app.include_router(document_router)