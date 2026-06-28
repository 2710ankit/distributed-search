from sqlalchemy.orm import Session

from app.models.documents import Document
from app.dtos.document import CreateDocumentRequest
from app.tasks.document_task import index_document



def create_document(
    db: Session,
    tenant_id: str,
    payload: CreateDocumentRequest
):
    document = Document(
        tenant_id=tenant_id,
        title=payload.title,
        content=payload.content,
        indexed=False
    )

    db.add(document)
    db.flush()  
    db.commit()
    index_document.delay(document.id)

    db.refresh(document)

    return document