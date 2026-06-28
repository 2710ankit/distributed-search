from sqlalchemy.orm import Session
from app.db.elasticsearch import es
from app.db.redis import redis_client
import json


def search_documents(
    db: Session,
    tenant_id: str,
    query: str,
    page: int,
    page_size: int,
):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)  # Limit max page size
    offset = (page - 1) * page_size

    print(page,page_size,"PAGE AND PAGE SIZE")
    redis_key = f"search:{tenant_id}:{query}:{page}:{page_size}"
    redis_client.delete(redis_key)
    redis_data = redis_client.get(redis_key)
    if redis_data:
        return json.loads(redis_data)

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
        },
        sort=[
            {"_score": {"order": "desc"}},
            {"created_at": {"order": "desc"}}
        ]
    )

    hits = response["hits"]["hits"]
    total = response["hits"]["total"]["value"]

    result = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "items": [
            {
                "id": hit["_id"],
                **hit["_source"],
                "score": hit["_score"],
            }
            for hit in hits
        ],
    }

    redis_client.delete(redis_key)
    redis_client.set(redis_key, json.dumps(result))
    redis_client.expire(redis_key, 60 * 60 * 24)

    return result






#     import json
# from sqlalchemy.orm import Session
# from app.db.elasticsearch import es
# from app.db.redis import redis_client


# def search_documents(
#     db: Session,
#     tenant_id: str,
#     query: str,
#     size: int = 10,
#     search_after: list | None = None,
# ):
#     # clamp size
#     size = min(max(size, 1), 100)

#     redis_key = f"search:{tenant_id}:{query}:{size}:{json.dumps(search_after, default=str)}"


#     cached = redis_client.get(redis_key)
#     # if cached:
#     #     return json.loads(cached)
 
#     es_query = {
#         "bool": {
#             "must": [
#                 {
#                     "multi_match": {
#                         "query": query,
#                         "fields": ["title", "content"],
#                         "type": "bool_prefix",
#                     }
#                 }
#             ],
#             "filter": [
#                 {"term": {"tenant_id": tenant_id}}
#             ],
#         }
#     } 

#     body = {
#         "size": size,
#         "query": es_query,
#         "sort": [
#             {"_score": "desc"},
#             {"created_at": "asc"}   
#         ],
#     }

#     # cursor pagination
#     if search_after:
#         body["search_after"] = search_after

#     response = es.search(index="documents", body=body)

#     hits = response["hits"]["hits"]

#     items = [
#         {
#             "id": hit["_id"],
#             **hit["_source"],
#             "score": hit.get("_score"),
#         }
#         for hit in hits
#     ]

#     next_cursor = None
#     if hits:
#         # ALWAYS safe now because sort is defined
#         next_cursor = hits[-1].get("sort")

#     result = {
#         "items": items,
#         "next_cursor": next_cursor,
#     }

#     redis_client.set(redis_key, json.dumps(result))
#     redis_client.expire(redis_key, 60 * 60 * 24)

#     return result