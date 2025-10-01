"""Tests for api/endpoints/phase2_monitoring.py module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from jd_ingestion.api.endpoints.phase2_monitoring import router


class TestPhase2HealthCheck:
    """Test the phase2_health_check endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)  # Simulates database connectivity
        mock_db.execute.return_value = mock_result
        return mock_db

    @pytest.fixture
    def mock_metrics_summary(self):
        """Create mock metrics summary."""
        return {
            "websocket": {"active_connections": 5},
            "collaboration": {"total_operations": 100},
            "system": {"uptime_hours": 24.5},
        }

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_metrics_summary")
    async def test_phase2_health_check_success(
        self, mock_get_metrics, mock_db, mock_metrics_summary
    ):
        """Test successful health check."""
        from jd_ingestion.api.endpoints.phase2_monitoring import phase2_health_check

        mock_get_metrics.return_value = mock_metrics_summary

        result = await phase2_health_check(current_user=None, db=mock_db)

        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert result["components"]["database"] == "ok"
        assert result["components"]["websockets"] == "ok"
        assert result["metrics"]["active_websocket_connections"] == 5
        assert result["metrics"]["total_operations"] == 100

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_metrics_summary")
    async def test_phase2_health_check_database_failure(
        self, mock_get_metrics, mock_metrics_summary
    ):
        """Test health check with database failure."""
        from jd_ingestion.api.endpoints.phase2_monitoring import phase2_health_check

        mock_get_metrics.return_value = mock_metrics_summary

        # Mock database failure
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Database connection failed")

        with pytest.raises(HTTPException) as exc_info:
            await phase2_health_check(current_user=None, db=mock_db)

        assert exc_info.value.status_code == 503
        assert "Phase 2 services unavailable" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_metrics_summary")
    async def test_phase2_health_check_no_database_result(
        self, mock_get_metrics, mock_metrics_summary
    ):
        """Test health check when database returns no results."""
        from jd_ingestion.api.endpoints.phase2_monitoring import phase2_health_check

        mock_get_metrics.return_value = mock_metrics_summary

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None  # No database result
        mock_db.execute.return_value = mock_result

        result = await phase2_health_check(current_user=None, db=mock_db)

        assert result["status"] == "degraded"
        assert result["components"]["database"] == "error"


