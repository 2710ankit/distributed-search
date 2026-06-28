from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.dtos.document import (
    CreateDocumentRequest,
    DeleteResponse,
    DocumentResponse,
    PaginatedDocumentResponse,
    PaginatedSearchResponse,
)
from app.services.documents import (
    create_document,
    delete_document,
    get_document,
    list_documents,
    search_documents,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
def create_document_route(
    request: Request,
    payload: CreateDocumentRequest,
    db: Session = Depends(get_db),
):
    return create_document(
        db=db,
        tenant_id=request.state.tenant_id,
        payload=payload,
    )


@router.get("", response_model=PaginatedDocumentResponse)
def list_documents_route(
    request: Request,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
):
    return list_documents(
        db=db,
        tenant_id=request.state.tenant_id,
        page=page,
        page_size=page_size,
    )


@router.get("/search", response_model=PaginatedSearchResponse)
def search_documents_route(
    request: Request,
    query: str,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
):
    print("HEREEEE 2")
    return search_documents(
        db=db,
        tenant_id=request.state.tenant_id,
        query=query,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document_route(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db),
):
    return get_document(
        db=db,
        tenant_id=request.state.tenant_id,
        document_id=document_id,
    )


@router.delete("/{document_id}", response_model=DeleteResponse)
def delete_document_route(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db),
):
    deleted_id = delete_document(
        db=db,
        tenant_id=request.state.tenant_id,
        document_id=document_id,
    )
    return DeleteResponse(deleted=True, id=deleted_id)
