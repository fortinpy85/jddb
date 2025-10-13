"""
Tests for database connection module.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
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

    @patch("jd_ingestion.database.connection.settings")
    @patch("jd_ingestion.database.connection.create_async_engine")
    def test_async_engine_creation(self, mock_create_engine, mock_settings):
        """Test async engine is created with correct settings."""
        mock_settings.database_url = "postgresql+asyncpg://user:pass@localhost/test"
        mock_settings.debug = True
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine

        # Import and call the function
        from jd_ingestion.database.connection import get_async_engine

        # Reset global state
        import jd_ingestion.database.connection as conn
        conn._async_engine = None

        # Call get_async_engine to trigger creation
        result = get_async_engine()

        mock_create_engine.assert_called_once_with(
            "postgresql+asyncpg://user:pass@localhost/test",
            echo=True,
            pool_pre_ping=True,
        )
        assert result == mock_engine

    @patch("jd_ingestion.database.connection.settings")
    @patch("jd_ingestion.database.connection.create_engine")
    def test_sync_engine_creation(self, mock_create_engine, mock_settings):
        """Test sync engine is created with correct settings."""
        mock_settings.database_sync_url = "postgresql://user:pass@localhost/test"
        mock_settings.debug = False
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine

        # Import and call the function
        from jd_ingestion.database.connection import get_sync_engine

        # Reset global state
        import jd_ingestion.database.connection as conn
        conn._sync_engine = None

        # Call get_sync_engine to trigger creation
        result = get_sync_engine()

        mock_create_engine.assert_called_once_with(
            "postgresql://user:pass@localhost/test",
            echo=False,
            pool_pre_ping=True,
        )
        assert result == mock_engine


class TestSessionMakers:
    """Test session maker configuration."""

    @patch("jd_ingestion.database.connection.get_async_engine")
    @patch("jd_ingestion.database.connection.async_sessionmaker")
    def test_async_session_maker_creation(self, mock_sessionmaker, mock_get_engine):
        """Test async session maker is created with correct configuration."""
        mock_engine = Mock()
        mock_get_engine.return_value = mock_engine
        mock_session_factory = Mock()
        mock_sessionmaker.return_value = mock_session_factory

        from jd_ingestion.database.connection import get_async_session_local

        # Reset global state
        import jd_ingestion.database.connection as conn
        conn._async_session_local = None

        # Call get_async_session_local to trigger creation
        result = get_async_session_local()

        mock_sessionmaker.assert_called_once_with(
            mock_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        assert result == mock_session_factory

    @patch("jd_ingestion.database.connection.get_sync_engine")
    @patch("jd_ingestion.database.connection.sessionmaker")
    def test_sync_session_maker_creation(self, mock_sessionmaker, mock_get_engine):
        """Test sync session maker is created with correct configuration."""
        mock_engine = Mock()
        mock_get_engine.return_value = mock_engine
        mock_session_factory = Mock()
        mock_sessionmaker.return_value = mock_session_factory

        from jd_ingestion.database.connection import get_session_local

        # Reset global state
        import jd_ingestion.database.connection as conn
        conn._session_local = None

        # Call get_session_local to trigger creation
        result = get_session_local()

        mock_sessionmaker.assert_called_once_with(
            bind=mock_engine,
            autocommit=False,
            autoflush=False,
        )
        assert result == mock_session_factory


class TestBaseModel:
    """Test declarative base configuration."""

    def test_base_is_declarative_base(self):
        """Test that Base is a proper declarative base."""
        # Import the actual Base, not mocked

        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")

    def test_base_can_be_used_for_model_creation(self):
        """Test that Base can be used to create models."""
        # Import the actual Base
        from sqlalchemy import Column, Integer, String

        # Create a test model
        class TestModel(Base):
            __tablename__ = "test_table"

            id = Column(Integer, primary_key=True)
            name = Column(String(50))

        # Verify the model was created correctly
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

        # Should not raise exception
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
        mock_session = AsyncMock(spec=AsyncSession)

        with patch(
            "jd_ingestion.database.connection.get_async_session_local"
        ) as mock_get_session_local:
            # Create async context manager mock
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_context.__aexit__.return_value = None

            mock_session_factory = Mock(return_value=mock_context)
            mock_get_session_local.return_value = mock_session_factory

            # Create generator and get session
            session_generator = get_async_session()
            session = await session_generator.__anext__()

            # Verify session is returned
            assert session == mock_session

            # Complete the generator normally
            try:
                await session_generator.__anext__()
            except StopAsyncIteration:
                pass

            # Verify commit and close are called on successful completion
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_async_session_exception_rollback(self):
        """Test async session dependency rollback on exception."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch(
            "jd_ingestion.database.connection.get_async_session_local"
        ) as mock_get_session_local:
            # Create async context manager mock
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_context.__aexit__.return_value = None

            mock_session_factory = Mock(return_value=mock_context)
            mock_get_session_local.return_value = mock_session_factory

            session_generator = get_async_session()
            _session = await session_generator.__anext__()

            # Simulate exception during session usage
            try:
                await session_generator.athrow(Exception("Database error"))
            except Exception:
                pass

            # Verify rollback and close are called
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_async_session_always_closes(self):
        """Test async session is always closed in finally block."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch(
            "jd_ingestion.database.connection.get_async_session_local"
        ) as mock_get_session_local:
            # Create async context manager mock
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_context.__aexit__.return_value = None

            mock_session_factory = Mock(return_value=mock_context)
            mock_get_session_local.return_value = mock_session_factory

            session_generator = get_async_session()
            _session = await session_generator.__anext__()

            # Manually close the generator to trigger finally block
            await session_generator.aclose()

            # Verify close is called
            mock_session.close.assert_called_once()


class TestSyncSessionDependency:
    """Test synchronous session dependency functionality."""

    def test_get_sync_session_success(self):
        """Test successful sync session creation."""
        mock_session = Mock(spec=Session)

        with patch(
            "jd_ingestion.database.connection.get_session_local"
        ) as mock_get_session_local:
            mock_session_factory = Mock()
            mock_session_factory.return_value = mock_session
            mock_get_session_local.return_value = mock_session_factory

            # Create generator and get session
            session_gen = get_sync_session()
            result = next(session_gen)

            assert result == mock_session
            mock_get_session_local.assert_called_once()

            # Complete generator to trigger commit and close
            try:
                next(session_gen)
            except StopIteration:
                pass

            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    def test_get_sync_session_closes_on_exception(self):
        """Test sync session is closed even when exception occurs."""
        mock_session = Mock(spec=Session)

        with patch(
            "jd_ingestion.database.connection.get_session_local"
        ) as mock_get_session_local:
            mock_session_factory = Mock()
            mock_session_factory.return_value = mock_session
            mock_get_session_local.return_value = mock_session_factory

            session_gen = get_sync_session()
            result = next(session_gen)

            assert result == mock_session

            # Simulate exception during usage
            try:
                session_gen.throw(Exception("Database error"))
            except Exception:
                pass

            # Verify rollback and close are called
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()

    def test_get_db_dependency_success(self):
        """Test FastAPI database dependency success flow."""
        mock_session = Mock(spec=Session)

        with patch(
            "jd_ingestion.database.connection.get_session_local"
        ) as mock_get_session_local:
            mock_session_factory = Mock()
            mock_session_factory.return_value = mock_session
            mock_get_session_local.return_value = mock_session_factory

            # Create generator and get session
            db_generator = get_db()
            db_session = next(db_generator)

            assert db_session == mock_session
            mock_get_session_local.assert_called_once()

            # Complete the generator to trigger finally block
            try:
                next(db_generator)
            except StopIteration:
                pass

            # Verify commit and close are called in finally block
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    def test_get_db_dependency_closes_on_exception(self):
        """Test FastAPI database dependency cleanup on exception."""
        mock_session = Mock(spec=Session)

        with patch(
            "jd_ingestion.database.connection.get_session_local"
        ) as mock_get_session_local:
            mock_session_factory = Mock()
            mock_session_factory.return_value = mock_session
            mock_get_session_local.return_value = mock_session_factory

            db_generator = get_db()
            db_session = next(db_generator)

            assert db_session == mock_session

            # Simulate exception during database operations
            try:
                db_generator.throw(Exception("Database operation failed"))
            except Exception:
                pass

            # Verify rollback and close are called even on exception
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()


class TestConnectionModuleIntegration:
    """Test connection module integration scenarios."""

    def test_all_components_are_properly_exported(self):
        """Test that all expected components are exported."""
        from jd_ingestion.database.connection import (
            Base,
            configure_mappers,
            get_async_session,
            get_sync_session,
            get_db,
        )

        # Verify all components exist
        assert async_engine is not None
        assert AsyncSessionLocal is not None
        assert sync_engine is not None
        assert SessionLocal is not None
        assert Base is not None
        assert callable(configure_mappers)
        assert callable(get_async_session)
        assert callable(get_sync_session)
        assert callable(get_db)

    def test_session_dependencies_return_generators(self):
        """Test that session dependencies return proper generators."""
        from jd_ingestion.database.connection import get_async_session, get_db

        # Test async session dependency
        async_gen = get_async_session()
        assert hasattr(async_gen, "__anext__")
        assert hasattr(async_gen, "aclose")

        # Test sync session dependency
        sync_gen = get_db()
        assert hasattr(sync_gen, "__next__")
        assert hasattr(sync_gen, "close")

    @patch("jd_ingestion.database.connection.settings")
    def test_settings_integration(self, mock_settings):
        """Test that connection module properly integrates with settings."""
        # Verify settings are imported and used
        from jd_ingestion.database.connection import settings

        assert settings is mock_settings

    def test_base_model_inheritance_chain(self):
        """Test that Base has proper inheritance chain for SQLAlchemy models."""
        from sqlalchemy.orm import DeclarativeMeta

        # Base should be instance of DeclarativeMeta
        assert isinstance(Base, DeclarativeMeta)

        # Base should have required attributes for SQLAlchemy models
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")
