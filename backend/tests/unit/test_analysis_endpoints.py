"""
Tests for job analysis API endpoints.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from jd_ingestion.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_job_analysis_service():
    """Mock job analysis service."""
    service = Mock()
    service.compare_jobs = AsyncMock()
    service.analyze_skill_gap = AsyncMock()
    service.get_career_recommendations = AsyncMock()
    service.batch_compare_jobs = AsyncMock()
    return service


class TestJobAnalysisEndpoints:
    """Test job analysis endpoints."""

    @patch("jd_ingestion.api.endpoints.analysis.job_analysis_service")
    def test_compare_jobs_success(self, mock_service, client):
        """Test successful job comparison."""
        mock_service.compare_jobs = AsyncMock(
            return_value={
                "job_a_id": 1,
                "job_b_id": 2,
                "similarity_score": 0.85,
                "comparison_type": "similarity",
                "details": {
                    "section_similarities": {
                        "general_accountability": 0.90,
                        "specific_accountabilities": 0.80,
                    }
                },
            }
        )

        comparison_data = {
            "job_a_id": 1,
            "job_b_id": 2,
            "comparison_types": ["similarity"],
            "include_details": True,
        }

        response = client.post("/api/analysis/compare", json=comparison_data)
        assert response.status_code == 200

        data = response.json()
        assert data["similarity_score"] == 0.85
        assert "details" in data

    @patch("jd_ingestion.api.endpoints.analysis.job_analysis_service")
    def test_compare_jobs_not_found(self, mock_service, client):
        """Test job comparison with non-existent job."""
        mock_service.compare_jobs = AsyncMock(return_value=None)

        comparison_data = {"job_a_id": 999, "job_b_id": 1000}

        response = client.post("/api/analysis/compare", json=comparison_data)
        assert response.status_code == 404

    @patch("jd_ingestion.api.endpoints.analysis.job_analysis_service")
    def test_compare_jobs_invalid_data(self, mock_service, client):
        """Test job comparison with invalid data."""
        comparison_data = {"job_a_id": "invalid", "job_b_id": 2}  # Should be int

        response = client.post("/api/analysis/compare", json=comparison_data)
        assert response.status_code == 422

    @patch("jd_ingestion.api.endpoints.analysis.job_analysis_service")
    def test_analyze_skill_gap_success(self, mock_service, client):
        """Test successful skill gap analysis."""
        mock_service.analyze_skill_gap = AsyncMock(
            return_value={
                "current_job_id": 1,
                "target_job_id": 2,
                "skill_gaps": [
                    {
                        "skill": "Python Programming",
                        "current_level": "intermediate",
                        "required_level": "advanced",
                        "gap_score": 0.3,
                    }
                ],
                "development_suggestions": [
                    "Complete advanced Python certification",
                    "Work on machine learning projects",
                ],
            }
        )

        skill_gap_data = {"job_a_id": 1, "job_b_id": 2, "include_suggestions": True}

        response = client.post("/api/analysis/skill-gap", json=skill_gap_data)
        assert response.status_code == 200

        data = response.json()
        assert len(data["skill_gaps"]) == 1
        assert len(data["development_suggestions"]) == 2

    @patch("jd_ingestion.api.endpoints.analysis.job_analysis_service")
    def test_get_career_recommendations_success(self, mock_service, client):
        """Test successful career path recommendations."""
        mock_service.get_career_recommendations = AsyncMock(
            return_value={
                "current_job_id": 1,
                "recommendations": [
                    {
                        "target_job_id": 2,
                        "target_job_title": "Senior Data Scientist",
                        "feasibility_score": 0.85,
                        "progression_type": "vertical",
                        "timeline_months": 12,
                        "key_requirements": [
                            "Advanced statistics knowledge",
                            "Machine learning expertise",
                        ],
                    }
                ],
                "total_recommendations": 1,
            }
        )

        response = client.get("/api/analysis/career-recommendations/1")
        assert response.status_code == 200

        data = response.json()
        assert len(data["recommendations"]) == 1
        assert data["recommendations"][0]["feasibility_score"] == 0.85

    @patch("jd_ingestion.api.endpoints.analysis.job_analysis_service")
    def test_get_career_recommendations_with_filters(self, mock_service, client):
        """Test career recommendations with query filters."""
        mock_service.get_career_recommendations = AsyncMock(
            return_value={
                "current_job_id": 1,
                "recommendations": [],
                "total_recommendations": 0,
            }
        )

        response = client.get(
            "/api/analysis/career-recommendations/1?min_feasibility=0.8&limit=5"
        )
        assert response.status_code == 200

    @patch("jd_ingestion.api.endpoints.analysis.job_analysis_service")
    def test_batch_compare_jobs_success(self, mock_service, client):
        """Test successful batch job comparison."""
        mock_service.batch_compare_jobs = AsyncMock(
            return_value={
                "base_job_id": 1,
                "comparisons": [
                    {
                        "job_id": 2,
                        "similarity_score": 0.85,
                        "comparison_type": "similarity",
                    },
                    {
                        "job_id": 3,
                        "similarity_score": 0.72,
                        "comparison_type": "similarity",
                    },
                ],
                "total_comparisons": 2,
            }
        )

        batch_data = {
            "base_job_id": 1,
            "comparison_job_ids": [2, 3],
            "comparison_type": "similarity",
            "limit": 10,
        }

        response = client.post("/api/analysis/batch-compare", json=batch_data)
        assert response.status_code == 200

        data = response.json()
        assert len(data["comparisons"]) == 2
        assert data["base_job_id"] == 1

    @patch("jd_ingestion.api.endpoints.analysis.job_analysis_service")
    def test_batch_compare_limit_validation(self, mock_service, client):
        """Test batch comparison with limit validation."""
        batch_data = {
            "base_job_id": 1,
            "comparison_job_ids": list(range(2, 100)),  # Too many IDs
            "limit": 100,  # Exceeds max limit of 50
        }

        response = client.post("/api/analysis/batch-compare", json=batch_data)
        assert response.status_code == 422

    @patch("jd_ingestion.api.endpoints.analysis.job_analysis_service")
    def test_compare_jobs_service_error(self, mock_service, client):
        """Test handling service errors in job comparison."""
        mock_service.compare_jobs = AsyncMock(side_effect=Exception("Service error"))

        comparison_data = {"job_a_id": 1, "job_b_id": 2}

        response = client.post("/api/analysis/compare", json=comparison_data)
        assert response.status_code == 500

    @patch("jd_ingestion.api.endpoints.analysis.job_analysis_service")
    def test_skill_gap_analysis_no_suggestions(self, mock_service, client):
        """Test skill gap analysis without development suggestions."""
        mock_service.analyze_skill_gap = AsyncMock(
            return_value={
                "current_job_id": 1,
                "target_job_id": 2,
                "skill_gaps": [],
                "development_suggestions": [],
            }
        )

        skill_gap_data = {"job_a_id": 1, "job_b_id": 2, "include_suggestions": False}

        response = client.post("/api/analysis/skill-gap", json=skill_gap_data)
        assert response.status_code == 200

        data = response.json()
        assert len(data["skill_gaps"]) == 0
        assert len(data["development_suggestions"]) == 0

    @patch("jd_ingestion.api.endpoints.analysis.job_analysis_service")
    def test_career_recommendations_not_found(self, mock_service, client):
        """Test career recommendations for non-existent job."""
        mock_service.get_career_recommendations = AsyncMock(return_value=None)

        response = client.get("/api/analysis/career-recommendations/999")
        assert response.status_code == 404

    def test_job_comparison_request_validation(self):
        """Test JobComparisonRequest model validation."""
        from jd_ingestion.api.endpoints.analysis import JobComparisonRequest

        # Valid request
        valid_request = JobComparisonRequest(
            job_a_id=1,
            job_b_id=2,
            comparison_types=["similarity", "skill_gap"],
            include_details=True,
        )
        assert valid_request.job_a_id == 1
        assert len(valid_request.comparison_types) == 2

        # Default values
        minimal_request = JobComparisonRequest(job_a_id=1, job_b_id=2)
        assert minimal_request.comparison_types == [
            "similarity",
            "skill_gap",
            "requirements",
        ]
        assert minimal_request.include_details is True

    def test_batch_comparison_request_validation(self):
        """Test BatchComparisonRequest model validation."""
        from jd_ingestion.api.endpoints.analysis import BatchComparisonRequest

        # Valid request
        valid_request = BatchComparisonRequest(
            base_job_id=1,
            comparison_job_ids=[2, 3, 4],
            comparison_type="similarity",
            limit=10,
        )
        assert valid_request.base_job_id == 1
        assert len(valid_request.comparison_job_ids) == 3

        # Test limit validation (should be ≤ 50)
        with pytest.raises(ValueError):
            BatchComparisonRequest(base_job_id=1, comparison_job_ids=[2, 3], limit=100)

    def test_skill_gap_request_validation(self):
        """Test SkillGapRequest model validation."""
        from jd_ingestion.api.endpoints.analysis import SkillGapRequest

        # Valid request
        valid_request = SkillGapRequest(
            job_a_id=1, job_b_id=2, include_suggestions=True
        )
        assert valid_request.job_a_id == 1
        assert valid_request.include_suggestions is True

        # Default values
        minimal_request = SkillGapRequest(job_a_id=1, job_b_id=2)
        assert minimal_request.include_suggestions is True


class TestAnalysisEndpointsIntegration:
    """Integration tests for analysis endpoints."""

    @patch("jd_ingestion.api.endpoints.analysis.get_async_session")
    @patch("jd_ingestion.api.endpoints.analysis.job_analysis_service")
    def test_compare_jobs_with_database(self, mock_service, mock_get_session, client):
        """Test job comparison with database session."""
        mock_db = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_db

        mock_service.compare_jobs = AsyncMock(
            return_value={"job_a_id": 1, "job_b_id": 2, "similarity_score": 0.75}
        )

        comparison_data = {"job_a_id": 1, "job_b_id": 2}

        response = client.post("/api/analysis/compare", json=comparison_data)
        assert response.status_code == 200

    @patch("jd_ingestion.api.endpoints.analysis.job_analysis_service")
    def test_multiple_comparison_types(self, mock_service, client):
        """Test job comparison with multiple analysis types."""
        mock_service.compare_jobs = AsyncMock(
            return_value={
                "job_a_id": 1,
                "job_b_id": 2,
                "similarity_score": 0.85,
                "skill_gap_analysis": {"gaps": 3},
                "requirements_match": {"match_percentage": 0.78},
            }
        )

        comparison_data = {
            "job_a_id": 1,
            "job_b_id": 2,
            "comparison_types": ["similarity", "skill_gap", "requirements"],
            "include_details": True,
        }

        response = client.post("/api/analysis/compare", json=comparison_data)
        assert response.status_code == 200

        data = response.json()
        assert "similarity_score" in data
        assert "skill_gap_analysis" in data
        assert "requirements_match" in data
