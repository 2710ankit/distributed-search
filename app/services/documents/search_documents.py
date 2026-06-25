from sqlalchemy.orm import Session
from app.db.elasticsearch import es
from app.db.redis import redis_client
import json



def search_documents(
    db: Session,
    tenant_id: str,
    query: str,
):
    redis_key=f"search:{tenant_id}:{query}"
    redis_data = redis_client.get(redis_key)
    if redis_data:
        return json.loads(redis_data)

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

    response = [
        {
            "id": hit["_id"],
            **hit["_source"],
            "score": hit["_score"]
        }   
        for hit in response["hits"]["hits"]
    ]

    redis_client.set(redis_key, json.dumps(response))
    redis_client.expire(redis_key, 60 * 60 * 24)

    return response