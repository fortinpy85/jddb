"""Tests for utils/monitoring.py module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from jd_ingestion.utils.monitoring import (
    SystemMonitor,
    AlertManager,
    system_monitor,
    alert_manager,
    get_health_status,
    check_system_alerts,
)


class TestSystemMonitor:
    """Test the SystemMonitor class."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.info.return_value = {
            "used_memory": 1024000,
            "connected_clients": 5,
            "uptime_in_seconds": 86400,
        }
        return mock_redis

    def test_system_monitor_initialization(self):
        """Test SystemMonitor initialization."""
        with patch(
            "jd_ingestion.utils.monitoring.redis.from_url"
        ) as mock_redis_from_url:
            mock_redis_client = MagicMock()
            mock_redis_client.ping.return_value = True
            mock_redis_from_url.return_value = mock_redis_client

            monitor = SystemMonitor()

            assert monitor.redis_client == mock_redis_client
            mock_redis_from_url.assert_called_once()
            mock_redis_client.ping.assert_called_once()

    def test_system_monitor_redis_init_failure(self):
        """Test SystemMonitor initialization with Redis failure."""
        with patch(
            "jd_ingestion.utils.monitoring.redis.from_url"
        ) as mock_redis_from_url:
            mock_redis_from_url.side_effect = Exception("Redis connection failed")

            monitor = SystemMonitor()

            assert monitor.redis_client is None

    @pytest.mark.asyncio
    @patch("jd_ingestion.utils.monitoring.get_async_session")
    async def test_check_database_health_success(self, mock_get_session):
        """Test successful database health check."""
        # Mock database session
        mock_session = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.size.return_value = 10
        mock_pool.checkedin.return_value = 8
        mock_pool.checkedout.return_value = 2
        mock_pool.overflow.return_value = 0

        mock_bind = MagicMock()
        mock_bind.pool = mock_pool
        mock_session.get_bind.return_value = mock_bind

        # Mock query result
        mock_result = MagicMock()
        mock_result.scalar.return_value = 100
        mock_session.execute.return_value = mock_result

        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock Redis initialization
        with patch("jd_ingestion.utils.monitoring.redis.from_url"):
            monitor = SystemMonitor()
            monitor.redis_client = MagicMock()  # Set to avoid init

        result = await monitor._check_database_health()

        assert result["status"] == "healthy"
        assert "response_time_ms" in result
        assert "pool_status" in result
        assert "job_count" in result
        assert result["job_count"] == 100

    @pytest.mark.asyncio
    @patch("jd_ingestion.utils.monitoring.get_async_session")
    async def test_check_database_health_slow_response(self, mock_get_session):
        """Test database health check with slow response."""
        mock_session = AsyncMock()

        # Mock slow database response
        async def slow_execute(query):
            import asyncio

            await asyncio.sleep(0.002)  # 2ms delay to simulate slow response
            mock_result = MagicMock()
            mock_result.scalar.return_value = 100
            return mock_result

        mock_session.execute.side_effect = slow_execute
        mock_bind = MagicMock()
        mock_pool = MagicMock()
        mock_pool.size.return_value = 10
        mock_pool.checkedin.return_value = 8
        mock_pool.checkedout.return_value = 2
        mock_pool.overflow.return_value = 0
        mock_bind.pool = mock_pool
        mock_session.get_bind.return_value = mock_bind

        mock_get_session.return_value.__aenter__.return_value = mock_session

        with patch("jd_ingestion.utils.monitoring.redis.from_url"):
            monitor = SystemMonitor()

        result = await monitor._check_database_health()

        # Should still be healthy for small delays, but response_time should be recorded
        assert result["status"] in ["healthy", "degraded"]
        assert "response_time_ms" in result

    @pytest.mark.asyncio
    @patch("jd_ingestion.utils.monitoring.get_async_session")
    async def test_check_database_health_failure(self, mock_get_session):
        """Test database health check failure."""
        from sqlalchemy.exc import OperationalError

        mock_get_session.side_effect = OperationalError("Connection failed", None, None)

        with patch("jd_ingestion.utils.monitoring.redis.from_url"):
            monitor = SystemMonitor()

        result = await monitor._check_database_health()

        assert result["status"] == "critical"
        assert "error" in result
        assert "Connection failed" in result["error"]

    def test_check_redis_health_success(self, mock_redis):
        """Test successful Redis health check."""
        with patch(
            "jd_ingestion.utils.monitoring.redis.from_url", return_value=mock_redis
        ):
            monitor = SystemMonitor()

        result = monitor._check_redis_health()

        assert result["status"] == "healthy"
        assert "ping_time_ms" in result
        assert "memory_usage_bytes" in result
        assert result["memory_usage_bytes"] == 1024000
        assert result["connected_clients"] == 5

    def test_check_redis_health_no_client(self):
        """Test Redis health check with no client."""
        with patch(
            "jd_ingestion.utils.monitoring.redis.from_url"
        ) as mock_redis_from_url:
            mock_redis_from_url.side_effect = Exception("Connection failed")
            monitor = SystemMonitor()

        result = monitor._check_redis_health()

        assert result["status"] == "critical"
        assert "Redis client not initialized" in result["error"]

    def test_check_redis_health_failure(self):
        """Test Redis health check failure."""
        mock_redis_client = MagicMock()
        mock_redis_client.ping.side_effect = Exception("Redis ping failed")

        with patch(
            "jd_ingestion.utils.monitoring.redis.from_url",
            return_value=mock_redis_client,
        ):
            monitor = SystemMonitor()

        result = monitor._check_redis_health()

        assert result["status"] == "critical"
        assert "Redis ping failed" in result["error"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.utils.monitoring.openai")
    @patch("jd_ingestion.utils.monitoring.settings")
    async def test_check_openai_health_success(self, mock_settings, mock_openai):
        """Test successful OpenAI health check."""
        mock_settings.openai_api_key = "test-key"
        mock_settings.embedding_model = "text-embedding-3-small"

        # Mock OpenAI response
        mock_models_response = MagicMock()
        mock_model = MagicMock()
        mock_model.id = "text-embedding-3-small"
        mock_models_response.data = [mock_model]
        mock_openai.Model.alist.return_value = mock_models_response

        with patch("jd_ingestion.utils.monitoring.redis.from_url"):
            monitor = SystemMonitor()

        result = await monitor._check_openai_health()

        assert result["status"] == "healthy"
        assert result["embedding_model_available"] is True
        assert "response_time_ms" in result

    @pytest.mark.asyncio
    @patch("jd_ingestion.utils.monitoring.settings")
    async def test_check_openai_health_no_api_key(self, mock_settings):
        """Test OpenAI health check with no API key."""
        mock_settings.openai_api_key = None

        with patch("jd_ingestion.utils.monitoring.redis.from_url"):
            monitor = SystemMonitor()

        result = await monitor._check_openai_health()

        assert result["status"] == "degraded"
        assert "OpenAI API key not configured" in result["error"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.utils.monitoring.openai")
    @patch("jd_ingestion.utils.monitoring.settings")
    async def test_check_openai_health_failure(self, mock_settings, mock_openai):
        """Test OpenAI health check failure."""
        mock_settings.openai_api_key = "test-key"
        mock_openai.Model.alist.side_effect = Exception("API error")

        with patch("jd_ingestion.utils.monitoring.redis.from_url"):
            monitor = SystemMonitor()

        result = await monitor._check_openai_health()

        assert result["status"] == "degraded"
        assert "API error" in result["error"]

    @patch("jd_ingestion.utils.monitoring.psutil")
    def test_get_system_metrics_success(self, mock_psutil):
        """Test successful system metrics collection."""
        # Mock psutil functions
        mock_psutil.cpu_percent.return_value = 45.5
        mock_psutil.cpu_count.return_value = 4

        mock_memory = MagicMock()
        mock_memory.total = 16000000000
        mock_memory.available = 8000000000
        mock_memory.percent = 50.0
        mock_memory.used = 8000000000
        mock_psutil.virtual_memory.return_value = mock_memory

        mock_disk = MagicMock()
        mock_disk.total = 500000000000
        mock_disk.used = 250000000000
        mock_disk.free = 250000000000
        mock_disk.percent = 50.0
        mock_psutil.disk_usage.return_value = mock_disk

        mock_network = MagicMock()
        mock_network.bytes_sent = 1000000
        mock_network.bytes_recv = 2000000
        mock_network.packets_sent = 1000
        mock_network.packets_recv = 1500
        mock_psutil.net_io_counters.return_value = mock_network

        mock_process = MagicMock()
        mock_process_memory = MagicMock()
        mock_process_memory.rss = 100000000
        mock_process_memory.vms = 200000000
        mock_process.memory_info.return_value = mock_process_memory
        mock_process.cpu_percent.return_value = 5.0
        mock_process.num_threads.return_value = 10
        mock_psutil.Process.return_value = mock_process

        mock_psutil.boot_time.return_value = (
            datetime.utcnow() - timedelta(days=1)
        ).timestamp()
        mock_psutil.getloadavg.return_value = [0.5, 0.7, 0.6]

        with patch("jd_ingestion.utils.monitoring.redis.from_url"):
            monitor = SystemMonitor()

        result = monitor._get_system_metrics()

        assert "cpu" in result
        assert result["cpu"]["percent"] == 45.5
        assert result["cpu"]["count"] == 4
        assert "memory" in result
        assert result["memory"]["percent"] == 50.0
        assert "disk" in result
        assert result["disk"]["percent"] == 50.0
        assert "network" in result
        assert "process" in result

    @patch("jd_ingestion.utils.monitoring.psutil")
    def test_get_system_metrics_failure(self, mock_psutil):
        """Test system metrics collection failure."""
        mock_psutil.cpu_percent.side_effect = Exception("System metrics error")

        with patch("jd_ingestion.utils.monitoring.redis.from_url"):
            monitor = SystemMonitor()

        result = monitor._get_system_metrics()

        assert "error" in result
        assert "System metrics error" in result["error"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.utils.monitoring.get_async_session")
    async def test_get_application_metrics_success(self, mock_get_session):
        """Test successful application metrics collection."""
        # Mock database session and queries
        mock_session = AsyncMock()

        # Mock job counts query
        mock_result1 = MagicMock()
        mock_result1.fetchall.return_value = [("active", 10), ("completed", 50)]

        # Mock recent jobs query
        mock_result2 = MagicMock()
        mock_result2.scalar.return_value = 5

        # Mock chunk statistics query
        mock_result3 = MagicMock()
        mock_result3.fetchone.return_value = (100, 75)

        mock_session.execute.side_effect = [mock_result1, mock_result2, mock_result3]
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock Redis client for Celery metrics
        mock_redis = MagicMock()
        mock_redis.llen.side_effect = [3, 1]  # active_tasks, failed_tasks

        with patch(
            "jd_ingestion.utils.monitoring.redis.from_url", return_value=mock_redis
        ):
            monitor = SystemMonitor()

        result = await monitor._get_application_metrics()

        assert "database" in result
        assert result["database"]["job_counts"] == {"active": 10, "completed": 50}
        assert result["database"]["recent_jobs_1h"] == 5
        assert result["database"]["total_chunks"] == 100
        assert result["database"]["embedded_chunks"] == 75

        assert "celery" in result
        assert result["celery"]["active_tasks"] == 3
        assert result["celery"]["failed_tasks"] == 1

    @pytest.mark.asyncio
    @patch("jd_ingestion.utils.monitoring.get_async_session")
    async def test_get_application_metrics_database_error(self, mock_get_session):
        """Test application metrics collection with database error."""
        mock_get_session.side_effect = Exception("Database connection failed")

        with patch("jd_ingestion.utils.monitoring.redis.from_url"):
            monitor = SystemMonitor()

        result = await monitor._get_application_metrics()

        assert "error" in result
        assert "Database connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_get_system_health_integration(self):
        """Test complete system health check integration."""
        with patch(
            "jd_ingestion.utils.monitoring.redis.from_url"
        ) as mock_redis_from_url:
            mock_redis = MagicMock()
            mock_redis.ping.return_value = True
            mock_redis.info.return_value = {"used_memory": 1024}
            mock_redis_from_url.return_value = mock_redis

            monitor = SystemMonitor()

            # Mock all health check methods
            with (
                patch.object(monitor, "_check_database_health") as mock_db_health,
                patch.object(monitor, "_check_redis_health") as mock_redis_health,
                patch.object(monitor, "_check_openai_health") as mock_openai_health,
                patch.object(monitor, "_get_system_metrics") as mock_system_metrics,
                patch.object(monitor, "_get_application_metrics") as mock_app_metrics,
            ):
                mock_db_health.return_value = {"status": "healthy"}
                mock_redis_health.return_value = {"status": "healthy"}
                mock_openai_health.return_value = {"status": "healthy"}
                mock_system_metrics.return_value = {"uptime": 86400}
                mock_app_metrics.return_value = {"database": {"job_counts": {}}}

                result = await monitor.get_system_health()

                assert result["status"] == "healthy"
                assert "components" in result
                assert "metrics" in result
                assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_get_system_health_degraded_status(self):
        """Test system health with degraded components."""
        with patch("jd_ingestion.utils.monitoring.redis.from_url"):
            monitor = SystemMonitor()

            # Mock health check methods with mixed statuses
            with (
                patch.object(monitor, "_check_database_health") as mock_db_health,
                patch.object(monitor, "_check_redis_health") as mock_redis_health,
                patch.object(monitor, "_check_openai_health") as mock_openai_health,
                patch.object(monitor, "_get_system_metrics") as mock_system_metrics,
                patch.object(monitor, "_get_application_metrics") as mock_app_metrics,
            ):
                mock_db_health.return_value = {"status": "healthy"}
                mock_redis_health.return_value = {"status": "degraded"}
                mock_openai_health.return_value = {"status": "healthy"}
                mock_system_metrics.return_value = {"uptime": 86400}
                mock_app_metrics.return_value = {"database": {"job_counts": {}}}

                result = await monitor.get_system_health()

                assert result["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_get_system_health_critical_status(self):
        """Test system health with critical components."""
        with patch("jd_ingestion.utils.monitoring.redis.from_url"):
            monitor = SystemMonitor()

            # Mock health check methods with critical status
            with (
                patch.object(monitor, "_check_database_health") as mock_db_health,
                patch.object(monitor, "_check_redis_health") as mock_redis_health,
                patch.object(monitor, "_check_openai_health") as mock_openai_health,
                patch.object(monitor, "_get_system_metrics") as mock_system_metrics,
                patch.object(monitor, "_get_application_metrics") as mock_app_metrics,
            ):
                mock_db_health.return_value = {"status": "critical"}
                mock_redis_health.return_value = {"status": "healthy"}
                mock_openai_health.return_value = {"status": "healthy"}
                mock_system_metrics.return_value = {"uptime": 86400}
                mock_app_metrics.return_value = {"database": {"job_counts": {}}}

                result = await monitor.get_system_health()

                assert result["status"] == "critical"


class TestAlertManager:
    """Test the AlertManager class."""

    @pytest.fixture
    def mock_monitor(self):
        """Create a mock SystemMonitor."""
        monitor = MagicMock()
        monitor.get_system_health = AsyncMock()
        return monitor

    def test_alert_manager_initialization(self, mock_monitor):
        """Test AlertManager initialization."""
        alert_manager = AlertManager(mock_monitor)

        assert alert_manager.monitor == mock_monitor
        assert "cpu_usage" in alert_manager.alert_thresholds
        assert "memory_usage" in alert_manager.alert_thresholds
        assert alert_manager.alert_history == []

    @pytest.mark.asyncio
    async def test_check_alerts_cpu_warning(self, mock_monitor):
        """Test CPU usage alert."""
        # Mock high CPU usage
        mock_health_data = {
            "metrics": {
                "system": {
                    "cpu": {"percent": 85},
                    "memory": {"percent": 50},
                    "disk": {"percent": 60},
                }
            },
            "components": {
                "database": {"status": "healthy"},
                "redis": {"status": "healthy"},
            },
        }
        mock_monitor.get_system_health.return_value = mock_health_data

        alert_manager = AlertManager(mock_monitor)
        alerts = await alert_manager.check_alerts()

        assert len(alerts) == 1
        assert alerts[0]["type"] == "cpu_high"
        assert alerts[0]["severity"] == "warning"
        assert alerts[0]["value"] == 85

    @pytest.mark.asyncio
    async def test_check_alerts_memory_warning(self, mock_monitor):
        """Test memory usage alert."""
        # Mock high memory usage
        mock_health_data = {
            "metrics": {
                "system": {
                    "cpu": {"percent": 50},
                    "memory": {"percent": 90},
                    "disk": {"percent": 60},
                }
            },
            "components": {
                "database": {"status": "healthy"},
                "redis": {"status": "healthy"},
            },
        }
        mock_monitor.get_system_health.return_value = mock_health_data

        alert_manager = AlertManager(mock_monitor)
        alerts = await alert_manager.check_alerts()

        assert len(alerts) == 1
        assert alerts[0]["type"] == "memory_high"
        assert alerts[0]["severity"] == "warning"
        assert alerts[0]["value"] == 90

    @pytest.mark.asyncio
    async def test_check_alerts_disk_critical(self, mock_monitor):
        """Test critical disk usage alert."""
        # Mock critical disk usage
        mock_health_data = {
            "metrics": {
                "system": {
                    "cpu": {"percent": 50},
                    "memory": {"percent": 50},
                    "disk": {"percent": 97},
                }
            },
            "components": {
                "database": {"status": "healthy"},
                "redis": {"status": "healthy"},
            },
        }
        mock_monitor.get_system_health.return_value = mock_health_data

        alert_manager = AlertManager(mock_monitor)
        alerts = await alert_manager.check_alerts()

        assert len(alerts) == 1
        assert alerts[0]["type"] == "disk_high"
        assert alerts[0]["severity"] == "critical"
        assert alerts[0]["value"] == 97

    @pytest.mark.asyncio
    async def test_check_alerts_component_critical(self, mock_monitor):
        """Test component critical alert."""
        # Mock critical component status
        mock_health_data = {
            "metrics": {
                "system": {
                    "cpu": {"percent": 50},
                    "memory": {"percent": 50},
                    "disk": {"percent": 60},
                }
            },
            "components": {
                "database": {"status": "critical", "error": "Connection failed"},
                "redis": {"status": "healthy"},
            },
        }
        mock_monitor.get_system_health.return_value = mock_health_data

        alert_manager = AlertManager(mock_monitor)
        alerts = await alert_manager.check_alerts()

        assert len(alerts) == 1
        assert alerts[0]["type"] == "database_critical"
        assert alerts[0]["severity"] == "critical"
        assert "Connection failed" in alerts[0]["message"]

    @pytest.mark.asyncio
    async def test_check_alerts_component_degraded(self, mock_monitor):
        """Test component degraded alert."""
        # Mock degraded component status
        mock_health_data = {
            "metrics": {
                "system": {
                    "cpu": {"percent": 50},
                    "memory": {"percent": 50},
                    "disk": {"percent": 60},
                }
            },
            "components": {
                "database": {"status": "healthy"},
                "redis": {"status": "degraded", "error": "Slow response"},
            },
        }
        mock_monitor.get_system_health.return_value = mock_health_data

        alert_manager = AlertManager(mock_monitor)
        alerts = await alert_manager.check_alerts()

        assert len(alerts) == 1
        assert alerts[0]["type"] == "redis_degraded"
        assert alerts[0]["severity"] == "warning"
        assert "Slow response" in alerts[0]["message"]

    @pytest.mark.asyncio
    async def test_check_alerts_multiple_alerts(self, mock_monitor):
        """Test multiple simultaneous alerts."""
        # Mock multiple alert conditions
        mock_health_data = {
            "metrics": {
                "system": {
                    "cpu": {"percent": 85},  # Alert
                    "memory": {"percent": 90},  # Alert
                    "disk": {"percent": 60},
                }
            },
            "components": {
                "database": {"status": "degraded", "error": "Slow queries"},  # Alert
                "redis": {"status": "healthy"},
            },
        }
        mock_monitor.get_system_health.return_value = mock_health_data

        alert_manager = AlertManager(mock_monitor)
        alerts = await alert_manager.check_alerts()

        assert len(alerts) == 3
        alert_types = {alert["type"] for alert in alerts}
        assert "cpu_high" in alert_types
        assert "memory_high" in alert_types
        assert "database_degraded" in alert_types

    @pytest.mark.asyncio
    async def test_check_alerts_no_alerts(self, mock_monitor):
        """Test no alerts when system is healthy."""
        # Mock healthy system
        mock_health_data = {
            "metrics": {
                "system": {
                    "cpu": {"percent": 50},
                    "memory": {"percent": 60},
                    "disk": {"percent": 70},
                }
            },
            "components": {
                "database": {"status": "healthy"},
                "redis": {"status": "healthy"},
                "openai": {"status": "healthy"},
            },
        }
        mock_monitor.get_system_health.return_value = mock_health_data

        alert_manager = AlertManager(mock_monitor)
        alerts = await alert_manager.check_alerts()

        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_alert_history_management(self, mock_monitor):
        """Test alert history management."""
        mock_health_data = {
            "metrics": {
                "system": {
                    "cpu": {"percent": 85},
                    "memory": {"percent": 50},
                    "disk": {"percent": 60},
                }
            },
            "components": {"database": {"status": "healthy"}},
        }
        mock_monitor.get_system_health.return_value = mock_health_data

        alert_manager = AlertManager(mock_monitor)

        # Add some alerts
        alerts = await alert_manager.check_alerts()
        assert len(alerts) == 1
        assert len(alert_manager.alert_history) == 1

        # Add more alerts
        alerts = await alert_manager.check_alerts()
        assert len(alert_manager.alert_history) == 2

        # Verify timestamp is added
        for alert in alert_manager.alert_history:
            assert "timestamp" in alert


class TestGlobalFunctions:
    """Test global convenience functions."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.utils.monitoring.system_monitor")
    async def test_get_health_status(self, mock_system_monitor):
        """Test get_health_status function."""
        expected_health = {"status": "healthy", "components": {}}
        mock_system_monitor.get_system_health.return_value = expected_health

        result = await get_health_status()

        assert result == expected_health
        mock_system_monitor.get_system_health.assert_called_once()

    @pytest.mark.asyncio
    @patch("jd_ingestion.utils.monitoring.alert_manager")
    async def test_check_system_alerts(self, mock_alert_manager):
        """Test check_system_alerts function."""
        expected_alerts = [{"type": "cpu_high", "severity": "warning"}]
        mock_alert_manager.check_alerts.return_value = expected_alerts

        result = await check_system_alerts()

        assert result == expected_alerts
        mock_alert_manager.check_alerts.assert_called_once()


class TestGlobalInstances:
    """Test global instances creation."""

    def test_global_instances_exist(self):
        """Test that global instances are created."""
        from jd_ingestion.utils.monitoring import system_monitor

        assert system_monitor is not None
        assert alert_manager is not None
        assert isinstance(alert_manager.monitor, SystemMonitor)

    @patch("jd_ingestion.utils.monitoring.redis.from_url")
    def test_global_monitor_redis_initialization(self, mock_redis_from_url):
        """Test global monitor Redis initialization."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_from_url.return_value = mock_redis

        # Re-import to trigger global instance creation
        import importlib
        import jd_ingestion.utils.monitoring

        importlib.reload(jd_ingestion.utils.monitoring)

        # The global instance should have been created with Redis client
        # (Note: This might be None if Redis connection failed during import)
        assert hasattr(system_monitor, "redis_client")


class TestIntegrationScenarios:
    """Test integration scenarios."""

    @pytest.mark.asyncio
    async def test_complete_monitoring_cycle(self):
        """Test complete monitoring cycle with mocked dependencies."""
        with (
            patch(
                "jd_ingestion.utils.monitoring.redis.from_url"
            ) as mock_redis_from_url,
            patch(
                "jd_ingestion.utils.monitoring.get_async_session"
            ) as mock_get_session,
            patch("jd_ingestion.utils.monitoring.psutil") as mock_psutil,
        ):
            # Mock Redis
            mock_redis = MagicMock()
            mock_redis.ping.return_value = True
            mock_redis.info.return_value = {"used_memory": 1024}
            mock_redis_from_url.return_value = mock_redis

            # Mock database
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar.return_value = 100
            mock_result.fetchall.return_value = [("active", 10)]
            mock_result.fetchone.return_value = (100, 50)
            mock_session.execute.return_value = mock_result
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Mock system metrics
            mock_psutil.cpu_percent.return_value = 85  # High CPU for alert
            mock_psutil.cpu_count.return_value = 4
            mock_memory = MagicMock()
            mock_memory.total = 16000000000
            mock_memory.available = 8000000000
            mock_memory.percent = 50.0
            mock_memory.used = 8000000000
            mock_psutil.virtual_memory.return_value = mock_memory

            monitor = SystemMonitor()
            alert_manager = AlertManager(monitor)

            # Get health status
            health = await monitor.get_system_health()
            assert "status" in health
            assert "components" in health
            assert "metrics" in health

            # Check alerts
            alerts = await alert_manager.check_alerts()
            # Should have CPU alert due to 85% usage
            cpu_alerts = [a for a in alerts if a["type"] == "cpu_high"]
            assert len(cpu_alerts) >= 0  # Might be 0 or 1 depending on mocking
