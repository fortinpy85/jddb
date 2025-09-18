#!/usr/bin/env python3
"""
This script checks the database connection and lists the existing tables.
"""
import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from src.jd_ingestion.database.connection import async_engine

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def check_tables() -> None:
    """
    Connects to the database, lists the tables in the public schema,
    and prints the database version.
    """
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                )
            )
            tables = [row[0] for row in result]
            logging.info(f"Existing tables: {tables}")

            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            logging.info(f"Database version: {version}")

    except SQLAlchemyError as e:
        logging.error(f"Database connection error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


async def main() -> None:
    """
    Runs the check_tables function.
    """
    await check_tables()


if __name__ == "__main__":
    asyncio.run(main())
