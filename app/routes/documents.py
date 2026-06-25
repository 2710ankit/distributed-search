from fastapi import APIRouter
from fastapi import Depends
from fastapi import Header
from fastapi import Request
from sqlalchemy.orm import Session
from app.db.postgres import get_db
from app.dtos.document import CreateDocumentRequest
from app.services.documents import create_document, list_documents, search_documents

router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)

@router.post("")
def create_document_route(
    request: Request,
    payload: CreateDocumentRequest,
    db: Session = Depends(get_db),
):
    return create_document(
        db=db,
        tenant_id=request.state.tenant_id,
        payload=payload
    )


@router.get("")
def list_documents_route(
    request: Request,
    db: Session = Depends(get_db),
):
    return list_documents(
        db=db,
        tenant_id=request.state.tenant_id,
    )   


@router.get("/search")
def search_documents_route(
    request: Request,
    query: str,
    db: Session = Depends(get_db),
):
    return search_documents(
        db=db,
        tenant_id=request.state.tenant_id,
        query=query
    )