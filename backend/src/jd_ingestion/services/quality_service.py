"""
Data quality assessment and metrics calculation service.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func

from ..database.models import (
    JobDescription,
    JobSection,
    JobMetadata,
    ContentChunk,
    DataQualityMetrics,
)
from ..utils.logging import get_logger

logger = get_logger(__name__)


class QualityService:
    """Service for calculating and managing data quality metrics."""

    # Expected sections for complete job descriptions
    EXPECTED_SECTIONS = {
        "general_accountability",
        "organization_structure",
        "nature_and_scope",
        "specific_accountabilities",
        "dimensions",
        "knowledge_skills_abilities",
    }

    # Required structured fields
    REQUIRED_STRUCTURED_FIELDS = {
        "position_title",
        "job_number",
        "classification",
        "department",
    }

    def __init__(self):
        self.calculation_version = "1.0"

    async def calculate_quality_metrics_for_job(
        self, db: AsyncSession, job_id: int
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive quality metrics for a single job.

        Args:
            db: Database session
            job_id: ID of the job to analyze

        Returns:
            Dictionary with calculated quality metrics
        """
        try:
            # Fetch job with related data
            query = (
                select(JobDescription)
                .options(
                    selectinload(JobDescription.sections),
                    selectinload(JobDescription.metadata_entry),
                    selectinload(JobDescription.chunks),
                )
                .where(JobDescription.id == job_id)
            )

            result = await db.execute(query)
            job = result.scalar_one_or_none()

            if not job:
                raise ValueError(f"Job with ID {job_id} not found")

            # Calculate metrics
            metrics = await self._calculate_metrics(job)

            # Save or update metrics in database
            await self._save_quality_metrics(db, job_id, metrics)

            return metrics

        except Exception as e:
            logger.error(
                "Failed to calculate quality metrics for job",
                job_id=job_id,
                error=str(e),
            )
            raise

    async def batch_calculate_quality_metrics(
        self, db: AsyncSession, job_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Calculate quality metrics for multiple jobs or all jobs.

        Args:
            db: Database session
            job_ids: Optional list of specific job IDs to process

        Returns:
            Dictionary with batch processing results
        """
        try:
            # Get job IDs to process
            if job_ids is None:
                query = select(JobDescription.id)
                result = await db.execute(query)
                job_ids = [row[0] for row in result.fetchall()]

            results = {
                "total_jobs": len(job_ids),
                "successful": 0,
                "failed": 0,
                "errors": [],
            }

            for job_id in job_ids:
                try:
                    await self.calculate_quality_metrics_for_job(db, job_id)
                    results["successful"] += 1
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({"job_id": job_id, "error": str(e)})
                    logger.error(
                        "Failed to calculate metrics for job",
                        job_id=job_id,
                        error=str(e),
                    )

            await db.commit()
            return results

        except Exception as e:
            logger.error("Failed to batch calculate quality metrics", error=str(e))
            await db.rollback()
            raise

    async def get_quality_report(
        self, db: AsyncSession, job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive quality report.

        Args:
            db: Database session
            job_id: Optional specific job ID for single job report

        Returns:
            Dictionary with quality report data
        """
        try:
            if job_id:
                return await self._get_single_job_quality_report(db, job_id)
            else:
                return await self._get_system_quality_report(db)

        except Exception as e:
            logger.error(
                "Failed to generate quality report", job_id=job_id, error=str(e)
            )
            raise

    async def _calculate_metrics(self, job: JobDescription) -> Dict[str, Any]:
        """Calculate quality metrics for a job."""

        # Content completeness
        content_completeness = self._calculate_content_completeness(job)
        sections_completeness = self._calculate_sections_completeness(job)
        metadata_completeness = self._calculate_metadata_completeness(job)

        # Quality indicators
        has_structured_fields = self._assess_structured_fields(job)
        has_all_sections = self._assess_sections_coverage(job)
        has_embeddings = self._assess_embeddings_coverage(job)

        # Processing quality
        processing_quality = self._assess_processing_quality(job)

        # Content characteristics
        content_characteristics = self._analyze_content_characteristics(job)

        # Language and encoding quality
        language_quality = self._assess_language_quality(job)

        # Validation results
        validation_results = self._validate_content(job)

        return {
            "content_completeness_score": content_completeness,
            "sections_completeness_score": sections_completeness,
            "metadata_completeness_score": metadata_completeness,
            "has_structured_fields": has_structured_fields,
            "has_all_sections": has_all_sections,
            "has_embeddings": has_embeddings,
            **processing_quality,
            **content_characteristics,
            **language_quality,
            "validation_results": validation_results,
            "quality_flags": self._generate_quality_flags(job, validation_results),
            "calculation_version": self.calculation_version,
        }

    def _calculate_content_completeness(self, job: JobDescription) -> Decimal:
        """Calculate overall content completeness score."""
        score = 0.0
        max_score = 4.0

        # Raw content exists and has reasonable length
        if job.raw_content and len(job.raw_content.strip()) > 100:
            score += 1.0

        # Job has sections
        if job.sections and len(job.sections) > 0:
            score += 1.0

        # Job has metadata
        if job.metadata_entry:
            score += 1.0

        # Job has content chunks
        if job.chunks and len(job.chunks) > 0:
            score += 1.0

        return Decimal(str(round(score / max_score, 3)))

    def _calculate_sections_completeness(self, job: JobDescription) -> Decimal:
        """Calculate section coverage completeness score."""
        if not job.sections:
            return Decimal("0.000")

        sections_found = {section.section_type.lower() for section in job.sections}
        expected_sections = {s.lower() for s in self.EXPECTED_SECTIONS}

        coverage = len(sections_found.intersection(expected_sections)) / len(
            expected_sections
        )
        return Decimal(str(round(coverage, 3)))

    def _calculate_metadata_completeness(self, job: JobDescription) -> Decimal:
        """Calculate metadata completeness score."""
        if not job.metadata_entry:
            return Decimal("0.000")

        metadata = job.metadata_entry
        fields_with_data = 0
        total_fields = 6  # reports_to, department, location, fte_count, salary_budget, effective_date

        if metadata.reports_to and metadata.reports_to.strip():
            fields_with_data += 1
        if metadata.department and metadata.department.strip():
            fields_with_data += 1
        if metadata.location and metadata.location.strip():
            fields_with_data += 1
        if metadata.fte_count is not None:
            fields_with_data += 1
        if metadata.salary_budget is not None:
            fields_with_data += 1
        if metadata.effective_date is not None:
            fields_with_data += 1

        return Decimal(str(round(fields_with_data / total_fields, 3)))

    def _assess_structured_fields(self, job: JobDescription) -> str:
        """Assess structured fields coverage."""
        fields_present = 0
        total_fields = len(self.REQUIRED_STRUCTURED_FIELDS)

        if job.title and job.title.strip():
            fields_present += 1
        if job.job_number and job.job_number.strip():
            fields_present += 1
        if job.classification and job.classification.strip():
            fields_present += 1
        if (
            job.metadata_entry
            and job.metadata_entry.department
            and job.metadata_entry.department.strip()
        ):
            fields_present += 1

        coverage = fields_present / total_fields

        if coverage >= 1.0:
            return "complete"
        elif coverage >= 0.5:
            return "partial"
        else:
            return "missing"

    def _assess_sections_coverage(self, job: JobDescription) -> str:
        """Assess section coverage."""
        if not job.sections:
            return "missing"

        sections_found = {section.section_type.lower() for section in job.sections}
        expected_sections = {s.lower() for s in self.EXPECTED_SECTIONS}

        coverage = len(sections_found.intersection(expected_sections)) / len(
            expected_sections
        )

        if coverage >= 0.8:
            return "complete"
        elif coverage >= 0.4:
            return "partial"
        else:
            return "missing"

    def _assess_embeddings_coverage(self, job: JobDescription) -> str:
        """Assess embeddings coverage."""
        if not job.chunks:
            return "missing"

        chunks_with_embeddings = sum(
            1 for chunk in job.chunks if chunk.embedding is not None
        )
        total_chunks = len(job.chunks)

        if total_chunks == 0:
            return "missing"

        coverage = chunks_with_embeddings / total_chunks

        if coverage >= 1.0:
            return "complete"
        elif coverage >= 0.5:
            return "partial"
        else:
            return "missing"

    def _assess_processing_quality(self, job: JobDescription) -> Dict[str, Any]:
        """Assess processing quality indicators."""

        # Determine extraction success based on content quality
        extraction_success = "success"

        if not job.sections or len(job.sections) == 0:
            extraction_success = "failed"
        elif len(job.sections) < 3:  # Expect at least 3 major sections
            extraction_success = "partial"

        return {
            "processing_errors_count": 0,  # Would be populated from processing logs
            "validation_errors_count": 0,  # Would be calculated from validation
            "content_extraction_success": extraction_success,
        }

    def _analyze_content_characteristics(self, job: JobDescription) -> Dict[str, Any]:
        """Analyze content characteristics."""
        raw_length = len(job.raw_content) if job.raw_content else 0

        # Calculate processed content length from sections
        processed_length = 0
        if job.sections:
            processed_length = sum(
                len(section.section_content)
                for section in job.sections
                if section.section_content
            )

        return {
            "raw_content_length": raw_length,
            "processed_content_length": processed_length,
            "sections_extracted_count": len(job.sections) if job.sections else 0,
            "chunks_generated_count": len(job.chunks) if job.chunks else 0,
        }

    def _assess_language_quality(self, job: JobDescription) -> Dict[str, Any]:
        """Assess language detection and encoding quality."""

        # Simple heuristic for language detection confidence
        confidence = Decimal("0.800")  # Default confidence

        if job.language:
            # If language is detected, assume reasonable confidence
            confidence = Decimal("0.850")

            # Check for mixed language indicators
            if job.raw_content:
                english_words = len(
                    re.findall(
                        r"\b(the|and|of|to|in|for|with|on|by|from|that|this|will|be|is|are)\b",
                        job.raw_content.lower(),
                    )
                )
                french_words = len(
                    re.findall(
                        r"\b(le|la|les|de|du|des|et|pour|avec|dans|sur|par|que|qui|est|sont)\b",
                        job.raw_content.lower(),
                    )
                )

                total_words = english_words + french_words
                if total_words > 10:  # Only assess if we have enough indicators
                    if job.language == "en" and french_words > english_words:
                        confidence = Decimal("0.300")  # Language mismatch
                    elif job.language == "fr" and english_words > french_words:
                        confidence = Decimal("0.300")  # Language mismatch

        # Assess encoding issues
        encoding_issues = "none"
        if job.raw_content:
            # Check for common encoding issue indicators
            if any(char in job.raw_content for char in ["�", "�", "â€™", "â€œ", "â€�"]):
                encoding_issues = "major"
            elif any(char in job.raw_content for char in ["Ã", "Â", "Ã©", "Ã¨", "Ã§"]):
                encoding_issues = "minor"

        return {
            "language_detection_confidence": confidence,
            "encoding_issues_detected": encoding_issues,
        }

    def _validate_content(self, job: JobDescription) -> Dict[str, Any]:
        """Perform detailed content validation."""
        errors = []
        warnings = []

        # Validate basic job information
        if not job.job_number or not job.job_number.strip():
            errors.append("Missing job number")

        if not job.title or not job.title.strip():
            errors.append("Missing job title")

        if not job.classification or not job.classification.strip():
            errors.append("Missing classification")

        # Validate content length
        if not job.raw_content or len(job.raw_content.strip()) < 100:
            errors.append("Raw content too short or missing")
        elif len(job.raw_content) > 100000:  # 100KB
            warnings.append("Raw content unusually long")

        # Validate sections
        if not job.sections or len(job.sections) == 0:
            errors.append("No sections extracted")
        else:
            section_types = {section.section_type for section in job.sections}
            missing_sections = self.EXPECTED_SECTIONS - {
                s.lower() for s in section_types
            }
            if missing_sections:
                warnings.append(
                    f"Missing expected sections: {', '.join(missing_sections)}"
                )

        # Validate chunks and embeddings
        if not job.chunks or len(job.chunks) == 0:
            errors.append("No content chunks generated")
        else:
            chunks_without_embeddings = sum(
                1 for chunk in job.chunks if chunk.embedding is None
            )
            if chunks_without_embeddings > 0:
                warnings.append(
                    f"{chunks_without_embeddings} chunks missing embeddings"
                )

        return {
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings),
        }

    def _generate_quality_flags(
        self, job: JobDescription, validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate quality flags and recommendations."""
        flags = {
            "high_quality": True,
            "needs_review": False,
            "processing_issues": False,
            "content_issues": False,
            "recommendations": [],
        }

        # Check for critical issues
        if validation_results["error_count"] > 0:
            flags["high_quality"] = False
            flags["needs_review"] = True
            flags["processing_issues"] = True
            flags["recommendations"].extend(
                ["Review processing errors", "Consider reprocessing file"]
            )

        # Check for content quality issues
        if not job.sections or len(job.sections) < 3:
            flags["content_issues"] = True
            flags["recommendations"].append("Review section extraction")

        if not job.chunks or len(job.chunks) == 0:
            flags["content_issues"] = True
            flags["recommendations"].append("Generate content chunks")

        # Check for missing embeddings
        if job.chunks:
            chunks_without_embeddings = sum(
                1 for chunk in job.chunks if chunk.embedding is None
            )
            if chunks_without_embeddings > 0:
                flags["recommendations"].append("Generate missing embeddings")

        # Content warnings
        if validation_results["warning_count"] > 2:
            flags["needs_review"] = True
            flags["recommendations"].append("Review content quality warnings")

        return flags

    async def _save_quality_metrics(
        self, db: AsyncSession, job_id: int, metrics: Dict[str, Any]
    ) -> None:
        """Save calculated quality metrics to database."""

        # Check if metrics already exist
        query = select(DataQualityMetrics).where(DataQualityMetrics.job_id == job_id)
        result = await db.execute(query)
        existing_metrics = result.scalar_one_or_none()

        if existing_metrics:
            # Update existing metrics
            for key, value in metrics.items():
                if hasattr(existing_metrics, key):
                    setattr(existing_metrics, key, value)
            existing_metrics.last_calculated = datetime.utcnow()
        else:
            # Create new metrics record
            quality_metrics = DataQualityMetrics(job_id=job_id, **metrics)
            db.add(quality_metrics)

        await db.flush()

    async def _get_single_job_quality_report(
        self, db: AsyncSession, job_id: int
    ) -> Dict[str, Any]:
        """Generate quality report for a single job."""

        query = select(DataQualityMetrics).where(DataQualityMetrics.job_id == job_id)
        result = await db.execute(query)
        metrics = result.scalar_one_or_none()

        if not metrics:
            raise ValueError(f"No quality metrics found for job {job_id}")

        return {
            "job_id": job_id,
            "overall_score": float(metrics.content_completeness_score or 0),
            "completeness": {
                "content": float(metrics.content_completeness_score or 0),
                "sections": float(metrics.sections_completeness_score or 0),
                "metadata": float(metrics.metadata_completeness_score or 0),
            },
            "quality_indicators": {
                "structured_fields": metrics.has_structured_fields,
                "sections": metrics.has_all_sections,
                "embeddings": metrics.has_embeddings,
            },
            "processing_quality": {
                "extraction_success": metrics.content_extraction_success,
                "processing_errors": metrics.processing_errors_count,
                "validation_errors": metrics.validation_errors_count,
            },
            "content_characteristics": {
                "raw_content_length": metrics.raw_content_length,
                "processed_content_length": metrics.processed_content_length,
                "sections_count": metrics.sections_extracted_count,
                "chunks_count": metrics.chunks_generated_count,
            },
            "language_quality": {
                "detection_confidence": float(
                    metrics.language_detection_confidence or 0
                ),
                "encoding_issues": metrics.encoding_issues_detected,
            },
            "validation_results": metrics.validation_results,
            "quality_flags": metrics.quality_flags,
            "last_calculated": (
                metrics.last_calculated.isoformat() if metrics.last_calculated else None
            ),
        }

    async def _get_system_quality_report(self, db: AsyncSession) -> Dict[str, Any]:
        """Generate system-wide quality report."""

        # Get aggregated statistics
        query = select(
            func.count(DataQualityMetrics.id).label("total_jobs"),
            func.avg(DataQualityMetrics.content_completeness_score).label(
                "avg_content_completeness"
            ),
            func.avg(DataQualityMetrics.sections_completeness_score).label(
                "avg_sections_completeness"
            ),
            func.avg(DataQualityMetrics.metadata_completeness_score).label(
                "avg_metadata_completeness"
            ),
            func.sum(DataQualityMetrics.processing_errors_count).label(
                "total_processing_errors"
            ),
            func.sum(DataQualityMetrics.validation_errors_count).label(
                "total_validation_errors"
            ),
        )

        result = await db.execute(query)
        stats = result.first()

        # Get quality distribution
        quality_distribution_query = select(
            func.count().label("count"),
            DataQualityMetrics.has_structured_fields,
            DataQualityMetrics.has_all_sections,
            DataQualityMetrics.has_embeddings,
        ).group_by(
            DataQualityMetrics.has_structured_fields,
            DataQualityMetrics.has_all_sections,
            DataQualityMetrics.has_embeddings,
        )

        distribution_result = await db.execute(quality_distribution_query)
        distribution_data = distribution_result.fetchall()

        return {
            "overview": {
                "total_jobs_analyzed": stats.total_jobs or 0,
                "average_content_completeness": float(
                    stats.avg_content_completeness or 0
                ),
                "average_sections_completeness": float(
                    stats.avg_sections_completeness or 0
                ),
                "average_metadata_completeness": float(
                    stats.avg_metadata_completeness or 0
                ),
                "total_processing_errors": stats.total_processing_errors or 0,
                "total_validation_errors": stats.total_validation_errors or 0,
            },
            "quality_distribution": [
                {
                    "count": row.count,
                    "structured_fields": row.has_structured_fields,
                    "sections": row.has_all_sections,
                    "embeddings": row.has_embeddings,
                }
                for row in distribution_data
            ],
            "generated_at": datetime.utcnow().isoformat(),
        }


# Global service instance
quality_service = QualityService()
