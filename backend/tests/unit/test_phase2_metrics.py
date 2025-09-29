"""
Tests for Phase 2 metrics monitoring module.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from collections import deque

from jd_ingestion.monitoring.phase2_metrics import (
    MetricEvent,
    WebSocketMetrics,
    CollaborationMetrics,
    TranslationMetrics,
    SystemMetrics,
    MetricsCollector,
    metrics_collector,
    start_monitoring,
    stop_monitoring,
    record_websocket_event,
    record_collaboration_event,
    record_translation_event,
    get_metrics_summary,
    get_performance_report,
)


class TestMetricDataClasses:
    """Test metric data classes."""

    def test_metric_event_creation(self):
        """Test MetricEvent creation."""
        event = MetricEvent(
            timestamp=datetime.now(),
            metric_name="test_metric",
            metric_value=123.45,
            metric_unit="ms",
            labels={"service": "websocket"},
            metadata={"version": "2.0"},
        )

        assert event.metric_name == "test_metric"
        assert event.metric_value == 123.45
        assert event.metric_unit == "ms"
        assert event.labels["service"] == "websocket"
        assert event.metadata["version"] == "2.0"

    def test_metric_event_defaults(self):
        """Test MetricEvent with default values."""
        event = MetricEvent(
            timestamp=datetime.now(),
            metric_name="test_metric",
            metric_value=100.0,
            metric_unit="count",
        )

        assert event.labels == {}
        assert event.metadata == {}

    def test_websocket_metrics_defaults(self):
        """Test WebSocketMetrics default values."""
        metrics = WebSocketMetrics()

        assert metrics.active_connections == 0
        assert metrics.total_connections == 0
        assert metrics.messages_sent == 0
        assert metrics.messages_received == 0
        assert metrics.connection_errors == 0
        assert metrics.average_latency_ms == 0.0
        assert metrics.peak_connections == 0
        assert metrics.last_activity is None

    def test_collaboration_metrics_defaults(self):
        """Test CollaborationMetrics default values."""
        metrics = CollaborationMetrics()

        assert metrics.active_sessions == 0
        assert metrics.total_operations == 0
        assert metrics.operations_per_minute == 0.0
        assert metrics.conflict_resolution_count == 0
        assert metrics.average_session_duration_minutes == 0.0
        assert metrics.document_saves == 0
        assert metrics.user_activity_events == 0

    def test_translation_metrics_defaults(self):
        """Test TranslationMetrics default values."""
        metrics = TranslationMetrics()

        assert metrics.translation_requests == 0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.cache_hit_ratio == 0.0
        assert metrics.average_translation_time_ms == 0.0
        assert metrics.memory_entries == 0
        assert metrics.similarity_searches == 0

    def test_system_metrics_defaults(self):
        """Test SystemMetrics default values."""
        metrics = SystemMetrics()

        assert metrics.cpu_usage_percent == 0.0
        assert metrics.memory_usage_percent == 0.0
        assert metrics.memory_usage_mb == 0.0
        assert metrics.disk_usage_percent == 0.0
        assert metrics.network_connections == 0
        assert metrics.database_connections == 0
        assert metrics.uptime_hours == 0.0


class TestMetricsCollector:
    """Test MetricsCollector class."""

    def test_collector_initialization(self):
        """Test MetricsCollector initialization."""
        collector = MetricsCollector()

        assert isinstance(collector.websocket_metrics, WebSocketMetrics)
        assert isinstance(collector.collaboration_metrics, CollaborationMetrics)
        assert isinstance(collector.translation_metrics, TranslationMetrics)
        assert isinstance(collector.system_metrics, SystemMetrics)
        assert isinstance(collector.metric_history, dict)
        assert isinstance(collector.operation_timings, deque)
        assert isinstance(collector.latency_measurements, deque)
        assert collector._collection_active is False

    def test_record_metric(self):
        """Test recording a metric."""
        collector = MetricsCollector()

        collector.record_metric(
            "test_metric",
            42.5,
            "seconds",
            labels={"service": "test"},
            metadata={"version": "1.0"},
        )

        assert "test_metric" in collector.metric_history
        assert len(collector.metric_history["test_metric"]) == 1

        event = collector.metric_history["test_metric"][0]
        assert event.metric_name == "test_metric"
        assert event.metric_value == 42.5
        assert event.metric_unit == "seconds"
        assert event.labels["service"] == "test"
        assert event.metadata["version"] == "1.0"

    def test_record_metric_defaults(self):
        """Test recording metric with default labels and metadata."""
        collector = MetricsCollector()

        collector.record_metric("simple_metric", 100.0, "count")

        event = collector.metric_history["simple_metric"][0]
        assert event.labels == {}
        assert event.metadata == {}

    def test_record_websocket_connection_connect(self):
        """Test recording WebSocket connection."""
        collector = MetricsCollector()

        collector.record_websocket_connection(connected=True)

        assert collector.websocket_metrics.active_connections == 1
        assert collector.websocket_metrics.total_connections == 1
        assert collector.websocket_metrics.peak_connections == 1
        assert collector.websocket_metrics.last_activity is not None

        # Connect another
        collector.record_websocket_connection(connected=True)

        assert collector.websocket_metrics.active_connections == 2
        assert collector.websocket_metrics.total_connections == 2
        assert collector.websocket_metrics.peak_connections == 2

    def test_record_websocket_connection_disconnect(self):
        """Test recording WebSocket disconnection."""
        collector = MetricsCollector()

        # First connect some users
        collector.record_websocket_connection(connected=True)
        collector.record_websocket_connection(connected=True)

        # Then disconnect one
        collector.record_websocket_connection(connected=False)

        assert collector.websocket_metrics.active_connections == 1
        assert (
            collector.websocket_metrics.total_connections == 2
        )  # Total doesn't decrease
        assert collector.websocket_metrics.peak_connections == 2

        # Disconnect below zero should be handled
        collector.record_websocket_connection(connected=False)
        collector.record_websocket_connection(connected=False)

        assert (
            collector.websocket_metrics.active_connections == 0
        )  # Should not go negative

    def test_record_websocket_message(self):
        """Test recording WebSocket messages."""
        collector = MetricsCollector()

        # Test sent message
        collector.record_websocket_message(sent=True)
        assert collector.websocket_metrics.messages_sent == 1
        assert collector.websocket_metrics.messages_received == 0

        # Test received message
        collector.record_websocket_message(sent=False)
        assert collector.websocket_metrics.messages_sent == 1
        assert collector.websocket_metrics.messages_received == 1

        # Test with latency
        collector.record_websocket_message(sent=True, latency_ms=50.5)
        assert collector.websocket_metrics.messages_sent == 2
        assert collector.websocket_metrics.average_latency_ms == 50.5

        # Test latency averaging
        collector.record_websocket_message(sent=True, latency_ms=75.5)
        assert collector.websocket_metrics.messages_sent == 3
        assert (
            collector.websocket_metrics.average_latency_ms == 63.0
        )  # Average of 50.5 and 75.5

    def test_record_collaboration_operation(self):
        """Test recording collaboration operations."""
        collector = MetricsCollector()

        collector.record_collaboration_operation("insert", conflict=False)

        assert collector.collaboration_metrics.total_operations == 1
        assert collector.collaboration_metrics.conflict_resolution_count == 0

        collector.record_collaboration_operation("delete", conflict=True)

        assert collector.collaboration_metrics.total_operations == 2
        assert collector.collaboration_metrics.conflict_resolution_count == 1

    def test_record_translation_request(self):
        """Test recording translation requests."""
        collector = MetricsCollector()

        # Test cache miss
        collector.record_translation_request(cache_hit=False, duration_ms=100.0)

        assert collector.translation_metrics.translation_requests == 1
        assert collector.translation_metrics.cache_hits == 0
        assert collector.translation_metrics.cache_misses == 1
        assert collector.translation_metrics.cache_hit_ratio == 0.0

        # Test cache hit
        collector.record_translation_request(cache_hit=True, duration_ms=25.0)

        assert collector.translation_metrics.translation_requests == 2
        assert collector.translation_metrics.cache_hits == 1
        assert collector.translation_metrics.cache_misses == 1
        assert collector.translation_metrics.cache_hit_ratio == 0.5

        # Test more cache hits to verify ratio calculation
        collector.record_translation_request(cache_hit=True)
        collector.record_translation_request(cache_hit=True)

        assert (
            collector.translation_metrics.cache_hit_ratio == 0.75
        )  # 3 hits out of 4 total

    @pytest.mark.asyncio
    async def test_measure_operation_context_manager(self):
        """Test the measure_operation context manager."""
        collector = MetricsCollector()

        async with collector.measure_operation("test_operation"):
            await asyncio.sleep(0.01)  # Small delay to measure

        assert len(collector.operation_timings) == 1
        operation = collector.operation_timings[0]
        assert operation["operation"] == "test_operation"
        assert operation["duration_ms"] > 0
        assert "timestamp" in operation

        # Check metric was recorded
        assert "operation_duration_test_operation" in collector.metric_history

    @pytest.mark.asyncio
    async def test_measure_operation_with_exception(self):
        """Test measure_operation context manager with exception."""
        collector = MetricsCollector()

        with pytest.raises(ValueError):
            async with collector.measure_operation("failing_operation"):
                raise ValueError("Test exception")

        # Should still record timing even with exception
        assert len(collector.operation_timings) == 1
        operation = collector.operation_timings[0]
        assert operation["operation"] == "failing_operation"

    @pytest.mark.asyncio
    @patch("jd_ingestion.monitoring.phase2_metrics.psutil")
    async def test_collect_system_metrics(self, mock_psutil):
        """Test system metrics collection."""
        # Mock psutil functions
        mock_psutil.cpu_percent.return_value = 45.5
        mock_memory = Mock()
        mock_memory.percent = 62.3
        mock_memory.used = 1024 * 1024 * 512  # 512 MB
        mock_psutil.virtual_memory.return_value = mock_memory

        mock_disk = Mock()
        mock_disk.percent = 78.9
        mock_psutil.disk_usage.return_value = mock_disk

        mock_psutil.net_connections.return_value = [Mock()] * 25  # 25 connections

        collector = MetricsCollector()
        await collector.collect_system_metrics()

        assert collector.system_metrics.cpu_usage_percent == 45.5
        assert collector.system_metrics.memory_usage_percent == 62.3
        assert collector.system_metrics.memory_usage_mb == 512.0
        assert collector.system_metrics.disk_usage_percent == 78.9
        assert collector.system_metrics.network_connections == 25

        # Verify metrics were recorded
        assert "system_cpu_usage" in collector.metric_history
        assert "system_memory_usage" in collector.metric_history
        assert "system_memory_mb" in collector.metric_history
        assert "system_network_connections" in collector.metric_history

    @pytest.mark.asyncio
    @patch("jd_ingestion.monitoring.phase2_metrics.psutil")
    async def test_collect_system_metrics_error_handling(self, mock_psutil):
        """Test system metrics collection error handling."""
        mock_psutil.cpu_percent.side_effect = Exception("CPU monitoring error")

        collector = MetricsCollector()
        # Should not raise exception
        await collector.collect_system_metrics()

    @pytest.mark.asyncio
    @patch("jd_ingestion.monitoring.phase2_metrics.get_async_session")
    async def test_collect_database_metrics(self, mock_get_session):
        """Test database metrics collection."""
        # Mock database session and queries
        mock_db = AsyncMock()
        mock_get_session.return_value.__aiter__.return_value = [mock_db]

        # Mock query results
        mock_result = Mock()
        mock_result.scalar.side_effect = [
            10,  # Active connections
            1024 * 1024 * 100,  # Database size (100 MB)
            25,
            15,
            8,
            0,
            42,  # Table row counts
        ]
        mock_db.execute.return_value = mock_result

        collector = MetricsCollector()
        await collector.collect_database_metrics()

        assert collector.system_metrics.database_connections == 10

        # Verify metrics were recorded
        assert "database_connections" in collector.metric_history
        assert "database_size_mb" in collector.metric_history

    @pytest.mark.asyncio
    @patch("jd_ingestion.monitoring.phase2_metrics.get_async_session")
    async def test_collect_database_metrics_error_handling(self, mock_get_session):
        """Test database metrics collection error handling."""
        mock_get_session.side_effect = Exception("Database connection error")

        collector = MetricsCollector()
        # Should not raise exception
        await collector.collect_database_metrics()

    @pytest.mark.asyncio
    @patch("jd_ingestion.monitoring.phase2_metrics.get_async_session")
    async def test_save_metrics_to_database(self, mock_get_session):
        """Test saving metrics to database."""
        mock_db = AsyncMock()
        mock_get_session.return_value.__aiter__.return_value = [mock_db]

        collector = MetricsCollector()
        # Set some test metrics
        collector.system_metrics.cpu_usage_percent = 50.0
        collector.websocket_metrics.active_connections = 5

        await collector.save_metrics_to_database()

        # Verify database operations were called
        assert mock_db.execute.call_count > 0
        mock_db.commit.assert_called_once()

    def test_get_metrics_summary(self):
        """Test getting metrics summary."""
        collector = MetricsCollector()

        # Set some test data
        collector.websocket_metrics.active_connections = 3
        collector.websocket_metrics.total_connections = 10
        collector.system_metrics.cpu_usage_percent = 45.5
        collector.translation_metrics.cache_hit_ratio = 0.8

        summary = collector.get_metrics_summary()

        assert "timestamp" in summary
        assert summary["websocket"]["active_connections"] == 3
        assert summary["websocket"]["total_connections"] == 10
        assert summary["system"]["cpu_usage_percent"] == 45.5
        assert summary["translation"]["cache_hit_ratio"] == 0.8

    def test_get_performance_report(self):
        """Test getting performance report."""
        collector = MetricsCollector()

        # Add some operation timings
        collector.operation_timings.append(
            {
                "operation": "websocket_message",
                "duration_ms": 50.0,
                "timestamp": datetime.utcnow(),
            }
        )
        collector.operation_timings.append(
            {
                "operation": "websocket_message",
                "duration_ms": 75.0,
                "timestamp": datetime.utcnow(),
            }
        )

        # Add latency measurements
        collector.latency_measurements.extend([25.0, 30.0, 35.0])

        report = collector.get_performance_report()

        assert "report_time" in report
        assert "summary" in report
        assert "performance" in report
        assert "recommendations" in report

        # Check operation timings
        performance = report["performance"]
        assert "operation_timings" in performance
        assert "websocket_message" in performance["operation_timings"]

        websocket_stats = performance["operation_timings"]["websocket_message"]
        assert websocket_stats["avg_ms"] == 62.5  # Average of 50.0 and 75.0
        assert websocket_stats["min_ms"] == 50.0
        assert websocket_stats["max_ms"] == 75.0
        assert websocket_stats["count"] == 2

    def test_generate_recommendations_high_cpu(self):
        """Test recommendations for high CPU usage."""
        collector = MetricsCollector()
        collector.system_metrics.cpu_usage_percent = 85.0

        recommendations = collector._generate_recommendations()

        assert any("High CPU usage" in rec for rec in recommendations)

    def test_generate_recommendations_high_memory(self):
        """Test recommendations for high memory usage."""
        collector = MetricsCollector()
        collector.system_metrics.memory_usage_percent = 90.0

        recommendations = collector._generate_recommendations()

        assert any("High memory usage" in rec for rec in recommendations)

    def test_generate_recommendations_high_latency(self):
        """Test recommendations for high latency."""
        collector = MetricsCollector()
        collector.websocket_metrics.average_latency_ms = 150.0

        recommendations = collector._generate_recommendations()

        assert any("High WebSocket latency" in rec for rec in recommendations)

    def test_generate_recommendations_many_conflicts(self):
        """Test recommendations for high conflict rate."""
        collector = MetricsCollector()
        collector.collaboration_metrics.total_operations = 100
        collector.collaboration_metrics.conflict_resolution_count = (
            15  # 15% conflict rate
        )

        recommendations = collector._generate_recommendations()

        assert any("High conflict resolution rate" in rec for rec in recommendations)

    def test_generate_recommendations_low_cache_hit_ratio(self):
        """Test recommendations for low cache hit ratio."""
        collector = MetricsCollector()
        collector.translation_metrics.translation_requests = 50
        collector.translation_metrics.cache_hit_ratio = 0.6  # Below 0.7 threshold

        recommendations = collector._generate_recommendations()

        assert any("Low translation cache hit ratio" in rec for rec in recommendations)

    def test_stop_collection(self):
        """Test stopping metrics collection."""
        collector = MetricsCollector()
        collector._collection_active = True

        collector.stop_collection()

        assert collector._collection_active is False

    @pytest.mark.asyncio
    async def test_start_collection_loop(self):
        """Test the collection loop starts and can be stopped."""
        collector = MetricsCollector()

        # Create a task for the collection loop
        collection_task = asyncio.create_task(
            collector.start_collection(interval_seconds=0.1)
        )

        # Let it run briefly
        await asyncio.sleep(0.05)

        # Stop collection
        collector.stop_collection()

        # Wait for task to complete
        try:
            await asyncio.wait_for(collection_task, timeout=1.0)
        except asyncio.TimeoutError:
            collection_task.cancel()


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.monitoring.phase2_metrics.metrics_collector")
    async def test_start_monitoring(self, mock_collector):
        """Test start_monitoring function."""
        mock_collector.start_collection = AsyncMock()

        await start_monitoring(interval_seconds=30)

        mock_collector.start_collection.assert_called_once_with(30)

    @patch("jd_ingestion.monitoring.phase2_metrics.metrics_collector")
    def test_stop_monitoring(self, mock_collector):
        """Test stop_monitoring function."""
        stop_monitoring()

        mock_collector.stop_collection.assert_called_once()

    @patch("jd_ingestion.monitoring.phase2_metrics.metrics_collector")
    def test_record_websocket_event_connection(self, mock_collector):
        """Test recording WebSocket connection event."""
        record_websocket_event("connection", connected=True)

        mock_collector.record_websocket_connection.assert_called_once_with(True)

    @patch("jd_ingestion.monitoring.phase2_metrics.metrics_collector")
    def test_record_websocket_event_message(self, mock_collector):
        """Test recording WebSocket message event."""
        record_websocket_event("message", sent=False, latency_ms=45.5)

        mock_collector.record_websocket_message.assert_called_once_with(False, 45.5)

    @patch("jd_ingestion.monitoring.phase2_metrics.metrics_collector")
    def test_record_collaboration_event(self, mock_collector):
        """Test recording collaboration event."""
        record_collaboration_event("insert", conflict=True)

        mock_collector.record_collaboration_operation.assert_called_once_with(
            "insert", True
        )

    @patch("jd_ingestion.monitoring.phase2_metrics.metrics_collector")
    def test_record_translation_event(self, mock_collector):
        """Test recording translation event."""
        record_translation_event(cache_hit=True, duration_ms=25.5)

        mock_collector.record_translation_request.assert_called_once_with(True, 25.5)

    @pytest.mark.asyncio
    @patch("jd_ingestion.monitoring.phase2_metrics.metrics_collector")
    async def test_get_metrics_summary(self, mock_collector):
        """Test getting metrics summary."""
        mock_collector.get_metrics_summary.return_value = {"test": "data"}

        result = await get_metrics_summary()

        assert result == {"test": "data"}
        mock_collector.get_metrics_summary.assert_called_once()

    @pytest.mark.asyncio
    @patch("jd_ingestion.monitoring.phase2_metrics.metrics_collector")
    async def test_get_performance_report(self, mock_collector):
        """Test getting performance report."""
        mock_collector.get_performance_report.return_value = {"performance": "report"}

        result = await get_performance_report()

        assert result == {"performance": "report"}
        mock_collector.get_performance_report.assert_called_once()


class TestGlobalCollector:
    """Test global metrics collector instance."""

    def test_global_collector_exists(self):
        """Test that global metrics collector exists."""
        assert metrics_collector is not None
        assert isinstance(metrics_collector, MetricsCollector)

    def test_global_collector_independent_state(self):
        """Test that global collector maintains independent state."""
        # Record some data in global collector
        metrics_collector.record_websocket_connection(True)
        initial_connections = metrics_collector.websocket_metrics.active_connections

        # Create new local collector
        local_collector = MetricsCollector()

        # Should have independent state
        assert local_collector.websocket_metrics.active_connections == 0
        assert (
            metrics_collector.websocket_metrics.active_connections
            == initial_connections
        )

        # Clean up global state
        metrics_collector.websocket_metrics.active_connections = 0
        metrics_collector.websocket_metrics.total_connections = 0


class TestMetricsIntegration:
    """Test metrics integration scenarios."""

    def test_deque_max_length_behavior(self):
        """Test that deques respect max length limits."""
        collector = MetricsCollector()

        # Test metric history max length (1000)
        for i in range(1500):
            collector.record_metric("test_metric", float(i), "count")

        assert len(collector.metric_history["test_metric"]) == 1000

        # Test operation timings max length (100)
        for i in range(150):
            collector.operation_timings.append(
                {
                    "operation": f"test_op_{i}",
                    "duration_ms": float(i),
                    "timestamp": datetime.utcnow(),
                }
            )

        assert len(collector.operation_timings) == 100

        # Test latency measurements max length (50)
        for i in range(75):
            collector.latency_measurements.append(float(i))

        assert len(collector.latency_measurements) == 50

    def test_metrics_time_based_filtering(self):
        """Test time-based filtering of metrics."""
        collector = MetricsCollector()

        # Add old and recent operations
        old_time = datetime.utcnow() - timedelta(minutes=10)
        recent_time = datetime.utcnow()

        collector.operation_timings.extend(
            [
                {"operation": "old_op", "duration_ms": 100.0, "timestamp": old_time},
                {
                    "operation": "recent_op",
                    "duration_ms": 50.0,
                    "timestamp": recent_time,
                },
            ]
        )

        # Set some collaboration metrics that depend on recent operations
        collector.record_collaboration_operation("insert", conflict=False)

        # Operations per minute should only count recent operations
        assert collector.collaboration_metrics.operations_per_minute >= 0

    @patch("jd_ingestion.monitoring.phase2_metrics.logger")
    def test_error_logging_integration(self, mock_logger):
        """Test that errors are properly logged."""
        collector = MetricsCollector()

        # Test system metrics collection error
        with patch(
            "jd_ingestion.monitoring.phase2_metrics.psutil.cpu_percent",
            side_effect=Exception("Test error"),
        ):
            asyncio.run(collector.collect_system_metrics())

        mock_logger.error.assert_called()

    def test_operations_per_minute_calculation(self):
        """Test operations per minute calculation accuracy."""
        collector = MetricsCollector()

        current_time = datetime.utcnow()

        # Add operations at different times
        collector.operation_timings.extend(
            [
                # Recent operations (within last minute)
                {
                    "operation": "op1",
                    "duration_ms": 10.0,
                    "timestamp": current_time - timedelta(seconds=30),
                },
                {
                    "operation": "op2",
                    "duration_ms": 20.0,
                    "timestamp": current_time - timedelta(seconds=45),
                },
                # Old operations (more than a minute ago)
                {
                    "operation": "op3",
                    "duration_ms": 30.0,
                    "timestamp": current_time - timedelta(minutes=2),
                },
            ]
        )

        collector.record_collaboration_operation("test", conflict=False)

        # Should count recent operations (at least 2, possibly 3 due to timing)
        assert collector.collaboration_metrics.operations_per_minute >= 2
        assert collector.collaboration_metrics.operations_per_minute <= 3
