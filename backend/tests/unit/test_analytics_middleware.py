"""
Tests for analytics middleware.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import Request, Response, FastAPI
from fastapi.testclient import TestClient

from jd_ingestion.middleware.analytics_middleware import (
    AnalyticsMiddleware,
    create_analytics_middleware,
)


@pytest.fixture
def mock_app():
    """Mock FastAPI application."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    @app.get("/search")
    async def search_endpoint(q: str = None):
        return {"results": []}

    @app.post("/ingestion/upload")
    async def upload_endpoint():
        return {"status": "uploaded"}

    @app.get("/jobs/{job_id}")
    async def job_endpoint(job_id: int):
        return {"job": job_id}

    return app


@pytest.fixture
def mock_request():
    """Mock request object."""
    request = Mock(spec=Request)
    request.url.path = "/test"
    request.method = "GET"
    request.headers = {"user-agent": "test-agent"}
    request.query_params = {}
    request.path_params = {}
    request.client = Mock()
    request.client.host = "127.0.0.1"
    return request


@pytest.fixture
def mock_response():
    """Mock response object."""
    response = Mock(spec=Response)
    response.status_code = 200
    return response


class TestAnalyticsMiddleware:
    """Test analytics middleware functionality."""

    def test_init(self):
        """Test middleware initialization."""
        app = Mock()
        middleware = AnalyticsMiddleware(app, track_all_requests=True)

        assert middleware.track_all_requests is True

    def test_init_with_tracking_disabled(self):
        """Test middleware initialization with tracking disabled."""
        app = Mock()
        middleware = AnalyticsMiddleware(app, track_all_requests=False)

        assert middleware.track_all_requests is False

    @patch("jd_ingestion.middleware.analytics_middleware.time")
    @patch("jd_ingestion.middleware.analytics_middleware.asyncio")
    async def test_dispatch_success(
        self, mock_asyncio, mock_time, mock_request, mock_response
    ):
        """Test successful request dispatch."""
        app = Mock()
        middleware = AnalyticsMiddleware(app, track_all_requests=True)

        # Mock time.time() to return consistent values
        mock_time.time.side_effect = [1000.0, 1000.5]  # 500ms response time

        # Mock call_next to return response
        async def mock_call_next(request):
            return mock_response

        # Mock asyncio.create_task
        mock_task = Mock()
        mock_asyncio.create_task.return_value = mock_task

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response == mock_response
        mock_asyncio.create_task.assert_called_once()

    @patch("jd_ingestion.middleware.analytics_middleware.time")
    async def test_dispatch_skip_paths(self, mock_time, mock_request):
        """Test that certain paths are skipped from tracking."""
        app = Mock()
        middleware = AnalyticsMiddleware(app, track_all_requests=True)

        # Set request path to a skipped path
        mock_request.url.path = "/docs"

        # Mock call_next
        mock_response = Mock()

        async def mock_call_next(request):
            return mock_response

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response == mock_response
        # Time should not be called for skipped paths
        mock_time.time.assert_not_called()

    @patch("jd_ingestion.middleware.analytics_middleware.time")
    @patch("jd_ingestion.middleware.analytics_middleware.asyncio")
    async def test_dispatch_with_exception(self, mock_asyncio, mock_time, mock_request):
        """Test dispatch when call_next raises an exception."""
        app = Mock()
        middleware = AnalyticsMiddleware(app, track_all_requests=True)

        # Mock time.time() to return consistent values
        mock_time.time.side_effect = [1000.0, 1000.3]  # 300ms response time

        # Mock call_next to raise exception
        async def mock_call_next(request):
            raise Exception("Test error")

        # Mock asyncio.create_task
        mock_task = Mock()
        mock_asyncio.create_task.return_value = mock_task

        with pytest.raises(Exception, match="Test error"):
            await middleware.dispatch(mock_request, mock_call_next)

        # Should still track the error
        mock_asyncio.create_task.assert_called_once()

    async def test_dispatch_tracking_disabled(self, mock_request, mock_response):
        """Test dispatch when tracking is disabled."""
        app = Mock()
        middleware = AnalyticsMiddleware(app, track_all_requests=False)

        # Mock call_next
        async def mock_call_next(request):
            return mock_response

        with patch(
            "jd_ingestion.middleware.analytics_middleware.asyncio"
        ) as mock_asyncio:
            response = await middleware.dispatch(mock_request, mock_call_next)

            assert response == mock_response
            mock_asyncio.create_task.assert_not_called()

    @patch("jd_ingestion.middleware.analytics_middleware.async_session_context")
    @patch("jd_ingestion.middleware.analytics_middleware.analytics_service")
    async def test_track_request_success(
        self, mock_analytics_service, mock_get_session
    ):
        """Test successful request tracking."""
        app = Mock()
        middleware = AnalyticsMiddleware(app)

        # Mock database session as async context manager
        mock_db = AsyncMock()
        mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_get_session.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock analytics service
        mock_analytics_service.track_activity = AsyncMock()

        request = Mock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        request.headers = {"user-agent": "test-agent"}
        request.query_params = {}
        request.path_params = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"

        response = Mock(spec=Response)
        response.status_code = 200

        await middleware._track_request(
            request=request,
            response=response,
            response_time_ms=500,
            session_id="test-session",
        )

        mock_analytics_service.track_activity.assert_called_once()

    @patch("jd_ingestion.middleware.analytics_middleware.async_session_context")
    @patch("jd_ingestion.middleware.analytics_middleware.analytics_service")
    async def test_track_request_with_error(
        self, mock_analytics_service, mock_get_session
    ):
        """Test request tracking with error."""
        app = Mock()
        middleware = AnalyticsMiddleware(app)

        # Mock database session as async context manager
        mock_db = AsyncMock()
        mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_get_session.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock analytics service
        mock_analytics_service.track_activity = AsyncMock()

        request = Mock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        request.headers = {"user-agent": "test-agent"}
        request.query_params = {}
        request.path_params = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"

        await middleware._track_request(
            request=request,
            response=None,
            response_time_ms=300,
            session_id="test-session",
            error="Test error",
        )

        # Should be called with status_code=500 for errors
        call_args = mock_analytics_service.track_activity.call_args
        assert call_args.kwargs["status_code"] == 500
        assert call_args.kwargs["metadata"]["error"] == "Test error"

    @patch("jd_ingestion.middleware.analytics_middleware.async_session_context")
    @patch("jd_ingestion.middleware.analytics_middleware.logger")
    async def test_track_request_database_error(self, mock_logger, mock_get_session):
        """Test request tracking when database error occurs."""
        app = Mock()
        middleware = AnalyticsMiddleware(app)

        # Mock database session to raise exception
        mock_get_session.side_effect = Exception("Database error")

        request = Mock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        request.headers = {}
        request.query_params = {}
        request.path_params = {}
        request.client = None

        await middleware._track_request(request=request)

        mock_logger.error.assert_called_once()

    def test_determine_action_type_search(self):
        """Test action type determination for search endpoints."""
        app = Mock()
        middleware = AnalyticsMiddleware(app)

        action = middleware._determine_action_type("/api/search", "GET")
        assert action == "search"

        action = middleware._determine_action_type("/search/jobs", "POST")
        assert action == "search"

    def test_determine_action_type_upload(self):
        """Test action type determination for upload endpoints."""
        app = Mock()
        middleware = AnalyticsMiddleware(app)

        action = middleware._determine_action_type("/api/ingestion/upload", "POST")
        assert action == "upload"

        action = middleware._determine_action_type("/ingestion/batch", "POST")
        assert action == "upload"

    def test_determine_action_type_export(self):
        """Test action type determination for export endpoints."""
        app = Mock()
        middleware = AnalyticsMiddleware(app)

        action = middleware._determine_action_type("/api/export", "GET")
        assert action == "export"

        action = middleware._determine_action_type("/jobs/123/export", "GET")
        assert action == "export"

    def test_determine_action_type_analytics(self):
        """Test action type determination for analytics endpoints."""
        app = Mock()
        middleware = AnalyticsMiddleware(app)

        action = middleware._determine_action_type("/api/analytics", "GET")
        assert action == "analytics"

    def test_determine_action_type_view(self):
        """Test action type determination for view endpoints."""
        app = Mock()
        middleware = AnalyticsMiddleware(app)

        action = middleware._determine_action_type("/api/jobs", "GET")
        assert action == "view"

        action = middleware._determine_action_type("/jobs/123", "GET")
        assert action == "view"

    def test_determine_action_type_default(self):
        """Test action type determination for default case."""
        app = Mock()
        middleware = AnalyticsMiddleware(app)

        action = middleware._determine_action_type("/api/unknown", "GET")
        assert action == "api_call"

    def test_extract_resource_id_numeric(self):
        """Test resource ID extraction for numeric IDs."""
        app = Mock()
        middleware = AnalyticsMiddleware(app)

        resource_id = middleware._extract_resource_id("/api/jobs/123")
        assert resource_id == "123"

        resource_id = middleware._extract_resource_id("/api/jobs/456/sections")
        assert resource_id == "456"

    def test_extract_resource_id_uuid(self):
        """Test resource ID extraction for UUID-like IDs."""
        app = Mock()
        middleware = AnalyticsMiddleware(app)

        uuid_id = "550e8400-e29b-41d4-a716-446655440000"
        resource_id = middleware._extract_resource_id(f"/api/jobs/{uuid_id}")
        assert resource_id == uuid_id

    def test_extract_resource_id_none(self):
        """Test resource ID extraction when no ID present."""
        app = Mock()
        middleware = AnalyticsMiddleware(app)

        resource_id = middleware._extract_resource_id("/api/jobs")
        assert resource_id is None

        resource_id = middleware._extract_resource_id("/api/search")
        assert resource_id is None

    @patch("jd_ingestion.middleware.analytics_middleware.async_session_context")
    @patch("jd_ingestion.middleware.analytics_middleware.analytics_service")
    async def test_track_search_request(self, mock_analytics_service, mock_get_session):
        """Test tracking of search requests with query parameters."""
        app = Mock()
        middleware = AnalyticsMiddleware(app)

        # Mock database session as async context manager
        mock_db = AsyncMock()
        mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_get_session.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock analytics service
        mock_analytics_service.track_activity = AsyncMock()

        request = Mock(spec=Request)
        request.url.path = "/api/search"
        request.method = "GET"
        request.headers = {"user-agent": "test-agent"}
        request.query_params = {"q": "test query", "classification": "EX-01"}
        request.path_params = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"

        response = Mock(spec=Response)
        response.status_code = 200

        await middleware._track_request(
            request=request, response=response, response_time_ms=250
        )

        call_args = mock_analytics_service.track_activity.call_args
        assert call_args.kwargs["action_type"] == "search"
        assert call_args.kwargs["search_query"] == "test query"
        assert call_args.kwargs["search_filters"] == {
            "q": "test query",
            "classification": "EX-01",
        }


