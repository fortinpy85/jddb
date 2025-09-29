"""
Middleware for automatic analytics tracking.
"""

import time
import asyncio
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..database.connection import get_async_session
from ..services.analytics_service import analytics_service
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track API requests and performance."""

    def __init__(self, app, track_all_requests: bool = True):
        super().__init__(app)
        self.track_all_requests = track_all_requests

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track analytics."""

        # Skip tracking for certain endpoints
        skip_paths = ["/docs", "/openapi.json", "/favicon.ico", "/health"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Extract session ID from headers
        session_id = request.headers.get("x-session-id")

        try:
            # Process the request
            response = await call_next(request)

            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)

            # Track the activity asynchronously (fire and forget)
            if self.track_all_requests:
                asyncio.create_task(
                    self._track_request(
                        request=request,
                        response=response,
                        response_time_ms=response_time_ms,
                        session_id=session_id,
                    )
                )

            return response

        except Exception as e:
            # Track errors as well
            response_time_ms = int((time.time() - start_time) * 1000)

            if self.track_all_requests:
                asyncio.create_task(
                    self._track_request(
                        request=request,
                        response=None,
                        response_time_ms=response_time_ms,
                        session_id=session_id,
                        error=str(e),
                    )
                )

            raise

    async def _track_request(
        self,
        request: Request,
        response: Response = None,
        response_time_ms: int = 0,
        session_id: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """Track request analytics in background."""
        try:
            # Get database session
            async for db in get_async_session():
                try:
                    # Determine action type based on endpoint
                    action_type = self._determine_action_type(
                        request.url.path, request.method
                    )

                    # Extract additional context
                    search_query = None
                    search_filters = None
                    results_count = None

                    # For search endpoints, try to extract query parameters
                    if action_type == "search":
                        search_query = request.query_params.get(
                            "q"
                        ) or request.query_params.get("query")
                        if request.query_params:
                            search_filters = dict(request.query_params)

                    # Extract resource ID from path
                    resource_id = self._extract_resource_id(request.url.path)

                    # Get client information
                    client_host = request.client.host if request.client else None
                    user_agent = request.headers.get("user-agent")

                    # Determine status code
                    status_code = response.status_code if response else 500

                    # Track the activity
                    await analytics_service.track_activity(
                        db=db,
                        action_type=action_type,
                        endpoint=request.url.path,
                        http_method=request.method,
                        session_id=session_id,
                        ip_address=client_host,
                        user_agent=user_agent,
                        resource_id=resource_id,
                        response_time_ms=response_time_ms,
                        status_code=status_code,
                        search_query=search_query,
                        search_filters=search_filters,
                        results_count=results_count,
                        metadata={
                            "error": error,
                            "path_params": (
                                dict(request.path_params)
                                if request.path_params
                                else None
                            ),
                            "query_params": (
                                dict(request.query_params)
                                if request.query_params
                                else None
                            ),
                        },
                    )

                    break  # Exit the async for loop after successful tracking

                except Exception as track_error:
                    logger.error(
                        "Failed to track request analytics",
                        path=request.url.path,
                        error=str(track_error),
                    )
                finally:
                    await db.close()

        except Exception as middleware_error:
            logger.error("Analytics middleware error", error=str(middleware_error))

    def _determine_action_type(self, path: str, method: str) -> str:
        """Determine action type based on endpoint path and method."""

        path_lower = path.lower()

        if "/search" in path_lower:
            return "search"
        elif "/ingestion" in path_lower and method == "POST":
            return "upload"
        elif "/export" in path_lower or path_lower.endswith("/export"):
            return "export"
        elif "/quality" in path_lower:
            return "analyze"
        elif "/analytics" in path_lower:
            return "analytics"
        elif "/jobs" in path_lower and method == "GET":
            return "view"
        elif "/tasks" in path_lower:
            return "process"
        else:
            return "api_call"

    def _extract_resource_id(self, path: str) -> Optional[str]:
        """Extract resource ID from URL path."""

        # Common patterns for extracting IDs
        path_parts = path.strip("/").split("/")

        for i, part in enumerate(path_parts):
            # Look for numeric IDs
            if part.isdigit():
                return part

            # Look for UUID-like patterns
            if len(part) >= 32 and "-" in part:
                return part

        return None


# Factory function to create the middleware
def create_analytics_middleware(track_all_requests: bool = True):
    """Create analytics middleware with configuration."""

    def middleware_factory(app):
        return AnalyticsMiddleware(app, track_all_requests=track_all_requests)

    return middleware_factory
