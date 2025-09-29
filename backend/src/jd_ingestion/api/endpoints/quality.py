"""
API endpoints for data quality metrics and validation.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ...database.connection import get_async_session
from ...services.quality_service import quality_service
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["quality"])


class QualityMetricsRequest(BaseModel):
    """Request model for calculating quality metrics."""

    job_ids: Optional[List[int]] = None
    recalculate: bool = False


class QualityReportRequest(BaseModel):
    """Request model for quality reports."""

    job_id: Optional[int] = None
    include_details: bool = True


@router.post("/metrics/calculate")
async def calculate_quality_metrics(
    request: QualityMetricsRequest, db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Calculate data quality metrics for jobs.

    Args:
        request: Calculation request parameters
        db: Database session

    Returns:
        Calculation results and statistics
    """
    try:
        logger.info("Starting quality metrics calculation", job_ids=request.job_ids)

        result = await quality_service.batch_calculate_quality_metrics(
            db=db, job_ids=request.job_ids
        )

        logger.info(
            "Quality metrics calculation completed",
            successful=result["successful"],
            failed=result["failed"],
        )

        return {
            "status": "completed",
            "message": f"Calculated metrics for {result['successful']} jobs",
            "results": result,
        }

    except Exception as e:
        logger.error("Quality metrics calculation failed", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate quality metrics: {str(e)}"
        )


@router.get("/metrics/{job_id}")
async def get_job_quality_metrics(
    job_id: int, db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get quality metrics for a specific job.

    Args:
        job_id: ID of the job
        db: Database session

    Returns:
        Quality metrics for the job
    """
    try:
        logger.info("Retrieving quality metrics for job", job_id=job_id)

        metrics = await quality_service.calculate_quality_metrics_for_job(db, job_id)

        return {"job_id": job_id, "metrics": metrics, "status": "success"}

    except ValueError as e:
        logger.warning("Job not found for quality metrics", job_id=job_id)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to retrieve quality metrics", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve quality metrics: {str(e)}"
        )


@router.post("/report")
async def generate_quality_report(
    request: QualityReportRequest, db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Generate a comprehensive quality report.

    Args:
        request: Report request parameters
        db: Database session

    Returns:
        Quality report data
    """
    try:
        logger.info("Generating quality report", job_id=request.job_id)

        report = await quality_service.get_quality_report(db=db, job_id=request.job_id)

        return {"status": "success", "report": report}

    except ValueError as e:
        logger.warning("Invalid request for quality report", error=str(e))
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to generate quality report", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to generate quality report: {str(e)}"
        )


@router.get("/overview")
async def get_quality_overview(
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get system-wide quality overview.

    Args:
        db: Database session

    Returns:
        System quality overview
    """
    try:
        logger.info("Generating system quality overview")

        overview = await quality_service.get_quality_report(db=db, job_id=None)

        return {"status": "success", "overview": overview}

    except Exception as e:
        logger.error("Failed to generate quality overview", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to generate quality overview: {str(e)}"
        )


@router.get("/validation/{job_id}")
async def validate_job_content(
    job_id: int, db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Perform detailed content validation for a specific job.

    Args:
        job_id: ID of the job to validate
        db: Database session

    Returns:
        Detailed validation results
    """
    try:
        logger.info("Performing content validation for job", job_id=job_id)

        # Calculate fresh metrics which includes validation
        metrics = await quality_service.calculate_quality_metrics_for_job(db, job_id)

        return {
            "job_id": job_id,
            "validation_status": "completed",
            "validation_results": metrics.get("validation_results", {}),
            "quality_flags": metrics.get("quality_flags", {}),
            "overall_score": metrics.get("content_completeness_score", 0),
            "recommendations": metrics.get("quality_flags", {}).get(
                "recommendations", []
            ),
        }

    except ValueError as e:
        logger.warning("Job not found for validation", job_id=job_id)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Content validation failed", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Content validation failed: {str(e)}"
        )


@router.get("/stats/distribution")
async def get_quality_distribution(
    metric: str = Query(
        "content_completeness_score", description="Metric to analyze distribution"
    ),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get quality metrics distribution statistics.

    Args:
        metric: The metric to analyze distribution for
        db: Database session

    Returns:
        Distribution statistics
    """
    try:
        logger.info("Generating quality distribution statistics", metric=metric)

        # Get system overview which includes distribution data
        overview = await quality_service.get_quality_report(db=db, job_id=None)

        return {
            "status": "success",
            "metric": metric,
            "distribution": overview.get("quality_distribution", []),
            "overview": overview.get("overview", {}),
        }

    except Exception as e:
        logger.error(
            "Failed to generate quality distribution", metric=metric, error=str(e)
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to generate quality distribution: {str(e)}"
        )


@router.post("/batch/validate")
async def batch_validate_jobs(
    job_ids: Optional[List[int]] = None, db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Perform batch validation of multiple jobs.

    Args:
        job_ids: Optional list of specific job IDs to validate
        db: Database session

    Returns:
        Batch validation results
    """
    try:
        logger.info(
            "Starting batch job validation",
            job_count=len(job_ids) if job_ids else "all",
        )

        # Use the batch calculation which includes validation
        result = await quality_service.batch_calculate_quality_metrics(
            db=db, job_ids=job_ids
        )

        return {
            "status": "completed",
            "validation_summary": {
                "total_jobs": result["total_jobs"],
                "successful_validations": result["successful"],
                "failed_validations": result["failed"],
                "errors": result["errors"],
            },
        }

    except Exception as e:
        logger.error("Batch validation failed", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Batch validation failed: {str(e)}"
        )


@router.get("/recommendations/{job_id}")
async def get_quality_recommendations(
    job_id: int, db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get quality improvement recommendations for a specific job.

    Args:
        job_id: ID of the job
        db: Database session

    Returns:
        Quality improvement recommendations
    """
    try:
        logger.info("Generating quality recommendations for job", job_id=job_id)

        # Get current metrics
        metrics = await quality_service.calculate_quality_metrics_for_job(db, job_id)
        quality_flags = metrics.get("quality_flags", {})

        return {
            "job_id": job_id,
            "high_quality": quality_flags.get("high_quality", False),
            "needs_review": quality_flags.get("needs_review", False),
            "processing_issues": quality_flags.get("processing_issues", False),
            "content_issues": quality_flags.get("content_issues", False),
            "recommendations": quality_flags.get("recommendations", []),
            "priority": (
                "high"
                if quality_flags.get("processing_issues")
                else "medium"
                if quality_flags.get("content_issues")
                else "low"
            ),
        }

    except ValueError as e:
        logger.warning("Job not found for recommendations", job_id=job_id)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to generate recommendations", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to generate recommendations: {str(e)}"
        )
