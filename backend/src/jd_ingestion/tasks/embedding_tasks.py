"""
Celery tasks for embedding generation.
"""

import asyncio
from typing import List, Dict, Any, Optional
from celery import current_task
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from .celery_app import celery_app
from ..config.settings import settings
from ..database.models import ContentChunk, JobDescription
from ..services.embedding_service import embedding_service
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Create async database session for tasks
engine = create_async_engine(settings.database_url)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@celery_app.task(
    bind=True,
    name="jd_ingestion.tasks.embedding_tasks.generate_embeddings_for_job_task",
)
def generate_embeddings_for_job_task(self, job_id: int) -> Dict[str, Any]:
    """
    Generate embeddings for all chunks of a specific job.

    Args:
        job_id: ID of the job to generate embeddings for

    Returns:
        Dictionary with embedding generation results
    """
    try:
        logger.info(
            "Starting embedding generation for job",
            job_id=job_id,
            task_id=self.request.id,
        )

        self.update_state(
            state="PROCESSING", meta={"status": "Starting embedding generation"}
        )

        # Run the async embedding generation
        result = asyncio.run(_generate_embeddings_for_job_async(job_id, self))

        logger.info(
            "Embedding generation completed for job",
            job_id=job_id,
            task_id=self.request.id,
        )
        return result

    except Exception as e:
        logger.error(
            "Embedding generation task failed",
            job_id=job_id,
            error=str(e),
            task_id=self.request.id,
        )

        # Determine if error is retryable
        if _is_retryable_error(e):
            logger.warning(
                "Retryable error detected in embedding generation, scheduling retry",
                job_id=job_id,
                error=str(e),
                retries=self.request.retries,
            )

            # Calculate exponential backoff with jitter
            backoff_delay = min(
                900, (2**self.request.retries) * 15 + (hash(str(e)) % 30)
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
            raise self.retry(exc=e, countdown=backoff_delay, max_retries=4)
        else:
            logger.error(
                "Non-retryable error in embedding generation, marking as failed",
                job_id=job_id,
                error=str(e),
            )

            self.update_state(
                state="FAILURE",
                meta={"error": str(e), "job_id": job_id, "retryable": False},
            )
            raise


async def _generate_embeddings_for_job_async(job_id: int, task) -> Dict[str, Any]:
    """Async implementation of embedding generation for a job."""
    async with AsyncSessionLocal() as db:
        try:
            # Get all chunks for this job that don't have embeddings
            chunks_query = select(ContentChunk).where(
                ContentChunk.job_id == job_id, ContentChunk.embedding.is_(None)
            )
            chunks_result = await db.execute(chunks_query)
            chunks = chunks_result.scalars().all()

            if not chunks:
                return {
                    "status": "completed",
                    "job_id": job_id,
                    "message": "No chunks found or all chunks already have embeddings",
                    "chunks_processed": 0,
                }

            # Update task progress
            task.update_state(
                state="PROCESSING",
                meta={
                    "status": f"Generating embeddings for {len(chunks)} chunks",
                    "total_chunks": len(chunks),
                },
            )

            successful_embeddings = 0
            failed_embeddings = 0

            # Process chunks in batches for better progress tracking
            batch_size = 5
            total_chunks = len(chunks)

            for i in range(0, len(chunks), batch_size):
                batch = chunks[i : i + batch_size]

                # Update progress
                progress = int((i / total_chunks) * 100)
                task.update_state(
                    state="PROCESSING",
                    meta={
                        "status": f"Processing batch {i//batch_size + 1}",
                        "progress": progress,
                        "chunks_processed": i,
                        "total_chunks": total_chunks,
                    },
                )

                # Generate embeddings for this batch
                for chunk in batch:
                    try:
                        embedding = await embedding_service.generate_embedding(
                            chunk.chunk_text
                        )

                        if embedding:
                            chunk.embedding = embedding
                            successful_embeddings += 1
                        else:
                            logger.warning(
                                "Failed to generate embedding for chunk",
                                chunk_id=chunk.id,
                            )
                            failed_embeddings += 1

                    except Exception as e:
                        logger.error(
                            "Error generating embedding for chunk",
                            chunk_id=chunk.id,
                            error=str(e),
                        )
                        failed_embeddings += 1

                # Commit batch
                await db.commit()

            result = {
                "status": "completed",
                "job_id": job_id,
                "chunks_processed": len(chunks),
                "successful_embeddings": successful_embeddings,
                "failed_embeddings": failed_embeddings,
            }

            logger.info(
                "Embedding generation completed for job",
                job_id=job_id,
                successful=successful_embeddings,
                failed=failed_embeddings,
            )

            return result

        except Exception as e:
            await db.rollback()
            raise


@celery_app.task(
    bind=True, name="jd_ingestion.tasks.embedding_tasks.batch_generate_embeddings_task"
)
def batch_generate_embeddings_task(self, job_ids: List[int]) -> Dict[str, Any]:
    """
    Generate embeddings for multiple jobs.

    Args:
        job_ids: List of job IDs to generate embeddings for

    Returns:
        Dictionary with batch embedding generation results
    """
    try:
        logger.info(
            "Starting batch embedding generation",
            job_count=len(job_ids),
            task_id=self.request.id,
        )

        self.update_state(
            state="PROCESSING", meta={"status": "Starting batch embedding generation"}
        )

        # Run the async batch embedding generation
        result = asyncio.run(_batch_generate_embeddings_async(job_ids, self))

        logger.info("Batch embedding generation completed", task_id=self.request.id)
        return result

    except Exception as e:
        logger.error(
            "Batch embedding generation task failed",
            error=str(e),
            task_id=self.request.id,
        )
        self.update_state(state="FAILURE", meta={"error": str(e), "job_ids": job_ids})
        raise


async def _batch_generate_embeddings_async(job_ids: List[int], task) -> Dict[str, Any]:
    """Async implementation of batch embedding generation."""
    async with AsyncSessionLocal() as db:
        try:
            total_jobs = len(job_ids)
            processed_jobs = 0
            successful_jobs = []
            failed_jobs = []
            total_chunks_processed = 0
            total_successful_embeddings = 0
            total_failed_embeddings = 0

            for job_id in job_ids:
                try:
                    # Update progress
                    progress = int((processed_jobs / total_jobs) * 100)
                    task.update_state(
                        state="PROCESSING",
                        meta={
                            "status": f"Processing job {processed_jobs + 1} of {total_jobs}",
                            "current_job_id": job_id,
                            "progress": progress,
                        },
                    )

                    # Generate embeddings for this job
                    result = await _generate_embeddings_for_job_async(job_id, task)

                    if result["status"] == "completed":
                        successful_jobs.append(job_id)
                        total_chunks_processed += result["chunks_processed"]
                        total_successful_embeddings += result["successful_embeddings"]
                        total_failed_embeddings += result["failed_embeddings"]
                    else:
                        failed_jobs.append({"job_id": job_id, "error": "Unknown error"})

                    processed_jobs += 1

                except Exception as e:
                    logger.error(
                        "Failed to generate embeddings for job in batch",
                        job_id=job_id,
                        error=str(e),
                    )
                    failed_jobs.append({"job_id": job_id, "error": str(e)})
                    processed_jobs += 1

            result = {
                "status": "completed",
                "total_jobs": total_jobs,
                "successful_jobs": len(successful_jobs),
                "failed_jobs": len(failed_jobs),
                "total_chunks_processed": total_chunks_processed,
                "total_successful_embeddings": total_successful_embeddings,
                "total_failed_embeddings": total_failed_embeddings,
                "results": {
                    "successful_job_ids": successful_jobs,
                    "failed_jobs": failed_jobs,
                },
            }

            logger.info(
                "Batch embedding generation completed",
                successful_jobs=len(successful_jobs),
                failed_jobs=len(failed_jobs),
                total_embeddings=total_successful_embeddings,
            )

            return result

        except Exception as e:
            await db.rollback()
            raise


@celery_app.task(
    bind=True,
    name="jd_ingestion.tasks.embedding_tasks.generate_missing_embeddings_task",
)
def generate_missing_embeddings_task(
    self, limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate embeddings for all chunks that don't have them.

    Args:
        limit: Maximum number of chunks to process

    Returns:
        Dictionary with embedding generation results
    """
    try:
        logger.info(
            "Starting missing embeddings generation",
            limit=limit,
            task_id=self.request.id,
        )

        self.update_state(
            state="PROCESSING", meta={"status": "Finding chunks without embeddings"}
        )

        # Run the async embedding generation
        result = asyncio.run(_generate_missing_embeddings_async(limit, self))

        logger.info("Missing embeddings generation completed", task_id=self.request.id)
        return result

    except Exception as e:
        logger.error(
            "Missing embeddings generation task failed",
            error=str(e),
            task_id=self.request.id,
        )
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise


async def _generate_missing_embeddings_async(
    limit: Optional[int], task
) -> Dict[str, Any]:
    """Async implementation of missing embeddings generation."""
    async with AsyncSessionLocal() as db:
        try:
            # Get all chunks that don't have embeddings
            chunks_query = select(ContentChunk).where(ContentChunk.embedding.is_(None))
            if limit:
                chunks_query = chunks_query.limit(limit)

            chunks_result = await db.execute(chunks_query)
            chunks = chunks_result.scalars().all()

            if not chunks:
                return {
                    "status": "completed",
                    "message": "No chunks found without embeddings",
                    "chunks_processed": 0,
                }

            # Update task progress
            task.update_state(
                state="PROCESSING",
                meta={
                    "status": f"Generating embeddings for {len(chunks)} chunks",
                    "total_chunks": len(chunks),
                },
            )

            successful_embeddings = 0
            failed_embeddings = 0

            # Process chunks with progress tracking
            batch_size = 10
            total_chunks = len(chunks)

            for i in range(0, len(chunks), batch_size):
                batch = chunks[i : i + batch_size]

                # Update progress
                progress = int((i / total_chunks) * 100)
                task.update_state(
                    state="PROCESSING",
                    meta={
                        "status": f"Processing batch {i//batch_size + 1}",
                        "progress": progress,
                        "chunks_processed": i,
                        "total_chunks": total_chunks,
                    },
                )

                # Generate embeddings for this batch
                texts = [chunk.chunk_text for chunk in batch]
                embeddings = await embedding_service.generate_embeddings_batch(
                    texts, batch_size=len(batch)
                )

                # Update chunks with embeddings
                for chunk, embedding in zip(batch, embeddings):
                    if embedding:
                        chunk.embedding = embedding
                        successful_embeddings += 1
                    else:
                        failed_embeddings += 1

                # Commit batch
                await db.commit()

            result = {
                "status": "completed",
                "chunks_processed": len(chunks),
                "successful_embeddings": successful_embeddings,
                "failed_embeddings": failed_embeddings,
            }

            logger.info(
                "Missing embeddings generation completed",
                successful=successful_embeddings,
                failed=failed_embeddings,
            )

            return result

        except Exception as e:
            await db.rollback()
            raise


def _is_retryable_error(exc: Exception) -> bool:
    """
    Determine if an exception should trigger a task retry.

    Args:
        exc: The exception that occurred

    Returns:
        True if the error is retryable, False otherwise
    """
    # Non-retryable errors (permanent failures)
    non_retryable_errors = (
        FileNotFoundError,  # File doesn't exist
        PermissionError,  # Permission denied
        ValueError,  # Invalid data/parameters
        TypeError,  # Type mismatches
        KeyError,  # Missing required data
    )

    if isinstance(exc, non_retryable_errors):
        return False

    # Retryable errors (temporary failures)
    retryable_errors = (
        ConnectionError,  # Network/database connection issues
        TimeoutError,  # Operation timeouts
        OSError,  # I/O errors
        ImportError,  # Module loading issues
        RuntimeError,  # General runtime issues
    )

    if isinstance(exc, retryable_errors):
        return True

    # Check error message for specific patterns (especially for OpenAI API)
    error_message = str(exc).lower()
    retryable_patterns = [
        "connection",
        "timeout",
        "temporary",
        "rate limit",
        "service unavailable",
        "internal server error",
        "database",
        "network",
        "redis",
        "celery",
        "openai",
        "api",
        "quota",
        "token",
        "embedding",
    ]

    for pattern in retryable_patterns:
        if pattern in error_message:
            return True

    # Default to non-retryable for safety
    return False
