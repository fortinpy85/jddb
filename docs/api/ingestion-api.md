# Ingestion API Documentation

**Base URL**: `/api/ingestion`
**Authentication**: API key required for all endpoints
**Version**: 1.0

---

## Overview

The Ingestion API handles file upload, processing, and batch import of job descriptions into the JDDB system. It supports multiple file formats, automatic language detection, section parsing, and skill extraction.

### Key Features

- Multi-format file upload (.txt, .doc, .docx, .pdf)
- Automatic language detection (English/French)
- Section parsing and extraction
- Skill extraction using Lightcast API
- Batch processing support
- Real-time processing status tracking
- Comprehensive error reporting

### Supported File Formats

| Format | Extension | Processing | Notes |
|--------|-----------|------------|-------|
| Plain Text | `.txt` | Direct parsing | Preferred format |
| Microsoft Word (Legacy) | `.doc` | Binary conversion | Requires python-docx |
| Microsoft Word | `.docx` | XML parsing | Native support |
| PDF | `.pdf` | Text extraction | OCR not supported |

---

## File Processing Pipeline

```
Upload File → Validate Format → Extract Text → Detect Language →
Parse Sections → Extract Skills → Store in Database → Return Job ID
```

### Processing Steps

1. **File Validation**: Check file size, format, and integrity
2. **Text Extraction**: Extract raw text content from file
3. **Language Detection**: Identify English or French content
4. **Section Parsing**: Extract structured sections using regex patterns
5. **Skill Extraction**: Identify skills using Lightcast API (if configured)
6. **Database Storage**: Save job description and all extracted data
7. **Response**: Return job ID and processing summary

---

## Authentication

All endpoints require API key authentication via the `X-API-Key` header.

```http
X-API-Key: your-api-key-here
```

---

## Endpoints

### Upload Single File

Upload a single job description file for processing.

```http
POST /api/ingestion/upload
```

#### Request

**Content-Type**: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | Job description file (.txt, .doc, .docx, .pdf) |
| `classification` | string | No | Override auto-detected classification (e.g., "EX-01") |
| `language` | string | No | Override auto-detected language ("en" or "fr") |
| `department` | string | No | Specify department name |
| `auto_extract_skills` | boolean | No | Enable automatic skill extraction (default: true) |

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "File processed successfully",
  "job_id": 42,
  "job_number": "103249",
  "job_title": "Director, Business Analysis",
  "classification": "EX-01",
  "language": "en",
  "file_name": "EX-01_Dir_Business_Analysis_103249.txt",
  "file_size": 12456,
  "processing_time_seconds": 3.45,
  "sections_extracted": 6,
  "skills_extracted": 12,
  "quality_score": 0.85
}
```

#### Error Responses

**400 Bad Request** - Invalid file format or parameters:
```json
{
  "detail": "Unsupported file format: .xlsx. Supported formats: .txt, .doc, .docx, .pdf"
}
```

**413 Payload Too Large** - File exceeds size limit:
```json
{
  "detail": "File size exceeds maximum limit of 10 MB"
}
```

**422 Unprocessable Entity** - Processing failed:
```json
{
  "detail": "Failed to extract text from file. File may be corrupted or in an unsupported format."
}
```

**500 Internal Server Error** - Server-side processing error:
```json
{
  "detail": "Database error during job creation"
}
```

#### Example

```bash
# Upload a text file with automatic processing
curl -X POST "http://localhost:8000/api/ingestion/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@EX-01_Director_103249.txt"

# Upload with overrides
curl -X POST "http://localhost:8000/api/ingestion/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@job_description.txt" \
  -F "classification=EX-02" \
  -F "language=fr" \
  -F "department=Finance"

# Upload without skill extraction
curl -X POST "http://localhost:8000/api/ingestion/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@job.txt" \
  -F "auto_extract_skills=false"
