from pydantic import BaseModel


class CreateDocumentRequest(BaseModel):
    title: str
    content: str