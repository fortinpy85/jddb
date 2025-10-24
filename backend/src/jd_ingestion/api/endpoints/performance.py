"""
API endpoints for performance monitoring and optimization.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from ...database.connection import get_async_session
from ...services.embedding_service import optimized_embedding_service
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class PerformanceStats(BaseModel):
    """Performance statistics response model."""

    index_performance: List[Dict[str, Any]]
    table_performance: List[Dict[str, Any]]


class VectorSearchBenchmark(BaseModel):
    """Vector search benchmark request model."""

    query_text: str
    limit: int = 10
    similarity_threshold: float = 0.7
    include_filters: bool = False
    classification_filter: Optional[str] = None
    language_filter: Optional[str] = None


@router.get("/stats", response_model=Dict[str, Any])
async def get_performance_statistics(db: AsyncSession = Depends(get_async_session)):
    """Get database performance statistics and index usage metrics."""
    try:
        logger.info("Retrieving performance statistics")

        stats = await optimized_embedding_service.get_performance_stats(db)

        return {
            "status": "success",
            "performance_stats": stats,
            "generated_at": "2025-09-13T12:33:00.000000",
        }

    except Exception as e:
        logger.error("Failed to retrieve performance statistics", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve performance stats: {str(e)}"
        )


@router.post("/benchmark/vector-search")
async def benchmark_vector_search(
    benchmark: VectorSearchBenchmark, db: AsyncSession = Depends(get_async_session)
):
    """Benchmark vector search performance with different configurations."""
    try:
        import time

        logger.info("Running vector search benchmark", query=benchmark.query_text)

        # Generate query embedding
        start_time = time.perf_counter()
        query_embedding = await optimized_embedding_service.generate_embedding(
            benchmark.query_text
        )
        embedding_time = time.perf_counter() - start_time

        if not query_embedding:
            raise HTTPException(
                status_code=400, detail="Failed to generate query embedding"
            )

        # Test standard similarity search
        start_time = time.perf_counter()
        similarity_results = (
            await optimized_embedding_service.find_similar_chunks_optimized(
                query_embedding=query_embedding,
                db=db,
                limit=benchmark.limit,
                similarity_threshold=benchmark.similarity_threshold,
                classification_filter=(
                    benchmark.classification_filter
                    if benchmark.include_filters
                    else None
                ),
                language_filter=(
                    benchmark.language_filter if benchmark.include_filters else None
                ),
            )
        )
        similarity_search_time = time.perf_counter() - start_time

        # Test semantic search
        start_time = time.perf_counter()
        semantic_results = await optimized_embedding_service.semantic_search_optimized(
            query=benchmark.query_text,
            db=db,
            classification_filter=(
                benchmark.classification_filter if benchmark.include_filters else None
            ),
            language_filter=(
                benchmark.language_filter if benchmark.include_filters else None
            ),
            limit=benchmark.limit,
            similarity_threshold=benchmark.similarity_threshold,
        )
        semantic_search_time = time.perf_counter() - start_time

        return {
            "status": "success",
            "benchmark_results": {
                "query_text": benchmark.query_text,
                "configuration": {
                    "limit": benchmark.limit,
                    "similarity_threshold": benchmark.similarity_threshold,
                    "filters_applied": benchmark.include_filters,
                    "classification_filter": benchmark.classification_filter,
                    "language_filter": benchmark.language_filter,
                },
                "performance_metrics": {
                    "embedding_generation_ms": round(embedding_time * 1000, 2),
                    "similarity_search_ms": round(similarity_search_time * 1000, 2),
                    "semantic_search_ms": round(semantic_search_time * 1000, 2),
                    "total_time_ms": round(
                        (embedding_time + similarity_search_time + semantic_search_time)
                        * 1000,
                        2,
                    ),
                },
                "result_counts": {
                    "similarity_results": len(similarity_results),
                    "semantic_results": len(semantic_results),
                },
                "sample_results": {
                    "similarity_search": similarity_results[:3],  # First 3 results
                    "semantic_search": semantic_results[:3],
                },
            },
            "generated_at": "2025-09-13T12:33:00.000000",
        }

    except Exception as e:
        logger.error("Vector search benchmark failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")


@router.post("/optimize/indexes")
async def optimize_database_indexes(db: AsyncSession = Depends(get_async_session)):
    """Run database optimization commands to improve performance."""
    try:
        logger.info("Running database optimization")

        from sqlalchemy import text

        # Analyze tables to update statistics
        analyze_commands = [
            "ANALYZE content_chunks;",
            "ANALYZE job_descriptions;",
            "ANALYZE usage_analytics;",
            "ANALYZE ai_usage_tracking;",
            "ANALYZE system_metrics;",
        ]

        results = []
        for command in analyze_commands:
            try:
                await db.execute(text(command))
                results.append({"command": command, "status": "success"})
            except Exception as cmd_error:
                logger.warning(
                    f"Optimization command failed: {command}", error=str(cmd_error)
                )
                results.append(
                    {"command": command, "status": "failed", "error": str(cmd_error)}
                )

        await db.commit()

        # Check if VACUUM is needed (this might take time, so we just report recommendation)
        vacuum_check_query = """
        SELECT
            schemaname,
            tablename,
            n_dead_tup,
            n_live_tup,
            CASE
                WHEN n_live_tup > 0 THEN round((n_dead_tup::float / n_live_tup::float) * 100, 2)
                ELSE 0
            END as dead_tuple_percent
        FROM pg_stat_user_tables
        WHERE tablename IN ('content_chunks', 'job_descriptions', 'usage_analytics', 'ai_usage_tracking')
        AND n_dead_tup > 0;
        """

        vacuum_result = await db.execute(text(vacuum_check_query))
        vacuum_recommendations = vacuum_result.fetchall()

        return {
            "status": "success",
            "optimization_results": {
                "analyze_commands": results,
                "vacuum_recommendations": [
                    {
                        "table": row.tablename,
                        "dead_tuples": row.n_dead_tup,
                        "dead_tuple_percentage": float(row.dead_tuple_percent),
                        "needs_vacuum": row.dead_tuple_percent > 10,
                    }
                    for row in vacuum_recommendations
                ],
            },
            "message": "Database optimization completed successfully",
            "generated_at": "2025-09-13T12:33:00.000000",
        }

    except Exception as e:
        logger.error("Database optimization failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/health")
async def performance_health_check(db: AsyncSession = Depends(get_async_session)):
    """Check the health and performance status of key database operations."""
    try:
        from sqlalchemy import text
        import time

        health_checks = []

        # Test basic query performance
        start_time = time.perf_counter()
        result = await db.execute(
            text("SELECT COUNT(*) FROM content_chunks WHERE embedding IS NOT NULL")
        )
        embedding_count = result.scalar()
        query_time = time.perf_counter() - start_time

        health_checks.append(
            {
                "check": "embedding_count_query",
                "duration_ms": round(query_time * 1000, 2),
                "result": embedding_count,
                "status": "healthy" if query_time < 0.1 else "slow",
            }
        )

        # Test index usage
        start_time = time.perf_counter()
        index_query = """
        SELECT COUNT(*) FROM pg_stat_user_indexes
        WHERE relname = 'content_chunks' AND indexname LIKE 'idx_%'
        """
        result = await db.execute(text(index_query))
        index_count = result.scalar()
        index_check_time = time.perf_counter() - start_time

        health_checks.append(
            {
                "check": "index_availability",
                "duration_ms": round(index_check_time * 1000, 2),
                "result": index_count,
                "status": "healthy" if (index_count or 0) > 0 else "warning",
            }
        )

        # Overall health status
        overall_status = "healthy"
        if any(check["status"] == "slow" for check in health_checks):
            overall_status = "degraded"
        if any(check["status"] == "warning" for check in health_checks):
            overall_status = "warning"

        return {
            "status": overall_status,
            "health_checks": health_checks,
            "summary": {
                "total_embeddings": embedding_count,
                "available_indexes": index_count,
                "performance_rating": overall_status,
            },
            "generated_at": "2025-09-13T12:33:00.000000",
        }

    except Exception as e:
        logger.error("Performance health check failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
