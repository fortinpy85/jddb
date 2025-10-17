# Translation Memory API Documentation

## Overview

The Translation Memory Service provides AI-powered translation memory functionality with semantic similarity search using pgvector embeddings. It enables efficient management of translation projects, storage of translation pairs, and intelligent suggestions based on context.

## Features

- **Project Management**: Organize translations into projects with language pair tracking
- **Semantic Search**: Vector-based similarity search for finding related translations
- **Quality Tracking**: Quality scores, confidence levels, and usage statistics
- **Domain Classification**: Organize translations by domain and subdomain
- **Bilingual Support**: Full English/French language pair support
- **Analytics**: Comprehensive project statistics and usage metrics

## Base URL

```
http://localhost:8000/api/translation-memory
```

## Authentication

Currently in development mode. Production deployment will include appropriate authentication mechanisms.

## Endpoints

### 1. Create Translation Project

Create a new translation project to organize translation memory entries.

**Endpoint**: `POST /api/translation-memory/projects`

**Request Body**:
```json
{
  "name": "Job Descriptions EN-FR",
  "description": "Translation memory for government job descriptions",
  "source_language": "en",
  "target_language": "fr",
  "project_type": "job_descriptions"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Translation project created successfully",
  "project": {
    "id": 1,
    "name": "Job Descriptions EN-FR",
    "description": "Translation memory for government job descriptions",
    "source_language": "en",
    "target_language": "fr",
    "project_type": "job_descriptions",
    "status": "active",
    "created_at": "2025-10-13T17:21:52.251025"
  }
}
```

### 2. List Translation Projects

Retrieve all translation projects with pagination support.

**Endpoint**: `GET /api/translation-memory/projects`

**Query Parameters**:
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Number of records to return (default: 20, max: 100)
- `status` (optional): Filter by project status

**Response**:
```json
{
  "success": true,
  "total": 5,
  "skip": 0,
  "limit": 20,
  "projects": [
    {
      "id": 1,
      "name": "Job Descriptions EN-FR",
      "description": "Translation memory for government job descriptions",
      "source_language": "en",
      "target_language": "fr",
      "project_type": "job_descriptions",
      "status": "active",
      "created_at": "2025-10-13T17:21:52.251025",
      "updated_at": null
    }
  ]
}
```

### 3. Add Translation to Memory

Add a new translation pair to a project with optional quality metrics and domain classification.

**Endpoint**: `POST /api/translation-memory/projects/{project_id}/translations`

**Path Parameters**:
- `project_id`: ID of the translation project

**Request Body**:
```json
{
  "source_text": "Senior Manager",
  "target_text": "Gestionnaire principal",
  "source_language": "en",
  "target_language": "fr",
  "domain": "job_descriptions",
  "subdomain": "management",
  "quality_score": 0.95,
  "confidence_score": 0.92,
  "metadata": {
    "translator": "professional",
    "reviewed": true
  }
}
```

**Response**:
```json
{
  "success": true,
  "message": "Translation added to memory successfully",
  "translation": {
    "id": 1,
    "source_text": "Senior Manager",
    "target_text": "Gestionnaire principal",
    "source_language": "en",
    "target_language": "fr",
    "domain": "job_descriptions",
    "subdomain": "management",
    "quality_score": 0.95,
    "confidence_score": 0.92,
    "usage_count": 0,
    "created_at": "2025-10-13T17:22:27.189882"
  }
}
```

**Note**: This endpoint automatically generates and stores vector embeddings for semantic similarity search.

### 4. Get Translation Suggestions

Get AI-powered translation suggestions based on semantic similarity to source text.

**Endpoint**: `POST /api/translation-memory/suggestions`

**Request Body**:
```json
{
  "source_text": "Senior Manager, Strategic Planning",
  "source_language": "en",
  "target_language": "fr",
  "project_id": 1,
  "context": "job_descriptions"
}
```

**Response**:
```json
{
  "success": true,
  "query": {
    "source_text": "Senior Manager, Strategic Planning",
    "source_language": "en",
    "target_language": "fr",
    "project_id": 1
  },
  "suggestions": [
    {
      "id": 1,
      "source_text": "Senior Manager",
      "target_text": "Gestionnaire principal",
      "source_language": "en",
      "target_language": "fr",
      "domain": "job_descriptions",
      "quality_score": 0.95,
      "usage_count": 5,
      "similarity_score": 0.87,
      "last_used": "2025-10-13T15:30:00"
    }
  ],
  "count": 1
}
```

