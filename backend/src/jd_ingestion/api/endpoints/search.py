# Standard library imports
import time
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from ...database.connection import get_async_session
from ...database.models import (
    ContentChunk,
    JobDescription,
    JobMetadata,
    JobSection,
    SearchAnalytics,
)
from ...services.embedding_service import embedding_service, optimized_embedding_service
from ...services.search_analytics_service import search_analytics_service
from ...services.search_recommendations_service import search_recommendations_service
from ...utils.cache import cache_service
from ...utils.error_handler import handle_errors, retry_on_failure
from ...utils.logging import PerformanceTimer, get_logger, log_performance_metric

logger = get_logger(__name__)
router = APIRouter()


class SearchQuery(BaseModel):
    """Enhanced search query parameters with date range and salary filters."""

    query: str
    classification: Optional[str] = None
    language: Optional[str] = None
    department: Optional[str] = None
    section_types: Optional[List[str]] = None
    limit: int = 20
    use_semantic_search: bool = True

    # Date range filters
    effective_date_from: Optional[date] = Field(
        None, description="Filter jobs effective from this date"
    )
    effective_date_to: Optional[date] = Field(
        None, description="Filter jobs effective to this date"
    )

    # Salary band filters
    salary_min: Optional[Decimal] = Field(
        None, description="Minimum salary budget filter", ge=0
    )
    salary_max: Optional[Decimal] = Field(
        None, description="Maximum salary budget filter", ge=0
    )

    # Location and FTE filters
    location: Optional[str] = Field(None, description="Filter by job location")
    min_fte: Optional[int] = Field(None, description="Minimum FTE count", ge=1)
    max_fte: Optional[int] = Field(None, description="Maximum FTE count", ge=1)


class SearchResult(BaseModel):
    """Search result item."""

    job_id: int
    job_number: str
    title: str
    classification: str
    language: str
    relevance_score: float
    matching_sections: List[Dict[str, Any]]
    snippet: str


