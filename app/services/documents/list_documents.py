from sqlalchemy.orm import Session
from app.models.documents import Document

def list_documents(
    db: Session,
    tenant_id: str
):
    documents = db.query(Document).filter(Document.tenant_id == tenant_id).all()

    return documents