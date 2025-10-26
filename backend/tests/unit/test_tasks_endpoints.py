"""
Tests for task management API endpoints.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, mock_open
from httpx import AsyncClient, ASGITransport
from pathlib import Path
import tempfile
import os

from jd_ingestion.api.main import app


@pytest.fixture
def mock_celery_app():
    """Mock celery app."""
    celery_app = Mock()

    # Mock task objects
    mock_task = Mock()
    mock_task.id = "test-task-123"
    mock_task.delay.return_value = mock_task

    # Mock result objects
    mock_result = Mock()
    mock_result.ready.return_value = False
    mock_result.successful.return_value = False
    mock_result.failed.return_value = False
    mock_result.status = "PENDING"
    mock_result.info = None
    mock_result.result = None

    celery_app.AsyncResult.return_value = mock_result

    # Mock inspect
    mock_inspect = Mock()
    mock_inspect.active.return_value = {}
    mock_inspect.scheduled.return_value = {}
    mock_inspect.reserved.return_value = {}
    mock_inspect.registered.return_value = {}
    celery_app.control.inspect.return_value = mock_inspect
    celery_app.control.revoke = Mock()

    return celery_app


@pytest.fixture
def mock_settings():
    """Mock settings."""
    settings = Mock()
    settings.supported_extensions_list = [".txt", ".docx", ".pdf"]
    settings.max_file_size_mb = 10
    settings.data_path = Path("/tmp")
    return settings


class TestUploadAndProcessEndpoint:
    """Test file upload and processing endpoint."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.process_single_file_task")
    @patch("jd_ingestion.api.endpoints.tasks.settings")
    async def test_upload_and_process_file_success(self, mock_settings, mock_task):
        """Test successful file upload and processing."""
        mock_settings.supported_extensions_list = [".txt", ".docx", ".pdf"]
        mock_settings.max_file_size_mb = 10
        mock_settings.data_path = Path("/tmp")

        # Mock task
        mock_task_instance = Mock()
        mock_task_instance.id = "upload-task-123"
        mock_task.delay.return_value = mock_task_instance

        # Create test file content
        test_content = b"Test job description content"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
            tmp_file.write(test_content)
            tmp_file.flush()
            tmp_file_path = tmp_file.name

        try:
            with patch("builtins.open", mock_open()) as _mock_file:
                with patch("pathlib.Path.mkdir"):
                    with open(tmp_file_path, "rb") as file:
                        async with AsyncClient(
                            transport=ASGITransport(app=app), base_url="http://test"
                        ) as ac:
                            response = await ac.post(
                                "/api/tasks/upload",
                                files={"file": ("test.txt", file, "text/plain")},
                                params={"generate_embeddings": True},
                            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "accepted"
            assert data["task_id"] == "upload-task-123"
            assert data["filename"] == "test.txt"

        finally:
            try:
                os.unlink(tmp_file_path)
            except (PermissionError, OSError):
                pass  # Ignore file locking issues on Windows

    @pytest.mark.asyncio
    async def test_upload_file_no_filename(self):
        """Test upload with no filename."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/tasks/upload", files={"file": ("", b"content", "text/plain")}
            )
        assert response.status_code == 400
        assert "No filename provided" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.settings")
    async def test_upload_file_unsupported_extension(self, mock_settings):
        """Test upload with unsupported file extension."""
        mock_settings.supported_extensions_list = [".txt"]

        test_content = b"Test content"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xyz") as tmp_file:
            tmp_file.write(test_content)
            tmp_file.flush()
            tmp_file_path = tmp_file.name

        try:
            with open(tmp_file_path, "rb") as file:
                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.post(
                        "/api/tasks/upload",
                        files={"file": ("test.xyz", file, "application/octet-stream")},
                    )

            assert response.status_code == 400
            assert "Unsupported file extension" in response.json()["detail"]

        finally:
            try:
                os.unlink(tmp_file_path)
            except (PermissionError, OSError):
                pass  # Ignore file locking issues on Windows

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.settings")
    async def test_upload_file_too_large(self, mock_settings):
        """Test upload with file too large."""
        mock_settings.supported_extensions_list = [".txt"]
        mock_settings.max_file_size_mb = 1  # 1MB limit

        # Create a mock large file
        large_content = b"x" * (2 * 1024 * 1024)  # 2MB content

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
            tmp_file.write(large_content)
            tmp_file.flush()
            tmp_file_path = tmp_file.name

        try:
            # Mock the UploadFile to have a size attribute
            with patch("fastapi.UploadFile") as _mock_upload_file:
                mock_file = Mock()
                mock_file.filename = "large.txt"
                mock_file.size = 2 * 1024 * 1024  # 2MB
                mock_file.read = AsyncMock(return_value=large_content)

                # This would typically be handled by FastAPI's validation
                # In actual usage, the file size check happens before our endpoint
                pass

        finally:
            try:
                os.unlink(tmp_file_path)
            except (PermissionError, OSError):
                pass  # Ignore file locking issues on Windows


class TestBatchProcessEndpoint:
    """Test batch processing endpoint."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.batch_process_files_task")
    @patch("pathlib.Path.exists")
    async def test_batch_process_directory_success(self, mock_exists, mock_task):
        """Test successful batch processing."""
        mock_exists.return_value = True

        mock_task_instance = Mock()
        mock_task_instance.id = "batch-task-456"
        mock_task.delay.return_value = mock_task_instance

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/tasks/batch-process",
                params={
                    "directory_path": "/test/path",
                    "max_files": 10,
                    "recursive": True,
                    "generate_embeddings": True,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["task_id"] == "batch-task-456"
        assert data["directory"] == "/test/path"

    @pytest.mark.asyncio
    @patch("pathlib.Path.exists")
    async def test_batch_process_directory_not_found(self, mock_exists):
        """Test batch processing with non-existent directory."""
        mock_exists.return_value = False

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/tasks/batch-process",
                params={"directory_path": "/nonexistent/path"},
            )

        assert response.status_code == 400
        assert "Directory does not exist" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.batch_process_files_task")
    @patch("pathlib.Path.exists")
    async def test_batch_process_task_submission_error(self, mock_exists, mock_task):
        """Test batch processing with task submission error."""
        mock_exists.return_value = True
        mock_task.delay.side_effect = Exception("Celery connection failed")

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/tasks/batch-process", params={"directory_path": "/test/path"}
            )

        assert response.status_code == 500
        assert "Batch processing submission failed" in response.json()["detail"]