@router.post("/")
@handle_errors(operation_name="search_jobs")
@retry_on_failure(max_retries=2, base_delay=1.0)
async def search_jobs(
    search_query: SearchQuery,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """Search job descriptions using semantic or full-text search."""
    start_time = time.time()
    search_id = None

    # Start search session for analytics
    search_id = await search_analytics_service.start_search_session(
        session_id=request.headers.get("x-session-id", "anonymous"),
        user_id=request.headers.get("x-user-id"),
        ip_address=request.client.host if request.client else None,
    )

    # Extract filters for analytics
    filters = {
        "classification": search_query.classification,
        "language": search_query.language,
        "department": search_query.department,
        "section_types": search_query.section_types,
        "limit": search_query.limit,
        "use_semantic_search": search_query.use_semantic_search,
    }

    embedding_time_ms = None

    # Try semantic search first if enabled and embeddings are available
    if search_query.use_semantic_search:
        logger.info("Attempting semantic search", query=search_query.query)
        semantic_results = await embedding_service.semantic_search(
            query=search_query.query,
            db=db,
            classification_filter=search_query.classification,
            language_filter=search_query.language,
            limit=search_query.limit,
        )

        # If we got good semantic results, use them
        if semantic_results:
            logger.info("Using semantic search results", count=len(semantic_results))
            detailed_results = []

            for result in semantic_results:
                # Get job details for snippet extraction
                job_query = select(JobDescription).where(
                    JobDescription.id == result["job_id"]
                )
                job_result = await db.execute(job_query)
                job = job_result.scalar_one()

                # Find matching sections
                matching_sections = await _get_matching_sections(
                    job_id=result["job_id"], search_query=search_query, db=db
                )

                detailed_results.append(
                    {
                        "job_id": result["job_id"],
                        "job_number": result["job_number"],
                        "title": result["title"],
                        "classification": result["classification"],
                        "language": result["language"],
                        "relevance_score": result["relevance_score"],
                        "matching_sections": matching_sections,
                        "snippet": _extract_snippet(
                            job.raw_content, search_query.query
                        ),
                    }
                )

            # Record analytics for successful semantic search
            execution_time_ms = int((time.time() - start_time) * 1000)
            await search_analytics_service.record_search(
                db=db,
                search_id=search_id,
                query_text=search_query.query,
                search_type="semantic",
                filters=filters,
                execution_time_ms=execution_time_ms,
                embedding_time_ms=embedding_time_ms,
                total_results=len(detailed_results),
                returned_results=len(detailed_results),
                session_id=request.headers.get("x-session-id", "anonymous"),
                user_id=request.headers.get("x-user-id"),
                ip_address=request.client.host if request.client else None,
            )

            return {
                "query": search_query.query,
                "search_type": "semantic",
                "total_results": len(detailed_results),
                "results": detailed_results,
            }

    # Fall back to full-text search
    logger.info("Using full-text search", query=search_query.query)
    fulltext_result = await _fulltext_search(search_query, db)

    # Record analytics for fulltext search
    execution_time_ms = int((time.time() - start_time) * 1000)
    await search_analytics_service.record_search(
        db=db,
        search_id=search_id,
        query_text=search_query.query,
        search_type="fulltext",
        filters=filters,
        execution_time_ms=execution_time_ms,
        total_results=fulltext_result.get("total_results", 0),
        returned_results=fulltext_result.get("total_results", 0),
        session_id=request.headers.get("x-session-id", "anonymous"),
        user_id=request.headers.get("x-user-id"),
        ip_address=request.client.host if request.client else None,
    )

    return fulltext_result


@router.post("/semantic")
@handle_errors(operation_name="semantic_search")
@retry_on_failure(max_retries=2, base_delay=1.0)
async def semantic_search(
    search_query: SearchQuery, db: AsyncSession = Depends(get_async_session)
):
    """Perform pure semantic search using vector embeddings."""
    semantic_results = await embedding_service.semantic_search(
        query=search_query.query,
        db=db,
        classification_filter=search_query.classification,
        language_filter=search_query.language,
        limit=search_query.limit,
    )

    if not semantic_results:
        return {
            "query": search_query.query,
            "search_type": "semantic",
            "total_results": 0,
            "results": [],
            "message": "No semantic matches found - try full-text search",
        }

    # Enhance results with detailed information
    detailed_results = []
    for result in semantic_results:
        job_query = select(JobDescription).where(JobDescription.id == result["job_id"])
        job_result = await db.execute(job_query)
        job = job_result.scalar_one()

        matching_sections = await _get_matching_sections(
            job_id=result["job_id"], search_query=search_query, db=db
        )

        detailed_results.append(
            {
                "job_id": result["job_id"],
                "job_number": result["job_number"],
                "title": result["title"],
                "classification": result["classification"],
                "language": result["language"],
                "relevance_score": result["relevance_score"],
                "matching_sections": matching_sections,
                "snippet": _extract_snippet(job.raw_content, search_query.query),
                "matching_chunks": result.get("matching_chunks", 0),
            }
        )

    return {
        "query": search_query.query,
        "search_type": "semantic",
        "total_results": len(detailed_results),
        "results": detailed_results,
    }


@router.post("/advanced")
@handle_errors(operation_name="advanced_search_with_filters")
@retry_on_failure(max_retries=2, base_delay=1.0)
async def advanced_search_with_filters(
    search_query: SearchQuery,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """Advanced search with date range, salary bands, and metadata filters."""
    try:
        with PerformanceTimer(
            "advanced_search",
            tags={
                "has_filters": bool(
                    search_query.salary_min or search_query.effective_date_from
                )
            },
        ):
            # Check cache for complex searches
            filters_dict = {
                "query": search_query.query,
                "classification": search_query.classification,
                "language": search_query.language,
                "department": search_query.department,
                "effective_date_from": (
                    search_query.effective_date_from.isoformat()
                    if search_query.effective_date_from
                    else None
                ),
                "effective_date_to": (
                    search_query.effective_date_to.isoformat()
                    if search_query.effective_date_to
                    else None
                ),
                "salary_min": (
                    float(search_query.salary_min) if search_query.salary_min else None
                ),
                "salary_max": (
                    float(search_query.salary_max) if search_query.salary_max else None
                ),
                "location": search_query.location,
                "min_fte": search_query.min_fte,
                "max_fte": search_query.max_fte,
                "limit": search_query.limit,
            }

            cached_results = await cache_service.get_cached_search_results(
                search_query.query, filters_dict
            )
            if cached_results:
                logger.debug("Cache hit for advanced search")
                log_performance_metric("advanced_search_cache_hit", 1, "count")
                return cached_results

            log_performance_metric("advanced_search_cache_miss", 1, "count")

            # Build the base query with metadata joins
            base_query = select(
                JobDescription.id,
                JobDescription.job_number,
                JobDescription.title,
                JobDescription.classification,
                JobDescription.language,
                JobDescription.status,
                JobDescription.created_at,
                JobMetadata.salary_budget,
                JobMetadata.effective_date,
                JobMetadata.department,
                JobMetadata.location,
                JobMetadata.fte_count,
            ).select_from(
                JobDescription.__table__.join(
                    JobMetadata.__table__,
                    JobDescription.id == JobMetadata.job_id,
                    isouter=True,
                )
            )

            # Apply filters
            where_clauses = [JobDescription.status == "processed"]

            if search_query.classification:
                where_clauses.append(
                    JobDescription.classification == search_query.classification
                )

            if search_query.language:
                where_clauses.append(JobDescription.language == search_query.language)

            # Date range filters
            if search_query.effective_date_from:
                where_clauses.append(
                    JobMetadata.effective_date >= search_query.effective_date_from
                )

            if search_query.effective_date_to:
                where_clauses.append(
                    JobMetadata.effective_date <= search_query.effective_date_to
                )

            # Salary band filters
            if search_query.salary_min:
                where_clauses.append(
                    JobMetadata.salary_budget >= search_query.salary_min
                )

            if search_query.salary_max:
                where_clauses.append(
                    JobMetadata.salary_budget <= search_query.salary_max
                )

            # Location filter
            if search_query.location:
                where_clauses.append(
                    JobMetadata.location.ilike(f"%{search_query.location}%")
                )

            # Department filter
            if search_query.department:
                where_clauses.append(
                    JobMetadata.department.ilike(f"%{search_query.department}%")
                )

            # FTE filters
            if search_query.min_fte:
                where_clauses.append(JobMetadata.fte_count >= search_query.min_fte)

            if search_query.max_fte:
                where_clauses.append(JobMetadata.fte_count <= search_query.max_fte)

            # Text search filter
            if search_query.query.strip():
                # Use full-text search on title and content
                text_search_clause = func.to_tsvector(
                    "english",
                    func.coalesce(JobDescription.title, "")
                    + " "
                    + func.coalesce(JobDescription.content, ""),
                ).match(func.plainto_tsquery("english", search_query.query))
                where_clauses.append(text_search_clause)

            # Apply all filters
            for clause in where_clauses:
                base_query = base_query.where(clause)

            # Add ordering by relevance and date
            if search_query.query.strip():
                base_query = base_query.order_by(
                    func.ts_rank(
                        func.to_tsvector(
                            "english",
                            func.coalesce(JobDescription.title, "")
                            + " "
                            + func.coalesce(JobDescription.content, ""),
                        ),
                        func.plainto_tsquery("english", search_query.query),
                    ).desc(),
                    JobDescription.created_at.desc(),
                )
            else:
                base_query = base_query.order_by(JobDescription.created_at.desc())

            # Apply limit
            base_query = base_query.limit(search_query.limit)

            # Execute query
            result = await db.execute(base_query)
            rows = result.fetchall()

            # Format results
            search_results = []
            for row in rows:
                search_results.append(
                    {
                        "job_id": row.id,
                        "job_number": row.job_number,
                        "title": row.title,
                        "classification": row.classification,
                        "language": row.language,
                        "status": row.status,
                        "created_at": (
                            row.created_at.isoformat() if row.created_at else None
                        ),
                        "salary_budget": (
                            float(row.salary_budget) if row.salary_budget else None
                        ),
                        "effective_date": (
                            row.effective_date.isoformat()
                            if row.effective_date
                            else None
                        ),
                        "department": row.department,
                        "location": row.location,
                        "fte_count": row.fte_count,
                    }
                )

            response = {
                "results": search_results,
                "total_found": len(search_results),
                "query": search_query.query,
                "filters_applied": {
                    "classification": search_query.classification,
                    "language": search_query.language,
                    "department": search_query.department,
                    "effective_date_from": (
                        search_query.effective_date_from.isoformat()
                        if search_query.effective_date_from
                        else None
                    ),
                    "effective_date_to": (
                        search_query.effective_date_to.isoformat()
                        if search_query.effective_date_to
                        else None
                    ),
                    "salary_min": (
                        float(search_query.salary_min)
                        if search_query.salary_min
                        else None
                    ),
                    "salary_max": (
                        float(search_query.salary_max)
                        if search_query.salary_max
                        else None
                    ),
                    "location": search_query.location,
                    "min_fte": search_query.min_fte,
                    "max_fte": search_query.max_fte,
                },
                "search_method": "advanced_filtered_search",
            }

            # Cache results for 30 minutes
            await cache_service.cache_search_results(
                search_query.query, filters_dict, response, 1800
            )

            # Log analytics
            await search_analytics_service.log_search(
                session_id=str(request.client.host),
                query=search_query.query,
                filters=filters_dict,
                result_count=len(search_results),
                db=db,
            )

            log_performance_metric("advanced_search_success", 1, "count")
            return response

    except Exception as e:
        logger.error("Advanced search failed", query=search_query.query, error=str(e))
        raise HTTPException(status_code=500, detail="Advanced search operation failed")


@router.get("/filters/stats")
@handle_errors(operation_name="get_filter_statistics")
async def get_filter_statistics(db: AsyncSession = Depends(get_async_session)):
    """Get statistics for filter options to help users understand data ranges."""
    try:
        with PerformanceTimer("filter_stats"):
            # Get salary range statistics
            salary_stats_query = select(
                func.min(JobMetadata.salary_budget).label("min_salary"),
                func.max(JobMetadata.salary_budget).label("max_salary"),
                func.avg(JobMetadata.salary_budget).label("avg_salary"),
                func.count(JobMetadata.salary_budget).label("salary_count"),
            ).where(JobMetadata.salary_budget.isnot(None))

            salary_result = await db.execute(salary_stats_query)
            salary_stats = salary_result.fetchone()

            # Get date range statistics
            date_stats_query = select(
                func.min(JobMetadata.effective_date).label("earliest_date"),
                func.max(JobMetadata.effective_date).label("latest_date"),
                func.count(JobMetadata.effective_date).label("date_count"),
            ).where(JobMetadata.effective_date.isnot(None))

            date_result = await db.execute(date_stats_query)
            date_stats = date_result.fetchone()

            # Get department and location counts
            dept_stats_query = (
                select(JobMetadata.department, func.count().label("count"))
                .where(JobMetadata.department.isnot(None))
                .group_by(JobMetadata.department)
                .order_by(func.count().desc())
                .limit(20)
            )

            dept_result = await db.execute(dept_stats_query)
            dept_stats = dept_result.fetchall()

            location_stats_query = (
                select(JobMetadata.location, func.count().label("count"))
                .where(JobMetadata.location.isnot(None))
                .group_by(JobMetadata.location)
                .order_by(func.count().desc())
                .limit(20)
            )

            location_result = await db.execute(location_stats_query)
            location_stats = location_result.fetchall()

            # Get FTE statistics
            fte_stats_query = select(
                func.min(JobMetadata.fte_count).label("min_fte"),
                func.max(JobMetadata.fte_count).label("max_fte"),
                func.avg(JobMetadata.fte_count).label("avg_fte"),
                func.count(JobMetadata.fte_count).label("fte_count"),
            ).where(JobMetadata.fte_count.isnot(None))

            fte_result = await db.execute(fte_stats_query)
            fte_stats = fte_result.fetchone()

            # Get classification and language counts
            classification_stats_query = (
                select(JobDescription.classification, func.count().label("count"))
                .where(
                    JobDescription.status == "processed",
                    JobDescription.classification.isnot(None),
                )
                .group_by(JobDescription.classification)
                .order_by(func.count().desc())
            )

            classification_result = await db.execute(classification_stats_query)
            classification_stats = classification_result.fetchall()

            language_stats_query = (
                select(JobDescription.language, func.count().label("count"))
                .where(
                    JobDescription.status == "processed",
                    JobDescription.language.isnot(None),
                )
                .group_by(JobDescription.language)
                .order_by(func.count().desc())
            )

            language_result = await db.execute(language_stats_query)
            language_stats = language_result.fetchall()

            response = {
                "salary_statistics": {
                    "min_salary": (
                        float(salary_stats.min_salary)
                        if salary_stats.min_salary
                        else None
                    ),
                    "max_salary": (
                        float(salary_stats.max_salary)
                        if salary_stats.max_salary
                        else None
                    ),
                    "avg_salary": (
                        float(salary_stats.avg_salary)
                        if salary_stats.avg_salary
                        else None
                    ),
                    "salary_count": salary_stats.salary_count,
                },
                "date_statistics": {
                    "earliest_date": (
                        date_stats.earliest_date.isoformat()
                        if date_stats.earliest_date
                        else None
                    ),
                    "latest_date": (
                        date_stats.latest_date.isoformat()
                        if date_stats.latest_date
                        else None
                    ),
                    "date_count": date_stats.date_count,
                },
                "fte_statistics": {
                    "min_fte": fte_stats.min_fte,
                    "max_fte": fte_stats.max_fte,
                    "avg_fte": float(fte_stats.avg_fte) if fte_stats.avg_fte else None,
                    "fte_count": fte_stats.fte_count,
                },
                "department_distribution": [
                    {"department": row.department, "count": row.count}
                    for row in dept_stats
                    if row.department
                ],
                "location_distribution": [
                    {"location": row.location, "count": row.count}
                    for row in location_stats
                    if row.location
                ],
                "classification_distribution": [
                    {"classification": row.classification, "count": row.count}
                    for row in classification_stats
                    if row.classification
                ],
                "language_distribution": [
                    {"language": row.language, "count": row.count}
                    for row in language_stats
                    if row.language
                ],
            }

            log_performance_metric("filter_stats_success", 1, "count")
            return response

    except Exception as e:
        logger.error("Filter statistics failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get filter statistics")


@router.get("/similar/{job_id}")
@handle_errors(operation_name="find_similar_jobs_optimized")
@retry_on_failure(max_retries=2, base_delay=1.0)
async def find_similar_jobs_optimized(
    job_id: int,
    limit: int = Query(10, ge=1, le=50, description="Number of similar jobs to return"),
    classification_filter: Optional[str] = Query(
        None, description="Filter by job classification"
    ),
    language_filter: Optional[str] = Query(
        None, description="Filter by language (EN/FR)"
    ),
    db: AsyncSession = Depends(get_async_session),
):
    """Find jobs similar to a given job description using optimized vector similarity."""
    try:
        with PerformanceTimer(
            "similar_jobs_search", tags={"job_id": job_id, "limit": limit}
        ):
            # Check cache first
            cached_results = await cache_service.get_cached_similar_jobs(job_id, limit)
            if cached_results:
                logger.debug("Cache hit for similar jobs", job_id=job_id)
                log_performance_metric("similar_jobs_cache_hit", 1, "count")
                return cached_results

            log_performance_metric("similar_jobs_cache_miss", 1, "count")

            # Get the source job
            source_query = select(JobDescription).where(JobDescription.id == job_id)
            source_result = await db.execute(source_query)
            source_job = source_result.scalar_one_or_none()

            if not source_job:
                raise HTTPException(status_code=404, detail="Job description not found")

            # Use optimized embedding service for vector similarity
            try:
                # Get representative chunks from the source job
                chunk_query = (
                    select(ContentChunk)
                    .where(
                        ContentChunk.job_id == job_id,
                        ContentChunk.embedding.isnot(None),
                    )
                    .limit(3)
                )  # Reduced for performance
                chunk_result = await db.execute(chunk_query)
                source_chunks = chunk_result.scalars().all()

                if source_chunks:
                    # Use batch similarity search for better performance
                    source_embeddings = [chunk.embedding for chunk in source_chunks]

                    batch_results = (
                        await optimized_embedding_service.batch_similarity_search(
                            query_embeddings=source_embeddings,
                            db=db,
                            limit_per_query=limit,
                            similarity_threshold=0.75,
                        )
                    )

                    # Aggregate results efficiently
                    job_similarities = {}
                    for results_batch in batch_results:
                        for chunk in results_batch:
                            job_id_key = chunk["job_id"]
                            if job_id_key == job_id:  # Skip self
                                continue

                            # Apply filters if specified
                            if (
                                classification_filter
                                and chunk.get("classification") != classification_filter
                            ):
                                continue
                            if (
                                language_filter
                                and chunk.get("language") != language_filter
                            ):
                                continue

                            if job_id_key not in job_similarities:
                                job_similarities[job_id_key] = {
                                    "job_id": chunk["job_id"],
                                    "job_number": chunk["job_number"],
                                    "title": chunk["title"],
                                    "classification": chunk["classification"],
                                    "language": chunk["language"],
                                    "similarity_scores": [],
                                    "matching_chunks": 0,
                                }
                            job_similarities[job_id_key]["similarity_scores"].append(
                                chunk["similarity_score"]
                            )
                            job_similarities[job_id_key]["matching_chunks"] += 1

                    if job_similarities:
                        # Calculate final similarity score (weighted average of top scores)
                        for job_data in job_similarities.values():
                            scores = sorted(job_data["similarity_scores"], reverse=True)
                            # Use weighted average of top 3 scores
                            top_scores = scores[:3]
                            if len(top_scores) >= 2:
                                job_data["similarity_score"] = (
                                    top_scores[0] * 0.5
                                    + top_scores[1] * 0.3
                                    + (
                                        top_scores[2]
                                        if len(top_scores) > 2
                                        else top_scores[1]
                                    )
                                    * 0.2
                                )
                            else:
                                job_data["similarity_score"] = top_scores[0]
                            # Remove intermediate data
                            del job_data["similarity_scores"]

                        # Sort by similarity score and take top results
                        similar_jobs = sorted(
                            job_similarities.values(),
                            key=lambda x: x["similarity_score"],
                            reverse=True,
                        )[:limit]

                        result = {
                            "source_job": {
                                "id": source_job.id,
                                "job_number": source_job.job_number,
                                "title": source_job.title,
                                "classification": source_job.classification,
                            },
                            "similar_jobs": [
                                {
                                    "id": job["job_id"],
                                    "job_number": job["job_number"],
                                    "title": job["title"],
                                    "classification": job["classification"],
                                    "language": job["language"],
                                    "similarity_score": job["similarity_score"],
                                    "matching_chunks": job["matching_chunks"],
                                }
                                for job in similar_jobs
                            ],
                            "total_found": len(similar_jobs),
                            "search_method": "optimized_vector_similarity",
                            "filters_applied": {
                                "classification": classification_filter,
                                "language": language_filter,
                            },
                        }

                        # Cache the results
                        await cache_service.cache_similar_jobs(job_id, limit, result)
                        log_performance_metric(
                            "similar_jobs_vector_success", 1, "count"
                        )
                        return result

            except Exception as vector_error:
                logger.warning(
                    "Vector similarity failed, falling back to text similarity",
                    error=str(vector_error),
                )

        # Fall back to title-based text similarity
        similar_query = (
            select(
                JobDescription.id,
                JobDescription.job_number,
                JobDescription.title,
                JobDescription.classification,
                JobDescription.language,
                func.ts_rank(
                    func.to_tsvector("english", JobDescription.title),
                    func.plainto_tsquery("english", source_job.title),
                ).label("rank"),
            )
            .where(JobDescription.id != job_id)
            .order_by(text("rank DESC"))
            .limit(limit)
        )

        similar_result = await db.execute(similar_query)
        similar_jobs = similar_result.fetchall()

        return {
            "source_job": {
                "id": source_job.id,
                "job_number": source_job.job_number,
                "title": source_job.title,
                "classification": source_job.classification,
            },
            "similar_jobs": [
                {
                    "id": job.id,
                    "job_number": job.job_number,
                    "title": job.title,
                    "classification": job.classification,
                    "language": job.language,
                    "similarity_score": float(job.rank),
                }
                for job in similar_jobs
            ],
            "total_found": len(similar_jobs),
            "search_method": "text_similarity",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Similar jobs search failed", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to find similar jobs")


@router.get("/compare/{job1_id}/{job2_id}")
@handle_errors(operation_name="compare_jobs")
async def compare_jobs(
    job1_id: int, job2_id: int, db: AsyncSession = Depends(get_async_session)
):
    """Compare two job descriptions with detailed similarity analysis."""
    try:
        # Get both jobs
        jobs_query = select(JobDescription).where(
            JobDescription.id.in_([job1_id, job2_id])
        )
        jobs_result = await db.execute(jobs_query)
        jobs = {job.id: job for job in jobs_result.scalars().all()}

        if job1_id not in jobs or job2_id not in jobs:
            raise HTTPException(
                status_code=404, detail="One or both job descriptions not found"
            )

        job1, job2 = jobs[job1_id], jobs[job2_id]

        # Get sections for both jobs
        sections_query = select(JobSection).where(
            JobSection.job_id.in_([job1_id, job2_id])
        )
        sections_result = await db.execute(sections_query)
        sections_by_job = {}
        for section in sections_result.scalars().all():
            if section.job_id not in sections_by_job:
                sections_by_job[section.job_id] = {}
            sections_by_job[section.job_id][
                section.section_type
            ] = section.section_content

        # Get content chunks with embeddings for similarity analysis
        chunks_query = select(ContentChunk).where(
            ContentChunk.job_id.in_([job1_id, job2_id]),
            ContentChunk.embedding.isnot(None),
        )
        chunks_result = await db.execute(chunks_query)
        chunks_by_job = {}
        for chunk in chunks_result.scalars().all():
            if chunk.job_id not in chunks_by_job:
                chunks_by_job[chunk.job_id] = []
            chunks_by_job[chunk.job_id].append(chunk)

        # Calculate overall similarity using chunk embeddings
        overall_similarity = 0.0
        section_similarities = {}

        if job1_id in chunks_by_job and job2_id in chunks_by_job:
            job1_chunks = chunks_by_job[job1_id]
            job2_chunks = chunks_by_job[job2_id]

            # Calculate pairwise similarities between all chunks
            similarities = []
            for chunk1 in job1_chunks:
                for chunk2 in job2_chunks:
                    similar_chunks = await embedding_service.find_similar_chunks(
                        query_embedding=chunk1.embedding,
                        db=db,
                        job_id_exclude=job1_id,
                        limit=1,
                        similarity_threshold=0.0,
                    )
                    for similar_chunk in similar_chunks:
                        if similar_chunk["job_id"] == job2_id:
                            similarities.append(similar_chunk["similarity_score"])
                            break

            if similarities:
                # Use the average of the top 50% similarities for overall score
                similarities.sort(reverse=True)
                top_half = similarities[: max(1, len(similarities) // 2)]
                overall_similarity = sum(top_half) / len(top_half)

        # Analyze section-by-section differences
        all_section_types = set()
        if job1_id in sections_by_job:
            all_section_types.update(sections_by_job[job1_id].keys())
        if job2_id in sections_by_job:
            all_section_types.update(sections_by_job[job2_id].keys())

        section_comparison = []
        for section_type in all_section_types:
            job1_content = sections_by_job.get(job1_id, {}).get(section_type, "")
            job2_content = sections_by_job.get(job2_id, {}).get(section_type, "")

            # Simple text-based similarity for sections
            if job1_content and job2_content:
                common_words = set(job1_content.lower().split()) & set(
                    job2_content.lower()
                )
                total_words = set(job1_content.lower().split()) | set(
                    job2_content.lower()
                )
                text_similarity = (
                    len(common_words) / len(total_words) if total_words else 0
                )
            else:
                text_similarity = 0.0

            section_comparison.append(
                {
                    "section_type": section_type,
                    "job1_content": (
                        job1_content[:200] + "..."
                        if len(job1_content) > 200
                        else job1_content
                    ),
                    "job2_content": (
                        job2_content[:200] + "..."
                        if len(job2_content) > 200
                        else job2_content
                    ),
                    "similarity_score": text_similarity,
                    "both_present": bool(job1_content and job2_content),
                    "job1_only": bool(job1_content and not job2_content),
                    "job2_only": bool(job2_content and not job1_content),
                }
            )

        # Basic job metadata comparison
        metadata_comparison = {
            "classification": {
                "job1": job1.classification,
                "job2": job2.classification,
                "match": job1.classification == job2.classification,
            },
            "language": {
                "job1": job1.language,
                "job2": job2.language,
                "match": job1.language == job2.language,
            },
            "title_similarity": _calculate_title_similarity(job1.title, job2.title),
        }

        return {
            "comparison_id": f"{job1_id}_{job2_id}",
            "jobs": {
                "job1": {
                    "id": job1.id,
                    "job_number": job1.job_number,
                    "title": job1.title,
                    "classification": job1.classification,
                    "language": job1.language,
                },
                "job2": {
                    "id": job2.id,
                    "job_number": job2.job_number,
                    "title": job2.title,
                    "classification": job2.classification,
                    "language": job2.language,
                },
            },
            "similarity_analysis": {
                "overall_similarity": round(overall_similarity, 3),
                "similarity_level": _get_similarity_level(overall_similarity),
                "metadata_comparison": metadata_comparison,
                "section_comparison": section_comparison,
            },
            "recommendations": _generate_comparison_recommendations(
                overall_similarity, metadata_comparison, section_comparison
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Job comparison failed", job1_id=job1_id, job2_id=job2_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to compare jobs")


def _calculate_title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity between two job titles."""
    if not title1 or not title2:
        return 0.0

    words1 = set(title1.lower().split())
    words2 = set(title2.lower().split())

    common = words1 & words2
    total = words1 | words2

    return len(common) / len(total) if total else 0.0


def _get_similarity_level(similarity: float) -> str:
    """Get human-readable similarity level."""
    if similarity >= 0.85:
        return "Very High"
    elif similarity >= 0.7:
        return "High"
    elif similarity >= 0.5:
        return "Moderate"
    elif similarity >= 0.3:
        return "Low"
    else:
        return "Very Low"


def _generate_comparison_recommendations(
    overall_similarity: float, metadata_comparison: Dict, section_comparison: List
) -> List[str]:
    """Generate recommendations based on comparison results."""
    recommendations = []

    if overall_similarity >= 0.8:
        recommendations.append(
            "These jobs are very similar and likely have significant overlap in responsibilities."
        )
    elif overall_similarity >= 0.6:
        recommendations.append(
            "These jobs have good similarity and may share common skill requirements."
        )
    elif overall_similarity < 0.3:
        recommendations.append(
            "These jobs are quite different and likely require distinct skill sets."
        )

    if not metadata_comparison["classification"]["match"]:
        recommendations.append(
            f"Different classifications ({metadata_comparison['classification']['job1']} vs {metadata_comparison['classification']['job2']}) may indicate different organizational levels."
        )

    missing_sections_job1 = [s for s in section_comparison if s["job2_only"]]
    missing_sections_job2 = [s for s in section_comparison if s["job1_only"]]

    if missing_sections_job1:
        recommendations.append(
            f"Job 1 is missing sections present in Job 2: {', '.join([s['section_type'] for s in missing_sections_job1])}"
        )

    if missing_sections_job2:
        recommendations.append(
            f"Job 2 is missing sections present in Job 1: {', '.join([s['section_type'] for s in missing_sections_job2])}"
        )

    return recommendations


@router.get("/facets")
@handle_errors(operation_name="get_search_facets")
async def get_search_facets(db: AsyncSession = Depends(get_async_session)):
    """Get available facets for search filtering."""
    try:
        # Get unique classifications
        classification_query = (
            select(JobDescription.classification, func.count().label("count"))
            .group_by(JobDescription.classification)
            .order_by(JobDescription.classification)
        )

        classification_result = await db.execute(classification_query)
        classifications = [
            {"value": row.classification, "count": row.count}
            for row in classification_result.fetchall()
        ]

        # Get unique languages
        language_query = (
            select(JobDescription.language, func.count().label("count"))
            .group_by(JobDescription.language)
            .order_by(JobDescription.language)
        )

        language_result = await db.execute(language_query)
        languages = [
            {"value": row.language, "count": row.count}
            for row in language_result.fetchall()
        ]

        # Get unique section types
        section_query = (
            select(JobSection.section_type, func.count().label("count"))
            .group_by(JobSection.section_type)
            .order_by(JobSection.section_type)
        )

        section_result = await db.execute(section_query)
        section_types = [
            {"value": row.section_type, "count": row.count}
            for row in section_result.fetchall()
        ]

        # Check embedding availability
        embedding_query = select(func.count(ContentChunk.id)).where(
            ContentChunk.embedding.isnot(None)
        )
        embedding_result = await db.execute(embedding_query)
        embedding_count = embedding_result.scalar()

        return {
            "classifications": classifications,
            "languages": languages,
            "section_types": section_types,
            "embedding_stats": {
                "chunks_with_embeddings": embedding_count,
                "semantic_search_available": embedding_count > 0,
            },
        }

    except Exception as e:
        logger.error("Failed to get search facets", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve search facets")


async def _fulltext_search(
    search_query: SearchQuery, db: AsyncSession
) -> Dict[str, Any]:
    """Perform traditional full-text search."""
    # Build base query with text search
    base_query = select(
        JobDescription.id,
        JobDescription.job_number,
        JobDescription.title,
        JobDescription.classification,
        JobDescription.language,
        func.ts_rank(
            func.to_tsvector("english", JobDescription.raw_content),
            func.plainto_tsquery("english", search_query.query),
        ).label("rank"),
    ).where(
        func.to_tsvector("english", JobDescription.raw_content).op("@@")(
            func.plainto_tsquery("english", search_query.query)
        )
    )

    # Apply filters
    if search_query.classification:
        base_query = base_query.where(
            JobDescription.classification == search_query.classification
        )
    if search_query.language:
        base_query = base_query.where(JobDescription.language == search_query.language)

    # Order by relevance and limit results
    base_query = base_query.order_by(text("rank DESC")).limit(search_query.limit)

    # Execute search
    result = await db.execute(base_query)
    search_results = result.fetchall()

    # Get detailed information for each result
    detailed_results = []
    for row in search_results:
        # Get job details
        job_query = select(JobDescription).where(JobDescription.id == row.id)
        job_result = await db.execute(job_query)
        job = job_result.scalar_one()

        # Find matching sections
        matching_sections = await _get_matching_sections(
            job_id=row.id, search_query=search_query, db=db
        )

        # Create search result
        detailed_results.append(
            {
                "job_id": row.id,
                "job_number": row.job_number,
                "title": row.title,
                "classification": row.classification,
                "language": row.language,
                "relevance_score": float(row.rank),
                "matching_sections": matching_sections,
                "snippet": _extract_snippet(job.raw_content, search_query.query),
            }
        )

    return {
        "query": search_query.query,
        "search_type": "fulltext",
        "total_results": len(detailed_results),
        "results": detailed_results,
    }


async def _get_matching_sections(
    job_id: int, search_query: SearchQuery, db: AsyncSession
) -> List[Dict[str, Any]]:
    """Get sections that match the search query."""
    matching_sections = []

    if search_query.section_types:
        sections_query = select(JobSection).where(
            JobSection.job_id == job_id,
            JobSection.section_type.in_(search_query.section_types),
        )
    else:
        sections_query = select(JobSection).where(JobSection.job_id == job_id)

    sections_result = await db.execute(sections_query)
    sections = sections_result.scalars().all()

    for section in sections:
        # Simple keyword matching for sections
        if any(
            word.lower() in section.section_content.lower()
            for word in search_query.query.split()
        ):
            matching_sections.append(
                {
                    "section_type": section.section_type,
                    "section_id": section.id,
                    "snippet": _extract_snippet(
                        section.section_content, search_query.query
                    ),
                }
            )

    return matching_sections


def _extract_snippet(content: str, query: str, max_length: int = 200) -> str:
    """Extract a relevant snippet from content based on search query."""
    if not content or not query:
        return content[:max_length] + "..." if len(content) > max_length else content

    # Find the first occurrence of any query term
    query_terms = query.lower().split()
    content_lower = content.lower()

    best_position = len(content)
    for term in query_terms:
        position = content_lower.find(term)
        if position != -1 and position < best_position:
            best_position = position

    if best_position == len(content):
        # No terms found, return beginning
        return content[:max_length] + "..." if len(content) > max_length else content

    # Extract snippet around the found term
    start = max(0, best_position - max_length // 3)
    end = min(len(content), start + max_length)

    snippet = content[start:end]

    # Add ellipsis if truncated
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."

    return snippet


# ================================
# SEARCH RECOMMENDATIONS ENDPOINTS
# ================================


@router.get("/suggestions")
@handle_errors(operation_name="get_query_suggestions")
async def get_query_suggestions(
    q: str = Query(..., min_length=3, description="Partial query text for suggestions"),
    user_id: Optional[str] = Query(
        None, description="User ID for personalized suggestions"
    ),
    session_id: Optional[str] = Query(
        None, description="Session ID for context-aware suggestions"
    ),
    limit: int = Query(5, ge=1, le=10, description="Maximum number of suggestions"),
    db: AsyncSession = Depends(get_async_session),
) -> List[Dict[str, Any]]:
    """
    Get ML-powered query suggestions based on partial input.

    Provides intelligent query completion using:
    - Historical search patterns
    - Semantic similarity analysis
    - User behavior analytics
    - Content-based filtering
    """
    try:
        # Fixed: Added operation_name parameter
        with PerformanceTimer("query_suggestions") as timer:
            suggestions = await search_recommendations_service.get_query_suggestions(
                db=db,
                partial_query=q,
                user_id=user_id,
                session_id=session_id,
                limit=limit,
            )

        logger.info(
            "Query suggestions generated",
            query=q,
            count=len(suggestions),
        )

        return suggestions

    except Exception as e:
        logger.error("Error generating query suggestions", query=q, error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to generate query suggestions"
        )


@router.get("/recommendations")
@handle_errors(operation_name="get_search_recommendations")
async def get_search_recommendations(
    query: Optional[str] = Query(None, description="Current search query for context"),
    classification: Optional[str] = Query(None, description="Classification filter"),
    user_id: Optional[str] = Query(
        None, description="User ID for personalized recommendations"
    ),
    limit: int = Query(
        8, ge=1, le=20, description="Maximum recommendations per category"
    ),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get comprehensive search recommendations including related searches,
    trending queries, and personalized suggestions.
    """
    try:
        with PerformanceTimer("search_recommendations") as timer:
            search_context = {"query": query or "", "classification": classification}

            recommendations = (
                await search_recommendations_service.get_search_recommendations(
                    db=db, search_context=search_context, user_id=user_id, limit=limit
                )
            )

        # Add metadata
        recommendations["metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "context": search_context,
            "total_recommendations": sum(
                len(v) for v in recommendations.values() if isinstance(v, list)
            ),
            "generation_time_ms": 0,
        }

        logger.info(
            "Search recommendations generated",
            context=search_context,
            user_id=user_id,
            total=recommendations["metadata"]["total_recommendations"],
        )

        return recommendations

    except Exception as e:
        logger.error("Error generating search recommendations", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to generate search recommendations"
        )


@router.get("/trending")
@handle_errors(operation_name="get_trending_searches")
async def get_trending_searches(
    period: str = Query(
        "24h", pattern="^(1h|6h|24h|7d)$", description="Time period for trends"
    ),
    limit: int = Query(
        10, ge=1, le=20, description="Maximum number of trending queries"
    ),
    db: AsyncSession = Depends(get_async_session),
) -> List[Dict[str, Any]]:
    """
    Get trending search queries for a specified time period.
    """
    try:
        with PerformanceTimer("trending_searches") as timer:
            # Map period to timedelta
            period_map = {
                "1h": timedelta(hours=1),
                "6h": timedelta(hours=6),
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
            }

            time_filter = datetime.now() - period_map[period]

            # Get trending queries from analytics
            query = (
                select(
                    SearchAnalytics.query_text,
                    func.count().label("search_count"),
                    func.avg(SearchAnalytics.total_results).label("avg_results"),
                    func.count(func.distinct(SearchAnalytics.session_id)).label(
                        "unique_sessions"
                    ),
                )
                .where(
                    and_(
                        SearchAnalytics.timestamp >= time_filter,
                        SearchAnalytics.total_results > 0,
                        func.length(SearchAnalytics.query_text) >= 3,
                    )
                )
                .group_by(SearchAnalytics.query_text)
                .order_by(desc("search_count"))
                .limit(limit)
            )

            result = await db.execute(query)
            rows = result.fetchall()

            trending = []
            for row in rows:
                trending.append(
                    {
                        "query": row.query_text,
                        "search_count": row.search_count,
                        "avg_results": float(row.avg_results or 0),
                        "unique_sessions": row.unique_sessions,
                        "trend_score": float(
                            row.search_count * row.unique_sessions
                        ),  # Simple trend scoring
                    }
                )

        logger.info(
            "Trending searches retrieved",
            period=period,
            count=len(trending),
        )

        return trending

    except Exception as e:
        logger.error("Error getting trending searches", period=period, error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve trending searches"
        )


@router.get("/popular-filters")
@handle_errors(operation_name="get_popular_filters")
async def get_popular_filters(
    query: Optional[str] = Query(
        None, description="Query context for filter suggestions"
    ),
    limit: int = Query(
        10, ge=1, le=20, description="Maximum number of filter suggestions"
    ),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get popular filter suggestions based on query context and general usage patterns.
    """
    try:
        with PerformanceTimer("popular_filters") as timer:
            filters = {
                "classifications": [],
                "departments": [],
                "languages": [],
                "date_ranges": [],
            }

            # Get popular classifications
            class_query = (
                select(JobDescription.classification, func.count().label("count"))
                .group_by(JobDescription.classification)
                .order_by(desc("count"))
                .limit(limit)
            )

            class_result = await db.execute(class_query)
            for row in class_result.fetchall():
                if row.classification:
                    filters["classifications"].append(
                        {
                            "value": row.classification,
                            "count": row.count,
                            "label": f"Classification: {row.classification}",
                        }
                    )

            # Get popular departments
            dept_query = (
                select(JobMetadata.department, func.count().label("count"))
                .where(JobMetadata.department.isnot(None))
                .group_by(JobMetadata.department)
                .order_by(desc("count"))
                .limit(limit)
            )

            dept_result = await db.execute(dept_query)
            for row in dept_result.fetchall():
                filters["departments"].append(
                    {
                        "value": row.department,
                        "count": row.count,
                        "label": f"Department: {row.department}",
                    }
                )

            # Get popular languages
            lang_query = (
                select(JobDescription.language, func.count().label("count"))
                .group_by(JobDescription.language)
                .order_by(desc("count"))
                .limit(5)
            )

            lang_result = await db.execute(lang_query)
            for row in lang_result.fetchall():
                if row.language:
                    filters["languages"].append(
                        {
                            "value": row.language,
                            "count": row.count,
                            "label": f"Language: {row.language}",
                        }
                    )

            # Add common date range suggestions
            filters["date_ranges"] = [
                {"value": "last_month", "label": "Last 30 days"},
                {"value": "last_quarter", "label": "Last 3 months"},
                {"value": "last_year", "label": "Last 12 months"},
                {"value": "current_year", "label": "Current year"},
            ]

        logger.info(
            "Popular filters retrieved",
            total=sum(len(v) for v in filters.values()),
        )

        return filters

    except Exception as e:
        logger.error("Error getting popular filters", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve popular filters"
        )
