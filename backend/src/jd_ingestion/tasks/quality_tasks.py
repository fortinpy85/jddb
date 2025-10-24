"""
Celery tasks for data quality metrics calculation.
"""

import asyncio
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from .celery_app import celery_app
from ..config.settings import settings
from ..services.quality_service import quality_service
from ..utils.logging import get_logger
from ..utils.retry_utils import is_retryable_error

logger = get_logger(__name__)

# Create async database session for tasks
engine = create_async_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@celery_app.task(
    bind=True, name="jd_ingestion.tasks.quality_tasks.calculate_quality_metrics_task"
)
def calculate_quality_metrics_task(self, job_id: int) -> Dict[str, Any]:
    """
    Calculate quality metrics for a specific job.

    Args:
        job_id: ID of the job to calculate metrics for

    Returns:
        Dictionary with quality metrics calculation results
    """
    try:
        logger.info(
            "Starting quality metrics calculation for job",
            job_id=job_id,
            task_id=self.request.id,
        )

        self.update_state(
            state="PROCESSING", meta={"status": "Starting quality metrics calculation"}
        )

        # Run the async quality calculation
        result = asyncio.run(_calculate_quality_metrics_async(job_id, self))

        logger.info(
            "Quality metrics calculation completed for job",
            job_id=job_id,
            task_id=self.request.id,
        )
        return result

    except Exception as e:
        logger.error(
            "Quality metrics calculation task failed",
            job_id=job_id,
            error=str(e),
            task_id=self.request.id,
        )

        # Determine if error is retryable
        if is_retryable_error(e):
            logger.warning(
                "Retryable error detected in quality calculation, scheduling retry",
                job_id=job_id,
                error=str(e),
                retries=self.request.retries,
            )

            # Calculate exponential backoff with jitter
            backoff_delay = min(
                300, (2**self.request.retries) * 10 + (hash(str(e)) % 15)
            )

            self.update_state(
                state="RETRY",
                meta={
                    "error": str(e),
                    "job_id": job_id,
                    "retry_count": self.request.retries,
                    "next_retry_in": backoff_delay,
                },
            )

            # Retry with exponential backoff
            raise self.retry(exc=e, countdown=backoff_delay, max_retries=3)
        else:
            logger.error(
                "Non-retryable error in quality calculation, marking as failed",
                job_id=job_id,
                error=str(e),
            )

            self.update_state(
                state="FAILURE",
                meta={"error": str(e), "job_id": job_id, "retryable": False},
            )
            raise


async def _calculate_quality_metrics_async(job_id: int, task) -> Dict[str, Any]:
    """Async implementation of quality metrics calculation."""
    async with AsyncSessionLocal() as db:
        try:
            # Update task progress
            task.update_state(
                state="PROCESSING",
                meta={"status": "Analyzing job content and structure"},
            )

            # Calculate quality metrics using the service
            metrics = await quality_service.calculate_quality_metrics_for_job(
                db, job_id
            )

            return {
                "status": "completed",
                "job_id": job_id,
                "metrics": {
                    "content_completeness": float(
                        metrics.get("content_completeness_score", 0)
                    ),
                    "sections_completeness": float(
                        metrics.get("sections_completeness_score", 0)
                    ),
                    "metadata_completeness": float(
                        metrics.get("metadata_completeness_score", 0)
                    ),
                    "has_structured_fields": metrics.get("has_structured_fields"),
                    "has_all_sections": metrics.get("has_all_sections"),
                    "has_embeddings": metrics.get("has_embeddings"),
                    "processing_errors": metrics.get("processing_errors_count", 0),
                    "validation_errors": metrics.get("validation_errors_count", 0),
                    "content_extraction_success": metrics.get(
                        "content_extraction_success"
                    ),
                    "quality_flags": metrics.get("quality_flags", {}),
                    "validation_results": metrics.get("validation_results", {}),
                },
            }

        except Exception:
            await db.rollback()
            raise