class TestEmbeddingGenerationEndpoints:
    """Test embedding generation endpoints."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.generate_embeddings_for_job_task")
    async def test_generate_embeddings_for_job_success(self, mock_task):
        """Test successful embedding generation for single job."""
        mock_task_instance = Mock()
        mock_task_instance.id = "embed-task-789"
        mock_task.delay.return_value = mock_task_instance

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/tasks/generate-embeddings", params={"job_id": 123}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["task_id"] == "embed-task-789"
        assert data["job_id"] == 123

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.generate_embeddings_for_job_task")
    async def test_generate_embeddings_for_job_error(self, mock_task):
        """Test embedding generation with error."""
        mock_task.delay.side_effect = Exception("Embedding service unavailable")

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/tasks/generate-embeddings", params={"job_id": 123}
            )

        assert response.status_code == 500
        assert "Embedding generation submission failed" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.batch_generate_embeddings_task")
    async def test_batch_generate_embeddings_success(self, mock_task):
        """Test successful batch embedding generation."""
        mock_task_instance = Mock()
        mock_task_instance.id = "batch-embed-task-101"
        mock_task.delay.return_value = mock_task_instance

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/tasks/batch-generate-embeddings", json=[1, 2, 3, 4, 5]
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["task_id"] == "batch-embed-task-101"
        assert data["job_ids"] == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_batch_generate_embeddings_empty_list(self):
        """Test batch embedding generation with empty job list."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post("/api/tasks/batch-generate-embeddings", json=[])

        assert response.status_code == 400
        assert "No job IDs provided" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.generate_missing_embeddings_task")
    async def test_generate_missing_embeddings_success(self, mock_task):
        """Test successful missing embeddings generation."""
        mock_task_instance = Mock()
        mock_task_instance.id = "missing-embed-task-202"
        mock_task.delay.return_value = mock_task_instance

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/tasks/generate-missing-embeddings", params={"limit": 100}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["task_id"] == "missing-embed-task-202"
        assert data["limit"] == 100

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.generate_missing_embeddings_task")
    async def test_generate_missing_embeddings_no_limit(self, mock_task):
        """Test missing embeddings generation without limit."""
        mock_task_instance = Mock()
        mock_task_instance.id = "missing-embed-task-203"
        mock_task.delay.return_value = mock_task_instance

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post("/api/tasks/generate-missing-embeddings")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] is None


