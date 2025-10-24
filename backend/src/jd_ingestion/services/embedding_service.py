"""
Unified OpenAI Embedding Service with performance optimizations and comprehensive features.
Consolidates functionality from both original and optimized embedding services.
"""

import asyncio
import math
import openai
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from datetime import datetime

from ..config.settings import settings
from ..database.models import ContentChunk
from ..utils.logging import get_logger
from ..utils.circuit_breaker import (
    get_openai_circuit_breaker,
    CircuitBreakerOpenException,
)
from .analytics_service import analytics_service
from .rate_limiting_service import rate_limiting_service

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating and managing OpenAI embeddings."""

    def __init__(self):
        """Initialize the embedding service."""
        if not settings.openai_api_key:
            logger.warning(
                "OpenAI API key not configured - embedding features will be unavailable"
            )
            self.client = None
        else:
            self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

        # Initialize circuit breaker for OpenAI API calls
        self.circuit_breaker = get_openai_circuit_breaker()

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a given text using OpenAI API with circuit breaker protection."""
        if not self.client:
            logger.warning(
                "OpenAI client not available - skipping embedding generation"
            )
            return None

        try:
            # Clean and truncate text if necessary
            clean_text = self._prepare_text_for_embedding(text)
            if not clean_text:
                return None

            # Estimate tokens for rate limiting (approximate: 1 token per 4 characters)
            estimated_tokens = len(clean_text) // 4
            estimated_cost = estimated_tokens * 0.0001 / 1000  # OpenAI pricing estimate

            # Check rate limits before making API call
            is_allowed, rate_statuses = await rate_limiting_service.check_rate_limit(
                service="openai",
                operation_type="embedding_generation",
                estimated_tokens=estimated_tokens,
                estimated_cost=estimated_cost,
            )

            if not is_allowed:
                # Get recommended delay
                delay = await rate_limiting_service.get_recommended_delay(
                    "openai", "embedding_generation"
                )
                logger.warning(
                    "Rate limit exceeded for OpenAI API",
                    estimated_tokens=estimated_tokens,
                    recommended_delay=delay,
                )

                if delay > 0 and delay < 5:  # Only wait if delay is reasonable
                    await asyncio.sleep(delay)

            start_time = datetime.utcnow()

            # Use circuit breaker to protect OpenAI API call
            async with self.circuit_breaker.protect("embedding_generation"):
                # Generate embedding using OpenAI
                response = await self.client.embeddings.create(
                    model=settings.embedding_model, input=clean_text
                )

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Extract embedding vector
            embedding = response.data[0].embedding

            # Calculate actual cost (OpenAI pricing)
            actual_tokens = response.usage.total_tokens
            actual_cost = actual_tokens * 0.0001 / 1000  # $0.0001 per 1K tokens

            # Record actual usage for rate limiting
            await rate_limiting_service.record_usage(
                service="openai",
                operation_type="embedding_generation",
                tokens_used=actual_tokens,
                cost=actual_cost,
            )

            # Log usage for cost tracking
            await self._log_api_usage(
                operation_type="embedding_generation",
                model_name=settings.embedding_model,
                input_tokens=actual_tokens,
                duration=duration,
            )

            return embedding

        except CircuitBreakerOpenException as e:
            logger.warning("OpenAI API circuit breaker is open", error=str(e))
            return None

        except Exception as e:
            logger.error(
                "Failed to generate embedding", text_length=len(text), error=str(e)
            )
            return None

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Alias for generate_embedding for backward compatibility."""
        return await self.generate_embedding(text)

    async def generate_embeddings_batch(
        self, texts: List[str], batch_size: int = 100
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts in batches."""
        if not self.client:
            return [None] * len(texts)

        embeddings: List[Optional[List[float]]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = await asyncio.gather(
                *[self.generate_embedding(text) for text in batch],
                return_exceptions=True,
            )

            # Handle exceptions in batch results
            for emb in batch_embeddings:
                if isinstance(emb, BaseException):
                    logger.error("Batch embedding generation failed", error=str(emb))
                    embeddings.append(None)
                else:
                    # emb is Optional[List[float]] here
                    embeddings.append(emb)

            # Add small delay between batches to respect rate limits
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)

        return embeddings

    async def find_similar_chunks(
        self,
        query_embedding: List[float],
        db: AsyncSession,
        job_id_exclude: Optional[int] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        classification_filter: Optional[str] = None,
        language_filter: Optional[str] = None,
        use_optimized: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Find similar content chunks using vector similarity search.
        Uses optimized HNSW index for better performance when use_optimized=True.
        """
        try:
            # Build the similarity search query using pgvector with optimization
            similarity_query = """
            SELECT
                cc.id,
                cc.job_id,
                cc.chunk_text,
                jd.job_number,
                jd.title,
                jd.classification,
                jd.language,
                (1 - (cc.embedding <=> %s::vector)) as similarity_score
            FROM content_chunks cc
            JOIN job_descriptions jd ON cc.job_id = jd.id
            WHERE cc.embedding IS NOT NULL
            """

            params: List[Any] = [query_embedding]

            # Add filters to optimize query performance using indexed columns
            if job_id_exclude:
                similarity_query += " AND cc.job_id != %s"
                params.append(job_id_exclude)

            if classification_filter:
                similarity_query += " AND jd.classification = %s"
                params.append(classification_filter)

            if language_filter:
                similarity_query += " AND jd.language = %s"
                params.append(language_filter)

            # Use vector distance ordering with index optimization
            similarity_query += """
            ORDER BY cc.embedding <=> %s::vector
            LIMIT %s
            """
            params.extend([query_embedding, limit])

            result = await db.execute(text(similarity_query), params)
            rows = result.fetchall()

            # Filter by similarity threshold and format results
            similar_chunks = []
            for row in rows:
                if row.similarity_score >= similarity_threshold:
                    similar_chunks.append(
                        {
                            "chunk_id": row.id,
                            "job_id": row.job_id,
                            "job_number": row.job_number,
                            "title": row.title,
                            "classification": row.classification,
                            "language": row.language,
                            "chunk_text": row.chunk_text,
                            "similarity_score": float(row.similarity_score),
                        }
                    )

            return similar_chunks

        except Exception as e:
            logger.error("Vector similarity search failed", error=str(e))
            return []

    # Backward compatibility alias for optimized method
    async def find_similar_chunks_optimized(
        self,
        query_embedding: List[float],
        db: AsyncSession,
        job_id_exclude: Optional[int] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        classification_filter: Optional[str] = None,
        language_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Optimized version - delegates to main method with optimized=True."""
        return await self.find_similar_chunks(
            query_embedding=query_embedding,
            db=db,
            job_id_exclude=job_id_exclude,
            limit=limit,
            similarity_threshold=similarity_threshold,
            classification_filter=classification_filter,
            language_filter=language_filter,
            use_optimized=True,
        )

    async def semantic_search(
        self,
        query: str,
        db: AsyncSession,
        classification_filter: Optional[str] = None,
        language_filter: Optional[str] = None,
        limit: int = 20,
        similarity_threshold: float = 0.6,
        use_optimized: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using query embedding and vector similarity.
        Enhanced with optimized query structure and improved index usage.
        """
        try:
            # Generate embedding for the search query
            query_embedding = await self.generate_embedding(query)
            if not query_embedding:
                logger.warning("Failed to generate query embedding")
                return []

            if use_optimized:
                # Optimized search query using indexes and efficient aggregation
                search_query = """
                SELECT
                    jd.id as job_id,
                    jd.job_number,
                    jd.title,
                    jd.classification,
                    jd.language,
                    MAX(1 - (cc.embedding <=> %s::vector)) as max_similarity_score,
                    COUNT(cc.id) as matching_chunks
                FROM content_chunks cc
                JOIN job_descriptions jd ON cc.job_id = jd.id
                WHERE cc.embedding IS NOT NULL
                """

                params: List[Any] = [query_embedding]

                # Add filters using indexed columns for optimal performance
                if classification_filter:
                    search_query += " AND jd.classification = %s"
                    params.append(classification_filter)

                if language_filter:
                    search_query += " AND jd.language = %s"
                    params.append(language_filter)

                # Group and filter with threshold, order by relevance
                search_query += """
                GROUP BY jd.id, jd.job_number, jd.title, jd.classification, jd.language
                HAVING MAX(1 - (cc.embedding <=> %s::vector)) >= %s
                ORDER BY max_similarity_score DESC
                LIMIT %s
                """
                params.extend([query_embedding, similarity_threshold, limit])

                result = await db.execute(text(search_query), params)
                rows = result.fetchall()
            else:
                # Fallback search using named parameters (for compatibility)
                search_query = """
                SELECT DISTINCT
                    jd.id as job_id,
                    jd.job_number,
                    jd.title,
                    jd.classification,
                    jd.language,
                    MAX(1 - (cc.embedding <=> :query_embedding)) as max_similarity_score,
                    COUNT(cc.id) as matching_chunks
                FROM content_chunks cc
                JOIN job_descriptions jd ON cc.job_id = jd.id
                WHERE cc.embedding IS NOT NULL
                """

                # Convert embedding list to PostgreSQL array string format
                embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
                named_params: Dict[str, Any] = {
                    "query_embedding": embedding_str,
                    "limit": limit,
                }

                if classification_filter:
                    search_query += " AND jd.classification = :classification"
                    named_params["classification"] = classification_filter

                if language_filter:
                    search_query += " AND jd.language = :language"
                    named_params["language"] = language_filter

                search_query += """
                GROUP BY jd.id, jd.job_number, jd.title, jd.classification, jd.language
                HAVING MAX(1 - (cc.embedding <=> :query_embedding)) > :similarity_threshold
                ORDER BY max_similarity_score DESC
                LIMIT :limit
                """
                named_params["similarity_threshold"] = similarity_threshold

                result = await db.execute(text(search_query), named_params)
                rows = result.fetchall()

            # Format results
            semantic_results = []
            for row in rows:
                semantic_results.append(
                    {
                        "job_id": row.job_id,
                        "job_number": row.job_number,
                        "title": row.title,
                        "classification": row.classification,
                        "language": row.language,
                        "relevance_score": float(row.max_similarity_score),
                        "matching_chunks": row.matching_chunks,
                    }
                )

            return semantic_results

        except Exception as e:
            logger.error("Semantic search failed", query=query, error=str(e))
            return []

    # Backward compatibility alias for optimized method
    async def semantic_search_optimized(
        self,
        query: str,
        db: AsyncSession,
        classification_filter: Optional[str] = None,
        language_filter: Optional[str] = None,
        limit: int = 20,
        similarity_threshold: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """Optimized version - delegates to main method with optimized=True."""
        return await self.semantic_search(
            query=query,
            db=db,
            classification_filter=classification_filter,
            language_filter=language_filter,
            limit=limit,
            similarity_threshold=similarity_threshold,
            use_optimized=True,
        )

    def _prepare_text_for_embedding(self, text: str) -> str:
        """Clean and prepare text for embedding generation."""
        if not text:
            return ""

        # Remove excessive whitespace and normalize
        clean_text = " ".join(text.split())

        # Truncate if too long (OpenAI has token limits)
        max_chars = 8000  # Conservative limit to stay under token limits
        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars]

        return clean_text

    async def _log_api_usage(
        self,
        operation_type: str,
        model_name: str,
        input_tokens: int,
        duration: float,
        job_id: Optional[int] = None,
    ):
        """Log API usage for cost tracking."""
        try:
            # Estimate cost based on OpenAI pricing
            cost_per_1k_tokens = 0.0001  # Approximate cost for text-embedding-ada-002
            estimated_cost = (input_tokens / 1000) * cost_per_1k_tokens

            # Log to console for immediate debugging
            logger.info(
                "OpenAI API usage",
                operation_type=operation_type,
                model_name=model_name,
                input_tokens=input_tokens,
                estimated_cost=estimated_cost,
                duration=duration,
                job_id=job_id,
            )

            # Track AI usage in analytics system
            # Use a new database session to avoid conflicts
            from ..database.connection import get_async_session

            async for db in get_async_session():
                try:
                    await analytics_service.track_ai_usage(
                        db=db,
                        service_type="openai",
                        operation_type=operation_type,
                        model_name=model_name,
                        input_tokens=input_tokens,
                        output_tokens=0,  # Embedding requests don't have output tokens
                        cost_usd=Decimal(str(estimated_cost)),
                        success="success",
                        metadata={
                            "duration": duration,
                            "job_id": job_id,
                            "cost_per_1k_tokens": cost_per_1k_tokens,
                        },
                    )
                    break  # Exit the async for loop after successful tracking
                except Exception as track_error:
                    logger.error("Failed to track AI usage", error=str(track_error))
                finally:
                    await db.close()

        except Exception as e:
            logger.error("Failed to log API usage", error=str(e))

    async def batch_similarity_search(
        self,
        query_embeddings: List[List[float]],
        db: AsyncSession,
        limit_per_query: int = 5,
        similarity_threshold: float = 0.7,
    ) -> List[List[Dict[str, Any]]]:
        """
        Perform batch similarity searches for multiple embeddings efficiently.
        Added from optimized embedding service.
        """
        try:
            # Execute all searches concurrently for better performance
            tasks = [
                self.find_similar_chunks(
                    query_embedding=embedding,
                    db=db,
                    limit=limit_per_query,
                    similarity_threshold=similarity_threshold,
                )
                for embedding in query_embeddings
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions and return results
            batch_results: List[List[Dict[str, Any]]] = []
            for i, result in enumerate(results):
                if isinstance(result, BaseException):
                    logger.error(
                        f"Batch search failed for query {i}", error=str(result)
                    )
                    batch_results.append([])
                else:
                    # result is List[Dict[str, Any]] here
                    batch_results.append(result)

            return batch_results

        except Exception as e:
            logger.error("Batch similarity search failed", error=str(e))
            return []

    async def get_performance_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Get performance statistics for embedding operations.
        Added from optimized embedding service.
        """
        try:
            # Query index usage and performance stats
            stats_query = """
            SELECT
                schemaname,
                relname as tablename,
                indexrelname as indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE relname IN ('content_chunks', 'job_descriptions')
            AND indexrelname LIKE 'idx_%'
            ORDER BY idx_scan DESC;
            """

            result = await db.execute(text(stats_query))
            index_stats = result.fetchall()

            # Query table statistics
            table_stats_query = """
            SELECT
                schemaname,
                relname as tablename,
                n_tup_ins,
                n_tup_upd,
                n_tup_del,
                n_live_tup,
                n_dead_tup,
                seq_scan,
                seq_tup_read,
                idx_scan,
                idx_tup_fetch
            FROM pg_stat_user_tables
            WHERE relname IN ('content_chunks', 'job_descriptions');
            """

            table_result = await db.execute(text(table_stats_query))
            table_stats = table_result.fetchall()

            return {
                "index_performance": [
                    {
                        "schema": row.schemaname,
                        "table": row.tablename,
                        "index": row.indexname,
                        "scans": row.idx_scan,
                        "tuples_read": row.idx_tup_read,
                        "tuples_fetched": row.idx_tup_fetch,
                    }
                    for row in index_stats
                ],
                "table_performance": [
                    {
                        "schema": row.schemaname,
                        "table": row.tablename,
                        "live_tuples": row.n_live_tup,
                        "dead_tuples": row.n_dead_tup,
                        "sequential_scans": row.seq_scan,
                        "index_scans": row.idx_scan,
                        "index_efficiency": round(
                            (row.idx_scan / max(row.seq_scan + row.idx_scan, 1)) * 100,
                            2,
                        ),
                    }
                    for row in table_stats
                ],
            }

        except Exception as e:
            logger.error("Failed to get performance stats", error=str(e))
            return {"error": str(e)}

    def calculate_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity between two embeddings."""
        if not embedding1 or not embedding2:
            return 0.0

        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have the same dimension")

        # Convert to numpy-like operations
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = math.sqrt(sum(a * a for a in embedding1))
        norm2 = math.sqrt(sum(b * b for b in embedding2))

        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _truncate_text(self, text: str, max_tokens: int = 8000) -> str:
        """Truncate text to fit within token limits."""
        if not text:
            return text

        # Rough estimate: 1 token ≈ 0.75 words ≈ 4 characters
        estimated_tokens = self._estimate_tokens(text)

        if estimated_tokens <= max_tokens:
            return text

        # Calculate truncation point
        words = text.split()
        target_words = int(max_tokens * 0.75)  # Conservative estimate

        if len(words) <= target_words:
            return text

        truncated = " ".join(words[:target_words])
        return truncated + "..."

    def _estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in text."""
        if not text:
            return 0

        # Rough estimate based on OpenAI's guidelines:
        # - 1 token ≈ 4 characters for English text
        # - 1 token ≈ 0.75 words on average
        word_count = len(text.split())
        char_count = len(text)

        # Use the more conservative estimate
        token_estimate_words = int(word_count / 0.75)
        token_estimate_chars = int(char_count / 4)

        return max(token_estimate_words, token_estimate_chars)

    async def batch_generate_embeddings(
        self, texts: List[str]
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        embeddings = []
        for text_content in texts:
            try:
                embedding = await self.generate_embedding(text_content)
                embeddings.append(embedding)
            except Exception as e:
                logger.error("Failed to generate embedding for text", error=str(e))
                embeddings.append(None)

        return embeddings

    async def get_similar_jobs(
        self,
        job_id: int,
        db: AsyncSession,
        limit: int = 5,
        similarity_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Find jobs similar to the given job ID based on embedding similarity."""
        try:
            # Get embeddings for the reference job
            result = await db.execute(
                select(ContentChunk.embedding)
                .where(ContentChunk.job_id == job_id)
                .where(ContentChunk.embedding.is_not(None))
                .limit(1)
            )
            reference_chunk = result.first()

            if not reference_chunk or not reference_chunk.embedding:
                logger.warning(f"No embeddings found for job {job_id}")
                return []

            # Use the existing find_similar_chunks method
            similar_chunks = await self.find_similar_chunks(
                query_embedding=reference_chunk.embedding,
                db=db,
                job_id_exclude=job_id,
                limit=limit * 3,  # Get more chunks to group by job
                similarity_threshold=similarity_threshold,
            )

            # Group by job and take the best match per job
            job_scores: Dict[str, Dict[str, Any]] = {}
            for chunk in similar_chunks:
                job_id_key = chunk["job_id"]
                if (
                    job_id_key not in job_scores
                    or chunk["similarity_score"]
                    > job_scores[job_id_key]["similarity_score"]
                ):
                    job_scores[job_id_key] = chunk

            # Sort by similarity and limit results
            similar_jobs = sorted(
                job_scores.values(), key=lambda x: x["similarity_score"], reverse=True
            )[:limit]

            return similar_jobs

        except Exception as e:
            logger.error(f"Failed to find similar jobs for job {job_id}", error=str(e))
            return []

    async def generate_embeddings_for_job(self, job_id: int, db: AsyncSession) -> bool:
        """Generate embeddings for all content chunks of a specific job."""
        try:
            # Get all chunks for this job that don't have embeddings
            result = await db.execute(
                select(ContentChunk)
                .where(ContentChunk.job_id == job_id)
                .where(ContentChunk.embedding.is_(None))
            )
            chunks_without_embeddings = result.scalars().all()

            if not chunks_without_embeddings:
                logger.info(f"All chunks for job {job_id} already have embeddings")
                return True

            success_count = 0
            total_count = len(chunks_without_embeddings)

            for chunk in chunks_without_embeddings:
                try:
                    chunk_text = (
                        str(chunk.chunk_text)
                        if not isinstance(chunk.chunk_text, str)
                        else chunk.chunk_text
                    )
                    embedding = await self.generate_embedding(chunk_text)
                    if embedding:
                        chunk.embedding = embedding  # type: ignore[assignment]
                        success_count += 1
                    else:
                        logger.warning(
                            f"Failed to generate embedding for chunk {chunk.id}"
                        )
                except Exception as e:
                    logger.error(
                        f"Error generating embedding for chunk {chunk.id}", error=str(e)
                    )

            # Commit the changes
            await db.commit()

            logger.info(
                f"Generated embeddings for job {job_id}: {success_count}/{total_count} chunks successful"
            )

            return success_count > 0

        except Exception as e:
            logger.error(
                f"Failed to generate embeddings for job {job_id}", error=str(e)
            )
            await db.rollback()
            return False

    def _validate_embedding(self, embedding: Optional[List[float]]) -> bool:
        """Validate that an embedding has the correct format and dimensions."""
        if embedding is None:
            return False

        if not isinstance(embedding, list):
            return False

        if len(embedding) == 0:
            return False

        # Check for expected embedding dimension (OpenAI text-embedding-ada-002 uses 1536)
        expected_dimension = 1536
        if len(embedding) != expected_dimension:
            return False

        # Check that all values are numeric
        try:
            return all(isinstance(x, (int, float)) for x in embedding)
        except Exception:
            return False

    def _create_chunks_for_embedding(
        self, text: str, chunk_size: int = 1000, overlap: int = 200
    ) -> List[str]:
        """Split text into chunks suitable for embedding generation."""
        if not text:
            return []

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))

            # Try to break at word boundaries
            if end < len(text):
                # Find the last space before the chunk size limit
                last_space = text.rfind(" ", start, end)
                if last_space > start:
                    end = last_space

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position, accounting for overlap
            if end >= len(text):
                break
            start = max(start + 1, end - overlap)

        return chunks


# Global unified embedding service instance
embedding_service = EmbeddingService()

# Backward compatibility: provide optimized_embedding_service as an alias
optimized_embedding_service = embedding_service
