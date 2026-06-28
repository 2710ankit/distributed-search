# API Examples

Base URL: `http://localhost:8000`

## Health Check

```bash
curl http://localhost:8000/health
```

## Create Document

```bash
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: netflix" \
  -d '{
    "title": "Quarterly Revenue Report",
    "content": "Revenue grew 15% year over year driven by subscriber growth."
  }'
```

## Get Document by ID

```bash
curl http://localhost:8000/documents/1 \
  -H "X-Tenant-Id: netflix"
```

## List Documents

```bash
curl "http://localhost:8000/documents?page=1&page_size=10" \
  -H "X-Tenant-Id: netflix"
```

## Search (Assignment Spec)

```bash
curl "http://localhost:8000/search?q=revenue&tenant=netflix&page=1&page_size=10"
```

## Search (Header-based Tenant)

```bash
curl "http://localhost:8000/documents/search?query=revenue&page=1&page_size=10" \
  -H "X-Tenant-Id: netflix"
```

## Delete Document

```bash
curl -X DELETE http://localhost:8000/documents/1 \
  -H "X-Tenant-Id: netflix"
```

## Rate Limit Test

Send more requests than `RATE_LIMIT` within the window to receive HTTP 429:

```bash
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    http://localhost:8000/documents \
    -H "X-Tenant-Id: test-tenant"
done
```

## Tenant Isolation Test

Document created under `netflix` should not be visible to `amazon`:

```bash
# Create as netflix
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: netflix" \
  -d '{"title": "Secret Doc", "content": "confidential data"}'

# Try to fetch as amazon (should 404)
curl http://localhost:8000/documents/1 -H "X-Tenant-Id: amazon"
```
