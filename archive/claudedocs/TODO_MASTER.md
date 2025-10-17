# Master TODO List

This document consolidates all remaining tasks and issues from various reports.

## Frontend

### Critical 🔴

-   **Translate Feature Crash**: The application crashes when the "Translate" feature is accessed from the job detail view.
    -   **File**: `src/app/page.tsx`, `src/components/translation/BilingualEditor.tsx`
    -   **Report**: `critical.md`

### High 🟠

-   **Navigation Buttons Not Disabled**: The "Translate" and "Improve" navigation buttons are not properly disabled when no job is selected.
    -   **File**: `src/components/layout/AppHeader.tsx`
    -   **Report**: `critical.md`

### Medium 🟡

-   **Inconsistent Quality Score**: All jobs show an 85% quality score in the list view, which is inconsistent with the detail view.
    -   **File**: `src/components/JobList.tsx`
    -   **Report**: `critical.md`
-   **Missing Job Metadata**: Multiple jobs are missing critical metadata like title and classification.
    -   **Report**: `critical.md`
-   **API Client Test Failure**: One test in `api.test.ts` related to `testConnection` is failing.
    -   **File**: `src/lib/api.test.ts`
    -   **Report**: `TEST_VERIFICATION_SUMMARY.md`
-   **Error Boundary Test Failures**: Two tests in `error-boundary.test.tsx` related to reset functionality are failing.
    -   **File**: `src/components/ui/error-boundary.test.tsx`
    -   **Report**: `TEST_VERIFICATION_SUMMARY.md`

### Low 🟢

-   **Skeleton Test Failures**: Two tests in `skeleton.test.tsx` are failing due to UI changes.
    -   **File**: `src/components/ui/skeleton.test.tsx`
    -   **Report**: `TEST_VERIFICATION_SUMMARY.md`
-   **React `act()` Warnings**: Three warnings in `transitions.test.tsx` and `animated-counter.test.tsx`.
    -   **Files**: `src/components/ui/transitions.test.tsx`, `src/components/ui/animated-counter.test.tsx`
    -   **Report**: `TEST_VERIFICATION_SUMMARY.md`
-   **Port Inconsistency**: The application is running on port 3004 instead of the documented 3003.
    -   **Report**: `critical.md`
-   **Blocked Feature - Translation Memory Update**: The `useTranslationMemory.ts` update endpoint is blocked by the backend.
    -   **File**: `src/hooks/useTranslationMemory.ts`
    -   **Report**: `frontend_list.md`
-   **Blocked Feature - Compare View Navigation**: Navigation to the editing view from `CompareView.tsx` is blocked by the backend.
    -   **File**: `src/components/compare/CompareView.tsx`
    -   **Report**: `frontend_list.md`

## Backend

### High 🟠

-   **Job Deletion Fails**: Job deletion fails due to a database constraint violation.
    -   **File**: `backend/src/jd_ingestion/api/endpoints/jobs.py`
    -   **Report**: `JOB_EDIT_DELETE_TROUBLESHOOTING_REPORT.md`
-   **Job Editing Not Implemented**: The job editing feature is not implemented.
    -   **Report**: `JOB_EDIT_DELETE_TROUBLESHOOTING_REPORT.md`

### Medium 🟡

-   **Translation Memory Service is a Stub**: The Translation Memory service needs to be implemented.
    -   **File**: `backend/src/jd_ingestion/services/translation_memory_service.py`
    -   **Report**: `backend_implementation_status_report.md`
-   **Lightcast Job Title Standardization Not Implemented**: This feature is blocked by an API subscription.
    -   **File**: `backend/src/jd_ingestion/services/lightcast_client.py`
    -   **Report**: `backend_implementation_status_report.md`

### Low 🟢

-   **Authentication/Authorization Not Audited**: The authentication and authorization code has not been audited.
    -   **Report**: `backend_implementation_status_report.md`
-   **Database Backup/Restore Not Audited**: The database backup and restore functionality has not been audited.
    -   **Report**: `backend_implementation_status_report.md`
-   **Hardcoded Secrets**: Hardcoded secrets are present in `settings.py`.
    -   **File**: `backend/src/jd_ingestion/config/settings.py`
    -   **Report**: `todo.md`
-   **CORS Wildcard in Production**: CORS is configured with a wildcard for production.
    -   **Report**: `todo.md`
-   **API Key Logged in Plain Text**: The API key is logged in plain text.
    -   **File**: `backend/src/jd_ingestion/auth/api_key.py`
    -   **Report**: `todo.md`

## Testing

### High 🟠

-   **Fix E2E Test Infrastructure**: The E2E test infrastructure needs to be fixed to use existing dev servers.
    -   **Report**: `E2E_TEST_EXECUTION_SUMMARY.md`
-   **Hardcoded URLs in Tests**: Hardcoded URLs are present in test files.
    -   **Report**: `E2E_TEST_EXECUTION_SUMMARY.md`
-   **Missing h1 Elements Breaking Tests**: Missing h1 elements in the UI are breaking tests.
    -   **Report**: `E2E_TEST_EXECUTION_SUMMARY.md`

### Medium 🟡

-   **Increase Backend Test Coverage**: Increase test coverage for tasks, services, and endpoints.
    -   **Report**: `TEST_IMPROVEMENT_REPORT.md`
-   **Increase Frontend Test Coverage**: Increase test coverage for the API client and components.
    -   **Report**: `TEST_IMPROVEMENT_REPORT.md`

### Low 🟢

-   **Enable Parallel Backend Test Execution**: Enable parallel execution for backend tests.
    -   **Report**: `BACKEND_TEST_REPORT.md`
-   **Add Test Coverage Reporting to CI/CD**: Add test coverage reporting to the CI/CD pipeline.
    -   **Report**: `TEST_IMPROVEMENT_REPORT.md`

## Documentation

### High 🟠

-   **Outdated `backend_list.md`**: The `backend_list.md` document is severely outdated and needs to be updated or removed.
    -   **File**: `backend_list.md`
    -   **Report**: `backend_implementation_status_report.md`
