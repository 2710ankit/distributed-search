from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateDocumentRequest(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    title: str
    content: str
    indexed: bool
    created_at: Optional[datetime] = None


class SearchResultItem(BaseModel):
    id: str
    tenant_id: str
    title: str
    content: str
    score: float
    created_at: Optional[str] = None
    highlight: Optional[dict] = None


class PaginatedSearchResponse(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    items: list[SearchResultItem]


class PaginatedDocumentResponse(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    items: list[DocumentResponse]


class DeleteResponse(BaseModel):
    deleted: bool
    id: int
