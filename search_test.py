from app.db.elasticsearch import es

response = es.search(
    index="documents",
    query={
        "match": {
            "title": "asd"
        }
    }
)

print(response)