from fastapi import FastAPI

from app.db.postgres import engine
from app.db.postgres import Base
from app.middlewares.tenant import TenantMiddleware
from app.models.documents import Document
from app.routes.documents import router as document_router

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.add_middleware(TenantMiddleware)

app.include_router(document_router)