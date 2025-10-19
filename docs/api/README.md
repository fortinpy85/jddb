# JDDB API Documentation

Comprehensive API documentation for the Job Description Database (JDDB) system.

**Base URL**: http://localhost:8000/api
**Live API Docs**: http://localhost:8000/api/docs

---

## Available APIs

### Core APIs

#### [Jobs API](jobs-api.md)
RESTful API for job description management including CRUD operations, filtering, statistics, section-level editing, and bulk export functionality.

**Key Features**:
- List jobs with advanced filtering
- CRUD operations (Create, Read, Update, Delete)
- Section-level content editing
- Bulk export (JSON, CSV, TXT)
- Processing status and statistics

**Base Endpoint**: `/api/jobs`

---

#### [Ingestion API](ingestion-api.md)
File upload and processing API supporting multiple formats with automatic section parsing and skill extraction.

**Key Features**:
- Multi-format file upload (.txt, .doc, .docx, .pdf)
- Batch upload support (up to 50 files)
- Automatic language detection
- Section parsing and skill extraction
- Processing status tracking

**Base Endpoint**: `/api/ingestion`

---

#### [Search API](search-api.md)
Full-text and semantic search across job descriptions with faceted filtering and relevance ranking.

**Key Features**:
- Full-text search across all job content
- Faceted filtering (classification, language, department, skills)
- Relevance ranking and scoring
- Advanced query syntax
- Section-level search

**Base Endpoint**: `/api/search`

---

### Specialized APIs

#### [Translation Memory API](translation_memory_api.md)
Bilingual translation concordance and terminology management for English↔French job descriptions.

**Key Features**:
- Translation memory search with fuzzy matching
- Terminology database management
- Sentence-level concordance
- Translation validation and quality assurance

**Base Endpoint**: `/api/translation-memory`

---

## Authentication

All API endpoints require authentication via API key.

**Header**:
```http
X-API-Key: your-api-key-here
```

**Error Response (401 Unauthorized)**:
```json
{
  "detail": "Invalid or missing API key"
}
```

---

## Response Format

### Success Response

```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": { ... }
}
```

### Error Response

```json
{
  "detail": "Error description"
}
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid API key |
| 404 | Not Found - Resource doesn't exist |
| 413 | Payload Too Large - File/request too large |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error |

---

## Rate Limiting

API rate limits vary by endpoint type:

| Endpoint Type | Rate Limit |
|--------------|------------|
| Read operations (GET) | 100 requests/minute |
| Write operations (POST, PATCH) | 20 requests/minute |
| File uploads | 20 requests/minute |
| Batch operations | 5 requests/minute |

**Rate Limit Headers**:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1729166400
```

---

## Quick Start Examples

### Python

```python
import requests

API_KEY = "your-api-key"  # pragma: allowlist secret
API_URL = "http://localhost:8000/api"

# List all jobs
response = requests.get(
    f"{API_URL}/jobs",
    headers={"X-API-Key": API_KEY}
)
jobs = response.json()

# Get specific job
job = requests.get(
    f"{API_URL}/jobs/1",
    headers={"X-API-Key": API_KEY}
).json()

# Upload file
with open("job.txt", "rb") as f:
    response = requests.post(
        f"{API_URL}/ingestion/upload",
        headers={"X-API-Key": API_KEY},
        files={"file": f}
    )
```

### JavaScript

```javascript
const API_KEY = 'your-api-key';  // pragma: allowlist secret
const API_URL = 'http://localhost:8000/api';

// List all jobs
const jobs = await fetch(`${API_URL}/jobs`, {
  headers: { 'X-API-Key': API_KEY }
}).then(r => r.json());

// Get specific job
const job = await fetch(`${API_URL}/jobs/1`, {
  headers: { 'X-API-Key': API_KEY }
}).then(r => r.json());

// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const upload = await fetch(`${API_URL}/ingestion/upload`, {
  method: 'POST',
  headers: { 'X-API-Key': API_KEY },
  body: formData
}).then(r => r.json());
```

### cURL

```bash
# List jobs
curl -X GET "http://localhost:8000/api/jobs" \
  -H "X-API-Key: your-api-key"

# Get specific job
curl -X GET "http://localhost:8000/api/jobs/1" \
  -H "X-API-Key: your-api-key"

# Upload file
curl -X POST "http://localhost:8000/api/ingestion/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@job_description.txt"

# Search jobs
curl -X POST "http://localhost:8000/api/search" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "strategic planning",
    "classification": ["EX-01"]
  }'
```

---

## API Versioning

Current version: **v1.0**

The API uses URL versioning for major changes. Future versions will be accessible via:
- v1: `/api/` (current)
- v2: `/api/v2/` (future)

---

## Additional Resources

- **Live API Documentation**: http://localhost:8000/api/docs (Swagger UI)
- **OpenAPI Schema**: http://localhost:8000/api/openapi.json
- **Development Guide**: [DEVELOPMENT-GUIDE.md](../../DEVELOPMENT-GUIDE.md)
- **Project Documentation**: [DOCUMENTATION.md](../../DOCUMENTATION.md)

---

**Last Updated**: 2025-10-18
**API Version**: 1.0
