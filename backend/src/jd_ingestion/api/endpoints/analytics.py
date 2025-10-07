"""
API endpoints for usage analytics and system metrics.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ...database.connection import get_async_session
from ...services.analytics_service import analytics_service
from ...services.search_analytics_service import search_analytics_service
from ...utils.logging import get_logger
from ...utils.error_handler import error_handler

logger = get_logger(__name__)
router = APIRouter(tags=["analytics"])

# Error metrics endpoint added for comprehensive monitoring


class ActivityTrackingRequest(BaseModel):
    """Request model for tracking activity."""

    action_type: str
    endpoint: str
    http_method: str = "GET"
    resource_id: Optional[str] = None
    search_query: Optional[str] = None
    search_filters: Optional[Dict] = None
    results_count: Optional[int] = None
    processing_time_ms: Optional[int] = None
    files_processed: Optional[int] = None
    metadata: Optional[Dict] = None


class AIUsageTrackingRequest(BaseModel):
    """Request model for tracking AI usage."""

    service_type: str
    operation_type: str
    model_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    request_id: Optional[str] = None
    success: str = "success"
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None


@router.post("/track/activity")
async def track_activity(
    request: ActivityTrackingRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Track user activity and system usage.

    Args:
        request: Activity tracking data
        http_request: FastAPI request object for extracting client info
        db: Database session

    Returns:
        Tracking confirmation
    """
    try:
        # Extract client information
        client_host = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent")

        # Generate session ID from request or use existing
        session_id = http_request.headers.get("x-session-id")

        await analytics_service.track_activity(
            db=db,
            action_type=request.action_type,
            endpoint=request.endpoint,
            http_method=request.http_method,
            session_id=session_id,
            ip_address=client_host,
            user_agent=user_agent,
            resource_id=request.resource_id,
            search_query=request.search_query,
            search_filters=request.search_filters,
            results_count=request.results_count,
            processing_time_ms=request.processing_time_ms,
            files_processed=request.files_processed,
            metadata=request.metadata,
        )

        return {"status": "success", "message": "Activity tracked successfully"}

    except Exception as e:
        logger.error("Failed to track activity", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to track activity: {str(e)}"
        )


