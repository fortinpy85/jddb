# Backend Architecture Guide

## 1. Overview

This document provides a high-level overview of the backend architecture for the JDDB. The backend is built using Python and the FastAPI framework, following modern design patterns to ensure scalability, maintainability, and performance.

## 2. Core Technologies

- **Language:** Python 3.9+
- **Framework:** FastAPI
- **Database:** PostgreSQL with pgvector
- **ORM:** SQLAlchemy (Core, not the ORM for flexibility)
- **Async Tasks:** Celery with Redis as the message broker
- **Data Validation:** Pydantic

## 3. Project Structure

The backend codebase is organized into the following key directories:

```
backend/
├── alembic/          # Database migration scripts
├── src/
│   ├── api/          # FastAPI routers (API endpoints)
│   ├── core/         # Core application logic, settings, and configs
│   ├── db/           # Database connection and session management
│   ├── models/       # Pydantic models for data representation
│   ├── services/     # Business logic for specific features
│   └── worker/       # Celery worker and task definitions
├── tests/            # Pytest tests for the application
├── .env              # Environment variables
└── requirements.txt  # Python dependencies
```

## 4. Request Lifecycle

A typical HTTP request flows through the application as follows:

1.  **Uvicorn:** The request is first received by the Uvicorn ASGI server.
2.  **FastAPI:** The request is passed to the FastAPI application.
3.  **Middleware:** The request goes through any configured middleware (e.g., for authentication, logging, CORS).
4.  **Router:** The request is routed to the appropriate API endpoint in the `src/api/` directory based on the URL path.
5.  **Service Layer:** The endpoint function calls a method in a service from the `src/services/` directory to execute the business logic.
6.  **Database Layer:** The service interacts with the database via the session managed in `src/db/`.
7.  **Pydantic Models:** Data is returned to the client, serialized according to the Pydantic models defined in `src/models/`.

## 5. Database Interaction

- **SQLAlchemy Core:** We use SQLAlchemy Core instead of the full ORM. This provides a powerful way to construct SQL queries using Python, while still giving us fine-grained control over the exact SQL being executed. This is particularly important for complex queries involving vector similarity.
- **Alembic Migrations:** The database schema is managed through Alembic. To make changes to the schema, a developer should create a new migration script using the `alembic revision` command.
- **Session Management:** Database sessions are managed using FastAPI's dependency injection system. A new session is created for each request and closed automatically.

## 6. Asynchronous Tasks (Celery)

- **Purpose:** Long-running tasks, such as processing uploaded documents or generating embeddings for a large batch of files, are handled asynchronously by Celery to avoid blocking the main API.
- **Workflow:**
    1.  An API endpoint receives a request (e.g., to process a file).
    2.  The endpoint dispatches a task to the Celery worker via the Redis message broker.
    3.  The API immediately returns a `202 Accepted` response to the client with a task ID.
    4.  The client can then poll a `/tasks/{task_id}` endpoint to check the status of the task.
    5.  The Celery worker, running in a separate process, picks up the task from the queue and executes it.

## 7. Authentication & Authorization

- **Mechanism:** Authentication is handled using JWT (JSON Web Tokens).
- **Flow:**
    1.  A user submits their credentials to a `/login` endpoint.
    2.  If the credentials are valid, the server returns a short-lived JWT access token.
    3.  The client must include this access token in the `Authorization` header for all subsequent requests to protected endpoints.
- **Implementation:** A FastAPI `Depends` function is used to verify the token and extract the current user for each request.
