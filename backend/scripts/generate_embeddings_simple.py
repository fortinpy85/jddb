#!/usr/bin/env python3
"""
This script generates embeddings for existing job descriptions in the database.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Dict, Any

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from jd_ingestion.config import settings
from jd_ingestion.database.models import JobDescription, ContentChunk
from jd_ingestion.services.embedding_service import embedding_service
from jd_ingestion.utils.logging import get_logger

logger = get_logger(__name__)


class SimpleEmbeddingGenerator:
    """
    A simple embedding generator that connects to the database and generates embeddings
    for job descriptions that don't have them yet.
    """

    def __init__(self):
        self.engine = create_async_engine(settings.database_url)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def get_stats(self) -> Dict[str, Any]:
        """
        Gets the current embedding statistics from the database.
        """
        async with self.async_session() as session:
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
            return {
                "total_jobs": total_jobs,
                "total_chunks": total_chunks,
                "chunks_with_embeddings": chunks_with_embeddings,
            }

    async def generate_embeddings(self) -> None:
        """
        Generates embeddings for all content chunks that don't have them yet.
        """
        async with self.async_session() as session:
            chunks_to_embed = (
                (
                    await session.execute(
                        select(ContentChunk).where(ContentChunk.embedding.is_(None))
                    )
                )
                .scalars()
                .all()
            )
            if not chunks_to_embed:
                logger.info("No new content chunks to embed.")
                return

            logger.info(f"Found {len(chunks_to_embed)} content chunks to embed.")
            for chunk in chunks_to_embed:
                try:
                    embedding = await embedding_service.generate_embedding(
                        chunk.content
                    )
                    chunk.embedding = embedding
                    session.add(chunk)
                except Exception as e:
                    logger.error(
                        f"Failed to generate embedding for chunk {chunk.id}: {e}"
                    )

            await session.commit()
            logger.info("Successfully generated and saved new embeddings.")

    async def close(self) -> None:
        """
        Closes the database connection.
        """
        await self.engine.dispose()


async def main() -> None:
    """
    The main entry point for the script.
    """
    parser = argparse.ArgumentParser(
        description="Generate embeddings for job descriptions"
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show embedding statistics only"
    )
    parser.add_argument(
        "--generate", action="store_true", help="Generate new embeddings"
    )
    args = parser.parse_args()

    generator = SimpleEmbeddingGenerator()

    try:
        if args.stats:
            stats = await generator.get_stats()
            logger.info("\nEmbedding Statistics")
            logger.info("=" * 50)
            logger.info(f"Total Jobs: {stats['total_jobs']}")
            logger.info(f"Total Chunks: {stats['total_chunks']}")
            logger.info(f"Chunks with Embeddings: {stats['chunks_with_embeddings']}")
            if stats["chunks_with_embeddings"] > 0:
                logger.info("Semantic search is available")
            else:
                logger.warning("No embeddings found - semantic search unavailable")
        elif args.generate:
            await generator.generate_embeddings()
        else:
            logger.info("Please specify either --stats or --generate.")

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)
    finally:
        await generator.close()


if __name__ == "__main__":
    asyncio.run(main())
