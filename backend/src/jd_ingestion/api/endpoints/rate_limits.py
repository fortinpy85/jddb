"""
Rate Limiting API Endpoints

API endpoints for managing rate limits, cost optimization, and usage monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...database.connection import get_async_session
from ...services.rate_limiting_service import (
    rate_limiting_service,
    RateLimitType,
    RateLimit,
)
from ...utils.logging import get_logger, PerformanceTimer

logger = get_logger(__name__)
router = APIRouter()


@router.get("/status/{service}")
async def get_rate_limit_status(
    service: str, db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get current rate limit status for a service.
    """
    try:
        with PerformanceTimer("rate_limit_status") as timer:
            # Check if service exists
            if service not in rate_limiting_service.rate_limits:
                raise HTTPException(
                    status_code=404, detail=f"Service '{service}' not found"
                )

            # Get usage stats
            usage_stats = await rate_limiting_service.get_usage_stats(db, service, 24)

            # Get token bucket statuses
            bucket_statuses = {}
            if service in rate_limiting_service.token_buckets:
                for limit_type, bucket in rate_limiting_service.token_buckets[
                    service
                ].items():
                    bucket_status = await bucket.get_status()
                    bucket_statuses[limit_type.value] = bucket_status

            # Get recommended delay
            recommended_delay = await rate_limiting_service.get_recommended_delay(
                service, "general"
            )

            result = {
                "service": service,
                "usage_stats": usage_stats,
                "token_buckets": bucket_statuses,
                "recommended_delay_seconds": recommended_delay,
                "status_timestamp": datetime.now().isoformat(),
            }

        # Log performance
        logger.debug(
            f"Rate limit status check took {timer.elapsed_ms}ms for service {service}"
        )

        logger.info(
            "Rate limit status retrieved", service=service, duration_ms=timer.elapsed_ms
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting rate limit status", service=service, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get rate limit status")