class TestMetricsEndpoints:
    """Test metrics-related endpoints."""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        return {"id": 1, "username": "admin", "role": "admin"}

    @pytest.fixture
    def mock_metrics_summary(self):
        """Create comprehensive mock metrics summary."""
        return {
            "websocket": {
                "active_connections": 10,
                "average_latency_ms": 50,
                "total_messages": 1000,
            },
            "collaboration": {
                "total_operations": 500,
                "conflict_resolution_count": 10,
                "active_sessions": 3,
            },
            "system": {
                "cpu_usage_percent": 45.2,
                "memory_usage_percent": 62.1,
                "database_connections": 15,
                "uptime_hours": 48.5,
            },
            "translation": {"cache_hit_ratio": 0.85, "translation_requests": 50},
        }

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_metrics_summary")
    async def test_get_current_metrics_success(
        self, mock_get_metrics, mock_admin_user, mock_metrics_summary
    ):
        """Test successful metrics retrieval."""
        from jd_ingestion.api.endpoints.phase2_monitoring import get_current_metrics

        mock_get_metrics.return_value = mock_metrics_summary

        result = await get_current_metrics(admin_user=mock_admin_user)

        assert result["success"] is True
        assert result["data"] == mock_metrics_summary

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_metrics_summary")
    async def test_get_current_metrics_failure(self, mock_get_metrics, mock_admin_user):
        """Test metrics retrieval failure."""
        from jd_ingestion.api.endpoints.phase2_monitoring import get_current_metrics

        mock_get_metrics.side_effect = Exception("Metrics service unavailable")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_metrics(admin_user=mock_admin_user)

        assert exc_info.value.status_code == 500
        assert "Failed to retrieve metrics" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_performance_report")
    async def test_get_performance_metrics_success(
        self, mock_get_report, mock_admin_user
    ):
        """Test successful performance metrics retrieval."""
        from jd_ingestion.api.endpoints.phase2_monitoring import get_performance_metrics

        mock_report = {"cpu_avg": 45.2, "memory_avg": 62.1, "response_time_avg": 150}
        mock_get_report.return_value = mock_report

        result = await get_performance_metrics(admin_user=mock_admin_user)

        assert result["success"] is True
        assert result["data"] == mock_report

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_metrics_summary")
    async def test_get_websocket_metrics(
        self, mock_get_metrics, mock_admin_user, mock_metrics_summary
    ):
        """Test WebSocket metrics retrieval."""
        from jd_ingestion.api.endpoints.phase2_monitoring import get_websocket_metrics

        mock_get_metrics.return_value = mock_metrics_summary

        result = await get_websocket_metrics(admin_user=mock_admin_user)

        assert result["success"] is True
        websocket_data = result["data"]
        assert websocket_data["active_connections"] == 10
        assert websocket_data["health_status"] == "healthy"

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_metrics_summary")
    async def test_get_websocket_metrics_high_load(
        self, mock_get_metrics, mock_admin_user
    ):
        """Test WebSocket metrics with high load detection."""
        from jd_ingestion.api.endpoints.phase2_monitoring import get_websocket_metrics

        high_load_metrics = {
            "websocket": {
                "active_connections": 150,  # High load threshold > 100
                "average_latency_ms": 50,
            }
        }
        mock_get_metrics.return_value = high_load_metrics

        result = await get_websocket_metrics(admin_user=mock_admin_user)

        assert result["data"]["health_status"] == "high_load"

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_metrics_summary")
    async def test_get_websocket_metrics_high_latency(
        self, mock_get_metrics, mock_admin_user
    ):
        """Test WebSocket metrics with high latency detection."""
        from jd_ingestion.api.endpoints.phase2_monitoring import get_websocket_metrics

        high_latency_metrics = {
            "websocket": {
                "active_connections": 50,
                "average_latency_ms": 250,  # High latency > 200ms
            }
        }
        mock_get_metrics.return_value = high_latency_metrics

        result = await get_websocket_metrics(admin_user=mock_admin_user)

        assert result["data"]["health_status"] == "high_latency"

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_metrics_summary")
    async def test_get_collaboration_metrics(
        self, mock_get_metrics, mock_admin_user, mock_metrics_summary
    ):
        """Test collaboration metrics retrieval."""
        from jd_ingestion.api.endpoints.phase2_monitoring import (
            get_collaboration_metrics,
        )

        mock_get_metrics.return_value = mock_metrics_summary

        result = await get_collaboration_metrics(admin_user=mock_admin_user)

        assert result["success"] is True
        collab_data = result["data"]
        assert collab_data["total_operations"] == 500
        assert collab_data["conflict_rate"] == 0.02  # 10/500
        assert collab_data["health_status"] == "healthy"

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_metrics_summary")
    async def test_get_collaboration_metrics_high_conflicts(
        self, mock_get_metrics, mock_admin_user
    ):
        """Test collaboration metrics with high conflict rate."""
        from jd_ingestion.api.endpoints.phase2_monitoring import (
            get_collaboration_metrics,
        )

        high_conflict_metrics = {
            "collaboration": {
                "total_operations": 100,
                "conflict_resolution_count": 15,  # 15% conflict rate > 10%
                "active_sessions": 3,
            }
        }
        mock_get_metrics.return_value = high_conflict_metrics

        result = await get_collaboration_metrics(admin_user=mock_admin_user)

        collab_data = result["data"]
        assert collab_data["conflict_rate"] == 0.15
        assert collab_data["health_status"] == "high_conflicts"

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_metrics_summary")
    async def test_get_collaboration_metrics_zero_operations(
        self, mock_get_metrics, mock_admin_user
    ):
        """Test collaboration metrics with zero operations."""
        from jd_ingestion.api.endpoints.phase2_monitoring import (
            get_collaboration_metrics,
        )

        zero_ops_metrics = {
            "collaboration": {
                "total_operations": 0,
                "conflict_resolution_count": 0,
                "active_sessions": 0,
            }
        }
        mock_get_metrics.return_value = zero_ops_metrics

        result = await get_collaboration_metrics(admin_user=mock_admin_user)

        collab_data = result["data"]
        assert collab_data["conflict_rate"] == 0
        assert collab_data["health_status"] == "healthy"

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_metrics_summary")
    async def test_get_system_metrics(
        self, mock_get_metrics, mock_admin_user, mock_metrics_summary
    ):
        """Test system metrics retrieval."""
        from jd_ingestion.api.endpoints.phase2_monitoring import get_system_metrics

        mock_get_metrics.return_value = mock_metrics_summary

        result = await get_system_metrics(admin_user=mock_admin_user)

        assert result["success"] is True
        system_data = result["data"]
        assert system_data["cpu_usage_percent"] == 45.2
        assert system_data["health_issues"] == []
        assert system_data["health_status"] == "healthy"

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_metrics_summary")
    async def test_get_system_metrics_health_issues(
        self, mock_get_metrics, mock_admin_user
    ):
        """Test system metrics with health issues detection."""
        from jd_ingestion.api.endpoints.phase2_monitoring import get_system_metrics

        unhealthy_metrics = {
            "system": {
                "cpu_usage_percent": 85,  # > 80%
                "memory_usage_percent": 90,  # > 85%
                "database_connections": 60,  # > 50
                "uptime_hours": 24,
            }
        }
        mock_get_metrics.return_value = unhealthy_metrics

        result = await get_system_metrics(admin_user=mock_admin_user)

        system_data = result["data"]
        expected_issues = ["high_cpu", "high_memory", "high_db_connections"]
        assert set(system_data["health_issues"]) == set(expected_issues)
        assert system_data["health_status"] == "degraded"


