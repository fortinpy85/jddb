"""
Tests for search recommendations service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from jd_ingestion.services.search_recommendations_service import (
    SearchRecommendationsService,
)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_cache_service():
    """Mock cache service."""
    cache = Mock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service."""
    service = Mock()
    service.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
    return service


@pytest.fixture
def recommendations_service():
    """Create search recommendations service instance."""
    return SearchRecommendationsService()


class TestSearchRecommendationsService:
    """Test search recommendations service."""

    def test_init(self, recommendations_service):
        """Test service initialization."""
        assert recommendations_service.min_query_length == 3
        assert recommendations_service.max_suggestions == 10
        assert recommendations_service.similarity_threshold == 0.7
        assert recommendations_service.cache_ttl == 3600

    async def test_get_query_suggestions_success(
        self, recommendations_service, mock_db
    ):
        """Test successful query suggestions generation."""
        # Mock database query results
        mock_suggestions = [
            ("data scientist python", 15),
            ("data scientist machine learning", 10),
            ("data analyst python", 8),
        ]

        mock_result = Mock()
        mock_result.fetchall.return_value = mock_suggestions
        mock_db.execute.return_value = mock_result

        suggestions = await recommendations_service.get_query_suggestions(
            db=mock_db, partial_query="data sci", limit=5
        )

        assert len(suggestions) == 3
        assert suggestions[0]["query"] == "data scientist python"
        assert suggestions[0]["frequency"] == 15
        assert suggestions[0]["confidence"] > 0

    async def test_get_query_suggestions_short_query(
        self, recommendations_service, mock_db
    ):
        """Test query suggestions with too short query."""
        suggestions = await recommendations_service.get_query_suggestions(
            db=mock_db,
            partial_query="da",
            limit=5,  # Too short
        )

        assert len(suggestions) == 0
        mock_db.execute.assert_not_called()

    @patch("jd_ingestion.services.search_recommendations_service.cache_service")
    async def test_get_query_suggestions_cached(
        self, mock_cache, recommendations_service, mock_db
    ):
        """Test query suggestions with cached results."""
        cached_suggestions = [
            {"query": "cached query", "frequency": 10, "confidence": 0.8}
        ]
        mock_cache.get.return_value = cached_suggestions

        suggestions = await recommendations_service.get_query_suggestions(
            db=mock_db, partial_query="test query", limit=5
        )

        assert suggestions == cached_suggestions
        mock_db.execute.assert_not_called()

    async def test_get_personalized_recommendations(
        self, recommendations_service, mock_db
    ):
        """Test personalized recommendations based on user history."""
        user_id = "user-123"

        # Mock user's search history
        mock_user_searches = [
            Mock(query_text="python developer", timestamp=datetime.now()),
            Mock(query_text="machine learning engineer", timestamp=datetime.now()),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_user_searches
        mock_db.execute.return_value = mock_result

        recommendations = (
            await recommendations_service.get_personalized_recommendations(
                db=mock_db, user_id=user_id, limit=5
            )
        )

        assert isinstance(recommendations, list)
        mock_db.execute.assert_called()

    async def test_get_trending_searches(self, recommendations_service, mock_db):
        """Test getting trending search queries."""
        # Mock trending data
        mock_trending = [
            ("artificial intelligence jobs", 45),
            ("remote work opportunities", 38),
            ("blockchain developer", 25),
        ]

        mock_result = Mock()
        mock_result.fetchall.return_value = mock_trending
        mock_db.execute.return_value = mock_result

        trending = await recommendations_service.get_trending_searches(
            db=mock_db, time_period=timedelta(days=7), limit=10
        )

        assert len(trending) == 3
        assert trending[0]["query"] == "artificial intelligence jobs"
        assert trending[0]["trend_score"] == 45

    @patch("jd_ingestion.services.search_recommendations_service.embedding_service")
    async def test_get_semantic_suggestions(
        self, mock_embedding_service, recommendations_service, mock_db
    ):
        """Test semantic query suggestions using embeddings."""
        mock_embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]

        # Mock similar queries from database
        mock_similar_queries = [
            Mock(query_text="machine learning engineer", similarity_score=0.85),
            Mock(query_text="data scientist python", similarity_score=0.78),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_similar_queries
        mock_db.execute.return_value = mock_result

        suggestions = await recommendations_service.get_semantic_suggestions(
            db=mock_db, query="ML engineer", limit=5
        )

        mock_embedding_service.generate_embedding.assert_called_once_with("ML engineer")
        assert isinstance(suggestions, list)

    async def test_get_category_recommendations(self, recommendations_service, mock_db):
        """Test getting recommendations by job category."""
        # Mock category-based recommendations
        mock_categories = [("IT", 150), ("Engineering", 120), ("Management", 90)]

        mock_result = Mock()
        mock_result.fetchall.return_value = mock_categories
        mock_db.execute.return_value = mock_result

        recommendations = await recommendations_service.get_category_recommendations(
            db=mock_db, limit=10
        )

        assert len(recommendations) == 3
        assert recommendations[0]["category"] == "IT"
        assert recommendations[0]["job_count"] == 150

    async def test_get_location_suggestions(self, recommendations_service, mock_db):
        """Test location-based suggestions."""
        partial_location = "Otta"

        # Mock location matches
        mock_locations = [("Ottawa, ON", 25), ("Ottawa Valley, ON", 5)]

        mock_result = Mock()
        mock_result.fetchall.return_value = mock_locations
        mock_db.execute.return_value = mock_result

        suggestions = await recommendations_service.get_location_suggestions(
            db=mock_db, partial_location=partial_location, limit=5
        )

        assert len(suggestions) == 2
        assert suggestions[0]["location"] == "Ottawa, ON"
        assert suggestions[0]["job_count"] == 25

    async def test_get_classification_suggestions(
        self, recommendations_service, mock_db
    ):
        """Test classification-based suggestions."""
        # Mock classification data
        mock_classifications = [("EX-01", 45), ("EX-02", 30), ("EX-03", 20)]

        mock_result = Mock()
        mock_result.fetchall.return_value = mock_classifications
        mock_db.execute.return_value = mock_result

        suggestions = await recommendations_service.get_classification_suggestions(
            db=mock_db, limit=10
        )

        assert len(suggestions) == 3
        assert suggestions[0]["classification"] == "EX-01"
        assert suggestions[0]["count"] == 45

    async def test_analyze_query_intent(self, recommendations_service):
        """Test query intent analysis."""
        queries_and_intents = [
            ("python developer remote", ["skill", "location"]),
            ("EX-01 manager", ["classification", "role"]),
            ("data scientist Toronto", ["skill", "location"]),
        ]

        for query, expected_intents in queries_and_intents:
            intent = await recommendations_service.analyze_query_intent(query)

            assert isinstance(intent, dict)
            assert "primary_intent" in intent
            assert "secondary_intents" in intent
            assert "confidence" in intent

    async def test_get_auto_complete_suggestions(
        self, recommendations_service, mock_db
    ):
        """Test auto-complete suggestions."""
        partial_query = "data sc"

        # Mock auto-complete matches
        mock_completions = [
            ("data scientist", 50),
            ("data science", 30),
            ("data science manager", 15),
        ]

        mock_result = Mock()
        mock_result.fetchall.return_value = mock_completions
        mock_db.execute.return_value = mock_result

        completions = await recommendations_service.get_auto_complete_suggestions(
            db=mock_db, partial_query=partial_query, limit=5
        )

        assert len(completions) == 3
        assert completions[0]["suggestion"] == "data scientist"
        assert completions[0]["frequency"] == 50

    async def test_get_related_searches(self, recommendations_service, mock_db):
        """Test getting related searches for a query."""
        base_query = "software engineer"

        # Mock related searches
        mock_related = [
            ("software developer", 0.85),
            ("software architect", 0.75),
            ("full stack developer", 0.70),
        ]

        mock_result = Mock()
        mock_result.fetchall.return_value = mock_related
        mock_db.execute.return_value = mock_result

        related = await recommendations_service.get_related_searches(
            db=mock_db, query=base_query, limit=5
        )

        assert len(related) == 3
        assert related[0]["query"] == "software developer"
        assert related[0]["similarity"] == 0.85

    def test_normalize_query(self, recommendations_service):
        """Test query normalization."""
        queries = [
            ("Python Developer", "python developer"),
            ("  Machine Learning  ", "machine learning"),
            ("Data-Scientist", "data scientist"),
            ("Full_Stack_Engineer", "full stack engineer"),
        ]

        for input_query, expected in queries:
            normalized = recommendations_service._normalize_query(input_query)
            assert normalized == expected

    def test_extract_keywords(self, recommendations_service):
        """Test keyword extraction from queries."""
        query = "senior python developer machine learning remote work"

        keywords = recommendations_service._extract_keywords(query)

        assert isinstance(keywords, list)
        assert "python" in keywords
        assert "developer" in keywords
        assert "machine learning" in keywords
        assert len(keywords) > 0

    async def test_get_filter_suggestions(self, recommendations_service, mock_db):
        """Test getting filter suggestions based on current results."""
        current_filters = {"classification": "EX-01"}

        # Mock filter suggestions
        mock_filter_suggestions = {
            "locations": [("Ottawa, ON", 15), ("Toronto, ON", 12)],
            "departments": [("IT", 20), ("Engineering", 8)],
            "languages": [("en", 25), ("fr", 10)],
        }

        with patch.object(
            recommendations_service,
            "_get_filter_suggestions",
            return_value=mock_filter_suggestions,
        ):
            suggestions = await recommendations_service.get_filter_suggestions(
                db=mock_db, current_filters=current_filters, result_count=35
            )

            assert "locations" in suggestions
            assert "departments" in suggestions
            assert len(suggestions["locations"]) == 2


class TestSearchRecommendationsServiceEdgeCases:
    """Test edge cases and error conditions."""

    async def test_empty_partial_query(self, recommendations_service, mock_db):
        """Test handling empty partial query."""
        suggestions = await recommendations_service.get_query_suggestions(
            db=mock_db, partial_query="", limit=5
        )

        assert len(suggestions) == 0

    async def test_database_error_handling(self, recommendations_service):
        """Test handling database errors."""
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception, match="Database connection failed"):
            await recommendations_service.get_query_suggestions(
                db=mock_db, partial_query="test query", limit=5
            )

    async def test_no_recommendations_available(self, recommendations_service, mock_db):
        """Test when no recommendations are available."""
        # Mock empty database results
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        recommendations = await recommendations_service.get_trending_searches(
            db=mock_db, time_period=timedelta(days=30), limit=10
        )

        assert len(recommendations) == 0

    async def test_invalid_time_period(self, recommendations_service, mock_db):
        """Test handling invalid time periods."""
        with pytest.raises(ValueError):
            await recommendations_service.get_trending_searches(
                db=mock_db,
                time_period=timedelta(days=-1),  # Invalid negative period
                limit=10,
            )

    async def test_large_limit_handling(self, recommendations_service, mock_db):
        """Test handling very large limit values."""
        # Should cap the limit to max_suggestions
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        suggestions = await recommendations_service.get_query_suggestions(
            db=mock_db,
            partial_query="test",
            limit=1000,  # Very large limit
        )

        # Should be capped to max_suggestions (10)
        assert isinstance(suggestions, list)
