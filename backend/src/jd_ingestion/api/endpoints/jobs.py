# Standard library imports
import csv
import io
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from ...database.connection import get_async_session
from ...database.models import (
    AIUsageTracking,
    ContentChunk,
    DataQualityMetrics,
    JobDescription,
    JobMetadata,
    JobSection,
    UsageAnalytics,
)
from ...utils.error_handler import handle_errors, retry_on_failure
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
@handle_errors(
    operation_name="list_jobs", context={"endpoint": "/jobs/", "method": "GET"}
)
@retry_on_failure(max_retries=2, base_delay=0.5)
async def list_jobs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    page: Optional[int] = Query(None, ge=1, description="Page number (1-based)"),
    size: Optional[int] = Query(None, ge=1, le=1000, description="Page size"),
    search: Optional[str] = Query(None, description="Search in job title and content"),
    classification: Optional[str] = Query(
        None, description="Filter by classification (e.g., EX-01)"
    ),
    language: Optional[str] = Query(None, description="Filter by language (en/fr)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    db: AsyncSession = Depends(get_async_session),
):
    """List job descriptions with optional filters."""
    # Handle page/size parameters vs skip/limit
    if page is not None and size is not None:
        # Convert page-based to offset-based
        skip = (page - 1) * size
        limit = size
    elif page is not None or size is not None:
        raise HTTPException(
            status_code=400,
            detail="Both 'page' and 'size' parameters must be provided together",
        )

    # Build base query
    base_query = select(JobDescription)

    # Apply filters
    if search:
        base_query = base_query.where(
            JobDescription.title.ilike(f"%{search}%")
            | JobDescription.raw_content.ilike(f"%{search}%")
        )
    if classification:
        base_query = base_query.where(JobDescription.classification == classification)
    if language:
        base_query = base_query.where(JobDescription.language == language)
    if department:
        base_query = base_query.join(JobDescription.job_metadata).where(
            JobMetadata.department.ilike(f"%{department}%")
        )

    # Get total count and paginated results in a single query if possible, or two efficient queries
    # For simplicity and broad compatibility, we'll stick to two queries, but ensure they are efficient.

    # Count query
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total_count = total_result.scalar_one()

    # Data query with pagination
    data_query = base_query.offset(skip).limit(limit)
    result = await db.execute(data_query)
    jobs = result.scalars().all()

    # Build pagination response
    if page is not None and size is not None:
        # Page-based pagination response
        pages = (total_count + size - 1) // size  # Calculate total pages
        pagination_info = {
            "page": page,
            "size": size,
            "total": total_count,
            "pages": pages,
            "has_more": page < pages,
        }
    else:
        # Offset-based pagination response
        pagination_info = {
            "skip": skip,
            "limit": limit,
            "total": total_count,
            "has_more": skip + limit < total_count,
        }

    return {
        "jobs": [
            {
                "id": job.id,
                "job_number": job.job_number,
                "title": job.title,
                "classification": job.classification,
                "language": job.language,
                "processed_date": (
                    job.processed_date.isoformat() if job.processed_date else None
                ),
                "file_path": job.file_path,
            }
            for job in jobs
        ],
        "pagination": pagination_info,
    }


@router.get("/status")
@handle_errors(
    operation_name="get_processing_status",
    context={"endpoint": "/jobs/status", "method": "GET"},
)
@retry_on_failure(max_retries=2, base_delay=0.5)
async def get_processing_status(db: AsyncSession = Depends(get_async_session)):
    """Get current processing status of all jobs."""
    # Get total job count
    total_result = await db.execute(select(func.count()).select_from(JobDescription))
    total_jobs = total_result.scalar_one()

    # Get jobs by classification
    classification_result = await db.execute(
        select(JobDescription.classification, func.count()).group_by(
            JobDescription.classification
        )
    )
    by_classification = {row[0]: row[1] for row in classification_result.fetchall()}

    # Get jobs by language
    language_result = await db.execute(
        select(JobDescription.language, func.count()).group_by(JobDescription.language)
    )
    by_language = {row[0]: row[1] for row in language_result.fetchall()}

    # Get last updated time
    last_updated_result = await db.execute(select(func.max(JobDescription.updated_at)))
    last_updated = last_updated_result.scalar_one_or_none()

    return {
        "total_jobs": total_jobs,
        "by_classification": by_classification,
        "by_language": by_language,
        "processing_status": {
            "pending": 0,
            "processing": 0,
            "completed": total_jobs,
            "needs_review": 0,
            "failed": 0,
        },
        "last_updated": last_updated.isoformat() if last_updated else None,
    }


