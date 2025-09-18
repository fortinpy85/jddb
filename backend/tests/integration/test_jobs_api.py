"""
Integration tests for Jobs API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
import json
from pathlib import Path

from jd_ingestion.database.models import JobDescription, JobSection, JobMetadata


@pytest.mark.integration
def test_get_jobs_empty(test_client: TestClient):
    """Test getting jobs when database is empty."""
    response = test_client.get("/api/jobs/")

    assert response.status_code == 200
    data = response.json()
    assert data["jobs"] == []
    assert data["pagination"]["total"] == 0


@pytest.mark.integration
def test_create_and_get_job(test_client: TestClient, test_session):
    """Test creating a job and retrieving it."""
    session, TestJobDescription, TestJobSection, TestJobMetadata = test_session

    job_data = {
        "job_number": "103249",
        "title": "Director, Business Analysis",
        "classification": "EX-01",
        "language": "EN",
        "file_path": "/test/path/job.txt",
        "raw_content": "Test job description content",
    }

    # Create job using test models
    job = TestJobDescription(**job_data)
    session.add(job)
    session.commit()
    session.refresh(job)

    # Get jobs
    response = test_client.get("/api/jobs/")

    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 1
    assert len(data["jobs"]) == 1
    assert data["jobs"][0]["job_number"] == "103249"
    assert data["jobs"][0]["title"] == "Director, Business Analysis"


@pytest.mark.integration
def test_get_job_by_id(test_client: TestClient, test_session):
    """Test getting a specific job by ID."""
    session, TestJobDescription, TestJobSection, TestJobMetadata = test_session

    job_data = {
        "job_number": "103249",
        "title": "Director, Business Analysis",
        "classification": "EX-01",
        "language": "EN",
        "file_path": "/test/path/job.txt",
        "raw_content": "Test job description content",
    }

    # Create job
    job = TestJobDescription(**job_data)
    session.add(job)
    session.commit()
    session.refresh(job)

    # Get specific job
    response = test_client.get(f"/api/jobs/{job.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job.id
    assert data["job_number"] == "103249"
    assert data["title"] == "Director, Business Analysis"


@pytest.mark.integration
def test_get_job_not_found(test_client: TestClient):
    """Test getting non-existent job."""
    response = test_client.get("/api/jobs/99999")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.integration
def test_get_jobs_with_pagination(test_client: TestClient, test_session):
    """Test job listing with pagination."""
    session, TestJobDescription, TestJobSection, TestJobMetadata = test_session

    # Create multiple jobs
    jobs_data = [
        {
            "job_number": f"10000{i}",
            "title": f"Test Job {i}",
            "classification": "EX-01",
            "language": "EN",
            "file_path": f"/test/path{i}.txt",
            "raw_content": f"Content {i}",
        }
        for i in range(25)  # Create 25 jobs
    ]

    jobs = [TestJobDescription(**data) for data in jobs_data]
    session.add_all(jobs)
    session.commit()

    # Test first page
    response = test_client.get("/api/jobs/?page=1&size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 25
    assert len(data["jobs"]) == 10
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["pages"] == 3

    # Test second page
    response = test_client.get("/api/jobs/?page=2&size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 25
    assert len(data["jobs"]) == 10
    assert data["pagination"]["page"] == 2

    # Test last page
    response = test_client.get("/api/jobs/?page=3&size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 25
    assert len(data["jobs"]) == 5  # Remaining jobs
    assert data["pagination"]["page"] == 3


@pytest.mark.integration
def test_filter_jobs_by_classification(test_client: TestClient, test_session):
    """Test filtering jobs by classification."""
    session, TestJobDescription, TestJobSection, TestJobMetadata = test_session

    # Create jobs with different classifications
    jobs_data = [
        {
            "job_number": "100001",
            "title": "EX-01 Job",
            "classification": "EX-01",
            "language": "EN",
            "file_path": "/test1.txt",
            "raw_content": "Content 1",
        },
        {
            "job_number": "100002",
            "title": "EX-02 Job",
            "classification": "EX-02",
            "language": "EN",
            "file_path": "/test2.txt",
            "raw_content": "Content 2",
        },
        {
            "job_number": "100003",
            "title": "Another EX-01 Job",
            "classification": "EX-01",
            "language": "EN",
            "file_path": "/test3.txt",
            "raw_content": "Content 3",
        },
    ]

    jobs = [TestJobDescription(**data) for data in jobs_data]
    session.add_all(jobs)
    session.commit()

    # Filter by EX-01
    response = test_client.get("/api/jobs/?classification=EX-01")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 2
    assert all(job["classification"] == "EX-01" for job in data["jobs"])

    # Filter by EX-02
    response = test_client.get("/api/jobs/?classification=EX-02")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 1
    assert data["jobs"][0]["classification"] == "EX-02"


@pytest.mark.integration
def test_filter_jobs_by_language(test_client: TestClient, test_session):
    """Test filtering jobs by language."""
    session, TestJobDescription, TestJobSection, TestJobMetadata = test_session

    jobs_data = [
        {
            "job_number": "100001",
            "title": "English Job",
            "classification": "EX-01",
            "language": "EN",
            "file_path": "/test1.txt",
            "raw_content": "English content",
        },
        {
            "job_number": "100002",
            "title": "French Job",
            "classification": "EX-01",
            "language": "FR",
            "file_path": "/test2.txt",
            "raw_content": "Contenu français",
        },
    ]

    jobs = [TestJobDescription(**data) for data in jobs_data]
    session.add_all(jobs)
    session.commit()

    # Filter by English
    response = test_client.get("/api/jobs/?language=EN")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 1
    assert data["jobs"][0]["language"] == "EN"

    # Filter by French
    response = test_client.get("/api/jobs/?language=FR")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 1
    assert data["jobs"][0]["language"] == "FR"


@pytest.mark.integration
def test_search_jobs_by_title(test_client: TestClient, test_session):
    """Test searching jobs by title."""
    session, TestJobDescription, TestJobSection, TestJobMetadata = test_session

    jobs_data = [
        {
            "job_number": "100001",
            "title": "Director of Business Analysis",
            "classification": "EX-01",
            "language": "EN",
            "file_path": "/test1.txt",
            "raw_content": "Content 1",
        },
        {
            "job_number": "100002",
            "title": "Senior Analyst",
            "classification": "EX-01",
            "language": "EN",
            "file_path": "/test2.txt",
            "raw_content": "Content 2",
        },
        {
            "job_number": "100003",
            "title": "Director of Communications",
            "classification": "EX-02",
            "language": "EN",
            "file_path": "/test3.txt",
            "raw_content": "Content 3",
        },
    ]

    jobs = [TestJobDescription(**data) for data in jobs_data]
    session.add_all(jobs)
    session.commit()

    # Search for "Director"
    response = test_client.get("/api/jobs/?search=Director")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 2
    assert all("Director" in job["title"] for job in data["jobs"])

    # Search for "Analyst"
    response = test_client.get("/api/jobs/?search=Analyst")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 1  # Only "Senior Analyst" contains "Analyst"
    assert "Senior Analyst" in data["jobs"][0]["title"]


@pytest.mark.integration
def test_get_job_with_sections(test_client: TestClient, test_session):
    """Test getting job with its sections."""
    session, TestJobDescription, TestJobSection, TestJobMetadata = test_session

    job_data = {
        "job_number": "103249",
        "title": "Director, Business Analysis",
        "classification": "EX-01",
        "language": "EN",
        "file_path": "/test/path/job.txt",
        "raw_content": "Test job description content",
    }

    # Create job
    job = TestJobDescription(**job_data)
    session.add(job)
    session.commit()
    session.refresh(job)

    # Add sections
    sections_data = [
        {
            "section_type": "GENERAL_ACCOUNTABILITY",
            "section_content": "General accountability content",
            "section_order": 1,
        },
        {
            "section_type": "SPECIFIC_ACCOUNTABILITIES",
            "section_content": "Specific accountability content",
            "section_order": 2,
        },
    ]

    for section_data in sections_data:
        section = TestJobSection(job_id=job.id, **section_data)
        session.add(section)

    session.commit()

    # Get job with sections
    response = test_client.get(f"/api/jobs/{job.id}")
    assert response.status_code == 200
    data = response.json()
    assert "sections" in data
    assert len(data["sections"]) == 2
    assert data["sections"][0]["section_type"] == "GENERAL_ACCOUNTABILITY"


@pytest.mark.integration
def test_get_job_with_metadata(test_client: TestClient, test_session):
    """Test getting job with its metadata."""
    session, TestJobDescription, TestJobSection, TestJobMetadata = test_session

    job_data = {
        "job_number": "103249",
        "title": "Director, Business Analysis",
        "classification": "EX-01",
        "language": "EN",
        "file_path": "/test/path/job.txt",
        "raw_content": "Test job description content",
    }

    # Create job
    job = TestJobDescription(**job_data)
    session.add(job)
    session.commit()
    session.refresh(job)

    # Add metadata
    metadata = TestJobMetadata(
        job_id=job.id,
        reports_to="Director General",
        department="Strategic Planning",
        fte_count=12,
        salary_budget=230000,
    )
    session.add(metadata)
    session.commit()

    # Get job with metadata
    response = test_client.get(f"/api/jobs/{job.id}")
    assert response.status_code == 200
    data = response.json()
    assert "job_metadata" in data
    assert data["job_metadata"]["reports_to"] == "Director General"
    assert data["job_metadata"]["fte_count"] == 12


@pytest.mark.integration
def test_get_job_statistics(test_client: TestClient, test_session):
    """Test getting job statistics."""
    session, TestJobDescription, TestJobSection, TestJobMetadata = test_session

    # Create jobs with different classifications and languages
    jobs_data = [
        {
            "job_number": "100001",
            "title": "Job 1",
            "classification": "EX-01",
            "language": "EN",
            "file_path": "/test1.txt",
            "raw_content": "Content 1",
        },
        {
            "job_number": "100002",
            "title": "Job 2",
            "classification": "EX-01",
            "language": "FR",
            "file_path": "/test2.txt",
            "raw_content": "Content 2",
        },
        {
            "job_number": "100003",
            "title": "Job 3",
            "classification": "EX-02",
            "language": "EN",
            "file_path": "/test3.txt",
            "raw_content": "Content 3",
        },
    ]

    jobs = [TestJobDescription(**data) for data in jobs_data]
    session.add_all(jobs)
    session.commit()

    # Get statistics
    response = test_client.get("/api/jobs/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["total_jobs"] == 3
    assert "classification_distribution" in data
    assert "language_distribution" in data
    assert data["classification_distribution"]["EX-01"] == 2
    assert data["classification_distribution"]["EX-02"] == 1
    assert data["language_distribution"]["EN"] == 2
    assert data["language_distribution"]["FR"] == 1


@pytest.mark.integration
def test_invalid_pagination_parameters(test_client: TestClient):
    """Test invalid pagination parameters."""
    # Test invalid page
    response = test_client.get("/api/jobs/?page=0")
    assert response.status_code == 422

    # Test invalid size
    response = test_client.get("/api/jobs/?size=0")
    assert response.status_code == 422

    # Test negative values
    response = test_client.get("/api/jobs/?page=-1&size=-10")
    assert response.status_code == 422