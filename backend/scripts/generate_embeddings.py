#!/usr/bin/env python3
"""
This script generates embeddings for existing job descriptions in the database.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

from jd_ingestion.config import settings
from jd_ingestion.database.models import JobDescription, JobSection, ContentChunk
from jd_ingestion.services.embedding_service import embedding_service
from jd_ingestion.utils.logging import get_logger

logger = get_logger(__name__)


class EmbeddingGenerator:
    """
    A class to generate and store embeddings for job descriptions.
    """

    def __init__(self):
        """
        Initializes the embedding generator.
        """
        self.engine = create_async_engine(settings.database_url)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    def _chunk_text(
        self, text: str, chunk_size: int = 512, overlap: int = 50
    ) -> List[str]:
        """
        Splits text into overlapping chunks.
        """
        if not text:
            return []

        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunks.append(" ".join(words[i : i + chunk_size]))
        return chunks

    async def create_content_chunks(self, job: JobDescription) -> List[ContentChunk]:
        """
        Creates content chunks from a job description.
        """
        chunks = []
        async with self.async_session() as session:
            sections = (
                (
                    await session.execute(
                        select(JobSection)
                        .where(JobSection.job_id == job.id)
                        .order_by(JobSection.section_order)
                    )
                )
                .scalars()
                .all()
            )

            if sections:
                for section in sections:
                    section_chunks = self._chunk_text(
                        section.section_content,
                        settings.chunk_size,
                        settings.chunk_overlap,
                    )
                    for i, chunk_text in enumerate(section_chunks):
                        chunks.append(
                            ContentChunk(
                                job_id=job.id,
                                section_id=section.id,
                                chunk_text=chunk_text,
                                chunk_index=len(chunks),
                            )
                        )
            elif job.raw_content:
                raw_chunks = self._chunk_text(
                    job.raw_content, settings.chunk_size, settings.chunk_overlap
                )
                for i, chunk_text in enumerate(raw_chunks):
                    chunks.append(
                        ContentChunk(
                            job_id=job.id, chunk_text=chunk_text, chunk_index=i
                        )
                    )
        return chunks

    async def generate_embeddings_for_job(
        self, job: JobDescription, force: bool = False
    ) -> Dict[str, Any]:
        """
        Generates embeddings for a single job description.
        """
        result = {
            "job_id": job.id,
            "job_number": job.job_number,
            "title": job.title,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "errors": [],
        }
        try:
            async with self.async_session() as session:
                if (
                    not force
                    and (
                        await session.execute(
                            select(func.count(ContentChunk.id)).where(
                                ContentChunk.job_id == job.id,
                                ContentChunk.embedding.isnot(None),
                            )
                        )
                    ).scalar_one()
                    > 0
                ):
                    result["message"] = "Skipping - embeddings already exist"
                    return result

                if force:
                    await session.execute(
                        ContentChunk.__table__.delete().where(
                            ContentChunk.job_id == job.id
                        )
                    )
                    await session.commit()

                chunks = await self.create_content_chunks(job)
                if not chunks:
                    result["errors"].append("No content chunks created")
                    return result
                result["chunks_created"] = len(chunks)

                for chunk in chunks:
                    try:
                        embedding = await embedding_service.generate_embedding(
                            chunk.chunk_text
                        )
                        if embedding:
                            chunk.embedding = embedding
                            result["embeddings_generated"] += 1
                        else:
                            result["errors"].append(
                                f"Failed to generate embedding for chunk {chunk.chunk_index}"
                            )
                    except Exception as e:
                        result["errors"].append(
                            f"Error generating embedding for chunk {chunk.chunk_index}: {e}"
                        )

                session.add_all(chunks)
                await session.commit()
                logger.info(f"Generated embeddings for job {job.id}", extra=result)
        except Exception as e:
            result["errors"].append(f"Job processing failed: {e}")
            logger.error(f"Failed to process job {job.id}", exc_info=e)
        return result

    async def generate_embeddings_batch(
        self, limit: Optional[int] = None, force: bool = False, dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Generates embeddings for multiple job descriptions.
        """
        summary = {
            "total_jobs": 0,
            "processed_jobs": 0,
            "total_chunks": 0,
            "total_embeddings": 0,
            "errors": [],
            "job_results": [],
        }
        try:
            async with self.async_session() as session:
                query = select(JobDescription).order_by(JobDescription.id)
                if limit:
                    query = query.limit(limit)
                jobs = (await session.execute(query)).scalars().all()
                summary["total_jobs"] = len(jobs)

                if dry_run:
                    logger.info(f"DRY RUN - would process {len(jobs)} jobs")
                    summary["message"] = f"DRY RUN - would process {len(jobs)} jobs"
                    return summary

                for i, job in enumerate(jobs, 1):
                    logger.info(
                        f"Processing job {i}/{len(jobs)}: {job.id} ({job.job_number})"
                    )
                    job_result = await self.generate_embeddings_for_job(job, force)
                    summary["job_results"].append(job_result)
                    if job_result["chunks_created"] > 0:
                        summary["processed_jobs"] += 1
                        summary["total_chunks"] += job_result["chunks_created"]
                        summary["total_embeddings"] += job_result[
                            "embeddings_generated"
                        ]
                    if job_result["errors"]:
                        summary["errors"].extend(
                            [
                                f"Job {job.job_number}: {error}"
                                for error in job_result["errors"]
                            ]
                        )
                    await asyncio.sleep(0.1)
        except Exception as e:
            summary["errors"].append(f"Batch processing failed: {e}")
            logger.error("Batch processing failed", exc_info=e)
        return summary

    async def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Gets current embedding statistics.
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
            jobs_with_embeddings = (
                await session.execute(
                    select(func.count(func.distinct(ContentChunk.job_id))).where(
                        ContentChunk.embedding.isnot(None)
                    )
                )
            ).scalar_one()
            return {
                "total_jobs": total_jobs,
                "jobs_with_embeddings": jobs_with_embeddings,
                "total_chunks": total_chunks,
                "chunks_with_embeddings": chunks_with_embeddings,
                "embedding_coverage": {
                    "jobs_percentage": (
                        (jobs_with_embeddings / total_jobs * 100)
                        if total_jobs > 0
                        else 0
                    ),
                    "chunks_percentage": (
                        (chunks_with_embeddings / total_chunks * 100)
                        if total_chunks > 0
                        else 0
                    ),
                },
            }

    async def close(self) -> None:
        """
        Closes database connections.
        """
        await self.engine.dispose()


