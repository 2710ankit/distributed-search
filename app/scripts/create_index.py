from app.db.elasticsearch import es

mapping = {
    "mappings": {
        "properties": {
            "tenant_id": {"type": "keyword"},
            "title": {"type": "text"},
            "content": {"type": "text"},
            "created_at": {"type": "date"},
        }
    }
}

es.indices.create(index="documents", body=mapping, ignore=400)

print("Elasticsearch index 'documents' created (or already exists).")