@router.get("/stats")
@handle_errors(
    operation_name="get_job_stats", context={"endpoint": "/jobs/stats", "method": "GET"}
)
@retry_on_failure(max_retries=2, base_delay=0.5)
async def get_job_stats(db: AsyncSession = Depends(get_async_session)):
    """Get basic job statistics."""
    try:
        # Total jobs count
        total_jobs_result = await db.execute(select(func.count(JobDescription.id)))
        total_jobs = total_jobs_result.scalar_one()

        # Classification distribution
        classification_result = await db.execute(
            select(
                JobDescription.classification, func.count(JobDescription.id)
            ).group_by(JobDescription.classification)
        )
        classification_distribution = {
            row[0]: row[1] for row in classification_result.fetchall()
        }

        # Language distribution
        language_result = await db.execute(
            select(JobDescription.language, func.count(JobDescription.id)).group_by(
                JobDescription.language
            )
        )
        language_distribution = {row[0]: row[1] for row in language_result.fetchall()}

        return {
            "total_jobs": total_jobs,
            "classification_distribution": classification_distribution,
            "language_distribution": language_distribution,
        }

    except Exception as e:
        logger.error("Failed to get job statistics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.get("/stats/comprehensive")
@handle_errors(
    operation_name="get_comprehensive_stats",
    context={"endpoint": "/jobs/stats/comprehensive", "method": "GET"},
)
@retry_on_failure(max_retries=2, base_delay=0.5)
async def get_comprehensive_stats(db: AsyncSession = Depends(get_async_session)):
    """Get comprehensive ingestion and processing statistics."""
    try:
        # Basic job statistics
        total_jobs_result = await db.execute(
            select(func.count()).select_from(JobDescription)
        )
        total_jobs = total_jobs_result.scalar_one()

        # Jobs with embeddings
        jobs_with_embeddings_result = await db.execute(
            select(func.count(func.distinct(ContentChunk.job_id)))
            .select_from(ContentChunk)
            .where(ContentChunk.embedding.isnot(None))
        )
        jobs_with_embeddings = jobs_with_embeddings_result.scalar_one()

        # Total content chunks and embeddings
        total_chunks_result = await db.execute(
            select(func.count()).select_from(ContentChunk)
        )
        total_chunks = total_chunks_result.scalar_one()

        embeddings_count_result = await db.execute(
            select(func.count())
            .select_from(ContentChunk)
            .where(ContentChunk.embedding.isnot(None))
        )
        embeddings_count = embeddings_count_result.scalar_one()

        # Data quality statistics
        quality_stats_result = await db.execute(
            select(
                func.avg(DataQualityMetrics.content_completeness_score),
                func.avg(DataQualityMetrics.sections_completeness_score),
                func.avg(DataQualityMetrics.metadata_completeness_score),
                func.count(),
                func.sum(DataQualityMetrics.processing_errors_count),
                func.sum(DataQualityMetrics.validation_errors_count),
            ).select_from(DataQualityMetrics)
        )
        quality_stats = quality_stats_result.fetchone()

        # AI usage statistics (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)

        ai_stats_result = await db.execute(
            select(
                func.count(),
                func.sum(AIUsageTracking.total_tokens),
                func.sum(AIUsageTracking.cost_usd),
                func.count().filter(AIUsageTracking.success == "success"),
                func.count().filter(AIUsageTracking.success != "success"),
            )
            .select_from(AIUsageTracking)
            .where(AIUsageTracking.request_timestamp >= thirty_days_ago)
        )
        ai_stats = ai_stats_result.fetchone()

        # Department distribution
        dept_stats_result = await db.execute(
            select(JobMetadata.department, func.count())
            .select_from(JobMetadata)
            .where(JobMetadata.department.isnot(None))
            .group_by(JobMetadata.department)
            .order_by(func.count().desc())
            .limit(10)
        )
        dept_distribution = {row[0]: row[1] for row in dept_stats_result.fetchall()}

        # Recent activity (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_uploads_result = await db.execute(
            select(func.count())
            .select_from(JobDescription)
            .where(JobDescription.created_at >= seven_days_ago)
        )
        recent_uploads = recent_uploads_result.scalar_one()

        # Processing performance
        avg_processing_time_result = await db.execute(
            select(func.avg(UsageAnalytics.processing_time_ms))
            .select_from(UsageAnalytics)
            .where(
                UsageAnalytics.action_type == "upload",
                UsageAnalytics.processing_time_ms.isnot(None),
                UsageAnalytics.timestamp >= thirty_days_ago,
            )
        )
        avg_processing_time = avg_processing_time_result.scalar_one()

        # Section completeness
        sections_stats_result = await db.execute(
            select(JobSection.section_type, func.count())
            .select_from(JobSection)
            .group_by(JobSection.section_type)
            .order_by(func.count().desc())
        )
        sections_distribution = {
            row[0]: row[1] for row in sections_stats_result.fetchall()
        }

        # Build comprehensive response
        return {
            "summary": {
                "total_jobs": total_jobs,
                "jobs_with_embeddings": jobs_with_embeddings,
                "total_content_chunks": total_chunks,
                "total_embeddings": embeddings_count,
                "recent_uploads_7d": recent_uploads,
                "embedding_coverage_percent": round(
                    (embeddings_count / max(total_chunks, 1)) * 100, 1
                ),
            },
            "quality_metrics": {
                "avg_content_completeness": float(quality_stats[0] or 0),
                "avg_sections_completeness": float(quality_stats[1] or 0),
                "avg_metadata_completeness": float(quality_stats[2] or 0),
                "jobs_with_quality_data": quality_stats[3] or 0,
                "total_processing_errors": quality_stats[4] or 0,
                "total_validation_errors": quality_stats[5] or 0,
                "quality_coverage_percent": round(
                    (quality_stats[3] or 0) / max(total_jobs, 1) * 100, 1
                ),
            },
            "ai_usage_30d": {
                "total_requests": ai_stats[0] or 0,
                "total_tokens": ai_stats[1] or 0,
                "total_cost_usd": float(ai_stats[2] or 0),
                "successful_requests": ai_stats[3] or 0,
                "failed_requests": ai_stats[4] or 0,
                "success_rate_percent": round(
                    (ai_stats[3] or 0) / max(ai_stats[0] or 1, 1) * 100, 1
                ),
            },
            "content_distribution": {
                "by_department": dept_distribution,
                "by_section_type": sections_distribution,
            },
            "performance": {
                "avg_processing_time_ms": float(avg_processing_time or 0),
                "processing_health": (
                    "good" if (avg_processing_time or 0) < 30000 else "slow"
                ),
            },
        }

    except Exception as e:
        logger.error("Failed to get comprehensive statistics", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve comprehensive statistics"
        )


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    include_content: bool = Query(False, description="Include full raw content"),
    include_sections: bool = Query(True, description="Include parsed sections"),
    include_metadata: bool = Query(True, description="Include job metadata"),
    db: AsyncSession = Depends(get_async_session),
):
    """Get detailed information about a specific job description."""
    try:
        # Get job description
        query = select(JobDescription).where(JobDescription.id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job description not found")

        response = {
            "id": job.id,
            "job_number": job.job_number,
            "title": job.title,
            "classification": job.classification,
            "language": job.language,
            "file_path": job.file_path,
            "file_hash": job.file_hash,
            "processed_date": (
                job.processed_date.isoformat() if job.processed_date else None
            ),
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        }

        # Include raw content if requested
        if include_content:
            response["raw_content"] = job.raw_content

        # Include sections if requested
        if include_sections:
            sections_query = (
                select(JobSection)
                .where(JobSection.job_id == job_id)
                .order_by(JobSection.section_order)
            )
            sections_result = await db.execute(sections_query)
            sections = sections_result.scalars().all()

            response["sections"] = [
                {
                    "id": section.id,
                    "section_type": section.section_type,
                    "section_content": section.section_content,
                    "section_order": section.section_order,
                }
                for section in sections
            ]

        # Include metadata if requested
        if include_metadata:
            metadata_query = select(JobMetadata).where(JobMetadata.job_id == job_id)
            metadata_result = await db.execute(metadata_query)
            metadata = metadata_result.scalar_one_or_none()

            if metadata:
                response["job_metadata"] = {
                    "reports_to": metadata.reports_to,
                    "department": metadata.department,
                    "location": metadata.location,
                    "fte_count": metadata.fte_count,
                    "salary_budget": (
                        float(metadata.salary_budget)
                        if metadata.salary_budget
                        else None
                    ),
                    "effective_date": (
                        metadata.effective_date.isoformat()
                        if metadata.effective_date
                        else None
                    ),
                }
            else:
                response["job_metadata"] = None

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve job details")


@router.get("/{job_id}/sections/{section_type}")
async def get_job_section(
    job_id: int, section_type: str, db: AsyncSession = Depends(get_async_session)
):
    """Get a specific section of a job description."""
    try:
        # Verify job exists
        job_query = select(JobDescription).where(JobDescription.id == job_id)
        job_result = await db.execute(job_query)
        job = job_result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job description not found")

        # Get section
        section_query = select(JobSection).where(
            JobSection.job_id == job_id, JobSection.section_type == section_type
        )
        section_result = await db.execute(section_query)
        section = section_result.scalar_one_or_none()

        if not section:
            raise HTTPException(
                status_code=404,
                detail=f"Section '{section_type}' not found for job {job_id}",
            )

        return {
            "job_id": job_id,
            "section_id": section.id,
            "section_type": section.section_type,
            "section_content": section.section_content,
            "section_order": section.section_order,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get job section",
            job_id=job_id,
            section_type=section_type,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve section")


@router.delete("/{job_id}")
async def delete_job(job_id: int, db: AsyncSession = Depends(get_async_session)):
    """Delete a job description and all related data."""
    try:
        # Get job to verify it exists
        query = select(JobDescription).where(JobDescription.id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job description not found")

        # Delete job (cascade will handle related records)
        await db.delete(job)
        await db.commit()

        logger.info("Job description deleted", job_id=job_id, job_number=job.job_number)

        return {
            "status": "success",
            "message": f"Job description {job.job_number} deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete job", job_id=job_id, error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete job description")


@router.post("/export/bulk")
async def bulk_export_jobs(
    export_request: Dict[str, Any], db: AsyncSession = Depends(get_async_session)
):
    """
    Export multiple jobs in various formats.

    Request body:
    {
        "job_ids": [1, 2, 3] (optional - if not provided, exports all jobs)
        "format": "txt|json|csv" (default: txt)
        "include_sections": true|false (default: true)
        "include_metadata": true|false (default: true)
        "include_content": true|false (default: false)
        "filters": {
            "classification": ["EX-01"],
            "language": ["en"],
            "department": ["IT"]
        }
    }
    """
    # Imports moved to top of file

    try:
        # Parse request parameters
        job_ids = export_request.get("job_ids", [])
        export_format = export_request.get("format", "txt")
        include_sections = export_request.get("include_sections", True)
        include_metadata = export_request.get("include_metadata", True)
        include_content = export_request.get("include_content", False)
        filters = export_request.get("filters", {})

        # Build query based on job_ids or filters
        query = select(JobDescription)

        if job_ids:
            query = query.where(JobDescription.id.in_(job_ids))
        else:
            # Apply filters if no specific job_ids provided
            if filters.get("classification"):
                query = query.where(
                    JobDescription.classification.in_(filters["classification"])
                )
            if filters.get("language"):
                query = query.where(JobDescription.language.in_(filters["language"]))
            if filters.get("department") and include_metadata:
                query = query.join(JobDescription.job_metadata).where(
                    JobMetadata.department.in_(filters["department"])
                )

        result = await db.execute(query)
        jobs = result.scalars().all()

        if not jobs:
            raise HTTPException(status_code=404, detail="No jobs found for export")

        # Fetch additional data if requested
        jobs_data = []
        for job in jobs:
            job_data = {
                "id": job.id,
                "job_number": job.job_number,
                "title": job.title,
                "classification": job.classification,
                "language": job.language,
                "file_path": job.file_path,
                "processed_date": job.processed_date,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
            }

            if include_content:
                job_data["raw_content"] = job.raw_content

            if include_sections:
                sections_result = await db.execute(
                    select(JobSection)
                    .where(JobSection.job_id == job.id)
                    .order_by(JobSection.section_order)
                )
                sections = sections_result.scalars().all()
                job_data["sections"] = [
                    {
                        "section_type": s.section_type,
                        "section_content": s.section_content,
                        "section_order": s.section_order,
                    }
                    for s in sections
                ]

            if include_metadata:
                metadata_result = await db.execute(
                    select(JobMetadata).where(JobMetadata.job_id == job.id)
                )
                metadata = metadata_result.scalar_one_or_none()
                if metadata:
                    job_data["metadata"] = {
                        "department": metadata.department,
                        "reports_to": metadata.reports_to,
                        "location": metadata.location,
                        "fte_count": metadata.fte_count,
                        "salary_budget": metadata.salary_budget,
                    }

            jobs_data.append(job_data)

        # Generate export based on format
        if export_format == "json":
            output = json.dumps(jobs_data, indent=2, default=str)
            content_type = "application/json"
            filename = f"jobs_export_{len(jobs_data)}_jobs.json"

        elif export_format == "csv":
            output = io.StringIO()
            if jobs_data:
                # Flatten the data for CSV
                flattened_data = []
                for job in jobs_data:
                    row = {
                        "id": job["id"],
                        "job_number": job["job_number"],
                        "title": job["title"],
                        "classification": job["classification"],
                        "language": job["language"],
                        "file_path": job["file_path"],
                        "processed_date": job["processed_date"],
                        "created_at": job["created_at"],
                        "updated_at": job["updated_at"],
                    }

                    if include_metadata and "metadata" in job and job["metadata"]:
                        metadata = job["metadata"]
                        row.update(
                            {
                                "department": metadata.get("department"),
                                "reports_to": metadata.get("reports_to"),
                                "location": metadata.get("location"),
                                "fte_count": metadata.get("fte_count"),
                                "salary_budget": metadata.get("salary_budget"),
                            }
                        )

                    if include_sections and "sections" in job:
                        # Add section content as separate columns
                        sections_dict = {
                            s["section_type"]: s["section_content"]
                            for s in job["sections"]
                        }
                        row.update(sections_dict)

                    if include_content:
                        row["raw_content"] = job.get("raw_content", "")

                    flattened_data.append(row)

                writer = csv.DictWriter(output, fieldnames=flattened_data[0].keys())
                writer.writeheader()
                writer.writerows(flattened_data)

            output_str = output.getvalue()
            output.close()
            content_type = "text/csv"
            filename = f"jobs_export_{len(jobs_data)}_jobs.csv"

        else:  # Default to txt format
            output_lines = []
            output_lines.append(f"BULK JOB EXPORT - {len(jobs_data)} Jobs")
            output_lines.append("=" * 50)
            output_lines.append("")

            for i, job in enumerate(jobs_data, 1):
                output_lines.append(f"JOB {i}: {job['title']} ({job['job_number']})")
                output_lines.append("-" * 50)
                output_lines.append(f"ID: {job['id']}")
                output_lines.append(f"Classification: {job['classification']}")
                output_lines.append(f"Language: {job['language']}")
                output_lines.append(f"Processed: {job['processed_date']}")

                if include_metadata and "metadata" in job and job["metadata"]:
                    metadata = job["metadata"]
                    output_lines.append("")
                    output_lines.append("METADATA:")
                    for key, value in metadata.items():
                        if value:
                            output_lines.append(
                                f"  {key.replace('_', ' ').title()}: {value}"
                            )

                if include_sections and "sections" in job:
                    output_lines.append("")
                    output_lines.append("SECTIONS:")
                    for section in job["sections"]:
                        output_lines.append(
                            f"  {section['section_type'].replace('_', ' ').title()}:"
                        )
                        output_lines.append(
                            f"    {section['section_content'][:200]}..."
                        )

                if include_content:
                    output_lines.append("")
                    output_lines.append("CONTENT:")
                    output_lines.append(job.get("raw_content", "")[:500] + "...")

                output_lines.append("")
                output_lines.append("")

            output_str = "\n".join(output_lines)
            content_type = "text/plain"
            filename = f"jobs_export_{len(jobs_data)}_jobs.txt"

        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(output_str.encode("utf-8")),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        logger.error("Bulk export failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/export/formats")
async def get_export_formats():
    """Get available export formats and options."""
    return {
        "formats": {
            "txt": {
                "name": "Plain Text",
                "description": "Human-readable text format",
                "content_type": "text/plain",
                "extension": "txt",
            },
            "json": {
                "name": "JSON",
                "description": "Structured JSON data",
                "content_type": "application/json",
                "extension": "json",
            },
            "csv": {
                "name": "CSV",
                "description": "Comma-separated values for spreadsheets",
                "content_type": "text/csv",
                "extension": "csv",
            },
        },
        "options": {
            "include_sections": {
                "name": "Include Sections",
                "description": "Include parsed job sections (accountability, structure, etc.)",
                "default": True,
            },
            "include_metadata": {
                "name": "Include Metadata",
                "description": "Include structured metadata (department, reports_to, etc.)",
                "default": True,
            },
            "include_content": {
                "name": "Include Raw Content",
                "description": "Include full raw content (warning: large files)",
                "default": False,
            },
        },
    }
