from app.tasks.document_task import index_document

index_document.delay(1)
index_document.delay(2)
