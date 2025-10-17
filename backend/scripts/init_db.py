#!/usr/bin/env python3
"""
This script initializes the database, creating the database if it doesn't exist,
creating the required extensions, and creating the tables.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from jd_ingestion.database.connection import Base, sync_engine
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
        logger.info("Dropping all tables...")
        Base.metadata.drop_all(sync_engine)
        logger.info("Creating all tables...")
        Base.metadata.create_all(sync_engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


async def main() -> None:
    """
    Main initialization function.
    """
    try:
        logger.info("Starting database initialization...")
        create_database_if_not_exists()
        create_extensions()
        create_tables()
        logger.info("Database initialization completed successfully!")
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")
        sys.exit(1)
    finally:
        if sync_engine:
            sync_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
