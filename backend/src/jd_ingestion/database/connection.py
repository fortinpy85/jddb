from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import AsyncIterator, Iterator

from ..config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)

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

Base = declarative_base()

sync_engine = create_engine(
    settings.database_sync_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=20,  # Increased from default 5
    max_overflow=40,  # Increased from default 10
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,  # Wait up to 30s for connection
)

async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # Verify connections before use
    pool_size=20,  # Increased from default 5 for concurrent load
    max_overflow=40,  # Increased from default 10 to handle spikes
    pool_recycle=3600,  # Recycle connections after 1 hour to prevent stale connections
    pool_timeout=30,  # Wait up to 30s for connection acquisition
    connect_args={
        "server_settings": {
            "application_name": "jd_ingestion_engine",
            "jit": "off",  # Disable JIT for faster simple queries
        }
    },
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def configure_mappers() -> None:
    """Ensure all model mappers are properly configured."""
    try:
        from sqlalchemy.orm import configure_mappers

        configure_mappers()
    except Exception as e:
        # If configure_mappers fails, it's likely already configured
        logger.debug(f"Mapper configuration skipped (likely already configured): {e}")


async def get_async_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


def get_sync_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def get_db() -> Iterator[Session]:
    yield from get_sync_session()
