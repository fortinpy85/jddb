"""
Tests for quality API endpoints.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from httpx import AsyncClient, ASGITransport

from jd_ingestion.api.main import app


@pytest.fixture
def mock_quality_service():
    """Mock quality service."""
    service = Mock()
    service.batch_calculate_quality_metrics = AsyncMock()
    service.calculate_quality_metrics_for_job = AsyncMock()
    service.get_quality_report = AsyncMock()
    return service


@pytest.fixture
def api_key_header():
    """Provide API key header for authenticated requests."""
    return {"X-API-Key": "test-api-key"}


@pytest.fixture
def sample_quality_metrics():
    """Sample quality metrics data."""
    return {
        "content_completeness_score": 0.85,
        "section_coverage_score": 0.90,
        "language_quality_score": 0.80,
        "structure_quality_score": 0.95,
        "validation_results": {
            "sections_present": 8,
            "sections_expected": 10,
            "required_fields_complete": True,
            "encoding_issues": False,
            "structure_issues": [],
        },
        "quality_flags": {
            "high_quality": True,
            "needs_review": False,
            "processing_issues": False,
            "content_issues": False,
            "recommendations": [
                "Consider adding missing sections for better completeness",
                "Content quality is excellent",
            ],
        },
    }


@pytest.fixture
def sample_batch_result():
    """Sample batch calculation result."""
    return {
        "total_jobs": 10,
        "successful": 8,
        "failed": 2,
        "errors": ["Job 5: Missing content", "Job 7: Processing error"],
    }


class TestQualityMetricsEndpoints:
    """Test quality metrics endpoints."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_calculate_quality_metrics_success(
        self, mock_service, sample_batch_result, api_key_header
    ):
        """Test successful quality metrics calculation."""
        mock_service.batch_calculate_quality_metrics = AsyncMock(
            return_value=sample_batch_result
        )

        request_data = {"job_ids": [1, 2, 3], "recalculate": False}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/quality/metrics/calculate",
                json=request_data,
                headers=api_key_header,
            )

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"
        assert data["results"]["successful"] == 8
        assert data["results"]["failed"] == 2

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_calculate_quality_metrics_all_jobs(
        self, mock_service, sample_batch_result, api_key_header
    ):
        """Test calculating quality metrics for all jobs."""
        mock_service.batch_calculate_quality_metrics = AsyncMock(
            return_value=sample_batch_result
        )

        request_data = {"job_ids": None, "recalculate": True}  # Calculate for all jobs

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/quality/metrics/calculate",
                json=request_data,
                headers=api_key_header,
            )

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"
        assert "Calculated metrics for 8 jobs" in data["message"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_calculate_quality_metrics_service_error(
        self, mock_service, api_key_header
    ):
        """Test quality metrics calculation with service error."""
        mock_service.batch_calculate_quality_metrics = AsyncMock(
            side_effect=Exception("Service error")
        )

        request_data = {"job_ids": [1, 2, 3], "recalculate": False}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/quality/metrics/calculate",
                json=request_data,
                headers=api_key_header,
            )

        assert response.status_code == 500
        assert "Failed to calculate quality metrics" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_get_job_quality_metrics_success(
        self, mock_service, sample_quality_metrics, api_key_header
    ):
        """Test successful job quality metrics retrieval."""
        mock_service.calculate_quality_metrics_for_job = AsyncMock(
            return_value=sample_quality_metrics
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/quality/metrics/123", headers=api_key_header)

        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == 123
        assert data["status"] == "success"
        assert data["metrics"]["content_completeness_score"] == 0.85

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_get_job_quality_metrics_not_found(
        self, mock_service, api_key_header
    ):
        """Test job quality metrics retrieval for non-existent job."""
        mock_service.calculate_quality_metrics_for_job = AsyncMock(
            side_effect=ValueError("Job not found")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/quality/metrics/999", headers=api_key_header)

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_get_job_quality_metrics_service_error(
        self, mock_service, api_key_header
    ):
        """Test job quality metrics retrieval with service error."""
        mock_service.calculate_quality_metrics_for_job = AsyncMock(
            side_effect=Exception("Database error")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/quality/metrics/123", headers=api_key_header)

        assert response.status_code == 500
        assert "Failed to retrieve quality metrics" in response.json()["detail"]


class TestQualityReportEndpoints:
    """Test quality report endpoints."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_generate_quality_report_for_job(self, mock_service, api_key_header):
        """Test generating quality report for specific job."""
        mock_report = {
            "job_id": 123,
            "overall_score": 0.85,
            "sections_analysis": {
                "total_sections": 8,
                "missing_sections": ["nature_and_scope"],
                "quality_scores": {"general_accountability": 0.9},
            },
            "content_analysis": {
                "word_count": 1500,
                "readability_score": 0.8,
                "language_issues": [],
            },
            "recommendations": ["Add missing nature and scope section"],
        }
        mock_service.get_quality_report = AsyncMock(return_value=mock_report)

        request_data = {"job_id": 123, "include_details": True}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/quality/report", json=request_data, headers=api_key_header
            )

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["report"]["job_id"] == 123
        assert data["report"]["overall_score"] == 0.85

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_generate_quality_report_system_wide(
        self, mock_service, api_key_header
    ):
        """Test generating system-wide quality report."""
        mock_report = {
            "overview": {
                "total_jobs": 100,
                "average_quality_score": 0.78,
                "high_quality_jobs": 65,
                "jobs_needing_review": 20,
            },
            "quality_distribution": [
                {"score_range": "0.9-1.0", "count": 25},
                {"score_range": "0.8-0.9", "count": 40},
                {"score_range": "0.7-0.8", "count": 20},
                {"score_range": "0.6-0.7", "count": 10},
                {"score_range": "0.0-0.6", "count": 5},
            ],
            "common_issues": [
                {"issue": "Missing sections", "frequency": 35},
                {"issue": "Language quality", "frequency": 15},
            ],
        }
        mock_service.get_quality_report = AsyncMock(return_value=mock_report)

        request_data = {"job_id": None, "include_details": False}  # System-wide report

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/quality/report", json=request_data, headers=api_key_header
            )

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["report"]["overview"]["total_jobs"] == 100

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_generate_quality_report_invalid_request(
        self, mock_service, api_key_header
    ):
        """Test quality report generation with invalid request."""
        mock_service.get_quality_report = AsyncMock(
            side_effect=ValueError("Invalid job ID")
        )

        request_data = {"job_id": -1, "include_details": True}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/quality/report", json=request_data, headers=api_key_header
            )

        assert response.status_code == 404
        assert "Invalid job ID" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_get_quality_overview_success(self, mock_service, api_key_header):
        """Test successful quality overview retrieval."""
        mock_overview = {
            "overview": {
                "total_jobs": 150,
                "average_quality_score": 0.82,
                "jobs_with_high_quality": 95,
                "jobs_needing_attention": 25,
            },
            "quality_trends": [
                {"date": "2024-01-01", "avg_score": 0.80},
                {"date": "2024-01-02", "avg_score": 0.82},
            ],
        }
        mock_service.get_quality_report = AsyncMock(return_value=mock_overview)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/quality/overview", headers=api_key_header)

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["overview"]["overview"]["total_jobs"] == 150

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_get_quality_overview_error(self, mock_service, api_key_header):
        """Test quality overview with service error."""
        mock_service.get_quality_report = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/quality/overview", headers=api_key_header)

        assert response.status_code == 500
        assert "Failed to generate quality overview" in response.json()["detail"]


class TestQualityValidationEndpoints:
    """Test quality validation endpoints."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_validate_job_content_success(
        self, mock_service, sample_quality_metrics, api_key_header
    ):
        """Test successful job content validation."""
        mock_service.calculate_quality_metrics_for_job = AsyncMock(
            return_value=sample_quality_metrics
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/quality/validation/123", headers=api_key_header
            )

        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == 123
        assert data["validation_status"] == "completed"
        assert data["overall_score"] == 0.85
        assert len(data["recommendations"]) == 2

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_validate_job_content_not_found(self, mock_service, api_key_header):
        """Test job content validation for non-existent job."""
        mock_service.calculate_quality_metrics_for_job = AsyncMock(
            side_effect=ValueError("Job not found")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/quality/validation/999", headers=api_key_header
            )

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_batch_validate_jobs_success(
        self, mock_service, sample_batch_result, api_key_header
    ):
        """Test successful batch job validation."""
        mock_service.batch_calculate_quality_metrics = AsyncMock(
            return_value=sample_batch_result
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/quality/batch/validate",
                params={"job_ids": [1, 2, 3, 4, 5]},
                headers=api_key_header,
            )

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"
        assert data["validation_summary"]["total_jobs"] == 10
        assert data["validation_summary"]["successful_validations"] == 8
        assert data["validation_summary"]["failed_validations"] == 2

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_batch_validate_jobs_all(
        self, mock_service, sample_batch_result, api_key_header
    ):
        """Test batch validation for all jobs."""
        mock_service.batch_calculate_quality_metrics = AsyncMock(
            return_value=sample_batch_result
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/quality/batch/validate", headers=api_key_header
            )

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"
        # Should use batch_calculate_quality_metrics with job_ids=None

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_batch_validate_jobs_error(self, mock_service, api_key_header):
        """Test batch validation with service error."""
        mock_service.batch_calculate_quality_metrics = AsyncMock(
            side_effect=Exception("Batch processing failed")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/quality/batch/validate",
                params={"job_ids": [1, 2, 3]},
                headers=api_key_header,
            )

        assert response.status_code == 500
        assert "Batch validation failed" in response.json()["detail"]


class TestQualityDistributionEndpoint:
    """Test quality distribution endpoint."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_get_quality_distribution_default_metric(
        self, mock_service, api_key_header
    ):
        """Test quality distribution with default metric."""
        mock_overview = {
            "quality_distribution": [
                {"score_range": "0.9-1.0", "count": 30, "percentage": 30.0},
                {"score_range": "0.8-0.9", "count": 45, "percentage": 45.0},
                {"score_range": "0.7-0.8", "count": 20, "percentage": 20.0},
                {"score_range": "0.0-0.7", "count": 5, "percentage": 5.0},
            ],
            "overview": {
                "total_jobs": 100,
                "average_score": 0.85,
                "median_score": 0.82,
            },
        }
        mock_service.get_quality_report = AsyncMock(return_value=mock_overview)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/quality/stats/distribution", headers=api_key_header
            )

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["metric"] == "content_completeness_score"
        assert len(data["distribution"]) == 4
        assert data["overview"]["total_jobs"] == 100

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_get_quality_distribution_custom_metric(
        self, mock_service, api_key_header
    ):
        """Test quality distribution with custom metric."""
        mock_overview = {
            "quality_distribution": [
                {"score_range": "0.9-1.0", "count": 25},
                {"score_range": "0.8-0.9", "count": 50},
            ],
            "overview": {"total_jobs": 75, "average_score": 0.87},
        }
        mock_service.get_quality_report = AsyncMock(return_value=mock_overview)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/quality/stats/distribution?metric=language_quality_score",
                headers=api_key_header,
            )

        assert response.status_code == 200

        data = response.json()
        assert data["metric"] == "language_quality_score"
        assert len(data["distribution"]) == 2

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_get_quality_distribution_error(self, mock_service, api_key_header):
        """Test quality distribution with service error."""
        mock_service.get_quality_report = AsyncMock(
            side_effect=Exception("Distribution calculation failed")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/quality/stats/distribution?metric=invalid_metric",
                headers=api_key_header,
            )

        assert response.status_code == 500
        assert "Failed to generate quality distribution" in response.json()["detail"]


class TestQualityRecommendationsEndpoint:
    """Test quality recommendations endpoint."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_get_quality_recommendations_high_quality(
        self, mock_service, api_key_header
    ):
        """Test quality recommendations for high-quality job."""
        mock_metrics = {
            "content_completeness_score": 0.95,
            "quality_flags": {
                "high_quality": True,
                "needs_review": False,
                "processing_issues": False,
                "content_issues": False,
                "recommendations": [
                    "Content quality is excellent",
                    "No immediate action required",
                ],
            },
        }
        mock_service.calculate_quality_metrics_for_job = AsyncMock(
            return_value=mock_metrics
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/quality/recommendations/123", headers=api_key_header
            )

        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == 123
        assert data["high_quality"] is True
        assert data["needs_review"] is False
        assert data["priority"] == "low"
        assert len(data["recommendations"]) == 2

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_get_quality_recommendations_needs_review(
        self, mock_service, api_key_header
    ):
        """Test quality recommendations for job needing review."""
        mock_metrics = {
            "content_completeness_score": 0.65,
            "quality_flags": {
                "high_quality": False,
                "needs_review": True,
                "processing_issues": False,
                "content_issues": True,
                "recommendations": [
                    "Add missing required sections",
                    "Improve content clarity and completeness",
                    "Review language quality and consistency",
                ],
            },
        }
        mock_service.calculate_quality_metrics_for_job = AsyncMock(
            return_value=mock_metrics
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/quality/recommendations/456", headers=api_key_header
            )

        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == 456
        assert data["high_quality"] is False
        assert data["needs_review"] is True
        assert data["content_issues"] is True
        assert data["priority"] == "medium"
        assert len(data["recommendations"]) == 3

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_get_quality_recommendations_processing_issues(
        self, mock_service, api_key_header
    ):
        """Test quality recommendations for job with processing issues."""
        mock_metrics = {
            "content_completeness_score": 0.30,
            "quality_flags": {
                "high_quality": False,
                "needs_review": True,
                "processing_issues": True,
                "content_issues": True,
                "recommendations": [
                    "URGENT: Re-process this job description",
                    "Check for encoding or parsing errors",
                    "Verify source document integrity",
                ],
            },
        }
        mock_service.calculate_quality_metrics_for_job = AsyncMock(
            return_value=mock_metrics
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/quality/recommendations/789", headers=api_key_header
            )

        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == 789
        assert data["processing_issues"] is True
        assert data["priority"] == "high"
        assert "URGENT" in data["recommendations"][0]

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_get_quality_recommendations_not_found(
        self, mock_service, api_key_header
    ):
        """Test quality recommendations for non-existent job."""
        mock_service.calculate_quality_metrics_for_job = AsyncMock(
            side_effect=ValueError("Job not found")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/quality/recommendations/999", headers=api_key_header
            )

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_get_quality_recommendations_service_error(
        self, mock_service, api_key_header
    ):
        """Test quality recommendations with service error."""
        mock_service.calculate_quality_metrics_for_job = AsyncMock(
            side_effect=Exception("Metrics calculation failed")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/quality/recommendations/123", headers=api_key_header
            )

        assert response.status_code == 500
        assert "Failed to generate recommendations" in response.json()["detail"]


class TestQualityEndpointsValidation:
    """Test request validation for quality endpoints."""

    @pytest.mark.asyncio
    async def test_quality_metrics_request_validation(self, api_key_header):
        """Test quality metrics request validation."""
        # Valid request
        _valid_request = {"job_ids": [1, 2, 3], "recalculate": True}

        # Invalid request with wrong types
        invalid_request = {
            "job_ids": "not_a_list",  # Should be list
            "recalculate": "not_a_boolean",  # Should be boolean
        }

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/quality/metrics/calculate",
                json=invalid_request,
                headers=api_key_header,
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_quality_report_request_validation(self, api_key_header):
        """Test quality report request validation."""
        # Invalid job_id type
        invalid_request = {"job_id": "not_an_int", "include_details": True}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/quality/report", json=invalid_request, headers=api_key_header
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_batch_validate_invalid_parameters(
        self, mock_service, api_key_header
    ):
        """Test batch validation with invalid parameters."""
        # Mock the service to avoid actual processing
        mock_service.batch_calculate_quality_metrics = AsyncMock(
            return_value={"total_jobs": 0, "successful": 0, "failed": 0, "errors": []}
        )

        # The endpoint accepts job_ids in body (not query params)
        # Passing query params doesn't cause validation error, it just gets ignored
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/quality/batch/validate",
                params={"job_ids": "invalid"},
                headers=api_key_header,
            )

        # Since query params are ignored and job_ids=None is valid, this succeeds
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_quality_distribution_invalid_metric(self, api_key_header):
        """Test quality distribution with potentially invalid metric names."""
        # The endpoint should handle any metric name gracefully
        with patch(
            "jd_ingestion.api.endpoints.quality.quality_service"
        ) as mock_service:
            mock_service.get_quality_report = AsyncMock(
                return_value={"quality_distribution": [], "overview": {}}
            )

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get(
                    "/api/quality/stats/distribution?metric=nonexistent_metric",
                    headers=api_key_header,
                )

            assert response.status_code == 200  # Should succeed but return empty data


