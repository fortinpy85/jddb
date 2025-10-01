import pytest
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from sqlalchemy.ext.asyncio import AsyncSession

from jd_ingestion.services.analytics_service import AnalyticsService
from jd_ingestion.database.models import (
    UsageAnalytics,
    SystemMetrics,
    AIUsageTracking,
)


class TestAnalyticsService:
    """Test suite for the AnalyticsService class."""

    @pytest.fixture
    def analytics_service(self):
        """Create an analytics service instance for testing."""
        return AnalyticsService()

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = AsyncMock(spec=AsyncSession)
        session.add = Mock()
        session.commit = AsyncMock()
        session.flush = AsyncMock()
        session.execute = AsyncMock()
        session.scalar = AsyncMock()
        return session

    @pytest.fixture
    def sample_usage_data(self):
        """Sample usage analytics data."""
        return {
            "action_type": "search",
            "endpoint": "/api/search",
            "http_method": "POST",
            "session_id": str(uuid.uuid4()),
            "user_id": "test_user",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 Test Browser",
            "resource_id": "job_123",
            "response_time_ms": 150,
            "status_code": 200,
            "search_query": "software engineer",
            "search_filters": {"location": "Ottawa"},
            "results_count": 25,
        }

    def test_analytics_service_initialization(self, analytics_service):
        """Test analytics service initializes correctly."""
        assert analytics_service is not None
        assert hasattr(analytics_service, "session_cache")
        assert isinstance(analytics_service.session_cache, dict)

    @pytest.mark.asyncio
    async def test_track_activity_basic(
        self, analytics_service, mock_db_session, sample_usage_data
    ):
        """Test basic activity tracking."""
        await analytics_service.track_activity(db=mock_db_session, **sample_usage_data)

        # Verify database interaction
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

        # Verify the UsageAnalytics object was created correctly
        added_object = mock_db_session.add.call_args[0][0]
        assert isinstance(added_object, UsageAnalytics)
        assert added_object.action_type == "search"
        assert added_object.endpoint == "/api/search"
        assert added_object.session_id == sample_usage_data["session_id"]

    @pytest.mark.asyncio
    async def test_track_activity_minimal_data(
        self, analytics_service, mock_db_session
    ):
        """Test activity tracking with minimal required data."""
        await analytics_service.track_activity(
            db=mock_db_session, action_type="view", endpoint="/api/jobs/123"
        )

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

        added_object = mock_db_session.add.call_args[0][0]
        assert isinstance(added_object, UsageAnalytics)
        assert added_object.action_type == "view"
        assert added_object.endpoint == "/api/jobs/123"
        assert added_object.http_method == "GET"  # Default value
        assert added_object.status_code == 200  # Default value

    @pytest.mark.asyncio
    async def test_record_system_metrics(self, analytics_service, mock_db_session):
        """Test system metrics recording."""
        metrics_data = {
            "cpu_usage_percent": 45.5,
            "memory_usage_percent": 62.3,
            "disk_usage_percent": 78.9,
            "active_connections": 25,
            "request_count": 1500,
            "error_count": 3,
            "average_response_time_ms": 120.5,
        }

        await analytics_service.record_system_metrics(
            db=mock_db_session, **metrics_data
        )

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

        added_object = mock_db_session.add.call_args[0][0]
        assert isinstance(added_object, SystemMetrics)
        assert added_object.cpu_usage_percent == 45.5
        assert added_object.memory_usage_percent == 62.3
        assert added_object.active_connections == 25

    @pytest.mark.asyncio
    async def test_track_ai_usage(self, analytics_service, mock_db_session):
        """Test AI usage tracking."""
        ai_usage_data = {
            "operation_type": "embedding_generation",
            "model_name": "text-embedding-ada-002",
            "tokens_used": 1500,
            "cost_usd": Decimal("0.0006"),
            "processing_time_ms": 2500,
            "batch_size": 10,
            "request_id": str(uuid.uuid4()),
        }

        await analytics_service.track_ai_usage(db=mock_db_session, **ai_usage_data)

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

        added_object = mock_db_session.add.call_args[0][0]
        assert isinstance(added_object, AIUsageTracking)
        assert added_object.operation_type == "embedding_generation"
        assert added_object.model_name == "text-embedding-ada-002"
        assert added_object.tokens_used == 1500
        assert added_object.cost_usd == Decimal("0.0006")

    @pytest.mark.asyncio
    async def test_get_usage_statistics_basic(self, analytics_service, mock_db_session):
        """Test getting basic usage statistics."""
        # Mock database results
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [
            Mock(action_type="search", count=100),
            Mock(action_type="view", count=150),
            Mock(action_type="upload", count=25),
        ]
        mock_db_session.execute.return_value = mock_result

        stats = await analytics_service.get_usage_statistics(db=mock_db_session, days=7)

        assert isinstance(stats, dict)
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_system_health_metrics(self, analytics_service, mock_db_session):
        """Test getting system health metrics."""
        # Mock database results for system metrics
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = Mock(
            cpu_usage_percent=45.5,
            memory_usage_percent=62.3,
            disk_usage_percent=78.9,
            active_connections=25,
            error_count=2,
            timestamp=datetime.utcnow(),
        )
        mock_db_session.execute.return_value = mock_result

        health = await analytics_service.get_system_health_metrics(db=mock_db_session)

        assert isinstance(health, dict)
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_ai_usage_summary(self, analytics_service, mock_db_session):
        """Test getting AI usage summary."""
        # Mock database results
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [
            Mock(
                operation_type="embedding_generation",
                model_name="text-embedding-ada-002",
                total_tokens=15000,
                total_cost=Decimal("6.00"),
                operation_count=100,
                avg_processing_time=2500.0,
            )
        ]
        mock_db_session.execute.return_value = mock_result

        summary = await analytics_service.get_ai_usage_summary(
            db=mock_db_session, days=30
        )

        assert isinstance(summary, list)
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_popular_search_terms(self, analytics_service, mock_db_session):
        """Test getting popular search terms."""
        # Mock database results
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [
            Mock(search_query="software engineer", search_count=50),
            Mock(search_query="data scientist", search_count=35),
            Mock(search_query="project manager", search_count=28),
        ]
        mock_db_session.execute.return_value = mock_result

        terms = await analytics_service.get_popular_search_terms(
            db=mock_db_session, days=7, limit=10
        )

        assert isinstance(terms, list)
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_database_statistics(self, analytics_service, mock_db_session):
        """Test getting database statistics."""
        # Mock multiple database results
        results = [
            Mock(),  # job_descriptions count
            Mock(),  # content_chunks count
            Mock(),  # job_sections count
            Mock(),  # job_metadata count
        ]
        results[0].scalar.return_value = 1500
        results[1].scalar.return_value = 7500
        results[2].scalar.return_value = 3000
        results[3].scalar.return_value = 1200
        mock_db_session.execute.side_effect = results

        stats = await analytics_service.get_database_statistics(db=mock_db_session)

        assert isinstance(stats, dict)
        assert "total_job_descriptions" in stats
        assert "total_content_chunks" in stats
        assert "total_job_sections" in stats
        assert "total_job_metadata" in stats
        assert mock_db_session.execute.call_count == 4

    @pytest.mark.asyncio
    async def test_get_data_quality_metrics(self, analytics_service, mock_db_session):
        """Test getting data quality metrics."""
        # Mock database results
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [
            Mock(
                metric_name="completeness_score",
                metric_value=0.95,
                job_id=123,
                timestamp=datetime.utcnow(),
            ),
            Mock(
                metric_name="accuracy_score",
                metric_value=0.88,
                job_id=124,
                timestamp=datetime.utcnow(),
            ),
        ]
        mock_db_session.execute.return_value = mock_result

        metrics = await analytics_service.get_data_quality_metrics(
            db=mock_db_session, days=7
        )

        assert isinstance(metrics, list)
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_processing_performance(self, analytics_service, mock_db_session):
        """Test getting processing performance metrics."""
        # Mock database results
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [
            Mock(
                action_type="file_processing",
                avg_processing_time=5500.0,
                total_operations=150,
                success_rate=0.96,
                date=datetime.utcnow().date(),
            )
        ]
        mock_db_session.execute.return_value = mock_result

        performance = await analytics_service.get_processing_performance(
            db=mock_db_session, days=30
        )

        assert isinstance(performance, list)
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_track_activity_exception_handling(
        self, analytics_service, mock_db_session
    ):
        """Test activity tracking with database exception."""
        # Mock database exception
        mock_db_session.commit.side_effect = Exception("Database connection error")

        # Should not raise exception
        await analytics_service.track_activity(
            db=mock_db_session, action_type="test", endpoint="/test"
        )

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_cache_functionality(self, analytics_service):
        """Test session caching functionality."""
        session_id = str(uuid.uuid4())

        # Initially empty
        assert len(analytics_service.session_cache) == 0

        # Could be used for session tracking in future implementations
        analytics_service.session_cache[session_id] = {
            "start_time": datetime.utcnow(),
            "activity_count": 1,
        }

        assert session_id in analytics_service.session_cache
        assert analytics_service.session_cache[session_id]["activity_count"] == 1

    @pytest.mark.asyncio
    async def test_get_usage_statistics_with_date_range(
        self, analytics_service, mock_db_session
    ):
        """Test usage statistics with specific date range."""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        stats = await analytics_service.get_usage_statistics(
            db=mock_db_session, start_date=start_date, end_date=end_date
        )

        assert isinstance(stats, dict)
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_track_ai_usage_minimal_data(
        self, analytics_service, mock_db_session
    ):
        """Test AI usage tracking with minimal required data."""
        await analytics_service.track_ai_usage(
            db=mock_db_session,
            operation_type="text_completion",
            model_name="gpt-3.5-turbo",
            tokens_used=500,
        )

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

        added_object = mock_db_session.add.call_args[0][0]
        assert isinstance(added_object, AIUsageTracking)
        assert added_object.operation_type == "text_completion"
        assert added_object.tokens_used == 500
        assert added_object.cost_usd is None  # Not required

    @pytest.mark.asyncio
    async def test_record_system_metrics_minimal_data(
        self, analytics_service, mock_db_session
    ):
        """Test system metrics recording with minimal data."""
        await analytics_service.record_system_metrics(
            db=mock_db_session, cpu_usage_percent=25.0
        )

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

        added_object = mock_db_session.add.call_args[0][0]
        assert isinstance(added_object, SystemMetrics)
        assert added_object.cpu_usage_percent == 25.0
        assert added_object.memory_usage_percent is None  # Optional field
