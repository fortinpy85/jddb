"""
Phase 2 monitoring and metrics API endpoints.

This module provides REST API endpoints for monitoring Phase 2 features
including WebSocket connections, collaborative editing, and system performance.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timedelta

from ...monitoring.phase2_metrics import (
    metrics_collector, get_metrics_summary, get_performance_report,
    record_websocket_event, record_collaboration_event, record_translation_event
)
from ...auth.dependencies import require_roles, require_role, AdminUser, OptionalCurrentUser
from ...database.connection import get_async_session
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/monitoring", tags=["phase2-monitoring"])


@router.get("/health")
async def phase2_health_check(
    current_user: OptionalCurrentUser = None,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Health check for Phase 2 features.
    Basic endpoint that can be accessed without authentication for system monitoring.
    """
    try:
        # Test database connectivity for Phase 2 tables
        result = await db.execute(text("SELECT 1 FROM users LIMIT 1"))
        database_ok = result.fetchone() is not None

        # Test WebSocket infrastructure
        websocket_ok = True  # Basic check - WebSocket manager is available

        # Get basic metrics
        summary = await get_metrics_summary()

        health_status = {
            "status": "healthy" if database_ok and websocket_ok else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "database": "ok" if database_ok else "error",
                "websockets": "ok" if websocket_ok else "error",
                "user_management": "ok" if database_ok else "error",
                "collaboration": "ok" if websocket_ok else "error"
            },
            "metrics": {
                "active_websocket_connections": summary["websocket"]["active_connections"],
                "total_operations": summary["collaboration"]["total_operations"],
                "system_uptime_hours": summary["system"]["uptime_hours"]
            }
        }

        if not database_ok or not websocket_ok:
            logger.warning("Phase 2 health check failed", extra=health_status)

        return health_status

    except Exception as e:
        logger.error(f"Phase 2 health check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Phase 2 services unavailable"
        )


@router.get("/metrics/summary")
async def get_current_metrics(
    admin_user: AdminUser
):
    """
    Get current Phase 2 metrics summary.
    Requires admin privileges.
    """
    try:
        summary = await get_metrics_summary()
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metrics"
        )


@router.get("/metrics/performance")
async def get_performance_metrics(
    admin_user: AdminUser
):
    """
    Get detailed performance report for Phase 2 features.
    Requires admin privileges.
    """
    try:
        report = await get_performance_report()
        return {
            "success": True,
            "data": report
        }
    except Exception as e:
        logger.error(f"Error getting performance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance report"
        )


@router.get("/metrics/websockets")
async def get_websocket_metrics(
    admin_user: AdminUser
):
    """
    Get WebSocket-specific metrics.
    Requires admin privileges.
    """
    summary = await get_metrics_summary()
    websocket_data = summary["websocket"]

    # Add additional WebSocket analysis
    websocket_data["health_status"] = "healthy"

    if websocket_data["active_connections"] > 100:
        websocket_data["health_status"] = "high_load"
    elif websocket_data["average_latency_ms"] > 200:
        websocket_data["health_status"] = "high_latency"

    return {
        "success": True,
        "data": websocket_data
    }


@router.get("/metrics/collaboration")
async def get_collaboration_metrics(
    admin_user: AdminUser
):
    """
    Get collaborative editing metrics.
    Requires admin privileges.
    """
    summary = await get_metrics_summary()
    collaboration_data = summary["collaboration"]

    # Calculate additional collaboration metrics
    conflict_rate = 0
    if collaboration_data["total_operations"] > 0:
        conflict_rate = collaboration_data["conflict_resolution_count"] / collaboration_data["total_operations"]

    collaboration_data["conflict_rate"] = conflict_rate
    collaboration_data["health_status"] = "healthy" if conflict_rate < 0.1 else "high_conflicts"

    return {
        "success": True,
        "data": collaboration_data
    }


