from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import declarative_base
from typing import AsyncIterator, Iterator, Optional

from ..config import settings

__all__ = [
    "async_engine",
    "AsyncSessionLocal",
    "sync_engine",
    "SessionLocal",
    "Base",
    "configure_mappers",
    "get_async_session",
    "get_sync_session",
    "get_db",
]

# Lazy initialization of database engines
_async_engine: Optional[AsyncEngine] = None
_sync_engine: Optional[Engine] = None
_async_session_local = None
_session_local = None

# Base class for all models
Base = declarative_base()


def get_async_engine() -> AsyncEngine:
    """Get or create async database engine."""
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
        )
    return _async_engine


def get_sync_engine() -> Engine:
    """Get or create sync database engine."""
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(
            settings.database_sync_url,
            echo=settings.debug,
            pool_pre_ping=True,
        )
    return _sync_engine


def get_async_session_local():
    """Get or create async session maker."""
    global _async_session_local
    if _async_session_local is None:
        _async_session_local = async_sessionmaker(
            get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_local


def get_session_local():
    """Get or create sync session maker."""
    global _session_local
    if _session_local is None:
        _session_local = sessionmaker(
            bind=get_sync_engine(),
            autocommit=False,
            autoflush=False,
        )
    return _session_local


# Module-level variables that act as lazy singletons
# These provide backward compatibility with the old eager initialization
async_engine = get_async_engine  # Function reference
sync_engine = get_sync_engine  # Function reference
AsyncSessionLocal = get_async_session_local  # Function reference
SessionLocal = get_session_local  # Function reference


# Configure the registry to ensure all models are properly mapped
def configure_mappers() -> None:
    """Ensure all model mappers are properly configured."""
    try:
        from sqlalchemy.orm import configure_mappers

        configure_mappers()
    except Exception:
        # If configure_mappers fails, it's likely already configured
        pass


async def get_async_session() -> AsyncIterator[AsyncSession]:
    """Dependency to get async database session."""
    session_local = get_async_session_local()
    async with session_local() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session() -> Iterator[Session]:
    """Get a sync database session."""
    session_local = get_session_local()
    db = session_local()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Iterator[Session]:
    """Dependency to get database session for FastAPI (alias for get_sync_session)."""
    yield from get_sync_session()
