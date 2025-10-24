"""
Translation Memory Service for Phase 2 Collaborative Features

This service provides translation memory functionality using pgvector
for semantic similarity matching and reusable translation storage.

Access Control & Permissions:
    Translation memory access is controlled via user permissions and project-level
    access control. Future enhancements will include:
    - User-based permission checks for create, read, update, delete operations
    - Project-level access control with role-based permissions
    - Team collaboration with granular permission management
"""

import logging
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from ..database.models import (
    TranslationProject,
    TranslationMemory,
    TranslationEmbedding,
)
from ..services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class TranslationMemoryService:
    """Translation Memory Service with pgvector semantic search."""

    def __init__(self):
        self.embedding_service = EmbeddingService()

    async def create_project(
        self,
        name: str,
        source_language: str,
        target_language: str,
        description: Optional[str] = None,
        project_type: str = "job_descriptions",
        created_by: Optional[int] = None,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Create a new translation project."""
        if db is None:
            raise ValueError("Database session is required")

        project = TranslationProject(
            name=name,
            description=description,
            source_language=source_language,
            target_language=target_language,
            project_type=project_type,
            status="active",
            created_by=created_by,
        )

        db.add(project)
        await db.commit()
        if db is not None:
            await db.refresh(project)
        else:
            raise ValueError("Database session became None after commit")

        logger.info(
            f"Created translation project: {name} ({source_language} → {target_language}) ID: {project.id}"
        )

        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "source_language": project.source_language,
            "target_language": project.target_language,
            "project_type": project.project_type,
            "status": project.status,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }

    async def add_translation_memory(
        self,
        project_id: int,
        source_text: str,
        target_text: str,
        source_language: str,
        target_language: str,
        domain: Optional[str] = None,
        subdomain: Optional[str] = None,
        quality_score: Optional[float] = None,
        confidence_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Add a new translation memory entry with embeddings."""
        if db is None:
            raise ValueError("Database session is required")

        # Create translation memory entry
        translation = TranslationMemory(
            project_id=project_id,
            source_text=source_text,
            target_text=target_text,
            source_language=source_language,
            target_language=target_language,
            domain=domain,
            subdomain=subdomain,
            quality_score=quality_score,
            confidence_score=confidence_score,
            usage_count=0,
            translation_metadata=metadata,
            created_by=created_by,
        )

        db.add(translation)
        await db.flush()  # Get the translation ID

        # Generate and store embedding for source text
        try:
            embedding_vector = await self.embedding_service.generate_embedding(
                source_text
            )

            # Create hash of source text for deduplication
            text_hash = hashlib.sha256(source_text.encode()).hexdigest()

            embedding = TranslationEmbedding(
                translation_id=translation.id,
                embedding=embedding_vector,
                embedding_model="text-embedding-ada-002",
                text_hash=text_hash,
            )

            db.add(embedding)
            await db.commit()
            await db.refresh(translation)

            logger.info(
                f"Added translation memory entry with embedding ID: {translation.id} for project {project_id}"
            )

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            await db.rollback()
            raise

        return {
            "id": translation.id,
            "project_id": translation.project_id,
            "source_text": translation.source_text,
            "target_text": translation.target_text,
            "source_language": translation.source_language,
            "target_language": translation.target_language,
            "domain": translation.domain,
            "subdomain": translation.subdomain,
            "quality_score": float(translation.quality_score)
            if translation.quality_score
            else None,
            "confidence_score": float(translation.confidence_score)
            if translation.confidence_score
            else None,
            "usage_count": translation.usage_count,
            "created_at": translation.created_at,
        }

    async def search_similar_translations(
        self,
        query_text: str,
        source_language: str,
        target_language: str,
        project_id: Optional[int] = None,
        domain: Optional[str] = None,
        similarity_threshold: float = 0.8,
        limit: int = 10,
        db: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar translations using semantic similarity."""
        if db is None:
            raise ValueError("Database session is required")

        # Generate embedding for query text
        try:
            query_embedding = await self.embedding_service.generate_embedding(
                query_text
            )
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return []

        # Build query with pgvector similarity search
        # Using cosine distance: 1 - cosine_similarity
        query = (
            select(
                TranslationMemory,
                TranslationEmbedding,
                (
                    1 - TranslationEmbedding.embedding.cosine_distance(query_embedding)
                ).label("similarity"),
            )
            .join(
                TranslationEmbedding,
                TranslationMemory.id == TranslationEmbedding.translation_id,
            )
            .where(TranslationMemory.source_language == source_language)
            .where(TranslationMemory.target_language == target_language)
        )

        # Apply optional filters
        if project_id:
            query = query.where(TranslationMemory.project_id == project_id)
        if domain:
            query = query.where(TranslationMemory.domain == domain)

        # Filter by similarity threshold and order by similarity
        query = (
            query.where(
                (1 - TranslationEmbedding.embedding.cosine_distance(query_embedding))
                >= similarity_threshold
            )
            .order_by(desc("similarity"))
            .limit(limit)
        )

        result = await db.execute(query)
        rows = result.all()

        translations = []
        for translation, embedding, similarity in rows:
            translations.append(
                {
                    "id": translation.id,
                    "source_text": translation.source_text,
                    "target_text": translation.target_text,
                    "source_language": translation.source_language,
                    "target_language": translation.target_language,
                    "domain": translation.domain,
                    "subdomain": translation.subdomain,
                    "quality_score": float(translation.quality_score)
                    if translation.quality_score
                    else None,
                    "confidence_score": float(translation.confidence_score)
                    if translation.confidence_score
                    else None,
                    "usage_count": translation.usage_count,
                    "similarity_score": float(similarity),
                    "last_used": translation.last_used,
                }
            )

        logger.info(
            f"Found {len(translations)} similar translations for query (length: {len(query_text)}, threshold: {similarity_threshold})"
        )

        return translations

    async def get_translation_suggestions(
        self,
        source_text: str,
        source_language: str,
        target_language: str,
        project_id: Optional[int] = None,
        domain: Optional[str] = None,
        limit: int = 5,
        db: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        """Get translation suggestions based on semantic similarity."""
        # Use search_similar_translations with a lower threshold for suggestions
        return await self.search_similar_translations(
            query_text=source_text,
            source_language=source_language,
            target_language=target_language,
            project_id=project_id,
            domain=domain,
            similarity_threshold=0.7,  # Lower threshold for suggestions
            limit=limit,
            db=db,
        )

    async def get_project_statistics(
        self, project_id: int, db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Get statistics for a translation project."""
        if db is None:
            raise ValueError("Database session is required")

        # Total translations
        total_query = select(func.count(TranslationMemory.id)).where(
            TranslationMemory.project_id == project_id
        )
        total_result = await db.execute(total_query)
        total_translations = total_result.scalar_one()

        # Unique source texts
        unique_query = select(
            func.count(func.distinct(TranslationMemory.source_text))
        ).where(TranslationMemory.project_id == project_id)
        unique_result = await db.execute(unique_query)
        unique_sources = unique_result.scalar_one()

        # Average quality score
        quality_query = select(func.avg(TranslationMemory.quality_score)).where(
            and_(
                TranslationMemory.project_id == project_id,
                TranslationMemory.quality_score.is_not(None),  # type: ignore[attr-defined]
            )
        )
        quality_result = await db.execute(quality_query)
        avg_quality = quality_result.scalar_one()

        # Domains
        domains_query = (
            select(TranslationMemory.domain, func.count(TranslationMemory.id))
            .where(
                and_(
                    TranslationMemory.project_id == project_id,
                    TranslationMemory.domain.isnot(None),
                )
            )
            .group_by(TranslationMemory.domain)
        )
        domains_result = await db.execute(domains_query)
        domains = [
            {"domain": domain, "count": count} for domain, count in domains_result.all()
        ]

        # Languages
        langs_query = (
            select(
                TranslationMemory.source_language,
                TranslationMemory.target_language,
                func.count(TranslationMemory.id),
            )
            .where(TranslationMemory.project_id == project_id)
            .group_by(
                TranslationMemory.source_language, TranslationMemory.target_language
            )
        )
        langs_result = await db.execute(langs_query)
        lang_pairs = langs_result.all()

        source_langs = list(set(source for source, _, _ in lang_pairs))
        target_langs = list(set(target for _, target, _ in lang_pairs))

        return {
            "total_translations": total_translations,
            "unique_sources": unique_sources,
            "avg_quality_score": float(avg_quality) if avg_quality else 0.0,
            "domains": domains,
            "languages": {"source": source_langs, "target": target_langs},
        }

    async def update_translation_quality(
        self,
        memory_id: int,
        quality_score: float,
        confidence_score: Optional[float] = None,
        feedback: Optional[str] = None,
        updated_by: Optional[int] = None,
        db: Optional[AsyncSession] = None,
    ) -> bool:
        """Update quality scores and feedback for a translation."""
        if db is None:
            raise ValueError("Database session is required")

        query = select(TranslationMemory).where(TranslationMemory.id == memory_id)
        result = await db.execute(query)
        translation = result.scalar_one_or_none()

        if not translation:
            logger.warning(f"Translation memory {memory_id} not found")
            return False

        translation.quality_score = quality_score  # type: ignore[assignment]
        if confidence_score is not None:
            translation.confidence_score = confidence_score  # type: ignore[assignment]

        if feedback:
            if translation.translation_metadata is None:
                translation.translation_metadata = {}  # type: ignore[assignment]
            metadata_dict = (
                dict(translation.translation_metadata)
                if translation.translation_metadata
                else {}
            )
            metadata_dict["feedback"] = feedback
            metadata_dict["updated_by"] = updated_by
            metadata_dict["updated_at"] = datetime.utcnow().isoformat()
            translation.translation_metadata = metadata_dict  # type: ignore[assignment]

        translation.updated_at = datetime.utcnow()  # type: ignore[assignment]

        await db.commit()

        logger.info(
            f"Updated translation quality scores for memory ID: {memory_id} (score: {quality_score})"
        )

        return True

    async def delete_translation_memory(
        self, memory_id: int, db: Optional[AsyncSession] = None
    ) -> bool:
        """Delete a translation memory entry."""
        if db is None:
            raise ValueError("Database session is required")

        query = select(TranslationMemory).where(TranslationMemory.id == memory_id)
        result = await db.execute(query)
        translation = result.scalar_one_or_none()

        if not translation:
            logger.warning(f"Translation memory {memory_id} not found")
            return False

        await db.delete(translation)
        await db.commit()

        logger.info(f"Deleted translation memory entry ID: {memory_id}")

        return True

    async def export_project_translations(
        self,
        project_id: int,
        format_type: str = "json",
        include_metadata: bool = True,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Export all translations from a project."""
        if db is None:
            raise ValueError("Database session is required")

        query = (
            select(TranslationMemory)
            .where(TranslationMemory.project_id == project_id)
            .order_by(TranslationMemory.created_at)
        )

        result = await db.execute(query)
        translations = result.scalars().all()

        exported_translations = []
        for translation in translations:
            item = {
                "source_text": translation.source_text,
                "target_text": translation.target_text,
                "source_language": translation.source_language,
                "target_language": translation.target_language,
                "domain": translation.domain,
                "quality_score": float(translation.quality_score)
                if translation.quality_score
                else None,
            }

            if include_metadata:
                item["metadata"] = {  # type: ignore[assignment]
                    "id": translation.id,
                    "subdomain": translation.subdomain,
                    "confidence_score": float(translation.confidence_score)
                    if translation.confidence_score
                    else None,
                    "usage_count": translation.usage_count,
                    "created_at": translation.created_at.isoformat()
                    if translation.created_at
                    else None,
                    "last_used": translation.last_used.isoformat()
                    if translation.last_used
                    else None,
                }
                if translation.translation_metadata:
                    item["metadata"]["custom"] = translation.translation_metadata  # type: ignore[index]

            exported_translations.append(item)

        logger.info(
            f"Exported {len(exported_translations)} translations from project {project_id} as {format_type}"
        )

        return {
            "translations": exported_translations,
            "total": len(exported_translations),
            "exported_at": datetime.utcnow().isoformat(),
            "format": format_type,
        }

    async def update_usage_stats(
        self,
        tm_id: int,
        used_translation: bool,
        user_feedback: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> bool:
        """Update usage statistics for a translation memory entry."""
        if db is None:
            raise ValueError("Database session is required")

        query = select(TranslationMemory).where(TranslationMemory.id == tm_id)
        result = await db.execute(query)
        translation = result.scalar_one_or_none()

        if not translation:
            logger.warning(f"Translation memory {tm_id} not found")
            return False

        if used_translation:
            translation.usage_count += 1  # type: ignore[assignment]
            translation.last_used = datetime.utcnow()  # type: ignore[assignment]

        if user_feedback:
            if translation.translation_metadata is None:
                translation.translation_metadata = {}  # type: ignore[assignment]
            metadata_dict = (
                dict(translation.translation_metadata)
                if translation.translation_metadata
                else {}
            )
            if "feedback_history" not in metadata_dict:
                metadata_dict["feedback_history"] = []
            metadata_dict["feedback_history"].append(
                {
                    "feedback": user_feedback,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            translation.translation_metadata = metadata_dict  # type: ignore[assignment]

        await db.commit()

        logger.info(
            f"Updated usage stats for translation ID: {tm_id} (used: {used_translation})"
        )

        return True

    # Alias methods to match test expectations
    async def add_translation(
        self,
        project_id: int,
        source_text: str,
        target_text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None,
        created_by: Optional[int] = None,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Alias for add_translation_memory with context parameter."""
        return await self.add_translation_memory(
            project_id=project_id,
            source_text=source_text,
            target_text=target_text,
            source_language=source_language,
            target_language=target_language,
            domain=context,
            created_by=created_by,
            db=db,
        )

    async def get_project_translations(
        self,
        project_id: int,
        db: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        """Get all translations for a project."""
        if db is None:
            raise ValueError("Database session is required")

        query = (
            select(TranslationMemory)
            .where(TranslationMemory.project_id == project_id)
            .order_by(TranslationMemory.created_at.desc())
        )

        result = await db.execute(query)
        translations = result.scalars().all()

        return [
            {
                "id": t.id,
                "source_text": t.source_text,
                "target_text": t.target_text,
                "source_language": t.source_language,
                "target_language": t.target_language,
                "domain": t.domain,
                "quality_score": float(t.quality_score) if t.quality_score else None,
                "created_at": t.created_at,
            }
            for t in translations
        ]

    async def update_translation(
        self,
        translation_id: int,
        target_text: Optional[str] = None,
        quality_score: Optional[float] = None,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Update an existing translation."""
        if db is None:
            raise ValueError("Database session is required")

        query = select(TranslationMemory).where(TranslationMemory.id == translation_id)
        result = await db.execute(query)
        translation = result.scalar_one_or_none()

        if not translation:
            raise ValueError(f"Translation {translation_id} not found")

        if target_text is not None:
            translation.target_text = target_text  # type: ignore[assignment]

        if quality_score is not None:
            translation.quality_score = quality_score  # type: ignore[assignment]

        translation.updated_at = datetime.utcnow()  # type: ignore[assignment]

        await db.commit()
        await db.refresh(translation)

        logger.info(f"Updated translation ID: {translation_id}")

        return {
            "id": translation.id,
            "source_text": translation.source_text,
            "target_text": translation.target_text,
            "quality_score": float(translation.quality_score)
            if translation.quality_score
            else None,
            "updated_at": translation.updated_at,
        }

    async def delete_translation(
        self,
        translation_id: int,
        db: Optional[AsyncSession] = None,
    ) -> bool:
        """Delete a translation. Alias for delete_translation_memory."""
        return await self.delete_translation_memory(translation_id, db)

    async def get_project_stats(
        self,
        project_id: int,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Get project statistics. Alias for get_project_statistics."""
        stats = await self.get_project_statistics(project_id, db)

        # Get project info
        assert db is not None, "Database session is required"
        query = select(TranslationProject).where(TranslationProject.id == project_id)
        result = await db.execute(query)
        project = result.scalar_one_or_none()

        if project:
            stats["project_id"] = project.id
            stats["project_name"] = project.name
            stats["translation_count"] = stats["total_translations"]

        return stats


# Global service instance
translation_memory_service = TranslationMemoryService()
