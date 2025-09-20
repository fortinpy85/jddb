"""
Health check endpoints for monitoring and observability.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
from datetime import datetime

from ...utils.monitoring import get_health_status, check_system_alerts, system_monitor
from ...utils.logging import get_logger, log_business_metric, PerformanceTimer

logger = get_logger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=Dict[str, Any])
async def basic_health_check():
    """Basic health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "jd-ingestion",
        "version": "1.0.0",
    }


@router.get("/detailed", response_model=Dict[str, Any])
async def detailed_health_check():
    """Comprehensive health check with system metrics."""
    try:
        with PerformanceTimer("health_check_detailed"):
            health_data = await get_health_status()
            log_business_metric(
                "health_check_requests", 1, "counter", {"type": "detailed"}
            )
            return health_data
    except Exception as e:
        logger.error("Detailed health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Health check failed")


@router.get("/alerts", response_model=List[Dict[str, Any]])
async def system_alerts():
    """Get current system alerts."""
    try:
        alerts = await check_system_alerts()
        log_business_metric("alert_check_requests", 1, "counter")
        return alerts
    except Exception as e:
        logger.error("Alert check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Alert check failed")


@router.get("/components/{component_name}")
async def component_health(component_name: str):
    """Get health status for a specific component."""
    valid_components = ["database", "redis", "openai"]
    if component_name not in valid_components:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid component. Must be one of: {', '.join(valid_components)}",
        )

    try:
        health_data = await get_health_status()
        component_status = health_data.get("components", {}).get(component_name)

        if not component_status:
            raise HTTPException(status_code=404, detail="Component not found")

        return {"component": component_name, **component_status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"{component_name} health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Component health check failed")


@router.get("/metrics/system")
async def system_metrics():
    """Get system resource metrics."""
    try:
        health_data = await get_health_status()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": health_data.get("metrics", {}).get("system", {}),
        }
    except Exception as e:
        logger.error("System metrics failed", error=str(e))
        raise HTTPException(status_code=500, detail="System metrics failed")


@router.get("/metrics/application")
async def application_metrics():
    """Get application-specific metrics."""
    try:
        health_data = await get_health_status()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": health_data.get("metrics", {}).get("application", {}),
        }
    except Exception as e:
        logger.error("Application metrics failed", error=str(e))
        raise HTTPException(status_code=500, detail="Application metrics failed")


@router.post("/warmup")
async def warmup_services(background_tasks: BackgroundTasks):
    """Warm up services for faster response times."""

    async def warmup_task():
        try:
            # Warm up database connection
            await system_monitor._check_database_health()

            # Warm up Redis connection
            system_monitor._check_redis_health()

            # Warm up OpenAI connection
            await system_monitor._check_openai_health()

            logger.info("Service warmup completed")
            log_business_metric("service_warmups", 1, "counter")
        except Exception as e:
            logger.error("Service warmup failed", error=str(e))

    background_tasks.add_task(warmup_task)
    return {"message": "Warmup initiated", "timestamp": datetime.utcnow().isoformat()}


@router.get("/readiness")
async def readiness_check():
    """Kubernetes readiness probe endpoint."""
    try:
        # Check critical components
        health_data = await get_health_status()
        components = health_data.get("components", {})

        # Database must be healthy
        db_status = components.get("database", {}).get("status")
        if db_status == "critical":
            raise HTTPException(status_code=503, detail="Database not ready")

        # Redis should be healthy (but degraded is acceptable)
        redis_status = components.get("redis", {}).get("status")
        if redis_status == "critical":
            raise HTTPException(status_code=503, detail="Redis not ready")

        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checked_components": ["database", "redis"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/liveness")
async def liveness_check():
    """Kubernetes liveness probe endpoint."""
    try:
        # Very basic check - just ensure the service is responding
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (
                datetime.utcnow() - datetime.fromtimestamp(0)
            ).total_seconds(),
        }
    except Exception as e:
        logger.error("Liveness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not alive")


@router.get("/startup")
async def startup_check():
    """Kubernetes startup probe endpoint."""
    try:
        # Check if all critical services are initialized
        health_data = await get_health_status()
        components = health_data.get("components", {})

        # Check that all components are at least responding
        for component_name, component_data in components.items():
            if "error" in component_data and "not initialized" in str(
                component_data["error"]
            ):
                raise HTTPException(
                    status_code=503, detail=f"{component_name} not initialized"
                )

        return {
            "status": "started",
            "timestamp": datetime.utcnow().isoformat(),
            "initialized_components": list(components.keys()),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Startup check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not started")
