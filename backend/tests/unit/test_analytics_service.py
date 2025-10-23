"""Tests for Analytics Service"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from jd_ingestion.services.analytics_service import AnalyticsService, analytics_service
from jd_ingestion.database.models import (
    UsageAnalytics,
    AIUsageTracking,
    SystemMetrics,
)


@pytest.fixture
def service():
    """Create analytics service instance"""
    return AnalyticsService()


class TestTrackActivity:
    @pytest.mark.asyncio
    async def test_track_activity_basic(self, service, async_session: AsyncSession):
        """Test basic activity tracking"""
        await service.track_activity(
            db=async_session,
            action_type="search",
            endpoint="/api/search",
            http_method="POST",
            session_id="test-session",
        )

        result = await async_session.execute(
            select(UsageAnalytics).where(UsageAnalytics.session_id == "test-session")
        )
        record = result.scalar_one_or_none()
        assert record is not None
        assert record.action_type == "search"
        assert record.endpoint == "/api/search"
        assert record.http_method == "POST"

    @pytest.mark.asyncio
    async def test_track_activity_with_search_data(
        self, service, async_session: AsyncSession
    ):
        """Test activity tracking with search metadata"""
        await service.track_activity(
            db=async_session,
            action_type="search",
            endpoint="/api/search",
            session_id="search-test",
            search_query="data engineer",
            search_filters={"location": "Toronto"},
            results_count=25,
            response_time_ms=150,
        )

        result = await async_session.execute(
            select(UsageAnalytics).where(UsageAnalytics.session_id == "search-test")
        )
        record = result.scalar_one_or_none()
        assert record.search_query == "data engineer"
        assert record.search_filters == {"location": "Toronto"}
        assert record.results_count == 25
        assert record.response_time_ms == 150

    @pytest.mark.asyncio
    async def test_track_activity_generates_session_id(
        self, service, async_session: AsyncSession
    ):
        """Test that session_id is auto-generated if not provided"""
        await service.track_activity(
            db=async_session,
            action_type="view",
            endpoint="/api/jobs/123",
        )

        result = await async_session.execute(select(UsageAnalytics))
        record = result.scalar_one_or_none()
        assert record is not None
        assert record.session_id is not None and len(record.session_id) > 0


class TestTrackAIUsage:
    @pytest.mark.asyncio
    async def test_track_ai_usage_basic(self, service, async_session: AsyncSession):
        """Test AI usage tracking"""
        await service.track_ai_usage(
            db=async_session,
            service_type="openai",
            operation_type="embedding",
            model_name="text-embedding-3-small",
            input_tokens=500,
            output_tokens=0,
            cost_usd=Decimal("0.01"),
        )

        result = await async_session.execute(select(AIUsageTracking))
        record = result.scalar_one_or_none()
        assert record is not None
        assert record.service_type == "openai"
        assert record.operation_type == "embedding"
        assert record.total_tokens == 500  # input + output
        assert record.cost_usd == Decimal("0.01")

    @pytest.mark.asyncio
    async def test_track_ai_usage_with_error(
        self, service, async_session: AsyncSession
    ):
        """Test AI usage tracking with error"""
        await service.track_ai_usage(
            db=async_session,
            service_type="openai",
            operation_type="completion",
            model_name="gpt-4",
            success="error",
            error_message="Rate limit exceeded",
        )

        result = await async_session.execute(select(AIUsageTracking))
        record = result.scalar_one_or_none()
        assert record.success == "error"
        assert record.error_message == "Rate limit exceeded"


class TestGetUsageStatistics:
    @pytest.mark.asyncio
    async def test_get_usage_statistics_day(self, service, async_session: AsyncSession):
        """Test getting usage statistics for a day"""
        # Create test data with explicit timestamps
        from jd_ingestion.database.models import UsageAnalytics, AIUsageTracking

        now = datetime.utcnow()

        # Create UsageAnalytics record with timestamp
        usage_record = UsageAnalytics(
            timestamp=now,
            session_id="s1",
            action_type="search",
            endpoint="/api/search",
            http_method="GET",
            response_time_ms=100,
        )
        async_session.add(usage_record)

        # Create AIUsageTracking record with request_timestamp
        ai_record = AIUsageTracking(
            service_type="openai",
            operation_type="embedding",
            model_name="test-model",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost_usd=Decimal("0.05"),
            request_timestamp=now,
        )
        async_session.add(ai_record)
        await async_session.commit()

        # Query with date range that includes the records
        end_date = now + timedelta(minutes=1)
        start_date = now - timedelta(minutes=1)

        stats = await service.get_usage_statistics(
            db=async_session, period="day", start_date=start_date, end_date=end_date
        )

        assert stats["period"] == "day"
        assert "usage" in stats
        assert "ai_usage" in stats
        assert stats["usage"]["total_requests"] == 1
        assert stats["ai_usage"]["total_requests"] == 1
        assert stats["ai_usage"]["total_tokens"] == 150

    @pytest.mark.asyncio
    async def test_get_usage_statistics_custom_range(
        self, service, async_session: AsyncSession
    ):
        """Test getting usage statistics with custom date range"""
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()

        stats = await service.get_usage_statistics(
            db=async_session, period="week", start_date=start, end_date=end
        )

        assert "start_date" in stats
        assert "end_date" in stats
        assert stats["usage"]["total_requests"] >= 0


class TestGenerateSystemMetrics:
    @pytest.mark.asyncio
    async def test_generate_system_metrics_daily(
        self, service, async_session: AsyncSession
    ):
        """Test generating daily system metrics"""
        # Create some test data
        await service.track_activity(
            db=async_session,
            action_type="search",
            endpoint="/api/search",
            session_id="test",
        )

        result = await service.generate_system_metrics(
            db=async_session, metric_type="daily"
        )

        assert result["metric_type"] == "daily"
        assert "period_start" in result
        assert "period_end" in result
        assert "metrics_id" in result
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_generate_system_metrics_creates_record(
        self, service, async_session: AsyncSession
    ):
        """Test that system metrics are persisted"""
        await service.generate_system_metrics(db=async_session, metric_type="hourly")

        result = await async_session.execute(
            select(SystemMetrics).where(SystemMetrics.metric_type == "hourly")
        )
        record = result.scalar_one_or_none()
        assert record is not None
        assert record.metric_type == "hourly"


class TestGetAnalyticsDashboard:
    @pytest.mark.asyncio
    async def test_get_analytics_dashboard(self, service, async_session: AsyncSession):
        """Test analytics dashboard generation"""
        dashboard = await service.get_analytics_dashboard(db=async_session)

        assert "recent_activity" in dashboard
        assert "weekly_trends" in dashboard
        assert "generated_at" in dashboard
        assert dashboard["recent_activity"]["period"] == "day"
        assert dashboard["weekly_trends"]["period"] == "week"


class TestGetSummaryStats:
    @pytest.mark.asyncio
    async def test_get_summary_stats_empty(self, service, async_session: AsyncSession):
        """Test summary stats with no data"""
        stats = await service.get_summary_stats(db=async_session)

        assert "total_jobs" in stats
        assert "jobs_with_embeddings" in stats
        assert "total_content_chunks" in stats
        assert "embedding_coverage_percent" in stats
        assert stats["total_jobs"] >= 0


class TestGetQualityMetrics:
    @pytest.mark.asyncio
    async def test_get_quality_metrics(self, service, async_session: AsyncSession):
        """Test quality metrics retrieval"""
        metrics = await service.get_quality_metrics(db=async_session)

        assert "avg_content_completeness" in metrics
        assert "avg_sections_completeness" in metrics
        assert "total_processing_errors" in metrics
        assert "quality_coverage_percent" in metrics


class TestGetAIUsageStats:
    @pytest.mark.asyncio
    async def test_get_ai_usage_stats(self, service, async_session: AsyncSession):
        """Test AI usage stats for last 30 days"""
        # Create test data - use explicit insert to control timestamp
        from jd_ingestion.database.models import AIUsageTracking

        ai_record = AIUsageTracking(
            service_type="openai",
            operation_type="completion",
            model_name="gpt-4",
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
            cost_usd=Decimal("0.15"),
            success="success",
            request_timestamp=datetime.now(),  # Use datetime.now() for consistency
        )
        async_session.add(ai_record)
        await async_session.commit()

        stats = await service.get_ai_usage_stats(db=async_session)

        assert "total_requests" in stats
        assert "total_tokens" in stats
        assert "total_cost_usd" in stats
        assert "success_rate_percent" in stats
        assert stats["total_requests"] >= 1
        assert stats["total_tokens"] >= 1500


class TestGetContentDistribution:
    @pytest.mark.asyncio
    async def test_get_content_distribution(self, service, async_session: AsyncSession):
        """Test content distribution stats"""
        distribution = await service.get_content_distribution(db=async_session)

        assert "by_department" in distribution
        assert "by_section_type" in distribution
        assert isinstance(distribution["by_department"], dict)


class TestGetPerformanceStats:
    @pytest.mark.asyncio
    async def test_get_performance_stats(self, service, async_session: AsyncSession):
        """Test performance statistics"""
        # Create upload activity with processing time
        await service.track_activity(
            db=async_session,
            action_type="upload",
            endpoint="/api/upload",
            processing_time_ms=5000,
        )

        stats = await service.get_performance_stats(db=async_session)

        assert "avg_processing_time_ms" in stats
        assert "processing_health" in stats
        assert stats["processing_health"] in ["good", "slow"]


class TestBackwardsCompatibility:
    @pytest.mark.asyncio
    async def test_record_system_metrics(self, service, async_session: AsyncSession):
        """Test backwards compatibility wrapper"""
        # Should not raise error
        await service.record_system_metrics(db=async_session)

    @pytest.mark.asyncio
    async def test_get_system_health_metrics(
        self, service, async_session: AsyncSession
    ):
        """Test system health metrics wrapper"""
        metrics = await service.get_system_health_metrics(db=async_session)
        assert "avg_processing_time_ms" in metrics

    @pytest.mark.asyncio
    async def test_get_ai_usage_summary(self, service, async_session: AsyncSession):
        """Test AI usage summary wrapper"""
        summary = await service.get_ai_usage_summary(db=async_session, days=30)
        assert isinstance(summary, list)

    @pytest.mark.asyncio
    async def test_get_data_quality_metrics(self, service, async_session: AsyncSession):
        """Test data quality metrics wrapper"""
        metrics = await service.get_data_quality_metrics(db=async_session, days=7)
        assert isinstance(metrics, list)


class TestGetDatabaseStatistics:
    @pytest.mark.asyncio
    async def test_get_database_statistics(self, service, async_session: AsyncSession):
        """Test database statistics"""
        stats = await service.get_database_statistics(db=async_session)

        assert "total_job_descriptions" in stats
        assert "total_content_chunks" in stats
        assert "total_job_sections" in stats
        assert all(isinstance(v, int) for v in stats.values())


class TestGetPopularSearchTerms:
    @pytest.mark.asyncio
    async def test_get_popular_search_terms_empty(
        self, service, async_session: AsyncSession
    ):
        """Test popular search terms with no data"""
        terms = await service.get_popular_search_terms(
            db=async_session, days=7, limit=10
        )
        assert isinstance(terms, list)


class TestGetProcessingPerformance:
    @pytest.mark.asyncio
    async def test_get_processing_performance(
        self, service, async_session: AsyncSession
    ):
        """Test processing performance metrics"""
        # Create upload activities
        await service.track_activity(
            db=async_session,
            action_type="upload",
            endpoint="/api/upload",
            processing_time_ms=3000,
        )

        performance = await service.get_processing_performance(
            db=async_session, days=30
        )
        assert isinstance(performance, list)


class TestGlobalServiceInstance:
    def test_global_instance_exists(self):
        """Test that global analytics_service instance exists"""
        assert analytics_service is not None
        assert isinstance(analytics_service, AnalyticsService)
