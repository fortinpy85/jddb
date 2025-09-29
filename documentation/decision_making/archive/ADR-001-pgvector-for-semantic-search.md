# ADR-001: Use of pgvector for Semantic Search

- **Date:** 2025-09-10
- **Category:** Technical
- **Decision Maker(s):** Technical Lead
- **Stakeholders:** Backend Development Team, Product Manager

---

## Problem Statement

The project requires a robust and efficient way to store vector embeddings and perform similarity searches to power the semantic search feature. We need to decide whether to use an integrated database solution or a separate, dedicated vector database.

---

## Options Considered

### Option 1: Use `pgvector` within our existing PostgreSQL database

- **Description:** `pgvector` is a PostgreSQL extension that allows for the storage and querying of vector embeddings directly within our primary database.
- **Pros:**
    - **Simplified Architecture:** Keeps all data (relational and vector) in a single database, reducing operational complexity.
    - **Lower Cost:** Avoids the need to pay for and maintain a separate dedicated vector database service.
    - **Transactional Integrity:** Allows for transactional operations that involve both relational and vector data.
- **Cons:**
    - **Potential Performance Bottlenecks:** May not scale as well as a dedicated vector database for extremely large datasets (billions of vectors).

### Option 2: Use a Dedicated Vector Database (e.g., Pinecone, Weaviate)

- **Description:** A separate, specialized database service designed exclusively for storing and querying vector embeddings.
- **Pros:**
    - **Optimized Performance:** Built from the ground up for vector search and may offer better performance at a very large scale.
    - **Managed Service:** Reduces the burden of managing and tuning the vector search infrastructure.
- **Cons:**
    - **Increased Complexity:** Requires managing and syncing data between two separate databases (PostgreSQL and the vector DB).
    - **Higher Cost:** Introduces an additional infrastructure cost.
    - **Data Sync Challenges:** Keeping the vector database in sync with the primary application database can be complex.

---

## Decision & Rationale

**Chosen Option:** Option 1: Use `pgvector` within our existing PostgreSQL database.

**Rationale:**
For the scale of our project (initially hundreds, eventually thousands of documents), `pgvector` offers the best balance of performance, simplicity, and cost. The benefit of a simplified architecture and lower operational overhead far outweighs the potential for performance issues at a scale we are unlikely to reach in the medium term. Keeping our data in a single, familiar database is a significant advantage for development speed and maintainability.

---

## Impact Assessment

- **Positive Impacts:** The development team can move faster by working with a single, familiar database. The project's infrastructure costs and complexity are kept to a minimum.
- **Negative Impacts / Trade-offs:** If the number of documents grows into the millions, we may need to revisit this decision and migrate to a dedicated vector database. This is considered an acceptable risk for now.
- **Impact on other areas:** This decision solidifies PostgreSQL as the single source of truth for all application data, simplifying the backend data access layer.

---

## Follow-up Information

- **Implementation Status:** Completed
- **Review Date:** N/A
- **Related Decisions:** N/A
