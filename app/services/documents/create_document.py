from sqlalchemy.orm import Session

from app.models.documents import Document
from app.dtos.document import CreateDocumentRequest


def create_document(
    db: Session,
    tenant_id: str,
    payload: CreateDocumentRequest
):
    print(tenant_id,"tenant_id")
    document = Document(
        tenant_id=tenant_id,
        title=payload.title,
        content=payload.content
    )

    db.add(document)

    db.commit()

    db.refresh(document)

    return document