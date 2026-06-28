from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.documents import Document


def get_document(
    db: Session,
    tenant_id: str,
    document_id: int,
) -> Document:
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.tenant_id == tenant_id)
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document
