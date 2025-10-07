 # UI/UX Improvement Plan

**Date:** 2025-10-04
**Reviewer:** Gemini Senior Developer Persona

## 1. Executive Summary

The JDDB application's frontend is built on a modern foundation using React, Radix UI, and a component-based architecture. The interface is functional and presents complex information effectively, particularly in the `SearchInterface` and `JobsTable` components.

However, a detailed review of the UI components and user flow reveals several opportunities to enhance usability, clarity, and efficiency. The current implementation often lacks sufficient user feedback for asynchronous operations, has inconsistencies in layout and interaction patterns, and misses opportunities to streamline complex workflows.

This document provides a comprehensive inventory of interactive components and a list of actionable recommendations to create a cleaner, more intuitive, and user-friendly interface. Implementing these changes will reduce user friction, improve task efficiency, and align the application with modern UX best practices.

---

## 2. Global UI/UX Recommendations

These suggestions apply across the entire application to ensure a consistent and predictable user experience.

| Component/Area | Observation | Recommendation |
| :--- | :--- | :--- |
| **Asynchronous Actions** | Buttons that trigger API calls (e.g., Search, Save, Upload) show a loading spinner but don't always prevent double-clicking. The cursor remains a pointer, not indicating a waiting state. | **Standardize Busy/Loading State:** Globally apply `cursor: wait` and `pointer-events: none` to the `<body>` or a top-level wrapper when a critical async action is in progress. Ensure all interactive elements inherit this state to prevent unintended user actions. |
| **Error Feedback** | API errors are caught and displayed, but often as a simple text message (e.g., `error instanceof Error ? err.message : "Search failed"`). This is not user-friendly. | **Implement User-Friendly Error Toasts:** Use the existing `Toast` component to display non-critical errors (e.g., failed facet loading). For critical errors (e.g., search or upload failure), use the `AlertBanner` or a dedicated modal to provide a clear, user-friendly message and suggested actions (e.g., "Could not connect to the server. Please check your connection and try again."). |
| **Empty States** | The `SearchInterface` has a good initial state, but other areas may lack this. The `JobsTable` shows a message but could be more engaging. | **Enhance Empty State Components:** Standardize empty state components across the app. Instead of just text, include an icon and a primary call-to-action button. For the `JobsTable`, the empty state should prominently feature the "Upload Job Descriptions" button to guide new users. |
| **Keyboard Navigation** | The application has a keyboard shortcuts modal, which is excellent. However, focus management during navigation is not always clear. | **Improve Focus Management:** When a view changes (e.g., `handleViewChange`), programmatically move focus to the main heading (`<h1>`) or the primary interactive element of the new view. For example, after navigating to 'search', focus should be set on the search input field. |

---

## 3. Component-Specific Improvements

### 3.1. Main Application Page (`page.tsx`)

| Component/Area | Observation | Recommendation |
| :--- | :--- | :--- |
| **View Navigation** | Navigating to views that require a selected job (e.g., 'Improve', 'Translate') without a selection falls back to the home page silently. | **Provide Contextual Feedback:** If a user clicks "Improve" without a selected job, show a toast notification explaining why they were redirected: "Please select a job first to use the improvement tools." |
| **Tab Management** | The `ProfileHeader` shows hardcoded open tabs. This appears to be placeholder UI and doesn't reflect the application's state. | **Implement Dynamic Tab Management:** The tab bar should dynamically represent the user's active context. For example, when a user selects a job, it should open in a new tab in this bar. This allows users to switch between multiple job details or comparison views, a powerful feature for a data-intensive application. |
| **Alert Banner** | The "Phase 3" alert banner is dismissible, but the state (`showAlertBanner`) is managed locally and will reappear on page refresh. | **Persist Banner Dismissal:** Store the dismissed state of the alert banner in `localStorage` or `user_preferences` on the backend. This prevents the same announcement from repeatedly appearing for the user. |

### 3.2. Search Interface (`SearchInterface.tsx`)

