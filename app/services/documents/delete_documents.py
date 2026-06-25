from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session
from app.db.elasticsearch import es
from app.db.redis import redis_client
import json
from app.models.documents import Document




def delete_document(
    db: Session,
    tenant_id: str,
    document_id: str,
):
    es.delete(
        index="documents",
        id=document_id,
        ignore=404
    )   

    redis_client.delete(f"search:{tenant_id}:{document_id}")

    print(document_id,type(document_id),"DOCUMENT_ID")
    doc = db.query(Document).filter(Document.id == document_id).first()

    if doc:
        db.delete(doc)
        db.commit()
    else:
        raise HTTPException(status_code=404, detail="Document not found")

    return True