async def main() -> None:
    """
    The main entry point for the script.
    """
    parser = argparse.ArgumentParser(
        description="Generate embeddings for job descriptions"
    )
    parser.add_argument("--limit", type=int, help="Limit number of jobs to process")
    parser.add_argument(
        "--force", action="store_true", help="Regenerate existing embeddings"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show embedding statistics only"
    )
    args = parser.parse_args()

    if not settings.openai_api_key and not args.stats and not args.dry_run:
        logger.error(
            "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        )
        sys.exit(1)

    generator = EmbeddingGenerator()
    try:
        if args.stats:
            stats = await generator.get_embedding_stats()
            logger.info("\n📊 Embedding Statistics")
            logger.info("=" * 50)
            logger.info(f"Total Jobs: {stats['total_jobs']}")
            logger.info(
                f"Jobs with Embeddings: {stats['jobs_with_embeddings']} ({stats['embedding_coverage']['jobs_percentage']:.2f}%)"
            )
            logger.info(f"Total Chunks: {stats['total_chunks']}")
            logger.info(
                f"Chunks with Embeddings: {stats['chunks_with_embeddings']} ({stats['embedding_coverage']['chunks_percentage']:.2f}%)"
            )
            if stats["chunks_with_embeddings"] > 0:
                logger.info("✅ Semantic search is available")
            else:
                logger.warning("⚠️  No embeddings found - semantic search unavailable")
        else:
            logger.info("\n🚀 Starting embedding generation...")
            if args.limit:
                logger.info(f"   Limiting to {args.limit} jobs")
            if args.force:
                logger.info("   Force mode: will regenerate existing embeddings")
            if args.dry_run:
                logger.info("   DRY RUN: no changes will be made")

            summary = await generator.generate_embeddings_batch(
                limit=args.limit, force=args.force, dry_run=args.dry_run
            )

            logger.info("\n📈 Results Summary")
            logger.info("=" * 50)
            if args.dry_run:
                logger.info(f"DRY RUN - Would process: {summary['total_jobs']} jobs")
            else:
                logger.info(f"Total Jobs: {summary['total_jobs']}")
                logger.info(f"Processed Jobs: {summary['processed_jobs']}")
                logger.info(f"Total Chunks Created: {summary['total_chunks']}")
                logger.info(f"Embeddings Generated: {summary['total_embeddings']}")
                if summary["errors"]:
                    logger.error(f"\n❌ Errors ({len(summary['errors'])}):")
                    for error in summary["errors"][:5]:
                        logger.error(f"   • {error}")
                    if len(summary["errors"]) > 5:
                        logger.error(
                            f"   ... and {len(summary['errors']) - 5} more errors"
                        )
                if summary["total_embeddings"] > 0:
                    logger.info("\n✅ Embedding generation completed successfully!")
                    logger.info("   Semantic search is now available.")
                else:
                    logger.warning("\n⚠️  No embeddings were generated.")
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Process interrupted by user")
    except Exception as e:
        logger.critical("Script failed", exc_info=e)
        sys.exit(1)
    finally:
        await generator.close()


if __name__ == "__main__":
    asyncio.run(main())