**Similarity Threshold**: Default threshold is 0.7 (70% similarity)

### 5. Search Similar Translations

Advanced search for similar translations with customizable similarity threshold and filtering.

**Endpoint**: `POST /api/translation-memory/search`

**Query Parameters**:
- `query_text` (required): Text to search for
- `source_language` (required): Source language code
- `target_language` (required): Target language code
- `project_id` (optional): Limit search to specific project
- `domain` (optional): Filter by domain
- `similarity_threshold` (optional): Minimum similarity score (0.0-1.0, default: 0.7)
- `limit` (optional): Maximum number of results (default: 10, max: 50)

**Example**:
```
POST /api/translation-memory/search?query_text=strategic+planning&source_language=en&target_language=fr&similarity_threshold=0.8&limit=5
```

**Response**:
```json
{
  "success": true,
  "query": {
    "text": "strategic planning",
    "source_language": "en",
    "target_language": "fr",
    "similarity_threshold": 0.8,
    "project_id": null,
    "domain": null
  },
  "results": [
    {
      "id": 15,
      "source_text": "Strategic Planning",
      "target_text": "Planification stratégique",
      "similarity_score": 0.98,
      "quality_score": 0.95,
      "usage_count": 12
    }
  ],
  "count": 1
}
```

### 6. Update Translation Usage

Track usage statistics and collect user feedback for translation memory entries.

**Endpoint**: `PUT /api/translation-memory/translations/{tm_id}/usage`

**Path Parameters**:
- `tm_id`: Translation memory entry ID

**Request Body**:
```json
{
  "used_translation": true,
  "user_feedback": {
    "rating": 5,
    "comment": "Perfect translation",
    "helpful": true
  }
}
```

**Response**:
```json
{
  "success": true,
  "message": "Translation usage updated successfully",
  "translation_id": 1
}
```

### 7. Get Project Statistics

Retrieve comprehensive statistics for a translation project.

**Endpoint**: `GET /api/translation-memory/projects/{project_id}/statistics`

**Path Parameters**:
- `project_id`: Project ID

**Response**:
```json
{
  "success": true,
  "statistics": {
    "total_translations": 150,
    "unique_sources": 145,
    "avg_quality_score": 0.89,
    "domains": [
      {
        "domain": "job_descriptions",
        "count": 120
      },
      {
        "domain": "general",
        "count": 30
      }
    ],
    "languages": {
      "source": ["en"],
      "target": ["fr"]
    }
  }
}
```

### 8. Health Check

Check the health status of the Translation Memory service.

**Endpoint**: `GET /api/translation-memory/health`

**Response**:
```json
{
  "success": true,
  "service": "Translation Memory",
  "status": "healthy",
  "timestamp": "2025-10-13T17:30:00.000000",
  "features": [
    "Project Management",
    "Translation Storage",
    "Vector Similarity Search",
    "Usage Tracking",
    "Statistics"
  ]
}
```

## Data Models

### CreateProjectRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Project name (max 255 chars) |
| description | string | No | Project description |
| source_language | string | Yes | Source language code (e.g., 'en') |
| target_language | string | Yes | Target language code (e.g., 'fr') |
| project_type | string | No | Type of project (default: 'job_descriptions') |

### AddTranslationRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| source_text | string | Yes | Source text to translate |
| target_text | string | Yes | Target translation |
| source_language | string | Yes | Source language code |
| target_language | string | Yes | Target language code |
| domain | string | No | Domain category (max 50 chars) |
| subdomain | string | No | Subdomain category (max 50 chars) |
| quality_score | float | No | Quality score (0.0-1.0) |
| confidence_score | float | No | Confidence score (0.0-1.0) |
| metadata | object | No | Additional metadata |

### TranslationSuggestionRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| source_text | string | Yes | Text to find suggestions for |
| source_language | string | Yes | Source language code |
| target_language | string | Yes | Target language code |
| project_id | integer | No | Limit to specific project |
| context | string | No | Additional context for matching |

### UpdateUsageRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| used_translation | boolean | Yes | Whether the translation was used |
| user_feedback | object | No | User feedback data |

## Technical Details

### Vector Embeddings

- **Model**: OpenAI text-embedding-ada-002
- **Dimensions**: 1536
- **Storage**: PostgreSQL with pgvector extension
- **Similarity Metric**: Cosine distance (1 - cosine_similarity)

### Database Schema

#### translation_projects
- Primary table for organizing translation memories
- Tracks language pairs and project metadata
- Supports project status management

#### translation_memory
- Stores translation pairs with quality metrics
- Includes domain classification
- Tracks usage statistics and last used timestamp
- Supports JSON metadata storage

#### translation_embeddings
- Stores vector embeddings for semantic search
- Links to translation_memory entries
- Includes text hash for deduplication
- Optimized with vector similarity indexes

### Performance Considerations

- **Embedding Generation**: ~100-200ms per translation (async)
- **Similarity Search**: ~10-50ms for typical queries
- **Batch Operations**: Supported for bulk imports
- **Caching**: Redis caching for frequently accessed translations
- **Indexing**: pgvector indexes for fast similarity search

## Error Handling

All endpoints return consistent error responses:

```json
{
  "detail": "Error description here"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad request (validation error)
- `404`: Resource not found
- `500`: Internal server error

## Usage Examples

### Complete Workflow Example

```bash
# 1. Create a translation project
curl -X POST http://localhost:8000/api/translation-memory/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Job Descriptions EN-FR",
    "source_language": "en",
    "target_language": "fr",
    "project_type": "job_descriptions"
  }'

# 2. Add translations to the project
curl -X POST http://localhost:8000/api/translation-memory/projects/1/translations \
  -H "Content-Type: application/json" \
  -d '{
    "source_text": "Senior Manager",
    "target_text": "Gestionnaire principal",
    "source_language": "en",
    "target_language": "fr",
    "domain": "job_descriptions",
    "quality_score": 0.95
  }'

# 3. Get translation suggestions
curl -X POST http://localhost:8000/api/translation-memory/suggestions \
  -H "Content-Type: application/json" \
  -d '{
    "source_text": "Senior Manager, Strategic Planning",
    "source_language": "en",
    "target_language": "fr",
    "project_id": 1
  }'

# 4. Search for similar translations
curl -X POST "http://localhost:8000/api/translation-memory/search?query_text=strategic+planning&source_language=en&target_language=fr&similarity_threshold=0.8&limit=5"

# 5. Update usage statistics
curl -X PUT http://localhost:8000/api/translation-memory/translations/1/usage \
  -H "Content-Type: application/json" \
  -d '{
    "used_translation": true,
    "user_feedback": {"rating": 5, "helpful": true}
  }'

# 6. Get project statistics
curl -X GET http://localhost:8000/api/translation-memory/projects/1/statistics
```

## Best Practices

1. **Quality Scores**: Always include quality scores (0.8-1.0 for professional translations)
2. **Domain Classification**: Use consistent domain names for better filtering
3. **Project Organization**: Create separate projects for different content types
4. **Usage Tracking**: Update usage statistics to improve future suggestions
5. **Similarity Thresholds**:
   - 0.9-1.0: Nearly identical matches
   - 0.8-0.9: High similarity, safe to use
   - 0.7-0.8: Similar context, review recommended
   - <0.7: Different context, manual review required

## Integration with Frontend

The Translation Memory Service integrates with the collaborative editing features:

1. **Real-time Suggestions**: Display suggestions as users type
2. **Context-Aware**: Use current document context for better matches
3. **User Feedback**: Collect ratings to improve suggestion quality
4. **History Tracking**: Show previously used translations

## Future Enhancements

- Multi-language project support (beyond pairs)
- Glossary integration
- Machine translation fallback
- Batch import/export functionality
- Advanced analytics and reporting
- Translation workflow management

## Support

For issues or questions:
- API Documentation: http://localhost:8000/api/docs
- GitHub Issues: https://github.com/fortinpy85/jddb/issues
- Health Check: http://localhost:8000/api/translation-memory/health
