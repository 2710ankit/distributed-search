## 1. Architecture Design

### 1.1 High-Level System Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────────────┐
│   Clients   │────▶│              FastAPI Application                    │
│ (REST/HTTP) │     │  ┌─────────────┐  ┌──────────────┐  ┌───────────┐ │
└─────────────┘     │  │   Tenant    │  │ Rate Limiter │  │  Routes   │ │
                    │  │ Middleware  │  │  (Redis)     │  │           │ │
                    │  └─────────────┘  └──────────────┘  └─────┬─────┘ │
                    └──────────────────────────────────────────────┼─────┘
                                                                   │
              ┌────────────────────┬───────────────────────────────┼──────────────┐
              ▼                    ▼                               ▼              ▼
     ┌────────────────┐   ┌────────────────┐            ┌──────────────┐  ┌──────────────┐
     │   PostgreSQL   │   │     Redis      │            │    Celery    │  │ Elasticsearch│
     │ (source of     │   │ (search cache, │            │   Worker     │  │ (search      │
     │  truth, CRUD)  │   │  rate limits)  │            │ (async index)│  │  index)      │
     └────────────────┘   └────────────────┘            └──────────────┘  └──────────────┘
```

**Components:**

| Component | Role | Why chosen |
|-----------|------|------------|
| **FastAPI** | REST API layer | Async-capable, auto OpenAPI docs, Pydantic validation |
| **PostgreSQL** | Document store (source of truth) | ACID transactions, relational integrity, proven at scale |
| **Elasticsearch** | Full-text search index | Inverted indexes, relevance scoring, sub-second search at millions of docs |
| **Redis** | Cache + rate limiting | In-memory speed, TTL support, atomic counters |
| **Celery + Redis** | Async task queue | Decouples indexing from write path, retries, horizontal worker scaling |

### 1.2 Data Flow Diagrams

#### Indexing Flow (Write Path)

```
POST /documents
      │
      ▼
┌─────────────┐    sync write     ┌──────────────┐
│   FastAPI   │──────────────────▶│  PostgreSQL  │  (indexed=false)
└──────┬──────┘                   └──────────────┘
       │
       │ enqueue index_document(document_id)
       ▼
┌─────────────┐                   ┌──────────────┐
│    Redis    │◀── Celery broker ─│ Celery Worker│
│   (queue)   │                   └──────┬───────┘
└─────────────┘                          │
                                           │ read doc from PG
                                           ▼
                                     ┌──────────────────┬──────────────┐
                                 │  Elasticsearch  │  PostgreSQL  │
                                 │  (index doc)    │ indexed=true │
                                 └─────────────────┴──────────────┘
```

**Consistency:** Eventual consistency between PostgreSQL and Elasticsearch. The API returns immediately after the Postgres write; search results appear after the async index completes (typically < 1s).

#### Search Flow (Read Path)

```
GET /search?q=query&tenant=netflix
      │
      ▼
┌─────────────┐   cache miss    ┌───────────────┐
│   FastAPI   │────────────────▶│ Elasticsearch │  (multi_match + tenant filter)
└──────┬──────┘                 └───────┬───────┘
       │                                │
       │ cache hit                      │ results
       ▼                                ▼
┌─────────────┐                  ┌─────────────┐
│    Redis    │◀── store TTL ────│  Response   │
│   (cache)   │                  └─────────────┘
└─────────────┘
```

### 1.3 Database / Storage Strategy

- **PostgreSQL** stores all documents with tenant_id, title, content, indexed flag, and created_at. This is the authoritative store for CRUD operations.
- **Elasticsearch** holds a denormalized search-optimized copy. Documents are indexed by ID matching Postgres primary key for easy reconciliation.
- **Redis** caches search result pages (key: `search:{tenant}:{query}:{page}:{page_size}`, TTL: 24h) and tracks per-tenant rate limit counters.

**Trade-off:** Dual-write complexity is avoided by making Postgres the single write target and using async indexing. Stale cache entries are invalidated on create/delete via pattern-based Redis key deletion.

### 1.4 API Design

#### Create Document

```http
POST /documents
X-Tenant-Id: netflix
Content-Type: application/json

