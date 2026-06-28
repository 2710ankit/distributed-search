from celery.app.base import logger
from app.workers.celery_app import celery

from app.db.postgres import SessionLocal
from app.db.elasticsearch import es

from app.models.documents import Document


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
            print(f"Document {document_id} not found")
            return 

        if document.indexed:
            print(f"Document {document_id} already indexed")
            return
 
        es.index(
            index="documents",
            id=document.id,
            document={
                "tenant_id": document.tenant_id,
                "title": document.title,
                "content": document.content,
                "created_at": document.created_at,
            },
        ) 

        document.indexed = True
        db.commit() 

        print(f"Indexed document {document.id}") 
    finally:
        db.close()