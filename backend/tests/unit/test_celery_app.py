"""Tests for tasks/celery_app.py module."""

import pytest
from unittest.mock import patch, MagicMock

from jd_ingestion.tasks.celery_app import celery_app


class TestCeleryAppConfiguration:
    """Test Celery app configuration."""

    def test_celery_app_creation(self):
        """Test that Celery app is created with correct name."""
        assert celery_app.main == "jd_ingestion"

    def test_celery_app_includes(self):
        """Test that Celery app includes the correct task modules."""
        expected_includes = [
            "jd_ingestion.tasks.processing_tasks",
            "jd_ingestion.tasks.embedding_tasks",
            "jd_ingestion.tasks.quality_tasks",
        ]

        assert celery_app.conf.include == expected_includes

    @patch("jd_ingestion.tasks.celery_app.settings")
    def test_celery_broker_configuration(self, mock_settings):
        """Test that Celery is configured with correct broker settings."""
        # Mock settings values
        mock_settings.celery_broker_url_final = "redis://localhost:6379/0"
        mock_settings.celery_result_backend_final = "redis://localhost:6379/1"

        # Import after mocking to get mocked values
        from jd_ingestion.tasks.celery_app import celery_app as test_app

        assert test_app.conf.broker_url == mock_settings.celery_broker_url_final

    def test_basic_configuration_properties(self):
        """Test basic Celery configuration properties."""
        assert celery_app.conf.timezone == "UTC"
        assert celery_app.conf.enable_utc is True
        assert celery_app.conf.worker_hijack_root_logger is False
        assert celery_app.conf.worker_send_task_events is True
        assert celery_app.conf.task_send_sent_event is True

    def test_retry_configuration(self):
        """Test retry-related configuration."""
        assert celery_app.conf.task_retry_backoff is True
        assert celery_app.conf.task_retry_backoff_max == 300
        assert celery_app.conf.task_retry_jitter is True
        assert celery_app.conf.task_acks_on_failure_or_timeout is True

    def test_task_routing_configuration(self):
        """Test task routing configuration."""
        expected_routes = {
            "jd_ingestion.tasks.processing_tasks.*": {"queue": "processing"},
            "jd_ingestion.tasks.embedding_tasks.*": {"queue": "embeddings"},
            "jd_ingestion.tasks.quality_tasks.*": {"queue": "quality"},
        }

        # Check basic routing
        for pattern, config in expected_routes.items():
            assert pattern in celery_app.conf.task_routes
            assert celery_app.conf.task_routes[pattern]["queue"] == config["queue"]

    def test_specific_task_routing(self):
        """Test specific task routing configurations."""
        task_configs = {
            "jd_ingestion.tasks.processing_tasks.process_single_file_task": {
                "queue": "processing",
                "retry_backoff": 5,
                "max_retries": 5,
                "soft_time_limit": 180,
                "time_limit": 300,
            },
            "jd_ingestion.tasks.processing_tasks.batch_process_files_task": {
                "queue": "processing",
                "retry_backoff": 10,
                "max_retries": 3,
                "soft_time_limit": 900,
                "time_limit": 1200,
            },
        }

        for task_name, expected_config in task_configs.items():
            assert task_name in celery_app.conf.task_routes
            actual_config = celery_app.conf.task_routes[task_name]

            for key, value in expected_config.items():
                assert actual_config[key] == value

    def test_embedding_task_routing(self):
        """Test embedding task-specific routing."""
        embedding_tasks = {
            "jd_ingestion.tasks.embedding_tasks.generate_embeddings_for_job_task": {
                "queue": "embeddings",
                "retry_backoff": 15,
                "max_retries": 4,
                "soft_time_limit": 300,
                "time_limit": 600,
            },
            "jd_ingestion.tasks.embedding_tasks.batch_generate_embeddings_task": {
                "queue": "embeddings",
                "retry_backoff": 30,
                "max_retries": 3,
                "soft_time_limit": 1800,
                "time_limit": 2400,
            },
            "jd_ingestion.tasks.embedding_tasks.generate_missing_embeddings_task": {
                "queue": "embeddings",
                "retry_backoff": 60,
                "max_retries": 2,
                "soft_time_limit": 3600,
                "time_limit": 4800,
            },
        }

        for task_name, expected_config in embedding_tasks.items():
            assert task_name in celery_app.conf.task_routes
            actual_config = celery_app.conf.task_routes[task_name]

            for key, value in expected_config.items():
                assert actual_config[key] == value

    def test_quality_task_routing(self):
        """Test quality task-specific routing."""
        quality_tasks = {
            "jd_ingestion.tasks.quality_tasks.calculate_quality_metrics_task": {
                "queue": "quality",
                "retry_backoff": 10,
                "max_retries": 3,
                "soft_time_limit": 120,
                "time_limit": 180,
            },
            "jd_ingestion.tasks.quality_tasks.batch_calculate_quality_metrics_task": {
                "queue": "quality",
                "retry_backoff": 30,
                "max_retries": 2,
                "soft_time_limit": 900,
                "time_limit": 1200,
            },
            "jd_ingestion.tasks.quality_tasks.generate_quality_report_task": {
                "queue": "quality",
                "retry_backoff": 15,
                "max_retries": 2,
                "soft_time_limit": 300,
                "time_limit": 420,
            },
            "jd_ingestion.tasks.quality_tasks.validate_job_content_task": {
                "queue": "quality",
                "retry_backoff": 5,
                "max_retries": 3,
                "soft_time_limit": 90,
                "time_limit": 150,
            },
        }

        for task_name, expected_config in quality_tasks.items():
            assert task_name in celery_app.conf.task_routes
            actual_config = celery_app.conf.task_routes[task_name]

            for key, value in expected_config.items():
                assert actual_config[key] == value

    def test_dead_letter_queue_routing(self):
        """Test dead letter queue routing configuration."""
        dlq_pattern = "jd_ingestion.tasks.*.dlq_*"
        assert dlq_pattern in celery_app.conf.task_routes
        assert celery_app.conf.task_routes[dlq_pattern]["queue"] == "failed_tasks"

    @patch("jd_ingestion.tasks.celery_app.settings")
    def test_serializer_configuration(self, mock_settings):
        """Test serializer configuration."""
        mock_settings.celery_task_serializer = "json"
        mock_settings.celery_result_serializer = "json"
        mock_settings.celery_accept_content_list = ["json"]

        # Re-import to get mocked settings
        import importlib
        import jd_ingestion.tasks.celery_app

        importlib.reload(jd_ingestion.tasks.celery_app)

        from jd_ingestion.tasks.celery_app import celery_app as reloaded_app

        assert reloaded_app.conf.task_serializer == "json"
        assert reloaded_app.conf.result_serializer == "json"
        assert reloaded_app.conf.accept_content == ["json"]

    @patch("jd_ingestion.tasks.celery_app.settings")
    def test_compression_configuration(self, mock_settings):
        """Test compression configuration."""
        mock_settings.celery_task_compression = "gzip"
        mock_settings.celery_result_compression = "gzip"

        # Re-import to get mocked settings
        import importlib
        import jd_ingestion.tasks.celery_app

        importlib.reload(jd_ingestion.tasks.celery_app)

        from jd_ingestion.tasks.celery_app import celery_app as reloaded_app

        assert reloaded_app.conf.task_compression == "gzip"
        assert reloaded_app.conf.result_compression == "gzip"

    @patch("jd_ingestion.tasks.celery_app.settings")
    def test_worker_configuration(self, mock_settings):
        """Test worker configuration settings."""
        mock_settings.celery_worker_concurrency = 4
        mock_settings.celery_worker_prefetch_multiplier = 1
        mock_settings.celery_worker_max_tasks_per_child = 1000
        mock_settings.celery_worker_max_memory_per_child = 200000  # 200MB
        mock_settings.celery_worker_disable_rate_limits = False

        # Re-import to get mocked settings
        import importlib
        import jd_ingestion.tasks.celery_app

        importlib.reload(jd_ingestion.tasks.celery_app)

        from jd_ingestion.tasks.celery_app import celery_app as reloaded_app

        assert reloaded_app.conf.worker_concurrency == 4
        assert reloaded_app.conf.worker_prefetch_multiplier == 1
        assert reloaded_app.conf.worker_max_tasks_per_child == 1000
        assert reloaded_app.conf.worker_max_memory_per_child == 200000
        assert reloaded_app.conf.worker_disable_rate_limits is False

    @patch("jd_ingestion.tasks.celery_app.settings")
    def test_task_execution_configuration(self, mock_settings):
        """Test task execution configuration."""
        mock_settings.celery_task_always_eager = False
        mock_settings.celery_task_eager_propagates = False
        mock_settings.celery_task_acks_late = True

        # Re-import to get mocked settings
        import importlib
        import jd_ingestion.tasks.celery_app

        importlib.reload(jd_ingestion.tasks.celery_app)

        from jd_ingestion.tasks.celery_app import celery_app as reloaded_app

        assert reloaded_app.conf.task_always_eager is False
        assert reloaded_app.conf.task_eager_propagates is False
        assert reloaded_app.conf.task_acks_late is True

    @patch("jd_ingestion.tasks.celery_app.settings")
    def test_timeout_and_retry_configuration(self, mock_settings):
        """Test timeout and retry configuration."""
        mock_settings.celery_task_soft_time_limit = 600
        mock_settings.celery_task_time_limit = 900
        mock_settings.celery_task_default_retry_delay = 60
        mock_settings.celery_task_max_retries = 3

        # Re-import to get mocked settings
        import importlib
        import jd_ingestion.tasks.celery_app

        importlib.reload(jd_ingestion.tasks.celery_app)

        from jd_ingestion.tasks.celery_app import celery_app as reloaded_app

        assert reloaded_app.conf.task_soft_time_limit == 600
        assert reloaded_app.conf.task_time_limit == 900
        assert reloaded_app.conf.task_default_retry_delay == 60
        assert reloaded_app.conf.task_max_retries == 3

    @patch("jd_ingestion.tasks.celery_app.settings")
    def test_broker_connection_configuration(self, mock_settings):
        """Test broker connection configuration."""
        mock_settings.celery_broker_connection_retry_on_startup = True
        mock_settings.celery_broker_connection_retry = True
        mock_settings.celery_broker_connection_max_retries = 10
        mock_settings.celery_task_reject_on_worker_lost = True

        # Re-import to get mocked settings
        import importlib
        import jd_ingestion.tasks.celery_app

        importlib.reload(jd_ingestion.tasks.celery_app)

        from jd_ingestion.tasks.celery_app import celery_app as reloaded_app

        assert reloaded_app.conf.broker_connection_retry_on_startup is True
        assert reloaded_app.conf.broker_connection_retry is True
        assert reloaded_app.conf.broker_connection_max_retries == 10
        assert reloaded_app.conf.task_reject_on_worker_lost is True

    @patch("jd_ingestion.tasks.celery_app.settings")
    def test_result_backend_configuration(self, mock_settings):
        """Test result backend configuration."""
        mock_settings.celery_result_expires = 3600  # 1 hour

        # Re-import to get mocked settings
        import importlib
        import jd_ingestion.tasks.celery_app

        importlib.reload(jd_ingestion.tasks.celery_app)

        from jd_ingestion.tasks.celery_app import celery_app as reloaded_app

        assert reloaded_app.conf.result_expires == 3600

    def test_task_route_queue_uniqueness(self):
        """Test that different task types use different queues."""
        processing_tasks = [
            task
            for task in celery_app.conf.task_routes.keys()
            if "processing_tasks" in task
        ]
        embedding_tasks = [
            task
            for task in celery_app.conf.task_routes.keys()
            if "embedding_tasks" in task
        ]
        quality_tasks = [
            task
            for task in celery_app.conf.task_routes.keys()
            if "quality_tasks" in task
        ]

        # Check that we have tasks for each category
        assert len(processing_tasks) >= 3  # At least 3 processing task routes
        assert len(embedding_tasks) >= 4  # At least 4 embedding task routes
        assert len(quality_tasks) >= 5  # At least 5 quality task routes

        # Verify queue assignments
        for task in processing_tasks:
            if task != "jd_ingestion.tasks.processing_tasks.*":
                assert celery_app.conf.task_routes[task]["queue"] == "processing"

        for task in embedding_tasks:
            if task != "jd_ingestion.tasks.embedding_tasks.*":
                assert celery_app.conf.task_routes[task]["queue"] == "embeddings"

        for task in quality_tasks:
            if task != "jd_ingestion.tasks.quality_tasks.*":
                assert celery_app.conf.task_routes[task]["queue"] == "quality"

    def test_task_time_limits_are_sensible(self):
        """Test that task time limits are greater than soft time limits."""
        specific_tasks = [
            task_name
            for task_name in celery_app.conf.task_routes.keys()
            if not task_name.endswith("*") and "dlq_" not in task_name
        ]

        for task_name in specific_tasks:
            config = celery_app.conf.task_routes[task_name]
            if "soft_time_limit" in config and "time_limit" in config:
                soft_limit = config["soft_time_limit"]
                hard_limit = config["time_limit"]
                assert hard_limit > soft_limit, (
                    f"Task {task_name} hard limit ({hard_limit}) should be greater than soft limit ({soft_limit})"
                )

    def test_retry_backoff_progression(self):
        """Test that retry backoff values are reasonable."""
        specific_tasks = [
            task_name
            for task_name in celery_app.conf.task_routes.keys()
            if not task_name.endswith("*") and "dlq_" not in task_name
        ]

        for task_name in specific_tasks:
            config = celery_app.conf.task_routes[task_name]
            if "retry_backoff" in config:
                backoff = config["retry_backoff"]
                assert isinstance(backoff, int), (
                    f"Retry backoff for {task_name} should be an integer"
                )
                assert 0 < backoff <= 60, (
                    f"Retry backoff for {task_name} should be between 1 and 60 seconds"
                )

    @patch("jd_ingestion.tasks.celery_app.logger")
    def test_logging_configuration(self, mock_logger):
        """Test that logging is configured properly on import."""
        # Re-import to trigger logging
        import importlib
        import jd_ingestion.tasks.celery_app

        importlib.reload(jd_ingestion.tasks.celery_app)

        # Check that info log was called
        mock_logger.info.assert_called()
        call_args = mock_logger.info.call_args[0]
        assert "Celery app configured" in call_args[0]


