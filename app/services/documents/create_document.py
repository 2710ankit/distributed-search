from sqlalchemy.orm import Session

from app.models.documents import Document
from app.dtos.document import CreateDocumentRequest
from app.db.elasticsearch import es



def create_document(
    db: Session,
    tenant_id: str,
    payload: CreateDocumentRequest
):
    document = Document(
        tenant_id=tenant_id,
        title=payload.title,
        content=payload.content
    )

    db.add(document)
    db.flush()  


    es.index(
        index="documents",
        id=str(document.id),
        document={
            "tenant_id": document.tenant_id,
            "title": document.title,
            "content": document.content
        }
    )
    db.commit()

    db.refresh(document)

    return document