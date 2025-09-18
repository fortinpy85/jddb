"""
Celery tasks for job description processing.
"""

import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from celery import current_task
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from .celery_app import celery_app
from ..config.settings import settings
from ..core.file_discovery import FileDiscovery
from ..processors.content_processor import ContentProcessor
from ..database.models import JobDescription, JobSection, JobMetadata, ContentChunk
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Create async database session for tasks
engine = create_async_engine(settings.database_url)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@celery_app.task(
    bind=True, name="jd_ingestion.tasks.processing_tasks.process_single_file_task"
)
def process_single_file_task(
    self, file_path: str, generate_embeddings: bool = True
) -> Dict[str, Any]:
    """
    Process a single job description file.

    Args:
        file_path: Path to the file to process
        generate_embeddings: Whether to generate embeddings after processing

    Returns:
        Dictionary with processing results
    """
    try:
        logger.info(
            "Starting file processing task",
            file_path=file_path,
            task_id=self.request.id,
        )

        # Update task state
        self.update_state(
            state="PROCESSING", meta={"status": "Starting file processing"}
        )

        # Run the async processing function
        result = asyncio.run(
            _process_single_file_async(file_path, self, generate_embeddings)
        )

        logger.info(
            "File processing task completed",
            file_path=file_path,
            task_id=self.request.id,
        )
        return result

    except Exception as e:
        logger.error(
            "File processing task failed",
            file_path=file_path,
            error=str(e),
            task_id=self.request.id,
        )

        # Determine if error is retryable
        if _is_retryable_error(e):
            logger.warning(
                "Retryable error detected, scheduling retry",
                file_path=file_path,
                error=str(e),
                retries=self.request.retries,
            )

            # Calculate exponential backoff with jitter
            backoff_delay = min(
                300, (2**self.request.retries) * 5 + (hash(str(e)) % 10)
            )

            self.update_state(
                state="RETRY",
                meta={
                    "error": str(e),
                    "file_path": file_path,
                    "retry_count": self.request.retries,
                    "next_retry_in": backoff_delay,
                },
            )

            # Retry with exponential backoff
            raise self.retry(exc=e, countdown=backoff_delay, max_retries=5)
        else:
            logger.error(
                "Non-retryable error, marking as failed",
                file_path=file_path,
                error=str(e),
            )

            self.update_state(
                state="FAILURE",
                meta={"error": str(e), "file_path": file_path, "retryable": False},
            )
            raise


