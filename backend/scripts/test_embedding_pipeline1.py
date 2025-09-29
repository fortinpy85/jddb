#!/usr/bin/env python3
"""
This script tests the complete embedding pipeline, including chunk creation,
embedding generation, and semantic search.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import List

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, text
from sqlalchemy.exc import SQLAlchemyError

from jd_ingestion.config import settings
from jd_ingestion.database.models import JobDescription, JobSection, ContentChunk
from jd_ingestion.services.embedding_service import embedding_service
from jd_ingestion.utils.logging import get_logger

logger = get_logger(__name__)


class EmbeddingPipelineTester:
    """
    A class to test the complete embedding pipeline.
    """

    def __init__(self):
        self.engine = create_async_engine(settings.database_url)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    def chunk_text(
        self, text: str, chunk_size: int = 100, overlap: int = 20
    ) -> List[str]:
        """
        Splits text into overlapping chunks.
        """
        if not text:
            return []
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i : i + chunk_size]
            if chunk_words:
                chunks.append(" ".join(chunk_words))
        return chunks

    async def create_chunks_from_sections(self) -> None:
        """
        Creates content chunks from job sections.
        """
        logger.info("\n--- Creating Content Chunks ---")
        async with self.async_session() as session:
            sections = (
                (
                    await session.execute(
                        select(JobSection).order_by(
                            JobSection.job_id, JobSection.section_order
                        )
                    )
                )
                .scalars()
                .all()
            )
            logger.info(f"Found {len(sections)} job sections")
            total_chunks_created = 0
            for section in sections:
                chunks = self.chunk_text(section.section_content)
                logger.info(
                    f"Section {section.id} ({section.section_type}): {len(chunks)} chunks"
                )
                for i, chunk_text in enumerate(chunks):
                    session.add(
                        ContentChunk(
                            job_id=section.job_id,
                            section_id=section.id,
                            chunk_text=chunk_text,
                            chunk_index=i,
                        )
                    )
                    total_chunks_created += 1
            await session.commit()
            logger.info(f"Created {total_chunks_created} content chunks")

    async def test_embedding_generation(self, limit: int = 5) -> None:
        """
        Tests embedding generation on a limited number of chunks.
        """
        logger.info("\n--- Testing Embedding Generation ---")
        if not settings.openai_api_key:
            logger.warning(
                "OpenAI API key not configured - skipping embedding generation"
            )
            return
        async with self.async_session() as session:
            chunks = (
                (
                    await session.execute(
                        select(ContentChunk)
                        .where(ContentChunk.embedding.is_(None))
                        .limit(limit)
                    )
                )
                .scalars()
                .all()
            )
            logger.info(f"Found {len(chunks)} chunks without embeddings")
            successful_embeddings = 0
            for chunk in chunks:
                logger.info(
                    f"Generating embedding for chunk {chunk.id} (job {chunk.job_id})..."
                )
                try:
                    embedding = await embedding_service.generate_embedding(
                        chunk.chunk_text
                    )
                    if embedding:
                        chunk.embedding = embedding
                        successful_embeddings += 1
                        logger.info(f"  Success: {len(embedding)} dimensions")
                    else:
                        logger.warning("  Failed: No embedding returned")
                except Exception as e:
                    logger.error(f"  Error: {e}")
            await session.commit()
            logger.info(f"Successfully generated {successful_embeddings} embeddings")

    async def test_semantic_search(
        self, query: str = "strategic planning director"
    ) -> None:
        """
        Tests semantic search functionality.
        """
        logger.info(f"\n--- Testing Semantic Search: '{query}' ---")
        async with self.async_session() as session:
            if (
                await session.execute(
                    select(func.count(ContentChunk.id)).where(
                        ContentChunk.embedding.isnot(None)
                    )
                )
            ).scalar_one() == 0:
                logger.warning("No embeddings found - cannot test semantic search")
                return
            logger.info(
                f"Found {(await session.execute(select(func.count(ContentChunk.id)).where(ContentChunk.embedding.isnot(None)))).scalar_one()} chunks with embeddings"
            )
            results = await embedding_service.semantic_search(
                query=query, db=session, limit=5
            )
            logger.info(f"Semantic search returned {len(results)} results:")
            for i, result in enumerate(results, 1):
                logger.info(f"  {i}. Job {result['job_number']}: {result['title']}")
                logger.info(f"     Relevance: {result['relevance_score']:.3f}")
                logger.info(f"     Matching chunks: {result['matching_chunks']}")

    async def get_stats(self) -> dict:
        """
        Gets current pipeline statistics.
        """
        async with self.async_session() as session:
            total_jobs = (
                await session.execute(select(func.count(JobDescription.id)))
            ).scalar_one()
            total_sections = (
                await session.execute(select(func.count(JobSection.id)))
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
                "total_sections": total_sections,
                "total_chunks": total_chunks,
                "chunks_with_embeddings": chunks_with_embeddings,
            }

    async def cleanup_chunks(self) -> None:
        """
        Removes all content chunks (for testing).
        """
        logger.info("\n--- Cleaning up existing chunks ---")
        async with self.async_session() as session:
            await session.execute(text("DELETE FROM content_chunks"))
            await session.commit()
            logger.info("All content chunks deleted")

    async def close(self) -> None:
        """
        Closes the database connection.
        """
        await self.engine.dispose()


async def main() -> None:
    """
    Main entry point for the script.
    """
    parser = argparse.ArgumentParser(description="Test embedding pipeline")
    parser.add_argument(
        "--cleanup", action="store_true", help="Clean up existing chunks first"
    )
    parser.add_argument(
        "--create-chunks", action="store_true", help="Create content chunks"
    )
    parser.add_argument(
        "--test-embeddings", action="store_true", help="Test embedding generation"
    )
    parser.add_argument(
        "--test-search", action="store_true", help="Test semantic search"
    )
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument(
        "--full-test", action="store_true", help="Run complete pipeline test"
    )
    args = parser.parse_args()

    tester = EmbeddingPipelineTester()
    try:
        if args.full_test:
            logger.info("Running full pipeline test...")
            if (
                input("This will cleanup existing chunks. Continue? (y/N): ").lower()
                != "y"
            ):
                logger.info("Cancelled")
                return
            await tester.cleanup_chunks()
            await tester.create_chunks_from_sections()
            await tester.test_embedding_generation(limit=3)
            await tester.test_semantic_search()
        elif args.cleanup:
            await tester.cleanup_chunks()
        elif args.create_chunks:
            await tester.create_chunks_from_sections()
        elif args.test_embeddings:
            await tester.test_embedding_generation()
        elif args.test_search:
            await tester.test_semantic_search()

        stats = await tester.get_stats()
        logger.info("\n" + "=" * 50)
        logger.info("PIPELINE STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Total Jobs: {stats['total_jobs']}")
        logger.info(f"Total Sections: {stats['total_sections']}")
        logger.info(f"Total Chunks: {stats['total_chunks']}")
        logger.info(f"Chunks with Embeddings: {stats['chunks_with_embeddings']}")
        if stats["total_chunks"] > 0 and stats["chunks_with_embeddings"] > 0:
            coverage = (stats["chunks_with_embeddings"] / stats["total_chunks"]) * 100
            logger.info(f"Embedding Coverage: {coverage:.1f}%")
            logger.info("Status: Semantic search available")
        else:
            logger.info("Status: No embeddings - semantic search unavailable")

    except (SQLAlchemyError, Exception) as e:
        logger.critical(f"Pipeline test failed: {e}")
        sys.exit(1)
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
