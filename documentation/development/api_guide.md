# API Guide: JDDB

## 1. Overview

This document provides a guide for developers using the JDDB backend API. It covers authentication, error handling, and provides an overview of the key API endpoints. For a complete, interactive list of all endpoints, please refer to the auto-generated Swagger documentation.

**Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs) (when running locally)

---

## 2. Authentication

- **Mechanism:** The API uses JWT (JSON Web Tokens) for authentication.
- **Flow:**
    1.  Obtain an access token by sending a `POST` request to the `/api/auth/login` endpoint with a username and password.
    2.  The server will respond with a JSON object containing an `access_token`.
    3.  For all subsequent requests to protected endpoints, you must include an `Authorization` header with the value `Bearer {your_access_token}`.

**Example Login Request:**
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=testuser&password=testpassword"
```

---

## 3. Error Handling

The API uses standard HTTP status codes to indicate the success or failure of a request.

- **`2xx` Success:**
    - `200 OK`: The request was successful.
    - `201 Created`: A new resource was successfully created.
    - `202 Accepted`: The request was accepted for processing (used for long-running async tasks).
- **`4xx` Client Errors:**
    - `400 Bad Request`: The request was malformed (e.g., invalid JSON).
    - `401 Unauthorized`: The request is missing a valid authentication token.
    - `403 Forbidden`: The authenticated user does not have permission to perform the action.
    - `404 Not Found`: The requested resource does not exist.
    - `422 Unprocessable Entity`: The request body is syntactically correct, but semantically invalid (e.g., a required field is missing). The response body will contain detailed information about the validation errors.
- **`5xx` Server Errors:**
    - `500 Internal Server Error`: An unexpected error occurred on the server.

**Error Response Body:**
When an error occurs, the API will return a JSON object with a `detail` key containing a description of the error.

```json
{
    "detail": "The requested job description was not found."
}
```

---

## 4. Key Endpoints

This is not an exhaustive list. Please see the Swagger UI for all available endpoints and their parameters.

### Job Descriptions (`/api/jobs`)

- **`GET /api/jobs`**: Retrieves a paginated list of all job descriptions.
- **`GET /api/jobs/{job_id}`**: Retrieves the details of a single job description.

### Search (`/api/search`)

- **`GET /api/search`**: Performs a search.
    - **`query` (param):** Performs a keyword search.
    - **`semantic_query` (param):** Performs a semantic vector search.
    - **`classification` (param):** Filters by job classification.

### Analysis (`/api/analysis`)

- **`GET /api/analysis/compare/{job_a_id}/{job_b_id}`**: Performs a detailed comparison of two job descriptions, including semantic similarity scores.

### Upload (`/api/upload`)

- **`POST /api/upload/files`**: Uploads one or more job description files. This is a `multipart/form-data` endpoint. It returns a task ID for a long-running background job.

### Tasks (`/api/tasks`)

- **`GET /api/tasks/{task_id}`**: Retrieves the status of a background task (e.g., a file processing job).

---

## 5. Real-time API (WebSockets)

- **Endpoint:** `ws://localhost:8000/ws/editor/{document_id}`
- **Purpose:** The WebSocket endpoint is used for the real-time collaborative editor in Phase 2.
- **Protocol:** See the `real_time_collaboration_guide.md` for details on the messaging protocol used over the WebSocket connection.

```
