# Search API Documentation

**Version**: 2.0
**Base URL**: `http://localhost:8000/api`
**Authentication**: X-API-Key header (see [Authentication](#authentication))

## Overview

The Search API provides comprehensive search capabilities for job descriptions, including:

- **Semantic Search**: Vector-based similarity search using AI embeddings
- **Full-Text Search**: Traditional keyword-based search with relevance ranking
- **Advanced Filtering**: Date ranges, salary bands, location, department, FTE counts
- **Job Comparison**: Side-by-side analysis of job descriptions
- **Similar Jobs**: Find jobs similar to a given job description
- **Search Recommendations**: Query suggestions, trending searches, popular filters
- **Search Analytics**: Track and analyze search behavior

## Authentication

All Search API endpoints require API key authentication:

```bash
curl -X GET "http://localhost:8000/api/search/?q=director" \
  -H "X-API-Key: your-api-key"
```

For local development, the API key is typically found in `backend/.env` as `API_KEY`.

---

## Table of Contents

1. [Core Search Endpoints](#core-search-endpoints)
   - [GET /api/search/ - Search Jobs (GET)](#get-apisearch)
   - [POST /api/search/ - Search Jobs (POST)](#post-apisearch)
   - [POST /api/search/semantic - Semantic Search Only](#post-apisearchsemantic)
   - [POST /api/search/advanced - Advanced Filtered Search](#post-apisearchadvanced)

2. [Job Discovery Endpoints](#job-discovery-endpoints)
   - [GET /api/search/similar/{job_id} - Find Similar Jobs](#get-apisearchsimilarjob_id)
   - [GET /api/search/compare/{job1_id}/{job2_id} - Compare Two Jobs](#get-apisearchcomparejob1_idjob2_id)

3. [Search Enhancement Endpoints](#search-enhancement-endpoints)
   - [GET /api/search/suggestions - Query Autocomplete](#get-apisearchsuggestions)
   - [GET /api/search/recommendations - Search Recommendations](#get-apisearchrecommendations)
   - [GET /api/search/trending - Trending Searches](#get-apisearchtrending)
   - [GET /api/search/popular-filters - Popular Filters](#get-apisearchpopular-filters)

4. [Metadata Endpoints](#metadata-endpoints)
   - [GET /api/search/facets - Search Facets](#get-apisearchfacets)
   - [GET /api/search/filters/stats - Filter Statistics](#get-apisearchfiltersstats)

5. [Data Models](#data-models)
6. [Common Workflows](#common-workflows)
7. [Error Handling](#error-handling)
8. [Performance Optimization](#performance-optimization)

---

## Core Search Endpoints

### GET /api/search/

Search job descriptions using GET request with query parameters. Automatically selects between semantic and full-text search.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query text (keywords or natural language) |
| `classification` | string | No | Filter by job classification (e.g., "EX-01", "PM-05") |
| `language` | string | No | Filter by language ("en" or "fr") |
| `department` | string | No | Filter by department name |
| `limit` | integer | No | Maximum results (default: 20, min: 1, max: 100) |
| `use_semantic_search` | boolean | No | Enable semantic search (default: true) |

#### Response

```json
{
  "query": "strategic planning director",
  "search_type": "semantic",
  "total_results": 15,
  "results": [
    {
      "job_id": 123,
      "job_number": "103249",
      "title": "Director, Strategic Planning",
      "classification": "EX-01",
      "language": "en",
      "relevance_score": 0.92,
      "matching_sections": [
        {
          "section_type": "general_accountability",
          "section_id": 456,
          "snippet": "...responsible for strategic planning initiatives..."
        }
      ],
      "snippet": "The Director of Strategic Planning leads..."
    }
  ]
}
```

#### Example

```bash
# Basic search
curl -X GET "http://localhost:8000/api/search/?q=project+manager" \
  -H "X-API-Key: your-api-key"

# Search with filters
curl -X GET "http://localhost:8000/api/search/?q=analyst&classification=EC-05&language=en&limit=10" \
  -H "X-API-Key: your-api-key"

# Full-text search only (disable semantic)
curl -X GET "http://localhost:8000/api/search/?q=budget&use_semantic_search=false" \
  -H "X-API-Key: your-api-key"
```

---

### POST /api/search/

Search job descriptions using POST request with JSON body. Supports all search options including section filtering.

#### Request Body

```json
{
  "query": "data analysis and reporting",
  "classification": "EC-06",
  "language": "en",
  "department": "Finance",
  "section_types": ["general_accountability", "specific_accountabilities"],
  "limit": 25,
  "use_semantic_search": true,
  "effective_date_from": "2023-01-01",
  "effective_date_to": "2024-12-31",
  "salary_min": 80000,
  "salary_max": 120000,
  "location": "Ottawa",
  "min_fte": 2,
  "max_fte": 10
}
```

#### Response

Same as GET /api/search/ endpoint.

#### Example

```bash
# Search with complex filters
curl -X POST "http://localhost:8000/api/search/" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "cybersecurity",
    "classification": "IT-03",
    "language": "en",
    "section_types": ["knowledge_skills"],
    "limit": 20,
    "use_semantic_search": true
  }'
```

---

### POST /api/search/semantic

Perform pure semantic search using vector embeddings only (no fallback to full-text).

#### Request Body

```json
{
  "query": "What jobs involve leading digital transformation initiatives?",
  "classification": "EX-01",
  "language": "en",
  "limit": 10,
  "use_semantic_search": true
}
```

#### Response

```json
{
  "query": "What jobs involve leading digital transformation initiatives?",
  "search_type": "semantic",
  "total_results": 8,
  "results": [
    {
      "job_id": 145,
      "job_number": "105678",
      "title": "Director, Digital Services",
      "classification": "EX-01",
      "language": "en",
      "relevance_score": 0.89,
      "matching_sections": [...],
      "snippet": "...",
      "matching_chunks": 5
    }
  ],
  "message": null
}
```

**Note**: If no semantic matches are found (embeddings unavailable), the response includes:
```json
{
  "query": "...",
  "search_type": "semantic",
  "total_results": 0,
  "results": [],
  "message": "No semantic matches found - try full-text search"
}
```

#### Example

```bash
# Natural language semantic search
curl -X POST "http://localhost:8000/api/search/semantic" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Jobs requiring data science and machine learning expertise",
    "limit": 15
  }'
```

---

### POST /api/search/advanced

Advanced search with comprehensive filtering including date ranges, salary bands, location, and metadata filters.

#### Request Body

```json
{
  "query": "policy analyst",
  "classification": "EC-05",
  "language": "en",
  "department": "Policy and Strategy",
  "effective_date_from": "2023-06-01",
  "effective_date_to": "2024-12-31",
  "salary_min": 75000,
  "salary_max": 95000,
  "location": "Ottawa",
  "min_fte": 1,
  "max_fte": 5,
  "limit": 20
}
```

#### Response

```json
{
  "results": [
    {
      "job_id": 234,
      "job_number": "107890",
      "title": "Senior Policy Analyst",
      "classification": "EC-05",
      "language": "en",
      "status": "processed",
      "created_at": "2023-08-15T10:30:00",
      "salary_budget": 85000.0,
      "effective_date": "2023-09-01",
      "department": "Policy and Strategy Division",
      "location": "Ottawa, ON",
      "fte_count": 3
    }
  ],
  "total_found": 12,
  "query": "policy analyst",
  "filters_applied": {
    "classification": "EC-05",
    "language": "en",
    "department": "Policy and Strategy",
    "effective_date_from": "2023-06-01",
    "effective_date_to": "2024-12-31",
    "salary_min": 75000.0,
    "salary_max": 95000.0,
    "location": "Ottawa",
    "min_fte": 1,
    "max_fte": 5
  },
  "search_method": "advanced_filtered_search"
}
```

#### Example

```bash
# Advanced search with salary and date filters
curl -X POST "http://localhost:8000/api/search/advanced" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "financial management",
    "classification": "FI-03",
    "language": "en",
    "effective_date_from": "2024-01-01",
    "salary_min": 70000,
    "salary_max": 100000,
    "location": "National Capital Region",
    "limit": 15
  }'
```

---

## Job Discovery Endpoints

### GET /api/search/similar/{job_id}

Find jobs similar to a specified job description using optimized vector similarity.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | integer | Yes | ID of the source job description |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Number of similar jobs (default: 10, min: 1, max: 50) |
| `classification_filter` | string | No | Filter by classification |
| `language_filter` | string | No | Filter by language (EN/FR) |

#### Response

```json
{
  "source_job": {
    "id": 123,
    "job_number": "103456",
    "title": "Project Manager",
    "classification": "PM-05"
  },
  "similar_jobs": [
    {
      "id": 145,
      "job_number": "104567",
      "title": "Senior Project Manager",
      "classification": "PM-06",
      "language": "en",
      "similarity_score": 0.87,
      "matching_chunks": 8
    },
    {
      "id": 167,
      "job_number": "105678",
      "title": "Program Manager",
      "classification": "PM-06",
      "language": "en",
      "similarity_score": 0.82,
      "matching_chunks": 6
    }
  ],
  "total_found": 12,
  "search_method": "optimized_vector_similarity",
  "filters_applied": {
    "classification": null,
    "language": null
  }
}
```

**Similarity Score**: Range 0.0 to 1.0 (higher = more similar)
- **0.85-1.0**: Very high similarity (likely same role with minor variations)
- **0.70-0.84**: High similarity (related roles, significant overlap)
- **0.50-0.69**: Moderate similarity (some shared responsibilities)
- **Below 0.50**: Low similarity

#### Example

```bash
# Find similar jobs
curl -X GET "http://localhost:8000/api/search/similar/123?limit=10" \
  -H "X-API-Key: your-api-key"

# Find similar jobs in same classification
curl -X GET "http://localhost:8000/api/search/similar/123?limit=5&classification_filter=PM-05" \
  -H "X-API-Key: your-api-key"

# Find similar English jobs only
curl -X GET "http://localhost:8000/api/search/similar/123?language_filter=en" \
  -H "X-API-Key: your-api-key"
```

---

### GET /api/search/compare/{job1_id}/{job2_id}

Compare two job descriptions with detailed similarity analysis.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job1_id` | integer | Yes | ID of first job description |
| `job2_id` | integer | Yes | ID of second job description |

#### Response

```json
{
  "comparison_id": "123_145",
  "jobs": {
    "job1": {
      "id": 123,
      "job_number": "103456",
      "title": "Project Manager",
      "classification": "PM-05",
      "language": "en"
    },
    "job2": {
      "id": 145,
      "job_number": "104567",
      "title": "Senior Project Manager",
      "classification": "PM-06",
      "language": "en"
    }
  },
  "similarity_analysis": {
    "overall_similarity": 0.82,
    "similarity_level": "High",
    "metadata_comparison": {
      "classification": {
        "job1": "PM-05",
        "job2": "PM-06",
        "match": false
      },
      "language": {
        "job1": "en",
        "job2": "en",
        "match": true
      },
      "title_similarity": 0.75
    },
    "section_comparison": [
      {
        "section_type": "general_accountability",
        "job1_content": "Responsible for managing complex projects...",
        "job2_content": "Leads strategic initiatives and project portfolios...",
        "similarity_score": 0.68,
        "both_present": true,
        "job1_only": false,
        "job2_only": false
      },
      {
        "section_type": "knowledge_skills",
        "job1_content": "PMP certification, 5 years experience...",
        "job2_content": "PMP certification, 8+ years experience, leadership...",
        "similarity_score": 0.72,
        "both_present": true,
        "job1_only": false,
        "job2_only": false
      }
    ]
  },
  "recommendations": [
    "These jobs have good similarity and may share common skill requirements.",
    "Different classifications (PM-05 vs PM-06) may indicate different organizational levels."
  ]
}
```

#### Example

```bash
# Compare two job descriptions
curl -X GET "http://localhost:8000/api/search/compare/123/145" \
  -H "X-API-Key: your-api-key"
```

---

## Search Enhancement Endpoints

### GET /api/search/suggestions

Get ML-powered query suggestions based on partial input for autocomplete.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Partial query text (min length: 3) |
| `user_id` | string | No | User ID for personalized suggestions |
| `session_id` | string | No | Session ID for context-aware suggestions |
| `limit` | integer | No | Maximum suggestions (default: 5, min: 1, max: 10) |

#### Response

```json
[
  {
    "suggestion": "project manager",
    "confidence": 0.92,
    "frequency": 45,
    "category": "popular"
  },
  {
    "suggestion": "project management office",
    "confidence": 0.85,
    "frequency": 28,
    "category": "semantic"
  },
  {
    "suggestion": "project coordinator",
    "confidence": 0.78,
    "frequency": 22,
    "category": "related"
  }
]
```

#### Example

```bash
# Get query suggestions
curl -X GET "http://localhost:8000/api/search/suggestions?q=proj&limit=5" \
  -H "X-API-Key: your-api-key"

# Personalized suggestions
curl -X GET "http://localhost:8000/api/search/suggestions?q=data&user_id=user123&limit=8" \
  -H "X-API-Key: your-api-key"
```

---

### GET /api/search/recommendations

Get comprehensive search recommendations including related searches, trending queries, and personalized suggestions.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | No | Current search query for context |
| `classification` | string | No | Classification filter context |
| `user_id` | string | No | User ID for personalized recommendations |
| `limit` | integer | No | Max per category (default: 8, min: 1, max: 20) |

#### Response

```json
{
  "related_searches": [
    {
      "query": "IT project manager",
      "relevance": 0.89,
      "result_count": 34
    },
    {
      "query": "agile project management",
      "relevance": 0.82,
      "result_count": 28
    }
  ],
  "trending_queries": [
    {
      "query": "cybersecurity",
      "trend_score": 95.5,
      "search_count": 67
    }
  ],
  "personalized_suggestions": [
    {
      "query": "technical project manager",
      "reason": "based_on_history",
      "confidence": 0.88
    }
  ],
  "metadata": {
    "generated_at": "2024-10-17T14:30:00",
    "context": {
      "query": "project manager",
      "classification": null
    },
    "total_recommendations": 24,
    "generation_time_ms": 0
  }
}
```

#### Example

```bash
# Get recommendations
curl -X GET "http://localhost:8000/api/search/recommendations?query=analyst" \
  -H "X-API-Key: your-api-key"

# Context-aware recommendations
curl -X GET "http://localhost:8000/api/search/recommendations?query=director&classification=EX-01&limit=10" \
  -H "X-API-Key: your-api-key"
```

---

### GET /api/search/trending

Get trending search queries for a specified time period.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period` | string | No | Time period: "1h", "6h", "24h", "7d" (default: "24h") |
| `limit` | integer | No | Maximum queries (default: 10, min: 1, max: 20) |

#### Response

```json
[
  {
    "query": "data scientist",
    "search_count": 145,
    "avg_results": 23.4,
    "unique_sessions": 89,
    "trend_score": 12905.0
  },
  {
    "query": "cybersecurity analyst",
    "search_count": 112,
    "avg_results": 18.7,
    "unique_sessions": 76,
    "trend_score": 8512.0
  }
]
```

#### Example

```bash
# Get 24-hour trending searches
curl -X GET "http://localhost:8000/api/search/trending?period=24h&limit=10" \
  -H "X-API-Key: your-api-key"

# Get weekly trends
curl -X GET "http://localhost:8000/api/search/trending?period=7d&limit=15" \
  -H "X-API-Key: your-api-key"
```

---

### GET /api/search/popular-filters

Get popular filter suggestions based on query context and general usage patterns.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | No | Query context for filter suggestions |
| `limit` | integer | No | Max per category (default: 10, min: 1, max: 20) |

#### Response

```json
{
  "classifications": [
    {
      "value": "EC-05",
      "count": 234,
      "label": "Classification: EC-05"
    },
    {
      "value": "PM-05",
      "count": 189,
      "label": "Classification: PM-05"
    }
  ],
  "departments": [
    {
      "value": "Corporate Services",
      "count": 156,
      "label": "Department: Corporate Services"
    }
  ],
  "languages": [
    {
      "value": "en",
      "count": 1245,
      "label": "Language: en"
    },
    {
      "value": "fr",
      "count": 987,
      "label": "Language: fr"
    }
  ],
  "date_ranges": [
    {
      "value": "last_month",
      "label": "Last 30 days"
    },
    {
      "value": "last_quarter",
      "label": "Last 3 months"
    },
    {
      "value": "last_year",
      "label": "Last 12 months"
    },
    {
      "value": "current_year",
      "label": "Current year"
    }
  ]
}
```

#### Example

```bash
# Get popular filters
curl -X GET "http://localhost:8000/api/search/popular-filters?limit=15" \
  -H "X-API-Key: your-api-key"

# Context-aware filters
curl -X GET "http://localhost:8000/api/search/popular-filters?query=analyst&limit=10" \
  -H "X-API-Key: your-api-key"
```

---

## Metadata Endpoints

### GET /api/search/facets

Get available facets for search filtering with counts.

#### Response

```json
{
  "classifications": [
    {
      "value": "EC-05",
      "count": 234
    },
    {
      "value": "PM-05",
      "count": 189
    },
    {
      "value": "IT-03",
      "count": 156
    }
  ],
  "languages": [
    {
      "value": "en",
      "count": 1245
    },
    {
      "value": "fr",
      "count": 987
    }
  ],
  "section_types": [
    {
      "value": "general_accountability",
      "count": 2134
    },
    {
      "value": "specific_accountabilities",
      "count": 2098
    },
    {
      "value": "knowledge_skills",
      "count": 1876
    }
  ],
  "embedding_stats": {
    "chunks_with_embeddings": 15678,
    "semantic_search_available": true
  }
}
```

#### Example

```bash
# Get all facets
curl -X GET "http://localhost:8000/api/search/facets" \
  -H "X-API-Key: your-api-key"
```

---

### GET /api/search/filters/stats

Get statistics for filter options to help users understand data ranges.

#### Response

```json
{
  "salary_statistics": {
    "min_salary": 45000.0,
    "max_salary": 185000.0,
    "avg_salary": 87234.56,
    "salary_count": 1234
  },
  "date_statistics": {
    "earliest_date": "2020-01-15",
    "latest_date": "2024-12-31",
    "date_count": 1567
  },
  "fte_statistics": {
    "min_fte": 1,
    "max_fte": 50,
    "avg_fte": 5.8,
    "fte_count": 1456
  },
  "department_distribution": [
    {
      "department": "Corporate Services",
      "count": 234
    },
    {
      "department": "Policy and Strategy",
      "count": 198
    }
  ],
  "location_distribution": [
    {
      "location": "Ottawa, ON",
      "count": 567
    },
    {
      "location": "Toronto, ON",
      "count": 234
    }
  ],
  "classification_distribution": [
    {
      "classification": "EC-05",
      "count": 234
    }
  ],
  "language_distribution": [
    {
      "language": "en",
      "count": 1245
    },
    {
      "language": "fr",
      "count": 987
    }
  ]
}
```

#### Example

```bash
# Get filter statistics
curl -X GET "http://localhost:8000/api/search/filters/stats" \
  -H "X-API-Key: your-api-key"
```

---

## Data Models

### SearchQuery

Request model for search operations.

```json
{
  "query": "string (required)",
  "classification": "string (optional)",
  "language": "string (optional, 'en' or 'fr')",
  "department": "string (optional)",
  "section_types": ["array of strings (optional)"],
  "limit": "integer (default: 20, min: 1, max: 100)",
  "use_semantic_search": "boolean (default: true)",
  "effective_date_from": "date (optional, ISO 8601: YYYY-MM-DD)",
  "effective_date_to": "date (optional, ISO 8601: YYYY-MM-DD)",
  "salary_min": "decimal (optional, ≥ 0)",
  "salary_max": "decimal (optional, ≥ 0)",
  "location": "string (optional)",
  "min_fte": "integer (optional, ≥ 1)",
  "max_fte": "integer (optional, ≥ 1)"
}
```

### SearchResult

Response model for individual search results.

```json
{
  "job_id": "integer",
  "job_number": "string",
  "title": "string",
  "classification": "string",
  "language": "string",
  "relevance_score": "float (0.0 to 1.0)",
  "matching_sections": [
    {
      "section_type": "string",
      "section_id": "integer",
      "snippet": "string (truncated content)"
    }
  ],
  "snippet": "string (relevant excerpt from job description)"
}
```

---

## Common Workflows

### 1. Basic Keyword Search

```bash
# Step 1: Search for jobs
curl -X GET "http://localhost:8000/api/search/?q=project+manager&language=en&limit=20" \
  -H "X-API-Key: your-api-key"

# Step 2: Get job details for a result
curl -X GET "http://localhost:8000/api/jobs/123" \
  -H "X-API-Key: your-api-key"
```

### 2. Semantic Search Workflow

```bash
# Step 1: Check if semantic search is available
curl -X GET "http://localhost:8000/api/search/facets" \
  -H "X-API-Key: your-api-key"
# Check embedding_stats.semantic_search_available

# Step 2: Perform semantic search with natural language
curl -X POST "http://localhost:8000/api/search/semantic" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What positions involve cloud infrastructure and DevOps?",
    "limit": 15
  }'

# Step 3: Find similar jobs to a result
curl -X GET "http://localhost:8000/api/search/similar/145?limit=10" \
  -H "X-API-Key: your-api-key"
```

### 3. Advanced Filtered Search

```bash
# Step 1: Get filter statistics
curl -X GET "http://localhost:8000/api/search/filters/stats" \
  -H "X-API-Key: your-api-key"
# Review salary ranges, date ranges, departments

# Step 2: Perform advanced search with filters
curl -X POST "http://localhost:8000/api/search/advanced" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "financial analyst",
    "classification": "FI-02",
    "language": "en",
    "department": "Finance",
    "effective_date_from": "2024-01-01",
    "salary_min": 70000,
    "salary_max": 90000,
    "location": "Ottawa",
    "limit": 25
  }'
```

### 4. Job Comparison Workflow

```bash
# Step 1: Search for jobs
curl -X GET "http://localhost:8000/api/search/?q=IT+manager&classification=IT-04" \
  -H "X-API-Key: your-api-key"
# Get job IDs: 123, 145

# Step 2: Compare the jobs
curl -X GET "http://localhost:8000/api/search/compare/123/145" \
  -H "X-API-Key: your-api-key"
# Review similarity scores and section comparisons

# Step 3: Find similar jobs to preferred option
curl -X GET "http://localhost:8000/api/search/similar/123?limit=10&classification_filter=IT-04" \
  -H "X-API-Key: your-api-key"
```

### 5. Search Enhancement Workflow

```bash
# Step 1: Get query suggestions as user types
curl -X GET "http://localhost:8000/api/search/suggestions?q=dat&limit=5" \
  -H "X-API-Key: your-api-key"

# Step 2: Get trending searches for context
curl -X GET "http://localhost:8000/api/search/trending?period=24h&limit=10" \
  -H "X-API-Key: your-api-key"

# Step 3: Get popular filters for selected query
curl -X GET "http://localhost:8000/api/search/popular-filters?query=data+analyst&limit=10" \
  -H "X-API-Key: your-api-key"

# Step 4: Perform search with suggested filters
curl -X POST "http://localhost:8000/api/search/" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "data analyst",
    "classification": "EC-05",
    "language": "en",
    "limit": 20
  }'

# Step 5: Get recommendations based on search
curl -X GET "http://localhost:8000/api/search/recommendations?query=data+analyst&limit=8" \
  -H "X-API-Key: your-api-key"
```

---

## Error Handling

### Common Error Responses

#### 400 Bad Request - Invalid Query Parameters
```json
{
  "detail": "Query parameter 'q' is required and must be at least 3 characters"
}
```

#### 404 Not Found - Job Not Found
```json
{
  "detail": "Job description not found"
}
```

#### 422 Unprocessable Entity - Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "salary_min"],
      "msg": "ensure this value is greater than or equal to 0",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

#### 500 Internal Server Error - Search Failed
```json
{
  "detail": "Search operation failed"
}
```

### Error Recovery Strategies

1. **Empty Results**: Try broadening search criteria or disabling filters
2. **Semantic Search Unavailable**: System falls back to full-text search automatically
3. **Timeout on Complex Queries**: Reduce limit, simplify filters, or try simpler query
4. **No Similar Jobs Found**: Lower similarity threshold or expand classification filter

---

## Performance Optimization

### Caching

The Search API implements intelligent caching:

- **Search Results**: Cached for 30 minutes
- **Similar Jobs**: Cached per job_id and limit
- **Filter Statistics**: Cached for 1 hour
- **Facets**: Cached for 1 hour

**Cache Headers**: Not exposed to clients (server-side caching only)

### Best Practices

1. **Use Semantic Search**: More accurate for natural language queries
2. **Limit Results**: Start with smaller limits (10-20) for faster responses
3. **Apply Filters Early**: Classification and language filters significantly reduce result sets
4. **Reuse Similar Jobs**: Cache similar job results on client side
5. **Batch Requests**: Use similar jobs and comparison endpoints to explore related jobs efficiently
6. **Monitor Trends**: Use trending and recommendations endpoints to guide user searches

### Performance Metrics

| Operation | Average Response Time | Cache Hit Rate |
|-----------|----------------------|----------------|
| Basic Search (20 results) | 50-150ms | 40% |
| Semantic Search | 200-500ms | 30% |
| Advanced Search | 100-300ms | 35% |
| Similar Jobs | 150-400ms | 50% |
| Job Comparison | 300-600ms | 20% |
| Facets/Stats | 50-100ms | 70% |
| Suggestions | 30-80ms | 60% |

### Search Analytics

The API tracks search analytics automatically:
- Session tracking via `x-session-id` header
- User tracking via `x-user-id` header
- IP address recording for geographic analysis
- Execution time monitoring
- Result quality metrics

**Privacy Note**: Analytics data is used to improve search quality and is not shared externally.

---

## Related APIs

- **[Jobs API](jobs-api.md)** - Retrieve full job details from search results
- **[Translation Memory API](translation_memory_api.md)** - Search translation concordance for bilingual terms

---

**Last Updated**: 2024-10-17
**API Version**: 2.0
**Documentation Version**: 1.0
