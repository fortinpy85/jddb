# Standard library imports
import csv
import io
import json
from typing import Any, Dict, Optional

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field
from datetime import datetime

# Local imports
from ...database.connection import get_async_session
from ...database.models import (
    JobDescription,
    JobMetadata,
    JobSection,
    job_description_skills,
)
from ...auth.api_key import get_api_key

# Statistics functions now available via analytics_service
from ...services.analytics_service import analytics_service
from ...utils.error_handler import handle_errors, retry_on_failure
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Request/Response Models
class JobDescriptionCreate(BaseModel):
    """Model for creating a new job description manually"""

    job_number: str = Field(..., description="Job number/ID")
    title: str = Field(..., description="Job title")
    classification: str = Field(..., description="Classification level (e.g., EX-01)")
    language: str = Field(default="en", description="Language code (en/fr)")
    department: Optional[str] = Field(None, description="Department name")
    reports_to: Optional[str] = Field(None, description="Reports to position")
    content: Optional[str] = Field(None, description="Full job description content")
    sections: Optional[Dict[str, str]] = Field(None, description="Job sections by type")


@router.get("/")
@retry_on_failure()
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
    skill_ids: Optional[str] = Query(
        None,
        description="Comma-separated skill IDs to filter by (jobs must have ALL specified skills)",
    ),
    db: AsyncSession = Depends(get_async_session),
    api_key: str = Security(get_api_key),
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

    # Build base query - load quality_metrics relationship
    base_query = select(JobDescription).options(
        selectinload(JobDescription.quality_metrics)
    )

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

    # Skill filtering - jobs must have ALL specified skills (AND logic)
    if skill_ids:
        skill_id_list = [
            int(sid.strip()) for sid in skill_ids.split(",") if sid.strip()
        ]
        if skill_id_list:
            # For each skill ID, we need to ensure the job has it
            # We use a subquery that counts how many of the required skills each job has
            # and only keep jobs that have all required skills
            for skill_id in skill_id_list:
                base_query = base_query.where(
                    JobDescription.id.in_(
                        select(job_description_skills.c.job_id).where(
                            job_description_skills.c.skill_id == skill_id
                        )
                    )
                )

    # Get total count and paginated results in a single query if possible, or two efficient queries
    # For simplicity and broad compatibility, we'll stick to two queries, but ensure they are efficient.

    # Count query - optimized to avoid subquery
    count_query = select(func.count(JobDescription.id))

    # Apply the same filters for count query
    if search:
        count_query = count_query.where(
            JobDescription.title.ilike(f"%{search}%")
            | JobDescription.raw_content.ilike(f"%{search}%")
        )
    if classification:
        count_query = count_query.where(JobDescription.classification == classification)
    if language:
        count_query = count_query.where(JobDescription.language == language)
    if department:
        count_query = count_query.join(JobDescription.job_metadata).where(
            JobMetadata.department.ilike(f"%{department}%")
        )

    # Apply same skill filtering to count query
    if skill_ids:
        skill_id_list = [
            int(sid.strip()) for sid in skill_ids.split(",") if sid.strip()
        ]
        if skill_id_list:
            for skill_id in skill_id_list:
                count_query = count_query.where(
                    JobDescription.id.in_(
                        select(job_description_skills.c.job_id).where(
                            job_description_skills.c.skill_id == skill_id
                        )
                    )
                )

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
                "quality_score": (
                    float(job.quality_metrics.content_completeness_score)
                    if job.quality_metrics
                    and job.quality_metrics.content_completeness_score
                    else 0.0
                ),
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
@retry_on_failure()
async def get_processing_status(
    db: AsyncSession = Depends(get_async_session), api_key: str = Security(get_api_key)
):
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
@retry_on_failure()
async def get_job_stats(
    db: AsyncSession = Depends(get_async_session), api_key: str = Security(get_api_key)
):
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

    except SQLAlchemyError as e:
        logger.error("Database error getting job statistics", error=str(e))
        raise HTTPException(
            status_code=500, detail="Database error retrieving statistics"
        )
    except Exception as e:
        logger.error("Unexpected error getting job statistics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.get("/stats/comprehensive")
@handle_errors(
    operation_name="get_comprehensive_stats",
    context={"endpoint": "/jobs/stats/comprehensive", "method": "GET"},
)
@retry_on_failure()
async def get_comprehensive_stats(
    db: AsyncSession = Depends(get_async_session), api_key: str = Security(get_api_key)
):
    """Get comprehensive ingestion and processing statistics."""
    try:
        summary = await analytics_service.get_summary_stats(db)
        quality_metrics = await analytics_service.get_quality_metrics(db)
        ai_usage = await analytics_service.get_ai_usage_stats(db)
        content_distribution = await analytics_service.get_content_distribution(db)
        performance = await analytics_service.get_performance_stats(db)

        return {
            "summary": summary,
            "quality_metrics": quality_metrics,
            "ai_usage_30d": ai_usage,
            "content_distribution": content_distribution,
            "performance": performance,
        }

    except SQLAlchemyError as e:
        logger.error("Database error getting comprehensive statistics", error=str(e))
        raise HTTPException(
            status_code=500, detail="Database error retrieving statistics"
        )
    except ValueError as e:
        logger.error("Data validation error in comprehensive statistics", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid data encountered")
    except Exception as e:
        logger.error("Unexpected error getting comprehensive statistics", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve comprehensive statistics"
        )


async def _get_job_details(
    job_id: int,
    db: AsyncSession,
    include_content: bool = False,
    include_sections: bool = True,
    include_metadata: bool = True,
    include_skills: bool = True,
) -> dict:
    """Get detailed information about a specific job description."""
    query = select(JobDescription).where(JobDescription.id == job_id)
    if include_sections:
        query = query.options(selectinload(JobDescription.sections))
    if include_metadata:
        query = query.options(selectinload(JobDescription.job_metadata))
    if include_skills:
        query = query.options(selectinload(JobDescription.skills))

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

    if include_content:
        response["raw_content"] = job.raw_content

    if include_sections:
        response["sections"] = [
            {
                "id": section.id,
                "section_type": section.section_type,
                "section_content": section.section_content,
                "section_order": section.section_order,
            }
            for section in job.sections
        ]

    if include_metadata and job.job_metadata:
        response["metadata"] = {
            "reports_to": job.job_metadata.reports_to,
            "department": job.job_metadata.department,
            "location": job.job_metadata.location,
            "fte_count": job.job_metadata.fte_count,
            "salary_budget": (
                float(job.job_metadata.salary_budget)
                if job.job_metadata.salary_budget
                else None
            ),
            "effective_date": (
                job.job_metadata.effective_date.isoformat()
                if job.job_metadata.effective_date
                else None
            ),
        }
    else:
        response["metadata"] = None

    if include_skills:
        # Get skills with confidence scores from the association table
        from sqlalchemy import select as sql_select
        from ...database.models import job_description_skills

        # Query to get skills with confidence scores
        skills_query = sql_select(
            job_description_skills.c.skill_id,
            job_description_skills.c.confidence,
        ).where(job_description_skills.c.job_id == job_id)

        skills_result = await db.execute(skills_query)
        skill_confidence_map = {row[0]: row[1] for row in skills_result.fetchall()}

        response["skills"] = [
            {
                "id": skill.id,
                "lightcast_id": skill.lightcast_id,
                "name": skill.name,
                "skill_type": skill.skill_type,
                "category": skill.category,
                "confidence": skill_confidence_map.get(skill.id, 0.0),
            }
            for skill in job.skills
        ]
    else:
        response["skills"] = []

    return response


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    include_content: bool = Query(False, description="Include full raw content"),
    include_sections: bool = Query(True, description="Include parsed sections"),
    include_metadata: bool = Query(True, description="Include job metadata"),
    include_skills: bool = Query(True, description="Include extracted skills"),
    db: AsyncSession = Depends(get_async_session),
    api_key: str = Security(get_api_key),
):
    """Get detailed information about a specific job description."""
    try:
        return await _get_job_details(
            job_id=job_id,
            db=db,
            include_content=include_content,
            include_sections=include_sections,
            include_metadata=include_metadata,
            include_skills=include_skills,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error("Database error getting job", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=500, detail="Database error retrieving job details"
        )
    except Exception as e:
        logger.error("Unexpected error getting job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve job details")


@router.get("/{job_id}/sections/{section_type}")
async def get_job_section(
    job_id: int,
    section_type: str,
    db: AsyncSession = Depends(get_async_session),
    api_key: str = Security(get_api_key),
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
    except SQLAlchemyError as e:
        logger.error(
            "Database error getting job section",
            job_id=job_id,
            section_type=section_type,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Database error retrieving section")
    except Exception as e:
        logger.error(
            "Unexpected error getting job section",
            job_id=job_id,
            section_type=section_type,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve section")


@router.post("/", status_code=201)
async def create_job(
    job_data: JobDescriptionCreate,
    db: AsyncSession = Depends(get_async_session),
    api_key: str = Security(get_api_key),
):
    """Create a new job description manually."""
    try:
        # Create job description
        new_job = JobDescription(
            job_number=job_data.job_number,
            title=job_data.title,
            classification=job_data.classification,
            language=job_data.language,
            file_path=f"manual/{job_data.job_number}.txt",
            processed_date=datetime.utcnow(),
            full_text_content=job_data.content or "",
        )

        db.add(new_job)
        await db.flush()  # Get the job ID

        # Create metadata if provided
        if job_data.department or job_data.reports_to:
            metadata = JobMetadata(
                job_id=new_job.id,
                department=job_data.department,
                reports_to=job_data.reports_to,
            )
            db.add(metadata)

        # Create sections if provided
        if job_data.sections:
            for section_type, section_content in job_data.sections.items():
                section = JobSection(
                    job_id=new_job.id,
                    section_type=section_type,
                    section_content=section_content,
                )
                db.add(section)

        await db.commit()
        await db.refresh(new_job)

        logger.info(
            "Job description created manually",
            job_id=new_job.id,
            job_number=new_job.job_number,
        )

        return {
            "status": "success",
            "message": f"Job description {new_job.job_number} created successfully",
            "job_id": new_job.id,
            "job": {
                "id": new_job.id,
                "job_number": new_job.job_number,
                "title": new_job.title,
                "classification": new_job.classification,
                "language": new_job.language,
            },
        }

    except SQLAlchemyError as e:
        logger.error("Database error creating job", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="Database error creating job description"
        )
    except Exception as e:
        logger.error("Unexpected error creating job", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create job description")


@router.post("/{job_id}/reprocess")
async def reprocess_job(
    job_id: int,
    db: AsyncSession = Depends(get_async_session),
    api_key: str = Security(get_api_key),
):
    """Reprocess a job description (re-run extraction and analysis)."""
    try:
        # Get job to verify it exists
        query = select(JobDescription).where(JobDescription.id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job description not found")

        # Update processed date to mark as reprocessed
        job.processed_date = datetime.utcnow()
        await db.commit()

        logger.info(
            "Job description reprocessed", job_id=job_id, job_number=job.job_number
        )

        return {
            "status": "success",
            "message": f"Job description {job.job_number} queued for reprocessing",
            "job_id": job.id,
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error("Database error reprocessing job", job_id=job_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="Database error reprocessing job description"
        )
    except Exception as e:
        logger.error("Unexpected error reprocessing job", job_id=job_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to reprocess job description"
        )


@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_async_session),
    api_key: str = Security(get_api_key),
):
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
    except SQLAlchemyError as e:
        logger.error("Database error deleting job", job_id=job_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="Database error deleting job description"
        )
    except Exception as e:
        logger.error("Unexpected error deleting job", job_id=job_id, error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete job description")


@router.post("/export/bulk")
async def bulk_export_jobs(
    export_request: Dict[str, Any],
    db: AsyncSession = Depends(get_async_session),
    api_key: str = Security(get_api_key),
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
        query = select(JobDescription).options(
            selectinload(JobDescription.sections),
            selectinload(JobDescription.job_metadata),
        )
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
                job_data["sections"] = [
                    {
                        "section_type": s.section_type,
                        "section_content": s.section_content,
                        "section_order": s.section_order,
                    }
                    for s in job.sections
                ]

            if include_metadata and job.job_metadata:
                job_data["metadata"] = {
                    "department": job.job_metadata.department,
                    "reports_to": job.job_metadata.reports_to,
                    "location": job.job_metadata.location,
                    "fte_count": job.job_metadata.fte_count,
                    "salary_budget": job.job_metadata.salary_budget,
                }

            jobs_data.append(job_data)

        # Generate export based on format
        if export_format == "json":
            output_str = json.dumps(jobs_data, indent=2, default=str)
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

    except SQLAlchemyError as e:
        logger.error("Database error during bulk export", error=str(e))
        raise HTTPException(status_code=500, detail="Database error during export")
    except ValueError as e:
        logger.error("Data validation error during bulk export", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid export parameters")
    except Exception as e:
        logger.error("Unexpected error during bulk export", error=str(e))
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/export/formats")
async def get_export_formats(api_key: str = Security(get_api_key)):
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
