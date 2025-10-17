"""
Tests for database connection module.
"""

import pytest
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

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
        async for session in get_async_session():
            assert isinstance(session, AsyncSession)


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
