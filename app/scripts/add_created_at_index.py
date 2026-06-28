from app.db.elasticsearch import es

mapping_update = {
    "properties": {
        "created_at": {
            "type": "date"
        }
    }
}

es.indices.put_mapping(
    index="documents",
    body=mapping_update
)