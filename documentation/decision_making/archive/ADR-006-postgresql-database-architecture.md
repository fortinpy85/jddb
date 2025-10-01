# ADR-006: PostgreSQL as Primary Database with Extensions Architecture

- **Date:** 2025-09-10
- **Category:** Technical
- **Decision Maker(s):** Technical Lead, Database Architect
- **Stakeholders:** Backend Development Team, DevOps Team, Security Team

---

## Problem Statement

The JDDB system required a database solution that could support:
- Relational data for job descriptions, users, and metadata
- Vector embeddings for semantic search capabilities
- Real-time collaborative editing with change tracking
- Translation memory and bilingual content management
- Audit trails and compliance logging
- High performance with complex queries and joins
- Scalability for government-wide deployment

---

## Options Considered

### Option 1: PostgreSQL with pgvector Extension - Chosen

- **Description:** Single PostgreSQL database with specialized extensions for advanced features
- **Pros:**
    - Unified data storage reducing operational complexity
    - ACID compliance ensuring data integrity
    - Rich extension ecosystem (pgvector, full-text search, JSON/JSONB)
    - Mature replication and backup solutions
    - Strong security features and government compliance support
    - Excellent performance for complex relational queries
    - Transactional integrity across relational and vector data
    - Cost-effective single database solution
- **Cons:**
    - Vector operations may not scale to billions of vectors
    - Single point of failure without proper replication
    - Requires expertise in PostgreSQL optimization

### Option 2: PostgreSQL + Dedicated Vector Database (Pinecone/Weaviate)

- **Description:** Separate specialized databases for different data types
- **Pros:**
    - Optimized vector search performance at massive scale
    - Managed service reducing operational burden for vector operations
    - Specialized tooling for vector data management
- **Cons:**
    - Increased architectural complexity with multiple databases
    - Data synchronization challenges between systems
    - Higher operational costs with multiple services
    - Potential consistency issues between databases
    - More complex backup and recovery procedures

### Option 3: NoSQL Database (MongoDB with Vector Search)

- **Description:** Document-based database with vector search capabilities
- **Pros:**
    - Flexible schema for varied job description formats
    - Built-in vector search capabilities
    - Horizontal scaling capabilities
- **Cons:**
    - Loss of ACID compliance for complex transactions
    - Less mature tooling for government compliance requirements
    - Limited support for complex relational queries
    - Team unfamiliarity with NoSQL operational patterns

### Option 4: Microservices with Specialized Databases

- **Description:** Separate databases per service (user management, content, vectors)
- **Pros:**
    - Optimal database choice for each domain
    - Independent scaling of different components
    - Clear service boundaries
- **Cons:**
    - Significant architectural complexity
    - Distributed transaction challenges
    - Multiple operational overhead points
    - Complex data consistency management

---

## Decision & Rationale

**Chosen Option:** Option 1: PostgreSQL with pgvector Extension

**Rationale:**
For the JDDB scale (thousands to hundreds of thousands of documents), PostgreSQL with extensions provides the optimal balance of functionality, performance, and operational simplicity. The unified architecture enables complex cross-domain queries while maintaining ACID compliance for critical collaborative editing features. The pgvector extension has proven adequate for semantic search requirements, and PostgreSQL's mature ecosystem provides enterprise-grade security and compliance features required for government deployment.

---

## Impact Assessment

- **Positive Impacts:**
    - Simplified operations with single database to monitor and maintain
    - Transactional integrity across all data operations
    - Reduced infrastructure costs with unified solution
    - Strong security and compliance capabilities for government requirements
    - Excellent tooling and community support for troubleshooting
    - Clear data relationships and referential integrity
    - Simplified backup and disaster recovery procedures

- **Negative Impacts / Trade-offs:**
    - Vector search performance may require optimization for large scales
    - Single database creates potential bottleneck without proper scaling
    - Requires PostgreSQL expertise for advanced optimization
    - Extension dependencies may complicate upgrades

- **Impact on other areas:**
    - Backend development simplified with single ORM/database connection
    - Testing simplified with single database setup
    - DevOps complexity reduced with single database deployment
    - Security auditing centralized on single data store
    - Migration strategies simplified with unified schema

---

## Follow-up Information

- **Implementation Status:** Completed
- **Review Date:** 2026-09-10 (annual review with performance assessment)
- **Related Decisions:**
    - ADR-001: Use of pgvector for Semantic Search
    - ADR-007: Database Schema Evolution Strategy
- **Performance Thresholds:**
    - Vector search response time <200ms for 95th percentile
    - Collaborative editing write operations <100ms
    - Migration to dedicated vector database if >1M documents
- **Extensions Used:**
    - pgvector for vector embeddings
    - pg_trgm for fuzzy text search
    - uuid-ossp for UUID generation
