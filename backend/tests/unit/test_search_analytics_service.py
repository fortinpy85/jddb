"""
Tests for search analytics service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import uuid

from jd_ingestion.services.search_analytics_service import SearchAnalyticsService
from jd_ingestion.database.models import SearchAnalytics


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def search_analytics_service():
    """Create search analytics service instance."""
    return SearchAnalyticsService()


@pytest.fixture
def sample_search_data():
    """Sample search data for testing."""
    return {
        "search_id": "test-search-123",
        "query_text": "data scientist python",
        "search_type": "semantic",
        "filters": {"classification": "EX-01", "language": "en"},
        "execution_time_ms": 250,
        "embedding_time_ms": 100,
        "total_results": 15,
        "returned_results": 10,
        "session_id": "session-456",
        "user_id": "user-789",
        "ip_address": "192.168.1.1",
        "client_type": "web",
    }


class TestSearchAnalyticsService:
    """Test search analytics service functionality."""

    async def test_start_search_session(self, search_analytics_service):
        """Test starting a new search session."""
        session_id = "test-session-123"
        user_id = "user-456"
        ip_address = "192.168.1.1"

        search_id = await search_analytics_service.start_search_session(
            session_id=session_id, user_id=user_id, ip_address=ip_address
        )

        # Should return a UUID string
        assert isinstance(search_id, str)
        assert len(search_id) == 36  # UUID4 length

        # Should be a valid UUID
        uuid_obj = uuid.UUID(search_id)
        assert str(uuid_obj) == search_id

    async def test_start_search_session_minimal(self, search_analytics_service):
        """Test starting search session with minimal parameters."""
        session_id = "test-session-123"

        search_id = await search_analytics_service.start_search_session(
            session_id=session_id
        )

        assert isinstance(search_id, str)
        assert len(search_id) == 36

    @patch("jd_ingestion.services.search_analytics_service.SearchAnalytics")
    async def test_record_search_success(
        self,
        mock_search_analytics_class,
        mock_db,
        search_analytics_service,
        sample_search_data,
    ):
        """Test successful search recording."""
        mock_search_record = Mock()
        mock_search_analytics_class.return_value = mock_search_record

        result = await search_analytics_service.record_search(
            db=mock_db, **sample_search_data
        )

        # Verify SearchAnalytics was created
        mock_search_analytics_class.assert_called_once()

        # Verify database operations
        mock_db.add.assert_called_once_with(mock_search_record)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_search_record)

        assert result == mock_search_record

    @patch("jd_ingestion.services.search_analytics_service.SearchAnalytics")
    async def test_record_search_with_error(
        self,
        mock_search_analytics_class,
        mock_db,
        search_analytics_service,
        sample_search_data,
    ):
        """Test recording search with error information."""
        mock_search_record = Mock()
        mock_search_analytics_class.return_value = mock_search_record

        error_info = {
            "error_type": "timeout",
            "error_message": "Search timeout after 30 seconds",
        }

        search_data = {**sample_search_data, "error_info": error_info}

        result = await search_analytics_service.record_search(db=mock_db, **search_data)

        # Verify error information was included
        call_args = mock_search_analytics_class.call_args[1]
        assert call_args["error_occurred"] == "yes"
        assert call_args["error_type"] == "timeout"
        assert call_args["error_message"] == "Search timeout after 30 seconds"

        assert result == mock_search_record

    @patch("jd_ingestion.services.search_analytics_service.SearchAnalytics")
    async def test_record_search_database_error(
        self,
        mock_search_analytics_class,
        mock_db,
        search_analytics_service,
        sample_search_data,
    ):
        """Test handling database errors during search recording."""
        mock_db.commit.side_effect = Exception("Database error")
        mock_db.rollback = AsyncMock()

        with pytest.raises(Exception, match="Database error"):
            await search_analytics_service.record_search(
                db=mock_db, **sample_search_data
            )

        mock_db.rollback.assert_called_once()

    async def test_record_user_interaction(self, mock_db, search_analytics_service):
        """Test recording user interaction with search results."""
        search_id = "test-search-123"
        interaction_data = {
            "clicked_results": [1, 3, 5],
            "result_rankings": {"1": 1, "3": 2, "5": 3},
            "user_satisfaction": 4,
        }

        # Mock database query
        mock_result = Mock()
        mock_search_record = Mock(spec=SearchAnalytics)
        mock_result.scalar_one_or_none.return_value = mock_search_record
        mock_db.execute.return_value = mock_result

        result = await search_analytics_service.record_user_interaction(
            db=mock_db, search_id=search_id, **interaction_data
        )

        # Verify database update
        assert mock_search_record.clicked_results == interaction_data["clicked_results"]
        assert mock_search_record.result_rankings == interaction_data["result_rankings"]
        assert (
            mock_search_record.user_satisfaction
            == interaction_data["user_satisfaction"]
        )

        mock_db.commit.assert_called_once()
        assert result == mock_search_record

    async def test_record_user_interaction_not_found(
        self, mock_db, search_analytics_service
    ):
        """Test recording interaction for non-existent search."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await search_analytics_service.record_user_interaction(
            db=mock_db, search_id="nonexistent-search", clicked_results=[1, 2]
        )

        assert result is None
        mock_db.commit.assert_not_called()

    async def test_get_search_statistics(self, mock_db, search_analytics_service):
        """Test getting search statistics."""
        # Mock database query results
        mock_result = Mock()
        mock_result.scalar.return_value = 150  # total searches
        mock_db.execute.return_value = mock_result

        # Mock additional statistics queries
        mock_db.execute.side_effect = [
            Mock(scalar=Mock(return_value=150)),  # total searches
            Mock(scalar=Mock(return_value=145)),  # successful searches
            Mock(scalar=Mock(return_value=125.5)),  # avg execution time
            Mock(scalar=Mock(return_value=50.2)),  # avg embedding time
            Mock(scalar=Mock(return_value=12.3)),  # avg results per query
        ]

        time_period = timedelta(days=7)
        stats = await search_analytics_service.get_search_statistics(
            db=mock_db, time_period=time_period
        )

        assert stats["total_searches"] == 150
        assert stats["successful_searches"] == 145
        assert stats["avg_execution_time_ms"] == 125.5
        assert stats["avg_embedding_time_ms"] == 50.2
        assert stats["avg_results_per_query"] == 12.3

        # Verify queries were made
        assert mock_db.execute.call_count == 5

    async def test_get_popular_queries(self, mock_db, search_analytics_service):
        """Test getting popular search queries."""
        mock_queries = [
            ("python developer", 25),
            ("data scientist", 20),
            ("project manager", 15),
        ]

        mock_result = Mock()
        mock_result.fetchall.return_value = mock_queries
        mock_db.execute.return_value = mock_result

        popular_queries = await search_analytics_service.get_popular_queries(
            db=mock_db, limit=10, time_period=timedelta(days=30)
        )

        assert len(popular_queries) == 3
        assert popular_queries[0]["query"] == "python developer"
        assert popular_queries[0]["count"] == 25
        assert popular_queries[1]["query"] == "data scientist"
        assert popular_queries[1]["count"] == 20

    async def test_get_search_trends(self, mock_db, search_analytics_service):
        """Test getting search trends over time."""
        mock_trends = [
            (datetime(2024, 1, 1), 10),
            (datetime(2024, 1, 2), 15),
            (datetime(2024, 1, 3), 12),
        ]

        mock_result = Mock()
        mock_result.fetchall.return_value = mock_trends
        mock_db.execute.return_value = mock_result

        trends = await search_analytics_service.get_search_trends(db=mock_db, days=7)

        assert len(trends) == 3
        assert trends[0]["date"] == datetime(2024, 1, 1)
        assert trends[0]["search_count"] == 10

    async def test_get_search_performance_metrics(
        self, mock_db, search_analytics_service
    ):
        """Test getting search performance metrics."""
        # Mock performance data
        mock_performance_data = [
            ("semantic", 150.5, 75.2),
            ("fulltext", 89.3, 0.0),
            ("hybrid", 180.7, 95.1),
        ]

        mock_result = Mock()
        mock_result.fetchall.return_value = mock_performance_data
        mock_db.execute.return_value = mock_result

        performance = await search_analytics_service.get_search_performance_metrics(
            db=mock_db, time_period=timedelta(days=7)
        )

        assert len(performance) == 3
        assert performance[0]["search_type"] == "semantic"
        assert performance[0]["avg_execution_time"] == 150.5
        assert performance[0]["avg_embedding_time"] == 75.2

    async def test_get_query_hash(self, search_analytics_service):
        """Test query hash generation."""
        query = "data scientist python machine learning"

        # Call the method (assuming it exists)
        hash_value = search_analytics_service._get_query_hash(query)

        # Should be a consistent hash
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 hex digest length

        # Same query should produce same hash
        hash_value2 = search_analytics_service._get_query_hash(query)
        assert hash_value == hash_value2

    async def test_get_failed_searches(self, mock_db, search_analytics_service):
        """Test getting failed search analysis."""
        mock_failed_searches = [
            Mock(
                query_text="nonexistent query",
                error_type="no_results",
                error_message="No matching results found",
                timestamp=datetime.now(),
            )
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_failed_searches
        mock_db.execute.return_value = mock_result

        failed_searches = await search_analytics_service.get_failed_searches(
            db=mock_db, limit=10, time_period=timedelta(days=7)
        )

        assert len(failed_searches) == 1
        assert failed_searches[0].query_text == "nonexistent query"
        assert failed_searches[0].error_type == "no_results"

    async def test_cleanup_old_analytics(self, mock_db, search_analytics_service):
        """Test cleaning up old analytics data."""
        # Mock cleanup result
        mock_result = Mock()
        mock_result.rowcount = 25
        mock_db.execute.return_value = mock_result

        deleted_count = await search_analytics_service.cleanup_old_analytics(
            db=mock_db, older_than_days=90
        )

        assert deleted_count == 25
        mock_db.commit.assert_called_once()


class TestSearchAnalyticsServiceEdgeCases:
    """Test edge cases and error conditions."""

    async def test_record_search_empty_query(self, mock_db, search_analytics_service):
        """Test recording search with empty query."""
        search_data = {
            "search_id": "test-123",
            "query_text": "",
            "search_type": "semantic",
            "filters": {},
            "execution_time_ms": 100,
        }

        with patch(
            "jd_ingestion.services.search_analytics_service.SearchAnalytics"
        ) as mock_class:
            mock_record = Mock()
            mock_class.return_value = mock_record

            result = await search_analytics_service.record_search(
                db=mock_db, **search_data
            )

            # Should still record the search
            assert result == mock_record
            mock_db.add.assert_called_once()

    async def test_get_statistics_no_data(self, mock_db, search_analytics_service):
        """Test getting statistics when no data exists."""
        # Mock empty results
        mock_result = Mock()
        mock_result.scalar.return_value = 0
        mock_db.execute.return_value = mock_result

        stats = await search_analytics_service.get_search_statistics(
            db=mock_db, time_period=timedelta(days=7)
        )

        assert stats["total_searches"] == 0
        assert stats.get("success_rate") == 0.0

    async def test_invalid_time_period(self, mock_db, search_analytics_service):
        """Test handling invalid time period."""
        with pytest.raises(ValueError):
            await search_analytics_service.get_search_statistics(
                db=mock_db,
                time_period=timedelta(days=-1),  # Negative time period
            )

    async def test_database_connection_error(self, search_analytics_service):
        """Test handling database connection errors."""
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("Connection lost")

        with pytest.raises(Exception, match="Connection lost"):
            await search_analytics_service.get_search_statistics(
                db=mock_db, time_period=timedelta(days=7)
            )
