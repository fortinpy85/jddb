"""
Search Analytics Service

Handles tracking, recording, and analyzing search query performance metrics.
Provides insights into query patterns, result relevance, and system performance.
"""

import hashlib
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from ..database.models import SearchAnalytics
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SearchAnalyticsService:
    """Service for managing search analytics and performance tracking."""

    @staticmethod
    async def start_search_session(
        session_id: str, user_id: Optional[str] = None, ip_address: Optional[str] = None
    ) -> str:
        """Start a new search session and return search_id."""
        search_id = str(uuid.uuid4())
        logger.info(
            "Starting search session", search_id=search_id, session_id=session_id
        )
        return search_id

    @staticmethod
    async def record_search(
        db: AsyncSession,
        search_id: str,
        query_text: str,
        search_type: str,
        filters: Dict[str, Any],
        execution_time_ms: int,
        embedding_time_ms: Optional[int] = None,
        total_results: int = 0,
        returned_results: int = 0,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        client_type: str = "web",
        error_info: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a search query and its results."""
        try:
            # Create hash for query deduplication
            query_hash = hashlib.sha256(query_text.encode()).hexdigest()

            # Determine result status
            has_results = "yes" if total_results > 0 else "no"
            if error_info:
                has_results = "error"

            # Create analytics record
            analytics_record = SearchAnalytics(
                search_id=search_id,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                query_text=query_text,
                query_hash=query_hash,
                search_type=search_type,
                filters_applied=filters,
                execution_time_ms=execution_time_ms,
                total_response_time_ms=execution_time_ms + (embedding_time_ms or 0),
                embedding_time_ms=embedding_time_ms,
                total_results=total_results,
                returned_results=returned_results,
                has_results=has_results,
                api_version="1.0",
                client_type=client_type,
                error_occurred="yes" if error_info else "no",
                error_type=error_info.get("type") if error_info else None,
                error_message=error_info.get("message") if error_info else None,
            )

            db.add(analytics_record)
            await db.commit()

            logger.info(
                "Search analytics recorded",
                search_id=search_id,
                query_text=(
                    query_text[:50] + "..." if len(query_text) > 50 else query_text
                ),
                search_type=search_type,
                execution_time_ms=execution_time_ms,
                total_results=total_results,
            )

        except Exception as e:
            logger.error("Failed to record search analytics", error=str(e))
            await db.rollback()

    @staticmethod
    async def record_user_feedback(
        db: AsyncSession,
        search_id: str,
        clicked_results: List[int],
        satisfaction_rating: Optional[int] = None,
    ) -> None:
        """Record user feedback for a search."""
        try:
            result = await db.execute(
                select(SearchAnalytics).where(SearchAnalytics.search_id == search_id)
            )
            search_record = result.scalar_one_or_none()

            if search_record:
                search_record.clicked_results = clicked_results  # type: ignore[assignment]
                if satisfaction_rating:
                    search_record.user_satisfaction = satisfaction_rating  # type: ignore[assignment]

                await db.commit()
                logger.info("User feedback recorded", search_id=search_id)
            else:
                logger.warning(
                    "Search record not found for feedback", search_id=search_id
                )

        except Exception as e:
            logger.error("Failed to record user feedback", error=str(e))
            await db.rollback()

    @staticmethod
    async def get_search_performance_stats(
        db: AsyncSession, days: int = 30
    ) -> Dict[str, Any]:
        """Get search performance statistics for the last N days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Base query for the time period
            base_query = select(SearchAnalytics).where(
                SearchAnalytics.timestamp >= cutoff_date
            )

            # Total searches
            total_searches_result = await db.execute(
                select(func.count()).select_from(base_query.subquery())
            )
            total_searches = total_searches_result.scalar() or 0

            # Search type breakdown
            search_type_result = await db.execute(
                select(SearchAnalytics.search_type, func.count().label("count"))
                .where(SearchAnalytics.timestamp >= cutoff_date)
                .group_by(SearchAnalytics.search_type)
            )
            search_types = {row[0]: row[1] for row in search_type_result.fetchall()}

            # Performance metrics
            perf_result = await db.execute(
                select(
                    func.avg(SearchAnalytics.execution_time_ms).label("avg_time"),
                    func.max(SearchAnalytics.execution_time_ms).label("max_time"),
                    func.min(SearchAnalytics.execution_time_ms).label("min_time"),
                    func.percentile_cont(0.95)
                    .within_group(SearchAnalytics.execution_time_ms)
                    .label("p95_time"),
                ).where(SearchAnalytics.timestamp >= cutoff_date)
            )
            perf_stats = perf_result.first()

            # Success rate
            success_result = await db.execute(
                select(SearchAnalytics.has_results, func.count().label("count"))
                .where(SearchAnalytics.timestamp >= cutoff_date)
                .group_by(SearchAnalytics.has_results)
            )
            result_stats = {row[0]: row[1] for row in success_result.fetchall()}

            # Popular queries
            popular_queries_result = await db.execute(
                select(SearchAnalytics.query_text, func.count().label("frequency"))
                .where(SearchAnalytics.timestamp >= cutoff_date)
                .group_by(SearchAnalytics.query_text)
                .order_by(desc("frequency"))
                .limit(10)
            )
            popular_queries = [
                {"query": row[0], "frequency": row[1]}
                for row in popular_queries_result.fetchall()
            ]

            return {
                "period_days": days,
                "total_searches": total_searches,
                "search_types": search_types,
                "performance": {
                    "avg_execution_time_ms": round(perf_stats[0] or 0, 2)
                    if perf_stats
                    else 0,  # type: ignore[index]
                    "max_execution_time_ms": perf_stats[1] or 0 if perf_stats else 0,  # type: ignore[index]
                    "min_execution_time_ms": perf_stats[2] or 0 if perf_stats else 0,  # type: ignore[index]
                    "p95_execution_time_ms": round(perf_stats[3] or 0, 2)
                    if perf_stats
                    else 0,  # type: ignore[index]
                },
                "success_rates": result_stats,
                "popular_queries": popular_queries,
            }

        except Exception as e:
            logger.error("Failed to get search performance stats", error=str(e))
            return {}

    @staticmethod
    async def get_query_trends(db: AsyncSession, days: int = 7) -> Dict[str, Any]:
        """Get query trends over time."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Daily search volume
            daily_volume_result = await db.execute(
                select(
                    func.date(SearchAnalytics.timestamp).label("date"),
                    func.count().label("searches"),
                )
                .where(SearchAnalytics.timestamp >= cutoff_date)
                .group_by(func.date(SearchAnalytics.timestamp))
                .order_by("date")
            )

            daily_volume = [
                {"date": str(row[0]), "searches": row[1]}
                for row in daily_volume_result.fetchall()
            ]

            # Performance trends
            perf_trends_result = await db.execute(
                select(
                    func.date(SearchAnalytics.timestamp).label("date"),
                    func.avg(SearchAnalytics.execution_time_ms).label("avg_time"),
                )
                .where(SearchAnalytics.timestamp >= cutoff_date)
                .group_by(func.date(SearchAnalytics.timestamp))
                .order_by("date")
            )

            performance_trends = [
                {"date": str(row[0]), "avg_execution_time_ms": round(row[1] or 0, 2)}
                for row in perf_trends_result.fetchall()
            ]

            return {
                "period_days": days,
                "daily_volume": daily_volume,
                "performance_trends": performance_trends,
            }

        except Exception as e:
            logger.error("Failed to get query trends", error=str(e))
            return {}

    @staticmethod
    async def get_slow_queries(
        db: AsyncSession, threshold_ms: int = 1000, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get slowest queries above threshold."""
        try:
            result = await db.execute(
                select(
                    SearchAnalytics.query_text,
                    SearchAnalytics.execution_time_ms,
                    SearchAnalytics.search_type,
                    SearchAnalytics.total_results,
                    SearchAnalytics.timestamp,
                )
                .where(SearchAnalytics.execution_time_ms >= threshold_ms)
                .order_by(desc(SearchAnalytics.execution_time_ms))
                .limit(limit)
            )

            return [
                {
                    "query": row[0],
                    "execution_time_ms": row[1],
                    "search_type": row[2],
                    "total_results": row[3],
                    "timestamp": row[4].isoformat(),
                }
                for row in result.fetchall()
            ]

        except Exception as e:
            logger.error("Failed to get slow queries", error=str(e))
            return []


# Global service instance
search_analytics_service = SearchAnalyticsService()
