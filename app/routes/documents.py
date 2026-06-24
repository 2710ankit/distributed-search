from fastapi import APIRouter
from fastapi import Depends
from fastapi import Header
from sqlalchemy.orm import Session
from app.db.postgres import get_db
from app.dtos.document import CreateDocumentRequest
from app.services.documents import create_document, list_documents

router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)

@router.post("")
def create_document_route(
    payload: CreateDocumentRequest,
    db: Session = Depends(get_db),
    x_tenant_id: str = Header(...)
):
    print(x_tenant_id,"x_tenant_id")
    return create_document(
        db=db,
        tenant_id=x_tenant_id,
        payload=payload
    )


@router.get("")
def list_documents_route(
    db: Session = Depends(get_db),
    x_tenant_id: str = Header(...)
):
    return list_documents(
        db=db,
        tenant_id=x_tenant_id,
    )   