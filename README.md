# Distributed Document Search Service

A multi-tenant document search prototype built with **FastAPI**, **PostgreSQL**, **Elasticsearch**, **Redis**, and **Celery**. Designed to demonstrate enterprise patterns: async indexing, tenant isolation, caching, rate limiting, and horizontal scalability.

## Quick Start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

Services:

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |
| Elasticsearch | http://localhost:9200 |
| PostgreSQL | localhost:5433 |
| Redis | localhost:6380 |

## Local Development (without Docker for API)

```bash
cp .env.example .env
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

docker compose up postgres redis elasticsearch -d
python app/scripts/create_index.py

uvicorn app.main:app --reload --port 8000

# In a separate terminal:
celery -A app.workers.celery_app worker --loglevel=info
```

## API Endpoints

All document endpoints require the `X-Tenant-Id` header. The search endpoint also accepts `tenant` as a query parameter per the assignment spec.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/documents` | Create and async-index a document |
| `GET` | `/documents` | List documents (paginated) |
| `GET` | `/documents/{id}` | Get document by ID |
| `DELETE` | `/documents/{id}` | Delete document |
| `GET` | `/search?q=&tenant=` | Full-text search (assignment spec) |
| `GET` | `/documents/search?query=` | Full-text search (header-based tenant) |
| `GET` | `/health` | Health check with dependency status |
 
## Architecture Overview

```
Client → FastAPI API → PostgreSQL (source of truth)
                    ↘ Redis (cache + rate limits)
                    ↘ Celery → Elasticsearch (search index)
```
 
## Project Structure

```
app/
├── db/              # Postgres, Redis, Elasticsearch clients
├── dtos/            # Request/response schemas
├── middlewares/     # Tenant isolation, rate limiting
├── models/          # SQLAlchemy models
├── routes/          # FastAPI routers
├── services/        # Business logic
├── tasks/           # Celery async indexing
├── workers/         # Celery app config
└── scripts/         # Index creation, seed data
```

## Seed Data (optional)

```bash
python -m app.scripts.seed_data
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5433/document_search` | Postgres connection |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6380` | Redis port |
| `REDIS_URL` | `redis://localhost:6380/0` | Celery broker/backend |
| `ELASTICSEARCH_URL` | `http://localhost:9200` | Elasticsearch URL |
| `RATE_LIMIT` | `1000` | Max requests per tenant per window |
| `RATE_LIMIT_WINDOW` | `60` | Rate limit window in seconds |

## AI Tool Usage

This project was developed with AI assistance (Claude/Cursor) for boilerplate generation, documentation drafting, and code review

