from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.dtos.document import PaginatedSearchResponse
from app.services.documents import search_documents

router = APIRouter(tags=["search"])


@router.get("/search", response_model=PaginatedSearchResponse)
def search_route(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
):
    return search_documents(
        db=db,
        tenant_id=request.state.tenant_id,
        query=q,
        page=page,
        page_size=page_size,
    )
