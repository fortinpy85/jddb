# API Research for Application Augmentation

**Date:** October 4, 2025
**Author:** Gemini Research Persona

## 1. Executive Summary

This document outlines findings from research into public, open, and relevant APIs that can be integrated to augment and enhance the capabilities of the JDDB application. The research focused on APIs in categories inspired by the Lightcast API, including skills/occupation data, labor market statistics, salary information, and advanced text analytics.

The following APIs represent high-value opportunities to enrich our job description data, provide deeper analytics, and introduce new intelligent features.

---

## 2. API Categories and Findings

### Category 1: Skills and Occupation Data

This category is the most direct way to enrich our core job description data, moving beyond simple text to structured, standardized information.

#### **API: O*NET Web Services**
*   **Website:** [https://www.onetonline.org/developers/](https://www.onetonline.org/developers/)
*   **Description:** The Occupational Information Network (O*NET) is the United States' primary source of occupational information, sponsored by the U.S. Department of Labor. The API provides access to their extensive database of standardized job titles, detailed work activities, required skills, knowledge, and abilities for thousands of occupations.
*   **Relevance to JDDB:**
    *   **Skill Standardization:** Validate and standardize skills extracted from job descriptions against a government-approved taxonomy.
    *   **Content Suggestion:** For a given job title (e.g., "Data Analyst"), we can pull typical tasks, required skills, and technology used to help users write more comprehensive job descriptions.
    *   **Career Pathing:** The "Related Occupations" data can be used to power skill-gap analysis and career pathing features.
*   **Access Model:** **Public / Open** (Free, requires attribution).

#### **API: European Skills, Competences, Qualifications and Occupations (ESCO)**
*   **Website:** [https://esco.ec.europa.eu/en/use-esco/api](https://esco.ec.europa.eu/en/use-esco/api)
*   **Description:** ESCO is the multilingual classification of European Skills, Competences, Qualifications and Occupations. It is a European Commission initiative that provides a standardized vocabulary in 27 languages.
*   **Relevance to JDDB:**
    *   **Enhanced Translation:** A perfect fit for our bilingual focus. We can ensure that a skill in English (e.g., "Project Management") is correctly mapped to its official equivalent in French ("Gestion de projet") and other languages.
    *   **International Standardization:** Provides a broader, international context for skills and occupations, useful for organizations that operate globally.
*   **Access Model:** **Public / Open** (Free).

---

### Category 2: Labor Market & Salary Data

These APIs provide macroeconomic context and real-time salary benchmarks, directly supporting predictive analytics and ensuring job descriptions are competitive.

#### **API: U.S. Bureau of Labor Statistics (BLS) API**
*   **Website:** [https://www.bls.gov/developers/](https://www.bls.gov/developers/)
*   **Description:** Provides access to a massive repository of U.S. economic data, including employment projections, national and regional wage data by occupation, and unemployment rates.
*   **Relevance to JDDB:**
    *   **Predictive Analytics:** Directly powers the "Predictive Content Analytics" features planned for Phase 6. We can show users how demand for a specific role is trending.
    *   **Salary Benchmarking:** Provide authoritative salary ranges for occupations based on national and regional data, helping users set competitive pay scales.
*   **Access Model:** **Public** (Free, requires registration for an API key).

#### **API: Adzuna API**
*   **Website:** [https://developer.adzuna.com/](https://developer.adzuna.com/)
*   **Description:** Adzuna aggregates job listings from thousands of sources. Their API provides access to real-time job market data, including salary statistics for specific job titles and locations based on live ads.
*   **Relevance to JDDB:**
    *   **Real-Time Salary Data:** Complements the historical, survey-based data from the BLS with real-time market data, giving a more dynamic view of salaries.
    *   **Competitive Analysis:** Allows for benchmarking a job description's requirements against what is currently being asked for in the market for similar roles.
*   **Access Model:** **Freemium** (Generous free tier for non-commercial use, requires an API key).

---

### Category 3: Text Analytics & Bias Detection

While our application has some AI capabilities, these specialized APIs can provide targeted, high-value analysis.

#### **API: Gender Decoder**
*   **Website:** There isn't a public, hosted API, but the logic is open-source and widely replicated. Example: [http://gender-decoder.katmatfield.com/](http://gender-decoder.katmatfield.com/)
*   **Description:** A tool based on research into gender-coded language in job ads. It checks text for words that are subtly associated with a particular gender and can discourage applicants.
*   **Relevance to JDDB:**
    *   **Bias Detection:** A direct and immediate implementation for our "Bias Detection" feature. We can integrate this logic into our backend to scan job descriptions and flag potentially biased language, with suggestions for neutral alternatives.
    *   **Improved Inclusivity:** Helps users write more inclusive job descriptions, which is a critical requirement for government and modern organizations.
*   **Access Model:** **Open Source** (The word lists and logic can be implemented directly in our backend).

---

## 3. Summary and Recommendation Matrix

| API Name | Primary Use Case for JDDB | Access Model | Relevance Score (1-5) |
| :--- | :--- | :--- | :--- |
| **O*NET Web Services** | Skill standardization & content suggestion | Public / Open | 5/5 (Highest) |
| **U.S. BLS API** | Salary data & predictive market trends | Public | 5/5 (Highest) |
| **Gender Decoder (Logic)** | Automated gender bias detection | Open Source | 5/5 (Highest) |
| **ESCO API** | Multilingual skill mapping & translation | Public / Open | 4/5 (High) |
| **Adzuna API** | Real-time salary benchmarks from job ads | Freemium | 4/5 (High) |

**Recommendation:**
1.  **Immediate Priority (Phase 5/6):** Integrate **O*NET** for skill validation and the **Gender Decoder** logic for bias detection. These are high-impact, low-cost features that align perfectly with our existing roadmap.
2.  **Next Priority (Phase 6):** Integrate the **U.S. BLS API** to build out the planned predictive analytics and salary benchmarking features.
3.  **Future Consideration:** Use the **Adzuna API** to add real-time market data and the **ESCO API** to enhance multilingual capabilities as the platform scales.
