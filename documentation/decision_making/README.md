# Architecture Decision Records (ADRs) - JDDB Project

## 1. Overview

This directory contains the Architecture Decision Records (ADRs) for the Job Description Database (JDDB) project. ADRs provide a structured way to document and track key technical, design, and business decisions made throughout the project lifecycle.

**Purpose**: Maintain a clear, accessible history of why certain choices were made, which improves transparency, aids in onboarding new team members, and provides context for future decisions.

**Scope**: This system covers all significant decisions that impact the project's architecture, user experience, technology choices, or strategic direction.

---

## 2. Decision Categories

Decisions are categorized to help with filtering and understanding the context.

- **Technical:** Decisions related to the software architecture, technology stack, libraries, and implementation approaches.
    - *Example:* Choosing to use `pgvector` instead of a dedicated vector database.

- **Design:** Decisions related to the user experience (UX), visual design (UI), and interaction patterns.
    - *Example:* Selecting a single-column layout for the Job Viewer page to prioritize readability.

- **Business:** Decisions related to feature prioritization, resource allocation, timelines, and strategic project direction.
    - *Example:* Deciding to build a 21-day prototype for the editor before committing to the full Phase 2 vision.

---

## 3. Process Workflow

### 3.1. When to Log a Decision

A decision should be logged if it meets one or more of the following criteria:

- It has a significant impact on the project's architecture, user experience, or timeline.
- It is a choice between two or more viable options.
- It is likely to be a question that a new team member might ask in the future.
- It reverses a previous decision.

### 3.2. Decision-Making Authority

- **Technical Decisions:** The technical lead has the final say, based on input from the development team.
- **Design Decisions:** The UX/UI lead has the final say, based on user research and team input.
- **Business Decisions:** The project/product manager has the final say, based on stakeholder input and strategic goals.

### 3.3. Logging Process

1.  **Copy the Template:** Create a new file by copying `log_entry_template.md`.
2.  **Name the File:** Name the new file using the format `ADR-XXX-brief-decision-summary.md`, where `XXX` is the next sequential number.
3.  **Fill out the Template:** Complete all the fields in the template with clear and concise information.
4.  **Save to Archive:** Save the new decision record in the `/archive` sub-directory.
5.  **Review (Optional):** If the decision is particularly complex or contentious, have another team member review the ADR for clarity.

---

## 4. Current ADRs

| ADR | Title | Category | Status | Date |
|-----|-------|----------|---------|------|
| [ADR-001](archive/ADR-001-pgvector-for-semantic-search.md) | Use of pgvector for Semantic Search | Technical | Completed | 2025-09-10 |
| [ADR-002](archive/ADR-002-technology-stack-selection.md) | Technology Stack Selection for JDDB Platform | Technical | Completed | 2025-09-15 |
| [ADR-003](archive/ADR-003-bun-javascript-runtime.md) | Bun as JavaScript Runtime and Package Manager | Technical | Completed | 2025-09-16 |
| [ADR-004](archive/ADR-004-frontend-architecture-approach.md) | Frontend Architecture Approach - Custom Bun Server vs Next.js | Technical | Completed | 2025-09-16 |
| [ADR-005](archive/ADR-005-zustand-state-management.md) | Zustand for Frontend State Management | Technical | Completed | 2025-09-17 |
| [ADR-006](archive/ADR-006-postgresql-database-architecture.md) | PostgreSQL as Primary Database with Extensions Architecture | Technical | Completed | 2025-09-10 |
| [ADR-007](archive/ADR-007-testing-strategy-playwright-bun.md) | Testing Strategy with Playwright and Bun Test Runner | Technical | Completed | 2025-09-18 |

## 5. Decision Impact Map

### Core Architecture Decisions
- **ADR-002** (Technology Stack) → Foundation for all other technical decisions
- **ADR-006** (PostgreSQL) → Enables **ADR-001** (pgvector integration)
- **ADR-004** (Frontend Architecture) → Depends on **ADR-003** (Bun runtime)

### Frontend Ecosystem Decisions
- **ADR-003** (Bun Runtime) → Enables **ADR-004** (Custom Server) and **ADR-007** (Testing Strategy)
- **ADR-005** (Zustand) → Complements **ADR-004** (Frontend Architecture)
- **ADR-007** (Testing) → Integrates with **ADR-003** (Bun) and **ADR-004** (Architecture)

## 6. Review & Update Process

- **Review Schedule:** Decisions are generally considered immutable to preserve the historical context. However, a decision can be superseded by a new one.
- **Annual Reviews:** Each ADR includes a review date for periodic assessment of continued validity
- **Superseding a Decision:** If a past decision is no longer valid, a *new* ADR should be created. This new ADR should reference the old one in the "Related Decisions" section and clearly state why the previous decision is being changed.
- **Access:** The decision log is open and accessible to all members of the project team.

## 7. Quick Start Guide

### Creating a New ADR
1. Copy `log_entry_template.md` to a new file
2. Name it `ADR-XXX-brief-decision-summary.md` (use next sequential number)
3. Fill out all template sections completely
4. Save in the `/archive` directory
5. Update this README with the new entry
6. Optional: Have another team member review for clarity

### Finding Related Decisions
- Use the Decision Impact Map above to understand dependencies
- Check the "Related Decisions" section in each ADR
- Search by category (Technical, Design, Business) for related choices
