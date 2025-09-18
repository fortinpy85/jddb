"""
Search Analytics API Endpoints

Provides endpoints for retrieving search performance metrics, trends, and analytics data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...database.connection import get_async_session
from ...services.search_analytics_service import search_analytics_service
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/performance")
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


@router.get("/trends")
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


@router.get("/slow-queries")
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


@router.post("/feedback/{search_id}")
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


@router.get("/dashboard")
async def get_analytics_dashboard(
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Get comprehensive analytics data for dashboard display."""
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
                "performance_alerts": _generate_performance_alerts(performance_stats),
            },
            "popular_queries": performance_stats.get("popular_queries", [])[
                :5
            ],  # Top 5
        }

        return dashboard_data

    except Exception as e:
        logger.error("Failed to get analytics dashboard data", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")


def _generate_performance_alerts(
    performance_stats: Dict[str, Any]
) -> List[Dict[str, str]]:
    """Generate performance alerts based on analytics data."""
    alerts = []

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
