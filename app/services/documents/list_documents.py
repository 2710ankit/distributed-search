from sqlalchemy.orm import Session

from app.models.documents import Document


def list_documents(
    db: Session,
    tenant_id: str,
    page: int = 1,
    page_size: int = 10,
):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    offset = (page - 1) * page_size

    query = db.query(Document).filter(Document.tenant_id == tenant_id)
    total = query.count()

    documents = (
        query
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
        "items": documents,
    }
