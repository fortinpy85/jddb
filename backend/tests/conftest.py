"""
Test configuration and fixtures for the JDDB backend tests.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import pytest
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
import tempfile
import os
from pathlib import Path

from jd_ingestion.api.main import app
from jd_ingestion.database.connection import get_async_session, get_db
from jd_ingestion.database.models import Base
from jd_ingestion.auth.api_key import get_api_key


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Create a test database URL."""
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def test_sync_db_url() -> str:
    """Create a test sync database URL."""
    return "sqlite:///:memory:"


@pytest.fixture
async def async_engine(test_db_url):
    """Create test async database engine."""
    engine = create_async_engine(test_db_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
def sync_engine(test_sync_db_url):
    """Create test sync database URL."""
    engine = create_engine(test_sync_db_url, echo=False)
    Base.metadata.create_all(engine)

    yield engine

    engine.dispose()


@pytest.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test async database session."""
    async_session_factory = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        yield session


@pytest.fixture
def sync_session(sync_engine):
    """Create test sync database session."""
    Session = sessionmaker(bind=sync_engine)
    session = Session()

    yield session

    session.close()


@pytest.fixture
def test_session():
    """Provide access to the test database session."""
    # Use in-memory database for sync tests
    from sqlalchemy import (
        create_engine,
    )
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    # Use the actual Base from models to include all tables
    sync_engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables using the actual Base metadata (includes data_quality_metrics)
    Base.metadata.create_all(sync_engine)

    Session = sessionmaker(bind=sync_engine)
    test_session = Session()

    # Import actual models instead of creating test-specific ones
    from jd_ingestion.database.models import JobDescription, JobSection, JobMetadata

    yield test_session, JobDescription, JobSection, JobMetadata

    test_session.close()


@pytest.fixture
def test_client(test_session):
    """Create test client with database override for sync tests."""
    session, JobDescription, JobSection, JobMetadata = test_session

    # No need to mock models - we're using the real ones now

    # Enhanced async wrapper for the sync session
    class AsyncSessionWrapper:
        def __init__(self, sync_session):
            self.sync_session = sync_session

        async def execute(self, statement):
            result = self.sync_session.execute(statement)
            return result

        async def commit(self):
            return self.sync_session.commit()

        async def rollback(self):
            return self.sync_session.rollback()

        async def refresh(self, instance):
            return self.sync_session.refresh(instance)

        def add(self, instance):
            return self.sync_session.add(instance)

        def add_all(self, instances):
            return self.sync_session.add_all(instances)

        async def close(self):
            return self.sync_session.close()

        def query(self, *args, **kwargs):
            return self.sync_session.query(*args, **kwargs)

        def get(self, entity, ident):
            return self.sync_session.get(entity, ident)

        def scalar(self, statement):
            return self.sync_session.scalar(statement)

    async_wrapper = AsyncSessionWrapper(session)

    def override_get_async_session():
        return async_wrapper

    def override_get_db():
        yield session

    def override_get_api_key():
        """Override API key validation for tests."""
        return "test-api-key"

    app.dependency_overrides[get_async_session] = override_get_async_session
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_api_key] = override_get_api_key

    # Override configure_mappers to prevent loading JSONB models
    from jd_ingestion.database import connection

    original_configure_mappers = connection.configure_mappers

    def test_configure_mappers():
        """Test version that doesn't configure JSONB models."""
        pass

    connection.configure_mappers = test_configure_mappers

    with TestClient(app) as client:
        yield client

    # Restore original configure_mappers function
    connection.configure_mappers = original_configure_mappers
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(async_session):
    """Create async test client."""
    from httpx import ASGITransport

    # Create a wrapper that returns the session directly
    async def override_get_async_session():
        return async_session

    def override_get_api_key():
        """Override API key validation for tests."""
        return "test-api-key"

    app.dependency_overrides[get_async_session] = override_get_async_session
    app.dependency_overrides[get_api_key] = override_get_api_key

    # Modern httpx API requires ASGITransport
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    await client.__aenter__()

    yield client

    await client.__aexit__(None, None, None)
    app.dependency_overrides.clear()


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_job_description_text():
    """Sample job description text for testing."""
    return """
    GENERAL ACCOUNTABILITY

    Under the direction of the Director General, responsible for managing and directing a comprehensive business analysis program to support strategic planning and operational effectiveness across the organization.

    ORGANIZATION STRUCTURE

    Reports to: Director General, Strategic Planning
    Supervises: 12 FTE (Business Analysts, Senior Analysts)
    Budget Authority: $2.3M annually

    SPECIFIC ACCOUNTABILITIES

    • Lead strategic business analysis initiatives
    • Develop comprehensive analytical frameworks
    • Manage stakeholder relationships
    • Provide executive reporting and recommendations
    """


@pytest.fixture
def sample_job_data():
    """Sample job description data for testing."""
    return {
        "job_number": "103249",
        "title": "Director, Business Analysis",
        "classification": "EX-01",
        "language": "EN",
        "file_path": "/test/path/job.txt",
        "raw_content": "Test job description content",
    }


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for testing."""
    return {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "embedding": [0.1] * 1536,  # Mock embedding vector
                "index": 0,
            }
        ],
        "model": "text-embedding-ada-002",
        "usage": {"prompt_tokens": 10, "total_tokens": 10},
    }


@pytest.fixture
def test_settings(monkeypatch):
    """Override settings for testing using monkeypatch."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("DATABASE_SYNC_URL", "sqlite:///:memory:")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("ENVIRONMENT", "test")

    # Re-import settings after monkeypatching env vars to ensure they are reloaded
    from jd_ingestion.config.settings import Settings

    return Settings()


@pytest.fixture
def sample_file_content():
    """Sample file content for upload testing."""
    return b"This is a test job description file content for testing purposes."


@pytest.fixture
def cleanup_test_files():
    """Cleanup fixture to remove test files."""
    created_files = []

    def track_file(file_path: Path):
        created_files.append(file_path)
        return file_path

    yield track_file

    # Cleanup
    for file_path in created_files:
        if file_path.exists():
            file_path.unlink()
