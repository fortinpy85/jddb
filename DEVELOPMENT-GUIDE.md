# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

- Always use context7 when I need code generation, setup or configuration steps, or library/API documentation.
- This means you should automatically use the Context7 MCP tools to resolve library id and get library docs without me having to explicitly ask.

### Backend (Python/FastAPI with Poetry)

**Package Management**: Uses Poetry for dependency management and virtual environment isolation.

- `cd backend && make setup` - Full environment setup (install deps via Poetry, init DB, create samples)
- `cd backend && make server` - Start development server (http://localhost:8000)
- `cd backend && make test` - Run test suite with pytest via Poetry
- `cd backend && make lint` - Run code linting with ruff via Poetry
- `cd backend && make format` - Format code with black via Poetry
- `cd backend && make type-check` - Run type checking with mypy via Poetry
- `cd backend && make db-init` - Initialize database and create tables
- `cd backend && make sample-data` - Create sample data for testing

**Direct Poetry Commands** (alternative to Makefile):
- `cd backend && poetry install` - Install dependencies and create virtual environment
- `cd backend && poetry run python -m pytest tests/` - Run tests directly
- `cd backend && poetry run uvicorn jd_ingestion.api.main:app --reload` - Start server directly
- `cd backend && poetry shell` - Activate virtual environment for development

### Frontend (React/TypeScript with Vite)

**Build Tool**: Uses Vite for fast development and optimized production builds.
**Package Management**: Uses npm for dependency management (Bun had bundler issues with closures).

- `npm install` - Install dependencies
- `npm run dev` - Start Vite development server (http://localhost:3006, auto-increments if port busy)
- `npm run build` - Production build using Vite
- `npm run start` - Preview production build (http://localhost:3002)
- `npm test` - Run unit tests with Vitest
- `npm run test:unit` - Run unit tests explicitly
- `npm run test:unit:watch` - Run unit tests in watch mode
- `npm run test:unit:coverage` - Run unit tests with coverage
- `npm run test:e2e` - Run end-to-end tests with Playwright
- `npm run test:e2e:headed` - Run e2e tests in headed mode (visible browser)
- `npm run test:all` - Run both unit and e2e tests sequentially
- `npm run lint` - Run ESLint for code quality
- `npm run type-check` - TypeScript type checking

**API Documentation**: Available at http://localhost:8000/api/docs when backend is running

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

### Frontend Structure (React/TypeScript/Vite)

The frontend uses **Vite** as the build tool and development server:

#### **Architecture Components**
- **Vite Entry Point**: `src/main.tsx` - Imports CSS and initializes React app
- **React Entry**: `src/frontend.tsx` - React app initialization and root rendering
- **HTML Template**: `index.html` - Root HTML file (at project root, required by Vite)
- **Build Config**: `vite.config.ts` - Vite configuration with React plugin and Tailwind PostCSS

#### **Application Structure**
- **Main App**: `src/app/page.tsx` - Dashboard with tabs for jobs, upload, search
- **API Client**: `src/lib/api.ts` - TypeScript client with singleton pattern for all API calls
- **State Management**: `src/lib/store.ts` - Zustand for global state
- **Components**: UI components using Radix UI and Tailwind CSS
- **Configuration**: `src/lib/constants.ts` - Centralized type-safe constants
- **Styles**: `src/index.css` - Tailwind directives and custom CSS (must be imported in main.tsx)

#### **Development vs Production Flow**
- **Development**: `npm run dev` → Vite dev server with HMR (Hot Module Replacement)
- **Production**: `npm run build` → Optimized static build → `npm run start` → Preview server
- **Testing**: Vitest for unit tests + Playwright for E2E tests

#### **Why Vite Over Bun Bundler?**
- **Stability**: Bun v1.2.23 bundler has critical closure bugs that break React components
- **Reliability**: Vite is production-proven with mature ecosystem and extensive plugin support
- **Performance**: Fast HMR, optimized builds, and excellent development experience
- **Community**: Large community, extensive documentation, and established best practices

#### **Migration from Bun Bundler (October 2025)**
- **Issue**: Bun bundler broke JavaScript closures in React components
- **Solution**: Migrated to Vite while keeping npm for package management
- **Files Archived**: `archive/build.bun.ts`, `archive/index.bun.tsx`
- **Critical Fix**: Added `import "./index.css"` to `src/main.tsx` for Tailwind CSS loading

### Database Schema (PostgreSQL + pgvector)

- `job_descriptions` - Core job data with full-text search
- `job_sections` - Parsed content sections (accountability, structure, etc.)
- `content_chunks` - AI-ready text chunks for RAG applications
- `job_metadata` - Structured fields (reports_to, department, budget)
- `ai_usage_tracking` - OpenAI API cost monitoring

## Key Configuration Files

### Backend Configuration (Poetry)

- `backend/pyproject.toml` - **Poetry configuration**: Python dependencies, build settings, tool configurations
- `backend/poetry.lock` - **Poetry lock file**: Exact dependency versions (commit to version control)
- `backend/.env` - Database URL, OpenAI API key, data directory path
- `backend/src/jd_ingestion/config/settings.py` - Pydantic settings with environment variable loading
- `backend/alembic/` - Database migrations managed via Poetry virtual environment

### Frontend Configuration (npm + Vite)

- `package.json` - **npm dependencies**: Frontend packages and scripts
- `package-lock.json` - **npm lock file**: Exact dependency versions (commit to version control)
- `.env.local` - `NEXT_PUBLIC_API_URL=http://localhost:8000/api`
- `tsconfig.json` - TypeScript configuration with `@/*` path mapping
- `components.json` - Radix UI components configuration
- `vite.config.ts` - **Vite configuration**: React plugin, PostCSS, Tailwind CSS integration

## File Processing Pipeline

The system processes government job description files with these patterns:

- Primary: `"EX-01 Dir, Business Analysis 103249 - JD.txt"`
- Legacy: `"JD_EX-01_123456_Director.txt"`
- Supports .txt, .doc, .docx, .pdf files
- Extracts sections: General Accountability, Organization Structure, Nature and Scope, Specific Accountabilities, Dimensions, Knowledge/Skills
- Bilingual support (English/French) with automatic language detection

## Development Workflow

### Package Manager Usage

**Backend (Poetry)**:
- Poetry manages Python dependencies and virtual environments
- All backend commands should use `poetry run` prefix or activate the Poetry shell first
- Dependencies defined in `backend/pyproject.toml` and locked in `backend/poetry.lock`
- Use `cd backend && poetry install` for initial setup or after dependency changes

**Frontend (npm + Vite)**:
- npm manages JavaScript/TypeScript dependencies
- Vite provides fast development server with Hot Module Replacement (HMR)
- Dependencies defined in `package.json` and locked in `package-lock.json`
- Use `npm install` for initial setup or after dependency changes

### Development Steps

1. **Backend Development**:
   - Use `cd backend && make server` (preferred) or `poetry run uvicorn jd_ingestion.api.main:app --reload`
   - API documentation automatically available at http://localhost:8000/api/docs
   - Hot reloading enabled for code changes

2. **Frontend Development**:
   - Use `npm run dev` for Vite development server with hot reloading
   - Automatically connects to backend API at http://localhost:8000/api
   - Fast HMR and optimized development experience with Vite

3. **Database Changes**:
   - Create Alembic migrations: `cd backend && poetry run alembic revision --autogenerate -m "description"`
   - Apply migrations: `cd backend && make db-migrate` or `poetry run alembic upgrade head`

4. **Testing**:
   - Backend: `cd backend && make test` (preferred) or `poetry run pytest tests/`
   - Frontend Unit Tests: `npm test` or `npm run test:unit` (Vitest with JSDOM)
   - Frontend E2E Tests: `npm run test:e2e` (browser-based with Playwright)
   - Run All Tests: `npm run test:all` (unit tests followed by e2e tests)

5. **Code Quality**:
   - Backend: `cd backend && make check` (format, lint, type-check) via Poetry
   - Frontend: `npm run lint` and `npm run type-check` for code quality

## Project Documentation

### Task Management
- **Active Tasks**: [`todo.md`](../todo.md) - Current development priorities and pending tasks
- **Completed Tasks**: [`completed.md`](../completed.md) - Historical record of all completed implementation tasks
- **Architecture**: This file contains development commands and system architecture overview

### Project Status
- **Phase 1**: ✅ Complete - Core infrastructure, testing, and GitHub repository publication
- **Phase 2**: ✅ Complete - Collaborative editing, translation memory, and real-time features implemented
- **Current Status**: Production-ready system with comprehensive test suite and CI/CD pipeline

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

### ✅ Resolved Issues (September 2025)

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

#### Test Framework Migration to Vitest

- **Previous Issue**: Bun test runner had conflicts with Playwright tests
- **Solution**: Migrated to Vitest for unit tests, kept Playwright for E2E
  - Unit tests: `src/` directory using Vitest with JSDOM environment
  - E2E tests: `tests/` directory using Playwright with browser automation
  - Commands: `npm test` runs unit tests, `npm run test:e2e` runs Playwright tests
- **Files**: `package.json`, `vite.config.ts`, `src/test-setup.ts`
- **Result**: Stable test infrastructure with full Vite ecosystem integration

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

### Testing Issues

#### Unit Test Failures
1. Run `npm test` or `npm run test:unit` for fast unit tests with Vitest
2. Check that `.env.local` exists with `NEXT_PUBLIC_API_URL=http://localhost:8000/api`
3. Ensure test files are in `src/` directory with `.test.ts` or `.test.tsx` extensions

#### E2E Test Issues
1. Use `npm run test:e2e` to run Playwright tests
2. Ensure backend server is running on port 8000
3. Playwright will automatically start frontend server on port 3000
4. For debugging: `npm run test:e2e:headed` to see browser actions

#### Backend Test Discovery
1. Run `cd backend && make test` to execute all backend tests
2. Tests are located in `backend/tests/` directory
3. If "no tests ran" error occurs, verify pytest is using correct test directory

## Quick Reference: Package Manager Commands

### When to Use Poetry (Backend)
```bash
cd backend

# Initial setup
poetry install

# Add new dependency
poetry add package-name
poetry add --group dev package-name  # Development dependency

# Run commands in Poetry environment
poetry run python script.py
poetry run pytest tests/
poetry run uvicorn jd_ingestion.api.main:app --reload

# Or activate shell and run commands directly
poetry shell
python script.py
pytest tests/
```

### When to Use npm (Frontend)
```bash
# In root directory (where package.json is located)

# Initial setup
npm install

# Add new dependency
npm install package-name
npm install --save-dev package-name  # Development dependency

# Run scripts
npm run dev                # Vite development server
npm test                   # Unit tests with Vitest
npm run test:unit          # Unit tests explicitly
npm run test:unit:watch    # Unit tests in watch mode
npm run test:e2e           # E2E tests with Playwright
npm run test:all           # All tests (unit + e2e)
npm run build              # Production build with Vite
npm run lint               # ESLint

# Preview production build
npm run start
```

### Key Differences
- **Poetry**: Python-specific, creates isolated virtual environments for backend
- **npm + Vite**: Standard JavaScript package manager with fast, modern build tool
- **Lock Files**: Both `poetry.lock` and `package-lock.json` should be committed to version control
