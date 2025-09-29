#!/usr/bin/env python3
"""
This script creates the database tables and required extensions.
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jd_ingestion.database.models import *  # Import all models  # noqa: F403
from jd_ingestion.database.connection import Base
from jd_ingestion.config import settings
from jd_ingestion.utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def main() -> None:
    """
    Creates the database tables and required extensions.
    """
    try:
        logger.info("Creating engine...")
        engine = create_engine(settings.database_sync_url)

        with engine.connect() as conn:
            with conn.begin():
                logger.info("Creating extensions...")
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                logger.info("Created pgvector extension")
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
                logger.info("Created pg_trgm extension")

        logger.info("Creating tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully!")

        with engine.connect() as conn:
            logger.info("Verifying table creation...")
            result = conn.execute(
                text(
                    """
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                    """
                )
            )
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"Tables in database: {tables}")

    except SQLAlchemyError as e:
        logger.error(f"Failed to create tables: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)
    finally:
        if "engine" in locals():
            engine.dispose()


if __name__ == "__main__":
    main()
