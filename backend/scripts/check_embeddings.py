#!/usr/bin/env python3
"""
This script checks the statistics of the embeddings in the database.
"""
import asyncio
import logging
import sys
from pathlib import Path
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jd_ingestion.config import settings
from jd_ingestion.database.models import JobDescription, ContentChunk

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def check_embedding_stats() -> None:
    """
    Connects to the database and checks the statistics of the embeddings.
    """
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            total_jobs = (
                await session.execute(select(func.count(JobDescription.id)))
            ).scalar_one()
            total_chunks = (
                await session.execute(select(func.count(ContentChunk.id)))
            ).scalar_one()
            chunks_with_embeddings = (
                await session.execute(
                    select(func.count(ContentChunk.id)).where(
                        ContentChunk.embedding.isnot(None)
                    )
                )
            ).scalar_one()
            jobs_with_embeddings = (
                await session.execute(
                    select(func.count(func.distinct(ContentChunk.job_id))).where(
                        ContentChunk.embedding.isnot(None)
                    )
                )
            ).scalar_one()

            jobs_percentage = (
                (jobs_with_embeddings / total_jobs * 100) if total_jobs > 0 else 0
            )
            chunks_percentage = (
                (chunks_with_embeddings / total_chunks * 100) if total_chunks > 0 else 0
            )

            logging.info("\nEmbedding Statistics")
            logging.info("=" * 50)
            logging.info(f"Total Jobs: {total_jobs}")
            logging.info(
                f"Jobs with Embeddings: {jobs_with_embeddings} ({jobs_percentage:.2f}%)"
            )
            logging.info(f"Total Chunks: {total_chunks}")
            logging.info(
                f"Chunks with Embeddings: {chunks_with_embeddings} ({chunks_percentage:.2f}%)"
            )

            if chunks_with_embeddings > 0:
                logging.info("✓ Semantic search is available")
            else:
                logging.warning("⚠ No embeddings found - semantic search unavailable")

    except SQLAlchemyError as e:
        logging.error(f"Database error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        await engine.dispose()


async def main() -> None:
    """
    Runs the check_embedding_stats function.
    """
    await check_embedding_stats()


if __name__ == "__main__":
    asyncio.run(main())