```

---

### Batch Upload

Upload multiple job description files in a single request.

```http
POST /api/ingestion/batch-upload
```

#### Request

**Content-Type**: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `files` | file[] | Yes | Array of job description files (max 50 files) |
| `auto_extract_skills` | boolean | No | Enable skill extraction for all files (default: true) |
| `continue_on_error` | boolean | No | Continue processing if one file fails (default: true) |

#### Response (200 OK)

```json
{
  "status": "success",
  "total_files": 10,
  "successful": 9,
  "failed": 1,
  "processing_time_seconds": 45.2,
  "results": [
    {
      "file_name": "EX-01_Director_103249.txt",
      "status": "success",
      "job_id": 42,
      "job_number": "103249",
      "job_title": "Director, Business Analysis",
      "sections_extracted": 6,
      "skills_extracted": 12
    },
    {
      "file_name": "corrupted_file.txt",
      "status": "failed",
      "error": "Failed to extract text from file"
    }
  ]
}
```

#### Error Responses

**400 Bad Request** - Invalid request:
```json
{
  "detail": "No files provided in request"
}
```

**413 Payload Too Large** - Too many files:
```json
{
  "detail": "Maximum 50 files allowed per batch upload. Received 75 files."
}
```

#### Example

```bash
# Batch upload multiple files
curl -X POST "http://localhost:8000/api/ingestion/batch-upload" \
  -H "X-API-Key: your-api-key" \
  -F "files=@job1.txt" \
  -F "files=@job2.txt" \
  -F "files=@job3.docx" \
  -F "files=@job4.pdf"

# Batch upload with error handling
curl -X POST "http://localhost:8000/api/ingestion/batch-upload" \
  -H "X-API-Key: your-api-key" \
  -F "files=@job1.txt" \
  -F "files=@job2.txt" \
  -F "continue_on_error=true"
```

---

### Get Upload Status

Check the processing status of an uploaded file.

```http
GET /api/ingestion/status/{job_id}
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | integer | Yes | Job identifier returned from upload |

#### Response (200 OK)

```json
{
  "job_id": 42,
  "job_number": "103249",
  "status": "completed",
  "file_name": "EX-01_Director_103249.txt",
  "upload_time": "2025-10-18T10:30:00Z",
  "processing_start": "2025-10-18T10:30:01Z",
  "processing_end": "2025-10-18T10:30:04Z",
  "processing_duration_seconds": 3.45,
  "sections_extracted": 6,
  "skills_extracted": 12,
  "quality_score": 0.85,
  "errors": []
}
```

**Status Values**:
- `pending` - Queued for processing
- `processing` - Currently being processed
- `completed` - Successfully processed
- `failed` - Processing failed
- `needs_review` - Completed with warnings

#### Error Responses

**404 Not Found**:
```json
{
  "detail": "Job with ID 42 not found"
}
```

#### Example

```bash
curl -X GET "http://localhost:8000/api/ingestion/status/42" \
  -H "X-API-Key: your-api-key"
```

---

### List Recent Uploads

Retrieve a list of recently uploaded files.

```http
GET /api/ingestion/recent
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Number of results (default: 50, max: 200) |
| `status` | string | No | Filter by status (completed, failed, processing, etc.) |
| `start_date` | string | No | Filter by upload date (ISO 8601 format) |
| `end_date` | string | No | Filter by upload date (ISO 8601 format) |

#### Response (200 OK)

```json
{
  "uploads": [
    {
      "job_id": 42,
      "job_number": "103249",
      "job_title": "Director, Business Analysis",
      "file_name": "EX-01_Director_103249.txt",
      "upload_time": "2025-10-18T10:30:00Z",
      "status": "completed",
      "processing_duration_seconds": 3.45
    }
  ],
  "total": 150,
  "limit": 50
}
```

#### Example

```bash
# Get last 20 uploads
curl -X GET "http://localhost:8000/api/ingestion/recent?limit=20" \
  -H "X-API-Key: your-api-key"

# Get failed uploads from last week
curl -X GET "http://localhost:8000/api/ingestion/recent?status=failed&start_date=2025-10-11T00:00:00Z" \
  -H "X-API-Key: your-api-key"
```

---

### Get Processing Statistics

Retrieve comprehensive ingestion statistics.

```http
GET /api/ingestion/stats
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date for statistics (ISO 8601) |
| `end_date` | string | No | End date for statistics (ISO 8601) |