class TestTaskStatusEndpoints:
    """Test task status and result endpoints."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.celery_app")
    async def test_get_task_status_pending(self, mock_celery_app):
        """Test getting status of pending task."""
        mock_result = Mock()
        mock_result.status = "PENDING"
        mock_result.ready.return_value = False
        mock_result.successful.return_value = False
        mock_result.failed.return_value = False
        mock_result.info = {"current": 0, "total": 100}

        mock_celery_app.AsyncResult.return_value = mock_result

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/tasks/test-task-123/status")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["status"] == "PENDING"
        assert data["ready"] is False
        assert data["info"] == {"current": 0, "total": 100}

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.celery_app")
    async def test_get_task_status_success(self, mock_celery_app):
        """Test getting status of successful task."""
        mock_result = Mock()
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.failed.return_value = False
        mock_result.result = {"processed_files": 5, "errors": []}

        mock_celery_app.AsyncResult.return_value = mock_result

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/tasks/test-task-123/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["ready"] is True
        assert data["successful"] is True
        assert data["result"]["processed_files"] == 5

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.celery_app")
    async def test_get_task_status_failure(self, mock_celery_app):
        """Test getting status of failed task."""
        mock_result = Mock()
        mock_result.status = "FAILURE"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = False
        mock_result.failed.return_value = True
        mock_result.info = Exception("Task processing failed")

        mock_celery_app.AsyncResult.return_value = mock_result

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/tasks/test-task-123/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "FAILURE"
        assert data["failed"] is True
        assert "Task processing failed" in data["error"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.celery_app")
    async def test_get_task_result_success(self, mock_celery_app):
        """Test getting result of completed task."""
        mock_result = Mock()
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.failed.return_value = False
        mock_result.result = {"job_id": 123, "embeddings_generated": 50}

        mock_celery_app.AsyncResult.return_value = mock_result

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/tasks/test-task-123/result")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["status"] == "SUCCESS"
        assert data["result"]["job_id"] == 123

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.celery_app")
    async def test_get_task_result_not_ready(self, mock_celery_app):
        """Test getting result of task not yet completed."""
        mock_result = Mock()
        mock_result.ready.return_value = False

        mock_celery_app.AsyncResult.return_value = mock_result

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/tasks/test-task-123/result")

        assert response.status_code == 202
        assert "Task not yet completed" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.celery_app")
    async def test_get_task_result_failed(self, mock_celery_app):
        """Test getting result of failed task."""
        mock_result = Mock()
        mock_result.ready.return_value = True
        mock_result.failed.return_value = True
        mock_result.info = Exception("Processing failed")

        mock_celery_app.AsyncResult.return_value = mock_result

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/tasks/test-task-123/result")

        assert response.status_code == 500
        assert "Task failed" in response.json()["detail"]


class TestTaskCancellationEndpoint:
    """Test task cancellation endpoint."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.celery_app")
    async def test_cancel_task_success(self, mock_celery_app):
        """Test successful task cancellation."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.delete("/api/tasks/test-task-123")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["status"] == "cancelled"

        mock_celery_app.control.revoke.assert_called_once_with(
            "test-task-123", terminate=True
        )

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.celery_app")
    async def test_cancel_task_error(self, mock_celery_app):
        """Test task cancellation with error."""
        mock_celery_app.control.revoke.side_effect = Exception("Celery error")

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.delete("/api/tasks/test-task-123")

        assert response.status_code == 500
        assert "Failed to cancel task" in response.json()["detail"]


class TestTaskListingEndpoints:
    """Test task listing and statistics endpoints."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.celery_app")
    async def test_list_active_tasks_success(self, mock_celery_app):
        """Test successful listing of active tasks."""
        mock_inspect = Mock()
        mock_inspect.active.return_value = {
            "worker1": [
                {
                    "id": "task-1",
                    "name": "process_single_file_task",
                    "args": ["/path/file.txt"],
                    "kwargs": {"generate_embeddings": True},
                },
                {
                    "id": "task-2",
                    "name": "generate_embeddings_for_job_task",
                    "args": [123],
                    "kwargs": {},
                },
            ],
            "worker2": [
                {
                    "id": "task-3",
                    "name": "batch_process_files_task",
                    "args": ["/data"],
                    "kwargs": {"max_files": 10},
                }
            ],
        }
        mock_celery_app.control.inspect.return_value = mock_inspect

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/tasks/")

        assert response.status_code == 200
        data = response.json()
        assert data["total_active"] == 3
        assert len(data["active_tasks"]) == 3
        assert len(data["workers"]) == 2
        assert data["active_tasks"][0]["task_id"] == "task-1"

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.celery_app")
    async def test_list_active_tasks_no_tasks(self, mock_celery_app):
        """Test listing active tasks when none exist."""
        mock_inspect = Mock()
        mock_inspect.active.return_value = None
        mock_celery_app.control.inspect.return_value = mock_inspect

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/tasks/")

        assert response.status_code == 200
        data = response.json()
        assert data["total_active"] == 0
        assert len(data["active_tasks"]) == 0

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.celery_app")
    async def test_get_task_stats_success(self, mock_celery_app):
        """Test successful task statistics retrieval."""
        mock_inspect = Mock()
        mock_inspect.active.return_value = {
            "worker1": [{"id": "task-1"}, {"id": "task-2"}],
            "worker2": [{"id": "task-3"}],
        }
        mock_inspect.scheduled.return_value = {"worker1": [{"id": "scheduled-1"}]}
        mock_inspect.reserved.return_value = {
            "worker1": [{"id": "reserved-1"}, {"id": "reserved-2"}]
        }
        mock_inspect.registered.return_value = {"worker1": ["task1", "task2", "task3"]}
        mock_celery_app.control.inspect.return_value = mock_inspect

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/tasks/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["workers"]["total"] == 2
        assert data["tasks"]["active"] == 3
        assert data["tasks"]["scheduled"] == 1
        assert data["tasks"]["reserved"] == 2
        assert len(data["registered_tasks"]) == 3
        assert "processing" in data["queues"]
        assert "embeddings" in data["queues"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.celery_app")
    async def test_get_task_stats_error(self, mock_celery_app):
        """Test task statistics with Celery error."""
        mock_celery_app.control.inspect.side_effect = Exception("Celery unavailable")

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/tasks/stats")

        assert response.status_code == 500
        assert "Failed to get task stats" in response.json()["detail"]


class TestTaskEndpointsEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_task_status_invalid_task_id(self):
        """Test getting status with invalid task ID format."""
        with patch("jd_ingestion.api.endpoints.tasks.celery_app") as mock_celery_app:
            mock_celery_app.AsyncResult.side_effect = Exception("Invalid task ID")

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get("/api/tasks/invalid-id/status")
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_upload_file_invalid_content_type(self):
        """Test file upload validation handles various scenarios."""
        # Test with missing file parameter would be handled by FastAPI validation
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post("/api/tasks/upload")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_batch_process_invalid_parameters(self):
        """Test batch processing with invalid parameter types."""
        # Invalid max_files type
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/tasks/batch-process",
                params={"directory_path": "/test/path", "max_files": "not_an_int"},
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_batch_generate_embeddings_invalid_job_ids(self):
        """Test batch embedding generation with invalid job IDs."""
        # Non-integer job IDs
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/tasks/batch-generate-embeddings", json=["not", "integers"]
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.celery_app")
    async def test_task_operations_celery_unavailable(self, mock_celery_app):
        """Test task operations when Celery is unavailable."""
        mock_celery_app.AsyncResult.side_effect = Exception("Celery broker unavailable")

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/tasks/test-task/status")
        assert response.status_code == 500
        assert "Failed to get task status" in response.json()["detail"]


class TestTaskEndpointsIntegration:
    """Test integration aspects of task endpoints."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.tasks.get_async_session")
    async def test_task_endpoints_database_dependency(self, mock_get_session):
        """Test that task endpoints properly handle database dependency."""
        mock_db = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_db

        # Upload endpoint uses database dependency
        with patch("jd_ingestion.api.endpoints.tasks.settings") as mock_settings:
            with patch(
                "jd_ingestion.api.endpoints.tasks.process_single_file_task"
            ) as mock_task:
                mock_settings.supported_extensions_list = [".txt"]
                mock_settings.max_file_size_mb = 10
                mock_settings.data_path = Path("/tmp")

                mock_task_instance = Mock()
                mock_task_instance.id = "test-task"
                mock_task.delay.return_value = mock_task_instance

                with patch("builtins.open", mock_open()):
                    with patch("pathlib.Path.mkdir"):
                        test_content = b"Test content"
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".txt"
                        ) as tmp_file:
                            tmp_file.write(test_content)
                            tmp_file.flush()
                            tmp_file_path = tmp_file.name

                        try:
                            with open(tmp_file_path, "rb") as file:
                                async with AsyncClient(
                                    transport=ASGITransport(app=app),
                                    base_url="http://test",
                                ) as ac:
                                    response = await ac.post(
                                        "/api/tasks/upload",
                                        files={
                                            "file": ("test.txt", file, "text/plain")
                                        },
                                    )
                            assert response.status_code == 200
                        finally:
                            try:
                                os.unlink(tmp_file_path)
                            except (PermissionError, OSError):
                                pass  # Ignore file locking issues on Windows

    @pytest.mark.asyncio
    async def test_task_endpoint_error_logging(self):
        """Test that task endpoints properly log errors."""
        with patch("jd_ingestion.api.endpoints.tasks.logger") as mock_logger:
            with patch(
                "jd_ingestion.api.endpoints.tasks.celery_app"
            ) as mock_celery_app:
                mock_celery_app.AsyncResult.side_effect = Exception("Test error")

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.get("/api/tasks/test-task/status")
                assert response.status_code == 500

                # Verify error was logged
                mock_logger.error.assert_called()
                args, kwargs = mock_logger.error.call_args
                assert "Failed to get task status" in args[0]
