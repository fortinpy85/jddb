"""
Tests for search recommendations service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from jd_ingestion.services.search_recommendations_service import (
    SearchRecommendationsService,
    search_recommendations_service,
)


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

    def test_global_instance(self):
        """Test global service instance exists."""
        assert search_recommendations_service is not None
        assert isinstance(search_recommendations_service, SearchRecommendationsService)

    # Query Suggestions Tests
    @pytest.mark.asyncio
    async def test_get_query_suggestions_short_query(
        self, recommendations_service, async_session
    ):
        """Test query suggestions with too short query."""
        suggestions = await recommendations_service.get_query_suggestions(
            db=async_session, partial_query="da", limit=5
        )
        assert len(suggestions) == 0

    @pytest.mark.asyncio
    @patch("jd_ingestion.services.search_recommendations_service.cache_service")
    async def test_get_query_suggestions_cached(
        self, mock_cache, recommendations_service, async_session
    ):
        """Test query suggestions with cached results."""
        cached_suggestions = [{"text": "cached query", "type": "popular", "score": 0.9}]
        mock_cache.get = AsyncMock(return_value=cached_suggestions)

        suggestions = await recommendations_service.get_query_suggestions(
            db=async_session, partial_query="test query", limit=5
        )

        assert suggestions == cached_suggestions
        mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    @patch("jd_ingestion.services.search_recommendations_service.cache_service")
    async def test_get_query_suggestions_empty_cache(
        self, mock_cache, recommendations_service, async_session
    ):
        """Test query suggestions with empty cache."""
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        suggestions = await recommendations_service.get_query_suggestions(
            db=async_session, partial_query="director", limit=5
        )

        assert isinstance(suggestions, list)
        mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    @patch("jd_ingestion.services.search_recommendations_service.cache_service")
    async def test_get_query_suggestions_cache_failure(
        self, mock_cache, recommendations_service, async_session
    ):
        """Test query suggestions when cache fails."""
        mock_cache.get = AsyncMock(side_effect=Exception("Cache error"))
        mock_cache.set = AsyncMock()

        suggestions = await recommendations_service.get_query_suggestions(
            db=async_session, partial_query="manager", limit=5
        )

        # Should still return results even if cache fails
        assert isinstance(suggestions, list)

    # Search Recommendations Tests
    @pytest.mark.asyncio
    async def test_get_search_recommendations_basic(
        self, recommendations_service, async_session
    ):
        """Test basic search recommendations."""
        search_context = {"query": "data scientist"}

        recommendations = await recommendations_service.get_search_recommendations(
            db=async_session, search_context=search_context, limit=8
        )

        assert isinstance(recommendations, dict)
        assert "related_searches" in recommendations
        assert "trending_queries" in recommendations
        assert "suggested_filters" in recommendations
        assert "popular_in_category" in recommendations

    @pytest.mark.asyncio
    async def test_get_search_recommendations_with_user(
        self, recommendations_service, async_session
    ):
        """Test search recommendations with user context."""
        search_context = {"query": "software engineer"}
        user_id = "user-123"

        recommendations = await recommendations_service.get_search_recommendations(
            db=async_session, search_context=search_context, user_id=user_id, limit=8
        )

        assert isinstance(recommendations, dict)
        assert "similar_users_searched" in recommendations

    @pytest.mark.asyncio
    async def test_get_search_recommendations_error_handling(
        self, recommendations_service
    ):
        """Test search recommendations error handling."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("DB error"))

        search_context = {"query": "test"}

        recommendations = await recommendations_service.get_search_recommendations(
            db=mock_db, search_context=search_context, limit=8
        )

        # Should return empty structure on error
        assert recommendations["related_searches"] == []
        assert recommendations["trending_queries"] == []

    # Popular Similar Queries Tests
    @pytest.mark.asyncio
    async def test_get_popular_similar_queries(
        self, recommendations_service, async_session
    ):
        """Test getting popular similar queries."""
        # Create mock result
        mock_row = MagicMock()
        mock_row.query_text = "data scientist python"
        mock_row.usage_count = 15
        mock_row.avg_results = 25.5
        mock_row.avg_time = 150.0

        mock_result = AsyncMock()
        mock_result.fetchall = Mock(return_value=[mock_row])

        async_session.execute = AsyncMock(return_value=mock_result)

        suggestions = await recommendations_service._get_popular_similar_queries(
            db=async_session, partial_query="data", limit=5
        )

        assert len(suggestions) == 1
        assert suggestions[0]["text"] == "data scientist python"
        assert suggestions[0]["type"] == "popular"
        assert suggestions[0]["score"] == 15.0

    @pytest.mark.asyncio
    async def test_get_popular_similar_queries_empty(
        self, recommendations_service, async_session
    ):
        """Test getting popular similar queries with no results."""
        mock_result = AsyncMock()
        mock_result.fetchall = Mock(return_value=[])

        async_session.execute = AsyncMock(return_value=mock_result)

        suggestions = await recommendations_service._get_popular_similar_queries(
            db=async_session, partial_query="zzz", limit=5
        )

        assert len(suggestions) == 0

    # Semantic Suggestions Tests
    @pytest.mark.asyncio
    @patch("jd_ingestion.services.search_recommendations_service.embedding_service")
    async def test_get_semantic_suggestions(
        self, mock_embedding_service, recommendations_service, async_session
    ):
        """Test semantic suggestions."""
        mock_embedding_service.generate_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3]
        )

        mock_row = MagicMock()
        mock_row.chunk_text = "python developer machine learning"
        mock_row.section_type = "responsibilities"
        mock_row.title = "Data Scientist"
        mock_row.classification = "CS-03"

        mock_result = AsyncMock()
        mock_result.fetchall = Mock(return_value=[mock_row])

        async_session.execute = AsyncMock(return_value=mock_result)

        suggestions = await recommendations_service._get_semantic_suggestions(
            db=async_session, partial_query="python", limit=5
        )

        assert isinstance(suggestions, list)

    @pytest.mark.asyncio
    @patch(
        "jd_ingestion.services.search_recommendations_service.embedding_service", None
    )
    async def test_get_semantic_suggestions_no_service(
        self, recommendations_service, async_session
    ):
        """Test semantic suggestions when embedding service unavailable."""
        suggestions = await recommendations_service._get_semantic_suggestions(
            db=async_session, partial_query="test", limit=5
        )

        assert len(suggestions) == 0

    # User-Based Suggestions Tests
    @pytest.mark.asyncio
    async def test_get_user_based_suggestions(
        self, recommendations_service, async_session
    ):
        """Test user-based suggestions."""
        mock_row = MagicMock()
        mock_row.query_text = "python developer"
        mock_row.total_results = 10
        mock_row.created_at = datetime.now()

        mock_result = AsyncMock()
        mock_result.fetchall = Mock(return_value=[mock_row])

        async_session.execute = AsyncMock(return_value=mock_result)

        suggestions = await recommendations_service._get_user_based_suggestions(
            db=async_session,
            partial_query="python",
            user_id="user-123",
            session_id=None,
            limit=5,
        )

        assert len(suggestions) == 1
        assert suggestions[0]["type"] == "personal"

    @pytest.mark.asyncio
    async def test_get_user_based_suggestions_no_user(
        self, recommendations_service, async_session
    ):
        """Test user-based suggestions with no user context."""
        suggestions = await recommendations_service._get_user_based_suggestions(
            db=async_session,
            partial_query="test",
            user_id=None,
            session_id=None,
            limit=5,
        )

        assert len(suggestions) == 0

    # Content-Based Suggestions Tests
    @pytest.mark.asyncio
    async def test_get_content_based_suggestions(
        self, recommendations_service, async_session
    ):
        """Test content-based suggestions."""
        mock_row = MagicMock()
        mock_row.title = "Senior Python Developer"
        mock_row.classification = "CS-03"
        mock_row.match_count = 5

        mock_result = AsyncMock()
        mock_result.fetchall = Mock(return_value=[mock_row])

        async_session.execute = AsyncMock(return_value=mock_result)

        suggestions = await recommendations_service._get_content_based_suggestions(
            db=async_session, partial_query="python", limit=5
        )

        assert isinstance(suggestions, list)

    # Related Searches Tests
    @pytest.mark.asyncio
    async def test_get_related_searches(self, recommendations_service, async_session):
        """Test getting related searches."""
        mock_row = MagicMock()
        mock_row.query_text = "python developer"
        mock_row.frequency = 10
        mock_row.avg_results = 25.0

        mock_result = AsyncMock()
        mock_result.fetchall = Mock(return_value=[mock_row])

        async_session.execute = AsyncMock(return_value=mock_result)

        search_context = {"query": "python"}

        related = await recommendations_service._get_related_searches(
            db=async_session, search_context=search_context, limit=5
        )

        assert len(related) == 1
        assert related[0]["query"] == "python developer"

    @pytest.mark.asyncio
    async def test_get_related_searches_empty_query(
        self, recommendations_service, async_session
    ):
        """Test related searches with empty query."""
        search_context = {}

        related = await recommendations_service._get_related_searches(
            db=async_session, search_context=search_context, limit=5
        )

        assert len(related) == 0

    # Trending Queries Tests
    @pytest.mark.asyncio
    async def test_get_trending_queries(self, recommendations_service, async_session):
        """Test getting trending queries."""
        mock_row = MagicMock()
        mock_row.query_text = "ai jobs"
        mock_row.frequency = 45

        mock_result = AsyncMock()
        mock_result.fetchall = Mock(return_value=[mock_row])

        async_session.execute = AsyncMock(return_value=mock_result)

        trending = await recommendations_service._get_trending_queries(
            db=async_session, limit=10
        )

        assert len(trending) == 1
        assert trending[0]["query"] == "ai jobs"
        assert trending[0]["trend"] == "up"

    # Suggested Filters Tests
    @pytest.mark.asyncio
    async def test_get_suggested_filters(self, recommendations_service, async_session):
        """Test getting suggested filters."""
        mock_class_row = MagicMock()
        mock_class_row.classification = "CS-03"
        mock_class_row.count = 50

        mock_dept_row = MagicMock()
        mock_dept_row.department = "IT"
        mock_dept_row.count = 30

        mock_result_class = AsyncMock()
        mock_result_class.fetchall = Mock(return_value=[mock_class_row])

        mock_result_dept = AsyncMock()
        mock_result_dept.fetchall = Mock(return_value=[mock_dept_row])

        async_session.execute = AsyncMock(
            side_effect=[mock_result_class, mock_result_dept]
        )

        search_context = {"query": "developer"}

        filters = await recommendations_service._get_suggested_filters(
            db=async_session, search_context=search_context
        )

        assert isinstance(filters, list)
        assert len(filters) == 2

    # Similar Users Searches Tests
    @pytest.mark.asyncio
    async def test_get_similar_users_searches(
        self, recommendations_service, async_session
    ):
        """Test getting similar users' searches."""
        mock_user_row = MagicMock()
        mock_user_row.query_text = "python developer"
        mock_user_row.filters_applied = {"classification": "CS-03"}

        mock_similar_row = MagicMock()
        mock_similar_row.query_text = "java developer"
        mock_similar_row.frequency = 5
        mock_similar_row.user_id = "user-456"

        mock_result_user = AsyncMock()
        mock_result_user.fetchall = Mock(return_value=[mock_user_row])

        mock_result_similar = AsyncMock()
        mock_result_similar.fetchall = Mock(return_value=[mock_similar_row])

        async_session.execute = AsyncMock(
            side_effect=[mock_result_user, mock_result_similar]
        )

        similar = await recommendations_service._get_similar_users_searches(
            db=async_session, user_id="user-123", limit=5
        )

        assert isinstance(similar, list)

    @pytest.mark.asyncio
    async def test_get_similar_users_searches_no_user(
        self, recommendations_service, async_session
    ):
        """Test similar users searches with no user ID."""
        similar = await recommendations_service._get_similar_users_searches(
            db=async_session, user_id="", limit=5
        )

        assert len(similar) == 0

    # Popular in Category Tests
    @pytest.mark.asyncio
    async def test_get_popular_in_category(
        self, recommendations_service, async_session
    ):
        """Test getting popular searches in category."""
        mock_row = MagicMock()
        mock_row.query_text = "data analyst"
        mock_row.frequency = 15
        mock_row.avg_results = 20.0

        mock_result = AsyncMock()
        mock_result.fetchall = Mock(return_value=[mock_row])

        async_session.execute = AsyncMock(return_value=mock_result)

        search_context = {
            "query": "data",
            "classification": "CS-02",
            "department": "IT",
        }

        popular = await recommendations_service._get_popular_in_category(
            db=async_session, search_context=search_context, limit=5
        )

        assert isinstance(popular, list)

    # Helper Methods Tests
    def test_extract_key_terms(self, recommendations_service):
        """Test key term extraction."""
        content = "python developer with machine learning experience"
        partial_query = "python"

        terms = recommendations_service._extract_key_terms(content, partial_query)

        assert isinstance(terms, list)
        assert any("python" in term for term in terms)

    def test_extract_key_terms_empty(self, recommendations_service):
        """Test key term extraction with empty content."""
        terms = recommendations_service._extract_key_terms("", "test")
        assert len(terms) == 0

    def test_extract_search_terms(self, recommendations_service):
        """Test search term extraction from titles."""
        title = "Senior Software Engineer III"

        terms = recommendations_service._extract_search_terms(title)

        assert isinstance(terms, list)
        assert len(terms) > 0

    def test_extract_search_terms_empty(self, recommendations_service):
        """Test search term extraction with empty title."""
        terms = recommendations_service._extract_search_terms("")
        assert len(terms) == 0

    def test_rank_and_deduplicate_suggestions(self, recommendations_service):
        """Test ranking and deduplication."""
        suggestions = [
            {"text": "python developer", "type": "popular", "score": 0.9},
            {"text": "Python Developer", "type": "content", "score": 0.7},  # Duplicate
            {"text": "java developer", "type": "semantic", "score": 0.8},
        ]

        result = recommendations_service._rank_and_deduplicate_suggestions(
            suggestions, "python", limit=5
        )

        assert len(result) == 2  # Duplicate removed
        assert result[0]["text"].lower() == "python developer"

    def test_rank_and_deduplicate_suggestions_empty(self, recommendations_service):
        """Test ranking with empty suggestions."""
        result = recommendations_service._rank_and_deduplicate_suggestions(
            [], "test", limit=5
        )
        assert len(result) == 0

    def test_get_fallback_suggestions(self, recommendations_service):
        """Test fallback suggestions."""
        suggestions = recommendations_service._get_fallback_suggestions("manager", 5)

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert all(s["type"] == "fallback" for s in suggestions)

    def test_get_fallback_suggestions_no_match(self, recommendations_service):
        """Test fallback suggestions with no match."""
        suggestions = recommendations_service._get_fallback_suggestions("zzz", 5)

        assert isinstance(suggestions, list)

    def test_get_fallback_suggestions_partial_match(self, recommendations_service):
        """Test fallback suggestions with partial match."""
        suggestions = recommendations_service._get_fallback_suggestions("dir", 5)

        assert isinstance(suggestions, list)
        assert any("director" in s["text"] for s in suggestions)


class TestSearchRecommendationsServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_partial_query(self, recommendations_service, async_session):
        """Test handling empty partial query."""
        suggestions = await recommendations_service.get_query_suggestions(
            db=async_session, partial_query="", limit=5
        )

        assert len(suggestions) == 0

    @pytest.mark.asyncio
    async def test_whitespace_query(self, recommendations_service, async_session):
        """Test handling whitespace-only query."""
        suggestions = await recommendations_service.get_query_suggestions(
            db=async_session, partial_query="   ", limit=5
        )

        assert len(suggestions) == 0

    @pytest.mark.asyncio
    async def test_database_error_handling(self, recommendations_service):
        """Test handling database errors."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("Database error"))

        suggestions = await recommendations_service.get_query_suggestions(
            db=mock_db, partial_query="test query", limit=5
        )

        # Should return empty list on error
        assert len(suggestions) == 0

    @pytest.mark.asyncio
    async def test_no_recommendations_available(
        self, recommendations_service, async_session
    ):
        """Test when no recommendations are available."""
        mock_result = AsyncMock()
        mock_result.fetchall = Mock(return_value=[])

        async_session.execute = AsyncMock(return_value=mock_result)

        trending = await recommendations_service._get_trending_queries(
            db=async_session, limit=10
        )

        assert len(trending) == 0

    @pytest.mark.asyncio
    @patch("jd_ingestion.services.search_recommendations_service.cache_service")
    async def test_cache_set_failure(
        self, mock_cache, recommendations_service, async_session
    ):
        """Test handling cache set failures."""
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(side_effect=Exception("Cache write error"))

        # Should not raise exception, just log warning
        suggestions = await recommendations_service.get_query_suggestions(
            db=async_session, partial_query="director", limit=5
        )

        assert isinstance(suggestions, list)
