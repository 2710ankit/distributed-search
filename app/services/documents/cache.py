from app.db.redis import redis_client


def invalidate_tenant_search_cache(tenant_id: str) -> None:
    pattern = f"search:{tenant_id}:*"
    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)
