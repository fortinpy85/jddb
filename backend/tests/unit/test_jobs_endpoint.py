"""
Unit tests for jobs API endpoint
Tests all /api/jobs endpoints including CRUD operations and filtering
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from jd_ingestion.database.models import (
    JobDescription,
    JobMetadata,
    JobSection,
    Skill,
    job_description_skills,
)


@pytest.fixture
async def sample_job(async_session: AsyncSession) -> JobDescription:
    """Create a sample job description for testing"""
    job = JobDescription(
        job_number="123456",
        title="Director, Business Analysis",
        classification="EX-01",
        language="en",
        file_path="/data/test_job.txt",
        file_hash="test_hash_123",
        raw_content="Test job description content",
        processed_date=datetime.utcnow(),
    )
    async_session.add(job)
    await async_session.flush()

    # Add metadata
    metadata = JobMetadata(
        job_id=job.id,
        department="Business Analysis",
        reports_to="VP, Operations",
        location="Ottawa, ON",
        fte_count=5.0,  # SQLite doesn't support Decimal, use float
        salary_budget=500000.00,  # SQLite doesn't support Decimal, use float
    )
    async_session.add(metadata)

    # Add sections
    sections = [
        JobSection(
            job_id=job.id,
            section_type="GENERAL_ACCOUNTABILITY",
            section_content="Provides strategic direction for business analysis",
            section_order=1,
        ),
        JobSection(
            job_id=job.id,
            section_type="SPECIFIC_ACCOUNTABILITIES",
            section_content="Leads analysis initiatives\nDevelops strategies",
            section_order=2,
        ),
    ]
    for section in sections:
        async_session.add(section)

    await async_session.commit()
    await async_session.refresh(job)
    return job


@pytest.fixture
async def sample_skill(async_session: AsyncSession) -> Skill:
    """Create a sample skill for testing"""
    skill = Skill(
        lightcast_id="SKILL123",
        name="Strategic Planning",
        skill_type="specialized",
        category="Business",
    )
    async_session.add(skill)
    await async_session.commit()
    await async_session.refresh(skill)
    return skill


class TestListJobs:
    """Tests for GET /api/jobs endpoint"""

    @pytest.mark.asyncio
    async def test_list_jobs_basic(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test basic job listing"""
        response = await async_client.get("/api/jobs/")

        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "pagination" in data
        assert len(data["jobs"]) > 0
        assert data["jobs"][0]["job_number"] == "123456"

    @pytest.mark.asyncio
    async def test_list_jobs_pagination(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test pagination parameters"""
        # Test skip/limit
        response = await async_client.get("/api/jobs/?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["skip"] == 0
        assert data["pagination"]["limit"] == 10

        # Test page/size
        response = await async_client.get("/api/jobs/?page=1&size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["size"] == 10

    @pytest.mark.asyncio
    async def test_list_jobs_filter_classification(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test filtering by classification"""
        response = await async_client.get("/api/jobs/?classification=EX-01")

        assert response.status_code == 200
        data = response.json()
        assert all(job["classification"] == "EX-01" for job in data["jobs"])

    @pytest.mark.asyncio
    async def test_list_jobs_filter_language(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test filtering by language"""
        response = await async_client.get("/api/jobs/?language=en")

        assert response.status_code == 200
        data = response.json()
        assert all(job["language"] == "en" for job in data["jobs"])

    @pytest.mark.asyncio
    async def test_list_jobs_filter_department(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test filtering by department"""
        response = await async_client.get("/api/jobs/?department=Business")

        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) > 0

    @pytest.mark.asyncio
    async def test_list_jobs_search(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test search functionality"""
        response = await async_client.get("/api/jobs/?search=Director")

        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) > 0

    @pytest.mark.asyncio
    async def test_list_jobs_skill_filter(
        self,
        async_session: AsyncSession,
        sample_job: JobDescription,
        sample_skill: Skill,
        async_client: AsyncClient,
    ):
        """Test filtering by skill IDs"""
        # Associate skill with job
        stmt = job_description_skills.insert().values(
            job_id=sample_job.id,
            skill_id=sample_skill.id,
            confidence=0.85,
        )
        await async_session.execute(stmt)
        await async_session.commit()
        response = await async_client.get(f"/api/jobs/?skill_ids={sample_skill.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) > 0
        # Verify skills are included in response
        assert "skills" in data["jobs"][0]


class TestGetJob:
    """Tests for GET /api/jobs/{id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_job_basic(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test retrieving a single job"""
        response = await async_client.get(f"/api/jobs/{sample_job.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_job.id
        assert data["job_number"] == "123456"
        assert data["title"] == "Director, Business Analysis"

    @pytest.mark.asyncio
    async def test_get_job_with_sections(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test retrieving job with sections"""
        response = await async_client.get(
            f"/api/jobs/{sample_job.id}?include_sections=true"
        )

        assert response.status_code == 200
        data = response.json()
        assert "sections" in data
        assert len(data["sections"]) == 2
        assert data["sections"][0]["section_type"] == "GENERAL_ACCOUNTABILITY"

    @pytest.mark.asyncio
    async def test_get_job_with_metadata(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test retrieving job with metadata"""
        response = await async_client.get(
            f"/api/jobs/{sample_job.id}?include_metadata=true"
        )

        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data
        assert data["metadata"]["department"] == "Business Analysis"
        assert data["metadata"]["reports_to"] == "VP, Operations"

    @pytest.mark.asyncio
    async def test_get_job_with_content(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test retrieving job with raw content"""
        response = await async_client.get(
            f"/api/jobs/{sample_job.id}?include_content=true"
        )

        assert response.status_code == 200
        data = response.json()
        assert "raw_content" in data
        assert data["raw_content"] == "Test job description content"

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, async_client: AsyncClient):
        """Test retrieving non-existent job"""
        response = await async_client.get("/api/jobs/99999")

        assert response.status_code == 404


class TestGetJobSection:
    """Tests for GET /api/jobs/{id}/sections/{section_type} endpoint"""

    @pytest.mark.asyncio
    async def test_get_job_section(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test retrieving specific job section"""
        response = await async_client.get(
            f"/api/jobs/{sample_job.id}/sections/GENERAL_ACCOUNTABILITY"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["section_type"] == "GENERAL_ACCOUNTABILITY"
        assert "section_content" in data

    @pytest.mark.asyncio
    async def test_get_job_section_not_found(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test retrieving non-existent section"""
        response = await async_client.get(
            f"/api/jobs/{sample_job.id}/sections/NON_EXISTENT_SECTION"
        )

        assert response.status_code == 404


class TestCreateJob:
    """Tests for POST /api/jobs endpoint"""

    @pytest.mark.asyncio
    async def test_create_job_basic(self, async_client: AsyncClient):
        """Test creating a new job description"""
        job_data = {
            "job_number": "789012",
            "title": "Test Job",
            "classification": "EX-02",
            "language": "en",
        }
        response = await async_client.post("/api/jobs/", json=job_data)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["job"]["job_number"] == "789012"

    @pytest.mark.asyncio
    async def test_create_job_with_metadata(self, async_client: AsyncClient):
        """Test creating job with metadata"""
        job_data = {
            "job_number": "789013",
            "title": "Test Job with Metadata",
            "classification": "EX-02",
            "language": "en",
            "department": "IT",
            "reports_to": "CIO",
        }
        response = await async_client.post("/api/jobs/", json=job_data)

        assert response.status_code == 201
        data = response.json()
        assert data["job"]["job_number"] == "789013"

    @pytest.mark.asyncio
    async def test_create_job_with_sections(self, async_client: AsyncClient):
        """Test creating job with sections"""
        job_data = {
            "job_number": "789014",
            "title": "Test Job with Sections",
            "classification": "EX-02",
            "language": "en",
            "sections": {
                "GENERAL_ACCOUNTABILITY": "Test accountability content",
                "SPECIFIC_ACCOUNTABILITIES": "Test specific content",
            },
        }
        response = await async_client.post("/api/jobs/", json=job_data)

        assert response.status_code == 201


class TestUpdateJob:
    """Tests for PATCH /api/jobs/{id} endpoint"""

    @pytest.mark.asyncio
    async def test_update_job_title(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test updating job title"""
        update_data = {"title": "Updated Title"}
        response = await async_client.patch(
            f"/api/jobs/{sample_job.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job"]["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_job_classification(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test updating job classification"""
        update_data = {"classification": "EX-02"}
        response = await async_client.patch(
            f"/api/jobs/{sample_job.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job"]["classification"] == "EX-02"

    @pytest.mark.asyncio
    async def test_update_job_metadata(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test updating job metadata fields"""
        update_data = {
            "department": "Updated Department",
            "reports_to": "Updated Manager",
        }
        response = await async_client.patch(
            f"/api/jobs/{sample_job.id}", json=update_data
        )

        assert response.status_code == 200


class TestUpdateJobSection:
    """Tests for PATCH /api/jobs/{id}/sections/{section_id} endpoint"""

    @pytest.mark.asyncio
    async def test_update_job_section(
        self,
        async_session: AsyncSession,
        sample_job: JobDescription,
        async_client: AsyncClient,
    ):
        """Test updating a job section"""
        # Query sections directly from database to avoid greenlet issues
        from sqlalchemy import select

        section_query = (
            select(JobSection).where(JobSection.job_id == sample_job.id).limit(1)
        )
        section_result = await async_session.execute(section_query)
        section = section_result.scalar_one()
        section_id = section.id

        update_data = {"section_content": "Updated section content"}
        response = await async_client.patch(
            f"/api/jobs/{sample_job.id}/sections/{section_id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["section"]["section_content"] == "Updated section content"

    @pytest.mark.asyncio
    async def test_update_job_section_updates_timestamp(
        self,
        async_session: AsyncSession,
        sample_job: JobDescription,
        async_client: AsyncClient,
    ):
        """Test that section update refreshes job timestamp"""
        # Query section directly from database to avoid greenlet issues
        from sqlalchemy import select

        section_query = (
            select(JobSection).where(JobSection.job_id == sample_job.id).limit(1)
        )
        section_result = await async_session.execute(section_query)
        section = section_result.scalar_one()
        section_id = section.id

        update_data = {"section_content": "New content"}
        response = await async_client.patch(
            f"/api/jobs/{sample_job.id}/sections/{section_id}", json=update_data
        )

        assert response.status_code == 200

        # Verify timestamp was updated (refresh to get latest data)
        await async_session.refresh(sample_job)
        # Check that updated_at is now set (it may have been None before)
        assert sample_job.updated_at is not None

    @pytest.mark.asyncio
    async def test_update_job_section_not_found(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test updating non-existent section"""
        update_data = {"section_content": "Updated content"}
        response = await async_client.patch(
            f"/api/jobs/{sample_job.id}/sections/99999", json=update_data
        )

        assert response.status_code == 404


class TestDeleteJob:
    """Tests for DELETE /api/jobs/{id} endpoint"""

    @pytest.mark.asyncio
    async def test_delete_job(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test deleting a job description"""
        response = await async_client.delete(f"/api/jobs/{sample_job.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Verify job is deleted
        get_response = await async_client.get(f"/api/jobs/{sample_job.id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_job_not_found(self, async_client: AsyncClient):
        """Test deleting non-existent job"""
        response = await async_client.delete("/api/jobs/99999")

        assert response.status_code == 404


class TestReprocessJob:
    """Tests for POST /api/jobs/{id}/reprocess endpoint"""

    @pytest.mark.asyncio
    async def test_reprocess_job(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test reprocessing a job description"""
        response = await async_client.post(f"/api/jobs/{sample_job.id}/reprocess")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["job_id"] == sample_job.id

    @pytest.mark.asyncio
    async def test_reprocess_job_not_found(self, async_client: AsyncClient):
        """Test reprocessing non-existent job"""
        response = await async_client.post("/api/jobs/99999/reprocess")

        assert response.status_code == 404


class TestJobStatus:
    """Tests for GET /api/jobs/status endpoint"""

    @pytest.mark.asyncio
    async def test_get_processing_status(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test retrieving processing status"""
        response = await async_client.get("/api/jobs/status")

        assert response.status_code == 200
        data = response.json()
        assert "total_jobs" in data
        assert "by_classification" in data
        assert "by_language" in data
        assert "processing_status" in data


class TestJobStats:
    """Tests for GET /api/jobs/stats endpoint"""

    @pytest.mark.asyncio
    async def test_get_job_stats(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test retrieving job statistics"""
        response = await async_client.get("/api/jobs/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_jobs" in data
        assert "classification_distribution" in data
        assert "language_distribution" in data


class TestBulkExport:
    """Tests for POST /api/jobs/export/bulk endpoint"""

    @pytest.mark.asyncio
    async def test_export_jobs_json(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test exporting jobs in JSON format"""
        export_request = {
            "job_ids": [sample_job.id],
            "format": "json",
            "include_sections": True,
        }
        response = await async_client.post("/api/jobs/export/bulk", json=export_request)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    @pytest.mark.asyncio
    async def test_export_jobs_csv(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test exporting jobs in CSV format"""
        export_request = {
            "job_ids": [sample_job.id],
            "format": "csv",
            "include_metadata": True,
        }
        response = await async_client.post("/api/jobs/export/bulk", json=export_request)

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_export_jobs_txt(
        self, sample_job: JobDescription, async_client: AsyncClient
    ):
        """Test exporting jobs in TXT format"""
        export_request = {
            "job_ids": [sample_job.id],
            "format": "txt",
            "include_content": True,
        }
        response = await async_client.post("/api/jobs/export/bulk", json=export_request)

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

    @pytest.mark.asyncio
    async def test_export_with_filters(self, async_client: AsyncClient):
        """Test exporting jobs with filters instead of job IDs"""
        export_request = {
            "format": "json",
            "filters": {
                "classification": ["EX-01"],
                "language": ["en"],
            },
        }
        response = await async_client.post("/api/jobs/export/bulk", json=export_request)

        assert response.status_code in [200, 404]  # 404 if no jobs match filters


class TestExportFormats:
    """Tests for GET /api/jobs/export/formats endpoint"""

    @pytest.mark.asyncio
    async def test_get_export_formats(self, async_client: AsyncClient):
        """Test retrieving available export formats"""
        response = await async_client.get("/api/jobs/export/formats")

        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert "txt" in data["formats"]
        assert "json" in data["formats"]
        assert "csv" in data["formats"]
        assert "options" in data
