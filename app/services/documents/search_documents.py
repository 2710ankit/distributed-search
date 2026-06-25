from sqlalchemy.orm import Session
from app.db.elasticsearch import es


def search_documents(
    db: Session,
    tenant_id: str,
    query: str,
):
    response = es.search(
        index="documents",
        query={
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": [
                                "title",
                                "content"
                            ],
                            "type": "bool_prefix"
                        }
                    }
                ],
                "filter": [
                    {
                        "term": {
                            "tenant_id": tenant_id
                        }
                    }
                ]
            }
        }
    )

    return [
        {
            "id": hit["_id"],
            **hit["_source"],
            "score": hit["_score"]
        }
        for hit in response["hits"]["hits"]
    ]