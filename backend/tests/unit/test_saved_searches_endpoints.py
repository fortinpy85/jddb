"""
Tests for saved searches API endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from jd_ingestion.api.main import app
from jd_ingestion.database.models import SavedSearch, UserPreference


@pytest.fixture
def mock_db_session():
    """Mock database session fixture."""
    mock_session = AsyncMock()
    return mock_session


@pytest.fixture
def override_get_async_session(mock_db_session):
    """Override function for database dependency."""

    async def _override():
        yield mock_db_session

    return _override


@pytest.fixture
def mock_analytics_service():
    """Mock analytics service fixture."""
    with patch("jd_ingestion.api.endpoints.saved_searches.analytics_service") as mock:
        mock.track_activity = AsyncMock()
        yield mock


@pytest.fixture
def sample_saved_search():
    """Sample saved search data."""
    return SavedSearch(
        id=1,
        name="Test Search",
        description="A test search",
        user_id="user123",
        session_id="session123",
        search_query="python developer",
        search_type="text",
        search_filters={"location": "Toronto", "level": "senior"},
        is_public="false",
        is_favorite="true",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        last_used=datetime.now(),
        use_count=5,
        last_result_count=25,
        last_execution_time_ms=150,
        search_metadata={"tags": ["python", "backend"]},
    )


@pytest.fixture
def sample_user_preference():
    """Sample user preference data."""
    return UserPreference(
        id=1,
        user_id="user123",
        session_id="session123",
        preference_type="ui",
        preference_key="theme",
        preference_value="dark",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestCreateSavedSearch:
    """Test create saved search endpoint."""

    @pytest.mark.asyncio
    async def test_create_saved_search_success(
        self, mock_analytics_service, override_get_async_session, mock_db_session
    ):
        """Test successful saved search creation."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        # Mock the saved search creation
        mock_search = Mock()
        mock_search.id = 1
        mock_search.name = "Test Search"
        mock_search.description = "Test Description"
        mock_search.search_query = "python developer"
        mock_search.search_type = "text"
        mock_search.search_filters = {"location": "Toronto"}
        mock_search.is_public = "false"
        mock_search.is_favorite = "true"
        mock_search.created_at = datetime.now()
        mock_search.search_metadata = {"tags": ["python"]}

        search_data = {
            "name": "Test Search",
            "description": "Test Description",
            "search_query": "python developer",
            "search_type": "text",
            "search_filters": {"location": "Toronto"},
            "is_public": False,
            "is_favorite": True,
            "search_metadata": {"tags": ["python"]},
        }

        headers = {"x-user-id": "user123", "x-session-id": "session123"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/saved-searches/", json=search_data, headers=headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "saved_search" in data
        assert data["saved_search"]["name"] == "Test Search"

        mock_analytics_service.track_activity.assert_called_once()

        # Clean up overrides
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_saved_search_no_headers(self):
        """Test saved search creation without required headers."""
        search_data = {"name": "Test Search"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post("/api/saved-searches/", json=search_data)

        assert response.status_code == 400
        assert (
            "x-user-id or x-session-id header is required" in response.json()["detail"]
        )

    @pytest.mark.asyncio
    async def test_create_saved_search_minimal_data(
        self, mock_analytics_service, override_get_async_session, mock_db_session
    ):
        """Test saved search creation with minimal data."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        search_data = {"name": "Minimal Search"}
        headers = {"x-session-id": "session123"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/saved-searches/", json=search_data, headers=headers
            )

        assert response.status_code == 200

        # Clean up overrides
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_saved_search_error(self):
        """Test saved search creation with database error."""
        # Override the dependency to return a session that fails
        from jd_ingestion.database.connection import get_async_session
        from jd_ingestion.api.main import app

        async def error_db_session():
            mock_db = AsyncMock()

            # Make add() raise an exception when called synchronously
            def failing_add(*args, **kwargs):
                raise Exception("Database error")

            mock_db.add = failing_add
            mock_db.rollback = AsyncMock()
            return mock_db

        app.dependency_overrides[get_async_session] = error_db_session

        search_data = {"name": "Test Search"}
        headers = {"x-user-id": "user123"}

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/saved-searches/", json=search_data, headers=headers
                )
            assert response.status_code == 500
            assert "Failed to create saved search" in response.json()["detail"]
        finally:
            # Clean up the override
            app.dependency_overrides.clear()


class TestListSavedSearches:
    """Test list saved searches endpoint."""

    @pytest.mark.asyncio
    async def test_list_saved_searches_success(
        self, mock_analytics_service, sample_saved_search
    ):
        """Test successful listing of saved searches."""
        from jd_ingestion.database.connection import get_async_session
        from jd_ingestion.api.main import app

        # Set up mock database session with proper async mocking
        async def mock_db_session():
            mock_db = AsyncMock()

            # Mock the count query result
            mock_count_result = Mock()
            mock_count_result.scalar_one.return_value = 1

            # Mock the search results
            mock_search_result = Mock()
            mock_search_result.scalars.return_value.all.return_value = [
                sample_saved_search
            ]

            # Set up side_effect to return count first, then search results
            mock_db.execute.side_effect = [
                mock_count_result,
                mock_search_result,
            ]

            return mock_db

        app.dependency_overrides[get_async_session] = mock_db_session

        headers = {"x-user-id": "user123", "x-session-id": "session123"}

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get("/api/saved-searches/", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["searches"]) == 1
            assert data["searches"][0]["name"] == "Test Search"
            assert "pagination" in data
        finally:
            # Clean up the override
            app.dependency_overrides.clear()

        mock_analytics_service.track_activity.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_saved_searches_with_filters(self, mock_analytics_service):
        """Test listing saved searches with filters."""
        from jd_ingestion.database.connection import get_async_session
        from jd_ingestion.api.main import app

        async def mock_db_session():
            mock_db = AsyncMock()

            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = []

            mock_count_result = Mock()
            mock_count_result.scalar_one.return_value = 0
            mock_db.execute.side_effect = [mock_count_result, mock_result]

            return mock_db

        app.dependency_overrides[get_async_session] = mock_db_session

        headers = {"x-user-id": "user123"}
        params = {
            "skip": 10,
            "limit": 25,
            "search_type": "semantic",
            "is_favorite": True,
        }

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get(
                    "/api/saved-searches/", headers=headers, params=params
                )
            assert response.status_code == 200
            data = response.json()
            assert data["pagination"]["skip"] == 10
            assert data["pagination"]["limit"] == 25
        finally:
            # Clean up the override
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_saved_searches_no_headers(self):
        """Test listing saved searches without required headers."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/saved-searches/")

        assert response.status_code == 400
        assert (
            "x-user-id or x-session-id header is required" in response.json()["detail"]
        )

    @pytest.mark.asyncio
    async def test_list_saved_searches_error(self):
        """Test listing saved searches with database error."""
        from jd_ingestion.database.connection import get_async_session
        from jd_ingestion.api.main import app

        async def error_db_session():
            mock_db = AsyncMock()
            mock_db.execute.side_effect = Exception("Database error")
            return mock_db

        app.dependency_overrides[get_async_session] = error_db_session

        headers = {"x-user-id": "user123"}

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get("/api/saved-searches/", headers=headers)
            assert response.status_code == 500
            assert "Failed to list saved searches" in response.json()["detail"]
        finally:
            # Clean up the override
            app.dependency_overrides.clear()


class TestGetSavedSearch:
    """Test get saved search endpoint."""

    @pytest.mark.asyncio
    async def test_get_saved_search_success(
        self,
        mock_analytics_service,
        override_get_async_session,
        mock_db_session,
        sample_saved_search,
    ):
        """Test successful retrieval of a saved search."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        # Setup mock database response
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_saved_search
        mock_db_session.execute.return_value = mock_result

        headers = {"x-user-id": "user123", "x-session-id": "session123"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/saved-searches/1", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["search"]["name"] == "Test Search"
        assert data["search"]["id"] == 1

        mock_analytics_service.track_activity.assert_called_once()

        # Clean up overrides
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_saved_search_not_found(self):
        """Test getting non-existent saved search."""
        from jd_ingestion.database.connection import get_async_session
        from jd_ingestion.api.main import app

        async def mock_db_session():
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            return mock_db

        app.dependency_overrides[get_async_session] = mock_db_session

        headers = {"x-user-id": "user123"}

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get("/api/saved-searches/999", headers=headers)
            assert response.status_code == 404
            assert "Saved search not found" in response.json()["detail"]
        finally:
            # Clean up the override
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_saved_search_access_denied(self, sample_saved_search):
        """Test access denied to saved search."""
        from jd_ingestion.database.connection import get_async_session
        from jd_ingestion.api.main import app

        async def mock_db_session():
            mock_db = AsyncMock()

            # Make search private and owned by different user
            sample_saved_search.user_id = "different_user"
            sample_saved_search.is_public = "false"

            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = sample_saved_search
            mock_db.execute.return_value = mock_result
            return mock_db

        app.dependency_overrides[get_async_session] = mock_db_session

        headers = {"x-user-id": "user123"}

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get("/api/saved-searches/1", headers=headers)
            assert response.status_code == 403
            assert "Access denied to this saved search" in response.json()["detail"]
        finally:
            # Clean up the override
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_public_saved_search(
        self, mock_analytics_service, sample_saved_search
    ):
        """Test getting public saved search by different user."""
        from jd_ingestion.database.connection import get_async_session
        from jd_ingestion.api.main import app

        async def mock_db_session():
            mock_db = AsyncMock()

            # Make search public
            sample_saved_search.is_public = "true"
            sample_saved_search.user_id = "different_user"

            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = sample_saved_search
            mock_db.execute.return_value = mock_result
            return mock_db

        app.dependency_overrides[get_async_session] = mock_db_session

        headers = {"x-user-id": "user123"}

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get("/api/saved-searches/1", headers=headers)
            assert response.status_code == 200
        finally:
            # Clean up the override
            app.dependency_overrides.clear()


class TestUpdateSavedSearch:
    """Test update saved search endpoint."""

    @pytest.mark.asyncio
    async def test_update_saved_search_success(
        self, mock_analytics_service, sample_saved_search
    ):
        """Test successful saved search update."""
        from jd_ingestion.database.connection import get_async_session
        from jd_ingestion.api.main import app

        async def mock_db_session():
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = sample_saved_search
            mock_db.execute.return_value = mock_result
            return mock_db

        app.dependency_overrides[get_async_session] = mock_db_session

        update_data = {
            "name": "Updated Search",
            "description": "Updated description",
            "is_favorite": False,
        }
        headers = {"x-user-id": "user123"}

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.put(
                    "/api/saved-searches/1", json=update_data, headers=headers
                )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "search" in data
            mock_analytics_service.track_activity.assert_called_once()
        finally:
            # Clean up the override
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_saved_search_not_found(self):
        """Test updating non-existent saved search."""
        from jd_ingestion.database.connection import get_async_session
        from jd_ingestion.api.main import app

        async def mock_db_session():
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            return mock_db

        app.dependency_overrides[get_async_session] = mock_db_session

        update_data = {"name": "Updated Search"}
        headers = {"x-user-id": "user123"}

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.put(
                    "/api/saved-searches/999", json=update_data, headers=headers
                )
            assert response.status_code == 404
            assert "Saved search not found" in response.json()["detail"]
        finally:
            # Clean up the override
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_saved_search_permission_denied(self, sample_saved_search):
        """Test updating saved search without permission."""
        from jd_ingestion.database.connection import get_async_session
        from jd_ingestion.api.main import app

        async def mock_db_session():
            mock_db = AsyncMock()

            # Make search owned by different user
            sample_saved_search.user_id = "different_user"

            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = sample_saved_search
            mock_db.execute.return_value = mock_result
            return mock_db

        app.dependency_overrides[get_async_session] = mock_db_session

        update_data = {"name": "Updated Search"}
        headers = {"x-user-id": "user123"}

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.put(
                    "/api/saved-searches/1", json=update_data, headers=headers
                )
            assert response.status_code == 403
            assert (
                "Permission denied to update this saved search"
                in response.json()["detail"]
            )
        finally:
            # Clean up the override
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_saved_search_partial_update(
        self, mock_analytics_service, sample_saved_search
    ):
        """Test partial update of saved search."""
        from jd_ingestion.database.connection import get_async_session
        from jd_ingestion.api.main import app

        async def mock_db_session():
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = sample_saved_search
            mock_db.execute.return_value = mock_result
            return mock_db

        app.dependency_overrides[get_async_session] = mock_db_session

        # Update only one field
        update_data = {"is_favorite": False}
        headers = {"x-user-id": "user123"}

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.put(
                    "/api/saved-searches/1", json=update_data, headers=headers
                )
            assert response.status_code == 200
        finally:
            # Clean up the override
            app.dependency_overrides.clear()


class TestDeleteSavedSearch:
    """Test delete saved search endpoint."""

    @pytest.mark.asyncio
    async def test_delete_saved_search_success(
        self,
        mock_analytics_service,
        override_get_async_session,
        sample_saved_search,
        mock_db_session,
    ):
        """Test successful saved search deletion."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_saved_search
        mock_db_session.execute.return_value = mock_result

        headers = {"x-user-id": "user123"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.delete("/api/saved-searches/1", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "deleted successfully" in data["message"]

        mock_db_session.delete.assert_called_once_with(sample_saved_search)
        mock_analytics_service.track_activity.assert_called_once()

        # Clean up overrides
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_saved_search_not_found(
        self, override_get_async_session, mock_db_session
    ):
        """Test deleting non-existent saved search."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        headers = {"x-user-id": "user123"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.delete("/api/saved-searches/999", headers=headers)

        assert response.status_code == 404
        assert "Saved search not found" in response.json()["detail"]

        # Clean up overrides
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_saved_search_permission_denied(
        self, override_get_async_session, sample_saved_search, mock_db_session
    ):
        """Test deleting saved search without permission."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        # Make search owned by different user
        sample_saved_search.user_id = "different_user"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_saved_search
        mock_db_session.execute.return_value = mock_result

        headers = {"x-user-id": "user123"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.delete("/api/saved-searches/1", headers=headers)

        assert response.status_code == 403
        assert (
            "Permission denied to delete this saved search" in response.json()["detail"]
        )

        # Clean up overrides
        app.dependency_overrides.clear()


class TestExecuteSavedSearch:
    """Test execute saved search endpoint."""

    @pytest.mark.asyncio
    async def test_execute_saved_search_success(
        self,
        mock_analytics_service,
        override_get_async_session,
        sample_saved_search,
        mock_db_session,
    ):
        """Test successful saved search execution."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_saved_search
        mock_db_session.execute.return_value = mock_result

        headers = {"x-user-id": "user123"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post("/api/saved-searches/1/execute", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "search" in data
        assert "execution_info" in data
        assert "use_count" in data["execution_info"]
        assert "redirect_url" in data["execution_info"]

        mock_analytics_service.track_activity.assert_called_once()

        # Clean up overrides
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_execute_saved_search_not_found(
        self, override_get_async_session, mock_db_session
    ):
        """Test executing non-existent saved search."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        headers = {"x-user-id": "user123"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post("/api/saved-searches/999/execute", headers=headers)

        assert response.status_code == 404
        assert "Saved search not found" in response.json()["detail"]

        # Clean up overrides
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_execute_saved_search_access_denied(
        self, override_get_async_session, sample_saved_search, mock_db_session
    ):
        """Test executing saved search without access."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        # Make search private and owned by different user
        sample_saved_search.user_id = "different_user"
        sample_saved_search.is_public = "false"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_saved_search
        mock_db_session.execute.return_value = mock_result

        headers = {"x-user-id": "user123"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post("/api/saved-searches/1/execute", headers=headers)

        assert response.status_code == 403
        assert "Access denied to this saved search" in response.json()["detail"]

        # Clean up overrides
        app.dependency_overrides.clear()


class TestGetPopularPublicSearches:
    """Test get popular public searches endpoint."""

    @pytest.mark.asyncio
    async def test_get_popular_public_searches_success(
        self, override_get_async_session, sample_saved_search, mock_db_session
    ):
        """Test successful retrieval of popular public searches."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        # Make search public
        sample_saved_search.is_public = "true"

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_saved_search]
        mock_db_session.execute.return_value = mock_result

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/saved-searches/public/popular?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "popular_searches" in data
        assert len(data["popular_searches"]) == 1
        assert data["popular_searches"][0]["name"] == "Test Search"

        # Clean up overrides
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_popular_public_searches_empty(
        self, override_get_async_session, mock_db_session
    ):
        """Test getting popular public searches when none exist."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/saved-searches/public/popular")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["popular_searches"]) == 0

        # Clean up overrides
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_popular_public_searches_limit_validation(self):
        """Test limit parameter validation."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/saved-searches/public/popular?limit=100")

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_popular_public_searches_error(
        self, override_get_async_session, mock_db_session
    ):
        """Test error handling for popular public searches."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        _mock_db = AsyncMock()
        mock_db_session.execute.side_effect = Exception("Database error")

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/saved-searches/public/popular")

        assert response.status_code == 500
        assert "Failed to get popular searches" in response.json()["detail"]

        # Clean up overrides
        app.dependency_overrides.clear()


class TestUserPreferences:
    """Test user preferences endpoints."""

    @pytest.mark.asyncio
    async def test_set_user_preference_success(
        self, override_get_async_session, mock_db_session
    ):
        """Test successful user preference setting."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        # Mock no existing preference
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Mock new preference creation
        mock_pref = Mock()
        mock_pref.id = 1

        preference_data = {
            "preference_type": "ui",
            "preference_key": "theme",
            "preference_value": "dark",
        }
        headers = {"x-user-id": "user123"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/saved-searches/preferences", json=preference_data, headers=headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["preference"]["preference_type"] == "ui"
        assert data["preference"]["preference_key"] == "theme"
        assert data["preference"]["preference_value"] == "dark"

        # Clean up overrides
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_set_user_preference_update_existing(
        self, override_get_async_session, sample_user_preference, mock_db_session
    ):
        """Test updating existing user preference."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        # Mock existing preference
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user_preference
        mock_db_session.execute.return_value = mock_result

        preference_data = {
            "preference_type": "ui",
            "preference_key": "theme",
            "preference_value": "light",
        }
        headers = {"x-user-id": "user123"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/saved-searches/preferences", json=preference_data, headers=headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["preference"]["preference_value"] == "light"

        # Clean up overrides
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_set_user_preference_no_headers(self):
        """Test setting user preference without required headers."""
        preference_data = {
            "preference_type": "ui",
            "preference_key": "theme",
            "preference_value": "dark",
        }

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/saved-searches/preferences", json=preference_data
            )

        assert response.status_code == 400
        assert (
            "x-user-id or x-session-id header is required" in response.json()["detail"]
        )

    @pytest.mark.asyncio
    async def test_get_user_preferences_success(
        self, override_get_async_session, sample_user_preference, mock_db_session
    ):
        """Test successful user preferences retrieval."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_user_preference]
        mock_db_session.execute.return_value = mock_result

        headers = {"x-user-id": "user123"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/saved-searches/preferences/ui", headers=headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "preferences" in data
        assert len(data["preferences"]) == 1
        assert data["preferences"][0]["preference_key"] == "theme"

        # Clean up overrides
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_user_preferences_empty(
        self, override_get_async_session, mock_db_session
    ):
        """Test getting user preferences when none exist."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        headers = {"x-session-id": "session123"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/saved-searches/preferences/ui", headers=headers
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["preferences"]) == 0

        # Clean up overrides
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_user_preferences_no_headers(self):
        """Test getting user preferences without required headers."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/saved-searches/preferences/ui")

        assert response.status_code == 400
        assert (
            "x-user-id or x-session-id header is required" in response.json()["detail"]
        )


class TestSavedSearchesEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_get_user_session_function(self):
        """Test get_user_session utility function."""
        from jd_ingestion.api.endpoints.saved_searches import get_user_session

        # Mock request with headers
        request = Mock()
        request.headers = {"x-user-id": "user123", "x-session-id": "session123"}

        result = get_user_session(request)
        assert result["user_id"] == "user123"
        assert result["session_id"] == "session123"

        # Mock request without headers
        request.headers = {}
        result = get_user_session(request)
        assert result["user_id"] is None
        assert result["session_id"] is None

    @pytest.mark.asyncio
    async def test_search_permission_logic_session_only(
        self,
        mock_analytics_service,
        override_get_async_session,
        sample_saved_search,
        mock_db_session,
    ):
        """Test permission logic for session-only users."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        _mock_db = AsyncMock()

        # Make search owned by session only
        sample_saved_search.user_id = None
        sample_saved_search.session_id = "session123"
        sample_saved_search.is_public = "false"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_saved_search
        mock_db_session.execute.return_value = mock_result

        # Access with same session
        headers = {"x-session-id": "session123"}
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/saved-searches/1", headers=headers)
        assert response.status_code == 200

        # Access with different session
        headers = {"x-session-id": "different_session"}
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/saved-searches/1", headers=headers)
        assert response.status_code == 403

        # Clean up overrides
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_search_filters_in_list_endpoint(
        self, mock_analytics_service, override_get_async_session, mock_db_session
    ):
        """Test search filtering logic in list endpoint."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        _mock_db = AsyncMock()

        # Mock empty results for filters test
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        mock_count_result = Mock()
        mock_count_result.scalar_one.return_value = 0
        mock_db_session.execute.side_effect = [mock_count_result, mock_result]

        headers = {"x-user-id": "user123"}

        # Test search type filter
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/saved-searches/?search_type=semantic", headers=headers
            )
        assert response.status_code == 200

        # Test favorite filter
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/saved-searches/?is_favorite=true", headers=headers
            )
        assert response.status_code == 200

        # Test pagination
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/saved-searches/?skip=20&limit=5", headers=headers
            )
        assert response.status_code == 200

        # Clean up overrides
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_analytics_tracking_calls(
        self,
        mock_analytics_service,
        override_get_async_session,
        sample_saved_search,
        mock_db_session,
    ):
        """Test that analytics tracking is called with correct parameters."""
        # Clear any existing overrides first
        app.dependency_overrides.clear()

        # Override the database dependency
        from jd_ingestion.database.connection import get_async_session

        app.dependency_overrides[get_async_session] = override_get_async_session

        _mock_db = AsyncMock()

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_saved_search
        mock_db_session.execute.return_value = mock_result

        headers = {"x-user-id": "user123", "x-session-id": "session123"}

        # Test get saved search analytics
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/saved-searches/1", headers=headers)
        assert response.status_code == 200

        # Verify analytics call
        mock_analytics_service.track_activity.assert_called_once()
        call_kwargs = mock_analytics_service.track_activity.call_args[1]
        assert call_kwargs["action_type"] == "view_saved_search"
        assert call_kwargs["resource_id"] == "1"
        assert call_kwargs["user_id"] == "user123"
        assert call_kwargs["session_id"] == "session123"

        # Clean up overrides
        app.dependency_overrides.clear()
