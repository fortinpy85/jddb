"""
Translation Memory Service for Phase 2 Collaborative Features

This service provides translation memory functionality using pgvector
for semantic similarity matching and reusable translation storage.
"""
import logging
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from sqlalchemy.dialects.postgresql import array

from ..database.models import TranslationProject, TranslationMemory, TranslationEmbedding
from ..database.connection import get_db
from ..services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class TranslationMemoryService:
    """Service for managing translation memory with pgvector similarity search."""

    def __init__(self):
        self.embedding_service = EmbeddingService()

    def create_project(
        self,
        name: str,
        source_language: str,
        target_language: str,
        description: Optional[str] = None,
        project_type: str = 'job_descriptions',
        created_by: Optional[int] = None,
        db: Optional[Session] = None
    ) -> TranslationProject:
        """Create a new translation project."""
        if db is None:
            db = next(get_db())

        try:
            project = TranslationProject(
                name=name,
                description=description,
                source_language=source_language,
                target_language=target_language,
                project_type=project_type,
                created_by=created_by
            )

            db.add(project)
            db.commit()
            db.refresh(project)

            logger.info(f"Created translation project: {name} ({source_language} -> {target_language})")
            return project

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating translation project: {e}")
            raise

    def add_translation_memory(
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
        db: Optional[Session] = None
    ) -> TranslationMemory:
        """Add a new translation memory entry with embeddings."""
        if db is None:
            db = next(get_db())

        try:
            # Create context hash for deduplication
            context_data = f"{source_text.strip().lower()}||{target_text.strip().lower()}"
            context_hash = hashlib.sha256(context_data.encode()).hexdigest()

            # Check for existing translation
            existing = db.query(TranslationMemory).filter(
                and_(
                    TranslationMemory.project_id == project_id,
                    TranslationMemory.context_hash == context_hash
                )
            ).first()

            if existing:
                # Update usage count and last used
                existing.usage_count += 1
                existing.last_used = datetime.utcnow()
                db.commit()
                logger.info(f"Updated existing translation memory entry: {existing.id}")
                return existing

            # Create new translation memory entry
            tm_entry = TranslationMemory(
                project_id=project_id,
                source_text=source_text,
                target_text=target_text,
                source_language=source_language,
                target_language=target_language,
                domain=domain,
                subdomain=subdomain,
                quality_score=Decimal(str(quality_score)) if quality_score else None,
                confidence_score=Decimal(str(confidence_score)) if confidence_score else None,
                context_hash=context_hash,
                tm_metadata=metadata or {},
                created_by=created_by
            )

            db.add(tm_entry)
            db.commit()
            db.refresh(tm_entry)

            # Generate and store embeddings
            self._generate_embeddings(tm_entry, db)

            logger.info(f"Added translation memory entry: {tm_entry.id}")
            return tm_entry

        except Exception as e:
            db.rollback()
            logger.error(f"Error adding translation memory: {e}")
            raise

    def _generate_embeddings(self, tm_entry: TranslationMemory, db: Session):
        """Generate and store embeddings for translation memory entry."""
        try:
            # Generate embedding for source text
            source_embedding = self.embedding_service.generate_embedding(tm_entry.source_text)

            # Create text hash for the source text
            text_hash = hashlib.sha256(tm_entry.source_text.encode()).hexdigest()

            embedding_entry = TranslationEmbedding(
                memory_id=tm_entry.id,
                embedding=source_embedding,
                text_hash=text_hash
            )

            db.add(embedding_entry)
            db.commit()

            logger.info(f"Generated embeddings for translation memory: {tm_entry.id}")

        except Exception as e:
            logger.error(f"Error generating embeddings for TM {tm_entry.id}: {e}")
            # Don't raise here as the TM entry itself is valid

    def search_similar_translations(
        self,
        query_text: str,
        source_language: str,
        target_language: str,
        project_id: Optional[int] = None,
        similarity_threshold: float = 0.7,
        limit: int = 10,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar translations using vector similarity."""
        if db is None:
            db = next(get_db())

        try:
            # Generate embedding for query text
            query_embedding = self.embedding_service.generate_embedding(query_text)

            # Build the base query
            query = db.query(
                TranslationMemory,
                TranslationEmbedding,
                func.cosine_similarity(
                    TranslationEmbedding.embedding,
                    array(query_embedding)
                ).label('similarity')
            ).join(
                TranslationEmbedding,
                TranslationMemory.id == TranslationEmbedding.memory_id
            ).filter(
                and_(
                    TranslationMemory.source_language == source_language,
                    TranslationMemory.target_language == target_language
                )
            )

            # Filter by project if specified
            if project_id:
                query = query.filter(TranslationMemory.project_id == project_id)

            # Apply similarity threshold and ordering
            query = query.filter(
                func.cosine_similarity(
                    TranslationEmbedding.embedding,
                    array(query_embedding)
                ) >= similarity_threshold
            ).order_by(
                func.cosine_similarity(
                    TranslationEmbedding.embedding,
                    array(query_embedding)
                ).desc()
            ).limit(limit)

            results = []
            for tm, embedding, similarity in query.all():
                results.append({
                    'id': tm.id,
                    'source_text': tm.source_text,
                    'target_text': tm.target_text,
                    'similarity_score': float(similarity),
                    'quality_score': float(tm.quality_score) if tm.quality_score else None,
                    'confidence_score': float(tm.confidence_score) if tm.confidence_score else None,
                    'usage_count': tm.usage_count,
                    'domain': tm.domain,
                    'subdomain': tm.subdomain,
                    'metadata': tm.tm_metadata,
                    'last_used': tm.last_used.isoformat() if tm.last_used else None,
                    'created_at': tm.created_at.isoformat()
                })

            logger.info(f"Found {len(results)} similar translations for query")
            return results

        except Exception as e:
            logger.error(f"Error searching similar translations: {e}")
            raise

    def get_translation_suggestions(
        self,
        source_text: str,
        source_language: str,
        target_language: str,
        project_id: Optional[int] = None,
        context: Optional[str] = None,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """Get translation suggestions with confidence scoring."""
        if db is None:
            db = next(get_db())

        # Start with exact matches
        exact_matches = self._find_exact_matches(
            source_text, source_language, target_language, project_id, db
        )

        # Add fuzzy matches
        fuzzy_matches = self.search_similar_translations(
            source_text, source_language, target_language, project_id,
            similarity_threshold=0.6, limit=5, db=db
        )

        # Remove duplicates and rank by confidence
        suggestions = []
        seen_ids = set()

        # Add exact matches first
        for match in exact_matches:
            if match['id'] not in seen_ids:
                match['match_type'] = 'exact'
                match['confidence'] = 1.0
                suggestions.append(match)
                seen_ids.add(match['id'])

        # Add fuzzy matches
        for match in fuzzy_matches:
            if match['id'] not in seen_ids:
                match['match_type'] = 'fuzzy'
                match['confidence'] = match['similarity_score']
                suggestions.append(match)
                seen_ids.add(match['id'])

        # Sort by confidence score
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)

        return suggestions[:10]  # Return top 10 suggestions

    def _find_exact_matches(
        self,
        source_text: str,
        source_language: str,
        target_language: str,
        project_id: Optional[int],
        db: Session
    ) -> List[Dict[str, Any]]:
        """Find exact text matches in translation memory."""
        query = db.query(TranslationMemory).filter(
            and_(
                TranslationMemory.source_text == source_text,
                TranslationMemory.source_language == source_language,
                TranslationMemory.target_language == target_language
            )
        )

        if project_id:
            query = query.filter(TranslationMemory.project_id == project_id)

        results = []
        for tm in query.all():
            results.append({
                'id': tm.id,
                'source_text': tm.source_text,
                'target_text': tm.target_text,
                'quality_score': float(tm.quality_score) if tm.quality_score else None,
                'confidence_score': float(tm.confidence_score) if tm.confidence_score else None,
                'usage_count': tm.usage_count,
                'domain': tm.domain,
                'subdomain': tm.subdomain,
                'metadata': tm.tm_metadata,
                'last_used': tm.last_used.isoformat() if tm.last_used else None,
                'created_at': tm.created_at.isoformat()
            })

        return results

    def update_usage_stats(
        self,
        tm_id: int,
        used_translation: bool = True,
        user_feedback: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ):
        """Update usage statistics for a translation memory entry."""
        if db is None:
            db = next(get_db())

        try:
            tm_entry = db.query(TranslationMemory).filter(
                TranslationMemory.id == tm_id
            ).first()

            if not tm_entry:
                raise ValueError(f"Translation memory entry {tm_id} not found")

            if used_translation:
                tm_entry.usage_count += 1
                tm_entry.last_used = datetime.utcnow()

            # Update metadata with user feedback
            if user_feedback:
                if not tm_entry.tm_metadata:
                    tm_entry.tm_metadata = {}

                feedback_key = f"feedback_{datetime.utcnow().isoformat()}"
                tm_entry.tm_metadata[feedback_key] = user_feedback

            db.commit()
            logger.info(f"Updated usage stats for translation memory: {tm_id}")

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating usage stats: {e}")
            raise

    def get_project_statistics(
        self,
        project_id: int,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Get statistics for a translation project."""
        if db is None:
            db = next(get_db())

        try:
            project = db.query(TranslationProject).filter(
                TranslationProject.id == project_id
            ).first()

            if not project:
                raise ValueError(f"Translation project {project_id} not found")

            # Count total entries
            total_entries = db.query(TranslationMemory).filter(
                TranslationMemory.project_id == project_id
            ).count()

            # Count by domain
            domain_counts = db.query(
                TranslationMemory.domain,
                func.count(TranslationMemory.id)
            ).filter(
                TranslationMemory.project_id == project_id
            ).group_by(TranslationMemory.domain).all()

            # Calculate average quality scores
            avg_quality = db.query(
                func.avg(TranslationMemory.quality_score)
            ).filter(
                and_(
                    TranslationMemory.project_id == project_id,
                    TranslationMemory.quality_score.isnot(None)
                )
            ).scalar()

            # Total usage count
            total_usage = db.query(
                func.sum(TranslationMemory.usage_count)
            ).filter(
                TranslationMemory.project_id == project_id
            ).scalar() or 0

            # Most used translations
            top_translations = db.query(TranslationMemory).filter(
                TranslationMemory.project_id == project_id
            ).order_by(
                TranslationMemory.usage_count.desc()
            ).limit(5).all()

            return {
                'project_id': project_id,
                'project_name': project.name,
                'total_entries': total_entries,
                'total_usage': int(total_usage),
                'average_quality_score': float(avg_quality) if avg_quality else None,
                'domain_distribution': {domain: count for domain, count in domain_counts},
                'top_translations': [
                    {
                        'id': tm.id,
                        'source_text': tm.source_text[:100] + '...' if len(tm.source_text) > 100 else tm.source_text,
                        'usage_count': tm.usage_count,
                        'quality_score': float(tm.quality_score) if tm.quality_score else None
                    }
                    for tm in top_translations
                ],
                'source_language': project.source_language,
                'target_language': project.target_language
            }

        except Exception as e:
            logger.error(f"Error getting project statistics: {e}")
            raise