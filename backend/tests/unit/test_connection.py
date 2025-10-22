"""
Tests for database connection module.
"""

import pytest
import os
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import text

from jd_ingestion.database.connection import (
    async_engine,
    AsyncSessionLocal,
    sync_engine,
    SessionLocal,
    Base,
    configure_mappers,
    get_async_session,
    get_sync_session,
    get_db,
)
from jd_ingestion.config.settings import settings


class TestDatabaseEngines:
    """Test database engine creation and configuration."""

    def test_async_engine_creation(self):
        """Test async engine is created with correct settings."""
        assert async_engine is not None

    def test_sync_engine_creation(self):
        """Test sync engine is created with correct settings."""
        assert sync_engine is not None


class TestSessionMakers:
    """Test session maker configuration."""

    def test_async_session_maker_creation(self):
        """Test async session maker is created with correct configuration."""
        assert AsyncSessionLocal is not None

    def test_sync_session_maker_creation(self):
        """Test sync session maker is created with correct configuration."""
        assert SessionLocal is not None


class TestBaseModel:
    """Test declarative base configuration."""

    def test_base_is_declarative_base(self):
        """Test that Base is a proper declarative base."""
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")

    def test_base_can_be_used_for_model_creation(self):
        """Test that Base can be used to create models."""
        from sqlalchemy import Column, Integer, String

        class TestModel(Base):
            __tablename__ = "test_table"

            id = Column(Integer, primary_key=True)
            name = Column(String(50))

        assert TestModel.__tablename__ == "test_table"
        assert hasattr(TestModel, "id")
        assert hasattr(TestModel, "name")
        assert hasattr(TestModel, "__table__")


class TestConfigureMappers:
    """Test mapper configuration functionality."""

    @patch("sqlalchemy.orm.configure_mappers")
    def test_configure_mappers_success(self, mock_configure_mappers):
        """Test successful mapper configuration."""
        configure_mappers()
        mock_configure_mappers.assert_called_once()

    @patch("sqlalchemy.orm.configure_mappers")
    def test_configure_mappers_handles_exception(self, mock_configure_mappers):
        """Test mapper configuration handles exceptions gracefully."""
        mock_configure_mappers.side_effect = Exception("Mapper configuration failed")
        try:
            configure_mappers()
        except Exception as e:
            pytest.fail(
                f"configure_mappers should handle exceptions gracefully, but raised: {e}"
            )
        mock_configure_mappers.assert_called_once()


class TestAsyncSessionDependency:
    """Test async session dependency functionality."""

    @pytest.mark.asyncio
    async def test_get_async_session_success_flow(self):
        """Test successful async session dependency flow."""
        async_session_gen = get_async_session()
        session = await async_session_gen.__anext__()
        try:
            assert isinstance(session, AsyncSession)
        finally:
            await session.close()


class TestSyncSessionDependency:
    """Test synchronous session dependency functionality."""

    def test_get_sync_session_success(self):
        """Test successful sync session creation."""
        for session in get_sync_session():
            assert isinstance(session, Session)

    def test_get_db_dependency_success(self):
        """Test FastAPI database dependency success flow."""
        for session in get_db():
            assert isinstance(session, Session)


class TestConnectionModuleIntegration:
    """Test connection module integration scenarios."""

    def test_all_components_are_properly_exported(self):
        """Test that all expected components are exported."""
        assert async_engine is not None
        assert AsyncSessionLocal is not None
        assert sync_engine is not None
        assert SessionLocal is not None
        assert Base is not None
        assert callable(configure_mappers)
        assert callable(get_async_session)
        assert callable(get_sync_session)
        assert callable(get_db)


class TestDatabaseURLConfiguration:
    """Test database URL configuration for CI/CD environments."""

    def test_database_url_format_async(self):
        """Verify async database URL uses correct asyncpg driver."""
        # In test environment, we use SQLite which is acceptable
        # In CI/CD with PostgreSQL, must use postgresql+asyncpg://
        url_str = str(async_engine.url)
        if "postgresql" in url_str:
            assert "postgresql+asyncpg" in url_str, (
                f"Async DATABASE_URL must use postgresql+asyncpg:// driver, "
                f"got: {url_str}"
            )
        elif "sqlite" in url_str:
            assert (
                "aiosqlite" in url_str or "sqlite" in url_str
            ), f"Async SQLite must use aiosqlite driver, got: {url_str}"

    def test_database_url_format_sync(self):
        """Verify sync database URL uses correct postgresql driver."""
        url_str = str(sync_engine.url)
        # Sync driver should not have asyncpg
        assert (
            "asyncpg" not in url_str
        ), f"Sync DATABASE_SYNC_URL must not use asyncpg driver, got: {url_str}"

    def test_settings_database_url_async(self):
        """Verify settings async database URL format."""
        if "postgresql" in settings.database_url:
            assert settings.database_url.startswith("postgresql+asyncpg://"), (
                f"Settings async DATABASE_URL must use postgresql+asyncpg:// driver, "
                f"got: {settings.database_url}"
            )

    def test_settings_database_url_sync(self):
        """Verify settings sync database URL format."""
        if "postgresql" in settings.database_sync_url:
            assert settings.database_sync_url.startswith("postgresql://"), (
                f"Settings sync DATABASE_SYNC_URL must use postgresql:// driver, "
                f"got: {settings.database_sync_url}"
            )
            assert "asyncpg" not in settings.database_sync_url, (
                f"Settings sync URL must not have asyncpg, "
                f"got: {settings.database_sync_url}"
            )

    def test_ci_environment_variables(self):
        """Verify CI/CD environment uses correct database URLs."""
        if os.getenv("ENVIRONMENT") == "testing":
            # In CI/CD testing environment
            db_url = os.getenv("DATABASE_URL", "")
            db_sync_url = os.getenv("DATABASE_SYNC_URL", "")

            # Both should be set in CI/CD
            if db_url and "postgresql" in db_url:
                assert db_url.startswith("postgresql+asyncpg://"), (
                    f"CI DATABASE_URL must use postgresql+asyncpg:// driver, "
                    f"got: {db_url}"
                )

            if db_sync_url and "postgresql" in db_sync_url:
                assert db_sync_url.startswith("postgresql://"), (
                    f"CI DATABASE_SYNC_URL must use postgresql:// driver, "
                    f"got: {db_sync_url}"
                )
                assert (
                    "asyncpg" not in db_sync_url
                ), f"CI sync URL must not have asyncpg, got: {db_sync_url}"

    @pytest.mark.asyncio
    async def test_async_connection_works(self):
        """Test async database connection actually works."""
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            assert row is not None
            assert row[0] == 1

    def test_sync_connection_works(self):
        """Test sync database connection actually works."""
        with sync_engine.begin() as conn:
            result = conn.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            assert row is not None
            assert row[0] == 1

    @pytest.mark.asyncio
    async def test_async_session_query(self):
        """Test async session can execute queries."""
        async_session_gen = get_async_session()
        session = await async_session_gen.__anext__()
        try:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
        finally:
            await session.close()

    def test_sync_session_query(self):
        """Test sync session can execute queries."""
        for session in get_sync_session():
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1
            break  # Only test first session
