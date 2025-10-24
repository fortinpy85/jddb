"""
Production monitoring and health check utilities.
"""

import psutil
import redis
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from openai import AsyncOpenAI

from ..config import settings
from ..database.connection import get_async_session
from .logging import (
    get_logger,
    log_performance_metric,
    log_business_metric,
    PerformanceTimer,
)

logger = get_logger(__name__)


class SystemMonitor:
    """Monitor system resources and application health."""

    def __init__(self):
        self.redis_client = None
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis client for monitoring."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url, decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Redis monitoring client initialized")
        except Exception as e:
            logger.error("Failed to initialize Redis monitoring", error=str(e))
            self.redis_client = None

    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status."""
        health_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "components": {},
            "metrics": {},
        }

        # Check database health
        db_health = await self._check_database_health()
        health_data["components"]["database"] = db_health

        # Check Redis health
        redis_health = self._check_redis_health()
        health_data["components"]["redis"] = redis_health

        # Check OpenAI API health
        openai_health = await self._check_openai_health()
        health_data["components"]["openai"] = openai_health

        # Get system metrics
        system_metrics = self._get_system_metrics()
        health_data["metrics"]["system"] = system_metrics

        # Get application metrics
        app_metrics = await self._get_application_metrics()
        health_data["metrics"]["application"] = app_metrics

        # Determine overall status
        component_statuses = [
            comp["status"] for comp in health_data["components"].values()
        ]
        if "critical" in component_statuses:
            health_data["status"] = "critical"
        elif "degraded" in component_statuses:
            health_data["status"] = "degraded"

        # Log metrics
        log_performance_metric("health_check_duration", system_metrics.get("uptime", 0))

        return health_data

    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            with PerformanceTimer("database_health_check"):
                async for session in get_async_session():
                    # Basic connectivity test
                    await session.execute(text("SELECT 1"))

                    # Check connection pool
                    bind = session.get_bind()
                    pool_status = {}
                    if hasattr(bind, "pool"):
                        pool = bind.pool  # type: ignore[attr-defined]
                        pool_status = {
                            "size": pool.size(),  # type: ignore[attr-defined,union-attr]
                            "checked_in": pool.checkedin(),  # type: ignore[attr-defined,union-attr]
                            "checked_out": pool.checkedout(),  # type: ignore[attr-defined,union-attr]
                            "overflow": pool.overflow(),  # type: ignore[attr-defined,union-attr]
                        }

                    # Test query performance
                    start_time = datetime.utcnow()
                    result = await session.execute(
                        text("SELECT COUNT(*) FROM job_descriptions")
                    )
                    job_count = result.scalar()
                    query_time = (datetime.utcnow() - start_time).total_seconds() * 1000

                    return {
                        "status": "healthy" if query_time < 1000 else "degraded",
                        "response_time_ms": query_time,
                        "pool_status": pool_status,
                        "job_count": job_count,
                        "last_check": datetime.utcnow().isoformat(),
                    }

            # Fallback if no session is available
            return {
                "status": "critical",
                "error": "No database session available",
                "last_check": datetime.utcnow().isoformat(),
            }
        except OperationalError as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "critical",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error("Database health check error", error=str(e))
            return {
                "status": "degraded",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat(),
            }

    def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        if not self.redis_client:
            return {
                "status": "critical",
                "error": "Redis client not initialized",
                "last_check": datetime.utcnow().isoformat(),
            }

        try:
            with PerformanceTimer("redis_health_check"):
                # Basic connectivity test
                start_time = datetime.utcnow()
                self.redis_client.ping()
                ping_time = (datetime.utcnow() - start_time).total_seconds() * 1000

                # Get Redis info
                info = self.redis_client.info()
                memory_usage = info.get("used_memory", 0)
                connected_clients = info.get("connected_clients", 0)

                return {
                    "status": "healthy" if ping_time < 100 else "degraded",
                    "ping_time_ms": ping_time,
                    "memory_usage_bytes": memory_usage,
                    "connected_clients": connected_clients,
                    "uptime_seconds": info.get("uptime_in_seconds", 0),
                    "last_check": datetime.utcnow().isoformat(),
                }
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            return {
                "status": "critical",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat(),
            }

    async def _check_openai_health(self) -> Dict[str, Any]:
        """Check OpenAI API connectivity and rate limits."""
        if not settings.openai_api_key:
            return {
                "status": "degraded",
                "error": "OpenAI API key not configured",
                "last_check": datetime.utcnow().isoformat(),
            }

        try:
            # Simple API test (list models is lightweight)
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            start_time = datetime.utcnow()
            models = await client.models.list()
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Check if our embedding model is available
            model_names = [model.id for model in models.data]
            embedding_model_available = settings.embedding_model in model_names

            return {
                "status": "healthy" if embedding_model_available else "degraded",
                "response_time_ms": response_time,
                "embedding_model_available": embedding_model_available,
                "available_models": len(model_names),
                "last_check": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error("OpenAI health check failed", error=str(e))
            return {
                "status": "degraded",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat(),
            }

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Memory metrics
            memory = psutil.virtual_memory()

            # Disk metrics
            disk = psutil.disk_usage("/")

            # Network metrics
            network = psutil.net_io_counters()

            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()

            metrics = {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "load_average": (
                        list(psutil.getloadavg())
                        if hasattr(psutil, "getloadavg")
                        else None
                    ),
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent,
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv,
                },
                "process": {
                    "memory_rss": process_memory.rss,
                    "memory_vms": process_memory.vms,
                    "cpu_percent": process.cpu_percent(),
                    "num_threads": process.num_threads(),
                },
                "uptime": (
                    datetime.utcnow() - datetime.fromtimestamp(psutil.boot_time())
                ).total_seconds(),
            }

            # Log key metrics
            log_performance_metric("cpu_usage_percent", cpu_percent)
            log_performance_metric("memory_usage_percent", memory.percent)
            log_performance_metric("disk_usage_percent", disk.percent)

            return metrics
        except Exception as e:
            logger.error("Failed to get system metrics", error=str(e))
            return {"error": str(e)}

    async def _get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics."""
        try:
            metrics = {}

            # Database metrics
            async for session in get_async_session():
                # Job counts by status
                result = await session.execute(
                    text(
                        """
                    SELECT status, COUNT(*) as count
                    FROM job_descriptions
                    GROUP BY status
                """
                    )
                )
                job_counts = {row[0]: row[1] for row in result.fetchall()}

                # Recent processing activity
                result = await session.execute(
                    text(
                        """
                    SELECT COUNT(*) as count
                    FROM job_descriptions
                    WHERE created_at > NOW() - INTERVAL '1 hour'
                """
                    )
                )
                recent_jobs = result.scalar() or 0

                # Content chunks statistics
                result = await session.execute(
                    text(
                        """
                    SELECT COUNT(*) as total_chunks,
                           COUNT(embedding) as embedded_chunks
                    FROM content_chunks
                """
                    )
                )
                chunk_stats = result.fetchone()

                metrics["database"] = {
                    "job_counts": job_counts,
                    "recent_jobs_1h": recent_jobs,
                    "total_chunks": chunk_stats[0] if chunk_stats else 0,
                    "embedded_chunks": chunk_stats[1] if chunk_stats else 0,
                }

            # Celery task metrics (if Redis is available)
            if self.redis_client:
                try:
                    # Get active tasks
                    active_tasks = self.redis_client.llen("celery")
                    failed_tasks = self.redis_client.llen("celery_failed")

                    metrics["celery"] = {
                        "active_tasks": active_tasks,
                        "failed_tasks": failed_tasks,
                    }
                except Exception as e:
                    logger.warning("Failed to get Celery metrics", error=str(e))

            # Log business metrics
            if "database" in metrics and isinstance(metrics.get("database"), dict):
                db_metrics = metrics["database"]
                if isinstance(db_metrics.get("job_counts"), dict):
                    total_jobs = sum(db_metrics["job_counts"].values())  # type: ignore[union-attr]
                    log_business_metric("total_jobs", total_jobs, "gauge")
                log_business_metric(
                    "recent_jobs_1h", metrics["database"]["recent_jobs_1h"], "gauge"
                )

            return metrics
        except Exception as e:
            logger.error("Failed to get application metrics", error=str(e))
            return {"error": str(e)}