class TestCreateAnalyticsMiddleware:
    """Test middleware factory function."""

    def test_create_analytics_middleware_default(self):
        """Test creating middleware with default settings."""
        middleware_factory = create_analytics_middleware()

        app = Mock()
        middleware = middleware_factory(app)

        assert isinstance(middleware, AnalyticsMiddleware)
        assert middleware.track_all_requests is True

    def test_create_analytics_middleware_disabled(self):
        """Test creating middleware with tracking disabled."""
        middleware_factory = create_analytics_middleware(track_all_requests=False)

        app = Mock()
        middleware = middleware_factory(app)

        assert isinstance(middleware, AnalyticsMiddleware)
        assert middleware.track_all_requests is False


class TestAnalyticsMiddlewareIntegration:
    """Integration tests for analytics middleware."""

    def test_middleware_integration(self, mock_app):
        """Test middleware integration with FastAPI app."""
        # Add middleware to app
        mock_app.add_middleware(AnalyticsMiddleware, track_all_requests=False)

        # Create test client
        client = TestClient(mock_app)

        # Make request
        response = client.get("/test")

        assert response.status_code == 200
        assert response.json() == {"message": "test"}

    @patch("jd_ingestion.middleware.analytics_middleware.async_session_context")
    @patch("jd_ingestion.middleware.analytics_middleware.analytics_service")
    def test_middleware_with_tracking(
        self, mock_analytics_service, mock_get_session, mock_app
    ):
        """Test middleware with tracking enabled."""
        # Mock database session as async generator
        mock_db = AsyncMock()

        async def mock_async_gen():
            yield mock_db

        mock_get_session.return_value = mock_async_gen()

        # Mock analytics service
        mock_analytics_service.track_activity = AsyncMock()

        # Add middleware with tracking enabled
        mock_app.add_middleware(AnalyticsMiddleware, track_all_requests=True)

        # Create test client
        client = TestClient(mock_app)

        # Make request
        response = client.get("/test")

        assert response.status_code == 200
        # Note: In real integration test, we'd need to wait for background task
        # For unit test, we just verify the middleware was added successfully