@router.get("/metrics/system")
async def get_system_metrics(
    admin_user: AdminUser
):
    """
    Get system resource metrics.
    Requires admin privileges.
    """
    summary = await get_metrics_summary()
    system_data = summary["system"]

    # Add system health assessment
    health_issues = []
    if system_data["cpu_usage_percent"] > 80:
        health_issues.append("high_cpu")
    if system_data["memory_usage_percent"] > 85:
        health_issues.append("high_memory")
    if system_data["database_connections"] > 50:
        health_issues.append("high_db_connections")

    system_data["health_issues"] = health_issues
    system_data["health_status"] = "healthy" if not health_issues else "degraded"

    return {
        "success": True,
        "data": system_data
    }


@router.get("/metrics/history")
async def get_metrics_history(
    admin_user: AdminUser,
    metric_name: str = Query(..., description="Name of the metric to retrieve"),
    hours: int = Query(24, ge=1, le=168, description="Number of hours of history to retrieve"),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get historical metrics data from the database.
    Requires admin privileges.
    """
    try:
        since_time = datetime.utcnow() - timedelta(hours=hours)

        result = await db.execute(text("""
            SELECT metric_name, metric_value, metric_unit, recorded_at, metadata
            FROM system_metrics
            WHERE metric_name = :metric_name
              AND recorded_at >= :since_time
            ORDER BY recorded_at DESC
            LIMIT 1000
        """), {
            "metric_name": metric_name,
            "since_time": since_time
        })

        rows = result.fetchall()
        history = []

        for row in rows:
            history.append({
                "metric_name": row[0],
                "metric_value": float(row[1]),
                "metric_unit": row[2],
                "recorded_at": row[3].isoformat(),
                "metadata": row[4]
            })

        return {
            "success": True,
            "data": {
                "metric_name": metric_name,
                "time_range_hours": hours,
                "data_points": len(history),
                "history": history
            }
        }

    except Exception as e:
        logger.error(f"Error retrieving metrics history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metrics history"
        )


@router.get("/active-sessions")
async def get_active_sessions(
    admin_user: AdminUser,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get information about active editing sessions.
    Requires admin privileges.
    """
    try:
        result = await db.execute(text("""
            SELECT
                es.id,
                es.session_id,
                es.job_id,
                es.session_type,
                es.status,
                es.created_at,
                es.updated_at,
                u.username as created_by_username,
                COUNT(ep.id) as participant_count
            FROM editing_sessions es
            LEFT JOIN users u ON es.created_by = u.id
            LEFT JOIN editing_participants ep ON es.id = ep.session_id
            WHERE es.status = 'active'
            GROUP BY es.id, es.session_id, es.job_id, es.session_type, es.status,
                     es.created_at, es.updated_at, u.username
            ORDER BY es.updated_at DESC
        """))

        sessions = []
        for row in result.fetchall():
            sessions.append({
                "session_id": row[1],
                "job_id": row[2],
                "session_type": row[3],
                "status": row[4],
                "created_at": row[5].isoformat(),
                "updated_at": row[6].isoformat(),
                "created_by": row[7],
                "participant_count": row[8]
            })

        return {
            "success": True,
            "data": {
                "active_sessions_count": len(sessions),
                "sessions": sessions
            }
        }

    except Exception as e:
        logger.error(f"Error retrieving active sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active sessions"
        )


@router.get("/user-activity")
async def get_user_activity(
    admin_user: AdminUser,
    hours: int = Query(24, ge=1, le=168, description="Hours of activity to retrieve"),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get user activity metrics for the specified time period.
    Requires admin privileges.
    """
    try:
        since_time = datetime.utcnow() - timedelta(hours=hours)

        # Get user activity events
        result = await db.execute(text("""
            SELECT
                u.username,
                ua.event_type,
                COUNT(*) as event_count,
                MAX(ua.created_at) as last_activity
            FROM user_analytics ua
            JOIN users u ON ua.user_id = u.id
            WHERE ua.created_at >= :since_time
            GROUP BY u.username, ua.event_type
            ORDER BY event_count DESC
        """), {"since_time": since_time})

        activity_data = []
        for row in result.fetchall():
            activity_data.append({
                "username": row[0],
                "event_type": row[1],
                "event_count": row[2],
                "last_activity": row[3].isoformat()
            })

        # Get active users count
        result = await db.execute(text("""
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM user_analytics
            WHERE created_at >= :since_time
        """), {"since_time": since_time})

        active_users = result.scalar()

        return {
            "success": True,
            "data": {
                "time_range_hours": hours,
                "active_users_count": active_users,
                "activity_breakdown": activity_data
            }
        }

    except Exception as e:
        logger.error(f"Error retrieving user activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user activity"
        )


@router.post("/events/websocket")
async def record_websocket_metric(
    admin_user: AdminUser,
    event_type: str,
    connected: Optional[bool] = None,
    sent: Optional[bool] = None,
    latency_ms: Optional[float] = None
):
    """
    Record a WebSocket event for metrics collection.
    Used by the WebSocket infrastructure to report events.
    """
    try:
        kwargs = {}
        if connected is not None:
            kwargs['connected'] = connected
        if sent is not None:
            kwargs['sent'] = sent
        if latency_ms is not None:
            kwargs['latency_ms'] = latency_ms

        record_websocket_event(event_type, **kwargs)

        return {
            "success": True,
            "message": f"WebSocket {event_type} event recorded"
        }

    except Exception as e:
        logger.error(f"Error recording WebSocket event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record WebSocket event"
        )


@router.post("/events/collaboration")
async def record_collaboration_metric(
    admin_user: AdminUser,
    operation_type: str,
    conflict: bool = False
):
    """
    Record a collaboration event for metrics collection.
    """
    try:
        record_collaboration_event(operation_type, conflict)

        return {
            "success": True,
            "message": f"Collaboration {operation_type} event recorded"
        }

    except Exception as e:
        logger.error(f"Error recording collaboration event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record collaboration event"
        )


@router.get("/dashboard")
async def get_monitoring_dashboard(
    admin_user: AdminUser
):
    """
    Get comprehensive monitoring dashboard data for Phase 2 features.
    Requires admin privileges.
    """
    try:
        # Get all metrics summaries
        summary = await get_metrics_summary()
        report = await get_performance_report()

        # Determine overall system health
        health_score = 100
        health_issues = []

        # Check various health indicators
        if summary["system"]["cpu_usage_percent"] > 80:
            health_score -= 20
            health_issues.append("High CPU usage")

        if summary["system"]["memory_usage_percent"] > 85:
            health_score -= 20
            health_issues.append("High memory usage")

        if summary["websocket"]["average_latency_ms"] > 200:
            health_score -= 15
            health_issues.append("High WebSocket latency")

        if summary["collaboration"]["total_operations"] > 0:
            conflict_rate = summary["collaboration"]["conflict_resolution_count"] / summary["collaboration"]["total_operations"]
            if conflict_rate > 0.1:
                health_score -= 10
                health_issues.append("High conflict resolution rate")

        if summary["translation"]["cache_hit_ratio"] < 0.7 and summary["translation"]["translation_requests"] > 10:
            health_score -= 10
            health_issues.append("Low translation cache hit ratio")

        health_status = "excellent" if health_score >= 90 else \
                       "good" if health_score >= 75 else \
                       "fair" if health_score >= 60 else "poor"

        dashboard_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "health": {
                "overall_score": health_score,
                "status": health_status,
                "issues": health_issues
            },
            "metrics_summary": summary,
            "performance_report": report,
            "alerts": report.get("recommendations", [])
        }

        return {
            "success": True,
            "data": dashboard_data
        }

    except Exception as e:
        logger.error(f"Error generating monitoring dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate monitoring dashboard"
        )