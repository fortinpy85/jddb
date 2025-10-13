# GEMINI.MD: AI Collaboration Guide

This document provides essential context for AI models interacting with this project. Adhering to these guidelines will ensure consistency and maintain code quality.

## 1. Project Overview & Purpose

*   **Primary Goal:** A full-stack web application for managing and analyzing job descriptions. It features a modern, AI-powered system with a FastAPI backend and a React frontend. The application is designed for government organizations and provides intelligent document processing, semantic search, and collaborative editing capabilities.
*   **Business Domain:** Government Human Resources, specifically job description management and analysis.
*   **Project Status:**
    *   **Phase 1 Completed:** Core infrastructure, document processing, semantic search, and modern frontend.
    *   **Phase 2 Completed:** Real-time collaborative editing, translation concordance, and AI-powered assistance.

## 2. Core Technologies & Stack

*   **Languages:** Python 3.9+, TypeScript
*   **Frameworks & Runtimes:** FastAPI, React, Bun
*   **Databases:** PostgreSQL with the pgvector extension for semantic search.
*   **Key Libraries/Dependencies:**
    *   **Backend:** SQLAlchemy, Alembic, OpenAI, Celery, Redis
    *   **Frontend:** Tailwind CSS, Radix UI, Zustand, Playwright
*   **Package Manager(s):** Poetry for Python, Bun for JavaScript/TypeScript.

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
*   **Frontend Structure (React/TypeScript/Bun):**
    *   The frontend uses a custom Bun-based architecture, not a standard Next.js setup.
    *   **Bun Server:** `src/index.tsx` is the custom server handling API routes and serving the Single Page Application (SPA).
    *   **React Entry:** `src/frontend.tsx` is the root of the React application.
    *   **Build Process:** `build.ts` is a custom build script using Bun's native bundler.
    *   **State Management:** Zustand (`src/lib/store.ts`) is used for global state.
    *   **API Client:** A singleton API client is located at `src/lib/api.ts`.

## 4. Coding Conventions & Style Guide

*   **Formatting:**
    *   **Python:** `black` for code formatting (88-character line length).
    *   **TypeScript:** `prettier` for code formatting (2-space indentation, single quotes).
*   **Naming Conventions:**
    *   Follows standard Python (PEP 8) and TypeScript conventions.
*   **API Design:** RESTful API principles are used.
*   **Error Handling:** Custom error classes and `try...catch` blocks are used.

## 5. Key Files & Entrypoints

*   **Main Entrypoint(s):**
    *   **Backend:** `backend/src/jd_ingestion/api/main.py`
    *   **Frontend:** `src/index.tsx` (Bun server), `src/frontend.tsx` (React app)
*   **Configuration:**
    *   `.env` files for environment variables.
    *   `backend/pyproject.toml`: Backend dependencies and project settings.
    *   `package.json`: Frontend dependencies and scripts.
    *   `tsconfig.json`: TypeScript configuration.
    *   `backend/alembic.ini`: Database migration configuration.
    *   `build.ts`: Custom Bun build script for the frontend.
*   **CI/CD Pipeline:** CI/CD is configured in the `.github/workflows/` directory.

## 6. Development & Testing Workflow

*   **Local Development Environment:**
    *   **Backend:** Run `make server` in the `backend` directory.
    *   **Frontend:** Run `bun dev` in the root directory.
    *   Batch scripts (`server.bat`, `frontend.bat`) are available for Windows users.
*   **Backend Commands (via `make` in `/backend`):**
    *   `make setup`: Full environment setup.
    *   `make server`: Start development server.
    *   `make test`: Run test suite.
    *   `make lint`: Run code linting.
    *   `make format`: Format code.
    *   `make type-check`: Run type checking.
    *   `make db-init`: Initialize the database.
*   **Frontend Commands (via `bun run` in root):**
    *   `bun install`: Install dependencies.
    *   `bun dev`: Start development server.
    *   `bun run build`: Create a production build.
    *   `bun test`: Run unit tests.
    *   `bun run test:e2e`: Run end-to-end tests with Playwright.
    *   `bun run lint`: Run ESLint.
    *   `bun run type-check`: Run TypeScript type checker.

## 7. Specific Instructions for AI Collaboration

*   **Contribution Guidelines:** All contributions should follow the guidelines in [CONTRIBUTING.md](CONTRIBUTING.md). This includes branch strategy, commit conventions (Conventional Commits), and pull request processes.
*   **Security:** Be mindful of security. Do not hardcode secrets or keys.
*   **Dependencies:**
    *   Use `poetry` to manage Python dependencies in the `backend` directory.
    *   Use `bun` to manage JavaScript/TypeScript dependencies in the root directory.
*   **Commit Messages:** Follow the Conventional Commits specification (e.g., `feat:`, `fix:`, `docs:`).

## 8. Troubleshooting

*   **Application Won't Load:**
    1.  Ensure `.env.local` exists with the correct API URL.
    2.  Verify both frontend (`localhost:3000`) and backend (`localhost:8000`) servers are running.
    3.  Check the browser console for errors.
*   **Backend API Errors:**
    1.  Verify the PostgreSQL database is running.
    2.  Check the `backend/.env` file for correct database credentials.
    3.  Run `make db-init` if database tables do not exist.
*   **Testing Issues:**
    *   **Unit Tests:** Run `bun test`. Test files are in the `src/` directory.
    *   **E2E Tests:** Run `bun run test:e2e`. Test files are in the `tests/` directory.
    *   **Backend Tests:** Run `cd backend && make test`.

## 9. Quick Reference: Package Manager Commands

### Poetry (Backend)
*   `cd backend`
*   `poetry install`: Initial setup.
*   `poetry add <package>`: Add a new dependency.
*   `poetry run <command>`: Run a command in the virtual environment.

### Bun (Frontend)
*   `bun install`: Initial setup.
*   `bun add <package>`: Add a new dependency.
*   `bun run <script>`: Run a script from `package.json`.