class TestQualityEndpointsIntegration:
    """Test integration aspects of quality endpoints."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.quality.quality_service")
    async def test_quality_endpoints_database_session_handling(
        self, mock_service, api_key_header
    ):
        """Test proper database session handling."""
        # Mock the service method to return expected data
        mock_service.calculate_quality_metrics_for_job = AsyncMock(
            return_value={
                "content_completeness_score": 0.8,
                "quality_flags": {"high_quality": True, "recommendations": []},
            }
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/quality/metrics/123", headers=api_key_header)

        assert response.status_code == 200

        # Verify the service was called (database session handling is internal to the endpoint)
        # We can't easily mock the session object, so just verify the call happened
        mock_service.calculate_quality_metrics_for_job.assert_called_once()
        call_args = mock_service.calculate_quality_metrics_for_job.call_args
        # First arg should be a database session, second should be job_id
        assert call_args[0][1] == 123

    @pytest.mark.asyncio
    async def test_quality_endpoints_error_response_format(self, api_key_header):
        """Test that error responses follow consistent format."""
        with patch(
            "jd_ingestion.api.endpoints.quality.quality_service"
        ) as mock_service:
            mock_service.calculate_quality_metrics_for_job = AsyncMock(
                side_effect=Exception("Test error")
            )

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get(
                    "/api/quality/metrics/123", headers=api_key_header
                )

            assert response.status_code == 500

            error_data = response.json()
            assert "detail" in error_data
            assert "Failed to retrieve quality metrics" in error_data["detail"]
            assert "Test error" in error_data["detail"]
