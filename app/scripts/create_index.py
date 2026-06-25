from app.db.elasticsearch import es

mapping = {
    "mappings": {
        "properties": {
            "tenant_id": {
                "type": "keyword"
            },
            "title": {
                "type": "text"
            },
            "content": {
                "type": "text"
            }
        }
    }
}

es.indices.create(
    index="documents",
    body=mapping,
    ignore=400
)