{
  "title": "Quarterly Report",
  "content": "Revenue grew 15% year over year..."
}
```

**Response (201):**

```json
{
  "id": 42,
  "tenant_id": "netflix",
  "title": "Quarterly Report",
  "content": "Revenue grew 15% year over year...",
  "indexed": false,
  "created_at": "2026-06-28T10:00:00"
}
```

#### Search Documents (Assignment Spec)

```http
GET /search?q=revenue&tenant=netflix&page=1&page_size=10
```

**Response (200):**

```json
{
  "page": 1,
  "page_size": 10,
  "total": 1523,
  "total_pages": 153,
  "items": [
    {
      "id": "42",
      "tenant_id": "netflix",
      "title": "Quarterly Report",
      "content": "Revenue grew 15%...",
      "score": 8.42,
      "created_at": "2026-06-28T10:00:00",
      "highlight": {
        "content": ["<em>Revenue</em> grew 15% year over year..."]
      }
    }
  ]
}
```

#### Get Document

```http
GET /documents/42
X-Tenant-Id: netflix
```

#### Delete Document

```http
DELETE /documents/42
X-Tenant-Id: netflix
```

**Response (200):**

```json
{ "deleted": true, "id": 42 }
```

#### Health Check

```http
GET /health
```

**Response (200):**

```json
{
  "status": "UP",
  "dependencies": {
    "postgres": "UP",
    "redis": "UP",
    "elasticsearch": "UP"
 403
  }
}
```

### 1.5 Consistency Model

| Operation | Consistency | Notes |
|-----------|-------------|-------|
| Create | Strong (Postgres), Eventual (ES) | Search may lag by seconds until Celery indexes |
| Read by ID | Strong | Always from Postgres with tenant filter |
| Search | Eventual | ES index + Redis cache; cache invalidated on writes |
| Delete | Strong (Postgres), Eventual (ES) | ES delete is best-effort with 404 ignore |

**Trade-off:** We prioritize write availability and low latency over immediate search consistency. For most document search use cases, a few seconds of indexing lag is acceptable.

### 1.6 Caching Strategy

| Layer | What | TTL | Invalidation |
|-------|------|-----|--------------|
| Redis | Search result pages | 24 hours | Pattern delete on create/delete for tenant |
| Elasticsearch | Inverted index (built-in) | N/A | Updated by Celery worker |
| Application | None (stateless) | N/A | N/A |

Cache keys include tenant, query, page, and page_size to prevent cross-tenant leakage.

### 1.7 Message Queue Usage

- **Celery** with Redis as broker handles `index_document` tasks asynchronously.
- Tasks use `autoretry_for=(Exception,)` with exponential backoff (max 5 retries).
- Idempotency: tasks check `document.indexed` before re-indexing.
- Workers scale horizontally: `docker compose up --scale celery-worker=3`.

### 1.8 Multi-Tenancy Approach

- **Isolation strategy:** Shared database, shared Elasticsearch index, tenant_id on every document.
- **API enforcement:** `TenantMiddleware` requires `X-Tenant-Id` header (or `tenant` query param on `/search`).
- **Query enforcement:** All Postgres queries and ES searches filter by `tenant_id`.
- **Rate limiting:** Per-tenant counters in Redis prevent noisy-neighbor problems.

**Security note:** This prototype uses header-based tenant identification. Production would require JWT/API-key auth where tenant_id is derived from the authenticated identity, not client-supplied headers.

---

## 2. Production Readiness Analysis

###  Scalability (100x Growth)

| Dimension | Current | At 100x | Strategy |
|-----------|---------|---------|----------|
| Documents (10M → 1B) | Single ES node | ES cluster with sharding | Shard by tenant_id hash; 20+ shards; dedicated master nodes |
| Search QPS (1K → 100K) | Single API instance | Auto-scaling API pods | Kubernetes HPA on CPU/latency; CDN for static; read replicas |
| Indexing throughput | 1 Celery worker | Worker pool | Scale Celery workers; bulk indexing API; backpressure via queue depth |
| Postgres | Single instance | Read replicas + partitioning | Table partitioning by tenant_id; connection pooling (PgBouncer) |

### Security

- **Authentication:** OAuth2/JWT with tenant claims embedded in token; reject client-supplied tenant headers.
- **Authorization:** RBAC per tenant; document-level ACLs if needed.
- **Encryption:** TLS everywhere (API, inter-service); encrypt Postgres/ES at rest (AWS KMS); secrets in Vault.
- **API security:** Input validation (Pydantic), rate limiting (implemented), WAF, CORS policy, request size limits.

### Observability

- **Logging:** Structured JSON logs (structlog) with correlation IDs; centralized in ELK/Datadog.
- **Tracing:** OpenTelemetry across API → Celery → ES for end-to-end request tracing.
- **Alerting:** PagerDuty on p95 > 500ms, error rate > 1%, dependency health failures.

### Performance

- **Elasticsearch:** Tune shard count; use `_source` filtering; query caching; force-merge during off-peak.
- **PostgreSQL:** Index on `(tenant_id, created_at)`; connection pooling; prepared statements.
- **Redis:** Pipeline batch operations; consider Redis Cluster for cache scale.
- **API:** Async endpoints for I/O-bound ops; response compression; pagination limits enforced.


## 3. Enterprise Experience Showcase
###  Similar Distributed System

At Gammastack, I have built a similar distributed system which consist of api, admin-api, bullMQ and redis. 

###  Performance Optimization

i have optimized many apis. But the most important one was when we have to share the response to casino provider after every bet. There were many N+1 queries.
I reduced them. Added indexes on DB level, implemented curosr based paginations. Moved non important tasks to queues.


###  Architectural Trade-off Decision
While designing the casino system, we had to make trade off between the consistency patterns for the gamification tools.
They were pushed to queues and ultimately we had eventual consitency for that case.

---

## 4. AI Tool Usage

AI tools (Claude via Cursor IDE) were used throughout this project:

| Area | AI Contribution | Human Contribution |
|------|----------------|-------------------|
| Boilerplate code | FastAPI routes, Pydantic models, Docker config | Architecture decisions, tenant isolation design |
| Bug fixes | Identified cache invalidation bug, type mismatches | Reviewed and validated all fixes |
| Documentation | Drafted architecture doc structure and diagrams | Customized trade-off analysis and experience section |
| Code review | Suggested Celery retry config, ES mapping | Final decisions on consistency model and API design |

All AI-generated code was reviewed, tested, and modified to fit project conventions. Architectural decisions and production readiness analysis reflect the candidate's own engineering judgment.
