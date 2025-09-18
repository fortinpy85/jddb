"""
Task management API endpoints for Celery-based background processing.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, List
from pathlib import Path
import tempfile

from ...database.connection import get_async_session
from ...tasks.processing_tasks import process_single_file_task, batch_process_files_task
from ...tasks.embedding_tasks import (
    generate_embeddings_for_job_task,
    batch_generate_embeddings_task,
    generate_missing_embeddings_task,
)
from ...tasks.celery_app import celery_app
from ...config import settings
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["tasks"])


@router.post("/upload")
async def upload_and_process_file(
    file: UploadFile = File(...),
    generate_embeddings: bool = True,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Upload a file and process it using Celery.

    Args:
        file: The uploaded file
        generate_embeddings: Whether to generate embeddings after processing

    Returns:
        Task information for tracking progress
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.supported_extensions_list:
            raise HTTPException(
                status_code=400, detail=f"Unsupported file extension: {file_ext}"
            )

        # Check file size
        if (
            hasattr(file, "size")
            and file.size > settings.max_file_size_mb * 1024 * 1024
        ):
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB",
            )

        # Save uploaded file temporarily
        upload_dir = settings.data_path / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        temp_file_path = upload_dir / file.filename

        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Submit to Celery
        task = process_single_file_task.delay(str(temp_file_path), generate_embeddings)

        logger.info(
            "File upload task submitted",
            filename=file.filename,
            task_id=task.id,
            temp_path=str(temp_file_path),
        )

        return {
            "status": "accepted",
            "task_id": task.id,
            "filename": file.filename,
            "message": "File upload task submitted. Use /tasks/{task_id}/status to track progress.",
        }

    except Exception as e:
        logger.error(
            "File upload submission failed", filename=file.filename, error=str(e)
        )
        raise HTTPException(
            status_code=500, detail=f"Upload submission failed: {str(e)}"
        )


@router.post("/batch-process")
async def batch_process_directory(
    directory_path: str,
    max_files: Optional[int] = None,
    recursive: bool = True,
    generate_embeddings: bool = True,
):
    """
    Start batch processing of files in a directory using Celery.

    Args:
        directory_path: Path to directory containing files
        max_files: Maximum number of files to process
        recursive: Whether to scan subdirectories
        generate_embeddings: Whether to generate embeddings after processing

    Returns:
        Task information for tracking progress
    """
    try:
        # Validate directory
        data_path = Path(directory_path)
        if not data_path.exists():
            raise HTTPException(status_code=400, detail="Directory does not exist")

        # Submit batch processing task to Celery
        task = batch_process_files_task.delay(
            directory_path, max_files, recursive, generate_embeddings
        )

        logger.info(
            "Batch processing task submitted",
            directory=directory_path,
            task_id=task.id,
            max_files=max_files,
        )

        return {
            "status": "accepted",
            "task_id": task.id,
            "directory": directory_path,
            "message": "Batch processing task submitted. Use /tasks/{task_id}/status to track progress.",
        }

    except Exception as e:
        logger.error(
            "Batch processing submission failed", directory=directory_path, error=str(e)
        )
        raise HTTPException(
            status_code=500, detail=f"Batch processing submission failed: {str(e)}"
        )


@router.post("/generate-embeddings")
async def generate_embeddings_for_job(job_id: int):
    """
    Generate embeddings for a specific job using Celery.

    Args:
        job_id: ID of the job to generate embeddings for

    Returns:
        Task information for tracking progress
    """
    try:
        # Submit embedding generation task to Celery
        task = generate_embeddings_for_job_task.delay(job_id)

        logger.info(
            "Embedding generation task submitted", job_id=job_id, task_id=task.id
        )

        return {
            "status": "accepted",
            "task_id": task.id,
            "job_id": job_id,
            "message": "Embedding generation task submitted. Use /tasks/{task_id}/status to track progress.",
        }

    except Exception as e:
        logger.error(
            "Embedding generation submission failed", job_id=job_id, error=str(e)
        )
        raise HTTPException(
            status_code=500, detail=f"Embedding generation submission failed: {str(e)}"
        )


@router.post("/batch-generate-embeddings")
async def batch_generate_embeddings(job_ids: List[int]):
    """
    Generate embeddings for multiple jobs using Celery.

    Args:
        job_ids: List of job IDs to generate embeddings for

    Returns:
        Task information for tracking progress
    """
    try:
        if not job_ids:
            raise HTTPException(status_code=400, detail="No job IDs provided")

        # Submit batch embedding generation task to Celery
        task = batch_generate_embeddings_task.delay(job_ids)

        logger.info(
            "Batch embedding generation task submitted",
            job_count=len(job_ids),
            task_id=task.id,
        )

        return {
            "status": "accepted",
            "task_id": task.id,
            "job_ids": job_ids,
            "message": "Batch embedding generation task submitted. Use /tasks/{task_id}/status to track progress.",
        }

    except Exception as e:
        logger.error("Batch embedding generation submission failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Batch embedding generation submission failed: {str(e)}",
        )


@router.post("/generate-missing-embeddings")
async def generate_missing_embeddings(limit: Optional[int] = None):
    """
    Generate embeddings for all chunks that don't have them using Celery.

    Args:
        limit: Maximum number of chunks to process

    Returns:
        Task information for tracking progress
    """
    try:
        # Submit missing embeddings generation task to Celery
        task = generate_missing_embeddings_task.delay(limit)

        logger.info(
            "Missing embeddings generation task submitted", limit=limit, task_id=task.id
        )

        return {
            "status": "accepted",
            "task_id": task.id,
            "limit": limit,
            "message": "Missing embeddings generation task submitted. Use /tasks/{task_id}/status to track progress.",
        }

    except Exception as e:
        logger.error("Missing embeddings generation submission failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Missing embeddings generation submission failed: {str(e)}",
        )


@router.get("/{task_id}/status")
async def get_task_status(task_id: str):
    """
    Get the status of a Celery task.

    Args:
        task_id: The task ID to check

    Returns:
        Task status information
    """
    try:
        # Get task result from Celery
        result = celery_app.AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "failed": result.failed() if result.ready() else None,
        }

        # Add result if task is completed
        if result.ready():
            if result.successful():
                response["result"] = result.result
            elif result.failed():
                response["error"] = str(result.info)
        else:
            # Add progress info if available
            if result.info and isinstance(result.info, dict):
                response["info"] = result.info

        return response

    except Exception as e:
        logger.error("Failed to get task status", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/{task_id}/result")
async def get_task_result(task_id: str):
    """
    Get the result of a completed Celery task.

    Args:
        task_id: The task ID to get result for

    Returns:
        Task result
    """
    try:
        # Get task result from Celery
        result = celery_app.AsyncResult(task_id)

        if not result.ready():
            raise HTTPException(status_code=202, detail="Task not yet completed")

        if result.failed():
            raise HTTPException(
                status_code=500, detail=f"Task failed: {str(result.info)}"
            )

        return {"task_id": task_id, "status": result.status, "result": result.result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get task result", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get task result: {str(e)}"
        )


@router.delete("/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancel a running Celery task.

    Args:
        task_id: The task ID to cancel

    Returns:
        Cancellation status
    """
    try:
        # Revoke task in Celery
        celery_app.control.revoke(task_id, terminate=True)

        logger.info("Task cancelled", task_id=task_id)

        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task cancellation requested",
        }

    except Exception as e:
        logger.error("Failed to cancel task", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.get("/")
async def list_active_tasks():
    """
    List all active tasks in Celery.

    Returns:
        List of active tasks
    """
    try:
        # Get active tasks from Celery
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()

        if not active_tasks:
            return {"active_tasks": [], "total_active": 0}

        # Flatten and format task info
        all_tasks = []
        for worker, tasks in active_tasks.items():
            for task in tasks:
                all_tasks.append(
                    {
                        "task_id": task["id"],
                        "task_name": task["name"],
                        "worker": worker,
                        "args": task["args"],
                        "kwargs": task["kwargs"],
                    }
                )

        return {
            "active_tasks": all_tasks,
            "total_active": len(all_tasks),
            "workers": list(active_tasks.keys()),
        }

    except Exception as e:
        logger.error("Failed to list active tasks", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to list active tasks: {str(e)}"
        )


@router.get("/stats")
async def get_task_stats():
    """
    Get Celery task statistics.

    Returns:
        Task statistics
    """
    try:
        inspect = celery_app.control.inspect()

        # Get various task stats
        active_tasks = inspect.active() or {}
        scheduled_tasks = inspect.scheduled() or {}
        reserved_tasks = inspect.reserved() or {}
        registered_tasks = inspect.registered() or {}

        # Count tasks
        total_active = sum(len(tasks) for tasks in active_tasks.values())
        total_scheduled = sum(len(tasks) for tasks in scheduled_tasks.values())
        total_reserved = sum(len(tasks) for tasks in reserved_tasks.values())

        # Get worker info
        workers = list(active_tasks.keys()) if active_tasks else []

        return {
            "workers": {"total": len(workers), "active_workers": workers},
            "tasks": {
                "active": total_active,
                "scheduled": total_scheduled,
                "reserved": total_reserved,
            },
            "registered_tasks": (
                list(registered_tasks.values())[0] if registered_tasks else []
            ),
            "queues": ["processing", "embeddings"],  # Our configured queues
        }

    except Exception as e:
        logger.error("Failed to get task stats", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get task stats: {str(e)}"
        )
