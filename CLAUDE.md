# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (Python/FastAPI)

- `cd backend && make setup` - Full environment setup (install deps, init DB, create samples)
- `cd backend && make server` - Start development server (http://localhost:8000)
- `cd backend && make test` - Run test suite
- `cd backend && make lint` - Run code linting
- `cd backend && make format` - Format code with black
- `cd backend && make type-check` - Run type checking with mypy
- `cd backend && make db-init` - Initialize database and create tables
- `cd backend && make sample-data` - Create sample data for testing

### Frontend (React/Bun)

- `bun dev` - Start development server (http://localhost:3000)
- `bun run build` - Production build using custom build.ts script
- API documentation at http://localhost:8000/api/docs

### Windows Batch Scripts (Root Directory)

- `server.bat` - Start backend API server (root directory)
- `frontend.bat` - Start frontend application (root directory)
- `scripts/setup-windows.bat` - Install dependencies
- `scripts/init-db.bat` - Initialize database

## Architecture Overview

### Backend Structure (FastAPI/Python)

- **API Endpoints**: `backend/src/jd_ingestion/api/endpoints/`
  - `jobs.py` - Job management and retrieval
  - `ingestion.py` - File processing and upload
  - `search.py` - Search functionality
- **Core Processing**: `backend/src/jd_ingestion/core/` - File discovery and processing logic
- **Database Models**: `backend/src/jd_ingestion/database/` - SQLAlchemy models and connections
- **Configuration**: `backend/src/jd_ingestion/config/settings.py` - Environment-based settings using Pydantic

### Frontend Structure (React/TypeScript/Bun)

- **Main App**: `src/app/page.tsx` - Dashboard with tabs for jobs, upload, search
- **API Client**: `src/lib/api.ts` - TypeScript client with singleton pattern for all API calls
- **State Management**: `src/lib/store.ts` - Zustand for global state
- **Components**: UI components using Radix UI and Tailwind CSS
- **Build System**: Custom `build.ts` script with Bun and Tailwind plugin

### Database Schema (PostgreSQL + pgvector)

- `job_descriptions` - Core job data with full-text search
- `job_sections` - Parsed content sections (accountability, structure, etc.)
- `content_chunks` - AI-ready text chunks for RAG applications
- `job_metadata` - Structured fields (reports_to, department, budget)
- `ai_usage_tracking` - OpenAI API cost monitoring

## Key Configuration Files

### Backend Configuration

- `backend/.env` - Database URL, OpenAI API key, data directory path
- `backend/src/jd_ingestion/config/settings.py` - Pydantic settings with environment variable loading
- `backend/alembic/` - Database migrations

### Frontend Configuration

- `.env.local` - `NEXT_PUBLIC_API_URL=http://localhost:8000/api`
- `tsconfig.json` - TypeScript configuration with `@/*` path mapping
- `components.json` - Radix UI components configuration

## File Processing Pipeline

The system processes government job description files with these patterns:

- Primary: `"EX-01 Dir, Business Analysis 103249 - JD.txt"`
- Legacy: `"JD_EX-01_123456_Director.txt"`
- Supports .txt, .doc, .docx, .pdf files
- Extracts sections: General Accountability, Organization Structure, Nature and Scope, Specific Accountabilities, Dimensions, Knowledge/Skills
- Bilingual support (English/French) with automatic language detection

## Development Workflow

1. **Backend Development**: Use `make server` for hot reloading, API docs at /api/docs
2. **Frontend Development**: Use `bun dev`, connects to backend API automatically
3. **Database Changes**: Create Alembic migrations, run `make db-migrate`
4. **Testing**: Backend has pytest setup, run `make test`
5. **Code Quality**: Use `make check` (format, lint, type-check) before commits

## Data Flow

1. **File Upload** → Frontend drag-and-drop → API `/ingestion/upload` → File processing
2. **Job Listing** → API `/jobs` → Frontend JobList component with filtering
3. **Search** → API `/search/` → Full-text search with faceted filtering
4. **Job Details** → API `/jobs/{id}` → Detailed view with sections and metadata

## API Client Pattern

The frontend uses a singleton API client (`src/lib/api.ts`) with:

- Type-safe methods matching backend endpoints
- Enhanced error handling with retry logic and timeout management
- Exponential backoff for failed requests
- Automatic JSON serialization/deserialization
- Environment validation and fallback configuration
- Connection testing and configuration validation methods

## Known Issues & Solutions

### ✅ Resolved Issues (November 2025)

#### Frontend Loading Issues

- **Issue**: Missing environment configuration and icon imports causing application crashes
- **Solution**: Added `.env.local` with `NEXT_PUBLIC_API_URL` and imported all missing Lucide React icons
- **Files**: `.env.local`, `src/app/page.tsx`, `src/components/JobList.tsx`

#### Backend API Route Conflicts

- **Issue**: FastAPI route ordering causing 422 errors on `/api/jobs/status` endpoint
- **Solution**: Moved `/status` route before `/{job_id}` parameter route in `jobs.py`
- **Files**: `backend/src/jd_ingestion/api/endpoints/jobs.py:76`

#### SQLAlchemy Relationship Mapping

- **Issue**: Mapper initialization failure: "JobDescription has no property 'metadata'"
- **Solution**: Fixed join statement to use proper relationship: `base_query.join(JobDescription.job_metadata)`
- **Files**: `backend/src/jd_ingestion/api/endpoints/jobs.py:35`

### Development Environment Setup

#### Required Environment Files

- **Frontend**: `.env.local` must contain `NEXT_PUBLIC_API_URL=http://localhost:8000/api`
- **Backend**: `.env` with database credentials and API keys (already present)

#### Process Environment Handling

- **Browser Environment**: API client handles `process` undefined in browser contexts
- **Fallback Configuration**: Graceful fallbacks for missing environment variables

### Error Handling & Reliability

#### API Client Enhancements

- **Retry Logic**: Automatic retries with exponential backoff for server errors (5xx) and network issues
- **Timeout Management**: Configurable timeouts with AbortController for request cancellation
- **Error Classification**: Distinguishes between retryable and non-retryable errors
- **Configuration Validation**: Environment validation and connection testing methods

#### FormData Upload Handling

- **File Uploads**: Proper Content-Type handling for multipart/form-data requests
- **Boundary Generation**: Let browser set Content-Type with proper boundary for FormData

## Troubleshooting Guide

### Application Won't Load

1. Check `.env.local` exists with correct API URL
2. Verify both frontend (port 3000) and backend (port 8000) servers are running
3. Check browser console for missing import errors

### Backend API Errors

1. Verify PostgreSQL database is running and accessible
2. Check `.env` file has correct database credentials
3. Run `make db-init` if database tables don't exist
4. Check server logs for SQLAlchemy relationship mapping errors

### Connection Issues

1. Use API client's `testConnection()` method to verify backend connectivity
2. Check `validateConfiguration()` for environment setup issues
3. Verify CORS settings allow frontend domain in `main.py`