#### Response (200 OK)

```json
{
  "total_uploads": 500,
  "successful_uploads": 475,
  "failed_uploads": 25,
  "success_rate": 0.95,
  "total_processing_time_hours": 4.5,
  "avg_processing_time_seconds": 3.2,
  "by_format": {
    "txt": 350,
    "docx": 100,
    "doc": 30,
    "pdf": 20
  },
  "by_classification": {
    "EX-01": 200,
    "EX-02": 150,
    "EX-03": 100,
    "EX-04": 50
  },
  "by_language": {
    "en": 350,
    "fr": 150
  },
  "sections_extracted_total": 3000,
  "skills_extracted_total": 6000,
  "avg_sections_per_job": 6.0,
  "avg_skills_per_job": 12.0
}
```

#### Example

```bash
# Get overall statistics
curl -X GET "http://localhost:8000/api/ingestion/stats" \
  -H "X-API-Key: your-api-key"

# Get statistics for specific period
curl -X GET "http://localhost:8000/api/ingestion/stats?start_date=2025-10-01T00:00:00Z&end_date=2025-10-18T23:59:59Z" \
  -H "X-API-Key: your-api-key"
```

---

### Validate File

Validate a file without processing it (dry run).

```http
POST /api/ingestion/validate
```

#### Request

**Content-Type**: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | File to validate |

#### Response (200 OK)

```json
{
  "valid": true,
  "file_name": "EX-01_Director_103249.txt",
  "file_size": 12456,
  "file_format": "txt",
  "estimated_processing_time_seconds": 3.5,
  "warnings": [
    "File name suggests classification EX-01 but could not be verified"
  ],
  "preview": {
    "detected_language": "en",
    "detected_classification": "EX-01",
    "detected_job_number": "103249",
    "first_100_chars": "Director, Business Analysis\n\nGENERAL ACCOUNTABILITY\n\nThe Director is responsible for..."
  }
}
```

#### Error Response (400 Bad Request)

```json
{
  "valid": false,
  "file_name": "invalid_file.xlsx",
  "errors": [
    "Unsupported file format: .xlsx",
    "File size exceeds maximum limit of 10 MB"
  ]
}
```

#### Example

```bash
curl -X POST "http://localhost:8000/api/ingestion/validate" \
  -H "X-API-Key: your-api-key" \
  -F "file=@job_description.txt"
```

---

### Reprocess Job

Trigger reprocessing of an existing job (re-extract sections and skills).

```http
POST /api/ingestion/reprocess/{job_id}
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | integer | Yes | Job identifier to reprocess |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `extract_skills` | boolean | No | Re-extract skills (default: true) |
| `overwrite_sections` | boolean | No | Overwrite existing sections (default: false) |

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Job 42 queued for reprocessing",
  "job_id": 42,
  "estimated_completion_time": "2025-10-18T10:35:00Z"
}
```

#### Error Responses

**404 Not Found**:
```json
{
  "detail": "Job with ID 42 not found"
}
```

**409 Conflict** - Job already processing:
```json
{
  "detail": "Job 42 is currently being processed. Cannot queue for reprocessing."
}
```

#### Example

```bash
# Reprocess with defaults
curl -X POST "http://localhost:8000/api/ingestion/reprocess/42" \
  -H "X-API-Key: your-api-key"

# Reprocess without skill extraction
curl -X POST "http://localhost:8000/api/ingestion/reprocess/42?extract_skills=false" \
  -H "X-API-Key: your-api-key"

# Reprocess and overwrite sections
curl -X POST "http://localhost:8000/api/ingestion/reprocess/42?overwrite_sections=true" \
  -H "X-API-Key: your-api-key"
```

---

## File Naming Conventions

The system uses file naming patterns to extract metadata:

### Supported Patterns

1. **Primary Pattern**: `{Classification}_{Title}_{JobNumber}_JD.{ext}`
   - Example: `EX-01_Dir_Business_Analysis_103249_JD.txt`
   - Extracts: Classification=EX-01, JobNumber=103249

