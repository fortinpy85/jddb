"""
Tests for search API endpoints.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta, date
from decimal import Decimal
from fastapi.testclient import TestClient
from fastapi import Request

from jd_ingestion.api.main import app
from jd_ingestion.database.models import (
    JobDescription,
    JobSection,
    JobMetadata,
    ContentChunk,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service."""
    service = Mock()
    service.semantic_search = AsyncMock()
    service.find_similar_chunks = AsyncMock()
    return service


@pytest.fixture
def mock_search_analytics_service():
    """Mock search analytics service."""
    service = Mock()
    service.start_search_session = AsyncMock(return_value="search-session-123")
    service.record_search = AsyncMock()
    service.log_search = AsyncMock()
    return service


@pytest.fixture
def mock_search_recommendations_service():
    """Mock search recommendations service."""
    service = Mock()
    service.get_query_suggestions = AsyncMock()
    service.get_search_recommendations = AsyncMock()
    return service


@pytest.fixture
def mock_cache_service():
    """Mock cache service."""
    service = Mock()
    service.get_cached_search_results = AsyncMock(return_value=None)
    service.cache_search_results = AsyncMock()
    service.get_cached_similar_jobs = AsyncMock(return_value=None)
    service.cache_similar_jobs = AsyncMock()
    return service


@pytest.fixture
def sample_search_query():
    """Sample search query data."""
    return {
        "query": "data scientist python",
        "classification": "EX-01",
        "language": "en",
        "department": "IT",
        "limit": 20,
        "use_semantic_search": True,
    }


@pytest.fixture
def sample_job_data():
    """Sample job data for testing."""
    return {
        "id": 1,
        "job_number": "12345",
        "title": "Data Scientist",
        "classification": "EX-01",
        "language": "en",
        "raw_content": "This is a data scientist position requiring Python skills...",
        "status": "processed",
        "created_at": datetime.now(),
    }


