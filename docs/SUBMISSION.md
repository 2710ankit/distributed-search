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
**Security note:** This prototype uses header-based tenant identification. Production would require JWT/API-key auth where tenant_id is derived from the authenticated identity, not client-supplied headers.

 

## 2. AI Tool Usage

AI tools (Claude via Cursor IDE) were used throughout this project:

| Area | AI Contribution | Human Contribution |
|------|----------------|-------------------|
| Documentation | Drafted architecture doc structure and diagrams | Customized trade-off analysis and experience section |
| Code review | Suggested Celery retry config, ES mapping | Final decisions on consistency model and API design |

All AI-generated code was reviewed, tested, and modified to fit project conventions. Architectural decisions and production readiness analysis reflect the candidate's own engineering judgment.
