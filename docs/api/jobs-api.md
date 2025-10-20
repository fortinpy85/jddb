# Jobs API Documentation

RESTful API for managing job descriptions in the JDDB system. This API provides comprehensive CRUD operations, filtering, statistics, and bulk export functionality.

**Base URL**: `/api/jobs`
**Authentication**: API Key required (via `X-API-Key` header)

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Data Models](#data-models)
4. [Endpoints](#endpoints)
   - [List Jobs](#get-apijobs)
   - [Get Job Details](#get-apijobsjob_id)
   - [Get Job Section](#get-apijobsjob_idsectionssection_type)
   - [Create Job](#post-apijobs)
   - [Update Job](#patch-apijobsjob_id)
   - [Delete Job](#delete-apijobsjob_id)
   - [Reprocess Job](#post-apijobsjob_idreprocess)
   - [Get Processing Status](#get-apijobsstatus)
   - [Get Basic Statistics](#get-apijobsstats)
   - [Get Comprehensive Statistics](#get-apijobsstatscomprehensive)
   - [Bulk Export](#post-apijobsexportbulk)
   - [Get Export Formats](#get-apijobsexportformats)
5. [Error Handling](#error-handling)
6. [Examples](#examples)
7. [Related APIs](#related-apis)

---

## Overview

The Jobs API is the core API for managing job descriptions in the JDDB system. It provides:

- **CRUD Operations**: Create, Read, Update, Delete job descriptions
- **Advanced Filtering**: Filter by classification, language, department, skills
- **Pagination**: Both offset-based and page-based pagination
- **Statistics**: Processing status and comprehensive analytics
- **Bulk Operations**: Export multiple jobs in various formats (TXT, JSON, CSV)
- **Reprocessing**: Trigger re-extraction and analysis of job descriptions

**Performance Features**:
- Result caching for status and stats endpoints
- Automatic retry on transient failures
- Optimized database queries with eager loading
- Streaming responses for large exports

---

## Authentication

All endpoints require API key authentication via the `X-API-Key` header.

**Header**:
```
X-API-Key: your-api-key-here
```

**Error Response** (401 Unauthorized):
```json
{
  "detail": "Invalid or missing API key"
}
```

---

## Data Models

### JobDescriptionCreate

Model for creating a new job description manually.

```json
{
  "job_number": "string",      // Required: Job number/ID
  "title": "string",           // Required: Job title
  "classification": "string",  // Required: Classification level (e.g., "EX-01")
  "language": "string",        // Optional: Language code ("en"/"fr"), default: "en"
  "department": "string",      // Optional: Department name
  "reports_to": "string",      // Optional: Reports to position
  "content": "string",         // Optional: Full job description content
  "sections": {                // Optional: Job sections by type
    "section_type": "content"
  }
}
```

### JobUpdate

Model for updating an existing job description (partial update).

```json
{
  "title": "string",           // Optional: Job title
  "classification": "string",  // Optional: Classification level
  "language": "string",        // Optional: Language code
  "raw_content": "string",     // Optional: Full job description content
  "department": "string",      // Optional: Department name
  "reports_to": "string"       // Optional: Reports to position
}
```

### JobResponse

Standard job response model.

```json
{
  "id": 1,
  "job_number": "103249",
  "title": "Director, Business Analysis",
  "classification": "EX-01",
  "language": "en",
  "file_path": "/path/to/file.txt",
  "file_hash": "abc123...",
  "processed_date": "2025-10-17T10:30:00Z",
  "created_at": "2025-10-17T10:30:00Z",
  "updated_at": "2025-10-17T10:30:00Z",
  "quality_score": 0.85,
  "sections": [...],          // If include_sections=true
  "metadata": {...},          // If include_metadata=true
  "skills": [...],            // If include_skills=true
  "raw_content": "..."        // If include_content=true
}
```

---

## Endpoints

### GET /api/jobs

List job descriptions with optional filters and pagination.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `skip` | integer | No | Number of records to skip (default: 0, min: 0) |
| `limit` | integer | No | Number of records to return (default: 100, min: 1, max: 1000) |
| `page` | integer | No | Page number for page-based pagination (1-based, min: 1) |
| `size` | integer | No | Page size for page-based pagination (min: 1, max: 1000) |
| `search` | string | No | Search in job title and content |
| `classification` | string | No | Filter by classification (e.g., "EX-01") |
| `language` | string | No | Filter by language ("en" or "fr") |
| `department` | string | No | Filter by department (partial match) |
| `skill_ids` | string | No | Comma-separated skill IDs (jobs must have ALL specified skills) |

**Note**: Use either (`skip` + `limit`) OR (`page` + `size`), not both. If using page-based pagination, both `page` and `size` must be provided.

#### Success Response (200 OK)

**Offset-based pagination**:
```json
{
  "jobs": [
    {
      "id": 1,
      "job_number": "103249",
      "title": "Director, Business Analysis",
      "classification": "EX-01",
      "language": "en",
      "processed_date": "2025-10-17T10:30:00Z",
      "file_path": "/path/to/file.txt",
      "quality_score": 0.85,
      "created_at": "2025-10-17T10:30:00Z",
      "skills": [
        {
          "id": 42,
          "lightcast_id": "KS123ABC",
          "name": "Strategic Planning",
          "skill_type": "Specialized Skill",
          "category": "Business Strategy",
          "confidence": 0.92
        }
      ]
    }
  ],
  "pagination": {
    "skip": 0,
    "limit": 100,
    "total": 250,
    "has_more": true
  }
}
```

**Page-based pagination**:
```json
{
  "jobs": [...],
  "pagination": {
    "page": 1,
    "size": 50,
    "total": 250,
    "pages": 5,
    "has_more": true
  }
}
```

#### Error Responses

- **400 Bad Request**: Invalid pagination parameters
- **401 Unauthorized**: Invalid or missing API key
- **500 Internal Server Error**: Database error

#### Example

```bash
# List first 50 jobs in English
curl -X GET "http://localhost:8000/api/jobs?language=en&limit=50" \
  -H "X-API-Key: your-api-key"

# Page-based pagination
curl -X GET "http://localhost:8000/api/jobs?page=2&size=25" \
  -H "X-API-Key: your-api-key"

# Filter by skills (jobs with BOTH skills 42 and 67)
curl -X GET "http://localhost:8000/api/jobs?skill_ids=42,67" \
  -H "X-API-Key: your-api-key"

# Search with classification filter
curl -X GET "http://localhost:8000/api/jobs?search=Director&classification=EX-01" \
  -H "X-API-Key: your-api-key"
```

---

### GET /api/jobs/{job_id}

Get detailed information about a specific job description.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | integer | Yes | Unique job identifier |

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_content` | boolean | No | false | Include full raw content |
| `include_sections` | boolean | No | true | Include parsed sections |
| `include_metadata` | boolean | No | true | Include job metadata |
| `include_skills` | boolean | No | true | Include extracted skills |

#### Success Response (200 OK)

```json
{
  "id": 1,
  "job_number": "103249",
  "title": "Director, Business Analysis",
  "classification": "EX-01",
  "language": "en",
  "file_path": "/path/to/file.txt",
  "file_hash": "abc123...",
  "processed_date": "2025-10-17T10:30:00Z",
  "created_at": "2025-10-17T10:30:00Z",
  "updated_at": "2025-10-17T10:30:00Z",
  "raw_content": "Full job description text...",  // If include_content=true
  "sections": [
    {
      "id": 5,
      "section_type": "general_accountability",
      "section_content": "The Director is responsible for...",
      "section_order": 1
    }
  ],
  "metadata": {
    "reports_to": "Vice President",
    "department": "Business Strategy",
    "location": "Ottawa, ON",
    "fte_count": 5.0,
    "salary_budget": 500000.00,
    "effective_date": "2025-01-01"
  },
  "skills": [
    {
      "id": 42,
      "lightcast_id": "KS123ABC",
      "name": "Strategic Planning",
      "skill_type": "Specialized Skill",
      "category": "Business Strategy",
      "confidence": 0.92
    }
  ]
}
```

#### Error Responses

- **404 Not Found**: Job description not found
- **401 Unauthorized**: Invalid or missing API key
- **500 Internal Server Error**: Database error

#### Example

```bash
# Get full job details with all sections and metadata
curl -X GET "http://localhost:8000/api/jobs/1" \
  -H "X-API-Key: your-api-key"

# Get job with raw content included
curl -X GET "http://localhost:8000/api/jobs/1?include_content=true" \
  -H "X-API-Key: your-api-key"

# Get minimal job data (no sections, metadata, or skills)
curl -X GET "http://localhost:8000/api/jobs/1?include_sections=false&include_metadata=false&include_skills=false" \
  -H "X-API-Key: your-api-key"
```

---

### GET /api/jobs/{job_id}/sections/{section_type}

Get a specific section of a job description.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | integer | Yes | Unique job identifier |
| `section_type` | string | Yes | Section type identifier |

**Common Section Types**:
- `general_accountability`
- `organization_structure`
- `nature_and_scope`
- `specific_accountabilities`
- `dimensions`
- `knowledge_skills`

#### Success Response (200 OK)

```json
{
  "job_id": 1,
  "section_id": 5,
  "section_type": "general_accountability",
  "section_content": "The Director is responsible for leading the business analysis function...",
  "section_order": 1
}
```

#### Error Responses

- **404 Not Found**: Job or section not found
- **401 Unauthorized**: Invalid or missing API key
- **500 Internal Server Error**: Database error

#### Example

```bash
curl -X GET "http://localhost:8000/api/jobs/1/sections/general_accountability" \
  -H "X-API-Key: your-api-key"
```

---

### POST /api/jobs

Create a new job description manually.

#### Request Body

See [JobDescriptionCreate](#jobdescriptioncreate) model.

#### Success Response (201 Created)

```json
{
  "status": "success",
  "message": "Job description 103249 created successfully",
  "job_id": 1,
  "job": {
    "id": 1,
    "job_number": "103249",
    "title": "Director, Business Analysis",
    "classification": "EX-01",
    "language": "en"
  }
}
```

#### Error Responses

- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Invalid or missing API key
- **500 Internal Server Error**: Database error

#### Example

```bash
curl -X POST "http://localhost:8000/api/jobs" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "job_number": "103249",
    "title": "Director, Business Analysis",
    "classification": "EX-01",
    "language": "en",
    "department": "Business Strategy",
    "reports_to": "Vice President",
    "content": "The Director is responsible for...",
    "sections": {
      "general_accountability": "The Director leads..."
    }
  }'
```

---

### PATCH /api/jobs/{job_id}

Update a job description (partial update).

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | integer | Yes | Unique job identifier |

#### Request Body

See [JobUpdate](#jobupdate) model. Only include fields to update.

#### Success Response (200 OK)

```json
{
  "status": "success",
  "message": "Job description 103249 updated successfully",
  "job_id": 1,
  "job": {
    "id": 1,
    "job_number": "103249",
    "title": "Senior Director, Business Analysis",
    "classification": "EX-02",
    "language": "en",
    "updated_at": "2025-10-17T15:45:00Z"
  }
}
```

#### Error Responses

- **404 Not Found**: Job description not found
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Invalid or missing API key
- **500 Internal Server Error**: Database error

#### Example

```bash
# Update only the title and classification
curl -X PATCH "http://localhost:8000/api/jobs/1" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Director, Business Analysis",
    "classification": "EX-02"
  }'
```

---

### DELETE /api/jobs/{job_id}

Delete a job description and all related data (cascade delete).

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | integer | Yes | Unique job identifier |

#### Success Response (200 OK)

```json
{
  "status": "success",
  "message": "Job description 103249 deleted successfully"
}
```

#### Error Responses

- **404 Not Found**: Job description not found
- **401 Unauthorized**: Invalid or missing API key
- **500 Internal Server Error**: Database error

#### Example

```bash
curl -X DELETE "http://localhost:8000/api/jobs/1" \
  -H "X-API-Key: your-api-key"
```

---

### POST /api/jobs/{job_id}/reprocess

Reprocess a job description (re-run extraction and analysis).

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | integer | Yes | Unique job identifier |

#### Success Response (200 OK)

```json
{
  "status": "success",
  "message": "Job description 103249 queued for reprocessing",
  "job_id": 1
}
```

#### Error Responses

- **404 Not Found**: Job description not found
- **401 Unauthorized**: Invalid or missing API key
- **500 Internal Server Error**: Database error

#### Example

```bash
curl -X POST "http://localhost:8000/api/jobs/1/reprocess" \
  -H "X-API-Key: your-api-key"
```

---

### GET /api/jobs/status

Get current processing status of all jobs. **Cached for 60 seconds**.

#### Success Response (200 OK)

```json
{
  "total_jobs": 250,
  "by_classification": {
    "EX-01": 100,
    "EX-02": 75,
    "EX-03": 50,
    "EX-04": 25
  },
  "by_language": {
    "en": 180,
    "fr": 70
  },
  "processing_status": {
    "pending": 0,
    "processing": 0,
    "completed": 250,
    "needs_review": 0,
    "failed": 0
  },
  "last_updated": "2025-10-17T15:45:00Z"
}
```

#### Error Responses

- **401 Unauthorized**: Invalid or missing API key
- **500 Internal Server Error**: Database error

#### Example

```bash
curl -X GET "http://localhost:8000/api/jobs/status" \
  -H "X-API-Key: your-api-key"
```

---

### GET /api/jobs/stats

Get basic job statistics. **Cached for 2 minutes**.

#### Success Response (200 OK)

```json
{
  "total_jobs": 250,
  "classification_distribution": {
    "EX-01": 100,
    "EX-02": 75,
    "EX-03": 50,
    "EX-04": 25
  },
  "language_distribution": {
    "en": 180,
    "fr": 70
  }
}
```

#### Error Responses

- **401 Unauthorized**: Invalid or missing API key
- **500 Internal Server Error**: Database error

#### Example

```bash
curl -X GET "http://localhost:8000/api/jobs/stats" \
  -H "X-API-Key: your-api-key"
```

---

### GET /api/jobs/stats/comprehensive

Get comprehensive ingestion and processing statistics (not cached).

#### Success Response (200 OK)

```json
{
  "summary": {
    "total_jobs": 250,
    "total_sections": 1500,
    "total_chunks": 5000,
    "avg_sections_per_job": 6.0,
    "avg_chunks_per_job": 20.0
  },
  "quality_metrics": {
    "avg_completeness": 0.85,
    "avg_structure_score": 0.90,
    "jobs_needing_review": 15
  },
  "ai_usage_30d": {
    "total_requests": 5000,
    "total_tokens": 2500000,
    "total_cost": 125.50,
    "avg_cost_per_request": 0.025
  },
  "content_distribution": {
    "by_classification": {...},
    "by_language": {...},
    "by_department": {...}
  },
  "performance": {
    "avg_processing_time_seconds": 45.2,
    "total_processing_time_hours": 3.14
  }
}
```

#### Error Responses

- **400 Bad Request**: Data validation error
- **401 Unauthorized**: Invalid or missing API key
- **500 Internal Server Error**: Database error

#### Example

```bash
curl -X GET "http://localhost:8000/api/jobs/stats/comprehensive" \
  -H "X-API-Key: your-api-key"
```

---

### POST /api/jobs/export/bulk

Export multiple jobs in various formats (TXT, JSON, CSV).

#### Request Body

```json
{
  "job_ids": [1, 2, 3],           // Optional: specific job IDs (if omitted, exports all matching filters)
  "format": "txt",                // Optional: "txt"|"json"|"csv" (default: "txt")
  "include_sections": true,       // Optional: include parsed sections (default: true)
  "include_metadata": true,       // Optional: include metadata (default: true)
  "include_content": false,       // Optional: include raw content (default: false)
  "filters": {                    // Optional: filter criteria (used if no job_ids)
    "classification": ["EX-01"],
    "language": ["en"],
    "department": ["IT"]
  }
}
```

#### Success Response (200 OK)

Returns a streaming file download with appropriate Content-Type and Content-Disposition headers.

**Response Headers**:
```
Content-Type: text/plain | application/json | text/csv
Content-Disposition: attachment; filename=jobs_export_N_jobs.{txt|json|csv}
```

#### Error Responses

- **404 Not Found**: No jobs found for export
- **400 Bad Request**: Invalid export parameters
- **401 Unauthorized**: Invalid or missing API key
- **500 Internal Server Error**: Export failed

#### Example

```bash
# Export specific jobs as JSON
curl -X POST "http://localhost:8000/api/jobs/export/bulk" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "job_ids": [1, 2, 3],
    "format": "json",
    "include_sections": true,
    "include_metadata": true
  }' \
  --output jobs_export.json

# Export all EX-01 jobs in English as CSV
curl -X POST "http://localhost:8000/api/jobs/export/bulk" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "csv",
    "filters": {
      "classification": ["EX-01"],
      "language": ["en"]
    }
  }' \
  --output jobs_export.csv
```

---

### GET /api/jobs/export/formats

Get available export formats and options.

#### Success Response (200 OK)

```json
{
  "formats": {
    "txt": {
      "name": "Plain Text",
      "description": "Human-readable text format",
      "content_type": "text/plain",
      "extension": "txt"
    },
    "json": {
      "name": "JSON",
      "description": "Structured JSON data",
      "content_type": "application/json",
      "extension": "json"
    },
    "csv": {
      "name": "CSV",
      "description": "Comma-separated values for spreadsheets",
      "content_type": "text/csv",
      "extension": "csv"
    }
  },
  "options": {
    "include_sections": {
      "name": "Include Sections",
      "description": "Include parsed job sections (accountability, structure, etc.)",
      "default": true
    },
    "include_metadata": {
      "name": "Include Metadata",
      "description": "Include structured metadata (department, reports_to, etc.)",
      "default": true
    },
    "include_content": {
      "name": "Include Raw Content",
      "description": "Include full raw content (warning: large files)",
      "default": false
    }
  }
}
```

#### Example

```bash
curl -X GET "http://localhost:8000/api/jobs/export/formats" \
  -H "X-API-Key: your-api-key"
```

---

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error description"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid parameters or data |
| 401 | Unauthorized - Invalid or missing API key |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error - Database or server error |

### Retry Logic

All endpoints automatically retry on transient failures:
- Retry count: 3 attempts
- Exponential backoff: 1s, 2s, 4s
- Retries on: Network errors, database connection issues

---

## Examples

### Common Workflows

#### 1. Search and Filter Jobs

```bash
# Find all Director positions in Business Strategy department
curl -X GET "http://localhost:8000/api/jobs?search=Director&department=Business%20Strategy" \
  -H "X-API-Key: your-api-key"
```

#### 2. Get Complete Job Information

```bash
# Get job with all sections, metadata, skills, and raw content
curl -X GET "http://localhost:8000/api/jobs/1?include_content=true&include_sections=true&include_metadata=true&include_skills=true" \
  -H "X-API-Key: your-api-key"
```

#### 3. Create and Update Job

```bash
# Create new job
JOB_RESPONSE=$(curl -X POST "http://localhost:8000/api/jobs" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "job_number": "NEW001",
    "title": "New Position",
    "classification": "EX-01",
    "language": "en"
  }')

# Extract job_id from response and update
JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')

curl -X PATCH "http://localhost:8000/api/jobs/$JOB_ID" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "department": "IT Services"
  }'
```

#### 4. Export Jobs for Analysis

```bash
# Export all EX-01 jobs with full details as JSON
curl -X POST "http://localhost:8000/api/jobs/export/bulk" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "json",
    "include_sections": true,
    "include_metadata": true,
    "include_content": true,
    "filters": {
      "classification": ["EX-01"]
    }
  }' \
  --output ex01_jobs.json
```

---

## Related APIs

- **[Search API](search-api.md)** - Full-text and semantic search across jobs
- **[Ingestion API](ingestion-api.md)** - File upload and processing
- **[Translation Memory API](translation_memory_api.md)** - Translation concordance
- **[AI Writer API](ai-writer-api.md)** - AI-powered content generation
- **[Analytics API](analytics-api.md)** - Predictive analytics
- **[Statistics API](statistics-api.md)** - Comprehensive job statistics

---

## API Reference

**Live Documentation**: http://localhost:8000/api/docs

The interactive API documentation provides:
- Real-time API testing
- Request/response examples
- Schema validation
- Authentication testing

---

**Last Updated**: 2025-10-17
**API Version**: 2.0
**Endpoint**: `/api/jobs`