| Component/Area | Observation | Recommendation |
| :--- | :--- | :--- |
| **Search Button** | The search button is disabled if the query is empty, which is good. However, after a search, if the user clears the input, the results remain visible. | **Clear Results on Input Clear:** When the search input is cleared, the search results should also be cleared, returning the interface to its initial state. This provides a more intuitive experience. |
| **Filter Interaction** | Applying a filter from the `FilterBar` does not automatically re-run the search. The user must manually click the "Search" button again. | **Enable Automatic Search on Filter Change:** To streamline the workflow, make the search execute automatically whenever a filter is applied, removed, or changed. Provide a small loading indicator near the filters to show that the results are being updated. |
| **Section Type Filters** | The section type filters are presented as a long list of badges that can wrap and become disorganized. | **Use a Multi-Select Dropdown for Sections:** Replace the badge list with a more scalable `MultiSelect` or `ComboBox` component for the "Search in Sections" filter. This will handle a large number of section types more cleanly and is a more conventional UI pattern. |
| **Result Snippet** | The `result.snippet` is displayed as plain text. It's unclear which parts of the snippet matched the user's query. | **Highlight Matching Terms:** In the backend, modify the snippet generation to wrap matching keywords in a special tag (e.g., `<mark>`). On the frontend, use this to highlight the terms, immediately drawing the user's eye to the relevant text. |
| **View/Export Buttons** | The `onJobSelect` and `handleExport` functions reconstruct a `JobDescription` object from the `SearchResult`. This is redundant and potentially error-prone if the models diverge. | **Unify Data Models or Use IDs:** Refactor the API client or state management to handle `SearchResult` directly, or simply pass the `result.job_id` to the `onJobSelect` handler and have the parent component fetch the full `JobDescription` object. This simplifies the component's responsibility. |

### 3.3. Jobs Table (`JobsTable.tsx` - based on `page.tsx` usage)

| Component/Area | Observation | Recommendation |
| :--- | :--- | :--- |
| **Data Loading** | The `useEffect` in `page.tsx` calls `fetchJobs` and `fetchStats` on mount. There is a global `loading` state, but no specific feedback on the table itself. | **Implement Skeleton Loading:** While the jobs table data is loading, display a skeleton screen that mimics the layout of the table rows. This provides a much better perceived performance and user experience than a generic spinner. |
| **Pagination & Sorting** | The component appears to display a list of all jobs. There are no visible controls for pagination, sorting (e.g., by title, classification, date), or changing the number of items per page. | **Add Full-Featured Table Controls:** Implement server-side pagination, sorting, and filtering for the jobs table. Add controls to the UI for:
- Navigating between pages (Next, Previous, Page number).
- Sorting by clicking on column headers.
- A dropdown to select the number of results per page (e.g., 10, 25, 50). |
| **"Create New" Button** | The `onCreateNew` button logs a message to the console. This is an unimplemented but critical feature. | **Design a "Create New Job" Workflow:** This action should open a modal or navigate to a new page with a form for creating a new `JobDescription` from scratch, rather than from a file. The form should include fields for title, classification, and initial content. |

### 3.4. Core UI Components (`components/ui/`)

| Component/Area | Observation | Recommendation |
| :--- | :--- | :--- |
| **Input Fields** | The `Input` component is standard. In the `SearchInterface`, it's used for the department filter without a clear label. | **Ensure All Inputs Have Labels:** For accessibility and clarity, every input field must have an associated `<label>`. For compact UIs where a visible label is not desired, use an `aria-label` attribute. The department filter should have a visible label or a clearly associated icon with a tooltip. |
| **Buttons** | The design is consistent, but there is no clear visual distinction between primary actions (e.g., "Search") and secondary actions (e.g., "Export"). | **Establish a Visual Hierarchy for Buttons:** Define clear styles for button variants. For example:
- **Primary (`variant="default"`):** Solid background, for the main positive action on a page (e.g., Search, Save).
- **Secondary (`variant="secondary"`):** Less prominent style, for secondary actions (e.g., Export, Clear Filters).
- **Destructive (`variant="destructive"`):** Red color, for actions that delete data. |
