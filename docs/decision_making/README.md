# Decision Logging Framework

## 1. Overview

This document outlines the process and structure for recording key decisions made throughout the JDDB project. The goal is to maintain a clear, accessible history of why certain choices were made, which improves transparency, aids in onboarding new team members, and provides context for future decisions.

This system is based on the concept of Architecture Decision Records (ADRs).

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

## 4. Review & Update Process

- **Review Schedule:** Decisions are generally considered immutable to preserve the historical context. However, a decision can be superseded by a new one.
- **Superseding a Decision:** If a past decision is no longer valid, a *new* ADR should be created. This new ADR should reference the old one in the "Related Decisions" section and clearly state why the previous decision is being changed.
- **Access:** The decision log is open and accessible to all members of the project team.
