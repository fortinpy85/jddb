# Information Architecture: JDDB

## 1. Overview

This document outlines the information architecture (IA) for the Job Description Database (JDDB) web application. The goal is to create a structure that is intuitive for both novice users (like Sam) and power users (like Alex), ensuring that all features are logically organized and easily accessible.

## 2. High-Level Site Map

The application will be organized into the following primary sections:

- **/ (Dashboard)**: The main landing page after login.
- **/search**: The primary interface for finding and filtering job descriptions.
- **/jobs/{id}**: The detailed viewer for a single job description.
- **/upload**: The interface for uploading new documents.
- **/editor/{id}**: The future location for the Phase 2 collaborative editor.
- **/admin**: A section for user management and system settings (for administrators).

---

## 3. Navigation Structure

### 3.1. Primary Navigation (Top Bar)

A persistent top navigation bar will be present on all pages and will contain the following links:

- **Dashboard**: Links to the main dashboard view.
- **Search**: Links to the search interface.
- **Upload**: Links to the file upload page.
- **User Profile / Logout**: A dropdown menu with user-specific options.

### 3.2. Breadcrumbs

To aid in orientation, a breadcrumb trail will be displayed on nested pages. For example:

- `Home > Search > Job #103011`
- `Home > Editor > Job #103249`

---

## 4. Content Organization by Section

### 4.1. Dashboard (`/`)

- **Purpose**: Provide a high-level overview and quick access to common actions.
- **Content Components**:
    - Welcome message & brief introduction.
    - Key system statistics (e.g., "Total JDs Processed," "Recently Added").
    - A list of recently viewed or edited documents.
    - A prominent call-to-action button for "Upload New Documents."

### 4.2. Search (`/search`)

- **Purpose**: Allow users to find job descriptions efficiently.
- **Content Components**:
    - A large, clear search bar for keyword and semantic search.
    - A collapsible filter panel with options for:
        - Classification (e.g., EX-01, EX-02)
        - Language (English, French)
        - Status (e.g., Draft, Final)
    - A results area that displays a list of matching job descriptions, each with a title, job number, and a snippet of matching text.

### 4.3. Job Viewer (`/jobs/{id}`)

- **Purpose**: Display the full content of a single job description in a clean, readable format.
- **Content Components**:
    - A header containing the job title, number, and classification.
    - A main content area displaying the extracted sections of the JD (e.g., Accountability, Scope).
    - A metadata panel showing all extracted fields (e.g., Reports to, Department).
    - Action buttons for "Compare," "Edit" (Phase 2), and "Export."

### 4.4. Upload (`/upload`)

- **Purpose**: Allow users to ingest new documents into the system.
- **Content Components**:
    - A drag-and-drop file upload zone.
    - A progress indicator for uploads and processing status.
    - A summary of completed uploads and any errors.

### 4.5. Editor (`/editor/{id}` - Phase 2)

- **Purpose**: Provide a collaborative space for creating and editing job descriptions.
- **Content Components**:
    - A side-by-side editor view.
    - A real-time presence indicator for other collaborators.
    - A commenting and suggestions panel.
    - An AI assistant panel.

## 5. URL Structure

The URL structure will be designed to be clean, readable, and predictable.

- `/dashboard`
- `/search?query=director&classification=EX-02`
- `/jobs/103011`
- `/jobs/103011/compare/103249`
- `/upload`
- `/editor/103011`
- `/admin/users`
