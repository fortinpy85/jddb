# Job Description Database (JDDB) Documentation

This document provides a comprehensive overview of the JDDB project, its architecture, and development practices.

## 1. Project Overview & Purpose

*   **Primary Goal:** A full-stack web application for managing and analyzing job descriptions. It features a modern, AI-powered system with a FastAPI backend and a React frontend. The application is designed for government organizations and provides intelligent document processing, semantic search, and collaborative editing capabilities.
*   **Business Domain:** Government Human Resources, specifically job description management and analysis.
*   **Project Status:**
    *   **Phase 1 Completed:** Core infrastructure, document processing, semantic search, and modern frontend.
    *   **Phase 2 Completed:** Real-time collaborative editing, translation concordance, and AI-powered assistance.

## 2. Core Technologies & Stack

*   **Languages:** Python 3.9+, TypeScript
*   **Frameworks & Runtimes:** FastAPI, React, Vite
*   **Databases:** PostgreSQL with the pgvector extension for semantic search.
*   **Key Libraries/Dependencies:**
    *   **Backend:** SQLAlchemy, Alembic, OpenAI, Celery, Redis
    *   **Frontend:** Tailwind CSS, Radix UI, Zustand, Playwright
*   **Package Manager(s):** Poetry for Python, npm for JavaScript/TypeScript.

## 3. Architectural Patterns

*   **Overall Architecture:** Monorepo containing a separate backend and frontend application.
*   **Directory Structure Philosophy:**
    *   `/backend`: Contains the Python-based FastAPI application.
    *   `/src`: Contains the React-based frontend application.
    *   `/data`: Contains raw and processed data.
    *   `/docs`: Contains project documentation.
    *   `/tests`: Contains end-to-end tests (Playwright).
*   **Backend Structure (FastAPI/Python):**
    *   `backend/src/jd_ingestion/api/endpoints/`: API Endpoints
    *   `backend/src/jd_ingestion/core/`: Core business logic.
    *   `backend/src/jd_ingestion/database/`: SQLAlchemy models and database connection.
    *   `backend/src/jd_ingestion/config/settings.py`: Pydantic settings for environment management.
*   **Frontend Structure (React/TypeScript/Vite):**
    *   The frontend uses a custom Bun-based architecture, not a standard Next.js setup.
    *   **State Management:** Zustand (`src/lib/store.ts`) is used for global state.
    *   **API Client:** A singleton API client is located at `src/lib/api.ts`.

## 4. API Documentation

For detailed API documentation, please see the [API documentation](api/README.md) directory.

## 5. User Stories

For user stories, please see the [User Stories](user_stories.md) file.

## 6. Development & Testing Workflow

*   **Local Development Environment:**
    *   **Backend:** Run `make server` in the `backend` directory.
    *   **Frontend:** Run `npm run dev` in the root directory.
    *   Batch scripts (`server.bat`, `frontend.bat`) are available for Windows users.
*   **Backend Commands (via `make` in `/backend`):**
    *   `make setup`: Full environment setup.
    *   `make server`: Start development server.
    *   `make test`: Run test suite.
    *   `make lint`: Run code linting.
    *   `make format`: Format code.
    *   `make type-check`: Run type checking.
    *   `make db-init`: Initialize the database.
*   **Frontend Commands (via `npm` in root):**
    *   `npm install`: Install dependencies.
    *   `npm run dev`: Start development server.
    *   `npm run build`: Create a production build.
    *   `npm test`: Run unit tests.
    *   `npm run test:e2e`: Run end-to-end tests with Playwright.
    *   `npm run lint`: Run ESLint.
    *   `npm run type-check`: Run TypeScript type checker.

## 7. Contribution Guidelines

All contributions should follow the guidelines in [CONTRIBUTING.md](CONTRIBUTING.md). This includes branch strategy, commit conventions (Conventional Commits), and pull request processes.

## 8. Troubleshooting

*   **Application Won't Load:**
    1.  Ensure `.env.local` exists with the correct API URL.
    2.  Verify both frontend (`localhost:3000`) and backend (`localhost:8000`) servers are running.
    3.  Check the browser console for errors.
*   **Backend API Errors:**
    1.  Verify the PostgreSQL database is running.
    2.  Check the `backend/.env` file for correct database credentials.
    3.  Run `make db-init` if a database table does not exist.
