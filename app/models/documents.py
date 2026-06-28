from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.postgres import Base


class Document(Base):
    __tablename__ = "documents"

   
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    tenant_id = Column(
        String,
        nullable=False
    )

    title = Column(
        Text,
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )
    indexed = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )