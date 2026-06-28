from sqlalchemy.orm import Session

from app.dtos.document import CreateDocumentRequest
from app.models.documents import Document
from app.services.documents.cache import invalidate_tenant_search_cache
from app.tasks.document_task import index_document


def create_document(
    db: Session,
    tenant_id: str,
    payload: CreateDocumentRequest,
) -> Document:
    document = Document(
        tenant_id=tenant_id,
        title=payload.title,
        content=payload.content,
        indexed=False,
    )

    db.add(document)
    db.flush()
    db.commit()
    db.refresh(document)

    index_document.delay(document.id)
    invalidate_tenant_search_cache(tenant_id)

    return document
