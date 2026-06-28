import json

from sqlalchemy.orm import Session

from app.db.elasticsearch import es
from app.db.redis import redis_client

CACHE_TTL_SECONDS = 60 * 60 * 24


def search_documents(
    db: Session,
    tenant_id: str,
    query: str,
    page: int,
    page_size: int,
):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    offset = (page - 1) * page_size

    redis_key = f"search:{tenant_id}:{query}:{page}:{page_size}"
    cached = redis_client.get(redis_key)
    # if cached:
        # return json.loads(cached)

    response = es.search(
        index="documents",
        from_=offset,
        size=page_size,
        query={
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title", "content"],
                            "type": "best_fields",
                            "fuzziness": "AUTO",
                        }
                    }
                ],
                "filter": [{"term": {"tenant_id": tenant_id}}],
            }
        },
        sort=[
            {"_score": {"order": "desc"}},
            {"created_at": {"order": "desc"}},
        ],
        highlight={
            "fields": {
                "title": {},
                "content": {"fragment_size": 150, "number_of_fragments": 1},
            }
        },
    )

    hits = response["hits"]["hits"]
    total = response["hits"]["total"]["value"]

    items = []
    for hit in hits:
        item = {
            "id": hit["_id"],
            **hit["_source"],
            "score": hit["_score"],
        }
        if "highlight" in hit:
            item["highlight"] = hit["highlight"]
        items.append(item)

    result = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
        "items": items,
    }
    print("HEREEEE")

    redis_client.set(redis_key, json.dumps(result))
    redis_client.expire(redis_key, CACHE_TTL_SECONDS)

    return result