async def _process_single_file_async(
    file_path: str, task, generate_embeddings: bool = True
) -> Dict[str, Any]:
    """Async implementation of file processing."""
    async with AsyncSessionLocal() as db:
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File does not exist: {file_path}")

            # Initialize processors
            file_discovery = FileDiscovery(file_path_obj.parent)
            content_processor = ContentProcessor("")

            # Update task progress
            task.update_state(
                state="PROCESSING", meta={"status": "Extracting file metadata"}
            )

            # Extract file metadata
            file_metadata = file_discovery._extract_file_metadata(file_path_obj)

            if not file_metadata.is_valid:
                return {
                    "status": "error",
                    "file_path": file_path,
                    "errors": file_metadata.validation_errors,
                }

            # Update task progress
            task.update_state(
                state="PROCESSING", meta={"status": "Reading file content"}
            )

            # Read file content
            try:
                with open(file_path_obj, "r", encoding=file_metadata.encoding) as f:
                    raw_content = f.read()
            except Exception as e:
                raise Exception(f"Failed to read file: {str(e)}")

            # Update task progress
            task.update_state(state="PROCESSING", meta={"status": "Processing content"})

            # Process content
            try:
                processed_content = content_processor.process_content(
                    raw_content, file_metadata.language or "en"
                )
            except Exception as e:
                logger.error("Content processing failed", error=str(e))
                # Create minimal processed_content for fallback
                from dataclasses import dataclass, field

                @dataclass
                class MinimalStructuredFields:
                    position_title: str = ""
                    job_number: str = ""
                    classification: str = ""
                    department: str = ""
                    reports_to: str = ""

                @dataclass
                class MinimalProcessedContent:
                    cleaned_content: str = raw_content
                    sections: Dict = field(default_factory=dict)
                    structured_fields: MinimalStructuredFields = field(
                        default_factory=MinimalStructuredFields
                    )
                    processing_errors: list = field(default_factory=list)

                processed_content = MinimalProcessedContent()
                processed_content.processing_errors = [str(e)]

            # Update task progress
            task.update_state(
                state="PROCESSING", meta={"status": "Generating content chunks"}
            )

            # Generate chunks
            try:
                cleaned_content = processed_content.cleaned_content
                if not isinstance(cleaned_content, str):
                    cleaned_content = str(cleaned_content)

                chunks = content_processor.chunk_content(cleaned_content)
                logger.info("Chunk generation completed", chunk_count=len(chunks))
            except Exception as e:
                logger.error("Chunk generation failed", error=str(e))
                chunks = []

            # Update task progress
            task.update_state(state="PROCESSING", meta={"status": "Saving to database"})

            # Save to database
            try:
                # Create job description record
                job_description = JobDescription(
                    job_number=file_metadata.job_number or "UNKNOWN",
                    title=file_metadata.title or "Untitled",
                    classification=file_metadata.classification or "UNKNOWN",
                    language=file_metadata.language or "en",
                    file_path=str(file_path_obj),
                    raw_content=raw_content,
                    file_hash=file_metadata.file_hash,
                )

                db.add(job_description)
                await db.flush()  # Get the ID

                # Save sections
                for section_type, section_content in processed_content.sections.items():
                    if section_content and section_content.strip():
                        job_section = JobSection(
                            job_id=job_description.id,
                            section_type=section_type,
                            section_content=section_content,
                            section_order=list(processed_content.sections.keys()).index(
                                section_type
                            ),
                        )
                        db.add(job_section)

                # Save metadata if available
                if (
                    hasattr(processed_content.structured_fields, "department")
                    and processed_content.structured_fields.department
                ):
                    job_metadata = JobMetadata(
                        job_id=job_description.id,
                        department=processed_content.structured_fields.department,
                        reports_to=getattr(
                            processed_content.structured_fields, "reports_to", None
                        ),
                    )
                    db.add(job_metadata)

                # Save chunks
                for i, chunk_text in enumerate(chunks):
                    if chunk_text and chunk_text.strip():
                        content_chunk = ContentChunk(
                            job_id=job_description.id,
                            chunk_text=chunk_text,
                            chunk_index=i,
                        )
                        db.add(content_chunk)

                await db.commit()
                job_id = job_description.id

                logger.info("Job saved to database", job_id=job_id, file_path=file_path)

                # Trigger embedding generation if requested
                if generate_embeddings and chunks:
                    from .embedding_tasks import generate_embeddings_for_job_task

                    generate_embeddings_for_job_task.delay(job_id)

                # Trigger quality metrics calculation for the newly processed job
                from .quality_tasks import calculate_quality_metrics_task

                calculate_quality_metrics_task.delay(job_id)

                return {
                    "status": "success",
                    "file_path": file_path,
                    "job_id": job_id,
                    "metadata": {
                        "job_number": file_metadata.job_number,
                        "classification": file_metadata.classification,
                        "language": file_metadata.language,
                        "title": file_metadata.title,
                        "file_size": file_metadata.file_size,
                        "file_hash": file_metadata.file_hash,
                    },
                    "processed_content": {
                        "sections_found": len(processed_content.sections),
                        "sections": list(processed_content.sections.keys()),
                        "chunks_generated": len(chunks),
                        "processing_errors": processed_content.processing_errors,
                    },
                }

            except Exception as e:
                logger.error("Database save failed", error=str(e))
                await db.rollback()
                raise

        except Exception as e:
            await db.rollback()
            raise


