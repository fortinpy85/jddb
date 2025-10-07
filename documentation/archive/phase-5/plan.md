# Phase 5 Plan: Lightcast Integration & Skill Intelligence

**Goal:** Enrich the application with external labor market data by integrating the Lightcast API. This phase will introduce automated skill extraction, title standardization, and a strategic skills dashboard.

**Status:** This plan is a formal adoption of the `lightcast_integration_plan.md` document.

---

### 1. Foundational Setup

*   **Action:** Acquire Lightcast API credentials and configure them securely in the backend environment (`.env` and `settings.py`).
*   **Action:** Develop a dedicated backend service, `LightcastClient`, in `backend/src/jd_ingestion/services/` to manage all API authentication and requests.

### 2. Backend Implementation

*   **Action:** Update the database schema to support skills.
    *   **Details:** Create a `Skill` table and a `job_description_skills` many-to-many association table. Generate and apply the Alembic migration.
*   **Action:** Integrate skill extraction into the job upload workflow.
    *   **Details:** On file upload, call the Lightcast API to extract skills and populate the new database tables.
*   **Action:** Create API endpoints for title standardization (`POST /jobs/suggest-title`).
*   **Action:** Create analytics endpoints to serve aggregated skill data for the dashboard (e.g., `GET /analytics/skills/inventory`, `GET /analytics/skills/top`).

### 3. Frontend Implementation

*   **Action:** Display extracted skills as filterable tags on the job detail page.
*   **Action:** Implement the UI for the "Suggest Title" feature in the job editing interface.
*   **Action:** Build a new "Skills Dashboard" page using a charting library to visualize data from the new analytics endpoints.

### 4. Verification

*   **Action:** Write comprehensive backend unit tests (mocking the Lightcast API) and frontend E2E tests (verifying that skills appear and the dashboard renders).

---

**Milestone / Definition of Done:**
*   The application can successfully extract skills from an uploaded job description and display them to the user.
*   The "Skills Dashboard" is functional and displays analytics based on the extracted skills.
*   Users can receive and apply standardized job title suggestions.