class TestSearchJobsEndpoints:
    """Test search jobs endpoints."""

    @patch("jd_ingestion.api.endpoints.search.search_analytics_service")
    @patch("jd_ingestion.api.endpoints.search.embedding_service")
    def test_search_jobs_get_success(
        self, mock_embedding_service, mock_analytics_service, client
    ):
        """Test successful GET search."""
        mock_analytics_service.start_search_session = AsyncMock(
            return_value="session-123"
        )
        mock_analytics_service.record_search = AsyncMock()
        mock_embedding_service.semantic_search = AsyncMock(
            return_value=[
                {
                    "job_id": 1,
                    "job_number": "12345",
                    "title": "Data Scientist",
                    "classification": "EX-01",
                    "language": "en",
                    "relevance_score": 0.95,
                }
            ]
        )

        with patch(
            "jd_ingestion.api.endpoints.search.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock job query
            mock_job = Mock()
            mock_job.id = 1
            mock_job.raw_content = "Test content"
            mock_result = Mock()
            mock_result.scalar_one.return_value = mock_job
            mock_db.execute.return_value = mock_result

            response = client.get("/api/search/?q=python&classification=EX-01&limit=10")
            assert response.status_code == 200

            data = response.json()
            assert data["query"] == "python"
            assert data["search_type"] == "semantic"
            assert len(data["results"]) == 1

    @patch("jd_ingestion.api.endpoints.search.search_analytics_service")
    @patch("jd_ingestion.api.endpoints.search.embedding_service")
    def test_search_jobs_post_success(
        self,
        mock_embedding_service,
        mock_analytics_service,
        client,
        sample_search_query,
    ):
        """Test successful POST search."""
        mock_analytics_service.start_search_session = AsyncMock(
            return_value="session-123"
        )
        mock_analytics_service.record_search = AsyncMock()
        mock_embedding_service.semantic_search = AsyncMock(return_value=[])

        with patch(
            "jd_ingestion.api.endpoints.search.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            with patch(
                "jd_ingestion.api.endpoints.search._fulltext_search"
            ) as mock_fulltext:
                mock_fulltext.return_value = {
                    "query": "data scientist python",
                    "search_type": "fulltext",
                    "total_results": 0,
                    "results": [],
                }

                response = client.post("/api/search/", json=sample_search_query)
                assert response.status_code == 200

                data = response.json()
                assert data["query"] == "data scientist python"
                assert data["search_type"] == "fulltext"

    @patch("jd_ingestion.api.endpoints.search.embedding_service")
    def test_semantic_search_success(
        self, mock_embedding_service, client, sample_search_query
    ):
        """Test successful semantic search."""
        mock_embedding_service.semantic_search = AsyncMock(
            return_value=[
                {
                    "job_id": 1,
                    "job_number": "12345",
                    "title": "Data Scientist",
                    "classification": "EX-01",
                    "language": "en",
                    "relevance_score": 0.95,
                    "matching_chunks": 3,
                }
            ]
        )

        with patch(
            "jd_ingestion.api.endpoints.search.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock job query
            mock_job = Mock()
            mock_job.raw_content = "Test content with Python and data science"
            mock_result = Mock()
            mock_result.scalar_one.return_value = mock_job
            mock_db.execute.return_value = mock_result

            # Mock sections query
            mock_sections_result = Mock()
            mock_sections_result.scalars.return_value.all.return_value = []
            mock_db.execute.side_effect = [mock_result, mock_sections_result]

            response = client.post("/api/search/semantic", json=sample_search_query)
            assert response.status_code == 200

            data = response.json()
            assert data["search_type"] == "semantic"
            assert len(data["results"]) == 1
            assert data["results"][0]["matching_chunks"] == 3

    @patch("jd_ingestion.api.endpoints.search.embedding_service")
    def test_semantic_search_no_results(
        self, mock_embedding_service, client, sample_search_query
    ):
        """Test semantic search with no results."""
        mock_embedding_service.semantic_search = AsyncMock(return_value=[])

        response = client.post("/api/search/semantic", json=sample_search_query)
        assert response.status_code == 200

        data = response.json()
        assert data["total_results"] == 0
        assert "No semantic matches found" in data["message"]

    def test_search_invalid_parameters(self, client):
        """Test search with invalid parameters."""
        # Missing required query parameter
        response = client.get("/api/search/")
        assert response.status_code == 422

        # Invalid limit
        response = client.get("/api/search/?q=test&limit=200")
        assert response.status_code == 422

        # Invalid POST data
        response = client.post("/api/search/", json={"invalid": "data"})
        assert response.status_code == 422


class TestAdvancedSearchEndpoint:
    """Test advanced search with filters."""

    @patch("jd_ingestion.api.endpoints.search.cache_service")
    @patch("jd_ingestion.api.endpoints.search.search_analytics_service")
    def test_advanced_search_success(
        self, mock_analytics_service, mock_cache_service, client
    ):
        """Test successful advanced search with filters."""
        mock_cache_service.get_cached_search_results = AsyncMock(return_value=None)
        mock_cache_service.cache_search_results = AsyncMock()
        mock_analytics_service.log_search = AsyncMock()

        advanced_query = {
            "query": "senior manager",
            "classification": "EX-02",
            "salary_min": 75000,
            "salary_max": 100000,
            "effective_date_from": "2024-01-01",
            "location": "Ottawa",
            "min_fte": 1,
            "limit": 10,
        }

        with patch(
            "jd_ingestion.api.endpoints.search.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock database query results
            mock_result = Mock()
            mock_row = Mock()
            mock_row.id = 1
            mock_row.job_number = "67890"
            mock_row.title = "Senior Manager"
            mock_row.classification = "EX-02"
            mock_row.language = "en"
            mock_row.status = "processed"
            mock_row.created_at = datetime.now()
            mock_row.salary_budget = 85000
            mock_row.effective_date = date.today()
            mock_row.department = "HR"
            mock_row.location = "Ottawa"
            mock_row.fte_count = 1

            mock_result.fetchall.return_value = [mock_row]
            mock_db.execute.return_value = mock_result

            response = client.post("/api/search/advanced", json=advanced_query)
            assert response.status_code == 200

            data = response.json()
            assert len(data["results"]) == 1
            assert data["results"][0]["job_number"] == "67890"
            assert data["search_method"] == "advanced_filtered_search"
            assert data["filters_applied"]["salary_min"] == 75000

    @patch("jd_ingestion.api.endpoints.search.cache_service")
    def test_advanced_search_cached_results(self, mock_cache_service, client):
        """Test advanced search returning cached results."""
        cached_response = {
            "results": [{"job_id": 1, "title": "Cached Job"}],
            "total_found": 1,
            "query": "test query",
            "search_method": "advanced_filtered_search",
        }
        mock_cache_service.get_cached_search_results = AsyncMock(
            return_value=cached_response
        )

        search_query = {"query": "test query", "classification": "EX-01", "limit": 10}

        response = client.post("/api/search/advanced", json=search_query)
        assert response.status_code == 200

        data = response.json()
        assert data["results"][0]["title"] == "Cached Job"

    def test_advanced_search_invalid_filters(self, client):
        """Test advanced search with invalid filters."""
        invalid_query = {
            "query": "test",
            "salary_min": -1000,  # Invalid negative salary
            "limit": 10,
        }

        response = client.post("/api/search/advanced", json=invalid_query)
        assert response.status_code == 422


class TestFilterStatisticsEndpoint:
    """Test filter statistics endpoint."""

    def test_get_filter_statistics_success(self, client):
        """Test successful filter statistics retrieval."""
        with patch(
            "jd_ingestion.api.endpoints.search.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock salary statistics
            salary_stats = Mock()
            salary_stats.min_salary = Decimal("50000")
            salary_stats.max_salary = Decimal("150000")
            salary_stats.avg_salary = Decimal("85000")
            salary_stats.salary_count = 100

            # Mock date statistics
            date_stats = Mock()
            date_stats.earliest_date = date(2020, 1, 1)
            date_stats.latest_date = date(2024, 12, 31)
            date_stats.date_count = 150

            # Mock FTE statistics
            fte_stats = Mock()
            fte_stats.min_fte = 1
            fte_stats.max_fte = 5
            fte_stats.avg_fte = 2.5
            fte_stats.fte_count = 120

            # Mock distribution data
            dept_row = Mock()
            dept_row.department = "IT"
            dept_row.count = 25

            location_row = Mock()
            location_row.location = "Ottawa"
            location_row.count = 50

            class_row = Mock()
            class_row.classification = "EX-01"
            class_row.count = 75

            lang_row = Mock()
            lang_row.language = "en"
            lang_row.count = 90

            # Setup mock results
            mock_results = [
                Mock(fetchone=Mock(return_value=salary_stats)),
                Mock(fetchone=Mock(return_value=date_stats)),
                Mock(fetchall=Mock(return_value=[dept_row])),
                Mock(fetchall=Mock(return_value=[location_row])),
                Mock(fetchone=Mock(return_value=fte_stats)),
                Mock(fetchall=Mock(return_value=[class_row])),
                Mock(fetchall=Mock(return_value=[lang_row])),
            ]

            mock_db.execute.side_effect = mock_results

            response = client.get("/api/search/filters/stats")
            assert response.status_code == 200

            data = response.json()
            assert data["salary_statistics"]["min_salary"] == 50000.0
            assert data["salary_statistics"]["max_salary"] == 150000.0
            assert len(data["department_distribution"]) == 1
            assert data["department_distribution"][0]["department"] == "IT"

    def test_get_filter_statistics_error(self, client):
        """Test filter statistics with database error."""
        with patch(
            "jd_ingestion.api.endpoints.search.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_db.execute.side_effect = Exception("Database error")

            response = client.get("/api/search/filters/stats")
            assert response.status_code == 500
            assert "Failed to get filter statistics" in response.json()["detail"]


class TestSimilarJobsEndpoint:
    """Test similar jobs endpoint."""

    @patch("jd_ingestion.api.endpoints.search.cache_service")
    @patch("jd_ingestion.api.endpoints.search.optimized_embedding_service")
    def test_find_similar_jobs_success(
        self, mock_optimized_service, mock_cache_service, client
    ):
        """Test successful similar jobs search."""
        mock_cache_service.get_cached_similar_jobs = AsyncMock(return_value=None)
        mock_cache_service.cache_similar_jobs = AsyncMock()

        with patch(
            "jd_ingestion.api.endpoints.search.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock source job
            source_job = Mock()
            source_job.id = 1
            source_job.job_number = "12345"
            source_job.title = "Data Scientist"
            source_job.classification = "EX-01"

            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = source_job
            mock_db.execute.return_value = mock_result

            # Mock content chunks
            mock_chunk = Mock()
            mock_chunk.id = 1
            mock_chunk.embedding = [0.1, 0.2, 0.3]
            mock_chunks_result = Mock()
            mock_chunks_result.scalars.return_value.all.return_value = [mock_chunk]

            # Mock batch similarity results
            mock_optimized_service.batch_similarity_search = AsyncMock(
                return_value=[
                    [
                        {
                            "job_id": 2,
                            "job_number": "67890",
                            "title": "Senior Data Scientist",
                            "classification": "EX-02",
                            "language": "en",
                            "similarity_score": 0.85,
                        }
                    ]
                ]
            )

            mock_db.execute.side_effect = [mock_result, mock_chunks_result]

            response = client.get("/api/search/similar/1?limit=5")
            assert response.status_code == 200

            data = response.json()
            assert data["source_job"]["id"] == 1
            assert len(data["similar_jobs"]) == 1
            assert data["similar_jobs"][0]["similarity_score"] == 0.85
            assert data["search_method"] == "optimized_vector_similarity"

    @patch("jd_ingestion.api.endpoints.search.cache_service")
    def test_find_similar_jobs_cached(self, mock_cache_service, client):
        """Test similar jobs with cached results."""
        cached_result = {
            "source_job": {"id": 1, "title": "Test Job"},
            "similar_jobs": [{"id": 2, "title": "Similar Job"}],
            "total_found": 1,
        }
        mock_cache_service.get_cached_similar_jobs = AsyncMock(
            return_value=cached_result
        )

        response = client.get("/api/search/similar/1")
        assert response.status_code == 200

        data = response.json()
        assert data["similar_jobs"][0]["title"] == "Similar Job"

    def test_find_similar_jobs_not_found(self, client):
        """Test similar jobs with non-existent job."""
        with patch(
            "jd_ingestion.api.endpoints.search.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            response = client.get("/api/search/similar/999")
            assert response.status_code == 404
            assert "Job description not found" in response.json()["detail"]

    def test_find_similar_jobs_invalid_parameters(self, client):
        """Test similar jobs with invalid parameters."""
        # Invalid limit
        response = client.get("/api/search/similar/1?limit=100")
        assert response.status_code == 422

        # Negative limit
        response = client.get("/api/search/similar/1?limit=-1")
        assert response.status_code == 422


class TestJobComparisonEndpoint:
    """Test job comparison endpoint."""

    @patch("jd_ingestion.api.endpoints.search.embedding_service")
    def test_compare_jobs_success(self, mock_embedding_service, client):
        """Test successful job comparison."""
        with patch(
            "jd_ingestion.api.endpoints.search.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock job data
            job1 = Mock()
            job1.id = 1
            job1.job_number = "12345"
            job1.title = "Data Scientist"
            job1.classification = "EX-01"
            job1.language = "en"

            job2 = Mock()
            job2.id = 2
            job2.job_number = "67890"
            job2.title = "Senior Data Scientist"
            job2.classification = "EX-02"
            job2.language = "en"

            # Mock jobs query
            jobs_result = Mock()
            jobs_result.scalars.return_value.all.return_value = [job1, job2]

            # Mock sections query
            section1 = Mock()
            section1.job_id = 1
            section1.section_type = "general_accountability"
            section1.section_content = "Responsible for data analysis"

            section2 = Mock()
            section2.job_id = 2
            section2.section_type = "general_accountability"
            section2.section_content = "Lead data science initiatives"

            sections_result = Mock()
            sections_result.scalars.return_value.all.return_value = [section1, section2]

            # Mock chunks query
            chunks_result = Mock()
            chunks_result.scalars.return_value.all.return_value = []

            mock_db.execute.side_effect = [jobs_result, sections_result, chunks_result]

            response = client.get("/api/search/compare/1/2")
            assert response.status_code == 200

            data = response.json()
            assert data["comparison_id"] == "1_2"
            assert data["jobs"]["job1"]["id"] == 1
            assert data["jobs"]["job2"]["id"] == 2
            assert "similarity_analysis" in data
            assert "recommendations" in data

    def test_compare_jobs_not_found(self, client):
        """Test job comparison with non-existent jobs."""
        with patch(
            "jd_ingestion.api.endpoints.search.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock empty results
            jobs_result = Mock()
            jobs_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = jobs_result

            response = client.get("/api/search/compare/999/1000")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]


class TestSearchFacetsEndpoint:
    """Test search facets endpoint."""

    def test_get_search_facets_success(self, client):
        """Test successful search facets retrieval."""
        with patch(
            "jd_ingestion.api.endpoints.search.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock facet data
            class_row = Mock()
            class_row.classification = "EX-01"
            class_row.count = 50

            lang_row = Mock()
            lang_row.language = "en"
            lang_row.count = 75

            section_row = Mock()
            section_row.section_type = "general_accountability"
            section_row.count = 100

            mock_results = [
                Mock(fetchall=Mock(return_value=[class_row])),
                Mock(fetchall=Mock(return_value=[lang_row])),
                Mock(fetchall=Mock(return_value=[section_row])),
                Mock(scalar=Mock(return_value=500)),  # embedding count
            ]

            mock_db.execute.side_effect = mock_results

            response = client.get("/api/search/facets")
            assert response.status_code == 200

            data = response.json()
            assert len(data["classifications"]) == 1
            assert data["classifications"][0]["value"] == "EX-01"
            assert data["embedding_stats"]["semantic_search_available"] is True

    def test_get_search_facets_error(self, client):
        """Test search facets with database error."""
        with patch(
            "jd_ingestion.api.endpoints.search.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_db.execute.side_effect = Exception("Database error")

            response = client.get("/api/search/facets")
            assert response.status_code == 500
            assert "Failed to retrieve search facets" in response.json()["detail"]


class TestSearchRecommendationsEndpoints:
    """Test search recommendations endpoints."""

    @patch("jd_ingestion.api.endpoints.search.search_recommendations_service")
    def test_get_query_suggestions_success(self, mock_service, client):
        """Test successful query suggestions."""
        mock_suggestions = [
            {"query": "data scientist python", "frequency": 15, "confidence": 0.9},
            {"query": "data analyst", "frequency": 10, "confidence": 0.8},
        ]
        mock_service.get_query_suggestions = AsyncMock(return_value=mock_suggestions)

        response = client.get("/api/search/suggestions?q=data&limit=5")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert data[0]["query"] == "data scientist python"

    def test_get_query_suggestions_short_query(self, client):
        """Test query suggestions with too short query."""
        response = client.get("/api/search/suggestions?q=da")
        assert response.status_code == 422  # Query too short

    @patch("jd_ingestion.api.endpoints.search.search_recommendations_service")
    def test_get_search_recommendations_success(self, mock_service, client):
        """Test successful search recommendations."""
        mock_recommendations = {
            "trending": [{"query": "machine learning", "score": 0.9}],
            "related": [{"query": "artificial intelligence", "score": 0.8}],
            "popular": [{"query": "python developer", "score": 0.7}],
        }
        mock_service.get_search_recommendations = AsyncMock(
            return_value=mock_recommendations
        )

        response = client.get("/api/search/recommendations?query=data science&limit=5")
        assert response.status_code == 200

        data = response.json()
        assert "trending" in data
        assert "metadata" in data
        assert data["metadata"]["total_recommendations"] == 3

    def test_get_trending_searches_success(self, client):
        """Test successful trending searches retrieval."""
        with patch(
            "jd_ingestion.api.endpoints.search.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock trending data
            trending_row = Mock()
            trending_row.query_text = "python developer"
            trending_row.search_count = 25
            trending_row.avg_results = 15.0
            trending_row.unique_sessions = 20

            mock_result = Mock()
            mock_result.fetchall.return_value = [trending_row]
            mock_db.execute.return_value = mock_result

            response = client.get("/api/search/trending?period=24h&limit=10")
            assert response.status_code == 200

            data = response.json()
            assert len(data) == 1
            assert data[0]["query"] == "python developer"
            assert data[0]["search_count"] == 25

    def test_get_trending_searches_invalid_period(self, client):
        """Test trending searches with invalid period."""
        response = client.get("/api/search/trending?period=invalid")
        assert response.status_code == 422

    def test_get_popular_filters_success(self, client):
        """Test successful popular filters retrieval."""
        with patch(
            "jd_ingestion.api.endpoints.search.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock filter data
            class_row = Mock()
            class_row.classification = "EX-01"
            class_row.count = 50

            dept_row = Mock()
            dept_row.department = "IT"
            dept_row.count = 25

            lang_row = Mock()
            lang_row.language = "en"
            lang_row.count = 75

            mock_results = [
                Mock(fetchall=Mock(return_value=[class_row])),
                Mock(fetchall=Mock(return_value=[dept_row])),
                Mock(fetchall=Mock(return_value=[lang_row])),
            ]

            mock_db.execute.side_effect = mock_results

            response = client.get("/api/search/popular-filters?limit=10")
            assert response.status_code == 200

            data = response.json()
            assert "classifications" in data
            assert "departments" in data
            assert "languages" in data
            assert "date_ranges" in data
            assert len(data["classifications"]) == 1
            assert data["classifications"][0]["value"] == "EX-01"


class TestSearchUtilityFunctions:
    """Test search utility functions."""

    def test_extract_snippet_basic(self):
        """Test basic snippet extraction."""
        from jd_ingestion.api.endpoints.search import _extract_snippet

        content = "This is a long piece of content about data science and machine learning algorithms."
        query = "data science"

        snippet = _extract_snippet(content, query, max_length=50)
        assert "data science" in snippet.lower()
        assert len(snippet) <= 53  # max_length + "..."

    def test_extract_snippet_no_match(self):
        """Test snippet extraction when query terms not found."""
        from jd_ingestion.api.endpoints.search import _extract_snippet

        content = "This is content about something completely different."
        query = "data science"

        snippet = _extract_snippet(content, query, max_length=30)
        assert snippet.startswith("This is content")

    def test_calculate_title_similarity(self):
        """Test title similarity calculation."""
        from jd_ingestion.api.endpoints.search import _calculate_title_similarity

        # Identical titles
        similarity = _calculate_title_similarity("Data Scientist", "Data Scientist")
        assert similarity == 1.0

        # Partial match
        similarity = _calculate_title_similarity(
            "Data Scientist", "Senior Data Scientist"
        )
        assert 0.5 < similarity < 1.0

        # No match
        similarity = _calculate_title_similarity("Data Scientist", "Marketing Manager")
        assert similarity == 0.0

        # Empty titles
        similarity = _calculate_title_similarity("", "Test Title")
        assert similarity == 0.0

    def test_get_similarity_level(self):
        """Test similarity level categorization."""
        from jd_ingestion.api.endpoints.search import _get_similarity_level

        assert _get_similarity_level(0.9) == "Very High"
        assert _get_similarity_level(0.75) == "High"
        assert _get_similarity_level(0.6) == "Moderate"
        assert _get_similarity_level(0.4) == "Low"
        assert _get_similarity_level(0.1) == "Very Low"

    def test_generate_comparison_recommendations(self):
        """Test comparison recommendations generation."""
        from jd_ingestion.api.endpoints.search import (
            _generate_comparison_recommendations,
        )

        metadata_comparison = {
            "classification": {"job1": "EX-01", "job2": "EX-02", "match": False},
            "language": {"job1": "en", "job2": "en", "match": True},
            "title_similarity": 0.7,
        }

        section_comparison = [
            {
                "section_type": "section1",
                "job1_only": True,
                "job2_only": False,
                "both_present": False,
            },
            {
                "section_type": "section2",
                "job1_only": False,
                "job2_only": True,
                "both_present": False,
            },
        ]

        recommendations = _generate_comparison_recommendations(
            0.7, metadata_comparison, section_comparison
        )

        assert len(recommendations) >= 2
        assert any("similar" in rec.lower() for rec in recommendations)
        assert any("classification" in rec.lower() for rec in recommendations)


class TestSearchEndpointsErrorHandling:
    """Test error handling in search endpoints."""

    def test_search_database_error(self, client):
        """Test search with database connection error."""
        with patch(
            "jd_ingestion.api.endpoints.search.get_async_session"
        ) as mock_session:
            mock_session.side_effect = Exception("Database connection failed")

            response = client.get("/api/search/?q=test")
            assert response.status_code == 500

    def test_search_service_error(self, client):
        """Test search with embedding service error."""
        with patch(
            "jd_ingestion.api.endpoints.search.search_analytics_service"
        ) as mock_analytics:
            with patch(
                "jd_ingestion.api.endpoints.search.embedding_service"
            ) as mock_embedding:
                mock_analytics.start_search_session = AsyncMock(
                    return_value="session-123"
                )
                mock_embedding.semantic_search = AsyncMock(
                    side_effect=Exception("Service error")
                )

                with patch(
                    "jd_ingestion.api.endpoints.search.get_async_session"
                ) as mock_session:
                    mock_db = AsyncMock()
                    mock_session.return_value.__aenter__.return_value = mock_db

                    response = client.get("/api/search/?q=test")
                    assert response.status_code == 500

    def test_malformed_search_query(self, client):
        """Test search with malformed query data."""
        malformed_query = {
            "query": "",  # Empty query
            "limit": "invalid",  # Wrong type
            "classification": None,
        }

        response = client.post("/api/search/", json=malformed_query)
        assert response.status_code == 422

    def test_advanced_search_timeout_simulation(self, client):
        """Test advanced search handling slow database queries."""
        with patch(
            "jd_ingestion.api.endpoints.search.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Simulate slow query
            async def slow_execute(*args, **kwargs):
                await asyncio.sleep(0.1)  # Simulate delay
                raise Exception("Query timeout")

            mock_db.execute = slow_execute

            search_query = {
                "query": "test query",
                "classification": "EX-01",
                "limit": 10,
            }

            response = client.post("/api/search/advanced", json=search_query)
            assert response.status_code == 500
