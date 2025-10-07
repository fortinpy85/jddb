Of course. I have reviewed the additional API offerings and the broader Lightcast site. Here is a comprehensive action plan to integrate Lightcast into our application, focusing on your three priority areas.

This plan is structured in phases, starting with foundational backend work and moving to frontend implementation and testing.

### **Phase 0: Foundational Setup & Configuration**

This phase is critical for enabling any interaction with the Lightcast API.

*   **Action 0.1: API Key Acquisition & Scoping**
    *   **Task:** Contact Lightcast to procure an API key. Determine the scope of the subscription to ensure it includes access to the "Skills API" (for extraction and attributes), and the "Job Titles API" (for standardization).
    *   **Owner:** Project Lead / Business Development.

*   **Action 0.2: Secure Environment Configuration**
    *   **Task:** Add `LIGHTCAST_API_KEY` and `LIGHTCAST_CLIENT_ID` to the backend environment configuration.
    *   **Implementation:**
        1.  Add `LIGHTCAST_API_KEY` and `LIGHTCAST_CLIENT_ID` to `backend/.env.example`.
        2.  Update the Pydantic `Settings` model in `backend/src/jd_ingestion/config/settings.py` to load these new variables.
    *   **Rationale:** This securely manages credentials according to existing project conventions.

*   **Action 0.3: Create a Dedicated Backend API Client**
    *   **Task:** Develop a service module to handle all communication with the Lightcast API.
    *   **Implementation:**
        1.  Create a new file: `backend/src/jd_ingestion/services/lightcast_client.py`.
        2.  Implement a `LightcastClient` class within this file. It will handle authentication (obtaining an access token) and contain methods for each specific Lightcast API we will use (e.g., `extract_skills`, `standardize_title`).
    *   **Rationale:** Centralizes API interaction, making it reusable, testable, and easier to maintain.

---

### **Phase 1: Backend Feature Implementation**

This phase focuses on integrating the core logic for the three priority features into our FastAPI backend.

#### **Feature 1: Skills Extraction and Tagging**

*   **Action 1.1: Update Database Models**
    *   **Task:** Create database tables to store the standardized skills and link them to job descriptions.
    *   **Implementation:**
        1.  In `backend/src/jd_ingestion/database/models.py`, define a new `Skill` table with columns like `id`, `lightcast_id`, `name`, and `type` (e.g., common, specialized).
        2.  Create a many-to-many association table (`job_description_skills`) to link `JobDescription` and `Skill`.
        3.  Run `alembic revision --autogenerate` and `alembic upgrade head` to apply the schema changes.
    *   **Rationale:** Persists the structured skill data returned by Lightcast.

*   **Action 1.2: Integrate Skill Extraction into Job Upload**
    *   **Task:** Modify the job upload process to automatically extract and save skills.
    *   **Implementation:**
        1.  In the API endpoint for document uploads (e.g., in `backend/src/jd_ingestion/api/endpoints/jobs.py`), after parsing the text from the uploaded file, call the `lightcast_client.extract_skills()` method.
        2.  Process the response from Lightcast: for each skill returned, either find it in our `Skill` table or create a new entry.
        3.  Populate the `job_description_skills` association table to link the extracted skills with the newly created `JobDescription`.
    *   **Rationale:** Enriches job descriptions with standardized skill data upon creation.

*   **Action 1.3: Expose Skills via API**
    *   **Task:** Ensure the frontend can retrieve the skills for a given job.
    *   **Implementation:** Modify the response model for the `GET /jobs/{job_id}` endpoint to include a list of associated skills.
    *   **Rationale:** Provides the necessary data for the frontend to display.

#### **Feature 2: Job Title Standardization**

*   **Action 2.1: Create a Title Standardization Endpoint**
    *   **Task:** Develop a new API endpoint that provides standardized title suggestions.
    *   **Implementation:**
        1.  Add a `standardize_title()` method to the `LightcastClient` service. This method will call the Lightcast "Job Titles API" with the text of a job description.
        2.  Create a new endpoint, `POST /jobs/suggest-title`, that accepts a job description ID.
        3.  This endpoint will fetch the job description text, call the `lightcast_client.standardize_title()` method, and return a list of suggested, standardized job titles from the Lightcast API.
    *   **Rationale:** Provides an interactive way for users to normalize job titles based on the description's content.

#### **Feature 3: Skills Inventory & Dashboard**

*   **Action 3.1: Create Analytics Endpoints**
    *   **Task:** Develop backend endpoints to provide aggregated skill data for the dashboard.
    *   **Implementation:** Create a new API router, e.g., `backend/src/jd_ingestion/api/endpoints/analytics.py`, with the following endpoints:
        *   `GET /analytics/skills/inventory`: Returns a list of all unique skills present in the database, with counts of how many job descriptions feature each skill.
        *   `GET /analytics/skills/top?limit=10`: Returns the top N most frequent skills.
        *   `GET /analytics/skills/trends`: (Future enhancement) Could be designed to show skill growth over time by analyzing job creation dates.
    *   **Rationale:** Aggregates the stored skill data to power the frontend dashboard visualizations.

---

### **Phase 2: Frontend Implementation**

This phase focuses on building the user-facing components in our React application.

*   **Action 2.1: Display Extracted Skills**
    *   **Task:** Show the extracted skills on the job detail page.
    *   **Implementation:**
        1.  In the component responsible for displaying job details, fetch the job data (which now includes the skills list).
        2.  Create a new component, perhaps named `SkillTag`, to display each skill.
        3.  Render a list of these `SkillTag` components in a dedicated "Skills" section on the page.
    *   **Rationale:** Makes the enriched data visible and useful to the end-user.

*   **Action 2.2: Implement Title Standardization UI**
    *   **Task:** Add a feature to the UI to allow users to standardize a job title.
    *   **Implementation:**
        1.  In the job editing interface, add a "Suggest Title" button next to the job title input field.
        2.  On click, call the `POST /jobs/suggest-title` backend endpoint.
        3.  Display the returned suggestions in a dropdown or modal, allowing the user to select one to replace the current title.
    *   **Rationale:** Provides a seamless workflow for users to improve data quality.

*   **Action 2.3: Build the Skills Dashboard**
    *   **Task:** Create a new page or tab for skills analytics.
    *   **Implementation:**
        1.  Create a new route and component for the "Skills Dashboard".
        2.  Within this component, fetch data from the new `/analytics/skills/*` endpoints.
        3.  Use a charting library (e.g., Chart.js, Recharts) to create visualizations, such as a bar chart for the "Top 10 Skills" and a searchable table for the complete "Skill Inventory".
    *   **Rationale:** Delivers the high-level strategic insights that are the primary benefit of this integration.

---

### **Phase 3: Verification & Testing**

*   **Action 3.1: Backend Testing**
    *   **Task:** Write unit and integration tests for the new backend functionality.
    *   **Implementation:**
        1.  For the `LightcastClient`, write unit tests that mock the `requests` library to avoid making real API calls.
        2.  For the new API endpoints, write integration tests using `pytest` and the FastAPI `TestClient` to verify endpoint logic and database interactions.

*   **Action 3.2: Frontend Testing**
    *   **Task:** Write unit and end-to-end tests for the new UI components.
    *   **Implementation:**
        1.  Write unit tests for the new `SkillTag` and `SkillsDashboard` components using `bun test`.
        2.  Create new Playwright E2E tests (`bun run test:e2e`) for the user flows:
            *   Verify that after uploading a job description, skills are correctly displayed on the detail page.
            *   Verify that the "Suggest Title" button fetches and displays suggestions.
            *   Verify that the Skills Dashboard correctly renders charts and data.
