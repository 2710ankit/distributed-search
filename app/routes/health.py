from fastapi import APIRouter
from fastapi import HTTPException
from sqlalchemy import text

from app.db.postgres import SessionLocal
from app.db.redis import redis_client
from app.db.elasticsearch import es

router = APIRouter(
    prefix="/health",
    tags=["Health"]
)


@router.get("")
def health():

    print("HEREEE")
    status = {
        "postgres": "UP",
        "redis": "UP",
        "elasticsearch": "UP"
    }

    # PostgreSQL
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        status["postgres"] = "DOWN"

    # Redis
    try:
        redis_client.ping()
    except Exception:
        status["redis"] = "DOWN"

    # Elasticsearch
    try:
        if not es.ping():
            status["elasticsearch"] = "DOWN"
    except Exception:
        status["elasticsearch"] = "DOWN"

    if "DOWN" in status.values():
        raise HTTPException(
            status_code=503,
            detail=status
        )

    return {
        "status": "UP",
        "dependencies": status
    }