@celery_app.task(
    bind=True,
    name="jd_ingestion.tasks.quality_tasks.batch_calculate_quality_metrics_task",
)
def batch_calculate_quality_metrics_task(
    self, job_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Calculate quality metrics for multiple jobs.

    Args:
        job_ids: Optional list of job IDs to calculate metrics for (if None, processes all jobs)

    Returns:
        Dictionary with batch calculation results
    """
    try:
        logger.info(
            "Starting batch quality metrics calculation",
            job_count=len(job_ids) if job_ids else "all",
            task_id=self.request.id,
        )

        self.update_state(
            state="PROCESSING",
            meta={"status": "Starting batch quality metrics calculation"},
        )

        # Run the async batch calculation
        result = asyncio.run(_batch_calculate_quality_metrics_async(job_ids, self))

        logger.info(
            "Batch quality metrics calculation completed", task_id=self.request.id
        )
        return result

    except Exception as e:
        logger.error(
            "Batch quality metrics calculation task failed",
            error=str(e),
            task_id=self.request.id,
        )
        self.update_state(state="FAILURE", meta={"error": str(e), "job_ids": job_ids})
        raise


async def _batch_calculate_quality_metrics_async(
    job_ids: Optional[List[int]], task
) -> Dict[str, Any]:
    """Async implementation of batch quality metrics calculation."""
    async with AsyncSessionLocal() as db:
        try:
            # Use the quality service batch calculation method
            result = await quality_service.batch_calculate_quality_metrics(
                db=db, job_ids=job_ids
            )

            # Update task with final progress
            task.update_state(
                state="PROCESSING",
                meta={
                    "status": "Calculation completed",
                    "successful": result["successful"],
                    "failed": result["failed"],
                },
            )

            return {
                "status": "completed",
                "total_jobs": result["total_jobs"],
                "successful": result["successful"],
                "failed": result["failed"],
                "errors": result["errors"],
            }

        except Exception:
            await db.rollback()
            raise


@celery_app.task(
    bind=True, name="jd_ingestion.tasks.quality_tasks.generate_quality_report_task"
)
def generate_quality_report_task(self, job_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Generate a comprehensive quality report.

    Args:
        job_id: Optional job ID for single job report (if None, generates system-wide report)

    Returns:
        Dictionary with quality report data
    """
    try:
        report_type = "single job" if job_id else "system-wide"
        logger.info(
            "Starting quality report generation",
            report_type=report_type,
            job_id=job_id,
            task_id=self.request.id,
        )

        self.update_state(
            state="PROCESSING",
            meta={"status": f"Generating {report_type} quality report"},
        )

        # Run the async report generation
        result = asyncio.run(_generate_quality_report_async(job_id, self))

        logger.info(
            "Quality report generation completed",
            report_type=report_type,
            task_id=self.request.id,
        )
        return result

    except Exception as e:
        logger.error(
            "Quality report generation task failed",
            job_id=job_id,
            error=str(e),
            task_id=self.request.id,
        )
        self.update_state(state="FAILURE", meta={"error": str(e), "job_id": job_id})
        raise


async def _generate_quality_report_async(job_id: Optional[int], task) -> Dict[str, Any]:
    """Async implementation of quality report generation."""
    async with AsyncSessionLocal() as db:
        try:
            # Update task progress
            task.update_state(
                state="PROCESSING",
                meta={"status": "Analyzing quality data and generating report"},
            )

            # Generate report using the service
            report = await quality_service.get_quality_report(db=db, job_id=job_id)

            return {
                "status": "completed",
                "report_type": "single_job" if job_id else "system_wide",
                "job_id": job_id,
                "report": report,
            }

        except Exception:
            await db.rollback()
            raise


@celery_app.task(
    bind=True, name="jd_ingestion.tasks.quality_tasks.validate_job_content_task"
)
def validate_job_content_task(self, job_id: int) -> Dict[str, Any]:
    """
    Perform detailed content validation for a specific job.

    Args:
        job_id: ID of the job to validate

    Returns:
        Dictionary with validation results
    """
    try:
        logger.info(
            "Starting content validation for job",
            job_id=job_id,
            task_id=self.request.id,
        )

        self.update_state(
            state="PROCESSING", meta={"status": "Starting content validation"}
        )

        # Run the async validation
        result = asyncio.run(_validate_job_content_async(job_id, self))

        logger.info(
            "Content validation completed for job",
            job_id=job_id,
            task_id=self.request.id,
        )
        return result

    except Exception as e:
        logger.error(
            "Content validation task failed",
            job_id=job_id,
            error=str(e),
            task_id=self.request.id,
        )
        self.update_state(state="FAILURE", meta={"error": str(e), "job_id": job_id})
        raise


async def _validate_job_content_async(job_id: int, task) -> Dict[str, Any]:
    """Async implementation of content validation."""
    async with AsyncSessionLocal() as db:
        try:
            # Update task progress
            task.update_state(
                state="PROCESSING",
                meta={"status": "Performing detailed content validation"},
            )

            # Calculate metrics which includes validation
            metrics = await quality_service.calculate_quality_metrics_for_job(
                db, job_id
            )

            validation_results = metrics.get("validation_results", {})
            quality_flags = metrics.get("quality_flags", {})

            return {
                "status": "completed",
                "job_id": job_id,
                "validation_status": (
                    "passed" if not validation_results.get("errors") else "failed"
                ),
                "validation_results": validation_results,
                "quality_flags": quality_flags,
                "overall_score": float(metrics.get("content_completeness_score", 0)),
                "recommendations": quality_flags.get("recommendations", []),
                "needs_review": quality_flags.get("needs_review", False),
                "processing_issues": quality_flags.get("processing_issues", False),
                "content_issues": quality_flags.get("content_issues", False),
            }

        except Exception:
            await db.rollback()
            raise