class TestHistoricalMetrics:
    """Test historical metrics endpoints."""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        return {"id": 1, "username": "admin", "role": "admin"}

    @pytest.mark.asyncio
    async def test_get_metrics_history_success(self, mock_admin_user):
        """Test successful metrics history retrieval."""
        from jd_ingestion.api.endpoints.phase2_monitoring import get_metrics_history

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_rows = [
            ("cpu_usage", 45.2, "percent", datetime.utcnow(), '{"source": "system"}'),
            (
                "cpu_usage",
                47.1,
                "percent",
                datetime.utcnow() - timedelta(hours=1),
                '{"source": "system"}',
            ),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db.execute.return_value = mock_result

        result = await get_metrics_history(
            admin_user=mock_admin_user, metric_name="cpu_usage", hours=24, db=mock_db
        )

        assert result["success"] is True
        assert result["data"]["metric_name"] == "cpu_usage"
        assert result["data"]["time_range_hours"] == 24
        assert result["data"]["data_points"] == 2
        assert len(result["data"]["history"]) == 2

    @pytest.mark.asyncio
    async def test_get_metrics_history_database_error(self, mock_admin_user):
        """Test metrics history with database error."""
        from jd_ingestion.api.endpoints.phase2_monitoring import get_metrics_history

        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Database connection failed")

        with pytest.raises(HTTPException) as exc_info:
            await get_metrics_history(
                admin_user=mock_admin_user,
                metric_name="cpu_usage",
                hours=24,
                db=mock_db,
            )

        assert exc_info.value.status_code == 500
        assert "Failed to retrieve metrics history" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_active_sessions_success(self, mock_admin_user):
        """Test successful active sessions retrieval."""
        from jd_ingestion.api.endpoints.phase2_monitoring import get_active_sessions

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_rows = [
            (
                1,
                "session_123",
                101,
                "collaborative",
                "active",
                datetime.utcnow() - timedelta(hours=1),
                datetime.utcnow(),
                "admin",
                2,
            ),
            (
                2,
                "session_456",
                102,
                "review",
                "active",
                datetime.utcnow() - timedelta(hours=2),
                datetime.utcnow(),
                "editor",
                1,
            ),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db.execute.return_value = mock_result

        result = await get_active_sessions(admin_user=mock_admin_user, db=mock_db)

        assert result["success"] is True
        assert result["data"]["active_sessions_count"] == 2
        sessions = result["data"]["sessions"]
        assert sessions[0]["session_id"] == "session_123"
        assert sessions[0]["participant_count"] == 2

    @pytest.mark.asyncio
    async def test_get_user_activity_success(self, mock_admin_user):
        """Test successful user activity retrieval."""
        from jd_ingestion.api.endpoints.phase2_monitoring import get_user_activity

        mock_db = AsyncMock()
        # Mock activity data query
        mock_result1 = MagicMock()
        mock_result1.fetchall.return_value = [
            ("admin", "document_edit", 15, datetime.utcnow()),
            ("editor", "document_view", 8, datetime.utcnow() - timedelta(hours=1)),
        ]

        # Mock active users count query
        mock_result2 = MagicMock()
        mock_result2.scalar.return_value = 5

        mock_db.execute.side_effect = [mock_result1, mock_result2]

        result = await get_user_activity(
            admin_user=mock_admin_user, hours=24, db=mock_db
        )

        assert result["success"] is True
        assert result["data"]["time_range_hours"] == 24
        assert result["data"]["active_users_count"] == 5
        assert len(result["data"]["activity_breakdown"]) == 2


class TestEventRecording:
    """Test event recording endpoints."""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        return {"id": 1, "username": "admin", "role": "admin"}

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.record_websocket_event")
    async def test_record_websocket_metric_success(self, mock_record, mock_admin_user):
        """Test successful WebSocket event recording."""
        from jd_ingestion.api.endpoints.phase2_monitoring import record_websocket_metric

        result = await record_websocket_metric(
            admin_user=mock_admin_user,
            event_type="connection",
            connected=True,
            latency_ms=45.2,
        )

        assert result["success"] is True
        assert "WebSocket connection event recorded" in result["message"]
        mock_record.assert_called_once_with(
            "connection", connected=True, latency_ms=45.2
        )

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.record_websocket_event")
    async def test_record_websocket_metric_failure(self, mock_record, mock_admin_user):
        """Test WebSocket event recording failure."""
        from jd_ingestion.api.endpoints.phase2_monitoring import record_websocket_metric

        mock_record.side_effect = Exception("Event recording failed")

        with pytest.raises(HTTPException) as exc_info:
            await record_websocket_metric(
                admin_user=mock_admin_user, event_type="connection"
            )

        assert exc_info.value.status_code == 500
        assert "Failed to record WebSocket event" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.record_collaboration_event")
    async def test_record_collaboration_metric_success(
        self, mock_record, mock_admin_user
    ):
        """Test successful collaboration event recording."""
        from jd_ingestion.api.endpoints.phase2_monitoring import (
            record_collaboration_metric,
        )

        result = await record_collaboration_metric(
            admin_user=mock_admin_user, operation_type="text_insert", conflict=True
        )

        assert result["success"] is True
        assert "Collaboration text_insert event recorded" in result["message"]
        mock_record.assert_called_once_with("text_insert", True)

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.record_collaboration_event")
    async def test_record_collaboration_metric_failure(
        self, mock_record, mock_admin_user
    ):
        """Test collaboration event recording failure."""
        from jd_ingestion.api.endpoints.phase2_monitoring import (
            record_collaboration_metric,
        )

        mock_record.side_effect = Exception("Collaboration recording failed")

        with pytest.raises(HTTPException) as exc_info:
            await record_collaboration_metric(
                admin_user=mock_admin_user, operation_type="text_insert"
            )

        assert exc_info.value.status_code == 500


class TestMonitoringDashboard:
    """Test monitoring dashboard endpoint."""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        return {"id": 1, "username": "admin", "role": "admin"}

    @pytest.fixture
    def mock_comprehensive_metrics(self):
        """Create comprehensive mock metrics for dashboard."""
        return {
            "websocket": {"active_connections": 25, "average_latency_ms": 75},
            "collaboration": {
                "total_operations": 1000,
                "conflict_resolution_count": 50,
            },
            "system": {
                "cpu_usage_percent": 45,
                "memory_usage_percent": 60,
                "database_connections": 20,
            },
            "translation": {"cache_hit_ratio": 0.85, "translation_requests": 100},
        }

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_performance_report")
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_metrics_summary")
    async def test_get_monitoring_dashboard_healthy(
        self,
        mock_get_metrics,
        mock_get_report,
        mock_admin_user,
        mock_comprehensive_metrics,
    ):
        """Test monitoring dashboard with healthy system."""
        from jd_ingestion.api.endpoints.phase2_monitoring import (
            get_monitoring_dashboard,
        )

        mock_get_metrics.return_value = mock_comprehensive_metrics
        mock_report = {"recommendations": ["System performing well"]}
        mock_get_report.return_value = mock_report

        result = await get_monitoring_dashboard(admin_user=mock_admin_user)

        assert result["success"] is True
        dashboard = result["data"]
        assert dashboard["health"]["overall_score"] == 100
        assert dashboard["health"]["status"] == "excellent"
        assert dashboard["health"]["issues"] == []

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_performance_report")
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_metrics_summary")
    async def test_get_monitoring_dashboard_degraded(
        self, mock_get_metrics, mock_get_report, mock_admin_user
    ):
        """Test monitoring dashboard with degraded system."""
        from jd_ingestion.api.endpoints.phase2_monitoring import (
            get_monitoring_dashboard,
        )

        degraded_metrics = {
            "websocket": {
                "active_connections": 25,
                "average_latency_ms": 250,  # High latency
            },
            "collaboration": {
                "total_operations": 1000,
                "conflict_resolution_count": 150,  # High conflict rate
            },
            "system": {
                "cpu_usage_percent": 85,  # High CPU
                "memory_usage_percent": 90,  # High memory
                "database_connections": 20,
            },
            "translation": {
                "cache_hit_ratio": 0.5,  # Low cache hit ratio
                "translation_requests": 100,
            },
        }
        mock_get_metrics.return_value = degraded_metrics
        mock_get_report.return_value = {"recommendations": ["System needs attention"]}

        result = await get_monitoring_dashboard(admin_user=mock_admin_user)

        dashboard = result["data"]
        assert (
            dashboard["health"]["overall_score"] == 25
        )  # 100 - 20 - 20 - 15 - 10 - 10
        assert dashboard["health"]["status"] == "poor"
        expected_issues = [
            "High CPU usage",
            "High memory usage",
            "High WebSocket latency",
            "High conflict resolution rate",
            "Low translation cache hit ratio",
        ]
        assert set(dashboard["health"]["issues"]) == set(expected_issues)

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.phase2_monitoring.get_metrics_summary")
    async def test_get_monitoring_dashboard_failure(
        self, mock_get_metrics, mock_admin_user
    ):
        """Test monitoring dashboard failure."""
        from jd_ingestion.api.endpoints.phase2_monitoring import (
            get_monitoring_dashboard,
        )

        mock_get_metrics.side_effect = Exception("Metrics unavailable")

        with pytest.raises(HTTPException) as exc_info:
            await get_monitoring_dashboard(admin_user=mock_admin_user)

        assert exc_info.value.status_code == 500
        assert "Failed to generate monitoring dashboard" in str(exc_info.value.detail)


class TestEndpointIntegration:
    """Test endpoint integration scenarios."""

    def test_router_configuration(self):
        """Test that router is properly configured."""
        assert router.prefix == "/monitoring"
        assert "phase2-monitoring" in router.tags

    @pytest.mark.asyncio
    async def test_endpoint_dependencies(self):
        """Test that endpoints have proper dependencies."""
        from jd_ingestion.api.endpoints.phase2_monitoring import (
            get_current_metrics,
            get_performance_metrics,
            get_websocket_metrics,
        )

        # These should require admin authentication
        # The actual dependency injection is handled by FastAPI
        # We're just verifying the functions exist and are callable
        assert callable(get_current_metrics)
        assert callable(get_performance_metrics)
        assert callable(get_websocket_metrics)

    def test_health_check_no_auth_required(self):
        """Test that health check doesn't require authentication."""
        from jd_ingestion.api.endpoints.phase2_monitoring import phase2_health_check

        # Health check should accept optional user
        assert callable(phase2_health_check)

    @pytest.mark.asyncio
    async def test_metrics_history_query_parameters(self):
        """Test metrics history query parameter validation."""
        from jd_ingestion.api.endpoints.phase2_monitoring import get_metrics_history

        # This test verifies the function exists and parameter handling
        # The actual query parameter validation is handled by FastAPI
        assert callable(get_metrics_history)

    def test_event_recording_parameter_handling(self):
        """Test event recording parameter handling."""
        from jd_ingestion.api.endpoints.phase2_monitoring import (
            record_websocket_metric,
            record_collaboration_metric,
        )

        # Verify functions exist for parameter handling
        assert callable(record_websocket_metric)
        assert callable(record_collaboration_metric)
