# Product Requirements Document: Phase 1 - Job Description Ingestion Engine

**Product Name:** Job Description Database (JDDB) - Phase 1
**Version:** 1.0 (Completed)
**Date:** September 16, 2025

## 1. Introduction

This document outlines the product requirements for the initial phase of the Job Description Database (JDDB), which focused on building the core ingestion engine. This phase is **complete**. The system successfully processed, stored, and analyzed over 350 Executive-level government job descriptions, making them available via an AI-powered search interface.

This document is preserved as a record of the requirements for the foundational system.

## 2. Vision and Strategy

### 2.1. Product Concept

The goal of Phase 1 was to transform unstructured job description files into a searchable, intelligent database. This involved creating a system for ingesting documents, structuring their information, and enabling semantic search capabilities.

### 2.2. Business Context

This project was initiated to support organizational design, planning, and strategic analysis by centralizing and structuring all executive job descriptions. The primary goal was to create a single source of truth and improve adherence to Treasury Board Secretariat policies and standards.

## 3. Target Audience

The primary target audience for the Phase 1 system was **Human Resources (HR) Business Partners** at ESDC.

## 4. User Stories & Requirements

### 4.1. User Stories

*   **As an HR Business Partner, I want to** easily upload job description documents in various formats, so that I can quickly get them into the system.
*   **As an HR Business Partner, I want to** have the system automatically extract and structure the content of the job descriptions, so that I don't have to do it manually.
*   **As an HR Business Partner, I want to** be able to search for job descriptions using keywords and filters, so that I can easily find the information I need.

### 4.2. Functional Requirements

The JDDB system delivered the following functional requirements in Phase 1:

#### 4.2.1. File Ingestion

*   The system supports the ingestion of job description documents in `.txt`, `.doc`, `.docx`, and `.pdf` formats.
*   The system handles files with various naming conventions.
*   The system supports Optical Character Recognition (OCR) for scanned PDF documents.

#### 4.2.2. Content Processing

*   The system automatically identifies and extracts standardized sections from job descriptions.
*   The system parses and stores structured fields such as position title, job number, and classification.
*   The system supports both English and French job descriptions.

#### 4.2.3. Web Interface

*   A web-based interface for users to interact with the system.
*   A dashboard providing an overview of the job descriptions in the database.
*   A feature to upload multiple job descriptions at once.
*   A comprehensive search interface with full-text and semantic search capabilities.
*   A detailed view of each job description.

## 5. Non-Functional Requirements

### 5.1. Performance

*   The system processes a single job description in under 5 seconds.
*   Search queries return results in under 200ms.

### 5.2. Scalability

*   The system was designed to eventually handle all 1200 different job descriptions at ESDC.

### 5.3. Security

*   The system adheres to Government of Canada security standards.
*   Access is restricted to authorized users.

## 6. Success Metrics

The success of Phase 1 was measured by:

*   **Ingestion Accuracy:** >95% accuracy in extracting sections and fields.
*   **User Satisfaction:** Positive feedback from HR Business Partners.
*   **Time Savings:** A measurable reduction in the time required to process and analyze job descriptions.