class AlertManager:
    """Manage system alerts and notifications."""

    def __init__(self, monitor: SystemMonitor):
        self.monitor = monitor
        self.alert_thresholds = {
            "cpu_usage": 80,
            "memory_usage": 85,
            "disk_usage": 90,
            "database_response_time": 1000,  # ms
            "redis_response_time": 100,  # ms
        }
        self.alert_history: List[Dict[str, Any]] = []

    async def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for alert conditions and return active alerts."""
        health_data = await self.monitor.get_system_health()
        alerts = []

        # Check system metrics
        system_metrics = health_data.get("metrics", {}).get("system", {})

        # CPU alert
        cpu_percent = system_metrics.get("cpu", {}).get("percent", 0)
        if cpu_percent > self.alert_thresholds["cpu_usage"]:
            alerts.append(
                {
                    "type": "cpu_high",
                    "severity": "warning",
                    "message": f"High CPU usage: {cpu_percent:.1f}%",
                    "value": cpu_percent,
                    "threshold": self.alert_thresholds["cpu_usage"],
                }
            )

        # Memory alert
        memory_percent = system_metrics.get("memory", {}).get("percent", 0)
        if memory_percent > self.alert_thresholds["memory_usage"]:
            alerts.append(
                {
                    "type": "memory_high",
                    "severity": "warning",
                    "message": f"High memory usage: {memory_percent:.1f}%",
                    "value": memory_percent,
                    "threshold": self.alert_thresholds["memory_usage"],
                }
            )

        # Disk alert
        disk_percent = system_metrics.get("disk", {}).get("percent", 0)
        if disk_percent > self.alert_thresholds["disk_usage"]:
            alerts.append(
                {
                    "type": "disk_high",
                    "severity": "critical" if disk_percent > 95 else "warning",
                    "message": f"High disk usage: {disk_percent:.1f}%",
                    "value": disk_percent,
                    "threshold": self.alert_thresholds["disk_usage"],
                }
            )

        # Component health alerts
        for component, status_info in health_data.get("components", {}).items():
            if status_info["status"] == "critical":
                alerts.append(
                    {
                        "type": f"{component}_critical",
                        "severity": "critical",
                        "message": f"{component.title()} is critical: {status_info.get('error', 'Unknown error')}",
                        "component": component,
                    }
                )
            elif status_info["status"] == "degraded":
                alerts.append(
                    {
                        "type": f"{component}_degraded",
                        "severity": "warning",
                        "message": f"{component.title()} is degraded: {status_info.get('error', 'Performance issues')}",
                        "component": component,
                    }
                )

        # Log alerts
        for alert in alerts:
            logger.warning("system_alert", **alert)
            log_business_metric(
                "system_alerts",
                1,
                "counter",
                {"type": alert["type"], "severity": alert["severity"]},
            )

        # Store alert history
        for alert in alerts:
            alert["timestamp"] = datetime.utcnow().isoformat()
            self.alert_history.append(alert)

        # Keep only recent alerts (last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self.alert_history = [
            alert
            for alert in self.alert_history
            if datetime.fromisoformat(alert["timestamp"].replace("Z", "+00:00"))
            > cutoff_time
        ]

        return alerts


# Global instances
system_monitor = SystemMonitor()
alert_manager = AlertManager(system_monitor)


async def get_health_status() -> Dict[str, Any]:
    """Get comprehensive health status for the application."""
    return await system_monitor.get_system_health()


async def check_system_alerts() -> List[Dict[str, Any]]:
    """Check for system alerts."""
    return await alert_manager.check_alerts()
