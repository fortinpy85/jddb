#!/usr/bin/env python3
"""
This script initializes the database, creating the database if it doesn't exist,
creating the required extensions, creating the tables, and verifying the connection.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine
from jd_ingestion.database.connection import Base, sync_engine, async_engine
from jd_ingestion.database.models import *
from jd_ingestion.config import settings
from jd_ingestion.utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def create_database_if_not_exists() -> None:
    """
    Creates the database if it doesn't exist.
    """
    try:
        db_name = settings.database_sync_url.split("/")[-1]
        base_url = "/".join(settings.database_sync_url.split("/")[:-1])
        postgres_url = f"{base_url}/postgres"
        temp_engine = create_engine(postgres_url)
        with temp_engine.connect() as conn:
            conn.execution_options(autocommit=True)
            if not conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name},
            ).fetchone():
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                logger.info(f"Database '{db_name}' created.")
            else:
                logger.info(f"Database '{db_name}' already exists.")
        temp_engine.dispose()
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database: {e}")
        raise


def create_extensions() -> None:
    """
    Creates required PostgreSQL extensions.
    """
    try:
        with sync_engine.connect() as conn:
            with conn.begin():
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                logger.info("Created pgvector extension.")
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
                logger.info("Created pg_trgm extension.")
    except SQLAlchemyError as e:
        logger.error(f"Failed to create extensions: {e}")
        raise


def create_tables() -> None:
    """
    Creates all database tables.
    """
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=sync_engine)
        logger.info("Database tables created successfully.")
    except SQLAlchemyError as e:
        logger.error(f"Failed to create tables: {e}")
        raise


async def verify_async_connection() -> None:
    """
    Verifies that the async database connection works.
    """
    try:
        async with async_engine.connect() as conn:
            version = (await conn.execute(text("SELECT version()"))).scalar()
            logger.info(
                f"Async database connection verified. PostgreSQL version: {version}"
            )
    except SQLAlchemyError as e:
        logger.error(f"Async database connection failed: {e}")
        raise


def create_sample_data() -> None:
    """
    Creates sample data for testing (optional).
    """
    try:
        from sqlalchemy.orm import Session

        with Session(sync_engine) as session:
            if (
                session.execute(
                    text("SELECT COUNT(*) FROM job_descriptions")
                ).scalar_one()
                > 0
            ):
                logger.info("Sample data already exists.")
                return
            logger.info(
                "Sample data creation skipped - will be populated via ingestion."
            )
    except SQLAlchemyError as e:
        logger.error(f"Failed to create sample data: {e}")


async def main() -> None:
    """
    Main initialization function.
    """
    try:
        logger.info("Starting database initialization...")
        create_database_if_not_exists()
        create_extensions()
        create_tables()
        await verify_async_connection()
        create_sample_data()
        logger.info("Database initialization completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Start the API server: python -m jd_ingestion.api.main")
        logger.info("2. Use the ingestion endpoints to process job description files")
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")
        sys.exit(1)
    finally:
        if sync_engine:
            sync_engine.dispose()
        if async_engine:
            await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
