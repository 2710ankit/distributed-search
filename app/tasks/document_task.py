import logging

from app.workers.celery_app import celery

from app.db.postgres import SessionLocal
from app.db.elasticsearch import es

from app.models.documents import Document

logger = logging.getLogger(__name__)


@celery.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def index_document(self, document_id: int):
    db = SessionLocal()

    try:
        document = (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

        if not document:
            logger.warning("Document %s not found", document_id)
            return

        if document.indexed:
            logger.info("Document %s already indexed", document_id)
            return

        created_at = document.created_at.isoformat() if document.created_at else None

        es.index(
            index="documents",
            id=document.id,
            document={
                "tenant_id": document.tenant_id,
                "title": document.title,
                "content": document.content,
                "created_at": created_at,
            },
        )

        document.indexed = True
        db.commit()

        logger.info("Indexed document %s", document.id)
    finally:
        db.close()