@router.post("/check/{service}")
async def check_rate_limit(
    service: str,
    operation_type: str = Query(..., description="Type of operation to check"),
    estimated_tokens: int = Query(
        1, ge=1, description="Estimated tokens for the request"
    ),
    estimated_cost: float = Query(0.0, ge=0, description="Estimated cost in USD"),
    user_id: Optional[str] = Query(None, description="User ID for tracking"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Check if a request would be within rate limits.
    """
    try:
        with PerformanceTimer("rate_limit_check") as timer:
            is_allowed, statuses = await rate_limiting_service.check_rate_limit(
                service=service,
                operation_type=operation_type,
                estimated_tokens=estimated_tokens,
                estimated_cost=estimated_cost,
                user_id=user_id,
            )

            # Convert statuses to serializable format
            status_data = []
            for status in statuses:
                status_data.append(
                    {
                        "limit_type": status.limit_type.value,
                        "current_usage": status.current_usage,
                        "limit": status.limit,
                        "window_remaining_seconds": status.window_remaining_seconds,
                        "reset_time": status.reset_time.isoformat(),
                        "is_exceeded": status.is_exceeded,
                    }
                )

            # Get recommended delay if not allowed
            recommended_delay = 0.0
            if not is_allowed:
                recommended_delay = await rate_limiting_service.get_recommended_delay(
                    service, operation_type
                )

            result = {
                "service": service,
                "operation_type": operation_type,
                "is_allowed": is_allowed,
                "rate_limit_statuses": status_data,
                "recommended_delay_seconds": recommended_delay,
                "estimated_tokens": estimated_tokens,
                "estimated_cost": estimated_cost,
                "check_timestamp": datetime.now().isoformat(),
            }

        # Log performance
        logger.debug(
            f"Rate limit check took {timer.elapsed_ms}ms for service {service}"
        )

        logger.info(
            "Rate limit check completed",
            service=service,
            operation_type=operation_type,
            is_allowed=is_allowed,
            duration_ms=timer.elapsed_ms,
        )

        return result

    except Exception as e:
        logger.error(
            "Error checking rate limit",
            service=service,
            operation_type=operation_type,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to check rate limit")


@router.post("/record/{service}")
async def record_usage(
    service: str,
    operation_type: str = Query(..., description="Type of operation performed"),
    tokens_used: int = Query(1, ge=0, description="Actual tokens used"),
    cost: float = Query(0.0, ge=0, description="Actual cost in USD"),
    user_id: Optional[str] = Query(None, description="User ID for tracking"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Record actual API usage for rate limiting.
    """
    try:
        with PerformanceTimer("record_usage") as timer:
            await rate_limiting_service.record_usage(
                service=service,
                operation_type=operation_type,
                tokens_used=tokens_used,
                cost=cost,
                user_id=user_id,
            )

        # Log performance
        logger.debug(f"Record usage took {timer.elapsed_ms}ms for service {service}")

        logger.info(
            "Usage recorded",
            service=service,
            operation_type=operation_type,
            tokens_used=tokens_used,
            cost=cost,
            duration_ms=timer.elapsed_ms,
        )

        return {
            "service": service,
            "operation_type": operation_type,
            "tokens_used": tokens_used,
            "cost": cost,
            "recorded_at": datetime.now().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(
            "Error recording usage",
            service=service,
            operation_type=operation_type,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to record usage")


@router.get("/usage/{service}")
async def get_usage_statistics(
    service: str,
    period_hours: int = Query(
        24, ge=1, le=168, description="Period in hours (max 7 days)"
    ),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get detailed usage statistics for a service.
    """
    try:
        with PerformanceTimer("get_usage_statistics") as timer:
            stats = await rate_limiting_service.get_usage_stats(
                db, service, period_hours
            )

        # Log performance
        logger.debug(
            f"Usage statistics took {timer.elapsed_ms}ms for service {service}"
        )

        logger.info(
            "Usage statistics retrieved",
            service=service,
            period_hours=period_hours,
            duration_ms=timer.elapsed_ms,
        )

        return stats

    except Exception as e:
        logger.error("Error getting usage statistics", service=service, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get usage statistics")


@router.get("/optimization/{service}")
async def get_cost_optimization_recommendations(
    service: str = "openai", db: AsyncSession = Depends(get_async_session)
) -> List[Dict[str, Any]]:
    """
    Get cost optimization recommendations based on usage patterns.
    """
    try:
        with PerformanceTimer("get_cost_optimization") as timer:
            recommendations = (
                await rate_limiting_service.get_cost_optimization_recommendations(
                    db, service
                )
            )

        # Log performance
        logger.debug(
            f"Cost optimization took {timer.elapsed_ms}ms for service {service}"
        )

        logger.info(
            "Cost optimization recommendations generated",
            service=service,
            count=len(recommendations),
            duration_ms=timer.elapsed_ms,
        )

        return recommendations

    except Exception as e:
        logger.error(
            "Error generating cost optimization recommendations",
            service=service,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail="Failed to generate recommendations"
        )


@router.put("/limits/{service}")
async def update_rate_limits(
    service: str,
    limits: Dict[str, Dict[str, Any]],
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Update rate limits for a service.

    Expected format:
    {
        "requests_per_minute": {"limit": 3000, "window_seconds": 60, "burst_allowance": 1.2},
        "tokens_per_minute": {"limit": 150000, "window_seconds": 60, "burst_allowance": 1.2}
    }
    """
    try:
        with PerformanceTimer("update_rate_limits") as timer:
            # Convert input to RateLimit objects
            new_limits = {}
            for limit_type_str, limit_data in limits.items():
                try:
                    limit_type = RateLimitType(limit_type_str)
                    rate_limit = RateLimit(
                        limit=limit_data["limit"],
                        window_seconds=limit_data["window_seconds"],
                        burst_allowance=limit_data.get("burst_allowance", 1.2),
                    )
                    new_limits[limit_type] = rate_limit
                except ValueError:
                    logger.warning("Invalid rate limit type", limit_type=limit_type_str)
                    continue

            if not new_limits:
                raise HTTPException(
                    status_code=400, detail="No valid rate limits provided"
                )

            success = await rate_limiting_service.update_rate_limits(
                service, new_limits
            )

            if not success:
                raise HTTPException(
                    status_code=500, detail="Failed to update rate limits"
                )

        # Log performance
        logger.debug(
            f"Update rate limits took {timer.elapsed_ms}ms for service {service}"
        )

        logger.info(
            "Rate limits updated",
            service=service,
            limits=new_limits,
            duration_ms=timer.elapsed_ms,
        )

        return {
            "service": service,
            "updated_limits": limits,
            "updated_at": datetime.now().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating rate limits", service=service, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update rate limits")


@router.get("/services")
async def list_services() -> List[Dict[str, Any]]:
    """
    List all services with their configured rate limits.
    """
    try:
        services = []
        for service_name, limits in rate_limiting_service.rate_limits.items():
            service_info: Dict[str, Any] = {"name": service_name, "rate_limits": {}}

            for limit_type, rate_limit in limits.items():
                service_info["rate_limits"][limit_type.value] = {
                    "limit": rate_limit.limit,
                    "window_seconds": rate_limit.window_seconds,
                    "burst_allowance": rate_limit.burst_allowance,
                }

            services.append(service_info)

        logger.info("Listed rate-limited services", count=len(services))
        return services

    except Exception as e:
        logger.error("Error listing services", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list services")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for rate limiting service.
    """
    try:
        # Check if rate limiting service is functioning
        services_count = len(rate_limiting_service.rate_limits)
        buckets_count = sum(
            len(buckets) for buckets in rate_limiting_service.token_buckets.values()
        )

        return {
            "status": "healthy",
            "services_configured": services_count,
            "token_buckets_active": buckets_count,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error("Rate limiting service health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
