"""
Celery application configuration for async task processing.
"""

from celery import Celery
from ..config.settings import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Create Celery app
celery_app = Celery(
    "jd_ingestion",
    broker=settings.celery_broker_url_final,
    backend=settings.celery_result_backend_final,
    include=[
        "jd_ingestion.tasks.processing_tasks",
        "jd_ingestion.tasks.embedding_tasks",
        "jd_ingestion.tasks.quality_tasks",
    ],
)

# Configure Celery with production-ready settings
celery_app.conf.update(
    # Task execution and serialization
    task_serializer=settings.celery_task_serializer,
    accept_content=settings.celery_accept_content_list,
    result_serializer=settings.celery_result_serializer,
    timezone="UTC",
    enable_utc=True,
    # Production optimizations
    task_compression=settings.celery_task_compression,
    result_compression=settings.celery_result_compression,
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=settings.celery_task_eager_propagates,
    # Task routing
    task_routes={
        "jd_ingestion.tasks.processing_tasks.*": {"queue": "processing"},
        "jd_ingestion.tasks.embedding_tasks.*": {"queue": "embeddings"},
        "jd_ingestion.tasks.quality_tasks.*": {"queue": "quality"},
    },
    # Worker configuration
    worker_concurrency=settings.celery_worker_concurrency,
    worker_prefetch_multiplier=settings.celery_worker_prefetch_multiplier,
    worker_max_tasks_per_child=settings.celery_worker_max_tasks_per_child,
    worker_max_memory_per_child=settings.celery_worker_max_memory_per_child,
    worker_disable_rate_limits=settings.celery_worker_disable_rate_limits,
    worker_hijack_root_logger=False,
    task_acks_late=settings.celery_task_acks_late,
    # Task timeouts and retries
    task_soft_time_limit=settings.celery_task_soft_time_limit,
    task_time_limit=settings.celery_task_time_limit,
    task_default_retry_delay=settings.celery_task_default_retry_delay,
    task_max_retries=settings.celery_task_max_retries,
    # Enhanced retry configuration
    task_retry_backoff=True,
    task_retry_backoff_max=300,  # Maximum retry delay (5 minutes)
    task_retry_jitter=True,
    # Connection and reliability
    task_reject_on_worker_lost=settings.celery_task_reject_on_worker_lost,
    task_acks_on_failure_or_timeout=True,
    broker_connection_retry_on_startup=settings.celery_broker_connection_retry_on_startup,
    broker_connection_retry=settings.celery_broker_connection_retry,
    broker_connection_max_retries=settings.celery_broker_connection_max_retries,
    # Result backend settings
    result_expires=settings.celery_result_expires,
    # Monitoring and events
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Define task priorities and resilience settings
celery_app.conf.task_routes.update(
    {
        "jd_ingestion.tasks.processing_tasks.process_single_file_task": {
            "queue": "processing",
            "retry_backoff": 5,  # Start with 5-second delay
            "max_retries": 5,
            "soft_time_limit": 180,
            "time_limit": 300,
        },
        "jd_ingestion.tasks.processing_tasks.batch_process_files_task": {
            "queue": "processing",
            "retry_backoff": 10,  # Longer delay for batch tasks
            "max_retries": 3,
            "soft_time_limit": 900,  # 15 minutes
            "time_limit": 1200,  # 20 minutes
        },
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
            "soft_time_limit": 1800,  # 30 minutes
            "time_limit": 2400,  # 40 minutes
        },
        "jd_ingestion.tasks.embedding_tasks.generate_missing_embeddings_task": {
            "queue": "embeddings",
            "retry_backoff": 60,
            "max_retries": 2,
            "soft_time_limit": 3600,  # 1 hour
            "time_limit": 4800,  # 80 minutes
        },
        "jd_ingestion.tasks.quality_tasks.calculate_quality_metrics_task": {
            "queue": "quality",
            "retry_backoff": 10,
            "max_retries": 3,
            "soft_time_limit": 120,  # 2 minutes
            "time_limit": 180,  # 3 minutes
        },
        "jd_ingestion.tasks.quality_tasks.batch_calculate_quality_metrics_task": {
            "queue": "quality",
            "retry_backoff": 30,
            "max_retries": 2,
            "soft_time_limit": 900,  # 15 minutes
            "time_limit": 1200,  # 20 minutes
        },
        "jd_ingestion.tasks.quality_tasks.generate_quality_report_task": {
            "queue": "quality",
            "retry_backoff": 15,
            "max_retries": 2,
            "soft_time_limit": 300,  # 5 minutes
            "time_limit": 420,  # 7 minutes
        },
        "jd_ingestion.tasks.quality_tasks.validate_job_content_task": {
            "queue": "quality",
            "retry_backoff": 5,
            "max_retries": 3,
            "soft_time_limit": 90,  # 1.5 minutes
            "time_limit": 150,  # 2.5 minutes
        },
    }
)

# Dead letter queue configuration
celery_app.conf.task_routes.update(
    {
        "jd_ingestion.tasks.*.dlq_*": {"queue": "failed_tasks"},
    }
)

logger.info("Celery app configured", broker_url=settings.redis_url)