2. **Legacy Pattern**: `JD_{Classification}_{JobNumber}_{Title}.{ext}`
   - Example: `JD_EX-01_103249_Director.txt`
   - Extracts: Classification=EX-01, JobNumber=103249

3. **Simple Pattern**: `{JobNumber}_{Title}.{ext}`
   - Example: `103249_Director_Business_Analysis.txt`
   - Extracts: JobNumber=103249

### Best Practices

```bash
# Good file names (metadata extracted automatically)
EX-01_Dir_Business_Analysis_103249_JD.txt
JD_EX-02_104567_Manager_Finance.docx
103249_Director.txt

# Poor file names (manual metadata entry required)
job_description.txt
document1.docx
untitled.pdf
```

---

## Section Detection Patterns

The system recognizes the following standard job description sections:

| Section Type | Detection Keywords |
|-------------|-------------------|
| `general_accountability` | "General Accountability", "Purpose", "Summary" |
| `organization_structure` | "Organization Structure", "Reports To", "Reporting" |
| `nature_and_scope` | "Nature and Scope", "Environment", "Context" |
| `specific_accountabilities` | "Specific Accountabilities", "Key Responsibilities", "Duties" |
| `dimensions` | "Dimensions", "Resources", "Budget", "FTE" |
| `knowledge_skills` | "Knowledge and Skills", "Competencies", "Qualifications", "Education" |

### Custom Section Detection

If sections don't match standard patterns, they are classified as `custom_{index}` and stored for manual review.

---

## Error Handling

### Common Error Scenarios

#### 1. Unsupported File Format

**Request**:
```bash
curl -X POST "http://localhost:8000/api/ingestion/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@spreadsheet.xlsx"
```

**Response (400 Bad Request)**:
```json
{
  "detail": "Unsupported file format: .xlsx. Supported formats: .txt, .doc, .docx, .pdf"
}
```

#### 2. File Too Large

**Request**: Upload 15 MB file

**Response (413 Payload Too Large)**:
```json
{
  "detail": "File size (15728640 bytes) exceeds maximum limit of 10485760 bytes (10 MB)"
}
```

#### 3. Corrupted File

**Request**: Upload corrupted PDF

**Response (422 Unprocessable Entity)**:
```json
{
  "detail": "Failed to extract text from file. File may be corrupted or password-protected."
}
```

#### 4. Missing Required Metadata

**Request**: Upload file with no detectable classification

**Response (200 OK with warnings)**:
```json
{
  "status": "success",
  "job_id": 42,
  "warnings": [
    "Could not detect classification from file name. Defaulted to 'Unknown'",
    "Could not detect job number from file name. Using system-generated ID"
  ]
}
```

---

## Performance Considerations

### File Size Limits

- **Maximum file size**: 10 MB per file
- **Batch upload limit**: 50 files per request
- **Total batch size**: 100 MB maximum

### Processing Time

Average processing times by file size:

| File Size | Avg Processing Time |
|-----------|---------------------|
| < 100 KB | 1-2 seconds |
| 100 KB - 500 KB | 2-4 seconds |
| 500 KB - 1 MB | 4-8 seconds |
| 1 MB - 5 MB | 8-15 seconds |
| 5 MB - 10 MB | 15-30 seconds |

**Note**: Processing time includes text extraction, language detection, section parsing, and skill extraction.

### Rate Limiting

- **Upload endpoint**: 20 requests per minute
- **Batch upload**: 5 requests per minute
- **Status checks**: 100 requests per minute

---

## Best Practices

### 1. Use Consistent File Naming

```bash
# Recommended naming pattern
{Classification}_{Title}_{JobNumber}_JD.{ext}

# Examples
EX-01_Dir_Business_Analysis_103249_JD.txt
EX-02_Manager_Finance_104567_JD.docx
EX-03_Advisor_Policy_105890_JD.txt
```

### 2. Validate Before Uploading

Always validate files before processing to catch issues early:

