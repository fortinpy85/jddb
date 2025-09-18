# Guide: Semantic Search & Job Matching

This document provides a technical overview of the semantic search and job matching implementation in the JDDB. It covers the system architecture and provides a guide for developers working with these features.

**Status**: ✅ **Completed & Production-Ready**

---

## 1. System Overview

The semantic matching system uses AI-powered vector embeddings to understand the conceptual meaning of job descriptions, enabling highly relevant search and comparison.

### 1.1. Key Components

- **Vector-Based Search:** Core search functionality using the OpenAI `text-embedding-ada-002` model.
    - *Location:* `backend/src/jd_ingestion/services/embedding_service.py`
- **Job Analysis Service:** Calculates similarity between jobs and sections using vector embeddings.
    - *Location:* `backend/src/jd_ingestion/services/job_analysis_service.py`
- **Vector Database:** PostgreSQL with the `pgvector` extension is used for storing and querying embeddings.

### 1.2. Core Features

- **Semantic Search:** Allows users to search for jobs using natural language queries that match concepts, not just keywords.
- **Job-to-Job Comparison:** Calculates an overall similarity score between two jobs based on their content.
- **Section-wise Similarity:** Provides a detailed breakdown of similarity scores for individual sections (e.g., "Accountabilities," "Scope").

---

## 2. Developer's Guide

This section provides practical guidance for developers interacting with or extending the semantic search system.

### 2.1. Embedding Generation Workflow

When a new document is ingested, the following workflow is triggered to generate and store its embeddings:

1.  **Content Extraction:** The raw text is extracted from the document.
2.  **Chunking:** The extracted text is divided into smaller, meaningful chunks. See the chunking strategy below.
3.  **API Call:** Each chunk is sent to the OpenAI API to generate a vector embedding.
4.  **Database Storage:** The generated embedding vector is stored in the `content_chunks` table alongside the text chunk and a reference to the parent job description.

### 2.2. Chunking Strategy

A "smart chunking" strategy is used to optimize for Retrieval-Augmented Generation (RAG) performance:

- **Method:** Chunking is done by section. Each major section of a job description (e.g., "General Accountability," "Nature and Scope") is treated as a single chunk.
- **Rationale:** This preserves the semantic context within each section, leading to more accurate and relevant search results compared to arbitrary fixed-size chunking.
- **Token Size:** While sections can vary in size, they generally fall within the optimal token limit for the embedding models.

### 2.3. Querying & Filtering

The system supports combining semantic search with metadata filtering. This is a powerful feature for narrowing down results.

**Example Use Case:** Find jobs similar to "director of data science" that are classified as `EX-02`.

**Implementation:**
1.  The `embedding_service.semantic_search` function first performs a vector similarity search on the query text to get a list of relevant job IDs and their similarity scores.
2.  This list of IDs is then used as a filter in a subsequent SQLAlchemy query that also applies the metadata filters (e.g., `classification == 'EX-02'`).

```python
# Conceptual example from the service
async def semantic_search_with_filters(
    query: str,
    classification: str | None = None,
    limit: int = 20
):
    # 1. Get semantically similar job IDs from pgvector
    similar_job_ids = await self.get_similar_job_ids(query)

    # 2. Build a standard SQLAlchemy query
    stmt = select(JobDescription).where(JobDescription.id.in_(similar_job_ids))

    # 3. Add metadata filters
    if classification:
        stmt = stmt.where(JobDescription.classification == classification)

    # 4. Execute the combined query
    results = await db.execute(stmt.limit(limit))
    return results.scalars().all()
```

### 2.4. Environment Variables

To use the embedding service, the following environment variable must be set in your `.env` file:

- `OPENAI_API_KEY`: Your secret key for the OpenAI API.

---

## 3. API Endpoints

- **Semantic Search:** `GET /api/search/`
    - Use the `query` parameter for a standard keyword search or a `semantic_query` parameter to trigger a vector search.
- **Job Comparison:** `GET /api/analysis/compare/{job_a_id}/{job_b_id}`
    - Returns a detailed comparison including vector-based similarity scores.

---

## 4. Legacy vs. New Implementation

- **Replaced System:** The previous implementation used simple word-based Jaccard similarity, which had no semantic understanding.
- **New System:** The current system uses OpenAI's embedding models to perform cosine similarity calculations, resulting in far superior relevance and accuracy.