@celery_app.task(
    bind=True, name="jd_ingestion.tasks.processing_tasks.batch_process_files_task"
)
def batch_process_files_task(
    self,
    directory_path: str,
    max_files: Optional[int] = None,
    recursive: bool = True,
    generate_embeddings: bool = True,
) -> Dict[str, Any]:
    """
    Process multiple job description files from a directory.

    Args:
        directory_path: Directory containing files to process
        max_files: Maximum number of files to process
        recursive: Whether to scan subdirectories
        generate_embeddings: Whether to generate embeddings after processing

    Returns:
        Dictionary with batch processing results
    """
    try:
        logger.info(
            "Starting batch processing task",
            directory=directory_path,
            task_id=self.request.id,
        )

        self.update_state(state="PROCESSING", meta={"status": "Scanning directory"})

        # Scan directory
        data_path = Path(directory_path)
        if not data_path.exists():
            raise FileNotFoundError(f"Directory does not exist: {directory_path}")

        file_discovery = FileDiscovery(data_path)
        files_metadata = file_discovery.scan_directory(recursive=recursive)

        # Filter valid files
        valid_files = [f for f in files_metadata if f.is_valid]

        # Limit files if specified
        if max_files:
            valid_files = valid_files[:max_files]

        if not valid_files:
            return {"status": "error", "message": "No valid files found for processing"}

        # Process files
        total_files = len(valid_files)
        processed_files = 0
        successful_files = []
        failed_files = []

        for file_metadata in valid_files:
            try:
                self.update_state(
                    state="PROCESSING",
                    meta={
                        "status": f"Processing file {processed_files + 1} of {total_files}",
                        "current_file": file_metadata.file_path.name,
                        "progress": int((processed_files / total_files) * 100),
                    },
                )

                # Process single file (without triggering separate embedding task)
                result = asyncio.run(
                    _process_single_file_async(
                        str(file_metadata.file_path), self, generate_embeddings=False
                    )
                )

                if result["status"] == "success":
                    successful_files.append(
                        {
                            "file_path": str(file_metadata.file_path),
                            "job_id": result["job_id"],
                        }
                    )
                else:
                    failed_files.append(
                        {
                            "file_path": str(file_metadata.file_path),
                            "error": result.get("errors", "Unknown error"),
                        }
                    )

                processed_files += 1

            except Exception as e:
                logger.error(
                    "Failed to process file in batch",
                    file_path=str(file_metadata.file_path),
                    error=str(e),
                )
                failed_files.append(
                    {"file_path": str(file_metadata.file_path), "error": str(e)}
                )
                processed_files += 1

        # Trigger batch embedding generation for all successful jobs
        if generate_embeddings and successful_files:
            from .embedding_tasks import batch_generate_embeddings_task

            job_ids = [f["job_id"] for f in successful_files]
            batch_generate_embeddings_task.delay(job_ids)

        result = {
            "status": "completed",
            "directory": directory_path,
            "total_files_found": len(files_metadata),
            "valid_files_found": len(valid_files),
            "files_processed": processed_files,
            "successful_files": len(successful_files),
            "failed_files": len(failed_files),
            "results": {"successful": successful_files, "failed": failed_files},
        }

        logger.info(
            "Batch processing task completed",
            directory=directory_path,
            successful=len(successful_files),
            failed=len(failed_files),
            task_id=self.request.id,
        )

        return result

    except Exception as e:
        logger.error(
            "Batch processing task failed",
            directory=directory_path,
            error=str(e),
            task_id=self.request.id,
        )

        # Determine if error is retryable
        if _is_retryable_error(e):
            logger.warning(
                "Retryable error detected in batch processing, scheduling retry",
                directory=directory_path,
                error=str(e),
                retries=self.request.retries,
            )

            # Calculate exponential backoff with jitter
            backoff_delay = min(
                600, (2**self.request.retries) * 10 + (hash(str(e)) % 20)
            )

            self.update_state(
                state="RETRY",
                meta={
                    "error": str(e),
                    "directory": directory_path,
                    "retry_count": self.request.retries,
                    "next_retry_in": backoff_delay,
                },
            )

            # Retry with exponential backoff
            raise self.retry(exc=e, countdown=backoff_delay, max_retries=3)
        else:
            logger.error(
                "Non-retryable error in batch processing, marking as failed",
                directory=directory_path,
                error=str(e),
            )

            self.update_state(
                state="FAILURE",
                meta={"error": str(e), "directory": directory_path, "retryable": False},
            )
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

    # Check error message for specific patterns
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
    ]

    for pattern in retryable_patterns:
        if pattern in error_message:
            return True

    # Default to non-retryable for safety
    return False


def _handle_task_failure(task, exc: Exception, task_name: str, **context) -> None:
    """
    Handle task failure by logging and potentially sending to dead letter queue.

    Args:
        task: The Celery task instance
        exc: The exception that caused the failure
        task_name: Name of the failed task
        **context: Additional context for logging
    """
    logger.error(
        "Task failed after all retries",
        task_name=task_name,
        error=str(exc),
        task_id=task.request.id,
        retries=task.request.retries,
        **context,
    )

    # Could send to dead letter queue here
    # dlq_task_name = f"dlq_{task_name}"
    # celery_app.send_task(dlq_task_name, args=[context, str(exc)])
