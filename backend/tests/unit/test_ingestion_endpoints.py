"""
Tests for ingestion API endpoints.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
from fastapi.testclient import TestClient
from fastapi import UploadFile
import tempfile
import os

from jd_ingestion.api.main import app
from jd_ingestion.database.models import (
    JobDescription,
    JobSection,
    JobMetadata,
    ContentChunk,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_file_discovery():
    """Mock file discovery service."""
    discovery = Mock()
    discovery.scan_directory = Mock()
    discovery.get_stats = Mock()
    discovery._extract_file_metadata = Mock()
    return discovery


@pytest.fixture
def mock_content_processor():
    """Mock content processor."""
    processor = Mock()
    processor.process_content = Mock()
    processor.chunk_content = Mock()
    return processor


@pytest.fixture
def sample_file_metadata():
    """Sample file metadata for testing."""
    from jd_ingestion.core.file_discovery import FileMetadata

    return FileMetadata(
        file_path=Path("test_file.txt"),
        job_number="12345",
        classification="EX-01",
        language="en",
        title="Test Job",
        file_size=1024,
        file_hash="abc123",
        encoding="utf-8",
        is_valid=True,
        validation_errors=[],
    )


@pytest.fixture
def sample_processed_content():
    """Sample processed content for testing."""
    from dataclasses import dataclass, field
    from typing import Dict, List

    @dataclass
    class MockStructuredFields:
        position_title: str = "Test Position"
        job_number: str = "12345"
        classification: str = "EX-01"
        department: str = "IT Department"
        reports_to: str = "Director"
        location: str = "Ottawa"
        fte_count: float = 1.0
        salary_budget: float = 75000.0

    @dataclass
    class MockProcessedContent:
        cleaned_content: str = "Test content"
        sections: Dict = field(
            default_factory=lambda: {
                "general_accountability": "Test accountability",
                "specific_accountabilities": "Test specific",
            }
        )
        structured_fields: MockStructuredFields = field(
            default_factory=MockStructuredFields
        )
        processing_errors: List = field(default_factory=list)

    return MockProcessedContent()


class TestScanDirectoryEndpoint:
    """Test scan directory endpoint."""

    @patch("jd_ingestion.api.endpoints.ingestion.FileDiscovery")
    def test_scan_directory_success(
        self, mock_file_discovery_class, client, sample_file_metadata
    ):
        """Test successful directory scanning."""
        # Mock FileDiscovery instance
        mock_discovery = Mock()
        mock_discovery.scan_directory.return_value = [sample_file_metadata]
        mock_discovery.get_stats.return_value = {
            "total_files": 1,
            "valid_files": 1,
            "invalid_files": 0,
            "by_extension": {".txt": 1},
            "by_classification": {"EX-01": 1},
        }
        mock_file_discovery_class.return_value = mock_discovery

        response = client.post(
            "/api/ingestion/scan-directory",
            params={"directory_path": "/test/path", "recursive": True},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["directory"] == "/test/path"
        assert data["stats"]["total_files"] == 1
        assert len(data["files"]) == 1
        assert data["files"][0]["job_number"] == "12345"

    def test_scan_directory_nonexistent(self, client):
        """Test scanning non-existent directory."""
        response = client.post(
            "/api/ingestion/scan-directory",
            params={"directory_path": "/nonexistent/path"},
        )
        assert response.status_code == 400
        assert "Directory does not exist" in response.json()["detail"]

    @patch("jd_ingestion.api.endpoints.ingestion.FileDiscovery")
    def test_scan_directory_error(self, mock_file_discovery_class, client):
        """Test directory scanning with error."""
        mock_file_discovery_class.side_effect = Exception("Scan failed")

        response = client.post(
            "/api/ingestion/scan-directory", params={"directory_path": "/test/path"}
        )
        assert response.status_code == 500
        assert "Scan failed" in response.json()["detail"]


class TestProcessFileEndpoint:
    """Test process file endpoint."""

    @patch("jd_ingestion.api.endpoints.ingestion.ContentProcessor")
    @patch("jd_ingestion.api.endpoints.ingestion.FileDiscovery")
    @patch("builtins.open", create=True)
    def test_process_file_success(
        self,
        mock_open,
        mock_file_discovery_class,
        mock_content_processor_class,
        client,
        sample_file_metadata,
        sample_processed_content,
    ):
        """Test successful file processing."""
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "Test file content"
        )

        # Mock FileDiscovery
        mock_discovery = Mock()
        mock_discovery._extract_file_metadata.return_value = sample_file_metadata
        mock_file_discovery_class.return_value = mock_discovery

        # Mock ContentProcessor
        mock_processor = Mock()
        mock_processor.process_content.return_value = sample_processed_content
        mock_processor.chunk_content.return_value = ["chunk1", "chunk2"]
        mock_content_processor_class.return_value = mock_processor

        with patch("pathlib.Path.exists", return_value=True):
            response = client.post(
                "/api/ingestion/process-file",
                params={"file_path": "/test/file.txt", "save_to_db": False},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["file_path"] == "/test/file.txt"
        assert data["processed_content"]["chunks_generated"] == 2

    def test_process_file_nonexistent(self, client):
        """Test processing non-existent file."""
        response = client.post(
            "/api/ingestion/process-file", params={"file_path": "/nonexistent/file.txt"}
        )
        assert response.status_code == 400
        assert "File does not exist" in response.json()["detail"]

    @patch("jd_ingestion.api.endpoints.ingestion.ContentProcessor")
    @patch("jd_ingestion.api.endpoints.ingestion.FileDiscovery")
    @patch("jd_ingestion.api.endpoints.ingestion.embedding_service")
    @patch("builtins.open", create=True)
    def test_process_file_with_database_save(
        self,
        mock_open,
        mock_embedding_service,
        mock_file_discovery_class,
        mock_content_processor_class,
        client,
        sample_file_metadata,
        sample_processed_content,
    ):
        """Test file processing with database save."""
        # Setup mocks
        mock_open.return_value.__enter__.return_value.read.return_value = "Test content"

        mock_discovery = Mock()
        mock_discovery._extract_file_metadata.return_value = sample_file_metadata
        mock_file_discovery_class.return_value = mock_discovery

        mock_processor = Mock()
        mock_processor.process_content.return_value = sample_processed_content
        mock_processor.chunk_content.return_value = ["chunk1", "chunk2"]
        mock_content_processor_class.return_value = mock_processor

        mock_embedding_service.generate_embeddings_batch = AsyncMock(
            return_value=[[0.1, 0.2], [0.3, 0.4]]
        )

        with patch("pathlib.Path.exists", return_value=True):
            with patch(
                "jd_ingestion.api.endpoints.ingestion.get_async_session"
            ) as mock_session:
                mock_db = AsyncMock()
                mock_session.return_value.__aenter__.return_value = mock_db

                # Mock database operations
                mock_job = Mock()
                mock_job.id = 123
                mock_db.add = Mock()
                mock_db.commit = AsyncMock()

                # Mock query execution
                mock_result = Mock()
                mock_chunk = Mock()
                mock_chunk.id = 1
                mock_chunk.chunk_text = "chunk1"
                mock_result.scalars.return_value.all.return_value = [mock_chunk]
                mock_db.execute = AsyncMock(return_value=mock_result)

                response = client.post(
                    "/api/ingestion/process-file",
                    params={"file_path": "/test/file.txt", "save_to_db": True},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["saved_to_database"] is True

    @patch("jd_ingestion.api.endpoints.ingestion.Document")
    @patch("jd_ingestion.api.endpoints.ingestion.FileDiscovery")
    def test_process_docx_file(
        self,
        mock_file_discovery_class,
        mock_document_class,
        client,
        sample_file_metadata,
    ):
        """Test processing .docx file."""
        # Mock docx Document
        mock_doc = Mock()
        mock_paragraph = Mock()
        mock_paragraph.text = "Test paragraph"
        mock_doc.paragraphs = [mock_paragraph]
        mock_document_class.return_value = mock_doc

        # Mock FileDiscovery
        mock_discovery = Mock()
        mock_discovery._extract_file_metadata.return_value = sample_file_metadata
        mock_file_discovery_class.return_value = mock_discovery

        with patch("pathlib.Path.exists", return_value=True):
            with patch(
                "pathlib.Path.suffix",
                new_callable=lambda: property(lambda self: ".docx"),
            ):
                response = client.post(
                    "/api/ingestion/process-file",
                    params={"file_path": "/test/file.docx", "save_to_db": False},
                )

        assert response.status_code == 200

    @patch("jd_ingestion.api.endpoints.ingestion.FileDiscovery")
    def test_process_pdf_file_not_implemented(
        self, mock_file_discovery_class, client, sample_file_metadata
    ):
        """Test processing .pdf file (not yet implemented)."""
        mock_discovery = Mock()
        mock_discovery._extract_file_metadata.return_value = sample_file_metadata
        mock_file_discovery_class.return_value = mock_discovery

        with patch("pathlib.Path.exists", return_value=True):
            with patch(
                "pathlib.Path.suffix",
                new_callable=lambda: property(lambda self: ".pdf"),
            ):
                response = client.post(
                    "/api/ingestion/process-file",
                    params={"file_path": "/test/file.pdf", "save_to_db": False},
                )

        assert response.status_code == 200
        data = response.json()
        assert (
            "PDF content extraction not yet implemented"
            in data["processed_content"]["sections"]
        )


class TestBatchIngestEndpoint:
    """Test batch ingest endpoint."""

    @patch("jd_ingestion.api.endpoints.ingestion.FileDiscovery")
    def test_batch_ingest_success(
        self, mock_file_discovery_class, client, sample_file_metadata
    ):
        """Test successful batch ingestion."""
        mock_discovery = Mock()
        mock_discovery.scan_directory.return_value = [sample_file_metadata]
        mock_file_discovery_class.return_value = mock_discovery

        with patch("pathlib.Path.exists", return_value=True):
            response = client.post(
                "/api/ingestion/batch-ingest",
                params={
                    "directory_path": "/test/path",
                    "recursive": True,
                    "max_files": 10,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert data["files_to_process"] == 1

    @patch("jd_ingestion.api.endpoints.ingestion.FileDiscovery")
    def test_batch_ingest_no_valid_files(self, mock_file_discovery_class, client):
        """Test batch ingestion with no valid files."""
        invalid_metadata = Mock()
        invalid_metadata.is_valid = False

        mock_discovery = Mock()
        mock_discovery.scan_directory.return_value = [invalid_metadata]
        mock_file_discovery_class.return_value = mock_discovery

        with patch("pathlib.Path.exists", return_value=True):
            response = client.post(
                "/api/ingestion/batch-ingest", params={"directory_path": "/test/path"}
            )

        assert response.status_code == 400
        assert "No valid files found" in response.json()["detail"]

    def test_batch_ingest_nonexistent_directory(self, client):
        """Test batch ingestion with non-existent directory."""
        response = client.post(
            "/api/ingestion/batch-ingest",
            params={"directory_path": "/nonexistent/path"},
        )
        assert response.status_code == 400
        assert "Directory does not exist" in response.json()["detail"]


class TestUploadFileEndpoint:
    """Test upload file endpoint."""

    @patch("jd_ingestion.api.endpoints.ingestion.process_single_file")
    @patch("jd_ingestion.api.endpoints.ingestion.settings")
    def test_upload_file_success(self, mock_settings, mock_process_file, client):
        """Test successful file upload."""
        # Mock settings
        mock_settings.supported_extensions_list = [".txt", ".docx", ".pdf"]
        mock_settings.max_file_size_mb = 10
        mock_settings.data_path = Path("/tmp")

        # Mock process_single_file
        mock_process_file.return_value = {
            "status": "success",
            "job_id": 123,
            "metadata": {"job_number": "12345"},
        }

        # Create a test file
        test_content = b"Test file content"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
            tmp_file.write(test_content)
            tmp_file.flush()

            try:
                with open(tmp_file.name, "rb") as file:
                    response = client.post(
                        "/api/ingestion/upload",
                        files={"file": ("test.txt", file, "text/plain")},
                    )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert data["filename"] == "test.txt"
            finally:
                os.unlink(tmp_file.name)

    def test_upload_file_no_filename(self, client):
        """Test upload with no filename."""
        response = client.post(
            "/api/ingestion/upload", files={"file": ("", b"content", "text/plain")}
        )
        assert response.status_code == 400
        assert "No filename provided" in response.json()["detail"]

    @patch("jd_ingestion.api.endpoints.ingestion.settings")
    def test_upload_file_unsupported_extension(self, mock_settings, client):
        """Test upload with unsupported file extension."""
        mock_settings.supported_extensions_list = [".txt"]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xyz") as tmp_file:
            tmp_file.write(b"test content")
            tmp_file.flush()

            try:
                with open(tmp_file.name, "rb") as file:
                    response = client.post(
                        "/api/ingestion/upload",
                        files={"file": ("test.xyz", file, "application/octet-stream")},
                    )

                assert response.status_code == 400
                assert "Unsupported file extension" in response.json()["detail"]
            finally:
                os.unlink(tmp_file.name)

    @patch("jd_ingestion.api.endpoints.ingestion.settings")
    def test_upload_file_too_large(self, mock_settings, client):
        """Test upload with file too large."""
        mock_settings.supported_extensions_list = [".txt"]
        mock_settings.max_file_size_mb = 1  # 1MB limit

        # Create a mock UploadFile with size attribute
        large_file = Mock(spec=UploadFile)
        large_file.filename = "large.txt"
        large_file.size = 2 * 1024 * 1024  # 2MB
        large_file.read = AsyncMock(return_value=b"large content")

        # This test is more complex due to FastAPI's file handling
        # In a real scenario, we'd need to mock the file upload process
        pass  # Placeholder for complex file size testing


class TestIngestionStatsEndpoint:
    """Test ingestion statistics endpoint."""

    def test_get_ingestion_stats_success(self, client):
        """Test successful ingestion statistics retrieval."""
        with patch(
            "jd_ingestion.api.endpoints.ingestion.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock database query results
            mock_result = Mock()
            mock_result.scalar_one.return_value = 100  # total jobs
            mock_result.fetchall.return_value = [("EX-01", 50), ("EX-02", 30)]
            mock_result.scalar_one_or_none.return_value = datetime.now()
            mock_db.execute.return_value = mock_result

            response = client.get("/api/ingestion/stats")
            assert response.status_code == 200

            data = response.json()
            assert "total_jobs" in data
            assert "by_classification" in data
            assert "processing_status" in data
            assert "embedding_stats" in data

    def test_get_ingestion_stats_error(self, client):
        """Test ingestion statistics with database error."""
        with patch(
            "jd_ingestion.api.endpoints.ingestion.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_db.execute.side_effect = Exception("Database error")

            response = client.get("/api/ingestion/stats")
            assert response.status_code == 500
            assert (
                "Failed to retrieve ingestion statistics" in response.json()["detail"]
            )


class TestTaskStatsEndpoint:
    """Test task statistics endpoint."""

    @patch("jd_ingestion.api.endpoints.ingestion.celery_app")
    def test_get_task_stats_success(self, mock_celery_app, client):
        """Test successful task statistics retrieval."""
        # Mock Celery inspect
        mock_inspect = Mock()
        mock_inspect.active.return_value = {
            "worker1": [
                {
                    "name": "process_file",
                    "delivery_info": {"routing_key": "processing"},
                },
                {
                    "name": "generate_embedding",
                    "delivery_info": {"routing_key": "embeddings"},
                },
            ]
        }
        mock_inspect.reserved.return_value = {"worker1": []}
        mock_inspect.scheduled.return_value = {"worker1": []}

        mock_celery_app.control.inspect.return_value = mock_inspect

        response = client.get("/api/ingestion/task-stats")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "task_stats" in data
        assert data["task_stats"]["active_tasks"] == 2
        assert data["task_stats"]["workers_online"] == 1

    @patch("jd_ingestion.api.endpoints.ingestion.celery_app")
    def test_get_task_stats_celery_unavailable(self, mock_celery_app, client):
        """Test task statistics when Celery is unavailable."""
        mock_celery_app.control.inspect.side_effect = Exception("Celery unavailable")

        response = client.get("/api/ingestion/task-stats")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "unavailable"
        assert data["task_stats"]["active_tasks"] == 0


class TestEmbeddingGenerationEndpoint:
    """Test embedding generation endpoint."""

    def test_generate_embeddings_success(self, client):
        """Test successful embedding generation start."""
        with patch(
            "jd_ingestion.api.endpoints.ingestion.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock chunks without embeddings
            mock_chunk = Mock(spec=ContentChunk)
            mock_chunk.id = 1
            mock_chunk.chunk_text = "test chunk"
            mock_chunk.embedding = None

            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = [mock_chunk]
            mock_db.execute.return_value = mock_result

            response = client.post("/api/ingestion/generate-embeddings")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "started"
            assert data["chunks_to_process"] == 1

    def test_generate_embeddings_no_chunks(self, client):
        """Test embedding generation with no chunks to process."""
        with patch(
            "jd_ingestion.api.endpoints.ingestion.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            response = client.post("/api/ingestion/generate-embeddings")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "success"
            assert data["chunks_processed"] == 0

    def test_generate_embeddings_with_job_ids(self, client):
        """Test embedding generation for specific job IDs."""
        with patch(
            "jd_ingestion.api.endpoints.ingestion.get_async_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            response = client.post(
                "/api/ingestion/generate-embeddings",
                params={"job_ids": [1, 2, 3], "force_regenerate": True},
            )
            assert response.status_code == 200


class TestResilienceStatusEndpoint:
    """Test resilience status endpoint."""

    @patch("jd_ingestion.api.endpoints.ingestion.circuit_breaker_manager")
    def test_get_resilience_status_healthy(self, mock_cb_manager, client):
        """Test resilience status when all services are healthy."""
        mock_cb_manager.get_all_metrics.return_value = {
            "openai_api": {"state": "closed", "failure_count": 0},
            "database": {"state": "closed", "failure_count": 0},
        }

        response = client.get("/api/ingestion/resilience-status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["overall_health"] == "healthy"
        assert len(data["degraded_services"]) == 0

    @patch("jd_ingestion.api.endpoints.ingestion.circuit_breaker_manager")
    def test_get_resilience_status_degraded(self, mock_cb_manager, client):
        """Test resilience status when services are degraded."""
        mock_cb_manager.get_all_metrics.return_value = {
            "openai_api": {"state": "open", "failure_count": 5, "recovery_timeout": 60},
            "database": {"state": "closed", "failure_count": 0},
        }

        response = client.get("/api/ingestion/resilience-status")
        assert response.status_code == 200

        data = response.json()
        assert data["overall_health"] == "degraded"
        assert "embedding_service" in data["degraded_services"]
        assert len(data["recommendations"]) > 0

    @patch("jd_ingestion.api.endpoints.ingestion.circuit_breaker_manager")
    def test_get_resilience_status_error(self, mock_cb_manager, client):
        """Test resilience status with error."""
        mock_cb_manager.get_all_metrics.side_effect = Exception("Circuit breaker error")

        response = client.get("/api/ingestion/resilience-status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "error"


class TestCircuitBreakerResetEndpoint:
    """Test circuit breaker reset endpoint."""

    @patch("jd_ingestion.api.endpoints.ingestion.circuit_breaker_manager")
    def test_reset_specific_circuit_breaker(self, mock_cb_manager, client):
        """Test resetting specific circuit breaker."""
        mock_breaker = Mock()
        mock_breaker.reset = Mock()
        mock_cb_manager._breakers = {"openai_api": mock_breaker}

        response = client.post(
            "/api/ingestion/reset-circuit-breakers",
            params={"service_name": "openai_api"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "openai_api" in data["message"]
        mock_breaker.reset.assert_called_once()

    @patch("jd_ingestion.api.endpoints.ingestion.circuit_breaker_manager")
    def test_reset_nonexistent_circuit_breaker(self, mock_cb_manager, client):
        """Test resetting non-existent circuit breaker."""
        mock_cb_manager._breakers = {}

        response = client.post(
            "/api/ingestion/reset-circuit-breakers",
            params={"service_name": "nonexistent"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "error"
        assert "not found" in data["message"]

    @patch("jd_ingestion.api.endpoints.ingestion.circuit_breaker_manager")
    def test_reset_all_circuit_breakers(self, mock_cb_manager, client):
        """Test resetting all circuit breakers."""
        mock_cb_manager.reset_all = Mock()

        response = client.post("/api/ingestion/reset-circuit-breakers")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "All circuit breakers reset" in data["message"]
        mock_cb_manager.reset_all.assert_called_once()

    @patch("jd_ingestion.api.endpoints.ingestion.circuit_breaker_manager")
    def test_reset_circuit_breakers_error(self, mock_cb_manager, client):
        """Test circuit breaker reset with error."""
        mock_cb_manager.reset_all.side_effect = Exception("Reset failed")

        response = client.post("/api/ingestion/reset-circuit-breakers")
        assert response.status_code == 500
        assert "Failed to reset circuit breakers" in response.json()["detail"]


class TestIngestionEndpointsEdgeCases:
    """Test edge cases and error conditions."""

    def test_missing_required_parameters(self, client):
        """Test endpoints with missing required parameters."""
        response = client.post("/api/ingestion/scan-directory")
        assert response.status_code == 422

        response = client.post("/api/ingestion/process-file")
        assert response.status_code == 422

        response = client.post("/api/ingestion/batch-ingest")
        assert response.status_code == 422

    @patch("jd_ingestion.api.endpoints.ingestion.get_async_session")
    def test_database_connection_error(self, mock_session, client):
        """Test handling database connection errors."""
        mock_session.side_effect = Exception("Database connection failed")

        response = client.get("/api/ingestion/stats")
        assert response.status_code == 500

    def test_invalid_file_paths(self, client):
        """Test endpoints with invalid file paths."""
        # Invalid characters in path
        response = client.post(
            "/api/ingestion/process-file", params={"file_path": "invalid<>path"}
        )
        assert response.status_code in [400, 500]

        # Empty path
        response = client.post("/api/ingestion/process-file", params={"file_path": ""})
        assert response.status_code == 422

    @patch("jd_ingestion.api.endpoints.ingestion.FileDiscovery")
    def test_file_processing_with_encoding_error(
        self, mock_file_discovery_class, client, sample_file_metadata
    ):
        """Test file processing with encoding errors."""
        mock_discovery = Mock()
        mock_discovery._extract_file_metadata.return_value = sample_file_metadata
        mock_file_discovery_class.return_value = mock_discovery

        with patch("pathlib.Path.exists", return_value=True):
            with patch(
                "builtins.open",
                side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid"),
            ):
                response = client.post(
                    "/api/ingestion/process-file",
                    params={"file_path": "/test/file.txt"},
                )
                assert response.status_code == 500

    def test_large_response_truncation(self, client):
        """Test that large file lists are truncated in responses."""
        with patch(
            "jd_ingestion.api.endpoints.ingestion.FileDiscovery"
        ) as mock_discovery_class:
            # Create 200 mock files (should be truncated to 100)
            mock_files = []
            for i in range(200):
                mock_file = Mock()
                mock_file.file_path = Path(f"file_{i}.txt")
                mock_file.job_number = f"JOB_{i}"
                mock_file.classification = "EX-01"
                mock_file.language = "en"
                mock_file.title = f"Job {i}"
                mock_file.file_size = 1024
                mock_file.is_valid = True
                mock_file.validation_errors = []
                mock_files.append(mock_file)

            mock_discovery = Mock()
            mock_discovery.scan_directory.return_value = mock_files
            mock_discovery.get_stats.return_value = {
                "total_files": 200,
                "valid_files": 200,
                "invalid_files": 0,
            }
            mock_discovery_class.return_value = mock_discovery

            with patch("pathlib.Path.exists", return_value=True):
                response = client.post(
                    "/api/ingestion/scan-directory",
                    params={"directory_path": "/test/path"},
                )

            assert response.status_code == 200
            data = response.json()
            assert len(data["files"]) == 100  # Should be truncated
            assert data["total_files_found"] == 200  # But total count preserved
