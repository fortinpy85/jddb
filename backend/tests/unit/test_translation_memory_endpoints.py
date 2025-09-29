"""
Tests for translation memory API endpoints.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient

from jd_ingestion.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_tm_service():
    """Mock translation memory service."""
    service = Mock()
    service.create_project = Mock()
    service.add_translation_memory = Mock()
    service.get_translation_suggestions = Mock()
    service.search_similar_translations = Mock()
    service.update_usage_stats = Mock()
    service.get_project_statistics = Mock()
    return service


@pytest.fixture
def sample_project_data():
    """Sample project data."""
    return {
        "name": "Government Job Descriptions",
        "description": "Translation project for government job descriptions",
        "source_language": "en",
        "target_language": "fr",
        "project_type": "job_descriptions",
    }


@pytest.fixture
def sample_translation_data():
    """Sample translation data."""
    return {
        "source_text": "Data Scientist responsible for analysis",
        "target_text": "Scientifique des données responsable de l'analyse",
        "source_language": "en",
        "target_language": "fr",
        "domain": "technology",
        "subdomain": "data_science",
        "quality_score": 0.95,
        "confidence_score": 0.90,
        "metadata": {"context": "job_title", "reviewed": True},
    }


@pytest.fixture
def mock_project():
    """Mock project object."""
    project = Mock()
    project.id = 1
    project.name = "Test Project"
    project.description = "Test Description"
    project.source_language = "en"
    project.target_language = "fr"
    project.project_type = "job_descriptions"
    project.status = "active"
    project.created_at = datetime(2024, 1, 1, 12, 0, 0)
    return project


@pytest.fixture
def mock_translation():
    """Mock translation memory entry."""
    tm_entry = Mock()
    tm_entry.id = 1
    tm_entry.source_text = "Data Scientist"
    tm_entry.target_text = "Scientifique des données"
    tm_entry.source_language = "en"
    tm_entry.target_language = "fr"
    tm_entry.domain = "technology"
    tm_entry.subdomain = "data_science"
    tm_entry.quality_score = 0.95
    tm_entry.confidence_score = 0.90
    tm_entry.usage_count = 5
    tm_entry.created_at = datetime(2024, 1, 1, 12, 0, 0)
    return tm_entry


class TestTranslationProjectEndpoints:
    """Test translation project management endpoints."""

    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_create_project_success(
        self, mock_service, client, sample_project_data, mock_project
    ):
        """Test successful project creation."""
        mock_service.create_project.return_value = mock_project

        response = client.post(
            "/api/translation-memory/projects", json=sample_project_data
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["project"]["id"] == 1
        assert data["project"]["name"] == "Test Project"
        assert data["project"]["source_language"] == "en"
        assert data["project"]["target_language"] == "fr"

    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_create_project_service_error(
        self, mock_service, client, sample_project_data
    ):
        """Test project creation with service error."""
        mock_service.create_project.side_effect = Exception("Database error")

        response = client.post(
            "/api/translation-memory/projects", json=sample_project_data
        )
        assert response.status_code == 500
        assert "Failed to create translation project" in response.json()["detail"]

    def test_create_project_validation_error(self, client):
        """Test project creation with validation errors."""
        invalid_data = {
            "name": "",  # Empty name
            "source_language": "invalid_long_language_code",  # Too long
            "target_language": "fr",
            # Missing required fields
        }

        response = client.post("/api/translation-memory/projects", json=invalid_data)
        assert response.status_code == 422

    def test_list_projects_success(self, client):
        """Test successful project listing."""
        with patch(
            "jd_ingestion.api.endpoints.translation_memory.get_db"
        ) as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            # Mock query
            mock_query = Mock()
            mock_query.count.return_value = 2
            mock_query.offset.return_value.limit.return_value.all.return_value = [
                Mock(
                    id=1,
                    name="Project 1",
                    description="Description 1",
                    source_language="en",
                    target_language="fr",
                    project_type="job_descriptions",
                    status="active",
                    created_at=datetime(2024, 1, 1, 12, 0, 0),
                ),
                Mock(
                    id=2,
                    name="Project 2",
                    description="Description 2",
                    source_language="fr",
                    target_language="en",
                    project_type="job_descriptions",
                    status="active",
                    created_at=datetime(2024, 1, 2, 12, 0, 0),
                ),
            ]
            mock_db.query.return_value = mock_query

            response = client.get("/api/translation-memory/projects?skip=0&limit=10")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["total"] == 2
            assert len(data["projects"]) == 2
            assert data["projects"][0]["name"] == "Project 1"

    def test_list_projects_with_pagination(self, client):
        """Test project listing with pagination parameters."""
        with patch(
            "jd_ingestion.api.endpoints.translation_memory.get_db"
        ) as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            mock_query = Mock()
            mock_query.count.return_value = 100
            mock_query.offset.return_value.limit.return_value.all.return_value = []
            mock_db.query.return_value = mock_query

            response = client.get("/api/translation-memory/projects?skip=20&limit=5")
            assert response.status_code == 200

            data = response.json()
            assert data["skip"] == 20
            assert data["limit"] == 5
            assert data["total"] == 100

    def test_list_projects_error(self, client):
        """Test project listing with database error."""
        with patch(
            "jd_ingestion.api.endpoints.translation_memory.get_db"
        ) as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")

            response = client.get("/api/translation-memory/projects")
            assert response.status_code == 500
            assert "Failed to list translation projects" in response.json()["detail"]


class TestTranslationMemoryEndpoints:
    """Test translation memory management endpoints."""

    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_add_translation_success(
        self, mock_service, client, sample_translation_data, mock_translation
    ):
        """Test successful translation addition."""
        mock_service.add_translation_memory.return_value = mock_translation

        response = client.post(
            "/api/translation-memory/projects/1/translations",
            json=sample_translation_data,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["translation"]["id"] == 1
        assert data["translation"]["source_text"] == "Data Scientist"
        assert data["translation"]["target_text"] == "Scientifique des données"
        assert data["translation"]["quality_score"] == 0.95

    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_add_translation_service_error(
        self, mock_service, client, sample_translation_data
    ):
        """Test translation addition with service error."""
        mock_service.add_translation_memory.side_effect = Exception(
            "Translation creation failed"
        )

        response = client.post(
            "/api/translation-memory/projects/1/translations",
            json=sample_translation_data,
        )
        assert response.status_code == 500
        assert "Failed to add translation" in response.json()["detail"]

    def test_add_translation_validation_error(self, client):
        """Test translation addition with validation errors."""
        invalid_data = {
            "source_text": "",  # Empty text
            "target_text": "Valid translation",
            "source_language": "invalid_long_code",  # Too long
            "target_language": "fr",
            "quality_score": 1.5,  # Out of range
            "confidence_score": -0.1,  # Out of range
        }

        response = client.post(
            "/api/translation-memory/projects/1/translations", json=invalid_data
        )
        assert response.status_code == 422


class TestTranslationSuggestionsEndpoints:
    """Test translation suggestion endpoints."""

    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_get_translation_suggestions_success(self, mock_service, client):
        """Test successful translation suggestions retrieval."""
        mock_suggestions = [
            {
                "id": 1,
                "source_text": "Data Scientist",
                "target_text": "Scientifique des données",
                "similarity_score": 0.95,
                "quality_score": 0.90,
                "usage_count": 10,
            },
            {
                "id": 2,
                "source_text": "Data Analyst",
                "target_text": "Analyste de données",
                "similarity_score": 0.85,
                "quality_score": 0.88,
                "usage_count": 5,
            },
        ]
        mock_service.get_translation_suggestions.return_value = mock_suggestions

        request_data = {
            "source_text": "Senior Data Scientist",
            "source_language": "en",
            "target_language": "fr",
            "project_id": 1,
            "context": "job_title",
        }

        response = client.post("/api/translation-memory/suggestions", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert len(data["suggestions"]) == 2
        assert data["suggestions"][0]["similarity_score"] == 0.95

    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_get_translation_suggestions_empty_results(self, mock_service, client):
        """Test translation suggestions with no results."""
        mock_service.get_translation_suggestions.return_value = []

        request_data = {
            "source_text": "Unique specialized term",
            "source_language": "en",
            "target_language": "fr",
        }

        response = client.post("/api/translation-memory/suggestions", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["count"] == 0
        assert len(data["suggestions"]) == 0

    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_get_translation_suggestions_table_not_exists(self, mock_service, client):
        """Test translation suggestions when table doesn't exist."""
        mock_service.get_translation_suggestions.side_effect = Exception(
            'relation "translation_memory" does not exist'
        )

        request_data = {
            "source_text": "Data Scientist",
            "source_language": "en",
            "target_language": "fr",
        }

        response = client.post("/api/translation-memory/suggestions", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["count"] == 0
        assert "warning" in data
        assert "temporarily unavailable" in data["warning"]

    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_get_translation_suggestions_service_error(self, mock_service, client):
        """Test translation suggestions with service error."""
        mock_service.get_translation_suggestions.side_effect = Exception(
            "Service failure"
        )

        request_data = {
            "source_text": "Data Scientist",
            "source_language": "en",
            "target_language": "fr",
        }

        response = client.post("/api/translation-memory/suggestions", json=request_data)
        assert response.status_code == 500
        assert "Failed to get translation suggestions" in response.json()["detail"]


class TestTranslationSearchEndpoints:
    """Test translation search endpoints."""

    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_search_similar_translations_success(self, mock_service, client):
        """Test successful similar translations search."""
        mock_results = [
            {
                "id": 1,
                "source_text": "Machine Learning Engineer",
                "target_text": "Ingénieur en apprentissage automatique",
                "similarity_score": 0.88,
                "project_id": 1,
            },
            {
                "id": 2,
                "source_text": "Software Engineer",
                "target_text": "Ingénieur logiciel",
                "similarity_score": 0.75,
                "project_id": 1,
            },
        ]
        mock_service.search_similar_translations.return_value = mock_results

        response = client.post(
            "/api/translation-memory/search",
            params={
                "query_text": "Senior Software Engineer",
                "source_language": "en",
                "target_language": "fr",
                "project_id": 1,
                "similarity_threshold": 0.7,
                "limit": 10,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert data["query"]["similarity_threshold"] == 0.7
        assert len(data["results"]) == 2

    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_search_similar_translations_with_defaults(self, mock_service, client):
        """Test similar translations search with default parameters."""
        mock_service.search_similar_translations.return_value = []

        response = client.post(
            "/api/translation-memory/search",
            params={
                "query_text": "Project Manager",
                "source_language": "en",
                "target_language": "fr",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["query"]["similarity_threshold"] == 0.7  # default
        assert data["count"] == 0

    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_search_similar_translations_error(self, mock_service, client):
        """Test similar translations search with error."""
        mock_service.search_similar_translations.side_effect = Exception(
            "Search failed"
        )

        response = client.post(
            "/api/translation-memory/search",
            params={
                "query_text": "Manager",
                "source_language": "en",
                "target_language": "fr",
            },
        )
        assert response.status_code == 500
        assert "Failed to search similar translations" in response.json()["detail"]

    def test_search_similar_translations_invalid_parameters(self, client):
        """Test similar translations search with invalid parameters."""
        # Missing required parameters
        response = client.post("/api/translation-memory/search")
        assert response.status_code == 422

        # Invalid similarity threshold
        response = client.post(
            "/api/translation-memory/search",
            params={
                "query_text": "Manager",
                "source_language": "en",
                "target_language": "fr",
                "similarity_threshold": 1.5,  # Invalid range
            },
        )
        assert response.status_code == 422


class TestTranslationUsageEndpoints:
    """Test translation usage tracking endpoints."""

    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_update_translation_usage_success(self, mock_service, client):
        """Test successful translation usage update."""
        request_data = {
            "used_translation": True,
            "user_feedback": {"rating": 5, "comment": "Excellent translation"},
        }

        response = client.put(
            "/api/translation-memory/translations/1/usage", json=request_data
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["translation_id"] == 1
        assert "updated successfully" in data["message"]

    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_update_translation_usage_not_found(self, mock_service, client):
        """Test translation usage update for non-existent translation."""
        mock_service.update_usage_stats.side_effect = ValueError(
            "Translation not found"
        )

        request_data = {"used_translation": False}

        response = client.put(
            "/api/translation-memory/translations/999/usage", json=request_data
        )
        assert response.status_code == 404
        assert "Translation not found" in response.json()["detail"]

    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_update_translation_usage_service_error(self, mock_service, client):
        """Test translation usage update with service error."""
        mock_service.update_usage_stats.side_effect = Exception("Database error")

        request_data = {"used_translation": True}

        response = client.put(
            "/api/translation-memory/translations/1/usage", json=request_data
        )
        assert response.status_code == 500
        assert "Failed to update translation usage" in response.json()["detail"]


class TestProjectStatisticsEndpoints:
    """Test project statistics endpoints."""

    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_get_project_statistics_success(self, mock_service, client):
        """Test successful project statistics retrieval."""
        mock_stats = {
            "project_id": 1,
            "total_translations": 150,
            "total_usage": 450,
            "average_quality_score": 0.87,
            "languages": {"source": ["en", "fr"], "target": ["fr", "en"]},
            "domains": {"technology": 75, "management": 50, "administration": 25},
            "recent_activity": {
                "translations_added_last_week": 12,
                "translations_used_last_week": 89,
            },
        }
        mock_service.get_project_statistics.return_value = mock_stats

        response = client.get("/api/translation-memory/projects/1/statistics")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["statistics"]["total_translations"] == 150
        assert data["statistics"]["average_quality_score"] == 0.87
        assert "domains" in data["statistics"]

    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_get_project_statistics_not_found(self, mock_service, client):
        """Test project statistics for non-existent project."""
        mock_service.get_project_statistics.side_effect = ValueError(
            "Project not found"
        )

        response = client.get("/api/translation-memory/projects/999/statistics")
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_get_project_statistics_service_error(self, mock_service, client):
        """Test project statistics with service error."""
        mock_service.get_project_statistics.side_effect = Exception(
            "Statistics calculation failed"
        )

        response = client.get("/api/translation-memory/projects/1/statistics")
        assert response.status_code == 500
        assert "Failed to get project statistics" in response.json()["detail"]


class TestTranslationMemoryHealthEndpoint:
    """Test translation memory health endpoint."""

    def test_health_check_success(self, client):
        """Test successful health check."""
        response = client.get("/api/translation-memory/health")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["service"] == "Translation Memory"
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "features" in data
        assert len(data["features"]) > 0


class TestTranslationMemoryEndpointsValidation:
    """Test request validation for translation memory endpoints."""

    def test_create_project_request_validation(self):
        """Test CreateProjectRequest validation."""
        from jd_ingestion.api.endpoints.translation_memory import CreateProjectRequest

        # Valid request
        valid_request = CreateProjectRequest(
            name="Test Project",
            description="Test Description",
            source_language="en",
            target_language="fr",
            project_type="job_descriptions",
        )
        assert valid_request.name == "Test Project"
        assert valid_request.source_language == "en"

        # Test field limits
        with pytest.raises(ValueError):
            CreateProjectRequest(
                name="x" * 300,  # Exceeds max_length
                source_language="en",
                target_language="fr",
            )

    def test_add_translation_request_validation(self):
        """Test AddTranslationRequest validation."""
        from jd_ingestion.api.endpoints.translation_memory import AddTranslationRequest

        # Valid request
        valid_request = AddTranslationRequest(
            source_text="Test source",
            target_text="Test target",
            source_language="en",
            target_language="fr",
            quality_score=0.95,
            confidence_score=0.90,
        )
        assert valid_request.quality_score == 0.95

        # Test score validation
        with pytest.raises(ValueError):
            AddTranslationRequest(
                source_text="Test",
                target_text="Test",
                source_language="en",
                target_language="fr",
                quality_score=1.5,  # Exceeds maximum
            )

    def test_translation_suggestion_request_validation(self):
        """Test TranslationSuggestionRequest validation."""
        from jd_ingestion.api.endpoints.translation_memory import (
            TranslationSuggestionRequest,
        )

        # Valid request
        valid_request = TranslationSuggestionRequest(
            source_text="Test text",
            source_language="en",
            target_language="fr",
            project_id=1,
            context="job_title",
        )
        assert valid_request.project_id == 1
        assert valid_request.context == "job_title"

    def test_update_usage_request_validation(self):
        """Test UpdateUsageRequest validation."""
        from jd_ingestion.api.endpoints.translation_memory import UpdateUsageRequest

        # Valid request
        valid_request = UpdateUsageRequest(
            used_translation=True, user_feedback={"rating": 5}
        )
        assert valid_request.used_translation is True
        assert valid_request.user_feedback["rating"] == 5


class TestTranslationMemoryEndpointsIntegration:
    """Test integration aspects of translation memory endpoints."""

    @patch("jd_ingestion.api.endpoints.translation_memory.get_db")
    @patch("jd_ingestion.api.endpoints.translation_memory.tm_service")
    def test_endpoints_database_session_handling(
        self, mock_service, mock_get_db, client, sample_project_data
    ):
        """Test proper database session handling."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_project = Mock()
        mock_project.id = 1
        mock_project.name = "Test"
        mock_project.created_at = datetime.now()
        mock_service.create_project.return_value = mock_project

        response = client.post(
            "/api/translation-memory/projects", json=sample_project_data
        )
        assert response.status_code == 200

        # Verify service was called with database session
        mock_service.create_project.assert_called_once()
        call_kwargs = mock_service.create_project.call_args[1]
        assert call_kwargs["db"] == mock_db

    def test_translation_memory_error_response_format(self, client):
        """Test that error responses follow consistent format."""
        with patch(
            "jd_ingestion.api.endpoints.translation_memory.tm_service"
        ) as mock_service:
            mock_service.create_project.side_effect = Exception("Test error")

            response = client.post(
                "/api/translation-memory/projects",
                json={"name": "Test", "source_language": "en", "target_language": "fr"},
            )
            assert response.status_code == 500

            error_data = response.json()
            assert "detail" in error_data
            assert "Failed to create translation project" in error_data["detail"]
            assert "Test error" in error_data["detail"]

    def test_translation_memory_service_initialization(self):
        """Test that translation memory service is properly initialized."""
        from jd_ingestion.api.endpoints.translation_memory import tm_service

        assert tm_service is not None