@router.post("/track/ai-usage")
async def track_ai_usage(
    request: AIUsageTrackingRequest, db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Track AI service usage and costs.

    Args:
        request: AI usage tracking data
        db: Database session

    Returns:
        Tracking confirmation
    """
    try:
        await analytics_service.track_ai_usage(
            db=db,
            service_type=request.service_type,
            operation_type=request.operation_type,
            model_name=request.model_name,
            input_tokens=request.input_tokens,
            output_tokens=request.output_tokens,
            cost_usd=Decimal(str(request.cost_usd)),
            request_id=request.request_id,
            success=request.success,
            error_message=request.error_message,
            metadata=request.metadata,
        )

        return {"status": "success", "message": "AI usage tracked successfully"}

    except Exception as e:
        logger.error("Failed to track AI usage", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to track AI usage: {str(e)}"
        )


@router.get("/statistics")
async def get_usage_statistics(
    period: str = Query("day", description="Time period: hour, day, week, month"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get usage statistics for a specified period.

    Args:
        period: Time period for statistics
        start_date: Optional start date
        end_date: Optional end date
        db: Database session

    Returns:
        Usage statistics
    """
    try:
        # Parse dates if provided
        start_datetime = None
        end_datetime = None

        if start_date:
            start_datetime = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if end_date:
            end_datetime = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        stats = await analytics_service.get_usage_statistics(
            db=db, period=period, start_date=start_datetime, end_date=end_datetime
        )

        return {"status": "success", "statistics": stats}

    except ValueError as e:
        logger.warning("Invalid date format in analytics request", error=str(e))
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error("Failed to get usage statistics", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get usage statistics: {str(e)}"
        )


@router.get("/dashboard")
async def get_analytics_dashboard(
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get comprehensive analytics dashboard data.

    Args:
        db: Database session

    Returns:
        Dashboard analytics data
    """
    try:
        dashboard_data = await analytics_service.get_analytics_dashboard(db)

        return {"status": "success", "dashboard": dashboard_data}

    except Exception as e:
        logger.error("Failed to generate analytics dashboard", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to generate analytics dashboard: {str(e)}"
        )


@router.post("/metrics/generate")
async def generate_system_metrics(
    metric_type: str = Query(
        "daily", description="Metric type: hourly, daily, weekly, monthly"
    ),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Generate and store aggregated system metrics.

    Args:
        metric_type: Type of metrics to generate
        db: Database session

    Returns:
        Generated metrics summary
    """
    try:
        if metric_type not in ["hourly", "daily", "weekly", "monthly"]:
            raise HTTPException(status_code=400, detail="Invalid metric type")

        metrics_summary = await analytics_service.generate_system_metrics(
            db=db, metric_type=metric_type
        )

        return {"status": "success", "metrics": metrics_summary}

    except Exception as e:
        logger.error("Failed to generate system metrics", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to generate system metrics: {str(e)}"
        )


@router.get("/search-patterns")
async def get_search_patterns(
    period: str = Query("week", description="Analysis period"),
    limit: int = Query(20, description="Number of top patterns to return"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get search patterns and popular queries.

    Args:
        period: Time period for analysis
        limit: Number of top patterns to return
        db: Database session

    Returns:
        Search patterns analysis
    """
    try:
        stats = await analytics_service.get_usage_statistics(db, period)
        search_patterns = stats["search_patterns"]

        # Limit popular searches
        if len(search_patterns["popular_searches"]) > limit:
            search_patterns["popular_searches"] = search_patterns["popular_searches"][
                :limit
            ]

        return {
            "status": "success",
            "period": period,
            "search_patterns": search_patterns,
        }

    except Exception as e:
        logger.error("Failed to get search patterns", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get search patterns: {str(e)}"
        )


@router.get("/performance")
async def get_performance_metrics(
    period: str = Query("day", description="Analysis period"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get system performance metrics.

    Args:
        period: Time period for analysis
        db: Database session

    Returns:
        Performance metrics
    """
    try:
        stats = await analytics_service.get_usage_statistics(db, period)
        performance_metrics = stats["performance"]

        return {
            "status": "success",
            "period": period,
            "performance": performance_metrics,
        }

    except Exception as e:
        logger.error("Failed to get performance metrics", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.get("/performance-summary")
async def get_performance_summary(
    period: str = Query("day", description="Analysis period"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get system performance summary (alias for performance endpoint).

    Args:
        period: Time period for analysis
        db: Database session

    Returns:
        Performance summary data
    """
    try:
        stats = await analytics_service.get_usage_statistics(db, period)
        performance_metrics = stats["performance"]

        return {
            "status": "success",
            "period": period,
            "summary": performance_metrics,  # Use 'summary' key as expected by tests
        }

    except Exception as e:
        logger.error("Failed to get performance summary", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance summary: {str(e)}"
        )


@router.get("/ai-usage")
async def get_ai_usage_analysis(
    period: str = Query("week", description="Analysis period"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get detailed AI usage analysis.

    Args:
        period: Time period for analysis
        db: Database session

    Returns:
        AI usage analysis
    """
    try:
        stats = await analytics_service.get_usage_statistics(db, period)
        ai_usage = stats["ai_usage"]

        return {"status": "success", "period": period, "ai_usage": ai_usage}

    except Exception as e:
        logger.error("Failed to get AI usage analysis", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get AI usage analysis: {str(e)}"
        )


@router.get("/trends")
async def get_usage_trends(
    metric: str = Query(
        "requests",
        description="Metric to analyze: requests, sessions, searches, ai_cost",
    ),
    days: int = Query(30, description="Number of days for trend analysis"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get usage trends over time.

    Args:
        metric: Metric to analyze trends for
        days: Number of days to analyze
        db: Database session

    Returns:
        Usage trends data
    """
    try:
        # Get daily statistics for the specified period
        trends_data = []
        current_date = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        for i in range(days):
            day_start = current_date - timedelta(days=i + 1)
            day_end = current_date - timedelta(days=i)

            daily_stats = await analytics_service.get_usage_statistics(
                db=db, period="day", start_date=day_start, end_date=day_end
            )

            # Extract the requested metric
            if metric == "requests":
                value = daily_stats["usage"]["total_requests"]
            elif metric == "sessions":
                value = daily_stats["usage"]["unique_sessions"]
            elif metric == "searches":
                value = daily_stats["search_patterns"]["total_searches"]
            elif metric == "ai_cost":
                value = daily_stats["ai_usage"]["total_cost_usd"]
            else:
                value = 0

            trends_data.append({"date": day_start.isoformat(), "value": value})

        # Reverse to show chronological order
        trends_data.reverse()

        return {
            "status": "success",
            "metric": metric,
            "period_days": days,
            "trends": trends_data,
        }

    except Exception as e:
        logger.error("Failed to get usage trends", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get usage trends: {str(e)}"
        )


@router.get("/export")
async def export_analytics_data(
    period: str = Query("month", description="Period to export"),
    format: str = Query("json", description="Export format: json, csv"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Export analytics data in various formats.

    Args:
        period: Time period to export
        format: Export format
        db: Database session

    Returns:
        Exported analytics data
    """
    try:
        stats = await analytics_service.get_usage_statistics(db, period)

        if format.lower() == "csv":
            # For CSV export, we'd typically generate CSV content
            # For now, return JSON with indication of format
            return {
                "status": "success",
                "format": "csv",
                "message": "CSV export would be implemented here",
                "data": stats,
            }
        else:
            return {"status": "success", "format": "json", "data": stats}

    except Exception as e:
        logger.error("Failed to export analytics data", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to export analytics data: {str(e)}"
        )


# Utility endpoint for session management
@router.get("/session/generate")
async def generate_session_id() -> Dict[str, Any]:
    """
    Generate a new session ID for client tracking.

    Returns:
        New session ID
    """
    import uuid

    session_id = str(uuid.uuid4())

    return {
        "status": "success",
        "session_id": session_id,
        "instructions": "Include this session_id in the 'x-session-id' header for activity tracking",
    }


@router.get("/errors/metrics")
async def get_error_metrics() -> Dict[str, Any]:
    """
    Get comprehensive error metrics and statistics.

    Returns:
        Error metrics including total errors, breakdowns by category and severity,
        recovery statistics, and error rates.
    """
    try:
        # Get error statistics from the global error handler
        error_stats = error_handler.get_error_stats()

        # Calculate additional metrics
        total_errors = error_stats.get("total_errors", 0)
        recovery_attempts = error_stats.get("recovery_attempts", 0)
        successful_recoveries = error_stats.get("successful_recoveries", 0)

        # Calculate recovery rate
        recovery_rate = 0.0
        if recovery_attempts > 0:
            recovery_rate = (successful_recoveries / recovery_attempts) * 100

        # Calculate error rates by category and severity
        by_category = error_stats.get("by_category", {})
        by_severity = error_stats.get("by_severity", {})

        # Calculate percentages
        category_percentages = {}
        severity_percentages = {}

        if total_errors > 0:
            for category, count in by_category.items():
                category_percentages[category] = (count / total_errors) * 100

            for severity, count in by_severity.items():
                severity_percentages[severity] = (count / total_errors) * 100

        # Build comprehensive response
        response_data = {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "error_metrics": {
                "summary": {
                    "total_errors": total_errors,
                    "recovery_attempts": recovery_attempts,
                    "successful_recoveries": successful_recoveries,
                    "recovery_rate_percent": round(recovery_rate, 2),
                },
                "breakdown": {
                    "by_category": {
                        "counts": by_category,
                        "percentages": {
                            k: round(v, 2) for k, v in category_percentages.items()
                        },
                    },
                    "by_severity": {
                        "counts": by_severity,
                        "percentages": {
                            k: round(v, 2) for k, v in severity_percentages.items()
                        },
                    },
                },
                "health_indicators": {
                    "error_rate_status": (
                        "healthy"
                        if total_errors < 50
                        else "warning"
                        if total_errors < 100
                        else "critical"
                    ),
                    "recovery_rate_status": (
                        "excellent"
                        if recovery_rate > 80
                        else "good"
                        if recovery_rate > 60
                        else "needs_attention"
                    ),
                    "most_common_category": (
                        max(by_category.items(), key=lambda x: x[1])[0]
                        if by_category
                        else None
                    ),
                    "most_common_severity": (
                        max(by_severity.items(), key=lambda x: x[1])[0]
                        if by_severity
                        else None
                    ),
                },
            },
        }

        logger.info("Error metrics retrieved successfully", total_errors=total_errors)
        return response_data

    except Exception as e:
        logger.error("Failed to retrieve error metrics", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve error metrics: {str(e)}"
        )


@router.post("/errors/reset")
async def reset_error_metrics() -> Dict[str, Any]:
    """
    Reset error metrics counters.

    WARNING: This will clear all error statistics. Use with caution.

    Returns:
        Confirmation of reset operation
    """
    try:
        # Store current stats before reset
        current_stats = error_handler.get_error_stats()

        # Reset the error statistics
        error_handler.error_stats = {
            "total_errors": 0,
            "by_category": {},
            "by_severity": {},
            "recovery_attempts": 0,
            "successful_recoveries": 0,
        }

        logger.warning("Error metrics reset performed", previous_stats=current_stats)

        return {
            "status": "success",
            "message": "Error metrics have been reset",
            "timestamp": datetime.utcnow().isoformat(),
            "previous_stats": current_stats,
        }

    except Exception as e:
        logger.error("Failed to reset error metrics", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to reset error metrics: {str(e)}"
        )


# === Search Analytics Endpoints ===
# Merged from search_analytics.py for consolidation


@router.get("/search/performance")
async def get_search_performance(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Get search performance statistics for the specified time period."""
    try:
        stats = await search_analytics_service.get_search_performance_stats(
            db=db, days=days
        )

        if not stats:
            return {
                "message": "No search data found for the specified period",
                "period_days": days,
            }

        return stats

    except Exception as e:
        logger.error("Failed to get search performance stats", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve search performance statistics"
        )


@router.get("/search/trends")
async def get_search_trends(
    days: int = Query(7, ge=1, le=90, description="Number of days for trend analysis"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Get search query trends over time."""
    try:
        trends = await search_analytics_service.get_query_trends(db=db, days=days)

        if not trends:
            return {
                "message": "No trend data found for the specified period",
                "period_days": days,
            }

        return trends

    except Exception as e:
        logger.error("Failed to get search trends", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve search trends")


@router.get("/search/slow-queries")
async def get_slow_queries(
    threshold_ms: int = Query(
        1000, ge=100, le=10000, description="Minimum execution time in milliseconds"
    ),
    limit: int = Query(10, ge=1, le=50, description="Number of queries to return"),
    db: AsyncSession = Depends(get_async_session),
) -> List[Dict[str, Any]]:
    """Get the slowest search queries above the threshold."""
    try:
        slow_queries = await search_analytics_service.get_slow_queries(
            db=db, threshold_ms=threshold_ms, limit=limit
        )

        return slow_queries

    except Exception as e:
        logger.error("Failed to get slow queries", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve slow queries")


@router.post("/search/feedback/{search_id}")
async def record_search_feedback(
    search_id: str,
    clicked_results: List[int],
    satisfaction_rating: Optional[int] = Query(
        None, ge=1, le=5, description="User satisfaction rating (1-5)"
    ),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, str]:
    """Record user feedback for a specific search."""
    try:
        await search_analytics_service.record_user_feedback(
            db=db,
            search_id=search_id,
            clicked_results=clicked_results,
            satisfaction_rating=satisfaction_rating,
        )

        return {"message": "Feedback recorded successfully", "search_id": search_id}

    except Exception as e:
        logger.error(
            "Failed to record search feedback", search_id=search_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to record search feedback")


@router.get("/search/dashboard")
async def get_search_analytics_dashboard(
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Get comprehensive search analytics data for dashboard display."""
    try:
        # Get performance stats for last 30 days
        performance_stats = await search_analytics_service.get_search_performance_stats(
            db=db, days=30
        )

        # Get trends for last 7 days
        trends = await search_analytics_service.get_query_trends(db=db, days=7)

        # Get slow queries
        slow_queries = await search_analytics_service.get_slow_queries(
            db=db, threshold_ms=1000, limit=5
        )

        dashboard_data = {
            "overview": {
                "period": "Last 30 Days",
                "total_searches": performance_stats.get("total_searches", 0),
                "avg_response_time_ms": performance_stats.get("performance", {}).get(
                    "avg_execution_time_ms", 0
                ),
                "search_types": performance_stats.get("search_types", {}),
                "success_rates": performance_stats.get("success_rates", {}),
            },
            "trends": {
                "daily_volume": trends.get("daily_volume", []),
                "performance_trends": trends.get("performance_trends", []),
            },
            "performance_issues": {
                "slow_queries_count": len(slow_queries),
                "slow_queries": slow_queries[:3],  # Top 3 slowest
                "performance_alerts": _generate_search_performance_alerts(
                    performance_stats
                ),
            },
            "popular_queries": performance_stats.get("popular_queries", [])[
                :5
            ],  # Top 5
        }

        return dashboard_data

    except Exception as e:
        logger.error("Failed to get search analytics dashboard data", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve search dashboard data"
        )


def _generate_search_performance_alerts(
    performance_stats: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Generate performance alerts based on search analytics data."""
    alerts: List[Dict[str, str]] = []

    if not performance_stats:
        return alerts

    perf_data = performance_stats.get("performance", {})
    avg_time = perf_data.get("avg_execution_time_ms", 0)
    p95_time = perf_data.get("p95_execution_time_ms", 0)

    # Alert for slow average response time
    if avg_time > 2000:
        alerts.append(
            {
                "type": "warning",
                "message": f"Average search time is {avg_time:.0f}ms - consider optimization",
                "metric": "avg_response_time",
            }
        )

    # Alert for slow 95th percentile
    if p95_time > 5000:
        alerts.append(
            {
                "type": "critical",
                "message": f"95th percentile response time is {p95_time:.0f}ms - urgent optimization needed",
                "metric": "p95_response_time",
            }
        )

    # Alert for low success rate
    success_rates = performance_stats.get("success_rates", {})
    error_count = success_rates.get("error", 0)
    total_searches = performance_stats.get("total_searches", 0)

    if total_searches > 0 and error_count / total_searches > 0.05:  # >5% error rate
        error_rate = (error_count / total_searches) * 100
        alerts.append(
            {
                "type": "warning",
                "message": f"Search error rate is {error_rate:.1f}% - investigate failures",
                "metric": "error_rate",
            }
        )

    return alerts


# === Skills Analytics Endpoints ===


@router.get("/skills/inventory")
async def get_skills_inventory(
    search: Optional[str] = Query(None, description="Search skills by name"),
    skill_type: Optional[str] = Query(None, description="Filter by skill type"),
    min_job_count: Optional[int] = Query(
        None, ge=1, description="Minimum number of jobs"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Number of skills to return"),
    offset: int = Query(0, ge=0, description="Number of skills to skip"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get comprehensive skills inventory with job counts and statistics.

    Returns all skills in the database with:
    - Number of jobs requiring each skill
    - Average confidence score
    - Skill type and category information
    """
    try:
        from sqlalchemy import func, select, desc
        from ...database.models import Skill, job_description_skills

        # Build base query for skills with job counts
        skills_query = (
            select(
                Skill.id,
                Skill.lightcast_id,
                Skill.name,
                Skill.skill_type,
                Skill.category,
                Skill.subcategory,
                func.count(job_description_skills.c.job_id).label("job_count"),
                func.avg(job_description_skills.c.confidence).label("avg_confidence"),
            )
            .outerjoin(
                job_description_skills,
                Skill.id == job_description_skills.c.skill_id,
            )
            .group_by(
                Skill.id,
                Skill.lightcast_id,
                Skill.name,
                Skill.skill_type,
                Skill.category,
                Skill.subcategory,
            )
        )

        # Apply filters
        if search:
            skills_query = skills_query.where(Skill.name.ilike(f"%{search}%"))
        if skill_type:
            skills_query = skills_query.where(Skill.skill_type == skill_type)
        if min_job_count:
            skills_query = skills_query.having(
                func.count(job_description_skills.c.job_id) >= min_job_count
            )

        # Get total count before pagination
        count_query = select(func.count()).select_from(skills_query.subquery())
        count_result = await db.execute(count_query)
        total_count = count_result.scalar_one()

        # Apply ordering and pagination
        skills_query = (
            skills_query.order_by(desc("job_count"), Skill.name)
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(skills_query)
        skills = result.all()

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "skills": [
                {
                    "id": skill.id,
                    "lightcast_id": skill.lightcast_id,
                    "name": skill.name,
                    "skill_type": skill.skill_type,
                    "category": skill.category,
                    "subcategory": skill.subcategory,
                    "job_count": skill.job_count,
                    "avg_confidence": round(float(skill.avg_confidence), 3)
                    if skill.avg_confidence
                    else 0.0,
                }
                for skill in skills
            ],
        }

    except Exception as e:
        logger.error("Failed to get skills inventory", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve skills inventory"
        )


@router.get("/skills/top")
async def get_top_skills(
    limit: int = Query(10, ge=1, le=100, description="Number of top skills to return"),
    skill_type: Optional[str] = Query(None, description="Filter by skill type"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get top N most frequently requested skills across all job descriptions.

    Returns skills ordered by the number of jobs that require them.
    """
    try:
        from sqlalchemy import func, select, desc
        from ...database.models import Skill, JobDescription, job_description_skills

        # Query for top skills
        query = (
            select(
                Skill.id,
                Skill.lightcast_id,
                Skill.name,
                Skill.skill_type,
                Skill.category,
                func.count(job_description_skills.c.job_id).label("job_count"),
                func.avg(job_description_skills.c.confidence).label("avg_confidence"),
                func.max(job_description_skills.c.confidence).label("max_confidence"),
                func.min(job_description_skills.c.confidence).label("min_confidence"),
            )
            .join(
                job_description_skills,
                Skill.id == job_description_skills.c.skill_id,
            )
            .group_by(
                Skill.id,
                Skill.lightcast_id,
                Skill.name,
                Skill.skill_type,
                Skill.category,
            )
        )

        # Apply filter
        if skill_type:
            query = query.where(Skill.skill_type == skill_type)

        # Order by job count and limit
        query = query.order_by(desc("job_count"), Skill.name).limit(limit)

        result = await db.execute(query)
        skills = result.all()

        # Get total job count for percentage calculation
        total_jobs_result = await db.execute(select(func.count(JobDescription.id)))
        total_jobs = total_jobs_result.scalar_one()

        return {
            "total_jobs": total_jobs,
            "top_skills": [
                {
                    "id": skill.id,
                    "lightcast_id": skill.lightcast_id,
                    "name": skill.name,
                    "skill_type": skill.skill_type,
                    "category": skill.category,
                    "job_count": skill.job_count,
                    "percentage": round((skill.job_count / total_jobs * 100), 2)
                    if total_jobs > 0
                    else 0.0,
                    "avg_confidence": round(float(skill.avg_confidence), 3)
                    if skill.avg_confidence
                    else 0.0,
                    "confidence_range": {
                        "min": round(float(skill.min_confidence), 3)
                        if skill.min_confidence
                        else 0.0,
                        "max": round(float(skill.max_confidence), 3)
                        if skill.max_confidence
                        else 0.0,
                    },
                }
                for skill in skills
            ],
        }

    except Exception as e:
        logger.error("Failed to get top skills", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve top skills")


@router.get("/skills/types")
async def get_skill_types(
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get distribution of skills by type.

    Returns count of skills for each skill type category.
    """
    try:
        from sqlalchemy import func, select, desc
        from ...database.models import Skill, job_description_skills

        # Query for skill types distribution
        query = (
            select(
                Skill.skill_type,
                func.count(Skill.id).label("skill_count"),
                func.count(func.distinct(job_description_skills.c.job_id)).label(
                    "job_count"
                ),
            )
            .outerjoin(
                job_description_skills,
                Skill.id == job_description_skills.c.skill_id,
            )
            .group_by(Skill.skill_type)
            .order_by(desc("skill_count"))
        )

        result = await db.execute(query)
        types = result.all()

        return {
            "skill_types": [
                {
                    "type": skill_type.skill_type
                    if skill_type.skill_type
                    else "Unknown",
                    "skill_count": skill_type.skill_count,
                    "job_count": skill_type.job_count,
                }
                for skill_type in types
            ],
            "total_types": len(types),
        }

    except Exception as e:
        logger.error("Failed to get skill types", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve skill types")


@router.get("/skills/stats")
async def get_skills_statistics(
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get overall skills statistics.

    Returns summary statistics about skills in the system.
    """
    try:
        from sqlalchemy import func, select
        from ...database.models import Skill, JobDescription, job_description_skills

        # Total unique skills
        total_skills_result = await db.execute(select(func.count(Skill.id)))
        total_skills = total_skills_result.scalar_one()

        # Total skill-job associations
        total_associations_result = await db.execute(
            select(func.count()).select_from(job_description_skills)
        )
        total_associations = total_associations_result.scalar_one()

        # Jobs with skills
        jobs_with_skills_result = await db.execute(
            select(
                func.count(func.distinct(job_description_skills.c.job_id))
            ).select_from(job_description_skills)
        )
        jobs_with_skills = jobs_with_skills_result.scalar_one()

        # Total jobs
        total_jobs_result = await db.execute(select(func.count(JobDescription.id)))
        total_jobs = total_jobs_result.scalar_one()

        # Average skills per job
        avg_skills_per_job = (
            total_associations / jobs_with_skills if jobs_with_skills > 0 else 0
        )

        # Average confidence score
        avg_confidence_result = await db.execute(
            select(func.avg(job_description_skills.c.confidence)).select_from(
                job_description_skills
            )
        )
        avg_confidence = avg_confidence_result.scalar_one()

        return {
            "total_unique_skills": total_skills,
            "total_skill_associations": total_associations,
            "jobs_with_skills": jobs_with_skills,
            "total_jobs": total_jobs,
            "skills_coverage_percentage": round(
                (jobs_with_skills / total_jobs * 100), 2
            )
            if total_jobs > 0
            else 0.0,
            "avg_skills_per_job": round(avg_skills_per_job, 2),
            "avg_confidence_score": round(float(avg_confidence), 3)
            if avg_confidence
            else 0.0,
        }

    except Exception as e:
        logger.error("Failed to get skills statistics", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve skills statistics"
        )