class TestCeleryAppIntegration:
    """Test Celery app integration aspects."""

    def test_celery_app_can_be_imported(self):
        """Test that celery_app can be imported successfully."""
        from jd_ingestion.tasks.celery_app import celery_app

        assert celery_app is not None

    def test_celery_app_has_required_attributes(self):
        """Test that celery_app has all required attributes."""
        required_attrs = ["main", "conf", "control", "Task"]

        for attr in required_attrs:
            assert hasattr(celery_app, attr), f"celery_app should have attribute {attr}"

    def test_task_discovery(self):
        """Test that task modules are properly discoverable."""
        # This test ensures that the include configuration works
        expected_modules = [
            "jd_ingestion.tasks.processing_tasks",
            "jd_ingestion.tasks.embedding_tasks",
            "jd_ingestion.tasks.quality_tasks",
        ]

        for module in expected_modules:
            assert module in celery_app.conf.include

    @patch("jd_ingestion.tasks.celery_app.settings")
    def test_configuration_with_different_environments(self, mock_settings):
        """Test that configuration works with different environment settings."""
        # Test production-like settings
        mock_settings.celery_task_always_eager = False
        mock_settings.celery_worker_concurrency = 8
        mock_settings.celery_task_compression = "gzip"

        # Re-import to apply settings
        import importlib
        import jd_ingestion.tasks.celery_app

        importlib.reload(jd_ingestion.tasks.celery_app)

        from jd_ingestion.tasks.celery_app import celery_app as prod_app

        assert prod_app.conf.task_always_eager is False
        assert prod_app.conf.worker_concurrency == 8
        assert prod_app.conf.task_compression == "gzip"

        # Test development-like settings
        mock_settings.celery_task_always_eager = True
        mock_settings.celery_worker_concurrency = 1
        mock_settings.celery_task_compression = None

        # Re-import again
        importlib.reload(jd_ingestion.tasks.celery_app)

        from jd_ingestion.tasks.celery_app import celery_app as dev_app

        assert dev_app.conf.task_always_eager is True
        assert dev_app.conf.worker_concurrency == 1

    def test_queue_consistency(self):
        """Test that queue names are consistent across routing configuration."""
        all_routes = celery_app.conf.task_routes

        # Extract all unique queue names
        queues = set()
        for route_config in all_routes.values():
            if isinstance(route_config, dict) and "queue" in route_config:
                queues.add(route_config["queue"])

        expected_queues = {"processing", "embeddings", "quality", "failed_tasks"}
        assert queues == expected_queues, (
            f"Expected queues {expected_queues}, got {queues}"
        )
