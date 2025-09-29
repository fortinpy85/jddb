"""
Tests for health check endpoints.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import HTTPException

from jd_ingestion.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_health_status():
    """Mock health status data."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": {
                "status": "healthy",
                "response_time": 0.05,
                "last_check": datetime.utcnow().isoformat(),
            },
            "redis": {
                "status": "healthy",
                "response_time": 0.02,
                "last_check": datetime.utcnow().isoformat(),
            },
            "openai": {
                "status": "healthy",
                "response_time": 0.15,
                "last_check": datetime.utcnow().isoformat(),
            },
        },
        "metrics": {
            "system": {"cpu_percent": 45.2, "memory_percent": 62.1, "disk_usage": 78.5},
            "application": {
                "total_requests": 1250,
                "active_connections": 15,
                "error_rate": 0.02,
            },
        },
    }


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_basic_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/api/health/")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "jd-ingestion"
        assert data["version"] == "1.0.0"

    @patch("jd_ingestion.api.endpoints.health.get_health_status")
    @patch("jd_ingestion.api.endpoints.health.log_business_metric")
    def test_detailed_health_check_success(
        self, mock_log_metric, mock_health_status, client, mock_health_data
    ):
        """Test detailed health check success."""
        mock_health_status.return_value = mock_health_data

        response = client.get("/api/health/detailed")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert "metrics" in data

        mock_health_status.assert_called_once()
        mock_log_metric.assert_called_once_with(
            "health_check_requests", 1, "counter", {"type": "detailed"}
        )

    @patch("jd_ingestion.api.endpoints.health.get_health_status")
    def test_detailed_health_check_failure(self, mock_health_status, client):
        """Test detailed health check failure."""
        mock_health_status.side_effect = Exception("Health check failed")

        response = client.get("/api/health/detailed")
        assert response.status_code == 503
        assert "Health check failed" in response.json()["detail"]

    @patch("jd_ingestion.api.endpoints.health.check_system_alerts")
    @patch("jd_ingestion.api.endpoints.health.log_business_metric")
    def test_system_alerts_success(self, mock_log_metric, mock_alerts, client):
        """Test system alerts endpoint success."""
        mock_alerts.return_value = [
            {
                "severity": "warning",
                "message": "High memory usage",
                "timestamp": "2024-01-01T10:00:00",
            }
        ]

        response = client.get("/api/health/alerts")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["severity"] == "warning"

        mock_alerts.assert_called_once()
        mock_log_metric.assert_called_once_with("alert_check_requests", 1, "counter")

    @patch("jd_ingestion.api.endpoints.health.check_system_alerts")
    def test_system_alerts_failure(self, mock_alerts, client):
        """Test system alerts endpoint failure."""
        mock_alerts.side_effect = Exception("Alert check failed")

        response = client.get("/api/health/alerts")
        assert response.status_code == 500
        assert "Alert check failed" in response.json()["detail"]

    def test_component_health_invalid_component(self, client):
        """Test component health with invalid component name."""
        response = client.get("/api/health/components/invalid")
        assert response.status_code == 400
        assert "Invalid component" in response.json()["detail"]

    @patch("jd_ingestion.api.endpoints.health.get_health_status")
    def test_component_health_valid_component(
        self, mock_health_status, client, mock_health_status
    ):
        """Test component health with valid component."""
        mock_health_status.return_value = mock_health_status

        response = client.get("/api/health/components/database")
        assert response.status_code == 200

        data = response.json()
        assert data["component"] == "database"
        assert data["status"] == "healthy"

    @patch("jd_ingestion.api.endpoints.health.get_health_status")
    def test_component_health_not_found(self, mock_health_status, client):
        """Test component health when component not found."""
        mock_health_status.return_value = {"components": {}}

        response = client.get("/api/health/components/database")
        assert response.status_code == 404
        assert "Component not found" in response.json()["detail"]

    @patch("jd_ingestion.api.endpoints.health.get_health_status")
    def test_system_metrics(self, mock_health_status, client, mock_health_status):
        """Test system metrics endpoint."""
        mock_health_status.return_value = mock_health_status

        response = client.get("/api/health/metrics/system")
        assert response.status_code == 200

        data = response.json()
        assert "timestamp" in data
        assert "metrics" in data
        assert data["metrics"]["cpu_percent"] == 45.2

    @patch("jd_ingestion.api.endpoints.health.get_health_status")
    def test_application_metrics(self, mock_health_status, client, mock_health_status):
        """Test application metrics endpoint."""
        mock_health_status.return_value = mock_health_status

        response = client.get("/api/health/metrics/application")
        assert response.status_code == 200

        data = response.json()
        assert "timestamp" in data
        assert "metrics" in data
        assert data["metrics"]["total_requests"] == 1250

    @patch("jd_ingestion.api.endpoints.health.system_monitor")
    @patch("jd_ingestion.api.endpoints.health.log_business_metric")
    def test_warmup_services(self, mock_log_metric, mock_system_monitor, client):
        """Test warmup services endpoint."""
        mock_system_monitor._check_database_health = AsyncMock()
        mock_system_monitor._check_redis_health = Mock()
        mock_system_monitor._check_openai_health = AsyncMock()

        response = client.post("/api/health/warmup")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Warmup initiated"
        assert "timestamp" in data

    @patch("jd_ingestion.api.endpoints.health.get_health_status")
    def test_readiness_check_ready(self, mock_health_status, client):
        """Test readiness check when service is ready."""
        mock_health_status.return_value = {
            "components": {
                "database": {"status": "healthy"},
                "redis": {"status": "healthy"},
            }
        }

        response = client.get("/api/health/readiness")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ready"
        assert "database" in data["checked_components"]
        assert "redis" in data["checked_components"]

    @patch("jd_ingestion.api.endpoints.health.get_health_status")
    def test_readiness_check_database_critical(self, mock_health_status, client):
        """Test readiness check when database is critical."""
        mock_health_status.return_value = {
            "components": {
                "database": {"status": "critical"},
                "redis": {"status": "healthy"},
            }
        }

        response = client.get("/api/health/readiness")
        assert response.status_code == 503
        assert "Database not ready" in response.json()["detail"]

    @patch("jd_ingestion.api.endpoints.health.get_health_status")
    def test_readiness_check_redis_critical(self, mock_health_status, client):
        """Test readiness check when Redis is critical."""
        mock_health_status.return_value = {
            "components": {
                "database": {"status": "healthy"},
                "redis": {"status": "critical"},
            }
        }

        response = client.get("/api/health/readiness")
        assert response.status_code == 503
        assert "Redis not ready" in response.json()["detail"]

    def test_liveness_check(self, client):
        """Test liveness check endpoint."""
        response = client.get("/api/health/liveness")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
        assert "uptime_seconds" in data

    @patch("jd_ingestion.api.endpoints.health.get_health_status")
    def test_startup_check_started(self, mock_health_status, client):
        """Test startup check when service is started."""
        mock_health_status.return_value = {
            "components": {
                "database": {"status": "healthy"},
                "redis": {"status": "healthy"},
            }
        }

        response = client.get("/api/health/startup")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "started"
        assert "database" in data["initialized_components"]
        assert "redis" in data["initialized_components"]

    @patch("jd_ingestion.api.endpoints.health.get_health_status")
    def test_startup_check_not_initialized(self, mock_health_status, client):
        """Test startup check when component not initialized."""
        mock_health_status.return_value = {
            "components": {
                "database": {"error": "not initialized"},
                "redis": {"status": "healthy"},
            }
        }

        response = client.get("/api/health/startup")
        assert response.status_code == 503
        assert "not initialized" in response.json()["detail"]
