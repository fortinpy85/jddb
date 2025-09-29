"""
Tests for Celery tasks and configuration.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from jd_ingestion.tasks.celery_app import celery_app


class TestCeleryAppConfiguration:
    """Test Celery app configuration."""

    def test_celery_app_creation(self):
        """Test that Celery app is created correctly."""
        assert celery_app.main == "jd_ingestion"
        assert celery_app.conf.timezone == "UTC"
        assert celery_app.conf.enable_utc is True

    def test_task_routes(self):
        """Test task routing configuration."""
        routes = celery_app.conf.task_routes

        # Check general queue routing
        assert routes["jd_ingestion.tasks.processing_tasks.*"]["queue"] == "processing"
        assert routes["jd_ingestion.tasks.embedding_tasks.*"]["queue"] == "embeddings"
        assert routes["jd_ingestion.tasks.quality_tasks.*"]["queue"] == "quality"

    def test_specific_task_routes(self):
        """Test specific task routing with timeouts and retries."""
        routes = celery_app.conf.task_routes

        # Check process_single_file_task configuration
        single_file_config = routes.get(
            "jd_ingestion.tasks.processing_tasks.process_single_file_task"
        )
        assert single_file_config is not None
        assert single_file_config["queue"] == "processing"
        assert single_file_config["max_retries"] == 5
        assert single_file_config["soft_time_limit"] == 180

        # Check batch processing configuration
        batch_config = routes.get(
            "jd_ingestion.tasks.processing_tasks.batch_process_files_task"
        )
        assert batch_config is not None
        assert batch_config["queue"] == "processing"
        assert batch_config["max_retries"] == 3
        assert batch_config["soft_time_limit"] == 900

    def test_embedding_task_routes(self):
        """Test embedding task routing configuration."""
        routes = celery_app.conf.task_routes

        # Check generate_embeddings_for_job_task
        single_embedding_config = routes.get(
            "jd_ingestion.tasks.embedding_tasks.generate_embeddings_for_job_task"
        )
        assert single_embedding_config is not None
        assert single_embedding_config["queue"] == "embeddings"
        assert single_embedding_config["max_retries"] == 4

        # Check batch embedding task
        batch_embedding_config = routes.get(
            "jd_ingestion.tasks.embedding_tasks.batch_generate_embeddings_task"
        )
        assert batch_embedding_config is not None
        assert batch_embedding_config["soft_time_limit"] == 1800

    def test_quality_task_routes(self):
        """Test quality task routing configuration."""
        routes = celery_app.conf.task_routes

        # Check quality metrics calculation
        quality_config = routes.get(
            "jd_ingestion.tasks.quality_tasks.calculate_quality_metrics_task"
        )
        assert quality_config is not None
        assert quality_config["queue"] == "quality"
        assert quality_config["soft_time_limit"] == 120

    def test_dead_letter_queue_config(self):
        """Test dead letter queue configuration."""
        routes = celery_app.conf.task_routes
        dlq_config = routes.get("jd_ingestion.tasks.*.dlq_*")
        assert dlq_config is not None
        assert dlq_config["queue"] == "failed_tasks"

    def test_worker_configuration(self):
        """Test worker configuration settings."""
        conf = celery_app.conf

        # Check worker settings are present (values depend on settings module)
        assert hasattr(conf, "worker_concurrency")
        assert hasattr(conf, "worker_prefetch_multiplier")
        assert hasattr(conf, "worker_max_tasks_per_child")
        assert hasattr(conf, "worker_max_memory_per_child")

    def test_task_configuration(self):
        """Test general task configuration."""
        conf = celery_app.conf

        # Check task serialization
        assert hasattr(conf, "task_serializer")
        assert hasattr(conf, "result_serializer")
        assert hasattr(conf, "accept_content")

        # Check retry and timeout settings
        assert hasattr(conf, "task_soft_time_limit")
        assert hasattr(conf, "task_time_limit")
        assert hasattr(conf, "task_default_retry_delay")
        assert hasattr(conf, "task_max_retries")

        # Check retry backoff settings
        assert conf.task_retry_backoff is True
        assert conf.task_retry_backoff_max == 300
        assert conf.task_retry_jitter is True

    def test_monitoring_configuration(self):
        """Test monitoring and events configuration."""
        conf = celery_app.conf

        assert conf.worker_send_task_events is True
        assert conf.task_send_sent_event is True

    def test_reliability_configuration(self):
        """Test reliability and connection settings."""
        conf = celery_app.conf

        assert hasattr(conf, "task_reject_on_worker_lost")
        assert conf.task_acks_on_failure_or_timeout is True
        assert hasattr(conf, "broker_connection_retry_on_startup")

    def test_includes_configuration(self):
        """Test that task modules are properly included."""
        includes = celery_app.conf.include

        expected_includes = [
            "jd_ingestion.tasks.processing_tasks",
            "jd_ingestion.tasks.embedding_tasks",
            "jd_ingestion.tasks.quality_tasks",
        ]

        for module in expected_includes:
            assert module in includes


class TestProcessingTasks:
    """Test processing tasks (mock tests since tasks require full setup)."""

    @patch("jd_ingestion.tasks.processing_tasks.AsyncSessionLocal")
    @patch("jd_ingestion.tasks.processing_tasks.FileDiscovery")
    @patch("jd_ingestion.tasks.processing_tasks.ContentProcessor")
    def test_process_single_file_task_mock(
        self, mock_processor, mock_discovery, mock_session
    ):
        """Test process_single_file_task with mocks."""
        # This is a simplified test - in reality, we'd need to import and test the actual task
        # For now, we verify that the task is registered with Celery

        task_name = "jd_ingestion.tasks.processing_tasks.process_single_file_task"
        assert task_name in celery_app.tasks

    def test_batch_process_files_task_registration(self):
        """Test that batch processing task is registered."""
        task_name = "jd_ingestion.tasks.processing_tasks.batch_process_files_task"
        # The task would be registered when the module is imported
        # This test verifies the route configuration exists
        routes = celery_app.conf.task_routes
        assert task_name in routes

    def test_processing_queue_configuration(self):
        """Test processing queue configuration."""
        routes = celery_app.conf.task_routes
        processing_pattern = "jd_ingestion.tasks.processing_tasks.*"

        assert processing_pattern in routes
        assert routes[processing_pattern]["queue"] == "processing"


class TestEmbeddingTasks:
    """Test embedding tasks configuration."""

    def test_embedding_tasks_registration(self):
        """Test that embedding tasks are configured."""
        routes = celery_app.conf.task_routes

        embedding_tasks = [
            "jd_ingestion.tasks.embedding_tasks.generate_embeddings_for_job_task",
            "jd_ingestion.tasks.embedding_tasks.batch_generate_embeddings_task",
            "jd_ingestion.tasks.embedding_tasks.generate_missing_embeddings_task",
        ]

        for task_name in embedding_tasks:
            assert task_name in routes
            assert routes[task_name]["queue"] == "embeddings"

    def test_embedding_task_timeouts(self):
        """Test embedding task timeout configurations."""
        routes = celery_app.conf.task_routes

        # Single job embedding should have shorter timeout
        single_config = routes[
            "jd_ingestion.tasks.embedding_tasks.generate_embeddings_for_job_task"
        ]
        assert single_config["soft_time_limit"] == 300
        assert single_config["time_limit"] == 600

        # Batch embedding should have longer timeout
        batch_config = routes[
            "jd_ingestion.tasks.embedding_tasks.batch_generate_embeddings_task"
        ]
        assert batch_config["soft_time_limit"] == 1800
        assert batch_config["time_limit"] == 2400


class TestQualityTasks:
    """Test quality tasks configuration."""

    def test_quality_tasks_registration(self):
        """Test that quality tasks are configured."""
        routes = celery_app.conf.task_routes

        quality_tasks = [
            "jd_ingestion.tasks.quality_tasks.calculate_quality_metrics_task",
            "jd_ingestion.tasks.quality_tasks.batch_calculate_quality_metrics_task",
            "jd_ingestion.tasks.quality_tasks.generate_quality_report_task",
            "jd_ingestion.tasks.quality_tasks.validate_job_content_task",
        ]

        for task_name in quality_tasks:
            assert task_name in routes
            assert routes[task_name]["queue"] == "quality"

    def test_quality_task_retry_settings(self):
        """Test quality task retry configurations."""
        routes = celery_app.conf.task_routes

        # Validation task should have quick retries
        validate_config = routes[
            "jd_ingestion.tasks.quality_tasks.validate_job_content_task"
        ]
        assert validate_config["max_retries"] == 3
        assert validate_config["retry_backoff"] == 5

        # Quality metrics should have moderate retries
        metrics_config = routes[
            "jd_ingestion.tasks.quality_tasks.calculate_quality_metrics_task"
        ]
        assert metrics_config["max_retries"] == 3
        assert metrics_config["retry_backoff"] == 10


class TestTaskConfiguration:
    """Test individual task configuration settings."""

    def test_retry_backoff_settings(self):
        """Test retry backoff configurations for different task types."""
        routes = celery_app.conf.task_routes

        # Processing tasks should have moderate backoff
        single_process = routes[
            "jd_ingestion.tasks.processing_tasks.process_single_file_task"
        ]
        assert single_process["retry_backoff"] == 5

        batch_process = routes[
            "jd_ingestion.tasks.processing_tasks.batch_process_files_task"
        ]
        assert batch_process["retry_backoff"] == 10

        # Embedding tasks should have longer backoff (API rate limiting)
        embedding_task = routes[
            "jd_ingestion.tasks.embedding_tasks.generate_embeddings_for_job_task"
        ]
        assert embedding_task["retry_backoff"] == 15

    def test_time_limit_hierarchy(self):
        """Test that batch tasks have longer time limits than single tasks."""
        routes = celery_app.conf.task_routes

        # Single file processing
        single_limit = routes[
            "jd_ingestion.tasks.processing_tasks.process_single_file_task"
        ]["time_limit"]

        # Batch file processing
        batch_limit = routes[
            "jd_ingestion.tasks.processing_tasks.batch_process_files_task"
        ]["time_limit"]

        assert batch_limit > single_limit

        # Single embedding
        single_emb_limit = routes[
            "jd_ingestion.tasks.embedding_tasks.generate_embeddings_for_job_task"
        ]["time_limit"]

        # Batch embedding
        batch_emb_limit = routes[
            "jd_ingestion.tasks.embedding_tasks.batch_generate_embeddings_task"
        ]["time_limit"]

        assert batch_emb_limit > single_emb_limit

    def test_max_retries_by_task_type(self):
        """Test that different task types have appropriate retry counts."""
        routes = celery_app.conf.task_routes

        # File processing should have more retries (file I/O issues)
        single_process = routes[
            "jd_ingestion.tasks.processing_tasks.process_single_file_task"
        ]
        assert single_process["max_retries"] == 5

        # Embedding tasks should have moderate retries (API limitations)
        embedding_task = routes[
            "jd_ingestion.tasks.embedding_tasks.generate_embeddings_for_job_task"
        ]
        assert embedding_task["max_retries"] == 4

        # Quality tasks should have fewer retries (computation-based)
        quality_task = routes[
            "jd_ingestion.tasks.quality_tasks.calculate_quality_metrics_task"
        ]
        assert quality_task["max_retries"] == 3


class TestCeleryIntegration:
    """Test Celery integration aspects."""

    def test_task_always_eager_setting(self):
        """Test task_always_eager setting from configuration."""
        # This setting should come from the settings module
        assert hasattr(celery_app.conf, "task_always_eager")

    def test_compression_settings(self):
        """Test compression configurations."""
        conf = celery_app.conf

        assert hasattr(conf, "task_compression")
        assert hasattr(conf, "result_compression")

    def test_broker_and_backend_urls(self):
        """Test that broker and backend URLs are configured."""
        # URLs should come from settings
        assert celery_app.conf.broker_url is not None
        assert celery_app.conf.result_backend is not None

    def test_queue_names_consistency(self):
        """Test that all referenced queues are consistently named."""
        routes = celery_app.conf.task_routes

        expected_queues = {"processing", "embeddings", "quality", "failed_tasks"}
        used_queues = set()

        for route_config in routes.values():
            if isinstance(route_config, dict) and "queue" in route_config:
                used_queues.add(route_config["queue"])

        # All used queues should be in expected queues
        assert used_queues.issubset(expected_queues)
