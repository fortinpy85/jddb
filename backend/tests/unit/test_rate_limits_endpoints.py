"""
Tests for rate limiting API endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from jd_ingestion.api.main import app
from jd_ingestion.services.rate_limiting_service import (
    RateLimitType,
    RateLimit,
    RateLimitStatus,
)


@pytest.fixture
def mock_rate_limiting_service():
    """Mock rate limiting service fixture."""
    with patch("jd_ingestion.api.endpoints.rate_limits.rate_limiting_service") as mock:
        yield mock


@pytest.fixture
def mock_log_performance():
    """Mock log_performance_metric function."""

    async def mock_log_perf(metric_name, duration_ms, metadata):
        pass

    with patch(
        "jd_ingestion.api.endpoints.rate_limits.log_performance_metric",
        side_effect=mock_log_perf,
    ):
        yield


@pytest.fixture
def sample_usage_stats():
    """Sample usage statistics data."""
    return {
        "service": "openai",
        "total_requests": 1500,
        "total_tokens": 75000,
        "total_cost": 0.15,
        "average_tokens_per_request": 50.0,
        "period_hours": 24,
        "requests_per_hour": 62.5,
        "tokens_per_hour": 3125.0,
        "cost_per_hour": 0.00625,
    }


@pytest.fixture
def sample_rate_limit_status():
    """Sample rate limit status data."""
    return RateLimitStatus(
        limit_type=RateLimitType.REQUESTS_PER_MINUTE,
        current_usage=150,
        limit=1000,
        window_remaining_seconds=30,
        reset_time=datetime.now(),
        is_exceeded=False,
    )


class TestGetRateLimitStatus:
    """Test rate limit status endpoint."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_get_rate_limit_status_success(
        self,
        mock_session,
        mock_rate_limiting_service,
        mock_log_performance,
        sample_usage_stats,
    ):
        """Test successful rate limit status retrieval."""
        # Setup mocks (mock_log_performance is handled by fixture)
        mock_rate_limiting_service.rate_limits = {"openai": {}}

        # Configure get_usage_stats to accept parameters: (db, service, period_hours)
        async def mock_get_usage_stats(db, service, period_hours):
            return sample_usage_stats

        mock_rate_limiting_service.get_usage_stats = AsyncMock(
            side_effect=mock_get_usage_stats
        )

        mock_bucket = Mock()

        async def mock_get_bucket_status():
            return {
                "tokens": 800,
                "capacity": 1000,
                "last_refill": datetime.now().isoformat(),
            }

        mock_bucket.get_status = AsyncMock(side_effect=mock_get_bucket_status)

        mock_rate_limiting_service.token_buckets = {
            "openai": {RateLimitType.REQUESTS_PER_MINUTE: mock_bucket}
        }

        # Configure get_recommended_delay to accept parameters: (service, operation_type)
        async def mock_get_recommended_delay(service, operation_type):
            return 0.5

        mock_rate_limiting_service.get_recommended_delay = AsyncMock(
            side_effect=mock_get_recommended_delay
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/rate-limits/status/openai")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "openai"
        assert "usage_stats" in data
        assert "token_buckets" in data
        assert "recommended_delay_seconds" in data
        assert "status_timestamp" in data

    @pytest.mark.asyncio
    async def test_get_rate_limit_status_service_not_found(
        self, mock_rate_limiting_service
    ):
        """Test rate limit status for non-existent service."""
        mock_rate_limiting_service.rate_limits = {}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/rate-limits/status/nonexistent")

        assert response.status_code == 404
        assert "Service 'nonexistent' not found" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_get_rate_limit_status_error(
        self, mock_session, mock_rate_limiting_service, mock_log_performance
    ):
        """Test rate limit status with service error."""
        mock_rate_limiting_service.rate_limits = {"openai": {}}
        mock_rate_limiting_service.get_usage_stats = AsyncMock(
            side_effect=Exception("Database error")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/rate-limits/status/openai")

        assert response.status_code == 500
        assert "Failed to get rate limit status" in response.json()["detail"]


class TestCheckRateLimit:
    """Test rate limit checking endpoint."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_check_rate_limit_allowed(
        self,
        mock_session,
        mock_rate_limiting_service,
        mock_log_performance,
        sample_rate_limit_status,
    ):
        """Test rate limit check when request is allowed."""
        mock_rate_limiting_service.check_rate_limit = AsyncMock(
            return_value=(True, [sample_rate_limit_status])
        )
        mock_rate_limiting_service.get_recommended_delay = AsyncMock(return_value=0.0)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/rate-limits/check/openai",
                params={
                    "operation_type": "text_generation",
                    "estimated_tokens": 100,
                    "estimated_cost": 0.002,
                    "user_id": "user123",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "openai"
        assert data["operation_type"] == "text_generation"
        assert data["is_allowed"] is True
        assert data["estimated_tokens"] == 100
        assert data["estimated_cost"] == 0.002
        assert "rate_limit_statuses" in data
        assert "check_timestamp" in data

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_check_rate_limit_not_allowed(
        self,
        mock_session,
        mock_rate_limiting_service,
        mock_log_performance,
        sample_rate_limit_status,
    ):
        """Test rate limit check when request is not allowed."""
        exceeded_status = sample_rate_limit_status
        exceeded_status.is_exceeded = True

        mock_rate_limiting_service.check_rate_limit = AsyncMock(
            return_value=(False, [exceeded_status])
        )
        mock_rate_limiting_service.get_recommended_delay = AsyncMock(return_value=60.0)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/rate-limits/check/openai",
                params={"operation_type": "text_generation", "estimated_tokens": 1000},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["is_allowed"] is False
        assert data["recommended_delay_seconds"] == 60.0

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_check_rate_limit_error(
        self, mock_session, mock_rate_limiting_service, mock_log_performance
    ):
        """Test rate limit check with service error."""
        mock_rate_limiting_service.check_rate_limit = AsyncMock(
            side_effect=Exception("Service error")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/rate-limits/check/openai",
                params={"operation_type": "text_generation"},
            )

        assert response.status_code == 500
        assert "Failed to check rate limit" in response.json()["detail"]


class TestRecordUsage:
    """Test usage recording endpoint."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_record_usage_success(
        self, mock_session, mock_rate_limiting_service, mock_log_performance
    ):
        """Test successful usage recording."""
        mock_rate_limiting_service.record_usage = AsyncMock()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/rate-limits/record/openai",
                params={
                    "operation_type": "text_generation",
                    "tokens_used": 150,
                    "cost": 0.003,
                    "user_id": "user123",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "openai"
        assert data["operation_type"] == "text_generation"
        assert data["tokens_used"] == 150
        assert data["cost"] == 0.003
        assert data["status"] == "success"
        assert "recorded_at" in data

        mock_rate_limiting_service.record_usage.assert_called_once_with(
            service="openai",
            operation_type="text_generation",
            tokens_used=150,
            cost=0.003,
            user_id="user123",
        )

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_record_usage_minimal_params(
        self, mock_session, mock_rate_limiting_service, mock_log_performance
    ):
        """Test usage recording with minimal parameters."""
        mock_rate_limiting_service.record_usage = AsyncMock()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/rate-limits/record/openai", params={"operation_type": "embedding"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["tokens_used"] == 1  # default value
        assert data["cost"] == 0.0  # default value

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_record_usage_error(
        self, mock_session, mock_rate_limiting_service, mock_log_performance
    ):
        """Test usage recording with service error."""
        mock_rate_limiting_service.record_usage = AsyncMock(
            side_effect=Exception("Recording error")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/rate-limits/record/openai",
                params={"operation_type": "text_generation", "tokens_used": 100},
            )

        assert response.status_code == 500
        assert "Failed to record usage" in response.json()["detail"]


class TestGetUsageStatistics:
    """Test usage statistics endpoint."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_get_usage_statistics_success(
        self,
        mock_session,
        mock_rate_limiting_service,
        mock_log_performance,
        sample_usage_stats,
    ):
        """Test successful usage statistics retrieval."""
        mock_rate_limiting_service.get_usage_stats = AsyncMock(
            return_value=sample_usage_stats
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/rate-limits/usage/openai?period_hours=48")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "openai"
        assert data["total_requests"] == 1500
        assert data["total_tokens"] == 75000
        assert data["period_hours"] == 24

        mock_rate_limiting_service.get_usage_stats.assert_called_once_with(
            mock_session.return_value.__aenter__.return_value, "openai", 48
        )

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_get_usage_statistics_default_period(
        self,
        mock_session,
        mock_rate_limiting_service,
        mock_log_performance,
        sample_usage_stats,
    ):
        """Test usage statistics with default period."""
        mock_rate_limiting_service.get_usage_stats = AsyncMock(
            return_value=sample_usage_stats
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/rate-limits/usage/openai")

        assert response.status_code == 200
        mock_rate_limiting_service.get_usage_stats.assert_called_once_with(
            mock_session.return_value.__aenter__.return_value,
            "openai",
            24,  # default period
        )

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_get_usage_statistics_invalid_period(self, mock_session):
        """Test usage statistics with invalid period."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/rate-limits/usage/openai?period_hours=200")

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_get_usage_statistics_error(
        self, mock_session, mock_rate_limiting_service, mock_log_performance
    ):
        """Test usage statistics with service error."""
        mock_rate_limiting_service.get_usage_stats = AsyncMock(
            side_effect=Exception("Database error")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/rate-limits/usage/openai")

        assert response.status_code == 500
        assert "Failed to get usage statistics" in response.json()["detail"]


class TestGetCostOptimization:
    """Test cost optimization recommendations endpoint."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_get_cost_optimization_success(
        self, mock_session, mock_rate_limiting_service, mock_log_performance
    ):
        """Test successful cost optimization recommendations."""
        sample_recommendations = [
            {
                "category": "rate_limiting",
                "priority": "high",
                "title": "Reduce API call frequency",
                "description": "Consider batching requests to reduce API calls",
                "estimated_savings_percent": 25.0,
                "implementation_difficulty": "medium",
            },
            {
                "category": "model_selection",
                "priority": "medium",
                "title": "Use smaller model for simple tasks",
                "description": "Switch to GPT-3.5-turbo for basic text generation",
                "estimated_savings_percent": 10.0,
                "implementation_difficulty": "low",
            },
        ]

        mock_rate_limiting_service.get_cost_optimization_recommendations = AsyncMock(
            return_value=sample_recommendations
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/rate-limits/optimization/openai")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["category"] == "rate_limiting"
        assert data[0]["priority"] == "high"
        assert data[1]["category"] == "model_selection"

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_get_cost_optimization_default_service(
        self, mock_session, mock_rate_limiting_service, mock_log_performance
    ):
        """Test cost optimization with default service parameter."""
        mock_rate_limiting_service.get_cost_optimization_recommendations = AsyncMock(
            return_value=[]
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/rate-limits/optimization/")

        assert response.status_code == 200
        mock_rate_limiting_service.get_cost_optimization_recommendations.assert_called_once_with(
            mock_session.return_value.__aenter__.return_value,
            "openai",  # default service
        )

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_get_cost_optimization_error(
        self, mock_session, mock_rate_limiting_service, mock_log_performance
    ):
        """Test cost optimization with service error."""
        mock_rate_limiting_service.get_cost_optimization_recommendations = AsyncMock(
            side_effect=Exception("Analysis error")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/rate-limits/optimization/openai")

        assert response.status_code == 500
        assert "Failed to generate recommendations" in response.json()["detail"]


class TestUpdateRateLimits:
    """Test rate limit update endpoint."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_update_rate_limits_success(
        self, mock_session, mock_rate_limiting_service, mock_log_performance
    ):
        """Test successful rate limit update."""
        mock_rate_limiting_service.update_rate_limits = AsyncMock(return_value=True)

        limits_data = {
            "requests_per_minute": {
                "limit": 3000,
                "window_seconds": 60,
                "burst_allowance": 1.2,
            },
            "tokens_per_minute": {
                "limit": 150000,
                "window_seconds": 60,
                "burst_allowance": 1.5,
            },
        }

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.put("/api/rate-limits/limits/openai", json=limits_data)

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "openai"
        assert data["status"] == "success"
        assert "updated_at" in data
        assert "updated_limits" in data

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_update_rate_limits_invalid_type(
        self, mock_session, mock_rate_limiting_service, mock_log_performance
    ):
        """Test rate limit update with invalid limit type."""
        mock_rate_limiting_service.update_rate_limits = AsyncMock(return_value=True)

        limits_data = {
            "invalid_limit_type": {"limit": 1000, "window_seconds": 60},
            "requests_per_minute": {"limit": 3000, "window_seconds": 60},
        }

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.put("/api/rate-limits/limits/openai", json=limits_data)

        assert response.status_code == 200  # Should succeed with valid limits only

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_update_rate_limits_no_valid_limits(self, mock_session):
        """Test rate limit update with no valid limits."""
        limits_data = {
            "invalid_type_1": {"limit": 1000},
            "invalid_type_2": {"limit": 2000},
        }

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.put("/api/rate-limits/limits/openai", json=limits_data)

        assert response.status_code == 400
        assert "No valid rate limits provided" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    async def test_update_rate_limits_service_failure(
        self, mock_session, mock_rate_limiting_service, mock_log_performance
    ):
        """Test rate limit update with service failure."""
        mock_rate_limiting_service.update_rate_limits = AsyncMock(return_value=False)

        limits_data = {"requests_per_minute": {"limit": 3000, "window_seconds": 60}}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.put("/api/rate-limits/limits/openai", json=limits_data)

        assert response.status_code == 500
        assert "Failed to update rate limits" in response.json()["detail"]


class TestListServices:
    """Test services listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_services_success(self, mock_rate_limiting_service):
        """Test successful services listing."""
        mock_rate_limits = {
            "openai": {
                RateLimitType.REQUESTS_PER_MINUTE: RateLimit(
                    limit=3000, window_seconds=60, burst_allowance=1.2
                ),
                RateLimitType.TOKENS_PER_MINUTE: RateLimit(
                    limit=150000, window_seconds=60, burst_allowance=1.5
                ),
            },
            "anthropic": {
                RateLimitType.REQUESTS_PER_MINUTE: RateLimit(
                    limit=1000, window_seconds=60, burst_allowance=1.0
                )
            },
        }

        mock_rate_limiting_service.rate_limits = mock_rate_limits

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/rate-limits/services")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        openai_service = next(s for s in data if s["name"] == "openai")
        assert len(openai_service["rate_limits"]) == 2
        assert "requests_per_minute" in openai_service["rate_limits"]
        assert "tokens_per_minute" in openai_service["rate_limits"]

    @pytest.mark.asyncio
    async def test_list_services_empty(self, mock_rate_limiting_service):
        """Test services listing when no services configured."""
        mock_rate_limiting_service.rate_limits = {}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/rate-limits/services")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_list_services_error(self, mock_rate_limiting_service):
        """Test services listing with error."""
        mock_rate_limiting_service.rate_limits = None  # Cause AttributeError

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/rate-limits/services")

        assert response.status_code == 500
        assert "Failed to list services" in response.json()["detail"]


class TestHealthCheck:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, mock_rate_limiting_service):
        """Test healthy rate limiting service."""
        mock_rate_limiting_service.rate_limits = {"openai": {}, "anthropic": {}}
        mock_rate_limiting_service.token_buckets = {
            "openai": {"bucket1": Mock(), "bucket2": Mock()},
            "anthropic": {"bucket1": Mock()},
        }

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/rate-limits/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services_configured"] == 2
        assert data["token_buckets_active"] == 3
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, mock_rate_limiting_service):
        """Test unhealthy rate limiting service."""
        mock_rate_limiting_service.rate_limits = None  # Cause error

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/rate-limits/health")

        assert response.status_code == 200  # Endpoint returns 200 even when unhealthy
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data
        assert "timestamp" in data


class TestRateLimitsEndpointsIntegration:
    """Test rate limits endpoints integration scenarios."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.rate_limits.get_async_session")
    @patch("jd_ingestion.api.endpoints.rate_limits.log_performance_metric")
    async def test_performance_logging_integration(
        self,
        mock_log_metric,
        mock_session,
        mock_rate_limiting_service,
        mock_log_performance,
    ):
        """Test that performance metrics are logged correctly."""
        mock_rate_limiting_service.rate_limits = {"openai": {}}
        mock_rate_limiting_service.get_usage_stats = AsyncMock(return_value={})
        mock_rate_limiting_service.token_buckets = {}
        mock_rate_limiting_service.get_recommended_delay = AsyncMock(return_value=0.0)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/rate-limits/status/openai")

        assert response.status_code == 200
        mock_log_metric.assert_called_once()
        args = mock_log_metric.call_args[0]
        assert args[0] == "rate_limit_status"  # metric name
        assert isinstance(args[1], float)  # duration

    @pytest.mark.asyncio
    async def test_query_parameter_validation(self):
        """Test query parameter validation."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            # Test invalid estimated_tokens (should be >= 1)
            response = await ac.post(
                "/api/rate-limits/check/openai",
                params={"operation_type": "test", "estimated_tokens": 0},
            )
            assert response.status_code == 422

            # Test invalid estimated_cost (should be >= 0)
            response = await ac.post(
                "/api/rate-limits/check/openai",
                params={"operation_type": "test", "estimated_cost": -1.0},
            )
            assert response.status_code == 422

            # Test invalid tokens_used in record endpoint (should be >= 0)
            response = await ac.post(
                "/api/rate-limits/record/openai",
                params={"operation_type": "test", "tokens_used": -10},
            )
            assert response.status_code == 422
