from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.db.postgres import SessionLocal
from app.db.redis import redis_client
from app.db.elasticsearch import es

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health():
    status = {
        "postgres": "UP",
        "redis": "UP",
        "elasticsearch": "UP",
    }

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        status["postgres"] = "DOWN"

    try:
        redis_client.ping()
    except Exception:
        status["redis"] = "DOWN"

    try:
        if not es.ping():
            status["elasticsearch"] = "DOWN"
    except Exception:
        status["elasticsearch"] = "DOWN"

    if "DOWN" in status.values():
        raise HTTPException(status_code=503, detail=status)

    return {"status": "UP", "dependencies": status}