```bash
# Validate first
VALIDATION=$(curl -X POST "http://localhost:8000/api/ingestion/validate" \
  -H "X-API-Key: your-api-key" \
  -F "file=@job.txt")

# Check if valid
if [[ $(echo $VALIDATION | jq -r '.valid') == "true" ]]; then
  # Upload
  curl -X POST "http://localhost:8000/api/ingestion/upload" \
    -H "X-API-Key: your-api-key" \
    -F "file=@job.txt"
fi
```

### 3. Monitor Processing Status

For long-running batch uploads, poll the status endpoint:

```bash
# Upload and get job ID
RESPONSE=$(curl -X POST "http://localhost:8000/api/ingestion/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@large_job.pdf")

JOB_ID=$(echo $RESPONSE | jq -r '.job_id')

# Poll status until completed
while true; do
  STATUS=$(curl -X GET "http://localhost:8000/api/ingestion/status/$JOB_ID" \
    -H "X-API-Key: your-api-key" | jq -r '.status')

  if [[ "$STATUS" == "completed" || "$STATUS" == "failed" ]]; then
    echo "Processing $STATUS"
    break
  fi

  sleep 2
done
```

### 4. Handle Batch Upload Errors Gracefully

```bash
# Enable continue_on_error for batch uploads
curl -X POST "http://localhost:8000/api/ingestion/batch-upload" \
  -H "X-API-Key: your-api-key" \
  -F "files=@job1.txt" \
  -F "files=@job2.txt" \
  -F "files=@job3.txt" \
  -F "continue_on_error=true"

# Check results and retry failed files individually
```

---

## Integration Examples

### Python Integration

```python
import requests

API_KEY = "your-api-key"  # pragma: allowlist secret
API_URL = "http://localhost:8000/api/ingestion"

def upload_job_description(file_path):
    """Upload a single job description file."""
    with open(file_path, 'rb') as f:
        response = requests.post(
            f"{API_URL}/upload",
            headers={"X-API-Key": API_KEY},
            files={"file": f}
        )

    if response.status_code == 200:
        data = response.json()
        print(f"Success! Job ID: {data['job_id']}")
        return data['job_id']
    else:
        print(f"Error: {response.json()['detail']}")
        return None

def check_processing_status(job_id):
    """Check the processing status of an uploaded job."""
    response = requests.get(
        f"{API_URL}/status/{job_id}",
        headers={"X-API-Key": API_KEY}
    )

    return response.json()

# Usage
job_id = upload_job_description("EX-01_Director_103249.txt")
if job_id:
    status = check_processing_status(job_id)
    print(f"Status: {status['status']}")
    print(f"Sections extracted: {status['sections_extracted']}")
```

### JavaScript Integration

```javascript
const API_KEY = 'your-api-key';  // pragma: allowlist secret
const API_URL = 'http://localhost:8000/api/ingestion';

async function uploadJobDescription(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_URL}/upload`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY
    },
    body: formData
  });

  if (response.ok) {
    const data = await response.json();
    console.log(`Success! Job ID: ${data.job_id}`);
    return data.job_id;
  } else {
    const error = await response.json();
    console.error(`Error: ${error.detail}`);
    return null;
  }
}

async function checkProcessingStatus(jobId) {
  const response = await fetch(`${API_URL}/status/${jobId}`, {
    headers: {
      'X-API-Key': API_KEY
    }
  });

  return await response.json();
}

// Usage with file input
document.getElementById('fileInput').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  const jobId = await uploadJobDescription(file);

  if (jobId) {
    const status = await checkProcessingStatus(jobId);
    console.log(`Status: ${status.status}`);
    console.log(`Sections extracted: ${status.sections_extracted}`);
  }
});
```

---

## Related APIs

- **[Jobs API](jobs-api.md)** - Job description management and CRUD operations
- **[Search API](search-api.md)** - Full-text and semantic search
- **[Translation Memory API](translation_memory_api.md)** - Bilingual translation support

---

## Live API Documentation

For interactive API testing and real-time schema validation, access the Swagger UI when the backend is running:

**Swagger UI**: http://localhost:8000/api/docs

---

**Last Updated**: 2025-10-18
**API Version**: 1.0
**Maintainer**: Backend Team
