"""
Search Recommendations Service

ML-powered query suggestions and search recommendations based on:
- Historical search patterns
- Semantic similarity analysis
- User behavior analytics
- Content-based filtering
"""

import re
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, text
from collections import Counter, defaultdict

from ..database.models import (
    SearchAnalytics,
    JobDescription,
    JobSection,
    ContentChunk,
    JobMetadata,
    SavedSearch,
)
from ..services.embedding_service import embedding_service
from ..utils.logging import get_logger
from ..utils.cache import cache_service

logger = get_logger(__name__)


class SearchRecommendationsService:
    """Service for ML-powered search recommendations and query suggestions."""

    def __init__(self):
        self.min_query_length = 3
        self.max_suggestions = 10
        self.similarity_threshold = 0.7
        self.cache_ttl = 3600  # 1 hour

    async def get_query_suggestions(
        self,
        db: AsyncSession,
        partial_query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Generate query suggestions based on partial input using ML analysis.

        Combines:
        - Popular search patterns
        - Semantic similarity
        - User history (if available)
        - Content-based suggestions
        """
        if len(partial_query.strip()) < self.min_query_length:
            return []

        try:
            # Check cache first
            cache_key = f"query_suggestions:{partial_query.lower()}:{limit}"
            cached = await cache_service.get(cache_key)
            if cached:
                logger.info(
                    "Returning cached query suggestions",
                    query=partial_query,
                    count=len(cached),
                )
                return cached

            suggestions = []

            # 1. Get popular similar queries from analytics
            popular_queries = await self._get_popular_similar_queries(
                db, partial_query, limit
            )
            suggestions.extend(popular_queries)

            # 2. Generate semantic-based suggestions
            semantic_suggestions = await self._get_semantic_suggestions(
                db, partial_query, limit
            )
            suggestions.extend(semantic_suggestions)

            # 3. Get user-specific suggestions if available
            if user_id or session_id:
                user_suggestions = await self._get_user_based_suggestions(
                    db, partial_query, user_id, session_id, limit
                )
                suggestions.extend(user_suggestions)

            # 4. Generate content-based suggestions
            content_suggestions = await self._get_content_based_suggestions(
                db, partial_query, limit
            )
            suggestions.extend(content_suggestions)

            # Deduplicate and rank suggestions
            final_suggestions = self._rank_and_deduplicate_suggestions(
                suggestions, partial_query, limit
            )

            # Cache results
            await cache_service.set(cache_key, final_suggestions, ttl=self.cache_ttl)

            logger.info(
                "Generated query suggestions",
                query=partial_query,
                count=len(final_suggestions),
            )
            return final_suggestions

        except Exception as e:
            logger.error(
                "Error generating query suggestions", query=partial_query, error=str(e)
            )
            return []

    async def get_search_recommendations(
        self,
        db: AsyncSession,
        search_context: Dict[str, Any],
        user_id: Optional[str] = None,
        limit: int = 8,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive search recommendations including:
        - Related searches
        - Trending queries
        - Personalized suggestions
        - Filter recommendations
        """
        try:
            recommendations = {
                "related_searches": [],
                "trending_queries": [],
                "suggested_filters": [],
                "similar_users_searched": [],
                "popular_in_category": [],
            }

            # Run recommendation tasks in parallel
            tasks = [
                self._get_related_searches(db, search_context, limit),
                self._get_trending_queries(db, limit),
                self._get_suggested_filters(db, search_context),
                self._get_popular_in_category(db, search_context, limit),
            ]

            if user_id:
                tasks.append(self._get_similar_users_searches(db, user_id, limit))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            recommendations["related_searches"] = (
                results[0] if not isinstance(results[0], Exception) else []
            )
            recommendations["trending_queries"] = (
                results[1] if not isinstance(results[1], Exception) else []
            )
            recommendations["suggested_filters"] = (
                results[2] if not isinstance(results[2], Exception) else []
            )
            recommendations["popular_in_category"] = (
                results[3] if not isinstance(results[3], Exception) else []
            )

            if user_id and len(results) > 4:
                recommendations["similar_users_searched"] = (
                    results[4] if not isinstance(results[4], Exception) else []
                )

            logger.info(
                "Generated search recommendations",
                user_id=user_id,
                total_recommendations=sum(len(v) for v in recommendations.values()),
            )

            return recommendations

        except Exception as e:
            logger.error("Error generating search recommendations", error=str(e))
            return {
                "related_searches": [],
                "trending_queries": [],
                "suggested_filters": [],
                "similar_users_searched": [],
                "popular_in_category": [],
            }

    async def _get_popular_similar_queries(
        self, db: AsyncSession, partial_query: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Get popular queries similar to the partial input."""
        try:
            # Find queries that contain the partial query or are similar
            query = (
                select(
                    SearchAnalytics.query_text,
                    func.count(SearchAnalytics.id).label("usage_count"),
                    func.avg(SearchAnalytics.total_results).label("avg_results"),
                    func.avg(SearchAnalytics.execution_time_ms).label("avg_time"),
                )
                .where(
                    and_(
                        SearchAnalytics.query_text.ilike(f"%{partial_query}%"),
                        SearchAnalytics.total_results > 0,
                        SearchAnalytics.created_at
                        >= datetime.now() - timedelta(days=30),
                    )
                )
                .group_by(SearchAnalytics.query_text)
                .order_by(desc("usage_count"))
                .limit(limit)
            )

            result = await db.execute(query)
            rows = result.fetchall()

            suggestions = []
            for row in rows:
                suggestions.append(
                    {
                        "text": row.query_text,
                        "type": "popular",
                        "score": float(row.usage_count),
                        "metadata": {
                            "usage_count": row.usage_count,
                            "avg_results": float(row.avg_results or 0),
                            "avg_time_ms": float(row.avg_time or 0),
                        },
                    }
                )

            return suggestions

        except Exception as e:
            logger.error("Error getting popular similar queries", error=str(e))
            return []

    async def _get_semantic_suggestions(
        self, db: AsyncSession, partial_query: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Generate semantically similar query suggestions using embeddings."""
        try:
            if not embedding_service:
                return []

            # Generate embedding for partial query
            query_embedding = await embedding_service.generate_embedding(partial_query)
            if not query_embedding:
                return []

            # Find semantically similar content chunks and extract key terms
            similarity_query = text(
                """
                SELECT DISTINCT c.content, c.section_type, j.title, j.classification
                FROM content_chunks c
                JOIN job_descriptions j ON c.job_id = j.id
                WHERE c.embedding <=> :query_embedding < 0.3
                ORDER BY c.embedding <=> :query_embedding
                LIMIT :limit
            """
            )

            result = await db.execute(
                similarity_query,
                {
                    "query_embedding": f'[{",".join(map(str, query_embedding))}]',
                    "limit": limit * 2,
                },
            )

            similar_content = result.fetchall()

            # Extract key terms and phrases from similar content
            suggestions = []
            processed_terms = set()

            for content_row in similar_content:
                terms = self._extract_key_terms(content_row.content, partial_query)
                for term in terms:
                    if (
                        term not in processed_terms
                        and len(term) > self.min_query_length
                    ):
                        processed_terms.add(term)
                        suggestions.append(
                            {
                                "text": term,
                                "type": "semantic",
                                "score": 0.8,
                                "metadata": {
                                    "source_section": content_row.section_type,
                                    "source_job": content_row.title,
                                    "classification": content_row.classification,
                                },
                            }
                        )

            return suggestions[:limit]

        except Exception as e:
            logger.error("Error generating semantic suggestions", error=str(e))
            return []

    async def _get_user_based_suggestions(
        self,
        db: AsyncSession,
        partial_query: str,
        user_id: Optional[str],
        session_id: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Get personalized suggestions based on user search history."""
        try:
            conditions = []
            if user_id:
                conditions.append(SearchAnalytics.user_id == user_id)
            if session_id:
                conditions.append(SearchAnalytics.session_id == session_id)

            if not conditions:
                return []

            # Get user's recent successful searches
            query = (
                select(
                    SearchAnalytics.query_text,
                    SearchAnalytics.total_results,
                    SearchAnalytics.created_at,
                )
                .where(
                    and_(
                        *conditions,
                        SearchAnalytics.total_results > 0,
                        SearchAnalytics.created_at
                        >= datetime.now() - timedelta(days=7),
                        SearchAnalytics.query_text.ilike(f"%{partial_query}%"),
                    )
                )
                .order_by(desc(SearchAnalytics.created_at))
                .limit(limit)
            )

            result = await db.execute(query)
            rows = result.fetchall()

            suggestions = []
            for row in rows:
                suggestions.append(
                    {
                        "text": row.query_text,
                        "type": "personal",
                        "score": 0.9,
                        "metadata": {
                            "total_results": row.total_results,
                            "last_used": row.created_at.isoformat(),
                        },
                    }
                )

            return suggestions

        except Exception as e:
            logger.error("Error getting user-based suggestions", error=str(e))
            return []

    async def _get_content_based_suggestions(
        self, db: AsyncSession, partial_query: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Generate suggestions based on actual job content analysis."""
        try:
            # Search for matching terms in job titles and sections
            query = text(
                """
                SELECT DISTINCT
                    j.title,
                    j.classification,
                    COUNT(*) as match_count
                FROM job_descriptions j
                JOIN job_sections s ON j.id = s.job_id
                WHERE
                    j.title ILIKE :partial_query OR
                    s.content ILIKE :partial_query OR
                    j.classification ILIKE :partial_query
                GROUP BY j.title, j.classification
                ORDER BY match_count DESC
                LIMIT :limit
            """
            )

            result = await db.execute(
                query, {"partial_query": f"%{partial_query}%", "limit": limit}
            )

            rows = result.fetchall()

            suggestions = []
            for row in rows:
                # Extract meaningful search terms from titles
                title_terms = self._extract_search_terms(row.title)
                for term in title_terms:
                    if (
                        partial_query.lower() in term.lower()
                        and len(term) > self.min_query_length
                    ):
                        suggestions.append(
                            {
                                "text": term,
                                "type": "content",
                                "score": 0.7,
                                "metadata": {
                                    "source": "job_title",
                                    "classification": row.classification,
                                    "match_count": row.match_count,
                                },
                            }
                        )

            return suggestions[:limit]

        except Exception as e:
            logger.error("Error getting content-based suggestions", error=str(e))
            return []

    def _extract_key_terms(self, content: str, partial_query: str) -> List[str]:
        """Extract relevant key terms from content that match partial query context."""
        if not content:
            return []

        # Clean and tokenize content
        words = re.findall(r"\b[a-zA-Z]+\b", content.lower())
        partial_words = partial_query.lower().split()

        # Find phrases that contain partial query words
        terms = []
        for i, word in enumerate(words):
            if any(pw in word for pw in partial_words):
                # Extract 2-3 word phrases around matching words
                start = max(0, i - 1)
                end = min(len(words), i + 3)
                phrase = " ".join(words[start:end])
                if len(phrase) > self.min_query_length:
                    terms.append(phrase)

        return list(set(terms))

    def _extract_search_terms(self, title: str) -> List[str]:
        """Extract meaningful search terms from job titles."""
        if not title:
            return []

        # Remove common job prefixes and suffixes
        cleaned = re.sub(
            r"^(director|manager|senior|junior|lead|principal)\s+",
            "",
            title,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"\s+(i{1,3}|iv|v|1|2|3|4|5)$", "", cleaned, flags=re.IGNORECASE
        )

        # Extract meaningful multi-word terms
        words = cleaned.split()
        terms = []

        # Single words
        for word in words:
            if len(word) > 3:
                terms.append(word)

        # Two-word phrases
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i + 1]}"
            terms.append(phrase)

        # Full cleaned title
        if cleaned.strip():
            terms.append(cleaned.strip())

        return terms

    def _rank_and_deduplicate_suggestions(
        self, suggestions: List[Dict[str, Any]], partial_query: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Rank and deduplicate suggestions based on relevance and diversity."""
        if not suggestions:
            return []

        # Deduplicate by text (case-insensitive)
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            text_lower = suggestion["text"].lower()
            if text_lower not in seen:
                seen.add(text_lower)
                unique_suggestions.append(suggestion)

        # Rank by score and relevance to partial query
        def calculate_relevance(suggestion):
            text = suggestion["text"].lower()
            partial = partial_query.lower()

            # Boost exact matches
            if partial in text:
                relevance_boost = 1.0
            # Boost word matches
            elif any(word in text for word in partial.split()):
                relevance_boost = 0.8
            else:
                relevance_boost = 0.5

            # Type-based scoring
            type_scores = {
                "personal": 1.0,
                "popular": 0.9,
                "semantic": 0.8,
                "content": 0.7,
            }

            base_score = suggestion.get("score", 0.5)
            type_score = type_scores.get(suggestion.get("type", "content"), 0.5)

            return base_score * type_score * relevance_boost

        # Sort by calculated relevance
        unique_suggestions.sort(key=calculate_relevance, reverse=True)

        return unique_suggestions[:limit]

    async def _get_related_searches(
        self, db: AsyncSession, search_context: Dict[str, Any], limit: int
    ) -> List[Dict[str, Any]]:
        """Get searches related to current search context."""
        try:
            query_text = search_context.get("query", "")
            if not query_text:
                return []

            # Find searches with similar filters or terms
            conditions = [SearchAnalytics.total_results > 0]

            # Add query similarity condition
            if len(query_text) > 3:
                conditions.append(
                    SearchAnalytics.query_text.ilike(f"%{query_text[:5]}%")
                )

            query = (
                select(
                    SearchAnalytics.query_text,
                    func.count().label("frequency"),
                    func.avg(SearchAnalytics.total_results).label("avg_results"),
                )
                .where(and_(*conditions))
                .group_by(SearchAnalytics.query_text)
                .order_by(desc("frequency"))
                .limit(limit)
            )

            result = await db.execute(query)
            rows = result.fetchall()

            return [
                {
                    "query": row.query_text,
                    "frequency": row.frequency,
                    "avg_results": float(row.avg_results or 0),
                }
                for row in rows
            ]

        except Exception as e:
            logger.error("Error getting related searches", error=str(e))
            return []

    async def _get_trending_queries(
        self, db: AsyncSession, limit: int
    ) -> List[Dict[str, Any]]:
        """Get trending search queries from recent analytics."""
        try:
            # Get queries from last 24 hours with high frequency
            query = (
                select(SearchAnalytics.query_text, func.count().label("frequency"))
                .where(
                    and_(
                        SearchAnalytics.created_at
                        >= datetime.now() - timedelta(hours=24),
                        SearchAnalytics.total_results > 0,
                    )
                )
                .group_by(SearchAnalytics.query_text)
                .order_by(desc("frequency"))
                .limit(limit)
            )

            result = await db.execute(query)
            rows = result.fetchall()

            return [
                {
                    "query": row.query_text,
                    "frequency": row.frequency,
                    "trend": "up",  # Could be enhanced with trend analysis
                }
                for row in rows
            ]

        except Exception as e:
            logger.error("Error getting trending queries", error=str(e))
            return []

    async def _get_suggested_filters(
        self, db: AsyncSession, search_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest relevant filters based on search context."""
        try:
            query_text = search_context.get("query", "")

            # Analyze common filters used with similar queries
            suggestions = []

            # Suggest classification filters
            class_query = (
                select(JobDescription.classification, func.count().label("count"))
                .group_by(JobDescription.classification)
                .order_by(desc("count"))
                .limit(5)
            )

            result = await db.execute(class_query)
            classifications = result.fetchall()

            for cls in classifications:
                suggestions.append(
                    {
                        "filter_type": "classification",
                        "value": cls.classification,
                        "count": cls.count,
                        "label": f"Classification: {cls.classification}",
                    }
                )

            # Suggest department filters if available
            dept_query = (
                select(JobMetadata.department, func.count().label("count"))
                .where(JobMetadata.department.isnot(None))
                .group_by(JobMetadata.department)
                .order_by(desc("count"))
                .limit(5)
            )

            result = await db.execute(dept_query)
            departments = result.fetchall()

            for dept in departments:
                suggestions.append(
                    {
                        "filter_type": "department",
                        "value": dept.department,
                        "count": dept.count,
                        "label": f"Department: {dept.department}",
                    }
                )

            return suggestions[:8]

        except Exception as e:
            logger.error("Error getting suggested filters", error=str(e))
            return []

    async def _get_similar_users_searches(
        self, db: AsyncSession, user_id: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Get searches from users with similar search patterns."""
        try:
            # This would require user behavior analysis
            # For now, return empty - can be enhanced with collaborative filtering
            return []

        except Exception as e:
            logger.error("Error getting similar users searches", error=str(e))
            return []

    async def _get_popular_in_category(
        self, db: AsyncSession, search_context: Dict[str, Any], limit: int
    ) -> List[Dict[str, Any]]:
        """Get popular searches in the same category/classification."""
        try:
            # If no classification in context, return general popular searches
            classification = search_context.get("classification")

            conditions = [SearchAnalytics.total_results > 0]
            if classification:
                # This would require joining with job results
                # For now, get general popular searches
                pass

            query = (
                select(SearchAnalytics.query_text, func.count().label("frequency"))
                .where(and_(*conditions))
                .group_by(SearchAnalytics.query_text)
                .order_by(desc("frequency"))
                .limit(limit)
            )

            result = await db.execute(query)
            rows = result.fetchall()

            return [
                {"query": row.query_text, "frequency": row.frequency} for row in rows
            ]

        except Exception as e:
            logger.error("Error getting popular in category", error=str(e))
            return []


# Global instance
search_recommendations_service = SearchRecommendationsService()
