# Job Description Ingestion Engine

A comprehensive system for processing government job description files into a structured database optimized for AI applications.

## Overview

This engine processes 282+ government job description files (English and French) and transforms them into a searchable database with semantic capabilities. It extracts structured information, generates embeddings for similarity search, and provides a REST API for AI-powered analysis.

## Features

- **File Discovery**: Automatic scanning and metadata extraction from job description files
- **Content Processing**: Intelligent section parsing and structured field extraction
- **Bilingual Support**: Handles both English (JD) and French (DE) job descriptions
- **Database Storage**: PostgreSQL with pgvector for similarity search
- **REST API**: FastAPI-based endpoints for ingestion and search
- **Semantic Search**: Vector embeddings for finding similar positions
- **Quality Assurance**: Comprehensive validation and error handling

## Quick Start

For setup and installation instructions, please refer to the main [Setup Guide](../../docs/SETUP.md).

To start the server, run:

```bash
poetry run python scripts/dev_server.py
```

## API

- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health
- **API Root**: http://localhost:8000/api

## Development

### Running Tests

```bash
poetry run pytest src/jd_ingestion/tests/
```

### Code Quality

```bash
# Format code
poetry run black src/

# Type checking
poetry run mypy src/

# Linting
poetry run flake8 src/
```

### Database Migrations

```bash
# Create migration
poetry run alembic revision --autogenerate -m "Description"

# Apply migration
poetry run alembic upgrade head
```
