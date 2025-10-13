# Frontend Code Review: Incomplete Features and Future Enhancements

This document provides a comprehensive list of incomplete features, planned enhancements, and areas for code cleanup identified during a review of the frontend codebase.

## 1. Incomplete Features

### 1.1. AI-Powered Job Description Improvement

*   **Location:** `components/improvement/ImprovementView.tsx`
*   **Description:** The core logic for the AI-powered job description improvement feature is currently using placeholder data and simulations. The component makes a call to a `simulateImprovement` function which returns mock data.
*   **Status:** Done
*   **Plan:**
    1.  Integrate with the actual backend AI service for job description analysis and improvement suggestions.
    2.  Replace the `simulateImprovement` function with a real API call.
    3.  Handle loading and error states for the API call.
    4.  Ensure the UI correctly displays the suggestions from the AI service.

### 1.2. Quality Dashboard - Historical Data

*   **Location:** `components/ai/QualityDashboard.tsx`
*   **Description:** The Quality Dashboard has a "TODO" to be implemented once historical data is available. This suggests that the dashboard is not yet displaying historical quality metrics.
*   **Status:** Done
*   **Plan:**
    1.  Clarify the requirements for displaying historical data on the Quality Dashboard.
    2.  Work with the backend team to ensure the necessary API endpoints are available to fetch historical data.
    3.  Implement the UI to display historical quality metrics, including charts and trends.

### 1.3. Quality Dashboard - Phase 4

*   **Location:** `components/ai/QualityDashboard.tsx`
*   **Description:** The component contains a placeholder comment for "Phase 4".
*   **Status:** Done
*   **Plan:**
    1.  Determine the features and functionality planned for Phase 4 of the Quality Dashboard.
    2.  Create a detailed implementation plan for the Phase 4 features.

## 2. Planned Enhancements

### 2.1. Lock Warning Modal

*   **Location:** `app/page.tsx`
*   **Description:** A "Future Enhancement" comment indicates a plan to add a lock warning modal. This is likely to warn users when they are about to lose unsaved changes.
*   **Status:** Done
*   **Plan:**
    1.  Implement a modal component to display the lock warning.
    2.  Integrate the modal with the form or editor to detect unsaved changes.
    3.  Trigger the modal when the user attempts to navigate away with unsaved changes.

### 2.2. Navigate to Editing View with Merged Content

*   **Location:** `components/compare/CompareView.tsx`
*   **Description:** A "Future Enhancement" comment suggests that after comparing two job descriptions, the user should be able to navigate to an editing view with the merged content.
*   **Status:** Pending Backend
*   **Plan:**
    1.  Implement the logic to merge the content of the two job descriptions.
    2.  Add a button or link to navigate to the editing view.
    3.  Pass the merged content to the editing view as a prop or through state management.

### 2.3. Real-time Typing Indicators

*   **Location:** `components/editing/EnhancedDualPaneEditor.tsx`
*   **Description:** A "Future Enhancement" comment indicates a plan to send `typing_start` and `typing_stop` messages for real-time collaboration.
*   **Status:** Done
*   **Plan:**
    1.  Implement the client-side logic to detect when a user starts and stops typing.
    2.  Send the `typing_start` and `typing_stop` events to the server via websockets.
    3.  Implement the UI to display typing indicators to other users in the collaborative session.

### 2.4. Translation Memory API - Domain Parameter

*   **Location:** `hooks/useTranslationMemory.ts` (line 96-99), `backend/src/jd_ingestion/api/endpoints/translation_memory.py` (line 249)
*   **Description:** The code includes a `domain` parameter for future use with the translation memory API.
*   **Status:** ✅ Done
*   **Completed:**
    1.  Added `domain` query parameter to backend `/search` endpoint
    2.  Updated frontend to send domain parameter when provided
    3.  Backend now passes domain to service layer (ready for implementation)
*   **Note:** Translation Memory backend is currently stub implementation (returns empty results). Domain filtering will work once translation models are implemented.

### 2.5. Translation Memory - Update Translation Endpoint

*   **Location:** `hooks/useTranslationMemory.ts` (line 170-196)
*   **Description:** The `updateTranslation` function performs optimistic local updates but has no backend endpoint to persist changes.
*   **Status:** ⚠️ Blocked - Requires Backend Implementation
*   **Plan:**
    1.  Backend needs to implement `PUT /translation-memory/translations/{id}` endpoint
    2.  Endpoint should accept `target_text` parameter to update translation
    3.  Frontend is ready - will call endpoint once available
*   **Note:** Translation Memory backend is currently stub implementation. The entire feature needs database models and service implementation before this can be completed.

## 3. Code Cleanup and Refactoring

### 3.1. Remove "Future" Versions in Version History

*   **Location:** `hooks/useVersionHistory.ts` (line 66-99)
*   **Description:** The `useVersionHistory` hook contains a comment about removing "future" versions. This suggests that the version history logic might not be correctly handling branching or undo/redo actions.
*   **Status:** ✅ Done
*   **Completed:**
    1.  Fixed `pushVersion` function to correctly handle history slicing
    2.  Moved `setCurrentIndex` calls inside `setHistory` callback to use actual history length
    3.  Fixed both normal case and history size limit case
    4.  Ensured undo/redo branching works correctly (future branches are discarded when making new changes after undo)
*   **Fix Details:** Previous code calculated index using stale `prev` value outside callback. Now calculates index based on actual new history length, ensuring synchronization.

### 3.2. Placeholder Types

*   **Location:** `types/api.ts`
*   **Description:** The `api.ts` file contained 489 lines of placeholder types for missing imports.
*   **Status:** ✅ Done
*   **Completed:**
    1.  Audited all imports from `@/types/api` across the codebase
    2.  Found only 2 components using this file (BulkUpload.tsx, JobPostingGenerator.tsx)
    3.  Found only 2 types actually needed (JobDescription, UploadResponse)
    4.  Removed 489 lines of unused placeholder types (lines 121-610)
    5.  Added deprecation notice directing to `@/lib/types.ts`
*   **Impact:** 79% file size reduction (610 lines → 126 lines), improved maintainability