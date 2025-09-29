from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import declarative_base
from typing import AsyncIterator, Iterator

from ..config import settings

__all__ = [
    "async_engine",
    "AsyncSessionLocal",
    "sync_engine",
    "SessionLocal",
    "Base",
    "configure_mappers",
    "get_async_session",
    "get_db",
]

# Async database setup
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Sync database setup (for Alembic migrations and blocking operations)
sync_engine = create_engine(
    settings.database_sync_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

# Base class for all models
Base = declarative_base()


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
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db() -> Iterator[Session]:
    """Dependency to get database session for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
