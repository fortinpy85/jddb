"""
Tests for rate limiting service.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import timedelta
from decimal import Decimal

from jd_ingestion.services.rate_limiting_service import (
    RateLimitingService,
    RateLimitType,
    RateLimit,
    RateLimitStatus,
)
from jd_ingestion.utils.exceptions import (
    RateLimitExceededException as RateLimitExceeded,
)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def rate_limiting_service():
    """Create rate limiting service instance."""
    return RateLimitingService()


@pytest.fixture
def sample_rate_limits():
    """Sample rate limit configurations."""
    return {
        RateLimitType.REQUESTS_PER_MINUTE: RateLimit(limit=60, window_seconds=60),
        RateLimitType.TOKENS_PER_MINUTE: RateLimit(limit=10000, window_seconds=60),
        RateLimitType.COST_PER_HOUR: RateLimit(
            limit=100, window_seconds=3600
        ),  # $100/hour
        RateLimitType.COST_PER_DAY: RateLimit(
            limit=1000, window_seconds=86400
        ),  # $1000/day
    }


class TestRateLimitingService:
    """Test rate limiting service functionality."""

    def test_init(self, rate_limiting_service):
        """Test service initialization."""
        assert isinstance(rate_limiting_service.rate_limits, dict)
        assert isinstance(rate_limiting_service.usage_windows, dict)
        assert rate_limiting_service.service_type == "openai"

    def test_init_with_custom_config(self, sample_rate_limits):
        """Test initialization with custom rate limit configuration."""
        service = RateLimitingService(rate_limits=sample_rate_limits)

        assert service.rate_limits == sample_rate_limits
        assert len(service.rate_limits) == 4

    async def test_check_rate_limit_under_limit(self, rate_limiting_service):
        """Test rate limit check when under the limit."""
        # Simulate being under the limit
        limit_type = RateLimitType.REQUESTS_PER_MINUTE
        usage_amount = 1

        # Should not raise exception
        await rate_limiting_service.check_rate_limit(limit_type, usage_amount)

        # Should record the usage
        assert limit_type in rate_limiting_service.usage_windows

    async def test_check_rate_limit_exceeded(self, rate_limiting_service):
        """Test rate limit check when limit is exceeded."""
        limit_type = RateLimitType.REQUESTS_PER_MINUTE

        # Configure a very low limit for testing
        rate_limiting_service.rate_limits[limit_type] = RateLimit(
            limit=2, window_seconds=60
        )

        # Use up the limit
        await rate_limiting_service.check_rate_limit(limit_type, 1)
        await rate_limiting_service.check_rate_limit(limit_type, 1)

        # This should exceed the limit
        with pytest.raises(RateLimitExceeded) as exc_info:
            await rate_limiting_service.check_rate_limit(limit_type, 1)

        assert exc_info.value.limit_type == limit_type
        assert exc_info.value.retry_after > 0

    async def test_record_api_usage(self, rate_limiting_service, mock_db):
        """Test recording API usage in database."""
        usage_data = {
            "operation_type": "completion",
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150,
            "cost_usd": Decimal("0.05"),
            "model_name": "gpt-3.5-turbo",
            "request_id": "req-123",
            "success": True,
        }

        with patch(
            "jd_ingestion.services.rate_limiting_service.AIUsageTracking"
        ) as mock_usage_class:
            mock_usage_record = Mock()
            mock_usage_class.return_value = mock_usage_record

            await rate_limiting_service.record_api_usage(db=mock_db, **usage_data)

            # Verify usage tracking record was created
            mock_usage_class.assert_called_once()
            call_kwargs = mock_usage_class.call_args[1]
            assert call_kwargs["operation_type"] == "completion"
            assert call_kwargs["input_tokens"] == 100
            assert call_kwargs["cost_usd"] == Decimal("0.05")

            # Verify database operations
            mock_db.add.assert_called_once_with(mock_usage_record)
            mock_db.commit.assert_called_once()

    async def test_get_current_usage(self, rate_limiting_service, mock_db):
        """Test getting current usage statistics."""
        # Mock database query results
        mock_result = Mock()
        mock_result.scalar.return_value = 150  # total requests

        mock_db.execute.return_value = mock_result

        # Mock multiple queries for different metrics
        mock_db.execute.side_effect = [
            Mock(scalar=Mock(return_value=150)),  # total requests
            Mock(scalar=Mock(return_value=25000)),  # total tokens
            Mock(scalar=Mock(return_value=15.50)),  # total cost
        ]

        usage = await rate_limiting_service.get_current_usage(
            db=mock_db, time_window=timedelta(minutes=60)
        )

        assert usage["total_requests"] == 150
        assert usage["total_tokens"] == 25000
        assert usage["total_cost"] == 15.50
        assert mock_db.execute.call_count == 3

    async def test_get_rate_limit_status(self, rate_limiting_service):
        """Test getting rate limit status."""
        limit_type = RateLimitType.REQUESTS_PER_MINUTE

        # Add some usage
        await rate_limiting_service.check_rate_limit(limit_type, 5)

        status = await rate_limiting_service.get_rate_limit_status(limit_type)

        assert isinstance(status, RateLimitStatus)
        assert status.limit_type == limit_type
        assert status.current_usage == 5
        assert status.limit == rate_limiting_service.rate_limits[limit_type].limit

    async def test_wait_for_rate_limit_reset(self, rate_limiting_service):
        """Test waiting for rate limit reset."""
        limit_type = RateLimitType.REQUESTS_PER_MINUTE

        # Configure a low limit for testing
        rate_limiting_service.rate_limits[limit_type] = RateLimit(
            limit=1, window_seconds=1
        )

        # Exceed the limit
        await rate_limiting_service.check_rate_limit(limit_type, 1)

        with pytest.raises(RateLimitExceeded):
            await rate_limiting_service.check_rate_limit(limit_type, 1)

        # Wait for reset (short time for testing)
        await asyncio.sleep(1.1)

        # Should be able to make requests again
        await rate_limiting_service.check_rate_limit(limit_type, 1)

    async def test_burst_allowance(self, rate_limiting_service):
        """Test burst allowance functionality."""
        limit_type = RateLimitType.REQUESTS_PER_MINUTE

        # Configure limit with burst allowance
        rate_limiting_service.rate_limits[limit_type] = RateLimit(
            limit=10,
            window_seconds=60,
            burst_allowance=1.5,  # 50% burst
        )

        # Should allow up to 15 requests (10 * 1.5) in burst
        for i in range(15):
            await rate_limiting_service.check_rate_limit(limit_type, 1)

        # 16th request should fail
        with pytest.raises(RateLimitExceeded):
            await rate_limiting_service.check_rate_limit(limit_type, 1)

    async def test_sliding_window_behavior(self, rate_limiting_service):
        """Test sliding window rate limiting behavior."""
        limit_type = RateLimitType.REQUESTS_PER_MINUTE

        # Configure short window for testing
        rate_limiting_service.rate_limits[limit_type] = RateLimit(
            limit=2, window_seconds=2
        )

        # Use up the limit
        await rate_limiting_service.check_rate_limit(limit_type, 1)
        await rate_limiting_service.check_rate_limit(limit_type, 1)

        # Should be at limit
        with pytest.raises(RateLimitExceeded):
            await rate_limiting_service.check_rate_limit(limit_type, 1)

        # Wait for window to slide
        await asyncio.sleep(2.1)

        # Should be able to make requests again
        await rate_limiting_service.check_rate_limit(limit_type, 1)

    async def test_token_based_rate_limiting(self, rate_limiting_service):
        """Test token-based rate limiting."""
        limit_type = RateLimitType.TOKENS_PER_MINUTE

        # Set low token limit for testing
        rate_limiting_service.rate_limits[limit_type] = RateLimit(
            limit=100, window_seconds=60
        )

        # Use tokens gradually
        await rate_limiting_service.check_rate_limit(limit_type, 30)
        await rate_limiting_service.check_rate_limit(limit_type, 40)
        await rate_limiting_service.check_rate_limit(limit_type, 30)

        # Should be at limit (100 tokens used)
        with pytest.raises(RateLimitExceeded):
            await rate_limiting_service.check_rate_limit(limit_type, 1)

    async def test_cost_based_rate_limiting(self, rate_limiting_service):
        """Test cost-based rate limiting."""
        limit_type = RateLimitType.COST_PER_HOUR

        # Set low cost limit for testing
        rate_limiting_service.rate_limits[limit_type] = RateLimit(
            limit=5, window_seconds=3600
        )  # $5/hour

        # Use up cost budget in dollars (converted to cents for precision)
        await rate_limiting_service.check_rate_limit(limit_type, 200)  # $2.00
        await rate_limiting_service.check_rate_limit(limit_type, 300)  # $3.00

        # Should be at limit ($5.00)
        with pytest.raises(RateLimitExceeded):
            await rate_limiting_service.check_rate_limit(
                limit_type, 1
            )  # $0.01 would exceed

    async def test_cleanup_old_usage_data(self, rate_limiting_service, mock_db):
        """Test cleaning up old usage data."""
        # Mock deletion result
        mock_result = Mock()
        mock_result.rowcount = 150
        mock_db.execute.return_value = mock_result

        deleted_count = await rate_limiting_service.cleanup_old_usage_data(
            db=mock_db, older_than_days=30
        )

        assert deleted_count == 150
        mock_db.commit.assert_called_once()

    async def test_get_usage_analytics(self, rate_limiting_service, mock_db):
        """Test getting usage analytics."""
        # Mock analytics data
        mock_analytics = [
            ("completion", 150, 25000, Decimal("15.50")),
            ("embedding", 50, 10000, Decimal("2.00")),
        ]

        mock_result = Mock()
        mock_result.fetchall.return_value = mock_analytics
        mock_db.execute.return_value = mock_result

        analytics = await rate_limiting_service.get_usage_analytics(
            db=mock_db, time_period=timedelta(days=7)
        )

        assert len(analytics) == 2
        assert analytics[0]["operation_type"] == "completion"
        assert analytics[0]["request_count"] == 150
        assert analytics[0]["total_tokens"] == 25000

    def test_rate_limit_dataclass(self):
        """Test RateLimit dataclass."""
        rate_limit = RateLimit(limit=100, window_seconds=60)

        assert rate_limit.limit == 100
        assert rate_limit.window_seconds == 60
        assert rate_limit.burst_allowance == 1.2  # Default value

        # Test with custom burst allowance
        custom_limit = RateLimit(limit=50, window_seconds=30, burst_allowance=1.5)
        assert custom_limit.burst_allowance == 1.5

    def test_rate_limit_status_dataclass(self):
        """Test RateLimitStatus dataclass."""
        status = RateLimitStatus(
            limit_type=RateLimitType.REQUESTS_PER_MINUTE,
            current_usage=25,
            limit=100,
            window_remaining_seconds=45,
        )

        assert status.limit_type == RateLimitType.REQUESTS_PER_MINUTE
        assert status.current_usage == 25
        assert status.limit == 100
        assert status.window_remaining_seconds == 45

        # Test utilization percentage
        utilization = (status.current_usage / status.limit) * 100
        assert utilization == 25.0

    async def test_multiple_limit_types_concurrently(self, rate_limiting_service):
        """Test handling multiple limit types concurrently."""
        # Configure different limits
        rate_limiting_service.rate_limits = {
            RateLimitType.REQUESTS_PER_MINUTE: RateLimit(limit=10, window_seconds=60),
            RateLimitType.TOKENS_PER_MINUTE: RateLimit(limit=1000, window_seconds=60),
            RateLimitType.COST_PER_HOUR: RateLimit(limit=50, window_seconds=3600),
        }

        # Use different types concurrently
        await rate_limiting_service.check_rate_limit(
            RateLimitType.REQUESTS_PER_MINUTE, 1
        )
        await rate_limiting_service.check_rate_limit(
            RateLimitType.TOKENS_PER_MINUTE, 100
        )
        await rate_limiting_service.check_rate_limit(RateLimitType.COST_PER_HOUR, 5)

        # Each should track independently
        request_status = await rate_limiting_service.get_rate_limit_status(
            RateLimitType.REQUESTS_PER_MINUTE
        )
        token_status = await rate_limiting_service.get_rate_limit_status(
            RateLimitType.TOKENS_PER_MINUTE
        )

        assert request_status.current_usage == 1
        assert token_status.current_usage == 100


class TestRateLimitingServiceEdgeCases:
    """Test edge cases and error conditions."""

    async def test_zero_usage_amount(self, rate_limiting_service):
        """Test handling zero usage amount."""
        # Should not change usage counters
        initial_status = await rate_limiting_service.get_rate_limit_status(
            RateLimitType.REQUESTS_PER_MINUTE
        )

        await rate_limiting_service.check_rate_limit(
            RateLimitType.REQUESTS_PER_MINUTE, 0
        )

        final_status = await rate_limiting_service.get_rate_limit_status(
            RateLimitType.REQUESTS_PER_MINUTE
        )

        assert final_status.current_usage == initial_status.current_usage

    async def test_negative_usage_amount(self, rate_limiting_service):
        """Test handling negative usage amount."""
        with pytest.raises(ValueError, match="Usage amount must be non-negative"):
            await rate_limiting_service.check_rate_limit(
                RateLimitType.REQUESTS_PER_MINUTE, -1
            )

    async def test_unknown_limit_type(self, rate_limiting_service):
        """Test handling unknown rate limit type."""
        # Create a new enum value not in the configured limits
        unknown_type = "unknown_limit_type"

        with pytest.raises(KeyError):
            await rate_limiting_service.check_rate_limit(unknown_type, 1)

    async def test_database_error_in_record_usage(self, rate_limiting_service):
        """Test handling database errors when recording usage."""
        mock_db = Mock()
        mock_db.commit.side_effect = Exception("Database connection failed")
        mock_db.rollback = AsyncMock()

        usage_data = {
            "operation_type": "completion",
            "input_tokens": 100,
            "output_tokens": 50,
            "cost_usd": Decimal("0.05"),
            "success": True,
        }

        with patch("jd_ingestion.services.rate_limiting_service.AIUsageTracking"):
            with pytest.raises(Exception, match="Database connection failed"):
                await rate_limiting_service.record_api_usage(db=mock_db, **usage_data)

            mock_db.rollback.assert_called_once()

    def test_rate_limit_exceeded_exception(self):
        """Test RateLimitExceeded exception."""
        limit_type = RateLimitType.REQUESTS_PER_MINUTE
        current_usage = 100
        limit = 100
        retry_after = 60

        exc = RateLimitExceeded(
            limit_type=limit_type,
            current_usage=current_usage,
            limit=limit,
            retry_after=retry_after,
        )

        assert exc.limit_type == limit_type
        assert exc.current_usage == current_usage
        assert exc.limit == limit
        assert exc.retry_after == retry_after

        # Test string representation
        assert str(exc).startswith("Rate limit exceeded")

    async def test_concurrent_rate_limit_checks(self, rate_limiting_service):
        """Test concurrent rate limit checks for thread safety."""
        limit_type = RateLimitType.REQUESTS_PER_MINUTE

        # Configure low limit
        rate_limiting_service.rate_limits[limit_type] = RateLimit(
            limit=50, window_seconds=60
        )

        # Run many concurrent checks
        tasks = []
        for i in range(40):  # Under limit
            task = rate_limiting_service.check_rate_limit(limit_type, 1)
            tasks.append(task)

        # All should succeed
        await asyncio.gather(*tasks)

        status = await rate_limiting_service.get_rate_limit_status(limit_type)
        assert status.current_usage == 40
