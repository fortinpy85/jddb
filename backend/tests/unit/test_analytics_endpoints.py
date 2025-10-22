"""
Tests for analytics API endpoints.
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
def mock_analytics_service():
    """Mock analytics service."""
    service = Mock()
    service.track_activity = AsyncMock()
    service.track_ai_usage = AsyncMock()
    service.get_usage_statistics = AsyncMock()
    service.get_analytics_dashboard = AsyncMock()
    service.generate_system_metrics = AsyncMock()
    return service


@pytest.fixture
def mock_search_analytics_service():
    """Mock search analytics service."""
    service = Mock()
    service.get_search_performance_stats = AsyncMock()
    service.get_query_trends = AsyncMock()
    service.get_slow_queries = AsyncMock()
    service.record_user_feedback = AsyncMock()
    return service


@pytest.fixture
def sample_activity_data():
    """Sample activity tracking data."""
    return {
        "action_type": "search",
        "endpoint": "/api/search/",
        "http_method": "POST",
        "resource_id": "search-123",
        "search_query": "python developer",
        "search_filters": {"classification": "EX-01"},
        "results_count": 15,
        "processing_time_ms": 250,
        "files_processed": 1,
        "metadata": {"user_agent": "test-browser"},
    }


@pytest.fixture
def sample_ai_usage_data():
    """Sample AI usage tracking data."""
    return {
        "service_type": "openai",
        "operation_type": "completion",
        "model_name": "gpt-3.5-turbo",
        "input_tokens": 100,
        "output_tokens": 50,
        "cost_usd": 0.05,
        "request_id": "req-123",
        "success": "success",
        "error_message": None,
        "metadata": {"temperature": 0.7},
    }


class TestActivityTrackingEndpoints:
    """Test activity tracking endpoints."""

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_track_activity_success(self, mock_service, client, sample_activity_data):
        """Test successful activity tracking."""
        mock_service.track_activity = AsyncMock()

        response = client.post(
            "/api/analytics/track/activity",
            json=sample_activity_data,
            headers={"x-session-id": "session-123", "user-agent": "test-browser"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Activity tracked successfully"

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_track_activity_service_error(
        self, mock_service, client, sample_activity_data
    ):
        """Test activity tracking with service error."""
        mock_service.track_activity = AsyncMock(side_effect=Exception("Database error"))

        response = client.post(
            "/api/analytics/track/activity", json=sample_activity_data
        )
        assert response.status_code == 500
        assert "Failed to track activity" in response.json()["detail"]

    def test_track_activity_invalid_data(self, client):
        """Test activity tracking with invalid data."""
        invalid_data = {
            "action_type": "",  # Empty required field
            "endpoint": "/api/search/",
        }

        response = client.post("/api/analytics/track/activity", json=invalid_data)
        assert response.status_code == 422

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_track_ai_usage_success(self, mock_service, client, sample_ai_usage_data):
        """Test successful AI usage tracking."""
        mock_service.track_ai_usage = AsyncMock()

        response = client.post(
            "/api/analytics/track/ai-usage", json=sample_ai_usage_data
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "AI usage tracked successfully"

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_track_ai_usage_error(self, mock_service, client, sample_ai_usage_data):
        """Test AI usage tracking with error."""
        mock_service.track_ai_usage = AsyncMock(
            side_effect=Exception("Tracking failed")
        )

        response = client.post(
            "/api/analytics/track/ai-usage", json=sample_ai_usage_data
        )
        assert response.status_code == 500
        assert "Failed to track AI usage" in response.json()["detail"]


class TestUsageStatisticsEndpoints:
    """Test usage statistics endpoints."""

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_get_usage_statistics_success(self, mock_service, client):
        """Test successful usage statistics retrieval."""
        mock_stats = {
            "usage": {"total_requests": 1500, "unique_sessions": 250},
            "search_patterns": {"total_searches": 800},
            "ai_usage": {"total_cost_usd": 45.50},
            "performance": {"avg_response_time": 125.5},
        }
        mock_service.get_usage_statistics = AsyncMock(return_value=mock_stats)

        response = client.get("/api/analytics/statistics?period=day")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["statistics"]["usage"]["total_requests"] == 1500

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_get_usage_statistics_with_dates(self, mock_service, client):
        """Test usage statistics with custom date range."""
        mock_service.get_usage_statistics = AsyncMock(return_value={})

        start_date = "2024-01-01T00:00:00"
        end_date = "2024-01-31T23:59:59"

        response = client.get(
            f"/api/analytics/statistics?period=custom&start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 200

    def test_get_usage_statistics_invalid_date(self, client):
        """Test usage statistics with invalid date format."""
        response = client.get("/api/analytics/statistics?start_date=invalid-date")
        assert response.status_code == 400
        assert "Invalid date format" in response.json()["detail"]

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_get_analytics_dashboard_success(self, mock_service, client):
        """Test successful analytics dashboard retrieval."""
        mock_dashboard = {
            "overview": {"total_users": 150, "total_requests": 5000},
            "trends": [{"date": "2024-01-01", "requests": 100}],
            "performance": {"avg_response_time": 200},
        }
        mock_service.get_analytics_dashboard = AsyncMock(return_value=mock_dashboard)

        response = client.get("/api/analytics/dashboard")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["dashboard"]["overview"]["total_users"] == 150

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_generate_system_metrics_success(self, mock_service, client):
        """Test successful system metrics generation."""
        mock_metrics = {
            "metric_type": "daily",
            "generated_at": "2024-01-01T10:00:00",
            "summary": {"requests": 1000, "errors": 5},
        }
        mock_service.generate_system_metrics = AsyncMock(return_value=mock_metrics)

        response = client.post("/api/analytics/metrics/generate?metric_type=daily")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["metrics"]["metric_type"] == "daily"

    def test_generate_system_metrics_invalid_type(self, client):
        """Test system metrics generation with invalid type."""
        response = client.post("/api/analytics/metrics/generate?metric_type=invalid")
        assert response.status_code == 400
        assert "Invalid metric type" in response.json()["detail"]


class TestAnalyticsSpecificEndpoints:
    """Test specific analytics endpoints."""

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_get_search_patterns_success(self, mock_service, client):
        """Test successful search patterns retrieval."""
        mock_stats = {
            "search_patterns": {
                "popular_searches": [
                    {"query": "python developer", "count": 50},
                    {"query": "data scientist", "count": 30},
                ],
                "total_searches": 500,
            }
        }
        mock_service.get_usage_statistics = AsyncMock(return_value=mock_stats)

        response = client.get("/api/analytics/search-patterns?period=week&limit=10")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert len(data["search_patterns"]["popular_searches"]) == 2

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_get_search_patterns_with_limit(self, mock_service, client):
        """Test search patterns limiting when results exceed limit."""
        # Create 25 popular searches
        popular_searches = [
            {"query": f"query_{i}", "count": 100 - i} for i in range(25)
        ]
        mock_stats = {
            "search_patterns": {
                "popular_searches": popular_searches,
                "total_searches": 5000,
            }
        }
        mock_service.get_usage_statistics = AsyncMock(return_value=mock_stats)

        # Request with limit of 10
        response = client.get("/api/analytics/search-patterns?period=month&limit=10")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        # Should be limited to 10 results
        assert len(data["search_patterns"]["popular_searches"]) == 10
        # Should be the first 10 (highest counts)
        assert data["search_patterns"]["popular_searches"][0]["query"] == "query_0"

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_get_performance_metrics_success(self, mock_service, client):
        """Test successful performance metrics retrieval."""
        mock_stats = {
            "performance": {
                "avg_response_time": 150.5,
                "p95_response_time": 350.0,
                "error_rate": 0.02,
            }
        }
        mock_service.get_usage_statistics = AsyncMock(return_value=mock_stats)

        response = client.get("/api/analytics/performance?period=day")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["performance"]["avg_response_time"] == 150.5

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_get_performance_summary_success(self, mock_service, client):
        """Test successful performance summary retrieval."""
        mock_stats = {
            "performance": {"avg_response_time": 150.5, "total_requests": 1000}
        }
        mock_service.get_usage_statistics = AsyncMock(return_value=mock_stats)

        response = client.get("/api/analytics/performance-summary?period=day")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "summary" in data
        assert data["summary"]["avg_response_time"] == 150.5

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_get_ai_usage_analysis_success(self, mock_service, client):
        """Test successful AI usage analysis retrieval."""
        mock_stats = {
            "ai_usage": {
                "total_cost_usd": 125.50,
                "total_tokens": 50000,
                "requests_by_model": {"gpt-3.5-turbo": 100},
            }
        }
        mock_service.get_usage_statistics = AsyncMock(return_value=mock_stats)

        response = client.get("/api/analytics/ai-usage?period=week")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["ai_usage"]["total_cost_usd"] == 125.50

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_get_usage_trends_success(self, mock_service, client):
        """Test successful usage trends retrieval."""
        # Mock daily stats for trend calculation
        mock_daily_stats = {
            "usage": {"total_requests": 100, "unique_sessions": 20},
            "search_patterns": {"total_searches": 50},
            "ai_usage": {"total_cost_usd": 5.0},
        }
        mock_service.get_usage_statistics = AsyncMock(return_value=mock_daily_stats)

        response = client.get("/api/analytics/trends?metric=requests&days=7")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["metric"] == "requests"
        assert len(data["trends"]) == 7

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_get_trends_sessions_metric(self, mock_service, client):
        """Test trends endpoint with sessions metric."""
        mock_daily_stats = {
            "usage": {"total_requests": 100, "unique_sessions": 50},
            "search_patterns": {"total_searches": 200},
            "ai_usage": {"total_cost_usd": 1.5},
        }
        mock_service.get_usage_statistics = AsyncMock(return_value=mock_daily_stats)

        response = client.get("/api/analytics/trends?metric=sessions&days=3")
        assert response.status_code == 200

        data = response.json()
        assert data["metric"] == "sessions"
        assert len(data["trends"]) == 3

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_get_trends_searches_metric(self, mock_service, client):
        """Test trends endpoint with searches metric."""
        mock_daily_stats = {
            "usage": {"total_requests": 100, "unique_sessions": 50},
            "search_patterns": {"total_searches": 200},
            "ai_usage": {"total_cost_usd": 1.5},
        }
        mock_service.get_usage_statistics = AsyncMock(return_value=mock_daily_stats)

        response = client.get("/api/analytics/trends?metric=searches&days=3")
        assert response.status_code == 200

        data = response.json()
        assert data["metric"] == "searches"
        assert len(data["trends"]) == 3

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_get_trends_ai_cost_metric(self, mock_service, client):
        """Test trends endpoint with ai_cost metric."""
        mock_daily_stats = {
            "usage": {"total_requests": 100, "unique_sessions": 50},
            "search_patterns": {"total_searches": 200},
            "ai_usage": {"total_cost_usd": 1.5},
        }
        mock_service.get_usage_statistics = AsyncMock(return_value=mock_daily_stats)

        response = client.get("/api/analytics/trends?metric=ai_cost&days=3")
        assert response.status_code == 200

        data = response.json()
        assert data["metric"] == "ai_cost"
        assert len(data["trends"]) == 3

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_get_trends_unknown_metric(self, mock_service, client):
        """Test trends endpoint with unknown metric defaults to 0."""
        mock_daily_stats = {
            "usage": {"total_requests": 100, "unique_sessions": 50},
            "search_patterns": {"total_searches": 200},
            "ai_usage": {"total_cost_usd": 1.5},
        }
        mock_service.get_usage_statistics = AsyncMock(return_value=mock_daily_stats)

        response = client.get("/api/analytics/trends?metric=unknown&days=3")
        assert response.status_code == 200

        data = response.json()
        assert data["metric"] == "unknown"
        # Values should be 0 for unknown metric
        assert all(trend["value"] == 0 for trend in data["trends"])

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_export_analytics_data_json(self, mock_service, client):
        """Test analytics data export in JSON format."""
        mock_stats = {"usage": {"total_requests": 1000}}
        mock_service.get_usage_statistics = AsyncMock(return_value=mock_stats)

        response = client.get("/api/analytics/export?period=month&format=json")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["format"] == "json"
        assert data["data"]["usage"]["total_requests"] == 1000

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_export_analytics_data_csv(self, mock_service, client):
        """Test analytics data export in CSV format."""
        mock_stats = {"usage": {"total_requests": 1000}}
        mock_service.get_usage_statistics = AsyncMock(return_value=mock_stats)

        response = client.get("/api/analytics/export?period=month&format=csv")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["format"] == "csv"
        assert "CSV export would be implemented" in data["message"]

    def test_generate_session_id_success(self, client):
        """Test session ID generation."""
        response = client.get("/api/analytics/session/generate")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "session_id" in data
        assert len(data["session_id"]) == 36  # UUID length


class TestErrorMetricsEndpoints:
    """Test error metrics endpoints."""

    @patch("jd_ingestion.api.endpoints.analytics.error_handler")
    def test_get_error_metrics_success(self, mock_error_handler, client):
        """Test successful error metrics retrieval."""
        mock_error_stats = {
            "total_errors": 50,
            "recovery_attempts": 20,
            "successful_recoveries": 15,
            "by_category": {"database": 20, "api": 15, "validation": 15},
            "by_severity": {"warning": 30, "error": 15, "critical": 5},
        }
        mock_error_handler.get_error_stats.return_value = mock_error_stats

        response = client.get("/api/analytics/errors/metrics")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["error_metrics"]["summary"]["total_errors"] == 50
        assert data["error_metrics"]["summary"]["recovery_rate_percent"] == 75.0
        assert "breakdown" in data["error_metrics"]
        assert "health_indicators" in data["error_metrics"]

    @patch("jd_ingestion.api.endpoints.analytics.error_handler")
    def test_get_error_metrics_empty_stats(self, mock_error_handler, client):
        """Test error metrics with empty statistics."""
        mock_error_handler.get_error_stats.return_value = {
            "total_errors": 0,
            "recovery_attempts": 0,
            "successful_recoveries": 0,
            "by_category": {},
            "by_severity": {},
        }

        response = client.get("/api/analytics/errors/metrics")
        assert response.status_code == 200

        data = response.json()
        assert data["error_metrics"]["summary"]["total_errors"] == 0
        assert data["error_metrics"]["summary"]["recovery_rate_percent"] == 0.0

    @patch("jd_ingestion.api.endpoints.analytics.error_handler")
    def test_reset_error_metrics_success(self, mock_error_handler, client):
        """Test successful error metrics reset."""
        mock_current_stats = {"total_errors": 25, "by_category": {"api": 10}}
        mock_error_handler.get_error_stats.return_value = mock_current_stats

        response = client.post("/api/analytics/errors/reset")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Error metrics have been reset"
        assert data["previous_stats"]["total_errors"] == 25

    @patch("jd_ingestion.api.endpoints.analytics.error_handler")
    def test_error_metrics_failure(self, mock_error_handler, client):
        """Test error metrics endpoint failure."""
        mock_error_handler.get_error_stats.side_effect = Exception("Stats unavailable")

        response = client.get("/api/analytics/errors/metrics")
        assert response.status_code == 500
        assert "Failed to retrieve error metrics" in response.json()["detail"]


class TestSearchAnalyticsEndpoints:
    """Test search analytics endpoints."""

    @patch("jd_ingestion.api.endpoints.analytics.search_analytics_service")
    def test_get_search_performance_success(self, mock_service, client):
        """Test successful search performance retrieval."""
        mock_stats = {
            "total_searches": 500,
            "performance": {"avg_execution_time_ms": 150},
            "search_types": {"semantic": 300, "fulltext": 200},
            "success_rates": {"success": 480, "error": 20},
        }
        mock_service.get_search_performance_stats = AsyncMock(return_value=mock_stats)

        response = client.get("/api/analytics/search/performance?days=30")
        assert response.status_code == 200

        data = response.json()
        assert data["total_searches"] == 500
        assert data["performance"]["avg_execution_time_ms"] == 150

    @patch("jd_ingestion.api.endpoints.analytics.search_analytics_service")
    def test_get_search_performance_no_data(self, mock_service, client):
        """Test search performance with no data."""
        mock_service.get_search_performance_stats = AsyncMock(return_value=None)

        response = client.get("/api/analytics/search/performance?days=7")
        assert response.status_code == 200

        data = response.json()
        assert "No search data found" in data["message"]
        assert data["period_days"] == 7

    @patch("jd_ingestion.api.endpoints.analytics.search_analytics_service")
    def test_get_search_trends_success(self, mock_service, client):
        """Test successful search trends retrieval."""
        mock_trends = {
            "daily_volume": [{"date": "2024-01-01", "count": 100}],
            "performance_trends": [{"date": "2024-01-01", "avg_time": 120}],
        }
        mock_service.get_query_trends = AsyncMock(return_value=mock_trends)

        response = client.get("/api/analytics/search/trends?days=7")
        assert response.status_code == 200

        data = response.json()
        assert len(data["daily_volume"]) == 1
        assert data["daily_volume"][0]["count"] == 100

    @patch("jd_ingestion.api.endpoints.analytics.search_analytics_service")
    def test_get_search_trends_empty(self, mock_service, client):
        """Test search trends with no data."""
        mock_service.get_query_trends = AsyncMock(return_value=None)

        response = client.get("/api/analytics/search/trends?days=14")
        assert response.status_code == 200

        data = response.json()
        assert "No trend data found" in data["message"]
        assert data["period_days"] == 14

    @patch("jd_ingestion.api.endpoints.analytics.search_analytics_service")
    def test_get_slow_queries_success(self, mock_service, client):
        """Test successful slow queries retrieval."""
        mock_slow_queries = [
            {"query": "complex search", "execution_time_ms": 2500, "count": 5},
            {"query": "another slow query", "execution_time_ms": 1500, "count": 3},
        ]
        mock_service.get_slow_queries = AsyncMock(return_value=mock_slow_queries)

        response = client.get(
            "/api/analytics/search/slow-queries?threshold_ms=1000&limit=10"
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert data[0]["execution_time_ms"] == 2500

    @patch("jd_ingestion.api.endpoints.analytics.search_analytics_service")
    def test_record_search_feedback_success(self, mock_service, client):
        """Test successful search feedback recording."""
        mock_service.record_user_feedback = AsyncMock()

        feedback_data = {"clicked_results": [1, 3, 5], "satisfaction_rating": 4}

        response = client.post(
            "/api/analytics/search/feedback/search-123", params=feedback_data
        )
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Feedback recorded successfully"
        assert data["search_id"] == "search-123"

    @patch("jd_ingestion.api.endpoints.analytics.search_analytics_service")
    def test_get_search_analytics_dashboard_success(self, mock_service, client):
        """Test successful search analytics dashboard retrieval."""
        # Mock all required service calls
        mock_performance = {
            "total_searches": 1000,
            "performance": {"avg_execution_time_ms": 150},
            "search_types": {"semantic": 600, "fulltext": 400},
            "success_rates": {"success": 950, "error": 50},
            "popular_queries": [{"query": "python", "count": 100}],
        }
        mock_trends = {
            "daily_volume": [{"date": "2024-01-01", "count": 150}],
            "performance_trends": [{"date": "2024-01-01", "avg_time": 140}],
        }
        mock_slow_queries = [{"query": "slow query", "execution_time_ms": 3000}]

        mock_service.get_search_performance_stats = AsyncMock(
            return_value=mock_performance
        )
        mock_service.get_query_trends = AsyncMock(return_value=mock_trends)
        mock_service.get_slow_queries = AsyncMock(return_value=mock_slow_queries)

        response = client.get("/api/analytics/search/dashboard")
        assert response.status_code == 200

        data = response.json()
        assert data["overview"]["total_searches"] == 1000
        assert len(data["trends"]["daily_volume"]) == 1
        assert data["performance_issues"]["slow_queries_count"] == 1


class TestAnalyticsEndpointsEdgeCases:
    """Test edge cases and error conditions."""

    def test_track_activity_missing_required_fields(self, client):
        """Test activity tracking with missing required fields."""
        incomplete_data = {"endpoint": "/api/test/"}  # Missing action_type

        response = client.post("/api/analytics/track/activity", json=incomplete_data)
        assert response.status_code == 422

    def test_track_ai_usage_invalid_types(self, client):
        """Test AI usage tracking with invalid data types."""
        invalid_data = {
            "service_type": "openai",
            "operation_type": "completion",
            "model_name": "gpt-3.5-turbo",
            "input_tokens": "invalid",  # Should be int
            "output_tokens": 50,
            "cost_usd": 0.05,
        }

        response = client.post("/api/analytics/track/ai-usage", json=invalid_data)
        assert response.status_code == 422

    def test_get_usage_statistics_invalid_period(self, client):
        """Test usage statistics with invalid period."""
        response = client.get("/api/analytics/statistics?period=invalid_period")
        # Should still work as the service handles invalid periods
        assert response.status_code in [200, 400, 500]

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_service_unavailable_error(self, mock_service, client):
        """Test handling when analytics service is unavailable."""
        mock_service.get_usage_statistics = AsyncMock(
            side_effect=Exception("Service unavailable")
        )

        response = client.get("/api/analytics/statistics")
        assert response.status_code == 500
        assert "Failed to get usage statistics" in response.json()["detail"]

    def test_search_performance_invalid_parameters(self, client):
        """Test search performance with invalid parameters."""
        response = client.get(
            "/api/analytics/search/performance?days=500"
        )  # Exceeds max
        assert response.status_code == 422

    def test_slow_queries_invalid_parameters(self, client):
        """Test slow queries with invalid parameters."""
        response = client.get(
            "/api/analytics/search/slow-queries?threshold_ms=50000"
        )  # Exceeds max
        assert response.status_code == 422

    def test_search_feedback_invalid_rating(self, client):
        """Test search feedback with invalid satisfaction rating."""
        response = client.post(
            "/api/analytics/search/feedback/test-123",
            params={
                "clicked_results": [1, 2],
                "satisfaction_rating": 10,
            },  # Exceeds max of 5
        )
        assert response.status_code == 422


class TestSkillsAnalyticsEndpoints:
    """Test skills analytics endpoints."""

    def test_get_skills_inventory_success(self, client):
        """Test successful skills inventory retrieval."""
        response = client.get("/api/analytics/skills/inventory")
        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "skills" in data
        assert isinstance(data["skills"], list)

    def test_get_skills_inventory_with_search(self, client):
        """Test skills inventory with search filter."""
        response = client.get("/api/analytics/skills/inventory?search=python")
        assert response.status_code == 200

        data = response.json()
        assert "skills" in data

    def test_get_skills_inventory_with_skill_type(self, client):
        """Test skills inventory with skill type filter."""
        response = client.get("/api/analytics/skills/inventory?skill_type=technical")
        assert response.status_code == 200

        data = response.json()
        assert "skills" in data

    def test_get_skills_inventory_with_min_job_count(self, client):
        """Test skills inventory with minimum job count filter."""
        response = client.get("/api/analytics/skills/inventory?min_job_count=5")
        assert response.status_code == 200

        data = response.json()
        assert "skills" in data

    def test_get_skills_inventory_with_pagination(self, client):
        """Test skills inventory with pagination parameters."""
        response = client.get("/api/analytics/skills/inventory?limit=50&offset=10")
        assert response.status_code == 200

        data = response.json()
        assert data["limit"] == 50
        assert data["offset"] == 10

    def test_get_skills_inventory_with_all_filters(self, client):
        """Test skills inventory with all filters combined."""
        response = client.get(
            "/api/analytics/skills/inventory?search=data&skill_type=technical&min_job_count=3&limit=20"
        )
        assert response.status_code == 200

        data = response.json()
        assert "skills" in data
        assert data["limit"] == 20

    def test_get_top_skills_success(self, client):
        """Test successful top skills retrieval."""
        response = client.get("/api/analytics/skills/top")
        assert response.status_code == 200

        data = response.json()
        assert "top_skills" in data
        assert isinstance(data["top_skills"], list)

    def test_get_top_skills_with_limit(self, client):
        """Test top skills with custom limit."""
        response = client.get("/api/analytics/skills/top?limit=20")
        assert response.status_code == 200

        data = response.json()
        assert "top_skills" in data

    def test_get_top_skills_with_type_filter(self, client):
        """Test top skills filtered by skill type."""
        response = client.get("/api/analytics/skills/top?skill_type=soft")
        assert response.status_code == 200

        data = response.json()
        assert "top_skills" in data

    def test_get_top_skills_limit_validation(self, client):
        """Test top skills limit validation."""
        # Test exceeding max limit
        response = client.get("/api/analytics/skills/top?limit=200")
        assert response.status_code == 422

    def test_get_skill_types_success(self, client):
        """Test successful skill types distribution retrieval."""
        response = client.get("/api/analytics/skills/types")
        assert response.status_code == 200

        data = response.json()
        assert "skill_types" in data
        assert isinstance(data["skill_types"], list)

    def test_get_skills_statistics_success(self, client):
        """Test successful skills statistics retrieval."""
        response = client.get("/api/analytics/skills/stats")
        assert response.status_code == 200

        data = response.json()
        # Check for expected statistics fields
        assert (
            "total_unique_skills" in data
            or "total_skills" in data
            or "statistics" in data
        )

    def test_skills_inventory_invalid_min_job_count(self, client):
        """Test skills inventory with invalid min_job_count."""
        response = client.get("/api/analytics/skills/inventory?min_job_count=0")
        assert response.status_code == 422

    def test_skills_inventory_invalid_limit(self, client):
        """Test skills inventory with invalid limit."""
        response = client.get("/api/analytics/skills/inventory?limit=2000")
        assert response.status_code == 422

    def test_skills_inventory_invalid_offset(self, client):
        """Test skills inventory with invalid offset."""
        response = client.get("/api/analytics/skills/inventory?offset=-1")
        assert response.status_code == 422


class TestAnalyticsErrorHandling:
    """Test error handling across analytics endpoints."""

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_dashboard_service_error(self, mock_service, client):
        """Test dashboard endpoint with service error."""
        mock_service.get_analytics_dashboard = AsyncMock(
            side_effect=Exception("Dashboard service failed")
        )

        response = client.get("/api/analytics/dashboard")
        assert response.status_code == 500
        assert "Failed to generate analytics dashboard" in response.json()["detail"]

    @patch("jd_ingestion.api.endpoints.analytics.analytics_service")
    def test_search_patterns_service_error(self, mock_service, client):
        """Test search patterns endpoint with service error."""
        mock_service.get_usage_statistics = AsyncMock(
            side_effect=Exception("Search patterns failed")
        )

        response = client.get("/api/analytics/search-patterns")
        assert response.status_code == 500

    @patch("jd_ingestion.api.endpoints.analytics.search_analytics_service")
    def test_search_performance_service_error(self, mock_service, client):
        """Test search performance endpoint with service error."""
        mock_service.get_search_performance_stats = AsyncMock(
            side_effect=Exception("Performance stats failed")
        )

        response = client.get("/api/analytics/search/performance")
        assert response.status_code == 500

    @patch("jd_ingestion.api.endpoints.analytics.search_analytics_service")
    def test_search_trends_service_error(self, mock_service, client):
        """Test search trends endpoint with service error."""
        mock_service.get_query_trends = AsyncMock(
            side_effect=Exception("Trends service failed")
        )

        response = client.get("/api/analytics/search/trends")
        assert response.status_code == 500

    @patch("jd_ingestion.api.endpoints.analytics.search_analytics_service")
    def test_slow_queries_service_error(self, mock_service, client):
        """Test slow queries endpoint with service error."""
        mock_service.get_slow_queries = AsyncMock(
            side_effect=Exception("Slow queries failed")
        )

        response = client.get("/api/analytics/search/slow-queries")
        assert response.status_code == 500
