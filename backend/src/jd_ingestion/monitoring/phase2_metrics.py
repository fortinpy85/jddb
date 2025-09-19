"""
Performance monitoring and metrics collection for Phase 2 features.

This module provides monitoring capabilities for collaborative editing,
WebSocket connections, translation memory, and user activity.
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import psutil
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ..database.connection import get_async_session
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MetricEvent:
    """A single metric event."""
    timestamp: datetime
    metric_name: str
    metric_value: float
    metric_unit: str
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebSocketMetrics:
    """WebSocket connection metrics."""
    active_connections: int = 0
    total_connections: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    connection_errors: int = 0
    average_latency_ms: float = 0.0
    peak_connections: int = 0
    last_activity: Optional[datetime] = None


@dataclass
class CollaborationMetrics:
    """Collaborative editing metrics."""
    active_sessions: int = 0
    total_operations: int = 0
    operations_per_minute: float = 0.0
    conflict_resolution_count: int = 0
    average_session_duration_minutes: float = 0.0
    document_saves: int = 0
    user_activity_events: int = 0


@dataclass
class TranslationMetrics:
    """Translation memory metrics."""
    translation_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_ratio: float = 0.0
    average_translation_time_ms: float = 0.0
    memory_entries: int = 0
    similarity_searches: int = 0


@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    disk_usage_percent: float = 0.0
    network_connections: int = 0
    database_connections: int = 0
    uptime_hours: float = 0.0


class MetricsCollector:
    """Collects and aggregates metrics for Phase 2 features."""

    def __init__(self):
        self.websocket_metrics = WebSocketMetrics()
        self.collaboration_metrics = CollaborationMetrics()
        self.translation_metrics = TranslationMetrics()
        self.system_metrics = SystemMetrics()

        # Time-series data storage (in-memory for development)
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.operation_timings: deque = deque(maxlen=100)
        self.latency_measurements: deque = deque(maxlen=50)

        self.start_time = datetime.utcnow()
        self._collection_active = False

    async def start_collection(self, interval_seconds: int = 60):
        """Start periodic metrics collection."""
        self._collection_active = True
        logger.info("Started Phase 2 metrics collection")

        while self._collection_active:
            try:
                await self.collect_system_metrics()
                await self.collect_database_metrics()
                await self.save_metrics_to_database()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(interval_seconds)

    def stop_collection(self):
        """Stop metrics collection."""
        self._collection_active = False
        logger.info("Stopped Phase 2 metrics collection")

    @asynccontextmanager
    async def measure_operation(self, operation_name: str):
        """Context manager to measure operation timing."""
        start_time = time.time()
        start_dt = datetime.utcnow()

        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000

            # Store timing data
            self.operation_timings.append({
                'operation': operation_name,
                'duration_ms': duration_ms,
                'timestamp': start_dt
            })

            # Add to metric history
            self.record_metric(f"operation_duration_{operation_name}", duration_ms, "milliseconds")

            logger.debug(f"Operation '{operation_name}' took {duration_ms:.2f}ms")

    def record_metric(self, metric_name: str, value: float, unit: str,
                     labels: Optional[Dict[str, str]] = None,
                     metadata: Optional[Dict[str, Any]] = None):
        """Record a metric value."""
        event = MetricEvent(
            timestamp=datetime.utcnow(),
            metric_name=metric_name,
            metric_value=value,
            metric_unit=unit,
            labels=labels or {},
            metadata=metadata or {}
        )

        self.metric_history[metric_name].append(event)

    def record_websocket_connection(self, connected: bool = True):
        """Record WebSocket connection event."""
        if connected:
            self.websocket_metrics.active_connections += 1
            self.websocket_metrics.total_connections += 1
            self.websocket_metrics.peak_connections = max(
                self.websocket_metrics.peak_connections,
                self.websocket_metrics.active_connections
            )
        else:
            self.websocket_metrics.active_connections = max(0,
                self.websocket_metrics.active_connections - 1)

        self.websocket_metrics.last_activity = datetime.utcnow()
        self.record_metric("websocket_active_connections",
                          self.websocket_metrics.active_connections, "count")

    def record_websocket_message(self, sent: bool = True, latency_ms: float = None):
        """Record WebSocket message event."""
        if sent:
            self.websocket_metrics.messages_sent += 1
        else:
            self.websocket_metrics.messages_received += 1

        if latency_ms is not None:
            self.latency_measurements.append(latency_ms)
            if self.latency_measurements:
                self.websocket_metrics.average_latency_ms = sum(self.latency_measurements) / len(self.latency_measurements)

    def record_collaboration_operation(self, operation_type: str, conflict: bool = False):
        """Record collaborative editing operation."""
        self.collaboration_metrics.total_operations += 1

        if conflict:
            self.collaboration_metrics.conflict_resolution_count += 1

        # Calculate operations per minute
        recent_ops = [op for op in self.operation_timings
                     if op['timestamp'] > datetime.utcnow() - timedelta(minutes=1)]
        self.collaboration_metrics.operations_per_minute = len(recent_ops)

        self.record_metric("collaboration_operations",
                          self.collaboration_metrics.total_operations, "count",
                          labels={"operation_type": operation_type, "conflict": str(conflict)})

    def record_translation_request(self, cache_hit: bool = False, duration_ms: float = None):
        """Record translation memory request."""
        self.translation_metrics.translation_requests += 1

        if cache_hit:
            self.translation_metrics.cache_hits += 1
        else:
            self.translation_metrics.cache_misses += 1

        # Calculate cache hit ratio
        total_requests = self.translation_metrics.cache_hits + self.translation_metrics.cache_misses
        if total_requests > 0:
            self.translation_metrics.cache_hit_ratio = self.translation_metrics.cache_hits / total_requests

        if duration_ms is not None:
            self.record_metric("translation_duration", duration_ms, "milliseconds")

    async def collect_system_metrics(self):
        """Collect system resource metrics."""
        try:
            # CPU usage
            self.system_metrics.cpu_usage_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            self.system_metrics.memory_usage_percent = memory.percent
            self.system_metrics.memory_usage_mb = memory.used / (1024 * 1024)

            # Disk usage
            disk = psutil.disk_usage('/')
            self.system_metrics.disk_usage_percent = disk.percent

            # Network connections
            self.system_metrics.network_connections = len(psutil.net_connections())

            # Uptime
            uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
            self.system_metrics.uptime_hours = uptime_seconds / 3600

            # Record metrics
            self.record_metric("system_cpu_usage", self.system_metrics.cpu_usage_percent, "percent")
            self.record_metric("system_memory_usage", self.system_metrics.memory_usage_percent, "percent")
            self.record_metric("system_memory_mb", self.system_metrics.memory_usage_mb, "megabytes")
            self.record_metric("system_network_connections", self.system_metrics.network_connections, "count")

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    async def collect_database_metrics(self):
        """Collect database connection and performance metrics."""
        try:
            async for db in get_async_session():
                # Get database connection count
                result = await db.execute(text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"))
                active_connections = result.scalar()
                self.system_metrics.database_connections = active_connections

                # Get database size
                result = await db.execute(text("SELECT pg_database_size(current_database())"))
                db_size_bytes = result.scalar()
                db_size_mb = db_size_bytes / (1024 * 1024) if db_size_bytes else 0

                # Get table statistics for Phase 2 tables
                phase2_tables = ['users', 'user_sessions', 'editing_sessions', 'document_changes',
                               'translation_memory', 'user_analytics']

                for table in phase2_tables:
                    try:
                        result = await db.execute(text(f"SELECT count(*) FROM {table}"))
                        row_count = result.scalar()
                        self.record_metric(f"table_rows_{table}", row_count, "count")
                    except Exception:
                        # Table might not exist yet
                        pass

                self.record_metric("database_connections", active_connections, "count")
                self.record_metric("database_size_mb", db_size_mb, "megabytes")
                break

        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")

    async def save_metrics_to_database(self):
        """Save collected metrics to the database."""
        try:
            async for db in get_async_session():
                # Save system metrics
                metrics_to_save = [
                    ("system_cpu_usage", self.system_metrics.cpu_usage_percent, "percent"),
                    ("system_memory_usage", self.system_metrics.memory_usage_percent, "percent"),
                    ("websocket_active_connections", self.websocket_metrics.active_connections, "count"),
                    ("collaboration_active_sessions", self.collaboration_metrics.active_sessions, "count"),
                    ("translation_cache_hit_ratio", self.translation_metrics.cache_hit_ratio, "ratio"),
                ]

                for metric_name, value, unit in metrics_to_save:
                    await db.execute(text("""
                        INSERT INTO system_metrics (metric_name, metric_value, metric_unit, metadata)
                        VALUES (:name, :value, :unit, :metadata)
                    """), {
                        "name": metric_name,
                        "value": value,
                        "unit": unit,
                        "metadata": json.dumps({"source": "phase2_monitoring"})
                    })

                await db.commit()
                break

        except Exception as e:
            logger.error(f"Error saving metrics to database: {e}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all current metrics."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "websocket": {
                "active_connections": self.websocket_metrics.active_connections,
                "total_connections": self.websocket_metrics.total_connections,
                "messages_sent": self.websocket_metrics.messages_sent,
                "messages_received": self.websocket_metrics.messages_received,
                "average_latency_ms": self.websocket_metrics.average_latency_ms,
                "peak_connections": self.websocket_metrics.peak_connections
            },
            "collaboration": {
                "total_operations": self.collaboration_metrics.total_operations,
                "operations_per_minute": self.collaboration_metrics.operations_per_minute,
                "conflict_resolution_count": self.collaboration_metrics.conflict_resolution_count,
                "document_saves": self.collaboration_metrics.document_saves
            },
            "translation": {
                "translation_requests": self.translation_metrics.translation_requests,
                "cache_hit_ratio": self.translation_metrics.cache_hit_ratio,
                "memory_entries": self.translation_metrics.memory_entries
            },
            "system": {
                "cpu_usage_percent": self.system_metrics.cpu_usage_percent,
                "memory_usage_percent": self.system_metrics.memory_usage_percent,
                "memory_usage_mb": self.system_metrics.memory_usage_mb,
                "database_connections": self.system_metrics.database_connections,
                "uptime_hours": self.system_metrics.uptime_hours
            }
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a performance report for Phase 2 features."""
        # Calculate average operation times
        recent_operations = [op for op in self.operation_timings
                           if op['timestamp'] > datetime.utcnow() - timedelta(minutes=5)]

        operation_stats = defaultdict(list)
        for op in recent_operations:
            operation_stats[op['operation']].append(op['duration_ms'])

        avg_operation_times = {}
        for op_name, durations in operation_stats.items():
            avg_operation_times[op_name] = {
                "avg_ms": sum(durations) / len(durations),
                "min_ms": min(durations),
                "max_ms": max(durations),
                "count": len(durations)
            }

        return {
            "report_time": datetime.utcnow().isoformat(),
            "summary": self.get_metrics_summary(),
            "performance": {
                "operation_timings": avg_operation_times,
                "recent_latency": list(self.latency_measurements)[-10:] if self.latency_measurements else [],
                "memory_efficiency": {
                    "metric_history_size": sum(len(h) for h in self.metric_history.values()),
                    "operation_timings_size": len(self.operation_timings),
                    "latency_measurements_size": len(self.latency_measurements)
                }
            },
            "recommendations": self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations based on current metrics."""
        recommendations = []

        # High CPU usage
        if self.system_metrics.cpu_usage_percent > 80:
            recommendations.append("High CPU usage detected. Consider optimizing WebSocket message processing.")

        # High memory usage
        if self.system_metrics.memory_usage_percent > 85:
            recommendations.append("High memory usage detected. Review in-memory caching strategies.")

        # High latency
        if self.websocket_metrics.average_latency_ms > 100:
            recommendations.append("High WebSocket latency detected. Check network conditions and server load.")

        # Many conflicts
        conflict_ratio = (self.collaboration_metrics.conflict_resolution_count /
                         max(1, self.collaboration_metrics.total_operations))
        if conflict_ratio > 0.1:
            recommendations.append("High conflict resolution rate. Consider improving operational transformation.")

        # Low cache hit ratio
        if self.translation_metrics.cache_hit_ratio < 0.7 and self.translation_metrics.translation_requests > 10:
            recommendations.append("Low translation cache hit ratio. Review cache eviction policies.")

        return recommendations


# Global metrics collector instance
metrics_collector = MetricsCollector()


# Convenience functions
async def start_monitoring(interval_seconds: int = 60):
    """Start Phase 2 metrics monitoring."""
    await metrics_collector.start_collection(interval_seconds)


def stop_monitoring():
    """Stop Phase 2 metrics monitoring."""
    metrics_collector.stop_collection()


def record_websocket_event(event_type: str, **kwargs):
    """Record a WebSocket event."""
    if event_type == "connection":
        metrics_collector.record_websocket_connection(kwargs.get('connected', True))
    elif event_type == "message":
        metrics_collector.record_websocket_message(
            kwargs.get('sent', True),
            kwargs.get('latency_ms')
        )


def record_collaboration_event(operation_type: str, conflict: bool = False):
    """Record a collaboration event."""
    metrics_collector.record_collaboration_operation(operation_type, conflict)


def record_translation_event(cache_hit: bool = False, duration_ms: float = None):
    """Record a translation event."""
    metrics_collector.record_translation_request(cache_hit, duration_ms)


async def get_metrics_summary():
    """Get current metrics summary."""
    return metrics_collector.get_metrics_summary()


async def get_performance_report():
    """Get detailed performance report."""
    return metrics_collector.get_performance_report()